"""
Unit tests for PII detection and redaction service.

Tests cover:
- PII detection for all supported types
- Redaction at different levels (NONE, PARTIAL, FULL)
- Edge cases and mixed PII content
- Privacy validation and sanitization
"""

import pytest
from services.pii_service import PIIService, PIIType, RedactionLevel, get_pii_service


class TestPIIDetection:
    """Test PII detection across all supported types."""

    def setup_method(self):
        self.service = PIIService()

    def test_detect_email_address(self):
        text = "Please contact me at john.doe@example.com for details."
        detected = self.service.detect_pii(text, [PIIType.EMAIL])
        assert PIIType.EMAIL in detected
        assert "john.doe@example.com" in detected[PIIType.EMAIL]

    def test_detect_multiple_emails(self):
        text = "CC: alice@test.com and bob@company.org"
        detected = self.service.detect_pii(text, [PIIType.EMAIL])
        assert len(detected[PIIType.EMAIL]) == 2

    def test_detect_us_phone_number(self):
        text = "Call me at (555) 123-4567"
        detected = self.service.detect_pii(text, [PIIType.PHONE])
        assert PIIType.PHONE in detected

    def test_detect_chinese_phone_number(self):
        text = "我的手机号是 13812345678"
        detected = self.service.detect_pii(text, [PIIType.PHONE])
        assert PIIType.PHONE in detected

    def test_detect_credit_card(self):
        text = "Card number: 4111-1111-1111-1111"
        detected = self.service.detect_pii(text, [PIIType.CREDIT_CARD])
        assert PIIType.CREDIT_CARD in detected

    def test_detect_credit_card_no_dashes(self):
        text = "Card: 4111111111111111"
        detected = self.service.detect_pii(text, [PIIType.CREDIT_CARD])
        assert PIIType.CREDIT_CARD in detected

    def test_detect_ssn(self):
        text = "SSN: 123-45-6789"
        detected = self.service.detect_pii(text, [PIIType.SSN])
        assert PIIType.SSN in detected
        assert "123-45-6789" in detected[PIIType.SSN]

    def test_detect_chinese_id_number(self):
        text = "身份证号: 110101199001011234"
        detected = self.service.detect_pii(text, [PIIType.ID_NUMBER])
        assert PIIType.ID_NUMBER in detected

    def test_no_pii_in_clean_text(self):
        text = "This is a normal business email about shipping schedules."
        detected = self.service.detect_pii(text)
        assert len(detected) == 0

    def test_detect_all_types_mixed(self):
        text = (
            "Contact: user@test.com, phone 13912345678, "
            "card 4111-1111-1111-1111, SSN 123-45-6789"
        )
        detected = self.service.detect_pii(text)
        assert PIIType.EMAIL in detected
        assert PIIType.PHONE in detected
        assert PIIType.CREDIT_CARD in detected
        assert PIIType.SSN in detected

    def test_detect_specific_types_only(self):
        text = "Email: a@b.com, SSN: 123-45-6789"
        detected = self.service.detect_pii(text, [PIIType.EMAIL])
        assert PIIType.EMAIL in detected
        assert PIIType.SSN not in detected


class TestPIIRedaction:
    """Test PII redaction at different levels."""

    def setup_method(self):
        self.service = PIIService()

    def test_full_redaction_email(self):
        text = "Contact john@example.com for info"
        redacted, counts = self.service.redact_pii(text, RedactionLevel.FULL, [PIIType.EMAIL])
        assert "john@example.com" not in redacted
        assert "[EMAIL_REDACTED]" in redacted
        assert counts[PIIType.EMAIL] == 1

    def test_full_redaction_phone(self):
        text = "Call 13812345678 now"
        redacted, counts = self.service.redact_pii(text, RedactionLevel.FULL, [PIIType.PHONE])
        assert "13812345678" not in redacted
        assert "[PHONE_REDACTED]" in redacted

    def test_full_redaction_credit_card(self):
        text = "Pay with 4111-1111-1111-1111"
        redacted, counts = self.service.redact_pii(text, RedactionLevel.FULL, [PIIType.CREDIT_CARD])
        assert "4111" not in redacted
        assert "[CREDIT_CARD_REDACTED]" in redacted

    def test_full_redaction_ssn(self):
        text = "SSN is 123-45-6789"
        redacted, counts = self.service.redact_pii(text, RedactionLevel.FULL, [PIIType.SSN])
        assert "123-45-6789" not in redacted
        assert "[SSN_REDACTED]" in redacted

    def test_partial_redaction_email(self):
        text = "Contact john@example.com"
        redacted, counts = self.service.redact_pii(text, RedactionLevel.PARTIAL, [PIIType.EMAIL])
        assert "john@example.com" not in redacted
        assert "@example.com" in redacted
        assert redacted.startswith("Contact j")

    def test_partial_redaction_phone(self):
        text = "Call 13812345678"
        redacted, counts = self.service.redact_pii(text, RedactionLevel.PARTIAL, [PIIType.PHONE])
        assert "138" in redacted
        assert "5678" in redacted
        assert "****" in redacted

    def test_partial_redaction_ssn(self):
        text = "SSN: 123-45-6789"
        redacted, _ = self.service.redact_pii(text, RedactionLevel.PARTIAL, [PIIType.SSN])
        assert "6789" in redacted
        assert "***-**-" in redacted

    def test_no_redaction(self):
        text = "Contact john@example.com"
        redacted, counts = self.service.redact_pii(text, RedactionLevel.NONE)
        assert redacted == text
        assert counts == {}

    def test_redact_multiple_types(self):
        text = "Email: a@b.com, SSN: 123-45-6789"
        redacted, counts = self.service.redact_pii(text, RedactionLevel.FULL)
        assert "[EMAIL_REDACTED]" in redacted
        assert "[SSN_REDACTED]" in redacted
        assert PIIType.EMAIL in counts
        assert PIIType.SSN in counts

    def test_redact_empty_string(self):
        redacted, counts = self.service.redact_pii("", RedactionLevel.FULL)
        assert redacted == ""
        assert counts == {}


