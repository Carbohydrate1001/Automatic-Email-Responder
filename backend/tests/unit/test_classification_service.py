"""
Unit tests for classification_service.py
"""

import pytest
from unittest.mock import Mock, patch
from services.classification_service import ClassificationService, CATEGORIES


class TestClassificationService:
    """Test suite for ClassificationService."""

    @pytest.fixture
    def service(self, mock_config):
        """Create ClassificationService instance with mocked config."""
        with patch('services.classification_service.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            service = ClassificationService()
            service.client = mock_client
            return service

    def test_contains_any_with_match(self, service):
        """Test _contains_any returns True when keyword is found."""
        text = "I need a price quote for shipping"
        keywords = ["price", "quote", "quotation"]
        assert service._contains_any(text, keywords) is True

    def test_contains_any_without_match(self, service):
        """Test _contains_any returns False when no keyword is found."""
        text = "Hello world"
        keywords = ["price", "quote", "quotation"]
        assert service._contains_any(text, keywords) is False

    def test_contains_any_case_insensitive(self, service):
        """Test _contains_any is case insensitive."""
        text = "PRICE INQUIRY"
        keywords = ["price", "quote"]
        assert service._contains_any(text, keywords) is True

    def test_rule_based_non_business_with_non_business_keywords(self, service):
        """Test rule-based filter detects non-business emails."""
        subject = "OneDrive storage is almost full"
        body = "Your OneDrive storage is 95% full. Upgrade to get more space."
        assert service._rule_based_non_business(subject, body) is True

    def test_rule_based_non_business_with_business_keywords(self, service):
        """Test rule-based filter allows business emails."""
        subject = "Order tracking inquiry"
        body = "I need to track my shipment"
        assert service._rule_based_non_business(subject, body) is False

    def test_rule_based_non_business_with_mixed_keywords(self, service):
        """Test rule-based filter with mixed keywords favors business."""
        subject = "OneDrive order tracking"
        body = "I need to track my order stored in OneDrive"
        assert service._rule_based_non_business(subject, body) is False

    def test_gate_business_relevance_business_email(self, service):
        """Test business gate identifies business-related email."""
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = '{"is_business_related": true, "confidence": 0.9, "reasoning": "Logistics inquiry"}'
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        service.client.chat.completions.create.return_value = mock_response

        result = service._gate_business_relevance("Price inquiry", "I need a quote")

        assert result['is_business_related'] is True
        assert result['business_confidence'] == 0.9
        assert 'reasoning' in result

    def test_gate_business_relevance_non_business_email(self, service):
        """Test business gate identifies non-business email."""
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = '{"is_business_related": false, "confidence": 0.95, "reasoning": "System notification"}'
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        service.client.chat.completions.create.return_value = mock_response

        result = service._gate_business_relevance("OneDrive alert", "Storage full")

        assert result['is_business_related'] is False
        assert result['business_confidence'] == 0.95

    def test_gate_business_relevance_confidence_clamping(self, service):
        """Test business gate clamps confidence to 0.0-1.0 range."""
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = '{"is_business_related": true, "confidence": 1.5, "reasoning": "Test"}'
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        service.client.chat.completions.create.return_value = mock_response

        result = service._gate_business_relevance("Test", "Test")

        assert result['business_confidence'] == 1.0

    def test_classify_email_rule_based_non_business(self, service):
        """Test classification uses rule-based filter for obvious non-business."""
        result = service.classify_email(
            "OneDrive storage alert",
            "Your OneDrive is 95% full"
        )

        assert result['category'] == 'non_business'
        assert result['confidence'] == 0.98
        assert result['is_business_related'] is False
        assert 'Rule-based filter' in result['reasoning']

    def test_classify_email_business_gate_rejects(self, service):
        """Test classification respects business gate rejection."""
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = '{"is_business_related": false, "confidence": 0.85, "reasoning": "Newsletter"}'
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        service.client.chat.completions.create.return_value = mock_response

        result = service.classify_email("Newsletter", "Marketing content")

        assert result['category'] == 'non_business'
        assert result['is_business_related'] is False
        assert result['confidence'] >= 0.85

    def test_classify_email_pricing_inquiry(self, service):
        """Test classification of pricing inquiry."""
        # Mock business gate
        gate_response = Mock()
        gate_choice = Mock()
        gate_message = Mock()
        gate_message.content = '{"is_business_related": true, "confidence": 0.9, "reasoning": "Business inquiry"}'
        gate_choice.message = gate_message
        gate_response.choices = [gate_choice]

        # Mock category classification
        cat_response = Mock()
        cat_choice = Mock()
        cat_message = Mock()
        cat_message.content = '{"category": "pricing_inquiry", "confidence": 0.88, "reasoning": "Customer asks for price quote"}'
        cat_choice.message = cat_message
        cat_response.choices = [cat_choice]

        service.client.chat.completions.create.side_effect = [gate_response, cat_response]

        result = service.classify_email(
            "Price inquiry",
            "I need a quote for sea freight"
        )

        assert result['category'] == 'pricing_inquiry'
        assert result['confidence'] == 0.88
        assert result['is_business_related'] is True

    def test_classify_email_order_cancellation(self, service):
        """Test classification of order cancellation."""
        gate_response = Mock()
        gate_choice = Mock()
        gate_message = Mock()
        gate_message.content = '{"is_business_related": true, "confidence": 0.92, "reasoning": "Cancellation request"}'
        gate_choice.message = gate_message
        gate_response.choices = [gate_choice]

        cat_response = Mock()
        cat_choice = Mock()
        cat_message = Mock()
        cat_message.content = '{"category": "order_cancellation", "confidence": 0.91, "reasoning": "Customer wants to cancel order"}'
        cat_choice.message = cat_message
        cat_response.choices = [cat_choice]

        service.client.chat.completions.create.side_effect = [gate_response, cat_response]

        result = service.classify_email(
            "Cancel order",
            "I need to cancel my order #12345"
        )

        assert result['category'] == 'order_cancellation'
        assert result['confidence'] == 0.91

    def test_classify_email_invalid_category_fallback(self, service):
        """Test classification falls back to non_business for invalid category."""
        gate_response = Mock()
        gate_choice = Mock()
        gate_message = Mock()
        gate_message.content = '{"is_business_related": true, "confidence": 0.8, "reasoning": "Business"}'
        gate_choice.message = gate_message
        gate_response.choices = [gate_choice]

        cat_response = Mock()
        cat_choice = Mock()
        cat_message = Mock()
        cat_message.content = '{"category": "invalid_category", "confidence": 0.7, "reasoning": "Unknown"}'
        cat_choice.message = cat_message
        cat_response.choices = [cat_choice]

        service.client.chat.completions.create.side_effect = [gate_response, cat_response]

        result = service.classify_email("Test", "Test")

        assert result['category'] == 'non_business'

    def test_classify_email_confidence_clamping(self, service):
        """Test classification clamps confidence to valid range."""
        gate_response = Mock()
        gate_choice = Mock()
        gate_message = Mock()
        gate_message.content = '{"is_business_related": true, "confidence": 0.8, "reasoning": "Business"}'
        gate_choice.message = gate_message
        gate_response.choices = [gate_choice]

        cat_response = Mock()
        cat_choice = Mock()
        cat_message = Mock()
        cat_message.content = '{"category": "pricing_inquiry", "confidence": -0.5, "reasoning": "Test"}'
        cat_choice.message = cat_message
        cat_response.choices = [cat_choice]

        service.client.chat.completions.create.side_effect = [gate_response, cat_response]

        result = service.classify_email("Test", "Test")

        assert 0.0 <= result['confidence'] <= 1.0

    def test_classify_email_body_truncation(self, service):
        """Test classification truncates long email bodies."""
        gate_response = Mock()
        gate_choice = Mock()
        gate_message = Mock()
        gate_message.content = '{"is_business_related": true, "confidence": 0.8, "reasoning": "Business"}'
        gate_choice.message = gate_message
        gate_response.choices = [gate_choice]

        cat_response = Mock()
        cat_choice = Mock()
        cat_message = Mock()
        cat_message.content = '{"category": "pricing_inquiry", "confidence": 0.85, "reasoning": "Price inquiry"}'
        cat_choice.message = cat_message
        cat_response.choices = [cat_choice]

        service.client.chat.completions.create.side_effect = [gate_response, cat_response]

        long_body = "Test " * 1000  # Very long body
        result = service.classify_email("Test", long_body)

        # Verify the API was called with truncated body
        calls = service.client.chat.completions.create.call_args_list
        for call in calls:
            user_content = call[1]['messages'][1]['content']
            assert len(user_content) <= 3100  # 3000 chars + "Subject: " + "\n\nBody:\n"

    def test_classify_email_empty_subject_and_body(self, service):
        """Test classification handles empty subject and body."""
        gate_response = Mock()
        gate_choice = Mock()
        gate_message = Mock()
        gate_message.content = '{"is_business_related": false, "confidence": 0.95, "reasoning": "Empty email"}'
        gate_choice.message = gate_message
        gate_response.choices = [gate_choice]

        service.client.chat.completions.create.return_value = gate_response

        result = service.classify_email("", "")

        assert result['category'] == 'non_business'

    def test_classify_email_chinese_content(self, service):
        """Test classification handles Chinese content."""
        gate_response = Mock()
        gate_choice = Mock()
        gate_message = Mock()
        gate_message.content = '{"is_business_related": true, "confidence": 0.9, "reasoning": "询价"}'
        gate_choice.message = gate_message
        gate_response.choices = [gate_choice]

        cat_response = Mock()
        cat_choice = Mock()
        cat_message = Mock()
        cat_message.content = '{"category": "pricing_inquiry", "confidence": 0.87, "reasoning": "客户询价"}'
        cat_choice.message = cat_message
        cat_response.choices = [cat_choice]

        service.client.chat.completions.create.side_effect = [gate_response, cat_response]

        result = service.classify_email("询价", "我想了解海运价格")

        assert result['category'] == 'pricing_inquiry'
        assert result['confidence'] == 0.87

    def test_classify_email_high_confidence_override(self, service):
        """Test classification overrides high confidence if rule-based filter triggers."""
        gate_response = Mock()
        gate_choice = Mock()
        gate_message = Mock()
        gate_message.content = '{"is_business_related": true, "confidence": 0.8, "reasoning": "Business"}'
        gate_choice.message = gate_message
        gate_response.choices = [gate_choice]

        cat_response = Mock()
        cat_choice = Mock()
        cat_message = Mock()
        cat_message.content = '{"category": "pricing_inquiry", "confidence": 0.92, "reasoning": "Price inquiry"}'
        cat_choice.message = cat_message
        cat_response.choices = [cat_choice]

        service.client.chat.completions.create.side_effect = [gate_response, cat_response]

        # Email with non-business keywords but high confidence
        result = service.classify_email(
            "OneDrive pricing",
            "Microsoft 365 newsletter about OneDrive storage pricing"
        )

        # Should be overridden to non_business
        assert result['category'] == 'non_business'
        assert result['confidence'] == 0.85

    def test_categories_constant(self):
        """Test CATEGORIES constant contains expected categories."""
        expected_categories = [
            "pricing_inquiry",
            "order_cancellation",
            "order_tracking",
            "shipping_time",
            "shipping_exception",
            "billing_invoice",
            "non_business"
        ]
        assert CATEGORIES == expected_categories
