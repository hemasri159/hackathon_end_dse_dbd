import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "lost_and_found.db")


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Locations Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        building TEXT NOT NULL,
        zone TEXT,
        description TEXT
    );
    """)

    # 2. Items Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL CHECK(type IN ('lost', 'found')),
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        category TEXT NOT NULL,
        location_id INTEGER,
        location_name TEXT NOT NULL,
        date_occurred TEXT NOT NULL,
        date_reported TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open', 'claim_pending', 'claimed', 'returned', 'closed')),
        reporter_name TEXT NOT NULL,
        reporter_email TEXT NOT NULL,
        reporter_phone TEXT,
        secret_details TEXT,
        image_url TEXT,
        FOREIGN KEY (location_id) REFERENCES locations (id) ON DELETE SET NULL
    );
    """)

    # 3. Claims Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS claims (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER NOT NULL,
        claimant_name TEXT NOT NULL,
        claimant_email TEXT NOT NULL,
        claimant_phone TEXT,
        claimant_student_id TEXT NOT NULL,
        proof_description TEXT NOT NULL,
        proof_image_url TEXT,
        verification_status TEXT NOT NULL DEFAULT 'pending' CHECK(verification_status IN ('pending', 'approved', 'rejected', 'more_info_needed')),
        admin_notes TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (item_id) REFERENCES items (id) ON DELETE CASCADE
    );
    """)

    # 4. Activity Logs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS activity_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT NOT NULL,
        item_id INTEGER,
        claim_id INTEGER,
        details TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (item_id) REFERENCES items (id) ON DELETE SET NULL,
        FOREIGN KEY (claim_id) REFERENCES claims (id) ON DELETE SET NULL
    );
    """)

    conn.commit()
    conn.close()


def log_activity(action: str, details: str, item_id: Optional[int] = None, claim_id: Optional[int] = None):
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO activity_logs (action, item_id, claim_id, details, created_at) VALUES (?, ?, ?, ?, ?)",
        (action, item_id, claim_id, details, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
