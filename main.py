import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from database import get_db_connection, init_db, log_activity
from matcher import find_matches_for_item, find_all_matches, calculate_match_score

app = FastAPI(
    title="Campus Lost & Found Platform API",
    description="Backend API for reporting lost & found campus items, AI description matching, claims, and verification.",
    version="1.0.0"
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------ Pydantic Models ------------------

class ItemCreate(BaseModel):
    type: str = Field(..., description="'lost' or 'found'")
    title: str = Field(..., min_length=2, max_length=150)
    description: str = Field(..., min_length=5)
    category: str = Field(..., description="Item category")
    location_id: Optional[int] = None
    location_name: str = Field(..., description="Campus location name")
    date_occurred: str = Field(..., description="Date item was lost or found (YYYY-MM-DD)")
    reporter_name: str = Field(..., min_length=2)
    reporter_email: str = Field(..., min_length=5)
    reporter_phone: Optional[str] = ""
    secret_details: Optional[str] = ""
    image_url: Optional[str] = ""


class ItemStatusUpdate(BaseModel):
    status: str = Field(..., description="'open', 'claim_pending', 'claimed', 'returned', 'closed'")
    notes: Optional[str] = ""


class ClaimCreate(BaseModel):
    item_id: int
    claimant_name: str
    claimant_email: str
    claimant_phone: Optional[str] = ""
    claimant_student_id: str
    proof_description: str
    proof_image_url: Optional[str] = ""


class ClaimVerify(BaseModel):
    verification_status: str = Field(..., description="'approved', 'rejected', 'more_info_needed'")
    admin_notes: Optional[str] = ""
    resolve_item: Optional[bool] = True


class CustomMatchRequest(BaseModel):
    type: str = Field(default="lost", description="'lost' or 'found'")
    title: str
    description: str
    category: str
    location_name: Optional[str] = ""
    date_occurred: Optional[str] = ""


# ------------------ Helper Database Functions ------------------

def row_to_dict(row) -> Dict[str, Any]:
    if row is None:
        return {}
    return dict(row)


def rows_to_dicts(rows) -> List[Dict[str, Any]]:
    return [dict(r) for r in rows]


# ------------------ API Endpoints ------------------

@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/api/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/api/locations")
def get_locations():
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM locations ORDER BY name ASC").fetchall()
    conn.close()
    return rows_to_dicts(rows)


@app.get("/api/items")
def get_items(
    type: Optional[str] = Query(None, description="Filter by 'lost' or 'found'"),
    category: Optional[str] = Query(None, description="Filter by category"),
    location_id: Optional[int] = Query(None, description="Filter by location ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search query")
):
    conn = get_db_connection()
    query = "SELECT * FROM items WHERE 1=1"
    params = []

    if type:
        query += " AND type = ?"
        params.append(type.lower())
    if category:
        query += " AND category = ?"
        params.append(category)
    if location_id:
        query += " AND location_id = ?"
        params.append(location_id)
    if status:
        query += " AND status = ?"
        params.append(status.lower())
    if search:
        search_pattern = f"%{search}%"
        query += " AND (title LIKE ? OR description LIKE ? OR location_name LIKE ?)"
        params.extend([search_pattern, search_pattern, search_pattern])

    query += " ORDER BY id DESC"
    rows = conn.execute(query, params).fetchall()
    items = rows_to_dicts(rows)

    # Attach claim count for each item
    for item in items:
        claim_count = conn.execute(
            "SELECT COUNT(*) FROM claims WHERE item_id = ?", (item["id"],)
        ).fetchone()[0]
        item["claim_count"] = claim_count

    conn.close()
    return items


@app.get("/api/items/{item_id}")
def get_item(item_id: int):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Item not found")

    item = row_to_dict(row)

    # Get claims on this item
    claims = conn.execute(
        "SELECT * FROM claims WHERE item_id = ? ORDER BY id DESC", (item_id,)
    ).fetchall()
    item["claims"] = rows_to_dicts(claims)

    # Get potential matches
    opposite_type = "found" if item["type"] == "lost" else "lost"
    candidate_rows = conn.execute(
        "SELECT * FROM items WHERE type = ? AND status != 'returned' AND status != 'closed'",
        (opposite_type,)
    ).fetchall()
    candidates = rows_to_dicts(candidate_rows)

    matches = find_matches_for_item(item, candidates, min_score=25, top_k=5)
    item["matches"] = matches

    conn.close()
    return item


@app.post("/api/items", status_code=status.HTTP_201_CREATED)
def create_item(payload: ItemCreate):
    conn = get_db_connection()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO items (
        type, title, description, category, location_id, location_name,
        date_occurred, date_reported, status, reporter_name, reporter_email,
        reporter_phone, secret_details, image_url
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'open', ?, ?, ?, ?, ?)
    """, (
        payload.type.lower(),
        payload.title,
        payload.description,
        payload.category,
        payload.location_id,
        payload.location_name,
        payload.date_occurred,
        now_str,
        payload.reporter_name,
        payload.reporter_email,
        payload.reporter_phone,
        payload.secret_details,
        payload.image_url
    ))
    item_id = cursor.lastrowid
    conn.commit()

    created_row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    new_item = row_to_dict(created_row)

    # Log activity
    log_activity(
        action=f"ITEM_REPORTED_{payload.type.upper()}",
        details=f"{payload.reporter_name} reported {payload.type} item: '{payload.title}' at {payload.location_name}",
        item_id=item_id
    )

    # Instant Match Search
    opposite_type = "found" if payload.type.lower() == "lost" else "lost"
    candidates = rows_to_dicts(conn.execute(
        "SELECT * FROM items WHERE type = ? AND status != 'returned' AND status != 'closed'",
        (opposite_type,)
    ).fetchall())
    conn.close()

    immediate_matches = find_matches_for_item(new_item, candidates, min_score=35, top_k=5)

    return {
        "item": new_item,
        "matches": immediate_matches,
        "message": f"{payload.type.capitalize()} item reported successfully!"
    }


@app.put("/api/items/{item_id}/status")
def update_item_status(item_id: int, payload: ItemStatusUpdate):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Item not found")

    old_status = row["status"]
    new_status = payload.status.lower()

    conn.execute(
        "UPDATE items SET status = ? WHERE id = ?",
        (new_status, item_id)
    )
    conn.commit()
    conn.close()

    log_activity(
        action="ITEM_STATUS_UPDATED",
        details=f"Item #{item_id} status changed from '{old_status}' to '{new_status}'. {payload.notes or ''}".strip(),
        item_id=item_id
    )

    return {"message": f"Status updated to '{new_status}'", "id": item_id, "status": new_status}


@app.delete("/api/items/{item_id}")
def delete_item(item_id: int):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Item not found")

    conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()

    log_activity(
        action="ITEM_DELETED",
        details=f"Item #{item_id} ('{row['title']}') was deleted",
        item_id=item_id
    )

    return {"message": f"Item #{item_id} deleted successfully"}


# ------------------ AI / Description Matching Endpoints ------------------

@app.get("/api/items/{item_id}/matches")
def get_matches_for_item(item_id: int, min_score: int = Query(25, ge=0, le=100)):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Item not found")

    target_item = row_to_dict(row)
    opposite_type = "found" if target_item["type"] == "lost" else "lost"

    candidate_rows = conn.execute(
        "SELECT * FROM items WHERE type = ? AND status != 'closed'",
        (opposite_type,)
    ).fetchall()
    conn.close()

    candidates = rows_to_dicts(candidate_rows)
    matches = find_matches_for_item(target_item, candidates, min_score=min_score, top_k=10)

    return {
        "target_item": target_item,
        "matches_count": len(matches),
        "matches": matches
    }


@app.get("/api/matches")
def get_all_matches(min_score: int = Query(35, ge=0, le=100)):
    """
    Returns automated match recommendations across all open lost and found items.
    """
    conn = get_db_connection()
    lost_rows = conn.execute(
        "SELECT * FROM items WHERE type = 'lost' AND status NOT IN ('returned', 'closed')"
    ).fetchall()
    found_rows = conn.execute(
        "SELECT * FROM items WHERE type = 'found' AND status NOT IN ('returned', 'closed')"
    ).fetchall()
    conn.close()

    lost_items = rows_to_dicts(lost_rows)
    found_items = rows_to_dicts(found_rows)

    matches = find_all_matches(lost_items, found_items, min_score=min_score, top_k=25)
    return {
        "total_lost_items": len(lost_items),
        "total_found_items": len(found_items),
        "matches_count": len(matches),
        "matches": matches
    }


@app.post("/api/match-custom")
def match_custom_query(payload: CustomMatchRequest):
    """
    Real-time matching simulator: user inputs a description/details to see matching items in the database.
    """
    conn = get_db_connection()
    opposite_type = "found" if payload.type.lower() == "lost" else "lost"
    rows = conn.execute(
        "SELECT * FROM items WHERE type = ? AND status NOT IN ('returned', 'closed')",
        (opposite_type,)
    ).fetchall()
    conn.close()

    candidates = rows_to_dicts(rows)
    query_item = {
        "type": payload.type.lower(),
        "title": payload.title,
        "description": payload.description,
        "category": payload.category,
        "location_name": payload.location_name or "",
        "date_occurred": payload.date_occurred or datetime.now().strftime("%Y-%m-%d")
    }

    matches = find_matches_for_item(query_item, candidates, min_score=20, top_k=10)
    return {
        "query": query_item,
        "matches_count": len(matches),
        "matches": matches
    }


# ------------------ Claims & Verification Endpoints ------------------

@app.get("/api/claims")
def get_claims(
    item_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None)
):
    conn = get_db_connection()
    query = """
    SELECT c.*, i.title as item_title, i.type as item_type, i.category as item_category,
           i.location_name as item_location, i.status as item_current_status, i.image_url as item_image_url
    FROM claims c
    JOIN items i ON c.item_id = i.id
    WHERE 1=1
    """
    params = []
    if item_id:
        query += " AND c.item_id = ?"
        params.append(item_id)
    if status:
        query += " AND c.verification_status = ?"
        params.append(status.lower())

    query += " ORDER BY c.id DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows_to_dicts(rows)


@app.get("/api/claims/{claim_id}")
def get_claim(claim_id: int):
    conn = get_db_connection()
    row = conn.execute("""
    SELECT c.*, i.title as item_title, i.type as item_type, i.category as item_category,
           i.location_name as item_location, i.status as item_current_status, i.secret_details as item_secret_details
    FROM claims c
    JOIN items i ON c.item_id = i.id
    WHERE c.id = ?
    """, (claim_id,)).fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Claim not found")
    return row_to_dict(row)


@app.post("/api/claims", status_code=status.HTTP_201_CREATED)
def submit_claim(payload: ClaimCreate):
    conn = get_db_connection()
    item_row = conn.execute("SELECT * FROM items WHERE id = ?", (payload.item_id,)).fetchone()
    if not item_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Item not found")

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO claims (
        item_id, claimant_name, claimant_email, claimant_phone, claimant_student_id,
        proof_description, proof_image_url, verification_status, admin_notes, created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', '', ?, ?)
    """, (
        payload.item_id,
        payload.claimant_name,
        payload.claimant_email,
        payload.claimant_phone or "",
        payload.claimant_student_id,
        payload.proof_description,
        payload.proof_image_url or "",
        now_str,
        now_str
    ))
    claim_id = cursor.lastrowid

    # Update item status to 'claim_pending' if it was open
    if item_row["status"] == "open":
        conn.execute("UPDATE items SET status = 'claim_pending' WHERE id = ?", (payload.item_id,))

    conn.commit()

    created_claim = row_to_dict(conn.execute("SELECT * FROM claims WHERE id = ?", (claim_id,)).fetchone())
    conn.close()

    log_activity(
        action="CLAIM_SUBMITTED",
        details=f"{payload.claimant_name} filed claim #{claim_id} for item #{payload.item_id} ('{item_row['title']}')",
        item_id=payload.item_id,
        claim_id=claim_id
    )

    return {
        "claim": created_claim,
        "message": "Ownership claim filed successfully! A campus staff administrator will verify your proof."
    }


