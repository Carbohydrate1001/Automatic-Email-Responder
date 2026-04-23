"""
Unit tests for ScoringService.
Tests rubric-based scoring for classification and auto-send decisions.
"""

import pytest
import json
from unittest.mock import MagicMock, patch
from services.scoring_service import ScoringService, get_scoring_service


@pytest.fixture
def scoring_service():
    """Create a ScoringService instance for testing."""
    return ScoringService()


@pytest.fixture
def mock_openai_response_classification():
    """Mock OpenAI response for classification scoring."""
    return {
        "scores": {
            "keyword_match": {"score": 3, "reasoning": "Strong keyword match"},
            "intent_clarity": {"score": 3, "reasoning": "Intent is crystal clear"},
            "context_completeness": {"score": 2, "reasoning": "Adequate context"},
            "exclusion_confidence": {"score": 3, "reasoning": "Clearly distinct category"}
        },
        "weighted_score": 2.8,
        "confidence": 0.93
    }


@pytest.fixture
def mock_openai_response_auto_send():
    """Mock OpenAI response for auto-send scoring."""
    return {
        "scores": {
            "information_completeness": {"score": 3, "reasoning": "All info available"},
            "risk_level": {"score": 3, "reasoning": "Minimal risk"},
            "template_applicability": {"score": 3, "reasoning": "Perfect template fit"},
            "policy_alignment": {"score": 3, "reasoning": "Clearly compliant"}
        },
        "weighted_score": 3.0,
        "confidence": 1.0,
        "auto_send_recommended": True
    }


class TestScoringServiceInit:
    """Test ScoringService initialization."""

    def test_init_default_rubrics_path(self, scoring_service):
        """Test initialization with default rubrics path."""
        assert scoring_service.rubrics_file.name == "rubrics.yaml"
        assert scoring_service.client is not None

    def test_init_custom_rubrics_path(self, tmp_path):
        """Test initialization with custom rubrics path."""
        rubrics_file = tmp_path / "custom_rubrics.yaml"
        rubrics_file.write_text("test: data")

        service = ScoringService(rubrics_file=str(rubrics_file))
        assert service.rubrics_file == rubrics_file


class TestLoadRubrics:
    """Test rubrics loading."""

    def test_load_rubrics_success(self, scoring_service):
        """Test successful rubrics loading."""
        rubrics = scoring_service._load_rubrics()

        assert "classification_rubric" in rubrics
        assert "auto_send_rubric" in rubrics
        assert "prompts" in rubrics

    def test_load_rubrics_caching(self, scoring_service):
        """Test rubrics are cached after first load."""
        rubrics1 = scoring_service._load_rubrics()
        rubrics2 = scoring_service._load_rubrics()

        assert rubrics1 is rubrics2  # Same object reference

    def test_load_rubrics_file_not_found(self, tmp_path):
        """Test error when rubrics file doesn't exist."""
        nonexistent = tmp_path / "nonexistent.yaml"
        service = ScoringService(rubrics_file=str(nonexistent))

        with pytest.raises(FileNotFoundError):
            service._load_rubrics()

    def test_reload_clears_cache(self, scoring_service):
        """Test reload clears cache."""
        rubrics1 = scoring_service._load_rubrics()
        scoring_service.reload()
        rubrics2 = scoring_service._load_rubrics()

        # After reload, should load fresh (different object)
        assert rubrics1 is not rubrics2


class TestWeightedScoreCalculation:
    """Test weighted score calculation."""

    def test_calculate_weighted_score_perfect(self, scoring_service):
        """Test weighted score with perfect scores."""
        dimensions = [
            {"name": "dim1", "weight": 0.5},
            {"name": "dim2", "weight": 0.5}
        ]
        scores = {"dim1": 3, "dim2": 3}

        weighted = scoring_service._calculate_weighted_score(scores, dimensions)
        assert weighted == 3.0

    def test_calculate_weighted_score_mixed(self, scoring_service):
        """Test weighted score with mixed scores."""
        dimensions = [
            {"name": "dim1", "weight": 0.25},
            {"name": "dim2", "weight": 0.75}
        ]
        scores = {"dim1": 2, "dim2": 3}

        weighted = scoring_service._calculate_weighted_score(scores, dimensions)
        assert weighted == pytest.approx(2.75)

    def test_calculate_weighted_score_zero(self, scoring_service):
        """Test weighted score with all zeros."""
        dimensions = [
            {"name": "dim1", "weight": 0.5},
            {"name": "dim2", "weight": 0.5}
        ]
        scores = {"dim1": 0, "dim2": 0}

        weighted = scoring_service._calculate_weighted_score(scores, dimensions)
        assert weighted == 0.0

    def test_calculate_weighted_score_missing_dimension(self, scoring_service):
        """Test weighted score with missing dimension (defaults to 0)."""
        dimensions = [
            {"name": "dim1", "weight": 0.5},
            {"name": "dim2", "weight": 0.5}
        ]
        scores = {"dim1": 3}  # dim2 missing

        weighted = scoring_service._calculate_weighted_score(scores, dimensions)
        assert weighted == 1.5


