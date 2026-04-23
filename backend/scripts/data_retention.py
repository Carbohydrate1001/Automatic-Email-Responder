"""
Data Retention Script

Manages data lifecycle with configurable retention periods.
Supports automatic deletion, anonymization, and export of expired data.

Usage:
    python data_retention.py [--dry-run] [--config PATH] [--action ACTION]
"""

import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from models.database import get_db_connection
from models.audit_log import log_audit_event, AuditAction
from services.pii_service import get_pii_service, RedactionLevel
from utils.logger import get_logger


logger = get_logger('data_retention')


# Default retention periods (days)
DEFAULT_RETENTION = {
    'emails': 365,           # 1 year
    'replies': 365,          # 1 year
    'audit_log': 730,        # 2 years (compliance requirement)
    'pii_data': 180,         # 6 months
    'anonymized_data': 1095  # 3 years
}


class DataRetentionManager:
    """Manages data retention policies and cleanup."""

    def __init__(self, retention_config: Optional[Dict[str, int]] = None):
        """
        Initialize DataRetentionManager.

        Args:
            retention_config: Custom retention periods (days) per data type
        """
        self.retention = retention_config or DEFAULT_RETENTION
        self.pii_service = get_pii_service()

    def get_expired_emails(self, dry_run: bool = False) -> List[Dict]:
        """
        Find emails that have exceeded retention period.

        Args:
            dry_run: If True, only report without deleting

        Returns:
            List of expired email records
        """
        retention_days = self.retention.get('emails', 365)
        cutoff_date = (datetime.utcnow() - timedelta(days=retention_days)).isoformat()

        with get_db_connection() as conn:
            expired = conn.execute(
                """SELECT id, message_id, sender, subject, created_at
                   FROM emails
                   WHERE created_at < ?
                   ORDER BY created_at ASC""",
                (cutoff_date,)
            ).fetchall()

        result = [dict(row) for row in expired]

        logger.info("Found expired emails", {
            'count': len(result),
            'retention_days': retention_days,
            'cutoff_date': cutoff_date,
            'dry_run': dry_run
        })

        return result

    def delete_expired_data(self, dry_run: bool = False) -> Dict[str, int]:
        """
        Delete data that has exceeded retention period.

        Args:
            dry_run: If True, only report without deleting

        Returns:
            Dictionary with deletion counts
        """
        counts = {
            'emails_deleted': 0,
            'replies_deleted': 0,
            'audit_entries_deleted': 0
        }

        # Delete expired emails and related data
        email_retention = self.retention.get('emails', 365)
        email_cutoff = (datetime.utcnow() - timedelta(days=email_retention)).isoformat()

        audit_retention = self.retention.get('audit_log', 730)
        audit_cutoff = (datetime.utcnow() - timedelta(days=audit_retention)).isoformat()

        if dry_run:
            with get_db_connection() as conn:
                counts['emails_deleted'] = conn.execute(
                    "SELECT COUNT(*) as c FROM emails WHERE created_at < ?",
                    (email_cutoff,)
                ).fetchone()['c']

                counts['replies_deleted'] = conn.execute(
                    """SELECT COUNT(*) as c FROM replies
                       WHERE email_id IN (SELECT id FROM emails WHERE created_at < ?)""",
                    (email_cutoff,)
                ).fetchone()['c']

                counts['audit_entries_deleted'] = conn.execute(
                    "SELECT COUNT(*) as c FROM compliance_audit_log WHERE created_at < ?",
                    (audit_cutoff,)
                ).fetchone()['c']

            logger.info("Dry run - would delete", counts)
            return counts

        with get_db_connection() as conn:
            # Delete replies for expired emails
            cursor = conn.execute(
                """DELETE FROM replies
                   WHERE email_id IN (SELECT id FROM emails WHERE created_at < ?)""",
                (email_cutoff,)
            )
            counts['replies_deleted'] = cursor.rowcount

            # Delete expired emails
            cursor = conn.execute(
                "DELETE FROM emails WHERE created_at < ?",
                (email_cutoff,)
            )
            counts['emails_deleted'] = cursor.rowcount

            # Delete expired audit entries
            cursor = conn.execute(
                "DELETE FROM compliance_audit_log WHERE created_at < ?",
                (audit_cutoff,)
            )
            counts['audit_entries_deleted'] = cursor.rowcount

            conn.commit()

        # Log the retention action
        log_audit_event(
            action=AuditAction.DATA_DELETED,
            operator='data_retention_script',
            details={
                'retention_config': self.retention,
                'deletion_counts': counts,
                'email_cutoff': email_cutoff,
                'audit_cutoff': audit_cutoff
            }
        )

        logger.info("Data retention cleanup completed", counts)
        return counts

    def anonymize_expired_data(self, dry_run: bool = False) -> Dict[str, int]:
        """
        Anonymize expired data instead of deleting (keep metadata, remove PII).

        Args:
            dry_run: If True, only report without anonymizing

        Returns:
            Dictionary with anonymization counts
        """
        pii_retention = self.retention.get('pii_data', 180)
        cutoff_date = (datetime.utcnow() - timedelta(days=pii_retention)).isoformat()

        with get_db_connection() as conn:
            expired = conn.execute(
                """SELECT id, subject, sender, body
                   FROM emails
                   WHERE created_at < ? AND sender NOT LIKE '%[ANONYMIZED]%'""",
                (cutoff_date,)
            ).fetchall()

        count = 0

        if dry_run:
            logger.info("Dry run - would anonymize", {'count': len(expired)})
            return {'emails_anonymized': len(expired)}

        with get_db_connection() as conn:
            for row in expired:
                email_id = row['id']

                # Redact PII from subject and body
                redacted_subject, _ = self.pii_service.redact_pii(
                    row['subject'] or '', RedactionLevel.FULL
                )
                redacted_body, _ = self.pii_service.redact_pii(
                    row['body'] or '', RedactionLevel.FULL
                )

                # Anonymize sender
                anonymized_sender = '[ANONYMIZED]'

                conn.execute(
                    """UPDATE emails
                       SET subject = ?, sender = ?, body = ?
                       WHERE id = ?""",
                    (redacted_subject, anonymized_sender, redacted_body, email_id)
                )

                # Anonymize replies
                conn.execute(
                    """UPDATE replies
                       SET reply_text = '[ANONYMIZED]'
                       WHERE email_id = ?""",
                    (email_id,)
                )

                count += 1

            conn.commit()

        # Log the anonymization
        log_audit_event(
            action=AuditAction.DATA_ANONYMIZED,
            operator='data_retention_script',
            details={
                'emails_anonymized': count,
                'cutoff_date': cutoff_date
            }
        )

        logger.info("Data anonymization completed", {'count': count})
        return {'emails_anonymized': count}

    def right_to_be_forgotten(
        self,
        sender_email: str,
        operator: str = "system"
    ) -> Dict[str, int]:
        """
        Delete all data for a specific user (GDPR right to be forgotten).

        Args:
            sender_email: Email address of the user
            operator: Who initiated the request

        Returns:
            Dictionary with deletion counts
        """
        counts = {
            'emails_deleted': 0,
            'replies_deleted': 0,
            'audit_entries_anonymized': 0
        }

        with get_db_connection() as conn:
            # Find all emails from this sender
            emails = conn.execute(
                "SELECT id FROM emails WHERE sender LIKE ?",
                (f'%{sender_email}%',)
            ).fetchall()

            email_ids = [row['id'] for row in emails]

            if email_ids:
                placeholders = ','.join('?' * len(email_ids))

                # Delete replies
                cursor = conn.execute(
                    f"DELETE FROM replies WHERE email_id IN ({placeholders})",
                    email_ids
                )
                counts['replies_deleted'] = cursor.rowcount

                # Delete emails
                cursor = conn.execute(
                    f"DELETE FROM emails WHERE id IN ({placeholders})",
                    email_ids
                )
                counts['emails_deleted'] = cursor.rowcount

                # Anonymize audit log entries (keep for compliance, remove PII)
                cursor = conn.execute(
                    f"""UPDATE compliance_audit_log
                        SET details = '[REDACTED - RIGHT TO BE FORGOTTEN]'
                        WHERE email_id IN ({placeholders})""",
                    email_ids
                )
                counts['audit_entries_anonymized'] = cursor.rowcount

            conn.commit()

        # Log the action
        log_audit_event(
            action=AuditAction.DATA_DELETED,
            operator=operator,
            details={
                'reason': 'right_to_be_forgotten',
                'sender': '[REDACTED]',
                'deletion_counts': counts
            }
        )

        logger.info("Right to be forgotten executed", {
            'operator': operator,
            'counts': counts
        })

        return counts

    def export_user_data(
        self,
        sender_email: str,
        output_path: str,
        operator: str = "system"
    ) -> Dict[str, Any]:
        """
        Export all data for a specific user (GDPR data portability).

        Args:
            sender_email: Email address of the user
            output_path: Path to save exported data
            operator: Who initiated the request

        Returns:
            Export summary
        """
        with get_db_connection() as conn:
            emails = conn.execute(
                """SELECT e.*, r.reply_text, r.sent_at as reply_sent_at
                   FROM emails e
                   LEFT JOIN replies r ON e.id = r.email_id
                   WHERE e.sender LIKE ?
                   ORDER BY e.created_at DESC""",
                (f'%{sender_email}%',)
            ).fetchall()

        export_data = {
            'export_date': datetime.utcnow().isoformat(),
            'user_email': sender_email,
            'total_records': len(emails),
            'records': [dict(row) for row in emails]
        }

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        # Log the export
        log_audit_event(
            action=AuditAction.DATA_EXPORTED,
            operator=operator,
            details={
                'sender': '[REDACTED]',
                'records_exported': len(emails),
                'output_path': str(output_path)
            }
        )

        logger.info("User data exported", {
            'records': len(emails),
            'output_path': str(output_path)
        })

        return {
            'records_exported': len(emails),
            'output_path': str(output_path)
        }

    def get_retention_report(self) -> Dict[str, Any]:
        """
        Generate data retention status report.

        Returns:
            Report with data age statistics and upcoming expirations
        """
        report = {
            'retention_config': self.retention,
            'data_statistics': {},
            'upcoming_expirations': {}
        }

        with get_db_connection() as conn:
            # Email statistics
            email_stats = conn.execute(
                """SELECT
                       COUNT(*) as total,
                       MIN(created_at) as oldest,
                       MAX(created_at) as newest
                   FROM emails"""
            ).fetchone()

            report['data_statistics']['emails'] = {
                'total': email_stats['total'],
                'oldest': email_stats['oldest'],
                'newest': email_stats['newest']
            }

            # Count emails expiring in next 30 days
            email_retention = self.retention.get('emails', 365)
            expiry_window = (
                datetime.utcnow() - timedelta(days=email_retention - 30)
            ).isoformat()

            expiring_soon = conn.execute(
                "SELECT COUNT(*) as c FROM emails WHERE created_at < ?",
                (expiry_window,)
            ).fetchone()['c']

            report['upcoming_expirations']['emails_expiring_30d'] = expiring_soon

        return report


