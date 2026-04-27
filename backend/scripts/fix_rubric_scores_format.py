"""
Fix rubric scores format in database.
Converts old format (scores as integers) to new format (scores as {score, reasoning} dicts).
"""

import sys
import json
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from models.database import get_db_connection


def fix_rubric_scores_format():
    """Fix rubric scores format for all emails in database."""

    with get_db_connection() as conn:
        # Get all emails with rubric scores
        rows = conn.execute("""
            SELECT id, classification_rubric_scores, auto_send_rubric_scores
            FROM emails
            WHERE classification_rubric_scores IS NOT NULL
               OR auto_send_rubric_scores IS NOT NULL
        """).fetchall()

        print(f"Found {len(rows)} emails with rubric scores")

        fixed_count = 0

        for row in rows:
            email_id = row['id']
            classification_scores = row['classification_rubric_scores']
            auto_send_scores = row['auto_send_rubric_scores']

            updated = False

            # Fix classification_rubric_scores
            if classification_scores:
                try:
                    data = json.loads(classification_scores)
                    if 'scores' in data and isinstance(data['scores'], dict):
                        scores = data['scores']
                        needs_fix = False

                        # Check if any score is just an integer
                        for dim_name, dim_value in scores.items():
                            if not isinstance(dim_value, dict):
                                needs_fix = True
                                break

                        if needs_fix:
                            # Convert to new format
                            new_scores = {}
                            for dim_name, dim_value in scores.items():
                                if isinstance(dim_value, dict):
                                    # Already in correct format
                                    new_scores[dim_name] = dim_value
                                else:
                                    # Convert integer to {score, reasoning} format
                                    new_scores[dim_name] = {
                                        'score': int(dim_value),
                                        'reasoning': ''
                                    }

                            data['scores'] = new_scores
                            new_json = json.dumps(data, ensure_ascii=False)

                            conn.execute(
                                "UPDATE emails SET classification_rubric_scores = ? WHERE id = ?",
                                (new_json, email_id)
                            )
                            updated = True
                            print(f"  Fixed classification_rubric_scores for email {email_id}")

                except Exception as e:
                    print(f"  Error fixing classification_rubric_scores for email {email_id}: {e}")

            # Fix auto_send_rubric_scores
            if auto_send_scores:
                try:
                    data = json.loads(auto_send_scores)
                    if 'scores' in data and isinstance(data['scores'], dict):
                        scores = data['scores']
                        needs_fix = False

                        # Check if any score is just an integer
                        for dim_name, dim_value in scores.items():
                            if not isinstance(dim_value, dict):
                                needs_fix = True
                                break

                        if needs_fix:
                            # Convert to new format
                            new_scores = {}
                            for dim_name, dim_value in scores.items():
                                if isinstance(dim_value, dict):
                                    # Already in correct format
                                    new_scores[dim_name] = dim_value
                                else:
                                    # Convert integer to {score, reasoning} format
                                    new_scores[dim_name] = {
                                        'score': int(dim_value),
                                        'reasoning': ''
                                    }

                            data['scores'] = new_scores
                            new_json = json.dumps(data, ensure_ascii=False)

                            conn.execute(
                                "UPDATE emails SET auto_send_rubric_scores = ? WHERE id = ?",
                                (new_json, email_id)
                            )
                            updated = True
                            print(f"  Fixed auto_send_rubric_scores for email {email_id}")

                except Exception as e:
                    print(f"  Error fixing auto_send_rubric_scores for email {email_id}: {e}")

            if updated:
                fixed_count += 1

        conn.commit()
        print(f"\nFixed {fixed_count} emails")


if __name__ == '__main__':
    print("Fixing rubric scores format in database...")
    fix_rubric_scores_format()
    print("Done!")