class TestConfidenceMapping:
    """Test confidence score mapping."""

    def test_score_to_confidence_perfect(self, scoring_service):
        """Test mapping perfect score to confidence."""
        confidence = scoring_service._score_to_confidence(3.0)
        assert confidence == 1.0

    def test_score_to_confidence_zero(self, scoring_service):
        """Test mapping zero score to confidence."""
        confidence = scoring_service._score_to_confidence(0.0)
        assert confidence == 0.0

    def test_score_to_confidence_mid(self, scoring_service):
        """Test mapping mid-range score to confidence."""
        confidence = scoring_service._score_to_confidence(1.5)
        assert confidence == 0.5

    def test_score_to_confidence_clamping_high(self, scoring_service):
        """Test confidence clamping at upper bound."""
        confidence = scoring_service._score_to_confidence(5.0)
        assert confidence == 1.0

    def test_score_to_confidence_clamping_low(self, scoring_service):
        """Test confidence clamping at lower bound."""
        confidence = scoring_service._score_to_confidence(-1.0)
        assert confidence == 0.0


class TestClassificationScoring:
    """Test classification scoring."""

    def test_score_classification_llm_success(self, scoring_service, mock_openai_response_classification):
        """Test LLM-based classification scoring."""
        with patch.object(scoring_service.client.chat.completions, 'create') as mock_create:
            mock_response = MagicMock()
            mock_response.choices[0].message.content = json.dumps(mock_openai_response_classification)
            mock_create.return_value = mock_response

            result = scoring_service.score_classification(
                subject="Price inquiry",
                body="What is the price for Product A?",
                category="pricing_inquiry",
                use_llm=True
            )

            assert "scores" in result
            assert "weighted_score" in result
            assert "confidence" in result
            assert result["confidence"] >= 0.0
            assert result["confidence"] <= 1.0

    def test_score_classification_rule_based(self, scoring_service):
        """Test rule-based classification scoring."""
        result = scoring_service.score_classification(
            subject="Price inquiry",
            body="What is the price for Product A? I need a quote urgently.",
            category="pricing_inquiry",
            use_llm=False
        )

        assert "scores" in result
        assert "weighted_score" in result
        assert "confidence" in result
        assert result["method"] == "rule_based"

    def test_score_classification_short_email(self, scoring_service):
        """Test classification scoring with short email."""
        result = scoring_service.score_classification(
            subject="Price",
            body="Price?",
            category="pricing_inquiry",
            use_llm=False
        )

        # Short emails should have lower scores
        assert result["confidence"] < 0.5

    def test_score_classification_long_detailed_email(self, scoring_service):
        """Test classification scoring with long detailed email."""
        result = scoring_service.score_classification(
            subject="Detailed price inquiry for bulk order",
            body="Hello, I am interested in purchasing 1000 units of Product A. " * 10,
            category="pricing_inquiry",
            use_llm=False
        )

        # Long detailed emails should have higher scores
        assert result["confidence"] > 0.5


