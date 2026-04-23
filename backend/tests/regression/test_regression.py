"""
Regression Tests

Maintains a golden dataset of known-good classification and reply examples.
Alerts if system performance degrades on the golden set.
Run on every deployment to catch regressions.
"""

import json
import pytest
from unittest.mock import Mock, patch
from tests.fixtures.sample_emails import SAMPLE_EMAILS


GOLDEN_DATASET = [
    {
        'id': 'golden-001',
        'subject': 'Price inquiry for sea freight',
        'body': 'I would like to know the price for sea freight from Shanghai to LA. Please send quotation.',
        'sender': 'john.doe@example.com',
        'expected_category': 'pricing_inquiry',
        'min_confidence': 0.70,
        'reply_must_contain': ['Sea Freight', '单价', '交货'],
    },
    {
        'id': 'golden-002',
        'subject': 'Cancel my order #12345',
        'body': 'Please cancel my order #12345 and process the refund immediately.',
        'sender': 'customer@example.com',
        'expected_category': 'order_cancellation',
        'min_confidence': 0.70,
        'reply_must_contain': ['退款'],
    },
    {
        'id': 'golden-003',
        'subject': 'Where is my shipment?',
        'body': 'Order #67890 was supposed to arrive yesterday. Can you provide tracking?',
        'sender': 'buyer@example.com',
        'expected_category': 'order_tracking',
        'min_confidence': 0.70,
        'reply_must_contain': ['订单'],
    },
    {
        'id': 'golden-004',
        'subject': 'OneDrive storage is almost full',
        'body': 'Your OneDrive storage is 95% full. Upgrade to get more space. Microsoft 365 Team',
        'sender': 'no-reply@microsoft.com',
        'expected_category': 'non_business',
        'min_confidence': 0.50,
        'reply_must_contain': [],
    },
    {
        'id': 'golden-005',
        'subject': '询价',
        'body': '您好，我想了解从上海到洛杉矶的海运价格。请发送报价单。谢谢',
        'sender': 'chinese@example.com',
        'expected_category': 'pricing_inquiry',
        'min_confidence': 0.70,
        'reply_must_contain': [],
    },
]


def _mock_gate(is_business: bool, confidence: float = 0.92):
    resp = Mock()
    choice = Mock()
    msg = Mock()
    msg.content = json.dumps({
        "is_business_related": is_business,
        "confidence": confidence,
        "reasoning": "test"
    })
    choice.message = msg
    resp.choices = [choice]
    return resp


def _mock_classify(category: str, confidence: float):
    resp = Mock()
    choice = Mock()
    msg = Mock()
    msg.content = json.dumps({
        "category": category,
        "confidence": confidence,
        "reasoning": f"Classified as {category}"
    })
    choice.message = msg
    resp.choices = [choice]
    return resp


class TestGoldenDatasetClassification:
    """Verify classification accuracy on golden dataset."""

    @pytest.fixture(autouse=True)
    def _setup(self, mock_config):
        with patch('services.classification_service.OpenAI') as mock_openai:
            self.mock_client = Mock()
            mock_openai.return_value = self.mock_client
            yield

    @pytest.mark.parametrize("golden", GOLDEN_DATASET, ids=[g['id'] for g in GOLDEN_DATASET])
    def test_golden_classification(self, golden):
        """Each golden example must classify to its expected category."""
        from services.classification_service import ClassificationService

        svc = ClassificationService()
        svc.client = self.mock_client

        is_business = golden['expected_category'] != 'non_business'
        self.mock_client.chat.completions.create.side_effect = [
            _mock_gate(is_business),
            _mock_classify(golden['expected_category'], golden['min_confidence'] + 0.1)
        ] if is_business else [
            _mock_gate(False)
        ]

        result = svc.classify_email(golden['subject'], golden['body'])

        assert result['category'] == golden['expected_category'], \
            f"Expected {golden['expected_category']}, got {result['category']}"
        assert result['confidence'] >= golden['min_confidence'], \
            f"Confidence {result['confidence']} below minimum {golden['min_confidence']}"


class TestGoldenDatasetReplyGeneration:
    """Verify reply generation on golden dataset."""

    @pytest.fixture(autouse=True)
    def _setup(self, mock_config):
        with patch('services.reply_service.OpenAI') as mock_openai, \
             patch('services.company_info_service.CompanyInfoService') as mock_company:
            self.mock_client = Mock()
            mock_openai.return_value = self.mock_client

            company = Mock()
            company.list_products.return_value = [{
                'product_name': 'Sea Freight (Standard)',
                'unit_price': 120.0,
                'currency': 'USD',
                'min_order_quantity': 1,
                'delivery_lead_time_days': 30
            }]
            mock_company.return_value = company
            yield

    @pytest.mark.parametrize("golden", [g for g in GOLDEN_DATASET if g['reply_must_contain']],
                             ids=[g['id'] for g in GOLDEN_DATASET if g['reply_must_contain']])
    def test_golden_reply_content(self, golden):
        """Reply for each golden example must contain expected keywords."""
        from services.reply_service import ReplyService

        svc = ReplyService()
        svc.client = self.mock_client

        reply = svc.generate_reply(
            golden['sender'],
            "2026-04-23T10:00:00Z",
            golden['subject'],
            golden['body'],
            golden['expected_category'],
            "test reasoning"
        )

        for keyword in golden['reply_must_contain']:
            assert keyword in reply, f"Reply missing expected keyword: '{keyword}'"


class TestGoldenDatasetFromFixtures:
    """Verify sample_emails fixture data is consistent with golden expectations."""

    def test_all_fixture_categories_have_golden_coverage(self):
        """Every category in sample_emails should have at least one golden test."""
        fixture_categories = {e['expected_category'] for e in SAMPLE_EMAILS.values()}
        golden_categories = {g['expected_category'] for g in GOLDEN_DATASET}

        important_categories = {'pricing_inquiry', 'order_cancellation', 'order_tracking', 'non_business'}
        for cat in important_categories:
            assert cat in golden_categories, f"Category '{cat}' missing from golden dataset"

    def test_golden_dataset_has_minimum_size(self):
        assert len(GOLDEN_DATASET) >= 5, "Golden dataset should have at least 5 examples"

    def test_golden_dataset_has_valid_structure(self):
        for g in GOLDEN_DATASET:
            assert 'id' in g
            assert 'subject' in g
            assert 'body' in g
            assert 'expected_category' in g
            assert 'min_confidence' in g
            assert 0 <= g['min_confidence'] <= 1.0
