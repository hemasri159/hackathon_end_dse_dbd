import os
from datetime import datetime, timedelta
from database import get_db_connection, init_db, log_activity

def seed_database():
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if already seeded
    cursor.execute("SELECT COUNT(*) FROM locations")
    if cursor.fetchone()[0] > 0:
        print("Database already seeded.")
        conn.close()
        return

    print("Seeding campus locations...")
    locations = [
        ("Central Library", "Main Building", "1st Floor & 2nd Floor Study", "Quiet reading areas, computer labs, front desk"),
        ("Student Activity Center / Union", "SAC Building", "Ground Floor & Food Court", "Student lounges, game room, club desks"),
        ("Campus Dining Hall", "Dining Pavilion", "Cafeteria & Seating", "Main meal area, tray returns, patio seating"),
        ("Science & Technology Complex", "STC Wing B", "Labs 301-305 & Hallways", "Physics and engineering labs, lecture halls"),
        ("North Campus Recreation & Gym", "Recreation Center", "Fitness Floor & Lockers", "Basketball courts, weight room, front check-in"),
        ("Engineering Quad & Maker Lab", "Engineering Hall", "Maker Workshop & Courtyard", "3D printing lab, soldering stations, benches"),
        ("University Shuttle Stop #2", "Transit Hub", "East Loop Stop", "Campus bus pickup zone with covered bench"),
        ("East Campus Dormitories", "Residence Hall A", "Common Room & Lobby", "Dorm lounge, laundry room, mail room"),
    ]

    cursor.executemany(
        "INSERT INTO locations (name, building, zone, description) VALUES (?, ?, ?, ?)",
        locations
    )

    # Seed Items
    today = datetime.now()
    d_today = today.strftime("%Y-%m-%d")
    d_yesterday = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    d_2days = (today - timedelta(days=2)).strftime("%Y-%m-%d")
    d_3days = (today - timedelta(days=3)).strftime("%Y-%m-%d")
    d_5days = (today - timedelta(days=5)).strftime("%Y-%m-%d")

    items = [
        # Pair 1: AirPods Pro (Lost & Found matching)
        (
            "lost",
            "Apple AirPods Pro 2 in White MagSafe Case",
            "Lost my white Apple AirPods Pro case with charging case. Has a small faint scratch on the back near hinge. Left on 2nd-floor quiet study table near window.",
            "Electronics",
            1, "Central Library",
            d_3days, d_3days, "claim_pending",
            "Alex Rivera", "alex.rivera@campus.edu", "555-0142",
            "Has a tiny Pikachu decal on the bottom and serial ending in 9J2",
            "https://images.unsplash.com/photo-1600294037681-c80b4cb5b434?w=500&auto=format&fit=crop&q=60"
        ),
        (
            "found",
            "White Wireless Earbuds (Apple AirPods) in Case",
            "Found Apple AirPods in white charging case on desk 24 in 2nd-floor quiet study room. Handed over to library circulation desk.",
            "Electronics",
            1, "Central Library",
            d_3days, d_3days, "claim_pending",
            "Sarah Collins (Librarian)", "scollins@campus.edu", "555-0100",
            "Small yellow character sticker on bottom, engraving visible",
            "https://images.unsplash.com/photo-1600294037681-c80b4cb5b434?w=500&auto=format&fit=crop&q=60"
        ),

        # Pair 2: Leather Wallet
        (
            "lost",
            "Black Leather Bi-fold Wallet with Student ID",
            "Black leather wallet lost during lunch rush. Contains my student ID card, driver's license, and some cash.",
            "Bags & Wallets",
            3, "Campus Dining Hall",
            d_2days, d_2days, "open",
            "David Kim", "dkim@campus.edu", "555-0188",
            "Student ID card for David Kim (ID #2024881), gym card",
            "https://images.unsplash.com/photo-1627123424574-724758594e93?w=500&auto=format&fit=crop&q=60"
        ),
        (
            "found",
            "Dark Brown/Black Leather Men's Wallet",
            "Found near the tray return station in dining hall. Contains student identification card and cards.",
            "Bags & Wallets",
            3, "Campus Dining Hall",
            d_2days, d_2days, "open",
            "Marcus Green (Staff)", "mgreen@campus.edu", "555-0112",
            "Cards with initials D.K. inside",
            "https://images.unsplash.com/photo-1627123424574-724758594e93?w=500&auto=format&fit=crop&q=60"
        ),

        # Pair 3: Hydro Flask Water Bottle
        (
            "lost",
            "Hydro Flask 32oz Water Bottle - Forest Green",
            "Dark green insulated Hydro Flask bottle. Has multiple national park stickers including Yosemite and Zion.",
            "Bottles & Containers",
            4, "Science & Technology Complex",
            d_3days, d_2days, "open",
            "Maya Patel", "mpatel@campus.edu", "555-0193",
            "Small dent on the bottom rim, Yosemite sticker on left side",
            "https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=500&auto=format&fit=crop&q=60"
        ),
        (
            "found",
            "Green Metal Water Flask with Outdoor Stickers",
            "Found on front bench outside Science lecture hall 101. Forest green metal tumbler covered in stickers.",
            "Bottles & Containers",
            4, "Science & Technology Complex",
            d_3days, d_2days, "open",
            "Ethan Wright (TA)", "ewright@campus.edu", "555-0177",
            "Stickers: Yosemite, Outdoor hiking trails",
            "https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=500&auto=format&fit=crop&q=60"
        ),

        # Pair 4: Toyota Car Key Fob
        (
            "lost",
            "Toyota Key Fob on Blue Campus Lanyard",
            "Lost my car keys with a Toyota electronic key fob and a blue university lanyard with a barcode tag.",
            "Keys",
            5, "North Campus Recreation & Gym",
            d_yesterday, d_yesterday, "open",
            "Jordan Lee", "jlee@campus.edu", "555-0165",
            "Toyota 3-button fob, gym scan card barcode ending in 482",
            "https://images.unsplash.com/photo-1582139329536-e7284fece509?w=500&auto=format&fit=crop&q=60"
        ),
        (
            "found",
            "Car Key (Toyota) with Blue Strap and Gym Barcode",
            "Turned in to gym front desk. Toyota key fob attached to a blue woven strap lanyard.",
            "Keys",
            5, "North Campus Recreation & Gym",
            d_yesterday, d_yesterday, "open",
            "Chloe Vance (Gym Staff)", "cvance@campus.edu", "555-0120",
            "Planet Fitness tag barcode attached",
            "https://images.unsplash.com/photo-1582139329536-e7284fece509?w=500&auto=format&fit=crop&q=60"
        ),

        # Pair 5: Calculus Textbook
        (
            "lost",
            "Calculus: Early Transcendentals Hardcover Textbook",
            "Stewart Calculus 8th edition textbook. Left on round coffee table in SAC lounge.",
            "Books & Stationery",
            2, "Student Activity Center / Union",
            d_5days, d_5days, "open",
            "Liam Johnson", "ljohnson@campus.edu", "555-0149",
            "Inside front cover has name Liam J. and chapter 4 highlighted in yellow",
            "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=500&auto=format&fit=crop&q=60"
        ),
        (
            "found",
            "Hardcover Mathematics Calculus Textbook",
            "Found Stewart calculus book left in SAC second floor study lounge.",
            "Books & Stationery",
            2, "Student Activity Center / Union",
            d_5days, d_5days, "open",
            "Noah Miller", "nmiller@campus.edu", "555-0131",
            "Contains yellow highlighting and notes on first page",
            "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=500&auto=format&fit=crop&q=60"
        ),

        # Pair 6: Returned / Verified Example
        (
            "lost",
            "Navy Blue The North Face Backpack",
            "Navy blue backpack containing Dell XPS laptop and notes. Lost in library ground floor.",
            "Bags & Wallets",
            1, "Central Library",
            d_5days, d_5days, "returned",
            "Emily Watson", "ewatson@campus.edu", "555-0199",
            "Laptop serial #DXP-9920",
            "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=500&auto=format&fit=crop&q=60"
        ),
        (
            "found",
            "Navy Blue North Face Backpack with Laptop",
            "Found under study table 12 on ground floor of Central Library.",
            "Bags & Wallets",
            1, "Central Library",
            d_5days, d_5days, "returned",
            "Library Security Desk", "security@campus.edu", "555-0111",
            "Owner verified and picked up successfully",
            "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=500&auto=format&fit=crop&q=60"
        ),

        # Single Lost / Found Items
        (
            "lost",
            "Silver Casio Vintage Digital Watch (A168)",
            "Retro stainless steel Casio watch with light blue dial ring. Fell off while working on breadboard in Maker Lab.",
            "Jewelry & Accessories",
            6, "Engineering Quad & Maker Lab",
            d_yesterday, d_yesterday, "open",
            "Ryan Park", "rpark@campus.edu", "555-0155",
            "Slight scratch near the 12 o'clock clasp",
            "https://images.unsplash.com/photo-1524805444758-089113d48a6d?w=500&auto=format&fit=crop&q=60"
        ),
        (
            "found",
            "Stainless Steel Digital Wristwatch",
            "Turned in from maker lab workbench #3. Classic digital metal watch in working condition.",
            "Jewelry & Accessories",
            6, "Engineering Quad & Maker Lab",
            d_today, d_today, "open",
            "Sam Davis (Tech)", "sdavis@campus.edu", "555-0160",
            "Silver band Casio illuminate",
            "https://images.unsplash.com/photo-1524805444758-089113d48a6d?w=500&auto=format&fit=crop&q=60"
        ),
        (
            "lost",
            "TI-84 Plus CE Graphing Calculator in Black",
            "Black Texas Instruments graphing calculator with slide cover. Lost in STC Lab 301.",
            "Electronics",
            4, "Science & Technology Complex",
            d_today, d_today, "open",
            "Jessica Taylor", "jtaylor@campus.edu", "555-0144",
            "Battery cover has my initials JT in silver sharpie",
            "https://images.unsplash.com/photo-1594980596870-8aa52a78d8cd?w=500&auto=format&fit=crop&q=60"
        ),
        (
            "found",
            "Red Wool Winter Scarf",
            "Knitted red scarf found on shuttle bus seat during morning run.",
            "Clothing",
            7, "University Shuttle Stop #2",
            d_today, d_today, "open",
            "Driver Bob", "transit@campus.edu", "555-0105",
            "Handmade knit pattern with fringes",
            "https://images.unsplash.com/photo-1607083206869-4c7672e72a8a?w=500&auto=format&fit=crop&q=60"
        )
    ]

    cursor.executemany("""
    INSERT INTO items (
        type, title, description, category, location_id, location_name,
        date_occurred, date_reported, status, reporter_name, reporter_email,
        reporter_phone, secret_details, image_url
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, items)

    # Seed Sample Claim on Item #2 (Found AirPods)
    cursor.execute("""
    INSERT INTO claims (
        item_id, claimant_name, claimant_email, claimant_phone,
        claimant_student_id, proof_description, proof_image_url,
        verification_status, admin_notes, created_at, updated_at
    ) VALUES (
        2,
        'Alex Rivera',
        'alex.rivera@campus.edu',
        '555-0142',
        'STU-882914',
        'I have the original Apple Store purchase receipt matching serial #H829J2. The charging case also has a small Pikachu sticker on the bottom underneath the Lightning port.',
        'https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=500&auto=format&fit=crop&q=60',
        'pending',
        'Claimant submitted photo proof of Apple receipt and provided matching sticker description. Pending in-person ID verification.',
        ?, ?
    )
    """, (d_yesterday + " 14:30:00", d_yesterday + " 14:30:00"))

    # Seed Activity Logs
    cursor.execute("""
    INSERT INTO activity_logs (action, item_id, claim_id, details, created_at)
    VALUES ('ITEM_REPORTED', 1, NULL, 'Alex Rivera reported Lost Apple AirPods Pro 2', ?)
    """, (d_3days + " 10:15:00",))

    cursor.execute("""
    INSERT INTO activity_logs (action, item_id, claim_id, details, created_at)
    VALUES ('ITEM_REPORTED', 2, NULL, 'Sarah Collins reported Found AirPods at Central Library', ?)
    """, (d_3days + " 12:45:00",))

    cursor.execute("""
    INSERT INTO activity_logs (action, item_id, claim_id, details, created_at)
    VALUES ('CLAIM_SUBMITTED', 2, 1, 'Alex Rivera submitted verification claim for Found AirPods #2', ?)
    """, (d_yesterday + " 14:30:00",))

    cursor.execute("""
    INSERT INTO activity_logs (action, item_id, claim_id, details, created_at)
    VALUES ('ITEM_RETURNED', 11, NULL, 'Emily Watson collected returned North Face Backpack after ID verification', ?)
    """, (d_today + " 09:00:00",))

    conn.commit()
    conn.close()
    print("Database seeding completed successfully!")


if __name__ == "__main__":
    seed_database()