class TestAutoSendScoring:
    """Test auto-send readiness scoring."""

    def test_score_auto_send_llm_success(self, scoring_service, mock_openai_response_auto_send):
        """Test LLM-based auto-send scoring."""
        with patch.object(scoring_service.client.chat.completions, 'create') as mock_create:
            mock_response = MagicMock()
            mock_response.choices[0].message.content = json.dumps(mock_openai_response_auto_send)
            mock_create.return_value = mock_response

            result = scoring_service.score_auto_send_readiness(
                subject="Price inquiry",
                body="What is the price for Product A?",
                reply_text="Thank you for your inquiry. The price for Product A is $100.",
                category="pricing_inquiry",
                use_llm=True
            )

            assert "scores" in result
            assert "weighted_score" in result
            assert "confidence" in result
            assert "auto_send_recommended" in result

    def test_score_auto_send_rule_based(self, scoring_service):
        """Test rule-based auto-send scoring."""
        result = scoring_service.score_auto_send_readiness(
            subject="Price inquiry",
            body="What is the price?",
            reply_text="Thank you for your inquiry. The price for Product A is $100. Please let us know if you have any questions.",
            category="pricing_inquiry",
            use_llm=False
        )

        assert "scores" in result
        assert "weighted_score" in result
        assert result["method"] == "rule_based"

    def test_score_auto_send_high_confidence(self, scoring_service, mock_openai_response_auto_send):
        """Test auto-send with high confidence scores."""
        with patch.object(scoring_service.client.chat.completions, 'create') as mock_create:
            mock_response = MagicMock()
            mock_response.choices[0].message.content = json.dumps(mock_openai_response_auto_send)
            mock_create.return_value = mock_response

            result = scoring_service.score_auto_send_readiness(
                subject="Price inquiry",
                body="What is the price?",
                reply_text="The price is $100.",
                category="pricing_inquiry",
                use_llm=True
            )

            assert result["auto_send_recommended"] is True

    def test_score_auto_send_low_confidence(self, scoring_service):
        """Test auto-send with low confidence scores."""
        with patch.object(scoring_service.client.chat.completions, 'create') as mock_create:
            low_confidence_response = {
                "scores": {
                    "information_completeness": {"score": 0, "reasoning": "Missing info"},
                    "risk_level": {"score": 0, "reasoning": "High risk"},
                    "template_applicability": {"score": 1, "reasoning": "Poor fit"},
                    "policy_alignment": {"score": 2, "reasoning": "Uncertain"}
                },
                "weighted_score": 0.8,
                "confidence": 0.27,
                "auto_send_recommended": False
            }
            mock_response = MagicMock()
            mock_response.choices[0].message.content = json.dumps(low_confidence_response)
            mock_create.return_value = mock_response

            result = scoring_service.score_auto_send_readiness(
                subject="Complex issue",
                body="I have a complex problem...",
                reply_text="We need more information.",
                category="other",
                use_llm=True
            )

            assert result["auto_send_recommended"] is False

    def test_score_auto_send_threshold_enforcement(self, scoring_service):
        """Test auto-send threshold enforcement."""
        with patch.object(scoring_service.client.chat.completions, 'create') as mock_create:
            # Weighted score 2.4 < 2.5 threshold
            below_threshold_response = {
                "scores": {
                    "information_completeness": {"score": 2, "reasoning": "Some info"},
                    "risk_level": {"score": 2, "reasoning": "Low risk"},
                    "template_applicability": {"score": 3, "reasoning": "Good fit"},
                    "policy_alignment": {"score": 3, "reasoning": "Compliant"}
                },
                "weighted_score": 2.4,
                "confidence": 0.8,
                "auto_send_recommended": True
            }
            mock_response = MagicMock()
            mock_response.choices[0].message.content = json.dumps(below_threshold_response)
            mock_create.return_value = mock_response

            result = scoring_service.score_auto_send_readiness(
                subject="Inquiry",
                body="Question",
                reply_text="Answer",
                category="pricing_inquiry",
                use_llm=True
            )

            # Should be False because weighted_score < 2.5
            assert result["auto_send_recommended"] is False

    def test_score_auto_send_blocking_dimension(self, scoring_service):
        """Test auto-send blocked by single low dimension."""
        with patch.object(scoring_service.client.chat.completions, 'create') as mock_create:
            # One dimension score 0 should block auto-send
            blocking_response = {
                "scores": {
                    "information_completeness": {"score": 3, "reasoning": "Complete"},
                    "risk_level": {"score": 0, "reasoning": "High risk - legal issue"},
                    "template_applicability": {"score": 3, "reasoning": "Good fit"},
                    "policy_alignment": {"score": 3, "reasoning": "Compliant"}
                },
                "weighted_score": 2.65,
                "confidence": 0.88,
                "auto_send_recommended": True
            }
            mock_response = MagicMock()
            mock_response.choices[0].message.content = json.dumps(blocking_response)
            mock_create.return_value = mock_response

            result = scoring_service.score_auto_send_readiness(
                subject="Legal issue",
                body="I want to sue you",
                reply_text="We will review your case",
                category="other",
                use_llm=True
            )

            # Should be False because risk_level = 0
            assert result["auto_send_recommended"] is False


class TestSingletonPattern:
    """Test singleton pattern for get_scoring_service."""

    def test_get_scoring_service_singleton(self):
        """Test get_scoring_service returns same instance."""
        service1 = get_scoring_service()
        service2 = get_scoring_service()

        assert service1 is service2

    def test_get_scoring_service_returns_scoring_service(self):
        """Test get_scoring_service returns ScoringService instance."""
        service = get_scoring_service()
        assert isinstance(service, ScoringService)


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_score_classification_empty_body(self, scoring_service):
        """Test classification scoring with empty body."""
        result = scoring_service.score_classification(
            subject="",
            body="",
            category="pricing_inquiry",
            use_llm=False
        )

        assert result["confidence"] == 0.0

    def test_score_auto_send_empty_reply(self, scoring_service):
        """Test auto-send scoring with empty reply."""
        result = scoring_service.score_auto_send_readiness(
            subject="Question",
            body="What is the price?",
            reply_text="",
            category="pricing_inquiry",
            use_llm=False
        )

        assert result["confidence"] < 0.5

    def test_score_classification_invalid_category(self, scoring_service):
        """Test classification scoring with invalid category."""
        # Should not raise error, just use fallback scoring
        result = scoring_service.score_classification(
            subject="Test",
            body="Test body",
            category="invalid_category_xyz",
            use_llm=False
        )

        assert "confidence" in result