@app.put("/api/claims/{claim_id}/verify")
def verify_claim(claim_id: int, payload: ClaimVerify):
    conn = get_db_connection()
    claim_row = conn.execute("SELECT * FROM claims WHERE id = ?", (claim_id,)).fetchone()
    if not claim_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Claim not found")

    item_id = claim_row["item_id"]
    new_verification_status = payload.verification_status.lower()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Update claim verification status and admin notes
    conn.execute("""
    UPDATE claims
    SET verification_status = ?, admin_notes = ?, updated_at = ?
    WHERE id = ?
    """, (new_verification_status, payload.admin_notes or "", now_str, claim_id))

    # If approved, update item status
    if new_verification_status == "approved":
        new_item_status = "returned" if payload.resolve_item else "claimed"
        conn.execute("UPDATE items SET status = ? WHERE id = ?", (new_item_status, item_id))
    elif new_verification_status == "rejected":
        # Check if other pending claims exist
        other_claims = conn.execute(
            "SELECT COUNT(*) FROM claims WHERE item_id = ? AND id != ? AND verification_status = 'pending'",
            (item_id, claim_id)
        ).fetchone()[0]
        if other_claims == 0:
            conn.execute("UPDATE items SET status = 'open' WHERE id = ?", (item_id,))

    conn.commit()

    updated_claim = row_to_dict(conn.execute("SELECT * FROM claims WHERE id = ?", (claim_id,)).fetchone())
    conn.close()

    log_activity(
        action=f"CLAIM_{new_verification_status.upper()}",
        details=f"Claim #{claim_id} for item #{item_id} was marked '{new_verification_status}'. Notes: {payload.admin_notes or 'None'}",
        item_id=item_id,
        claim_id=claim_id
    )

    return {
        "claim": updated_claim,
        "message": f"Claim status updated to '{new_verification_status}'."
    }