def main():
    parser = argparse.ArgumentParser(description='Data retention management')
    parser.add_argument(
        '--action',
        choices=['delete', 'anonymize', 'report', 'forget', 'export'],
        default='report',
        help='Action to perform'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without executing'
    )
    parser.add_argument(
        '--email',
        help='User email for forget/export actions'
    )
    parser.add_argument(
        '--output',
        default='../reports/user_data_export.json',
        help='Output path for export action'
    )

    args = parser.parse_args()

    manager = DataRetentionManager()

    if args.action == 'report':
        report = manager.get_retention_report()
        print(json.dumps(report, indent=2, ensure_ascii=False))

    elif args.action == 'delete':
        counts = manager.delete_expired_data(dry_run=args.dry_run)
        prefix = "[DRY RUN] " if args.dry_run else ""
        print(f"{prefix}Deletion results:")
        for key, value in counts.items():
            print(f"  {key}: {value}")

    elif args.action == 'anonymize':
        counts = manager.anonymize_expired_data(dry_run=args.dry_run)
        prefix = "[DRY RUN] " if args.dry_run else ""
        print(f"{prefix}Anonymization results:")
        for key, value in counts.items():
            print(f"  {key}: {value}")

    elif args.action == 'forget':
        if not args.email:
            print("Error: --email required for forget action")
            return
        counts = manager.right_to_be_forgotten(args.email)
        print(f"Right to be forgotten executed for {args.email}:")
        for key, value in counts.items():
            print(f"  {key}: {value}")

    elif args.action == 'export':
        if not args.email:
            print("Error: --email required for export action")
            return
        script_dir = Path(__file__).parent
        output_path = script_dir / args.output
        result = manager.export_user_data(args.email, str(output_path))
        print(f"Data exported: {result['records_exported']} records")
        print(f"Output: {result['output_path']}")


if __name__ == '__main__':
    main()
