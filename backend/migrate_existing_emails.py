"""
One-time migration script to assign existing emails to centauric47@outlook.com
Run this once after deploying the user isolation fix.
"""

import sqlite3
from config import Config
from models.database import init_db

def migrate_existing_emails():
    """Assign all existing emails with NULL user_email to centauric47@outlook.com"""

    # First, ensure the user_email column exists
    print("Running database initialization to ensure user_email column exists...")
    init_db()
    print("Database schema updated.")

    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row

    try:
        # Count emails with NULL user_email
        null_count = conn.execute(
            "SELECT COUNT(*) as cnt FROM emails WHERE user_email IS NULL"
        ).fetchone()["cnt"]

        print(f"Found {null_count} emails with NULL user_email")

        if null_count == 0:
            print("No emails to migrate. All emails already have user_email assigned.")
            return

        # Update all NULL user_email to centauric47@outlook.com
        conn.execute(
            """UPDATE emails
               SET user_email = 'centauric47@outlook.com'
               WHERE user_email IS NULL"""
        )

        conn.commit()

        # Verify the update
        updated_count = conn.execute(
            "SELECT COUNT(*) as cnt FROM emails WHERE user_email = 'centauric47@outlook.com'"
        ).fetchone()["cnt"]

        print(f"Successfully migrated {null_count} emails to centauric47@outlook.com")
        print(f"Total emails for centauric47@outlook.com: {updated_count}")

    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("  Email User Migration Script")
    print("  Assigning existing emails to: centauric47@outlook.com")
    print("=" * 60)

    migrate_existing_emails()

    print("\nMigration complete!")
