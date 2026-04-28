"""
Background email polling scheduler.
Automatically fetches new emails at regular intervals.
"""

import time
import threading
import logging
from datetime import datetime
from services.graph_service import GraphService
from services.classification_service import ClassificationService
from services.reply_service import ReplyService
from models.database import get_db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailScheduler:
    def __init__(self, poll_interval_seconds=300):  # Default: 5 minutes
        self.poll_interval = poll_interval_seconds
        self.running = False
        self.thread = None
        self.classification_svc = ClassificationService()
        self.reply_svc = ReplyService()

    def start(self):
        """Start the background polling thread."""
        if self.running:
            logger.warning("Scheduler already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.thread.start()
        logger.info(f"Email scheduler started (polling every {self.poll_interval}s)")

    def stop(self):
        """Stop the background polling thread."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=10)
        logger.info("Email scheduler stopped")

    def _poll_loop(self):
        """Main polling loop."""
        while self.running:
            try:
                self._fetch_all_users_emails()
            except Exception as e:
                logger.error(f"Error in polling loop: {e}", exc_info=True)

            # Sleep in small intervals to allow quick shutdown
            for _ in range(self.poll_interval):
                if not self.running:
                    break
                time.sleep(1)

    def _fetch_all_users_emails(self):
        """Fetch emails for all authenticated users."""
        try:
            with get_db_connection() as conn:
                # Get all users with valid tokens
                users = conn.execute("""
                    SELECT DISTINCT user_email, access_token
                    FROM user_sessions
                    WHERE access_token IS NOT NULL
                    AND expires_at > datetime('now')
                """).fetchall()

            if not users:
                logger.debug("No authenticated users found")
                return

            logger.info(f"Polling emails for {len(users)} user(s)")

            for user in users:
                try:
                    self._fetch_user_emails(user['user_email'], user['access_token'])
                except Exception as e:
                    logger.error(f"Failed to fetch emails for {user['user_email']}: {e}")

        except Exception as e:
            logger.error(f"Error fetching user list: {e}", exc_info=True)

    def _fetch_user_emails(self, user_email, access_token, top=10):
        """Fetch and process emails for a single user."""
        try:
            graph = GraphService(access_token)
            emails = graph.get_emails(top=top)

            if not emails:
                logger.debug(f"No new emails for {user_email}")
                return

            logger.info(f"Processing {len(emails)} emails for {user_email}")
            processed_count = 0

            for msg in emails:
                message_id = msg.get("id", "")

                # Check if already processed
                with get_db_connection() as conn:
                    existing = conn.execute(
                        "SELECT id FROM emails WHERE message_id = ?", (message_id,)
                    ).fetchone()

                if existing:
                    continue

                # Process new email
                subject = msg.get("subject", "(No Subject)")
                sender = msg.get("from", {}).get("emailAddress", {}).get("address", "unknown")
                received_at = msg.get("receivedDateTime", "")
                body = msg.get("body", {}).get("content", msg.get("bodyPreview", ""))

                classification = self.classification_svc.classify_email(subject, body)
                result = self.reply_svc.process_email(
                    message_id=message_id,
                    subject=subject,
                    sender=sender,
                    received_at=received_at,
                    body=body,
                    classification=classification,
                    graph_service=graph,
                    operator=user_email,
                    user_email=user_email,
                )

                processed_count += 1
                logger.info(f"Processed email {message_id}: {result.get('status')} - {result.get('category')}")

            if processed_count > 0:
                logger.info(f"Successfully processed {processed_count} new emails for {user_email}")

        except Exception as e:
            logger.error(f"Error fetching emails for {user_email}: {e}", exc_info=True)


# Global scheduler instance
_scheduler = None


def get_scheduler():
    """Get or create the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = EmailScheduler(poll_interval_seconds=300)  # 5 minutes
    return _scheduler
