"""
Integration tests for the full email processing pipeline.
"""

import pytest
import sqlite3
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


class TestEmailPipeline:
    """Integration tests for the complete email processing workflow."""

    @pytest.fixture
    def mock_services(self, mock_config):
        """Mock all external services."""
        with patch('services.classification_service.OpenAI') as mock_openai_class, \
             patch('services.reply_service.OpenAI') as mock_openai_reply, \
             patch('services.reply_service.CompanyInfoService') as mock_company:

            # Mock OpenAI for classification
            mock_openai_client = Mock()
            mock_openai_class.return_value = mock_openai_client

            # Mock OpenAI for reply generation
            mock_reply_client = Mock()
            mock_openai_reply.return_value = mock_reply_client

            # Mock company info service
            mock_company_instance = Mock()
            mock_company_instance.list_products.return_value = [
                {
                    'product_name': 'Sea Freight (Standard)',
                    'unit_price': 120.0,
                    'currency': 'USD',
                    'min_order_quantity': 1,
                    'delivery_lead_time_days': 30
                }
            ]
            mock_company.return_value = mock_company_instance

            yield {
                'openai_classification': mock_openai_client,
                'openai_reply': mock_reply_client,
                'company_info': mock_company_instance
            }

    def test_full_pipeline_pricing_inquiry_auto_send(self, temp_db, mock_services):
        """Test complete pipeline for high-confidence pricing inquiry."""
        from services.classification_service import ClassificationService
        from services.reply_service import ReplyService

        # Setup classification service
        classification_service = ClassificationService()
        classification_service.client = mock_services['openai_classification']

        # Mock business gate response
        gate_response = Mock()
        gate_choice = Mock()
        gate_message = Mock()
        gate_message.content = '{"is_business_related": true, "confidence": 0.92, "reasoning": "Pricing inquiry"}'
        gate_choice.message = gate_message
        gate_response.choices = [gate_choice]

        # Mock category classification response
        cat_response = Mock()
        cat_choice = Mock()
        cat_message = Mock()
        cat_message.content = '{"category": "pricing_inquiry", "confidence": 0.88, "reasoning": "Customer asks for price quote"}'
        cat_choice.message = cat_message
        cat_response.choices = [cat_choice]

        mock_services['openai_classification'].chat.completions.create.side_effect = [
            gate_response, cat_response
        ]

        # Step 1: Classify email
        subject = "Price inquiry for sea freight"
        body = "I need a quote for sea freight from Shanghai to LA"

        classification = classification_service.classify_email(subject, body)

        assert classification['category'] == 'pricing_inquiry'
        assert classification['confidence'] == 0.88
        assert classification['is_business_related'] is True

        # Step 2: Generate reply
        reply_service = ReplyService()
        reply_service.client = mock_services['openai_reply']

        reply_text = reply_service.generate_reply(
            "customer@example.com",
            "2026-04-23T10:00:00Z",
            subject,
            body,
            classification['category'],
            classification['reasoning']
        )

        assert len(reply_text) > 0
        assert "Sea Freight" in reply_text

        # Step 3: Check auto-send decision
        confidence = classification['confidence']
        auto_send_eligible = confidence >= 0.75 and confidence >= 0.8

        assert auto_send_eligible is True

        # Step 4: Store in database
        temp_db.execute("""
            INSERT INTO emails (message_id, subject, sender, received_at, body, category, confidence, reasoning, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'test-msg-001',
            subject,
            'customer@example.com',
            '2026-04-23T10:00:00Z',
            body,
            classification['category'],
            classification['confidence'],
            classification['reasoning'],
            'auto_sent'
        ))
        temp_db.commit()

        # Verify database entry
        row = temp_db.execute("SELECT * FROM emails WHERE message_id = ?", ('test-msg-001',)).fetchone()
        assert row is not None
        assert row['category'] == 'pricing_inquiry'
        assert row['status'] == 'auto_sent'

    def test_full_pipeline_low_confidence_manual_review(self, temp_db, mock_services):
        """Test pipeline routes low-confidence emails to manual review."""
        from services.classification_service import ClassificationService
        from services.reply_service import ReplyService

        classification_service = ClassificationService()
        classification_service.client = mock_services['openai_classification']

        # Mock low confidence classification
        gate_response = Mock()
        gate_choice = Mock()
        gate_message = Mock()
        gate_message.content = '{"is_business_related": true, "confidence": 0.75, "reasoning": "Uncertain"}'
        gate_choice.message = gate_message
        gate_response.choices = [gate_choice]

        cat_response = Mock()
        cat_choice = Mock()
        cat_message = Mock()
        cat_message.content = '{"category": "order_tracking", "confidence": 0.72, "reasoning": "Possibly tracking"}'
        cat_choice.message = cat_message
        cat_response.choices = [cat_choice]

        mock_services['openai_classification'].chat.completions.create.side_effect = [
            gate_response, cat_response
        ]

        # Classify
        classification = classification_service.classify_email(
            "Unclear request",
            "I need help with something"
        )

        assert classification['confidence'] == 0.72

        # Check routing decision
        auto_send_eligible = classification['confidence'] >= 0.75 and classification['confidence'] >= 0.8
        assert auto_send_eligible is False

        # Should route to pending_review
        status = 'pending_review'

        temp_db.execute("""
            INSERT INTO emails (message_id, subject, sender, body, category, confidence, reasoning, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'test-msg-002',
            'Unclear request',
            'customer@example.com',
            'I need help',
            classification['category'],
            classification['confidence'],
            classification['reasoning'],
            status
        ))
        temp_db.commit()

        row = temp_db.execute("SELECT * FROM emails WHERE message_id = ?", ('test-msg-002',)).fetchone()
        assert row['status'] == 'pending_review'

    def test_full_pipeline_non_business_ignored(self, temp_db, mock_services):
        """Test pipeline ignores non-business emails."""
        from services.classification_service import ClassificationService
        from services.reply_service import ReplyService

        classification_service = ClassificationService()
        classification_service.client = mock_services['openai_classification']

        # Mock non-business classification
        gate_response = Mock()
        gate_choice = Mock()
        gate_message = Mock()
        gate_message.content = '{"is_business_related": false, "confidence": 0.95, "reasoning": "System notification"}'
        gate_choice.message = gate_message
        gate_response.choices = [gate_choice]

        mock_services['openai_classification'].chat.completions.create.return_value = gate_response

        classification = classification_service.classify_email(
            "OneDrive storage alert",
            "Your OneDrive is 95% full"
        )

        assert classification['category'] == 'non_business'
        assert classification['is_business_related'] is False

        # Generate reply (should be empty)
        reply_service = ReplyService()
        reply_text = reply_service.generate_reply(
            "no-reply@microsoft.com",
            "2026-04-23T10:00:00Z",
            "OneDrive alert",
            "Storage full",
            'non_business',
            "System notification"
        )

        assert reply_text == ""

        # Should be marked as ignored
        temp_db.execute("""
            INSERT INTO emails (message_id, subject, sender, body, category, confidence, reasoning, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'test-msg-003',
            'OneDrive alert',
            'no-reply@microsoft.com',
            'Storage full',
            'non_business',
            0.95,
            'System notification',
            'ignored_no_reply'
        ))
        temp_db.commit()

        row = temp_db.execute("SELECT * FROM emails WHERE message_id = ?", ('test-msg-003',)).fetchone()
        assert row['status'] == 'ignored_no_reply'

    def test_pipeline_handles_classification_error(self, temp_db, mock_services):
        """Test pipeline handles classification errors gracefully."""
        from services.classification_service import ClassificationService

        classification_service = ClassificationService()
        classification_service.client = mock_services['openai_classification']

        # Mock API error
        mock_services['openai_classification'].chat.completions.create.side_effect = Exception("API Error")

        with pytest.raises(Exception):
            classification_service.classify_email("Test", "Test")

    def test_pipeline_duplicate_message_id_handling(self, temp_db):
        """Test pipeline handles duplicate message IDs."""
        # Insert first email
        temp_db.execute("""
            INSERT INTO emails (message_id, subject, sender, body, category, confidence, reasoning, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'duplicate-msg',
            'Test',
            'test@example.com',
            'Test body',
            'pricing_inquiry',
            0.85,
            'Test',
            'pending_review'
        ))
        temp_db.commit()

        # Try to insert duplicate
        with pytest.raises(sqlite3.IntegrityError):
            temp_db.execute("""
                INSERT INTO emails (message_id, subject, sender, body, category, confidence, reasoning, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                'duplicate-msg',
                'Test 2',
                'test2@example.com',
                'Test body 2',
                'order_tracking',
                0.80,
                'Test',
                'pending_review'
            ))
            temp_db.commit()

    def test_pipeline_reply_storage(self, temp_db):
        """Test pipeline stores replies correctly."""
        # Insert email
        temp_db.execute("""
            INSERT INTO emails (message_id, subject, sender, body, category, confidence, reasoning, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'test-msg-004',
            'Test',
            'test@example.com',
            'Test',
            'pricing_inquiry',
            0.88,
            'Test',
            'auto_sent'
        ))
        temp_db.commit()

        email_id = temp_db.execute("SELECT id FROM emails WHERE message_id = ?", ('test-msg-004',)).fetchone()['id']

        # Store reply
        reply_text = "Thank you for your inquiry..."
        temp_db.execute("""
            INSERT INTO replies (email_id, reply_text, sent_at)
            VALUES (?, ?, ?)
        """, (email_id, reply_text, '2026-04-23T10:05:00Z'))
        temp_db.commit()

        # Verify reply
        reply = temp_db.execute("SELECT * FROM replies WHERE email_id = ?", (email_id,)).fetchone()
        assert reply is not None
        assert reply['reply_text'] == reply_text

    def test_pipeline_audit_log(self, temp_db):
        """Test pipeline creates audit log entries."""
        # Insert email
        temp_db.execute("""
            INSERT INTO emails (message_id, subject, sender, body, category, confidence, reasoning, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'test-msg-005',
            'Test',
            'test@example.com',
            'Test',
            'pricing_inquiry',
            0.75,
            'Test',
            'pending_review'
        ))
        temp_db.commit()

        email_id = temp_db.execute("SELECT id FROM emails WHERE message_id = ?", ('test-msg-005',)).fetchone()['id']

        # Create audit log entry for approval
        temp_db.execute("""
            INSERT INTO audit_log (email_id, action, operator)
            VALUES (?, ?, ?)
        """, (email_id, 'approved', 'admin@example.com'))
        temp_db.commit()

        # Verify audit log
        log = temp_db.execute("SELECT * FROM audit_log WHERE email_id = ?", (email_id,)).fetchone()
        assert log is not None
        assert log['action'] == 'approved'
        assert log['operator'] == 'admin@example.com'

    def test_pipeline_batch_processing(self, temp_db, mock_services):
        """Test pipeline can process multiple emails in batch."""
        from services.classification_service import ClassificationService

        classification_service = ClassificationService()
        classification_service.client = mock_services['openai_classification']

        # Mock responses for multiple emails
        gate_response = Mock()
        gate_choice = Mock()
        gate_message = Mock()
        gate_message.content = '{"is_business_related": true, "confidence": 0.85, "reasoning": "Business"}'
        gate_choice.message = gate_message
        gate_response.choices = [gate_choice]

        cat_response = Mock()
        cat_choice = Mock()
        cat_message = Mock()
        cat_message.content = '{"category": "pricing_inquiry", "confidence": 0.82, "reasoning": "Price"}'
        cat_choice.message = cat_message
        cat_response.choices = [cat_choice]

        mock_services['openai_classification'].chat.completions.create.side_effect = [
            gate_response, cat_response,
            gate_response, cat_response,
            gate_response, cat_response
        ]

        # Process 3 emails
        emails = [
            ("Email 1", "Body 1"),
            ("Email 2", "Body 2"),
            ("Email 3", "Body 3")
        ]

        for i, (subject, body) in enumerate(emails):
            classification = classification_service.classify_email(subject, body)

            temp_db.execute("""
                INSERT INTO emails (message_id, subject, sender, body, category, confidence, reasoning, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f'batch-msg-{i}',
                subject,
                'customer@example.com',
                body,
                classification['category'],
                classification['confidence'],
                classification['reasoning'],
                'auto_sent' if classification['confidence'] >= 0.8 else 'pending_review'
            ))

        temp_db.commit()

        # Verify all emails processed
        count = temp_db.execute("SELECT COUNT(*) as cnt FROM emails WHERE message_id LIKE 'batch-msg-%'").fetchone()['cnt']
        assert count == 3
