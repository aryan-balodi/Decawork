"""Database setup and management for the IT Admin Panel."""

import aiosqlite
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "admin_panel.db")


async def get_db():
    """Get a database connection."""
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def init_db():
    """Initialize database tables."""
    db = await get_db()
    try:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                role TEXT NOT NULL DEFAULT 'employee',
                department TEXT NOT NULL DEFAULT 'General',
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL,
                password_reset_required INTEGER NOT NULL DEFAULT 0,
                temp_password TEXT
            );

            CREATE TABLE IF NOT EXISTS licenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                software TEXT NOT NULL,
                total_seats INTEGER NOT NULL,
                icon TEXT DEFAULT '📦'
            );

            CREATE TABLE IF NOT EXISTS license_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                license_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                assigned_at TEXT NOT NULL,
                FOREIGN KEY (license_id) REFERENCES licenses(id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(license_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                details TEXT,
                timestamp TEXT NOT NULL
            );
        """)
        await db.commit()
    finally:
        await db.close()


async def seed_db():
    """Seed database with sample data if empty."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        count = (await cursor.fetchone())[0]
        if count > 0:
            return  # Already seeded

        now = datetime.now().isoformat()

        # Seed users
        users = [
            ("Alice Johnson", "alice@company.com", "admin", "Engineering", "active", now, 0, None),
            ("Bob Smith", "bob@company.com", "employee", "Marketing", "active", now, 0, None),
            ("Carol Davis", "carol@company.com", "employee", "Engineering", "active", now, 0, None),
            ("David Wilson", "david@company.com", "manager", "Sales", "active", now, 0, None),
            ("Eve Martinez", "eve@company.com", "contractor", "Design", "disabled", now, 0, None),
            ("Frank Brown", "frank@company.com", "employee", "HR", "active", now, 0, None),
            ("Grace Lee", "grace@company.com", "employee", "Engineering", "active", now, 0, None),
            ("Henry Taylor", "henry@company.com", "manager", "Finance", "active", now, 0, None),
        ]
        await db.executemany(
            "INSERT INTO users (name, email, role, department, status, created_at, password_reset_required, temp_password) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            users,
        )

        # Seed licenses
        licenses = [
            ("Microsoft 365", 10, "🏢"),
            ("Slack Pro", 15, "💬"),
            ("Jira", 8, "📋"),
            ("GitHub Enterprise", 12, "🐙"),
            ("Figma", 5, "🎨"),
        ]
        await db.executemany(
            "INSERT INTO licenses (software, total_seats, icon) VALUES (?, ?, ?)",
            licenses,
        )

        # Seed some license assignments
        assignments = [
            (1, 1, now),  # Alice -> Microsoft 365
            (1, 2, now),  # Bob -> Microsoft 365
            (1, 3, now),  # Carol -> Microsoft 365
            (2, 1, now),  # Alice -> Slack Pro
            (2, 2, now),  # Bob -> Slack Pro
            (2, 3, now),  # Carol -> Slack Pro
            (2, 4, now),  # David -> Slack Pro
            (3, 3, now),  # Carol -> Jira
            (3, 7, now),  # Grace -> Jira
            (4, 1, now),  # Alice -> GitHub Enterprise
            (4, 3, now),  # Carol -> GitHub Enterprise
            (4, 7, now),  # Grace -> GitHub Enterprise
            (5, 3, now),  # Carol -> Figma
        ]
        await db.executemany(
            "INSERT INTO license_assignments (license_id, user_id, assigned_at) VALUES (?, ?, ?)",
            assignments,
        )

        # Seed activity log
        activities = [
            ("User Created", "Created user alice@company.com", now),
            ("User Created", "Created user bob@company.com", now),
            ("License Assigned", "Assigned Microsoft 365 to alice@company.com", now),
            ("License Assigned", "Assigned Slack Pro to carol@company.com", now),
            ("Account Disabled", "Disabled account for eve@company.com", now),
        ]
        await db.executemany(
            "INSERT INTO activity_log (action, details, timestamp) VALUES (?, ?, ?)",
            activities,
        )

        await db.commit()
    finally:
        await db.close()
