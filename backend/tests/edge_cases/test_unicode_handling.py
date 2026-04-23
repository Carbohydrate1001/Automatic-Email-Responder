"""
Unicode and internationalization tests.
"""

import pytest
from unittest.mock import Mock, patch
from services.classification_service import ClassificationService
from services.reply_service import ReplyService


class TestUnicodeHandling:
    """Test suite for Unicode and internationalization handling."""

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

    def test_chinese_simplified_characters(self, classification_service):
        """Test handling of simplified Chinese characters."""
        gate_response = Mock()
        gate_choice = Mock()
        gate_message = Mock()
        gate_message.content = '{"is_business_related": true, "confidence": 0.9, "reasoning": "询价邮件"}'
        gate_choice.message = gate_message
        gate_response.choices = [gate_choice]

        cat_response = Mock()
        cat_choice = Mock()
        cat_message = Mock()
        cat_message.content = '{"category": "pricing_inquiry", "confidence": 0.88, "reasoning": "客户询价"}'
        cat_choice.message = cat_message
        cat_response.choices = [cat_choice]

        classification_service.client.chat.completions.create.side_effect = [gate_response, cat_response]

        subject = "询价"
        body = "您好，我想了解海运价格。谢谢！"

        result = classification_service.classify_email(subject, body)

        assert result['category'] == 'pricing_inquiry'
        assert result['is_business_related'] is True

    def test_chinese_traditional_characters(self, classification_service):
        """Test handling of traditional Chinese characters."""
        gate_response = Mock()
        gate_choice = Mock()
        gate_message = Mock()
        gate_message.content = '{"is_business_related": true, "confidence": 0.89, "reasoning": "詢價郵件"}'
        gate_choice.message = gate_message
        gate_response.choices = [gate_choice]

        cat_response = Mock()
        cat_choice = Mock()
        cat_message = Mock()
        cat_message.content = '{"category": "pricing_inquiry", "confidence": 0.86, "reasoning": "客戶詢價"}'
        cat_choice.message = cat_message
        cat_response.choices = [cat_choice]

        classification_service.client.chat.completions.create.side_effect = [gate_response, cat_response]

        subject = "詢價"
        body = "您好，我想瞭解海運價格。謝謝！"

        result = classification_service.classify_email(subject, body)

        assert result['category'] == 'pricing_inquiry'

    def test_emoji_in_subject_and_body(self, classification_service):
        """Test handling of emoji characters."""
        gate_response = Mock()
        gate_choice = Mock()
        gate_message = Mock()
        gate_message.content = '{"is_business_related": true, "confidence": 0.82, "reasoning": "Order tracking"}'
        gate_choice.message = gate_message
        gate_response.choices = [gate_choice]

        cat_response = Mock()
        cat_choice = Mock()
        cat_message = Mock()
        cat_message.content = '{"category": "order_tracking", "confidence": 0.81, "reasoning": "Tracking request"}'
        cat_choice.message = cat_message
        cat_response.choices = [cat_choice]

        classification_service.client.chat.completions.create.side_effect = [gate_response, cat_response]

        subject = "📦 Where is my package? 🚚"
        body = "Hi! 😊 I need tracking info for order #12345. Thanks! 🙏✨"

        result = classification_service.classify_email(subject, body)

        assert result['category'] == 'order_tracking'

    def test_mixed_scripts_email(self, classification_service):
        """Test email with mixed scripts (Latin, Chinese, Cyrillic)."""
        gate_response = Mock()
        gate_choice = Mock()
        gate_message = Mock()
        gate_message.content = '{"is_business_related": true, "confidence": 0.85, "reasoning": "Business inquiry"}'
        gate_choice.message = gate_message
        gate_response.choices = [gate_choice]

        cat_response = Mock()
        cat_choice = Mock()
        cat_message = Mock()
        cat_message.content = '{"category": "pricing_inquiry", "confidence": 0.83, "reasoning": "Price inquiry"}'
        cat_choice.message = cat_message
        cat_response.choices = [cat_choice]

        classification_service.client.chat.completions.create.side_effect = [gate_response, cat_response]

        subject = "Price inquiry 询价 Цена"
        body = "Hello 你好 Привет, I need pricing information."

        result = classification_service.classify_email(subject, body)

        assert result['category'] == 'pricing_inquiry'

    def test_special_unicode_characters(self, classification_service):
        """Test handling of special Unicode characters."""
        gate_response = Mock()
        gate_choice = Mock()
        gate_message = Mock()
        gate_message.content = '{"is_business_related": true, "confidence": 0.8, "reasoning": "Business"}'
        gate_choice.message = gate_message
        gate_response.choices = [gate_choice]

        cat_response = Mock()
        cat_choice = Mock()
        cat_message = Mock()
        cat_message.content = '{"category": "billing_invoice", "confidence": 0.79, "reasoning": "Invoice request"}'
        cat_choice.message = cat_message
        cat_response.choices = [cat_choice]

        classification_service.client.chat.completions.create.side_effect = [gate_response, cat_response]

        subject = "Invoice for €1,234.56"
        body = "Please send invoice with £ and ¥ symbols. Total: ₹10,000"

        result = classification_service.classify_email(subject, body)

        assert result['category'] == 'billing_invoice'

    def test_right_to_left_text(self, classification_service):
        """Test handling of right-to-left text (Arabic, Hebrew)."""
        gate_response = Mock()
        gate_choice = Mock()
        gate_message = Mock()
        gate_message.content = '{"is_business_related": true, "confidence": 0.87, "reasoning": "Business inquiry"}'
        gate_choice.message = gate_message
        gate_response.choices = [gate_choice]

        cat_response = Mock()
        cat_choice = Mock()
        cat_message = Mock()
        cat_message.content = '{"category": "pricing_inquiry", "confidence": 0.84, "reasoning": "Price inquiry"}'
        cat_choice.message = cat_message
        cat_response.choices = [cat_choice]

        classification_service.client.chat.completions.create.side_effect = [gate_response, cat_response]

        subject = "استفسار عن السعر"  # Arabic: Price inquiry
        body = "مرحبا، أريد معرفة الأسعار"  # Arabic: Hello, I want to know the prices

        result = classification_service.classify_email(subject, body)

        assert result['category'] == 'pricing_inquiry'

    def test_zero_width_characters(self, classification_service):
        """Test handling of zero-width Unicode characters."""
        gate_response = Mock()
        gate_choice = Mock()
        gate_message = Mock()
        gate_message.content = '{"is_business_related": true, "confidence": 0.8, "reasoning": "Business"}'
        gate_choice.message = gate_message
        gate_response.choices = [gate_choice]

        cat_response = Mock()
        cat_choice = Mock()
        cat_message = Mock()
        cat_message.content = '{"category": "pricing_inquiry", "confidence": 0.82, "reasoning": "Price"}'
        cat_choice.message = cat_message
        cat_response.choices = [cat_choice]

        classification_service.client.chat.completions.create.side_effect = [gate_response, cat_response]

        # Text with zero-width space (U+200B)
        subject = "Price​inquiry"
        body = "I​need​pricing"

        result = classification_service.classify_email(subject, body)

        assert result['category'] == 'pricing_inquiry'

    def test_customer_name_extraction_chinese(self, reply_service):
        """Test customer name extraction from Chinese email."""
        result = reply_service._extract_customer_name("张三@example.com")
        assert result == "张三"

    def test_customer_name_extraction_unicode(self, reply_service):
        """Test customer name extraction with Unicode characters."""
        result = reply_service._extract_customer_name("josé.garcía@example.com")
        assert "josé" in result.lower()
        assert "garcía" in result.lower()

    def test_reply_generation_preserves_unicode(self, reply_service):
        """Test reply generation preserves Unicode characters."""
        result = reply_service._generate_order_cancellation_template_reply(
            "客户@example.com",
            "取消订单",
            "我要取消订单"
        )

        # Should contain Chinese characters
        assert any('一' <= char <= '鿿' for char in result)

    def test_html_stripping_preserves_unicode(self, reply_service):
        """Test HTML stripping preserves Unicode content."""
        body = "<p>我的货物<b>延误</b>了！</p>"
        result = reply_service._summarize_exception_from_body(body)

        assert "我的货物" in result
        assert "延误" in result
        assert "<p>" not in result
        assert "<b>" not in result

    def test_normalization_of_unicode_variants(self, classification_service):
        """Test handling of Unicode normalization (NFC vs NFD)."""
        gate_response = Mock()
        gate_choice = Mock()
        gate_message = Mock()
        gate_message.content = '{"is_business_related": true, "confidence": 0.8, "reasoning": "Business"}'
        gate_choice.message = gate_message
        gate_response.choices = [gate_choice]

        cat_response = Mock()
        cat_choice = Mock()
        cat_message = Mock()
        cat_message.content = '{"category": "pricing_inquiry", "confidence": 0.82, "reasoning": "Price"}'
        cat_choice.message = cat_message
        cat_response.choices = [cat_choice]

        classification_service.client.chat.completions.create.side_effect = [gate_response, cat_response]

        # Same character in different Unicode forms
        subject_nfc = "café"  # NFC form
        subject_nfd = "café"  # NFD form (e + combining acute)

        result1 = classification_service.classify_email(subject_nfc, "pricing")

        classification_service.client.chat.completions.create.side_effect = [gate_response, cat_response]
        result2 = classification_service.classify_email(subject_nfd, "pricing")

        # Both should classify the same way
        assert result1['category'] == result2['category']

    def test_surrogate_pairs_handling(self, classification_service):
        """Test handling of Unicode surrogate pairs (emoji, rare characters)."""
        gate_response = Mock()
        gate_choice = Mock()
        gate_message = Mock()
        gate_message.content = '{"is_business_related": true, "confidence": 0.8, "reasoning": "Business"}'
        gate_choice.message = gate_message
        gate_response.choices = [gate_choice]

        cat_response = Mock()
        cat_choice = Mock()
        cat_message = Mock()
        cat_message.content = '{"category": "order_tracking", "confidence": 0.81, "reasoning": "Tracking"}'
        cat_choice.message = cat_message
        cat_response.choices = [cat_choice]

        classification_service.client.chat.completions.create.side_effect = [gate_response, cat_response]

        # Emoji that requires surrogate pairs
        subject = "Track my order 🚀🌟"
        body = "Where is shipment? 🎉🎊"

        result = classification_service.classify_email(subject, body)

        assert result['category'] == 'order_tracking'

    def test_bidi_text_handling(self, reply_service):
        """Test handling of bidirectional text (mixed LTR and RTL)."""
        # Mixed English and Arabic
        sender = "محمد.smith@example.com"
        result = reply_service._extract_customer_name(sender)

        # Should extract the local part
        assert "محمد" in result or "smith" in result

    def test_combining_characters(self, classification_service):
        """Test handling of combining diacritical marks."""
        gate_response = Mock()
        gate_choice = Mock()
        gate_message = Mock()
        gate_message.content = '{"is_business_related": true, "confidence": 0.8, "reasoning": "Business"}'
        gate_choice.message = gate_message
        gate_response.choices = [gate_choice]

        cat_response = Mock()
        cat_choice = Mock()
        cat_message = Mock()
        cat_message.content = '{"category": "pricing_inquiry", "confidence": 0.82, "reasoning": "Price"}'
        cat_choice.message = cat_message
        cat_response.choices = [cat_choice]

        classification_service.client.chat.completions.create.side_effect = [gate_response, cat_response]

        # Text with combining characters
        subject = "Prîcé înquîry"
        body = "Nëëd prïcïng"

        result = classification_service.classify_email(subject, body)

        assert result['category'] == 'pricing_inquiry'