# ------------------ Statistics & Activity ------------------

@app.get("/api/stats")
def get_stats():
    conn = get_db_connection()
    total_items = conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
    total_lost = conn.execute("SELECT COUNT(*) FROM items WHERE type = 'lost'").fetchone()[0]
    total_found = conn.execute("SELECT COUNT(*) FROM items WHERE type = 'found'").fetchone()[0]
    total_returned = conn.execute("SELECT COUNT(*) FROM items WHERE status = 'returned'").fetchone()[0]
    active_claims = conn.execute("SELECT COUNT(*) FROM claims WHERE verification_status = 'pending'").fetchone()[0]
    total_claims = conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0]

    recovery_rate = round((total_returned / total_items * 100), 1) if total_items > 0 else 0.0

    # Category counts
    cat_rows = conn.execute("""
    SELECT category, COUNT(*) as count
    FROM items
    GROUP BY category
    ORDER BY count DESC
    """).fetchall()

    # Location hotspots
    loc_rows = conn.execute("""
    SELECT location_name, COUNT(*) as count
    FROM items
    GROUP BY location_name
    ORDER BY count DESC
    LIMIT 5
    """).fetchall()

    conn.close()
    return {
        "total_items": total_items,
        "total_lost": total_lost,
        "total_found": total_found,
        "total_returned": total_returned,
        "active_claims": active_claims,
        "total_claims": total_claims,
        "recovery_rate": recovery_rate,
        "categories": rows_to_dicts(cat_rows),
        "location_hotspots": rows_to_dicts(loc_rows)
    }


@app.get("/api/activity")
def get_activity_logs(limit: int = Query(15, ge=1, le=100)):
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT * FROM activity_logs ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return rows_to_dicts(rows)


# ------------------ Static Files & Frontend Mount ------------------

FRONTEND_DIST = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

if os.path.exists(FRONTEND_DIST):
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
elif os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
