"""
Unit tests for config_loader.py
"""

import pytest
import tempfile
import os
from pathlib import Path
from services.config_loader import ConfigLoader


class TestConfigLoader:
    """Test suite for ConfigLoader."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory with test files."""
        temp_dir = tempfile.mkdtemp()

        # Create categories.yaml
        categories_content = """
categories:
  - id: test_category
    label_en: "Test Category"
    label_zh: "测试类别"
    description: "Test description"
    keywords:
      - "test"
      - "测试"

business_hints:
  - "business"
  - "order"

non_business_hints:
  - "newsletter"
  - "spam"
"""
        with open(os.path.join(temp_dir, 'categories.yaml'), 'w', encoding='utf-8') as f:
            f.write(categories_content)

        # Create thresholds.yaml
        thresholds_content = """
global:
  confidence_threshold: 0.75
  auto_send_minimum_confidence: 0.80
  business_gate_threshold: 0.60

routing_rules:
  test_category:
    auto_send_threshold: 0.85
    description: "Test routing rule"
    always_notify_human: false

default:
  auto_send_threshold: 0.80
  description: "Default rule"
  always_notify_human: false

retry:
  max_attempts: 3
  delay_seconds: 1.0
  exponential_backoff: false

rate_limiting:
  enabled: false
  max_auto_send_per_hour: 100
  max_auto_send_per_day: 500
"""
        with open(os.path.join(temp_dir, 'thresholds.yaml'), 'w', encoding='utf-8') as f:
            f.write(thresholds_content)

        yield temp_dir

        # Cleanup
        for file in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, file))
        os.rmdir(temp_dir)

    def test_load_categories_success(self, temp_config_dir):
        """Test loading categories configuration."""
        loader = ConfigLoader(temp_config_dir)
        config = loader.load_categories()

        assert 'categories' in config
        assert 'business_hints' in config
        assert 'non_business_hints' in config
        assert len(config['categories']) == 1
        assert config['categories'][0]['id'] == 'test_category'

    def test_load_categories_missing_file(self):
        """Test loading categories with missing file."""
        temp_dir = tempfile.mkdtemp()
        loader = ConfigLoader(temp_dir)

        with pytest.raises(FileNotFoundError):
            loader.load_categories()

        os.rmdir(temp_dir)

    def test_load_thresholds_success(self, temp_config_dir):
        """Test loading thresholds configuration."""
        loader = ConfigLoader(temp_config_dir)
        config = loader.load_thresholds()

        assert 'global' in config
        assert 'routing_rules' in config
        assert 'default' in config
        assert config['global']['confidence_threshold'] == 0.75

    def test_get_category_list(self, temp_config_dir):
        """Test getting category list."""
        loader = ConfigLoader(temp_config_dir)
        categories = loader.get_category_list()

        assert isinstance(categories, list)
        assert 'test_category' in categories

    def test_get_category_labels_chinese(self, temp_config_dir):
        """Test getting Chinese category labels."""
        loader = ConfigLoader(temp_config_dir)
        labels = loader.get_category_labels('zh')

        assert isinstance(labels, dict)
        assert labels['test_category'] == '测试类别'

    def test_get_category_labels_english(self, temp_config_dir):
        """Test getting English category labels."""
        loader = ConfigLoader(temp_config_dir)
        labels = loader.get_category_labels('en')

        assert isinstance(labels, dict)
        assert labels['test_category'] == 'Test Category'

    def test_get_category_keywords(self, temp_config_dir):
        """Test getting category keywords."""
        loader = ConfigLoader(temp_config_dir)
        keywords = loader.get_category_keywords('test_category')

        assert isinstance(keywords, list)
        assert 'test' in keywords
        assert '测试' in keywords

    def test_get_category_keywords_not_found(self, temp_config_dir):
        """Test getting keywords for non-existent category."""
        loader = ConfigLoader(temp_config_dir)
        keywords = loader.get_category_keywords('non_existent')

        assert keywords == []

    def test_get_business_hints(self, temp_config_dir):
        """Test getting business hints."""
        loader = ConfigLoader(temp_config_dir)
        hints = loader.get_business_hints()

        assert isinstance(hints, list)
        assert 'business' in hints
        assert 'order' in hints

    def test_get_non_business_hints(self, temp_config_dir):
        """Test getting non-business hints."""
        loader = ConfigLoader(temp_config_dir)
        hints = loader.get_non_business_hints()

        assert isinstance(hints, list)
        assert 'newsletter' in hints
        assert 'spam' in hints

    def test_get_global_threshold(self, temp_config_dir):
        """Test getting global threshold."""
        loader = ConfigLoader(temp_config_dir)
        threshold = loader.get_global_threshold('confidence_threshold')

        assert threshold == 0.75

    def test_get_global_threshold_default(self, temp_config_dir):
        """Test getting non-existent threshold returns default."""
        loader = ConfigLoader(temp_config_dir)
        threshold = loader.get_global_threshold('non_existent')

        assert threshold == 0.75

    def test_get_routing_rule_specific(self, temp_config_dir):
        """Test getting category-specific routing rule."""
        loader = ConfigLoader(temp_config_dir)
        rule = loader.get_routing_rule('test_category')

        assert rule['auto_send_threshold'] == 0.85
        assert rule['description'] == 'Test routing rule'

    def test_get_routing_rule_default(self, temp_config_dir):
        """Test getting default routing rule for unknown category."""
        loader = ConfigLoader(temp_config_dir)
        rule = loader.get_routing_rule('unknown_category')

        assert rule['auto_send_threshold'] == 0.80
        assert rule['description'] == 'Default rule'

    def test_get_retry_config(self, temp_config_dir):
        """Test getting retry configuration."""
        loader = ConfigLoader(temp_config_dir)
        config = loader.get_retry_config()

        assert config['max_attempts'] == 3
        assert config['delay_seconds'] == 1.0
        assert config['exponential_backoff'] is False

    def test_get_rate_limiting_config(self, temp_config_dir):
        """Test getting rate limiting configuration."""
        loader = ConfigLoader(temp_config_dir)
        config = loader.get_rate_limiting_config()

        assert config['enabled'] is False
        assert config['max_auto_send_per_hour'] == 100
        assert config['max_auto_send_per_day'] == 500

    def test_config_caching(self, temp_config_dir):
        """Test configuration caching."""
        loader = ConfigLoader(temp_config_dir)

        # Load twice
        config1 = loader.load_categories()
        config2 = loader.load_categories()

        # Should return same cached object
        assert config1 is config2

    def test_reload_clears_cache(self, temp_config_dir):
        """Test reload clears cache."""
        loader = ConfigLoader(temp_config_dir)

        # Load and cache
        config1 = loader.load_categories()

        # Reload
        loader.reload()

        # Load again
        config2 = loader.load_categories()

        # Should be different objects
        assert config1 is not config2

    def test_validate_config_success(self, temp_config_dir):
        """Test configuration validation succeeds."""
        loader = ConfigLoader(temp_config_dir)
        assert loader.validate_config() is True

    def test_validate_config_invalid_routing_rule(self, temp_config_dir):
        """Test validation fails for invalid routing rule."""
        # Add invalid routing rule
        thresholds_file = os.path.join(temp_config_dir, 'thresholds.yaml')
        with open(thresholds_file, 'a', encoding='utf-8') as f:
            f.write("""
  invalid_category:
    auto_send_threshold: 0.90
    description: "Invalid category"
""")

        loader = ConfigLoader(temp_config_dir)
        loader.reload()

        with pytest.raises(ValueError, match="unknown category"):
            loader.validate_config()

    def test_missing_required_category_field(self, temp_config_dir):
        """Test validation fails for missing required field."""
        categories_file = os.path.join(temp_config_dir, 'categories.yaml')
        with open(categories_file, 'w', encoding='utf-8') as f:
            f.write("""
categories:
  - id: incomplete_category
    label_en: "Incomplete"
    # Missing label_zh, description, keywords

business_hints:
  - "test"

non_business_hints:
  - "test"
""")

        loader = ConfigLoader(temp_config_dir)
        loader.reload()

        with pytest.raises(ValueError, match="missing required field"):
            loader.load_categories()

    def test_invalid_threshold_value(self, temp_config_dir):
        """Test validation fails for invalid threshold value."""
        thresholds_file = os.path.join(temp_config_dir, 'thresholds.yaml')
        with open(thresholds_file, 'w', encoding='utf-8') as f:
            f.write("""
global:
  confidence_threshold: 1.5  # Invalid: > 1.0
  auto_send_minimum_confidence: 0.80
  business_gate_threshold: 0.60

routing_rules: {}
default:
  auto_send_threshold: 0.80
  description: "Default"
""")

        loader = ConfigLoader(temp_config_dir)
        loader.reload()

        with pytest.raises(ValueError, match="Invalid threshold value"):
            loader.load_thresholds()
