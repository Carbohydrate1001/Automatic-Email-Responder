"""
Check rubric scores data in database.
"""

import sys
import json
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from models.database import get_db_connection


def check_rubric_data():
    """Check rubric scores data for a few emails."""

    with get_db_connection() as conn:
        # Get a few emails with rubric scores
        rows = conn.execute("""
            SELECT id, subject, classification_rubric_scores
            FROM emails
            WHERE classification_rubric_scores IS NOT NULL
            LIMIT 3
        """).fetchall()

        for row in rows:
            print(f"\n{'='*80}")
            print(f"Email ID: {row['id']}")
            print(f"Subject: {row['subject']}")
            print(f"\nClassification Rubric Scores:")

            if row['classification_rubric_scores']:
                data = json.loads(row['classification_rubric_scores'])
                print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    check_rubric_data()
