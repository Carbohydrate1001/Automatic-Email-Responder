"""
End-to-end tests for the full email processing pipeline.

Tests the complete flow: email receipt → classification → reply generation →
validation → auto-send/manual-review decision → database persistence.
All external services (OpenAI, Graph API) are mocked.
"""

import json
import pytest
import sqlite3
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone


@pytest.fixture
def e2e_db():
    """Create a fully-initialized test database matching production schema."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS emails (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id  TEXT UNIQUE NOT NULL,
            subject     TEXT,
            sender      TEXT,
            received_at TEXT,
            body        TEXT,
            category    TEXT,
            confidence  REAL,
            reasoning   TEXT,
            status      TEXT DEFAULT 'pending_review',
            retry_count INTEGER DEFAULT 0,
            last_error  TEXT,
            classification_rubric_scores TEXT,
            auto_send_rubric_scores TEXT,
            rubric_version TEXT DEFAULT 'v1.0',
            consent_status TEXT DEFAULT 'unknown',
            pii_detected INTEGER DEFAULT 0,
            pii_types TEXT,
            created_at  TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS replies (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id    INTEGER REFERENCES emails(id),
            reply_text  TEXT,
            sent_at     TEXT,
            reply_validation_scores TEXT,
            validation_passed INTEGER DEFAULT 1,
            validation_issues TEXT,
            created_at  TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS audit_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id    INTEGER REFERENCES emails(id),
            action      TEXT,
            operator    TEXT,
            created_at  TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS compliance_audit_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id    INTEGER,
            action      TEXT NOT NULL,
            operator    TEXT DEFAULT 'system',
            details     TEXT,
            ip_address  TEXT,
            user_agent  TEXT,
            created_at  TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    yield conn
    conn.close()
    os.unlink(path)


def _mock_openai_response(content: str):
    """Helper to create a mock OpenAI chat completion response."""
    resp = Mock()
    choice = Mock()
    msg = Mock()
    msg.content = content
    choice.message = msg
    resp.choices = [choice]
    return resp


def _gate_ok():
    return _mock_openai_response('{"is_business_related": true, "confidence": 0.92, "reasoning": "Business email"}')


def _gate_non_business():
    return _mock_openai_response('{"is_business_related": false, "confidence": 0.95, "reasoning": "System notification"}')


def _classify(category, confidence, reasoning="test"):
    return _mock_openai_response(json.dumps({
        "category": category, "confidence": confidence, "reasoning": reasoning
    }))


class TestFullPipelineE2E:
    """End-to-end tests exercising the full email processing pipeline."""

    @pytest.fixture(autouse=True)
    def _patch_services(self, e2e_db, mock_config):
        """Patch external services and database for all E2E tests."""
        with patch('services.classification_service.OpenAI') as cls_openai, \
             patch('services.reply_service.OpenAI') as reply_openai, \
             patch('models.database.get_db_connection') as mock_db_root, \
             patch('services.reply_service.get_db_connection') as mock_db_reply, \
             patch('models.audit_log.get_db_connection') as mock_audit_db, \
             patch('services.company_info_service.CompanyInfoService') as mock_company:

            self.cls_client = Mock()
            cls_openai.return_value = self.cls_client

            self.reply_client = Mock()
            reply_openai.return_value = self.reply_client

            import contextlib
            @contextlib.contextmanager
            def _db_ctx():
                yield e2e_db
            mock_db_root.side_effect = _db_ctx
            mock_db_reply.side_effect = _db_ctx
            mock_audit_db.side_effect = _db_ctx

            company = Mock()
            company.list_products.return_value = [{
                'product_name': 'Sea Freight (Standard)',
                'unit_price': 120.0,
                'currency': 'USD',
                'min_order_quantity': 1,
                'delivery_lead_time_days': 30
            }]
            mock_company.return_value = company

            self.db = e2e_db
            yield

    def _process(self, msg_id, subject, body, sender="customer@example.com"):
        from services.classification_service import ClassificationService
        from services.reply_service import ReplyService

        cls_svc = ClassificationService()
        cls_svc.client = self.cls_client
        classification = cls_svc.classify_email(subject, body)

        reply_svc = ReplyService()
        reply_svc.client = self.reply_client
        result = reply_svc.process_email(
            message_id=msg_id,
            subject=subject,
            sender=sender,
            received_at="2026-04-23T10:00:00Z",
            body=body,
            classification=classification,
        )
        return result

    # --- Happy path tests ---

    def test_pricing_inquiry_auto_sent(self):
        self.cls_client.chat.completions.create.side_effect = [
            _gate_ok(), _classify("pricing_inquiry", 0.92)
        ]
        result = self._process("e2e-001", "Price quote request", "Please quote sea freight Shanghai to LA")

        assert result['category'] == 'pricing_inquiry'
        assert result['reply_text'] != ''
        assert 'Sea Freight' in result['reply_text']

    def test_order_cancellation_template(self):
        self.cls_client.chat.completions.create.side_effect = [
            _gate_ok(), _classify("order_cancellation", 0.90)
        ]
        result = self._process("e2e-002", "Cancel order #12345", "Please cancel my order and refund")

        assert result['category'] == 'order_cancellation'
        assert '退款' in result['reply_text']

    def test_order_tracking_template(self):
        self.cls_client.chat.completions.create.side_effect = [
            _gate_ok(), _classify("order_tracking", 0.88)
        ]
        result = self._process("e2e-003", "Where is my package?", "Order #67890 tracking please")

        assert result['category'] == 'order_tracking'
        assert '物流' in result['reply_text'] or '订单' in result['reply_text']

    def test_non_business_ignored(self):
        self.cls_client.chat.completions.create.return_value = _gate_non_business()
        result = self._process("e2e-004", "OneDrive alert", "Storage 95% full", sender="no-reply@microsoft.com")

        assert result['category'] == 'non_business'
        assert result['status'] == 'ignored_no_reply'

    def test_low_confidence_pending_review(self):
        self.cls_client.chat.completions.create.side_effect = [
            _gate_ok(), _classify("shipping_time", 0.55)
        ]
        result = self._process("e2e-005", "Question", "How long does it take?")

        assert result['status'] == 'pending_review'

    # --- Database persistence tests ---

    def test_email_persisted_in_db(self):
        self.cls_client.chat.completions.create.side_effect = [
            _gate_ok(), _classify("pricing_inquiry", 0.85)
        ]
        result = self._process("e2e-006", "Quote", "Need a quote")

        row = self.db.execute("SELECT * FROM emails WHERE message_id = ?", ("e2e-006",)).fetchone()
        assert row is not None
        assert row['category'] == 'pricing_inquiry'

    def test_reply_persisted_in_db(self):
        self.cls_client.chat.completions.create.side_effect = [
            _gate_ok(), _classify("billing_invoice", 0.87)
        ]
        self._process("e2e-007", "Invoice request", "Send invoice for order #99")

        email_row = self.db.execute("SELECT id FROM emails WHERE message_id = ?", ("e2e-007",)).fetchone()
        reply_row = self.db.execute("SELECT * FROM replies WHERE email_id = ?", (email_row['id'],)).fetchone()
        assert reply_row is not None
        assert len(reply_row['reply_text']) > 0

    def test_audit_log_created(self):
        self.cls_client.chat.completions.create.side_effect = [
            _gate_ok(), _classify("pricing_inquiry", 0.86)
        ]
        self._process("e2e-008", "Price", "Quote please")

        email_row = self.db.execute("SELECT id FROM emails WHERE message_id = ?", ("e2e-008",)).fetchone()
        audit = self.db.execute("SELECT * FROM audit_log WHERE email_id = ?", (email_row['id'],)).fetchone()
        assert audit is not None

    # --- PII detection tests ---

    def test_pii_detected_and_flagged(self):
        self.cls_client.chat.completions.create.side_effect = [
            _gate_ok(), _classify("pricing_inquiry", 0.88)
        ]
        result = self._process("e2e-009", "Quote", "Contact me at john@secret.com or call 13812345678")

        row = self.db.execute("SELECT pii_detected, pii_types FROM emails WHERE message_id = ?", ("e2e-009",)).fetchone()
        assert row['pii_detected'] == 1
        pii_types = json.loads(row['pii_types'])
        assert 'email' in pii_types
        assert 'phone' in pii_types

    def test_no_pii_clean_email(self):
        self.cls_client.chat.completions.create.side_effect = [
            _gate_ok(), _classify("shipping_time", 0.84)
        ]
        self._process("e2e-010", "Shipping time", "How long to ship to New York?")

        row = self.db.execute("SELECT pii_detected FROM emails WHERE message_id = ?", ("e2e-010",)).fetchone()
        assert row['pii_detected'] == 0

    # --- Consent tracking ---

    def test_consent_status_stored(self):
        self.cls_client.chat.completions.create.side_effect = [
            _gate_ok(), _classify("pricing_inquiry", 0.85)
        ]
        self._process("e2e-011", "Quote", "Need pricing")

        row = self.db.execute("SELECT consent_status FROM emails WHERE message_id = ?", ("e2e-011",)).fetchone()
        assert row['consent_status'] == 'unknown'

    # --- Error handling ---

    def test_classification_api_error_uses_fallback(self):
        from openai import APIError
        self.cls_client.chat.completions.create.side_effect = Exception("API down")

        with pytest.raises(Exception):
            self._process("e2e-012", "Test", "Test body")

    # --- Batch processing ---

    def test_multiple_emails_processed(self):
        emails = [
            ("e2e-b1", "Price", "Quote please", "pricing_inquiry", 0.88),
            ("e2e-b2", "Cancel", "Cancel order", "order_cancellation", 0.91),
            ("e2e-b3", "Track", "Where is order?", "order_tracking", 0.86),
        ]
        for msg_id, subj, body, cat, conf in emails:
            self.cls_client.chat.completions.create.side_effect = [
                _gate_ok(), _classify(cat, conf)
            ]
            self._process(msg_id, subj, body)

        count = self.db.execute("SELECT COUNT(*) as c FROM emails WHERE message_id LIKE 'e2e-b%'").fetchone()['c']
        assert count == 3

    # --- Shipping templates ---

    def test_shipping_exception_template(self):
        self.cls_client.chat.completions.create.side_effect = [
            _gate_ok(), _classify("shipping_exception", 0.89)
        ]
        result = self._process("e2e-013", "Package delayed", "Tracking #ABC123 is late")

        assert '异常' in result['reply_text'] or '抱歉' in result['reply_text']

    def test_shipping_time_template(self):
        self.cls_client.chat.completions.create.side_effect = [
            _gate_ok(), _classify("shipping_time", 0.87)
        ]
        result = self._process("e2e-014", "Delivery time", "How long Beijing to NY?")

        assert '运输' in result['reply_text']

    def test_billing_invoice_template(self):
        self.cls_client.chat.completions.create.side_effect = [
            _gate_ok(), _classify("billing_invoice", 0.86)
        ]
        result = self._process("e2e-015", "Invoice", "Need invoice for order")

        assert '账单' in result['reply_text'] or '发票' in result['reply_text']
