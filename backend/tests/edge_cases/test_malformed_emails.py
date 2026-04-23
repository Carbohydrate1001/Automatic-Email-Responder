"""
Edge case tests for email classification and processing.
"""

import pytest
from unittest.mock import Mock, patch
from services.classification_service import ClassificationService
from services.reply_service import ReplyService
from tests.fixtures.sample_emails import SAMPLE_EMAILS


class TestEdgeCases:
    """Test suite for edge cases in email processing."""

    @pytest.fixture
    def classification_service(self, mock_config):
        """Create ClassificationService with mocked config."""
        with patch('services.classification_service.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            service = ClassificationService()
            service.client = mock_client
            return service

    @pytest.fixture
    def reply_service(self, mock_config):
        """Create ReplyService with mocked config."""
        with patch('services.reply_service.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            service = ReplyService()
            service.client = mock_client
            return service

    def test_multi_intent_email_classification(self, classification_service):
        """Test classification of email with multiple intents."""
        gate_response = Mock()
        gate_choice = Mock()
        gate_message = Mock()
        gate_message.content = '{"is_business_related": true, "confidence": 0.85, "reasoning": "Multiple requests"}'
        gate_choice.message = gate_message
        gate_response.choices = [gate_choice]

        cat_response = Mock()
        cat_choice = Mock()
        cat_message = Mock()
        # Should pick the first/primary intent
        cat_message.content = '{"category": "order_cancellation", "confidence": 0.75, "reasoning": "Primary intent is cancellation"}'
        cat_choice.message = cat_message
        cat_response.choices = [cat_choice]

        classification_service.client.chat.completions.create.side_effect = [gate_response, cat_response]

        email = SAMPLE_EMAILS['multi_intent']
        result = classification_service.classify_email(email['subject'], email['body'])

        assert result['category'] in ['order_cancellation', 'order_tracking']
        assert result['is_business_related'] is True

    def test_incomplete_email_classification(self, classification_service):
        """Test classification of very short/incomplete email."""
        gate_response = Mock()
        gate_choice = Mock()
        gate_message = Mock()
        gate_message.content = '{"is_business_related": false, "confidence": 0.88, "reasoning": "Too vague"}'
        gate_choice.message = gate_message
        gate_response.choices = [gate_choice]

        classification_service.client.chat.completions.create.return_value = gate_response

        email = SAMPLE_EMAILS['incomplete']
        result = classification_service.classify_email(email['subject'], email['body'])

        assert result['category'] == 'non_business'
        assert result['confidence'] >= 0.85

    def test_very_long_email_truncation(self, classification_service):
        """Test that very long emails are properly truncated."""
        gate_response = Mock()
        gate_choice = Mock()
        gate_message = Mock()
        gate_message.content = '{"is_business_related": true, "confidence": 0.8, "reasoning": "Business"}'
        gate_choice.message = gate_message
        gate_response.choices = [gate_choice]

        cat_response = Mock()
        cat_choice = Mock()
        cat_message = Mock()
        cat_message.content = '{"category": "pricing_inquiry", "confidence": 0.82, "reasoning": "Price inquiry"}'
        cat_choice.message = cat_message
        cat_response.choices = [cat_choice]

        classification_service.client.chat.completions.create.side_effect = [gate_response, cat_response]

        email = SAMPLE_EMAILS['very_long']
        result = classification_service.classify_email(email['subject'], email['body'])

        # Verify API was called with truncated content
        calls = classification_service.client.chat.completions.create.call_args_list
        for call in calls:
            user_content = call[1]['messages'][1]['content']
            # Should be truncated to ~3000 chars
            assert len(user_content) <= 3200

        assert result['category'] == 'pricing_inquiry'

    def test_chinese_email_classification(self, classification_service):
        """Test classification of Chinese language email."""
        gate_response = Mock()
        gate_choice = Mock()
        gate_message = Mock()
        gate_message.content = '{"is_business_related": true, "confidence": 0.92, "reasoning": "询价邮件"}'
        gate_choice.message = gate_message
        gate_response.choices = [gate_choice]

        cat_response = Mock()
        cat_choice = Mock()
        cat_message = Mock()
        cat_message.content = '{"category": "pricing_inquiry", "confidence": 0.89, "reasoning": "客户询价"}'
        cat_choice.message = cat_message
        cat_response.choices = [cat_choice]

        classification_service.client.chat.completions.create.side_effect = [gate_response, cat_response]

        email = SAMPLE_EMAILS['chinese']
        result = classification_service.classify_email(email['subject'], email['body'])

        assert result['category'] == 'pricing_inquiry'
        assert result['is_business_related'] is True

    def test_mixed_language_email_classification(self, classification_service):
        """Test classification of email with mixed Chinese and English."""
        gate_response = Mock()
        gate_choice = Mock()
        gate_message = Mock()
        gate_message.content = '{"is_business_related": true, "confidence": 0.87, "reasoning": "Business inquiry"}'
        gate_choice.message = gate_message
        gate_response.choices = [gate_choice]

        cat_response = Mock()
        cat_choice = Mock()
        cat_message = Mock()
        cat_message.content = '{"category": "pricing_inquiry", "confidence": 0.84, "reasoning": "Mixed language price inquiry"}'
        cat_choice.message = cat_message
        cat_response.choices = [cat_choice]

        classification_service.client.chat.completions.create.side_effect = [gate_response, cat_response]

        email = SAMPLE_EMAILS['mixed_language']
        result = classification_service.classify_email(email['subject'], email['body'])

        assert result['category'] == 'pricing_inquiry'

    def test_email_with_special_characters(self, classification_service):
        """Test classification of email with emojis and special characters."""
        gate_response = Mock()
        gate_choice = Mock()
        gate_message = Mock()
        gate_message.content = '{"is_business_related": true, "confidence": 0.8, "reasoning": "Business"}'
        gate_choice.message = gate_message
        gate_response.choices = [gate_choice]

        cat_response = Mock()
        cat_choice = Mock()
        cat_message = Mock()
        cat_message.content = '{"category": "order_tracking", "confidence": 0.78, "reasoning": "Tracking request"}'
        cat_choice.message = cat_message
        cat_response.choices = [cat_choice]

        classification_service.client.chat.completions.create.side_effect = [gate_response, cat_response]

        subject = "Where is my order? 📦🚚"
        body = "Hi! 😊 I need to track my shipment #12345. Thanks! 🙏"

        result = classification_service.classify_email(subject, body)

        assert result['category'] == 'order_tracking'

    def test_email_with_html_content(self, reply_service):
        """Test reply generation handles HTML in email body."""
        body = "<html><body><p>My shipment is <b>delayed</b>!</p></body></html>"

        result = reply_service._summarize_exception_from_body(body)

        # Should strip HTML tags
        assert "<html>" not in result
        assert "<body>" not in result
        assert "<p>" not in result
        assert "<b>" not in result
        assert "delayed" in result

    def test_email_with_no_sender_name(self, reply_service):
        """Test customer name extraction with no sender."""
        result = reply_service._extract_customer_name("")
        assert result == "客户"

        result = reply_service._extract_customer_name(None)
        assert result == "客户"

    def test_email_with_numeric_sender(self, reply_service):
        """Test customer name extraction with numeric email."""
        result = reply_service._extract_customer_name("12345@example.com")
        assert result == "12345"

    def test_email_with_complex_sender_format(self, reply_service):
        """Test customer name extraction with complex format."""
        result = reply_service._extract_customer_name("john.doe+tag@example.com")
        assert "john" in result
        assert "doe" in result

    def test_borderline_confidence_classification(self, classification_service):
        """Test classification with borderline confidence scores."""
        gate_response = Mock()
        gate_choice = Mock()
        gate_message = Mock()
        gate_message.content = '{"is_business_related": true, "confidence": 0.61, "reasoning": "Borderline"}'
        gate_choice.message = gate_message
        gate_response.choices = [gate_choice]

        cat_response = Mock()
        cat_choice = Mock()
        cat_message = Mock()
        cat_message.content = '{"category": "pricing_inquiry", "confidence": 0.76, "reasoning": "Uncertain"}'
        cat_choice.message = cat_message
        cat_response.choices = [cat_choice]

        classification_service.client.chat.completions.create.side_effect = [gate_response, cat_response]

        result = classification_service.classify_email("Maybe inquiry?", "I might need pricing")

        # Should still classify as business since gate confidence >= 0.6
        assert result['is_business_related'] is True
        assert result['category'] == 'pricing_inquiry'

    def test_email_with_multiple_order_numbers(self, reply_service):
        """Test order number extraction with multiple numbers."""
        text = "I have issues with order #12345 and order #67890"
        result = reply_service._extract_order_number_from_text(text)

        # Should extract the first one
        assert "12345" in result or "67890" in result

    def test_email_with_invalid_date_format(self, reply_service):
        """Test date resolution with various invalid formats."""
        invalid_dates = [
            "not-a-date",
            "2026-13-45",  # Invalid month/day
            "yesterday",
            "",
            None
        ]

        for invalid_date in invalid_dates:
            result = reply_service._resolve_base_date(invalid_date)
            # Should return current time without crashing
            assert result is not None
            assert result.tzinfo is not None

    def test_empty_product_catalog(self, reply_service):
        """Test reply generation with empty product catalog."""
        result = reply_service._select_product("Test", "Test", [])
        assert result is None

    @patch('services.reply_service.CompanyInfoService')
    def test_reply_generation_with_missing_product_fields(self, mock_company_service, reply_service):
        """Test reply generation handles missing product fields gracefully."""
        mock_service_instance = Mock()
        mock_service_instance.list_products.return_value = [
            {
                'product_name': 'Incomplete Product',
                'unit_price': None,  # Missing price
                'currency': 'USD',
                'min_order_quantity': None,  # Missing MOQ
                'delivery_lead_time_days': None  # Missing lead time
            }
        ]
        mock_company_service.return_value = mock_service_instance

        result = reply_service._generate_pricing_template_reply(
            "customer@example.com",
            "Inquiry",
            "incomplete product pricing",
            "2026-04-23T10:00:00Z"
        )

        # Should handle None values gracefully
        assert result is not None
        assert len(result) > 0

    def test_concurrent_classification_requests(self, classification_service):
        """Test classification service handles multiple requests."""
        gate_response = Mock()
        gate_choice = Mock()
        gate_message = Mock()
        gate_message.content = '{"is_business_related": true, "confidence": 0.8, "reasoning": "Business"}'
        gate_choice.message = gate_message
        gate_response.choices = [gate_choice]

        cat_response = Mock()
        cat_choice = Mock()
        cat_message = Mock()
        cat_message.content = '{"category": "pricing_inquiry", "confidence": 0.85, "reasoning": "Price"}'
        cat_choice.message = cat_message
        cat_response.choices = [cat_choice]

        classification_service.client.chat.completions.create.side_effect = [
            gate_response, cat_response,
            gate_response, cat_response,
            gate_response, cat_response
        ]

        # Simulate multiple concurrent-like requests
        results = []
        for i in range(3):
            result = classification_service.classify_email(f"Subject {i}", f"Body {i}")
            results.append(result)

        assert len(results) == 3
        for result in results:
            assert result['category'] == 'pricing_inquiry'

    def test_malformed_json_response_handling(self, classification_service):
        """Test classification handles malformed JSON from LLM."""
        gate_response = Mock()
        gate_choice = Mock()
        gate_message = Mock()
        gate_message.content = 'Not valid JSON at all'
        gate_choice.message = gate_message
        gate_response.choices = [gate_choice]

        classification_service.client.chat.completions.create.return_value = gate_response

        # Should raise JSONDecodeError
        with pytest.raises(Exception):
            classification_service.classify_email("Test", "Test")