class TestContainsPII:
    """Test PII presence checking."""

    def setup_method(self):
        self.service = PIIService()

    def test_contains_pii_true(self):
        assert self.service.contains_pii("Email me at test@test.com")

    def test_contains_pii_false(self):
        assert not self.service.contains_pii("Normal business text here")

    def test_contains_pii_specific_type(self):
        text = "SSN: 123-45-6789"
        assert self.service.contains_pii(text, [PIIType.SSN])
        assert not self.service.contains_pii(text, [PIIType.CREDIT_CARD])


class TestPIISummary:
    """Test PII summary generation."""

    def setup_method(self):
        self.service = PIIService()

    def test_summary_with_pii(self):
        text = "Contact: user@test.com, phone 13912345678"
        summary = self.service.get_pii_summary(text)
        assert summary['contains_pii'] is True
        assert summary['total_instances'] >= 2
        assert 'email' in summary['pii_types_found']
        assert 'phone' in summary['pii_types_found']

    def test_summary_without_pii(self):
        summary = self.service.get_pii_summary("Clean text")
        assert summary['contains_pii'] is False
        assert summary['total_instances'] == 0


class TestSanitizeForLogging:
    """Test log sanitization."""

    def setup_method(self):
        self.service = PIIService()

    def test_sanitize_redacts_pii(self):
        text = "User john@example.com called about order"
        sanitized = self.service.sanitize_for_logging(text)
        assert "john@example.com" not in sanitized

    def test_sanitize_truncates_long_text(self):
        text = "A" * 500
        sanitized = self.service.sanitize_for_logging(text, max_length=100)
        assert len(sanitized) <= 103  # 100 + "..."

    def test_sanitize_short_clean_text(self):
        text = "Normal text"
        sanitized = self.service.sanitize_for_logging(text)
        assert sanitized == "Normal text"


class TestEmailPrivacyValidation:
    """Test email privacy validation."""

    def setup_method(self):
        self.service = PIIService()

    def test_high_risk_credit_card(self):
        result = self.service.validate_email_privacy(
            "Payment info",
            "My card is 4111-1111-1111-1111"
        )
        assert result['risk_level'] == 'high'
        assert result['should_flag_for_review'] is True

    def test_high_risk_ssn(self):
        result = self.service.validate_email_privacy(
            "Tax form",
            "SSN: 123-45-6789"
        )
        assert result['risk_level'] == 'high'

    def test_medium_risk_phone(self):
        result = self.service.validate_email_privacy(
            "Contact info",
            "Call me at 13812345678"
        )
        assert result['risk_level'] == 'medium'
        assert result['should_flag_for_review'] is True

    def test_low_risk_clean(self):
        result = self.service.validate_email_privacy(
            "Order inquiry",
            "When will my order arrive?"
        )
        assert result['risk_level'] == 'low'
        assert result['should_flag_for_review'] is False

    def test_recommendations_for_credit_card(self):
        result = self.service.validate_email_privacy(
            "Payment",
            "Card: 4111-1111-1111-1111"
        )
        assert any("Credit card" in r for r in result['recommendations'])


class TestSingleton:
    """Test singleton pattern."""

    def test_get_pii_service_returns_same_instance(self):
        s1 = get_pii_service()
        s2 = get_pii_service()
        assert s1 is s2
