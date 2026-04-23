"""
Unit tests for reply_service.py
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from services.reply_service import ReplyService


class TestReplyService:
    """Test suite for ReplyService."""

    @pytest.fixture
    def service(self, mock_config):
        """Create ReplyService instance with mocked config."""
        with patch('services.reply_service.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            service = ReplyService()
            service.client = mock_client
            return service

    def test_extract_sender_local_part_standard_email(self, service):
        """Test extracting local part from standard email."""
        result = service._extract_sender_local_part("john.doe@example.com")
        assert result == "john.doe"

    def test_extract_sender_local_part_no_at_symbol(self, service):
        """Test extracting local part from email without @ symbol."""
        result = service._extract_sender_local_part("johndoe")
        assert result == "johndoe"

    def test_extract_sender_local_part_empty_string(self, service):
        """Test extracting local part from empty string."""
        result = service._extract_sender_local_part("")
        assert result == "客户"

    def test_extract_sender_local_part_none(self, service):
        """Test extracting local part from None."""
        result = service._extract_sender_local_part(None)
        assert result == "客户"

    def test_extract_customer_name_standard(self, service):
        """Test extracting customer name from standard email."""
        result = service._extract_customer_name("john.doe@example.com")
        assert result == "john doe"

    def test_extract_customer_name_with_underscores(self, service):
        """Test extracting customer name with underscores."""
        result = service._extract_customer_name("john_doe@example.com")
        assert result == "john doe"

    def test_extract_customer_name_with_hyphens(self, service):
        """Test extracting customer name with hyphens."""
        result = service._extract_customer_name("john-doe@example.com")
        assert result == "john doe"

    def test_extract_customer_name_mixed_separators(self, service):
        """Test extracting customer name with mixed separators."""
        result = service._extract_customer_name("john.doe_smith-jr@example.com")
        assert result == "john doe smith jr"

    def test_resolve_base_date_valid_iso_format(self, service):
        """Test resolving base date from valid ISO format."""
        received_at = "2026-04-23T10:00:00Z"
        result = service._resolve_base_date(received_at)
        assert result.year == 2026
        assert result.month == 4
        assert result.day == 23
        assert result.hour == 10

    def test_resolve_base_date_with_timezone(self, service):
        """Test resolving base date with timezone."""
        received_at = "2026-04-23T10:00:00+08:00"
        result = service._resolve_base_date(received_at)
        assert result.tzinfo is not None

    def test_resolve_base_date_empty_string(self, service):
        """Test resolving base date from empty string returns current time."""
        result = service._resolve_base_date("")
        assert isinstance(result, datetime)
        assert result.tzinfo is not None

    def test_resolve_base_date_invalid_format(self, service):
        """Test resolving base date from invalid format returns current time."""
        result = service._resolve_base_date("invalid-date")
        assert isinstance(result, datetime)

    def test_select_product_exact_match(self, service, sample_products):
        """Test product selection with exact name match."""
        result = service._select_product(
            "Sea Freight inquiry",
            "I need sea freight service",
            sample_products
        )
        assert result is not None
        assert result['product_name'] == 'Sea Freight (Standard)'

    def test_select_product_case_insensitive(self, service, sample_products):
        """Test product selection is case insensitive."""
        result = service._select_product(
            "AIR FREIGHT INQUIRY",
            "I need AIR FREIGHT service",
            sample_products
        )
        assert result is not None
        assert result['product_name'] == 'Air Freight (Express)'

    def test_select_product_no_match_returns_first(self, service, sample_products):
        """Test product selection returns first product when no match."""
        result = service._select_product(
            "General inquiry",
            "I need shipping",
            sample_products
        )
        assert result is not None
        assert result == sample_products[0]

    def test_select_product_empty_list(self, service):
        """Test product selection with empty product list."""
        result = service._select_product("Test", "Test", [])
        assert result is None

    @patch('services.reply_service.CompanyInfoService')
    def test_generate_pricing_template_reply_with_product(self, mock_company_service, service):
        """Test generating pricing template reply with product match."""
        mock_service_instance = Mock()
        mock_service_instance.list_products.return_value = [
            {
                'product_name': 'Sea Freight (Standard)',
                'unit_price': 120.0,
                'currency': 'USD',
                'min_order_quantity': 1,
                'delivery_lead_time_days': 30
            }
        ]
        mock_company_service.return_value = mock_service_instance

        result = service._generate_pricing_template_reply(
            "customer@example.com",
            "Sea freight inquiry",
            "I need sea freight pricing",
            "2026-04-23T10:00:00Z"
        )

        assert "customer" in result
        assert "Sea Freight (Standard)" in result
        assert "USD 120.0" in result
        assert "1" in result  # MOQ
        assert "感谢您对我们产品的询价" in result

    @patch('services.reply_service.CompanyInfoService')
    def test_generate_pricing_template_reply_no_products(self, mock_company_service, service):
        """Test generating pricing template reply with no products."""
        mock_service_instance = Mock()
        mock_service_instance.list_products.return_value = []
        mock_company_service.return_value = mock_service_instance

        result = service._generate_pricing_template_reply(
            "customer@example.com",
            "Inquiry",
            "I need pricing",
            "2026-04-23T10:00:00Z"
        )

        assert "未配置产品" in result
        assert "N/A" in result

    def test_generate_order_cancellation_template_reply(self, service):
        """Test generating order cancellation template reply."""
        result = service._generate_order_cancellation_template_reply(
            "customer@example.com",
            "Cancel order",
            "I want to cancel my order"
        )

        assert "customer" in result
        assert "取消订单" in result or "退款" in result
        assert "7" in result  # Processing time

    def test_generate_order_tracking_template_reply(self, service):
        """Test generating order tracking template reply."""
        result = service._generate_order_tracking_template_reply(
            "customer@example.com",
            "2026-04-23T10:00:00Z",
            "Track order",
            "Where is my order?"
        )

        assert "customer" in result
        assert "订单" in result
        assert "ORD" in result  # Order number prefix

    def test_generate_shipping_time_template_reply(self, service):
        """Test generating shipping time template reply."""
        result = service._generate_shipping_time_template_reply(
            "customer@example.com",
            "2026-04-23T10:00:00Z",
            "Shipping time",
            "How long does shipping take?"
        )

        assert "customer" in result
        assert "运输时间" in result or "预计" in result

    def test_generate_shipping_exception_template_reply(self, service):
        """Test generating shipping exception template reply."""
        result = service._generate_shipping_exception_template_reply(
            "customer@example.com",
            "Delayed shipment",
            "My order #12345 is delayed"
        )

        assert "customer" in result
        assert "12345" in result or "异常" in result

    def test_generate_billing_invoice_template_reply(self, service):
        """Test generating billing invoice template reply."""
        result = service._generate_billing_invoice_template_reply(
            "customer@example.com",
            "2026-04-23T10:00:00Z",
            "Invoice request",
            "I need an invoice"
        )

        assert "customer" in result
        assert "发票" in result or "账单" in result
        assert "INV" in result  # Invoice number prefix

    def test_generate_non_business_template_reply(self, service):
        """Test generating non-business template reply."""
        result = service._generate_non_business_template_reply()
        assert result == ""

    @patch('services.reply_service.CompanyInfoService')
    def test_generate_reply_pricing_inquiry(self, mock_company_service, service):
        """Test generate_reply for pricing inquiry category."""
        mock_service_instance = Mock()
        mock_service_instance.list_products.return_value = [
            {
                'product_name': 'Sea Freight (Standard)',
                'unit_price': 120.0,
                'currency': 'USD',
                'min_order_quantity': 1,
                'delivery_lead_time_days': 30
            }
        ]
        mock_company_service.return_value = mock_service_instance

        result = service.generate_reply(
            "customer@example.com",
            "2026-04-23T10:00:00Z",
            "Price inquiry",
            "I need sea freight pricing",
            "pricing_inquiry",
            "Customer asks for pricing"
        )

        assert len(result) > 0
        assert "Sea Freight" in result

    def test_generate_reply_order_cancellation(self, service):
        """Test generate_reply for order cancellation category."""
        result = service.generate_reply(
            "customer@example.com",
            "2026-04-23T10:00:00Z",
            "Cancel order",
            "I want to cancel",
            "order_cancellation",
            "Cancellation request"
        )

        assert len(result) > 0
        assert "取消" in result or "退款" in result

    def test_generate_reply_non_business(self, service):
        """Test generate_reply for non-business category returns empty."""
        result = service.generate_reply(
            "no-reply@microsoft.com",
            "2026-04-23T10:00:00Z",
            "OneDrive alert",
            "Storage full",
            "non_business",
            "System notification"
        )

        assert result == ""

    def test_generate_reply_unmapped_category_uses_gpt(self, service):
        """Test generate_reply uses GPT for unmapped categories."""
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = "Thank you for your inquiry. We will respond shortly."
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        service.client.chat.completions.create.return_value = mock_response

        result = service.generate_reply(
            "customer@example.com",
            "2026-04-23T10:00:00Z",
            "Custom inquiry",
            "Special request",
            "custom_category",
            "Custom reasoning"
        )

        assert len(result) > 0
        assert result == "Thank you for your inquiry. We will respond shortly."

    def test_extract_order_number_from_text_with_hash(self, service):
        """Test extracting order number with # prefix."""
        text = "My order #12345 is delayed"
        result = service._extract_order_number_from_text(text)
        assert result == "12345"

    def test_extract_order_number_from_text_with_word(self, service):
        """Test extracting order number with 'order' word."""
        text = "Order 67890 has not arrived"
        result = service._extract_order_number_from_text(text)
        assert result == "67890"

    def test_extract_order_number_from_text_no_match(self, service):
        """Test extracting order number when none found."""
        text = "Where is my shipment?"
        result = service._extract_order_number_from_text(text)
        assert result == "未提供"

    def test_summarize_exception_from_body_html_stripping(self, service):
        """Test exception summarization strips HTML."""
        body = "<p>My shipment is <b>delayed</b></p>"
        result = service._summarize_exception_from_body(body)
        assert "<p>" not in result
        assert "<b>" not in result
        assert "delayed" in result

    def test_summarize_exception_from_body_truncation(self, service):
        """Test exception summarization truncates long text."""
        body = "Exception " * 100
        result = service._summarize_exception_from_body(body)
        assert len(result) <= 200

    def test_summarize_exception_from_body_empty(self, service):
        """Test exception summarization with empty body."""
        result = service._summarize_exception_from_body("")
        assert result == "客户报告运输异常"

    def test_threshold_attribute(self, service):
        """Test service has threshold attribute from config."""
        assert hasattr(service, 'threshold')
        assert service.threshold == 0.75
