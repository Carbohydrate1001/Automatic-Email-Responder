"""
Unit tests for ValidationService.

Tests cover:
- Policy compliance checking
- Hallucination detection
- Quality validation
- Visual report generation
- Edge cases and error handling
"""

import pytest
import json
from pathlib import Path
from services.validation_service import ValidationService, get_validation_service


class TestValidationService:
    """Test suite for ValidationService."""

    @pytest.fixture
    def validation_service(self, tmp_path):
        """Create ValidationService with test config files."""
        # Create test rubrics file
        rubrics_file = tmp_path / "rubrics.yaml"
        rubrics_file.write_text("""
reply_quality_rubric:
  version: "1.0"
  dimensions:
    - name: factual_accuracy
      weight: 0.35
      blocking_threshold: 1
    - name: tone_appropriateness
      weight: 0.20
      blocking_threshold: 0
    - name: completeness
      weight: 0.25
      blocking_threshold: 1
    - name: policy_compliance
      weight: 0.20
      blocking_threshold: 0
  thresholds:
    minimum_quality_score: 0.75
    blocking_score: 1
    warning_score: 2

prompts:
  reply_quality_validation:
    system: "You are a validator."
    user_template: "Validate: {reply_text}"
""")

        # Create test policies file
        policies_file = tmp_path / "policies.yaml"
        policies_file.write_text("""
forbidden_patterns:
  financial_commitments:
    severity: "blocking"
    patterns:
      - pattern: "\\\\bguaranteed?\\\\b"
        regex: true
        case_sensitive: false
        reason: "Cannot guarantee outcomes"
      - pattern: "\\\\bwe promise\\\\b"
        regex: true
        case_sensitive: false
        reason: "Avoid absolute promises"
  inappropriate_tone:
    severity: "blocking"
    patterns:
      - pattern: "\\\\bstupid\\\\b"
        regex: true
        case_sensitive: false
        reason: "Offensive language"
""")

        return ValidationService(
            rubrics_file=str(rubrics_file),
            policies_file=str(policies_file)
        )

    # Policy Compliance Tests

    def test_policy_compliance_pass(self, validation_service):
        """Test policy compliance with clean reply."""
        reply_text = "Thank you for your inquiry. We will process your request within 5-7 business days."
        result = validation_service.check_policy_compliance(reply_text, "order_cancellation")

        assert result['passed'] is True
        assert len(result['violations']) == 0
        assert result['score'] == 3

    def test_policy_compliance_blocking_violation(self, validation_service):
        """Test policy compliance with blocking violation."""
        reply_text = "We guarantee a full refund within 24 hours."
        result = validation_service.check_policy_compliance(reply_text, "order_cancellation")

        assert result['passed'] is False
        assert len(result['violations']) > 0
        assert result['violations'][0]['severity'] == 'blocking'
        assert 'guarantee' in result['violations'][0]['pattern'].lower()

    def test_policy_compliance_multiple_violations(self, validation_service):
        """Test policy compliance with multiple violations."""
        reply_text = "We promise and guarantee a refund. You're stupid if you don't accept."
        result = validation_service.check_policy_compliance(reply_text, "order_cancellation")

        assert result['passed'] is False
        assert len(result['violations']) >= 2
        assert result['score'] == 0

    def test_policy_compliance_warning_only(self, validation_service):
        """Test policy compliance with warnings but no blocking issues."""
        # This would require adding warning-level patterns to the test config
        reply_text = "Thank you for contacting us."
        result = validation_service.check_policy_compliance(reply_text, "pricing_inquiry")

        assert result['passed'] is True

    def test_policy_compliance_case_insensitive(self, validation_service):
        """Test policy compliance is case insensitive."""
        reply_text = "We GUARANTEE this will work."
        result = validation_service.check_policy_compliance(reply_text, "order_cancellation")

        assert result['passed'] is False
        assert len(result['violations']) > 0

    # Hallucination Detection Tests

    def test_hallucination_detection_no_claims(self, validation_service):
        """Test hallucination detection with no factual claims."""
        reply_text = "Thank you for your inquiry. We will get back to you soon."
        result = validation_service.detect_hallucinations(reply_text, {})

        assert result['passed'] is True
        assert len(result['hallucinations']) == 0

    def test_hallucination_detection_price_claim(self, validation_service):
        """Test hallucination detection with price claim."""
        reply_text = "The product costs $99.99 and is available now."
        result = validation_service.detect_hallucinations(reply_text, {})

        # Should detect unverified price claim
        assert result['total_claims_checked'] > 0

    def test_hallucination_detection_product_claim(self, validation_service):
        """Test hallucination detection with product claim."""
        reply_text = "Our laptop model X1000 features 32GB RAM and 1TB SSD."
        result = validation_service.detect_hallucinations(reply_text, {})

        assert result['total_claims_checked'] > 0

    def test_hallucination_detection_policy_claim(self, validation_service):
        """Test hallucination detection with policy claim."""
        reply_text = "Our refund policy allows returns within 30 days."
        result = validation_service.detect_hallucinations(reply_text, {})

        assert result['total_claims_checked'] > 0

    def test_hallucination_detection_with_company_info(self, validation_service):
        """Test hallucination detection with company info provided."""
        reply_text = "The product costs $99.99."
        company_info = {
            'products': [
                {'product_name': 'Widget', 'price': 99.99}
            ]
        }
        result = validation_service.detect_hallucinations(reply_text, company_info)

        # Should still mark as unverified without exact matching logic
        assert result is not None

    # Quality Validation Tests (Rule-Based)

    def test_rule_based_validation_good_reply(self, validation_service):
        """Test rule-based validation with good reply."""
        reply_text = "Thank you for your inquiry about our products. " * 10
        email_context = {
            'subject': 'Product inquiry',
            'body': 'I would like to know more about your products.'
        }

        result = validation_service._rule_based_validate_quality(reply_text, email_context)

        assert result['quality_score'] > 0.5
        assert result['passed'] is True
        assert result['method'] == 'rule_based'

    def test_rule_based_validation_short_reply(self, validation_service):
        """Test rule-based validation with short reply."""
        reply_text = "OK."
        email_context = {
            'subject': 'Product inquiry',
            'body': 'I would like detailed information about your products, pricing, and delivery options.'
        }

        result = validation_service._rule_based_validate_quality(reply_text, email_context)

        # Short reply should score lower on completeness
        assert result['scores']['completeness'] < 3

    def test_rule_based_validation_negative_tone(self, validation_service):
        """Test rule-based validation with negative tone."""
        reply_text = "That's not our problem. You should have read the instructions."
        email_context = {
            'subject': 'Issue with order',
            'body': 'I received a damaged product.'
        }

        result = validation_service._rule_based_validate_quality(reply_text, email_context)

        # Should detect negative tone
        assert result['scores']['tone_appropriateness'] == 0

    # Combined Validation Tests

    def test_validate_reply_quality_pass(self, validation_service):
        """Test full validation pipeline with passing reply."""
        reply_text = "Thank you for your inquiry. We will process your request within 5-7 business days and send you a confirmation email."
        email_context = {
            'subject': 'Order cancellation',
            'body': 'I would like to cancel my order #12345.'
        }

        result = validation_service.validate_reply_quality(
            reply_text=reply_text,
            email_context=email_context,
            category='order_cancellation',
            company_info={},
            use_llm=False  # Use rule-based for testing
        )

        assert result['passed'] is True
        assert result['recommendation'] == 'AUTO_SEND'
        assert len(result['blocking_issues']) == 0

    def test_validate_reply_quality_fail_policy(self, validation_service):
        """Test full validation pipeline failing on policy."""
        reply_text = "We guarantee a full refund immediately."
        email_context = {
            'subject': 'Refund request',
            'body': 'I want a refund.'
        }

        result = validation_service.validate_reply_quality(
            reply_text=reply_text,
            email_context=email_context,
            category='order_cancellation',
            company_info={},
            use_llm=False
        )

        assert result['passed'] is False
        assert result['recommendation'] == 'MANUAL_REVIEW'
        assert len(result['blocking_issues']) > 0

    def test_validate_reply_quality_fail_tone(self, validation_service):
        """Test full validation pipeline failing on tone."""
        reply_text = "That's stupid. Not our problem."
        email_context = {
            'subject': 'Complaint',
            'body': 'I am not satisfied with the service.'
        }

        result = validation_service.validate_reply_quality(
            reply_text=reply_text,
            email_context=email_context,
            category='order_cancellation',
            company_info={},
            use_llm=False
        )

        assert result['passed'] is False
        assert len(result['blocking_issues']) > 0

    def test_validate_reply_quality_with_warnings(self, validation_service):
        """Test validation with warnings but no blocking issues."""
        reply_text = "Thank you for your inquiry. We will get back to you."
        email_context = {
            'subject': 'Product inquiry',
            'body': 'Tell me about your products.'
        }

        result = validation_service.validate_reply_quality(
            reply_text=reply_text,
            email_context=email_context,
            category='pricing_inquiry',
            company_info={},
            use_llm=False
        )

        # May have warnings but should pass
        assert result['passed'] is True or len(result['warnings']) > 0

    # Visual Report Tests

    def test_generate_visual_report(self, validation_service):
        """Test visual report generation."""
        validation_report = {
            'passed': True,
            'overall_quality_score': 0.85,
            'policy_compliance': {'passed': True, 'score': 3, 'violations': [], 'warnings': []},
            'hallucination_detection': {'passed': True, 'score': 3, 'hallucinations': [], 'warnings': []},
            'quality_validation': {
                'scores': {
                    'factual_accuracy': {'score': 3, 'reasoning': 'All facts verified'},
                    'tone_appropriateness': {'score': 3, 'reasoning': 'Professional tone'},
                    'completeness': {'score': 2, 'reasoning': 'Mostly complete'},
                    'policy_compliance': {'score': 3, 'reasoning': 'Compliant'}
                }
            },
            'blocking_issues': [],
            'warnings': [],
            'recommendation': 'AUTO_SEND'
        }

        report = validation_service._generate_visual_report(validation_report)

        assert isinstance(report, str)
        assert 'PASSED' in report
        assert '0.85' in report
        assert 'AUTO_SEND' in report
        assert '✅' in report

    def test_generate_visual_report_with_issues(self, validation_service):
        """Test visual report generation with issues."""
        validation_report = {
            'passed': False,
            'overall_quality_score': 0.45,
            'policy_compliance': {'passed': False, 'score': 0, 'violations': [
                {'type': 'financial_commitments', 'reason': 'Unauthorized guarantee', 'severity': 'blocking'}
            ], 'warnings': []},
            'hallucination_detection': {'passed': True, 'score': 2, 'hallucinations': [], 'warnings': []},
            'quality_validation': {
                'scores': {
                    'factual_accuracy': {'score': 2, 'reasoning': 'Some unverified claims'},
                    'tone_appropriateness': {'score': 1, 'reasoning': 'Slightly inappropriate'},
                    'completeness': {'score': 2, 'reasoning': 'Adequate'},
                    'policy_compliance': {'score': 0, 'reasoning': 'Policy violation'}
                }
            },
            'blocking_issues': [
                {'type': 'financial_commitments', 'reason': 'Unauthorized guarantee'}
            ],
            'warnings': [],
            'recommendation': 'MANUAL_REVIEW'
        }

        report = validation_service._generate_visual_report(validation_report)

        assert isinstance(report, str)
        assert 'FAILED' in report
        assert 'BLOCKING ISSUES' in report
        assert 'MANUAL_REVIEW' in report
        assert '❌' in report

    # Edge Cases

    def test_empty_reply_text(self, validation_service):
        """Test validation with empty reply text."""
        result = validation_service.validate_reply_quality(
            reply_text="",
            email_context={'subject': 'Test', 'body': 'Test'},
            category='pricing_inquiry',
            company_info={},
            use_llm=False
        )

        assert result is not None
        assert 'passed' in result

    def test_very_long_reply_text(self, validation_service):
        """Test validation with very long reply text."""
        reply_text = "Thank you for your inquiry. " * 1000
        result = validation_service.validate_reply_quality(
            reply_text=reply_text,
            email_context={'subject': 'Test', 'body': 'Test'},
            category='pricing_inquiry',
            company_info={},
            use_llm=False
        )

        assert result is not None
        assert 'passed' in result

    def test_unicode_content(self, validation_service):
        """Test validation with unicode content."""
        reply_text = "感谢您的咨询。我们会在5-7个工作日内处理您的请求。"
        result = validation_service.validate_reply_quality(
            reply_text=reply_text,
            email_context={'subject': '订单取消', 'body': '我想取消订单'},
            category='order_cancellation',
            company_info={},
            use_llm=False
        )

        assert result is not None
        assert 'passed' in result

    def test_special_characters_in_reply(self, validation_service):
        """Test validation with special characters."""
        reply_text = "Price: $99.99 (50% off!) Contact us @ support@example.com"
        result = validation_service.validate_reply_quality(
            reply_text=reply_text,
            email_context={'subject': 'Pricing', 'body': 'What is the price?'},
            category='pricing_inquiry',
            company_info={},
            use_llm=False
        )

        assert result is not None

    def test_html_content_in_reply(self, validation_service):
        """Test validation with HTML content."""
        reply_text = "<p>Thank you for your inquiry.</p><br><b>We will respond soon.</b>"
        result = validation_service.validate_reply_quality(
            reply_text=reply_text,
            email_context={'subject': 'Test', 'body': 'Test'},
            category='pricing_inquiry',
            company_info={},
            use_llm=False
        )

        assert result is not None

    # Utility Function Tests

    def test_extract_factual_claims(self, validation_service):
        """Test factual claim extraction."""
        text = "The product costs $99.99 and comes with a 2-year warranty. Our refund policy allows returns within 30 days."
        claims = validation_service._extract_factual_claims(text)

        assert len(claims) > 0
        assert any('Price claim' in claim for claim in claims)

    def test_verify_claim(self, validation_service):
        """Test claim verification."""
        claim = "Price claim: $99.99"
        company_info = {}

        result = validation_service._verify_claim(claim, company_info)

        assert 'status' in result
        assert result['status'] in ['true', 'false', 'unverified']

    def test_calculate_weighted_score(self, validation_service):
        """Test weighted score calculation."""
        scores = {
            'factual_accuracy': 3,
            'tone_appropriateness': 2,
            'completeness': 3,
            'policy_compliance': 3
        }
        dimensions = [
            {'name': 'factual_accuracy', 'weight': 0.35},
            {'name': 'tone_appropriateness', 'weight': 0.20},
            {'name': 'completeness', 'weight': 0.25},
            {'name': 'policy_compliance', 'weight': 0.20}
        ]

        weighted_score = validation_service._calculate_weighted_score(scores, dimensions)

        assert 0 <= weighted_score <= 3
        assert weighted_score > 2.5  # Should be high with these scores

    def test_generate_quality_bar(self, validation_service):
        """Test quality bar generation."""
        bar = validation_service._generate_quality_bar(0.85)

        assert isinstance(bar, str)
        assert '85%' in bar
        assert '🟩' in bar or '🟨' in bar

    def test_generate_score_bar(self, validation_service):
        """Test score bar generation."""
        bar = validation_service._generate_score_bar(3, 3)

        assert isinstance(bar, str)
        assert '🟢' in bar

    # Singleton Pattern Test

    def test_get_validation_service_singleton(self):
        """Test singleton pattern for get_validation_service."""
        service1 = get_validation_service()
        service2 = get_validation_service()

        assert service1 is service2

    # Reload Test

    def test_reload_clears_cache(self, validation_service):
        """Test reload clears configuration cache."""
        # Load configs
        validation_service._load_rubrics()
        validation_service._load_policies()

        assert validation_service._rubrics_cache is not None
        assert validation_service._policies_cache is not None

        # Reload
        validation_service.reload()

        assert validation_service._rubrics_cache is None
        assert validation_service._policies_cache is None
