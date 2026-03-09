"""
Reply generation and email processing service.
Generates GPT reply drafts and routes emails based on confidence threshold.
"""

from datetime import datetime, timezone
from openai import OpenAI
from config import Config
from models.database import get_db_connection

REPLY_SYSTEM_PROMPT = """You are a professional customer service representative for a logistics and trade company.
Write a clear, polite, and helpful reply email to the customer based on the email content and its identified category.
Keep the reply concise (3-5 sentences), professional, and empathetic.
Do NOT use placeholders like [tracking number] — acknowledge the inquiry and explain next steps generically.
Write in the same language as the customer's email."""


class ReplyService:
    """Generates reply drafts and orchestrates the full email processing pipeline."""

    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY, base_url=Config.OPENAI_BASE_URL)
        self.model = Config.OPENAI_MODEL
        self.threshold = Config.CONFIDENCE_THRESHOLD

    def generate_reply(self, subject: str, body: str, category: str, reasoning: str) -> str:
        """Generate a professional reply draft for the given email."""
        user_content = (
            f"Customer Email Subject: {subject}\n\n"
            f"Customer Email Body:\n{body[:3000]}\n\n"
            f"Identified Category: {category}\n"
            f"Classification Reasoning: {reasoning}"
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": REPLY_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.4,
            max_tokens=500,
        )

        return response.choices[0].message.content.strip()

    def process_email(
        self,
        message_id: str,
        subject: str,
        sender: str,
        received_at: str,
        body: str,
        classification: dict,
        graph_service=None,
        operator: str = "system",
    ) -> dict:
        """
        Full pipeline: persist email + reply, decide auto-send or pending_review.
        Returns the saved email record dict.
        """
        category = classification["category"]
        confidence = classification["confidence"]
        reasoning = classification.get("reasoning", "")

        reply_text = self.generate_reply(subject, body, category, reasoning)

        status = "auto_sent" if confidence >= self.threshold else "pending_review"
        sent_at = None

        if status == "auto_sent" and graph_service is not None:
            graph_service.send_reply(message_id, reply_text)
            graph_service.mark_as_read(message_id)
            sent_at = datetime.now(timezone.utc).isoformat()

        with get_db_connection() as conn:
            # Upsert email record
            conn.execute(
                """
                INSERT INTO emails (message_id, subject, sender, received_at, body,
                                    category, confidence, reasoning, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(message_id) DO UPDATE SET
                    category=excluded.category,
                    confidence=excluded.confidence,
                    reasoning=excluded.reasoning,
                    status=excluded.status
                """,
                (message_id, subject, sender, received_at, body,
                 category, confidence, reasoning, status),
            )
            email_row = conn.execute(
                "SELECT id FROM emails WHERE message_id = ?", (message_id,)
            ).fetchone()
            email_id = email_row["id"]

            # Save reply
            conn.execute(
                "INSERT INTO replies (email_id, reply_text, sent_at) VALUES (?, ?, ?)",
                (email_id, reply_text, sent_at),
            )

            # Audit log
            conn.execute(
                "INSERT INTO audit_log (email_id, action, operator) VALUES (?, ?, ?)",
                (email_id, status, operator),
            )
            conn.commit()

        return {
            "id": email_id,
            "message_id": message_id,
            "subject": subject,
            "sender": sender,
            "received_at": received_at,
            "category": category,
            "confidence": confidence,
            "status": status,
            "reply_text": reply_text,
        }
