# Configuration System Documentation

## Overview

The Automatic Email Responder now uses external YAML configuration files for categories, thresholds, and routing rules. This makes it easy to modify system behavior without changing code.

## Configuration Files

All configuration files are located in `backend/config/`:

```
backend/config/
├── categories.yaml      # Email categories and keywords
├── thresholds.yaml      # Routing thresholds and rules
└── schema.json          # JSON schema for validation
```

## Categories Configuration

**File:** `backend/config/categories.yaml`

Defines email categories, their labels, descriptions, and keywords for classification.

### Structure

```yaml
categories:
  - id: pricing_inquiry              # Unique category ID
    label_en: "Pricing Inquiry"      # English label
    label_zh: "询价/报价"             # Chinese label
    description: "Customer requests for product pricing or quotations"
    keywords:                         # Keywords for matching
      - "price"
      - "quote"
      - "询价"

business_hints:                       # Keywords indicating business emails
  - "order"
  - "shipment"
  - "订单"

non_business_hints:                   # Keywords indicating non-business emails
  - "newsletter"
  - "promotion"
  - "营销"
```

### Adding a New Category

1. Add a new entry to the `categories` list:

```yaml
  - id: custom_inquiry
    label_en: "Custom Inquiry"
    label_zh: "自定义询问"
    description: "Custom customer inquiries"
    keywords:
      - "custom"
      - "special"
      - "自定义"
```

2. Add corresponding routing rule in `thresholds.yaml` (see below)

3. Restart the application to load new configuration

### Modifying Keywords

Simply edit the `keywords` list for any category. Keywords are case-insensitive and support both English and Chinese.

## Thresholds Configuration

**File:** `backend/config/thresholds.yaml`

Defines confidence thresholds and routing rules for auto-send decisions.

### Structure

```yaml
# Global thresholds (apply to all categories unless overridden)
global:
  confidence_threshold: 0.75              # Minimum confidence for classification
  auto_send_minimum_confidence: 0.80     # Minimum confidence for auto-send
  business_gate_threshold: 0.60          # Threshold for business relevance

# Category-specific routing rules
routing_rules:
  pricing_inquiry:
    auto_send_threshold: 0.85            # Category-specific threshold
    description: "Standard pricing inquiries"
    require_product_match: true          # Additional requirements
    max_auto_send_per_day: 50           # Rate limiting

  order_cancellation:
    auto_send_threshold: 0.90            # Higher threshold for financial impact
    description: "Cancellation requests"
    escalate_if_amount_exceeds: 10000   # Escalate high-value orders

# Default rule for categories without specific rules
default:
  auto_send_threshold: 0.80
  description: "Default routing rule"
  always_notify_human: false

# Retry configuration for failed sends
retry:
  max_attempts: 3
  delay_seconds: 1.0
  exponential_backoff: false

# Rate limiting configuration
rate_limiting:
  enabled: false
  max_auto_send_per_hour: 100
  max_auto_send_per_day: 500
```

### Adjusting Thresholds

**To make auto-send more conservative (fewer auto-sends):**
- Increase `auto_send_threshold` values (e.g., 0.85 → 0.90)

**To make auto-send more aggressive (more auto-sends):**
- Decrease `auto_send_threshold` values (e.g., 0.85 → 0.80)

**Category-specific adjustments:**
```yaml
routing_rules:
  high_risk_category:
    auto_send_threshold: 0.95    # Very conservative
    always_notify_human: true    # Always flag for review

  low_risk_category:
    auto_send_threshold: 0.75    # More aggressive
```

### Routing Rule Options

| Option | Type | Description |
|--------|------|-------------|
| `auto_send_threshold` | float (0.0-1.0) | Minimum confidence for auto-send |
| `description` | string | Human-readable description |
| `require_product_match` | boolean | Require product match in email |
| `require_order_number` | boolean | Require order number in email |
| `max_auto_send_per_day` | integer | Daily auto-send limit |
| `escalate_if_amount_exceeds` | number | Escalate if amount > value |
| `always_notify_human` | boolean | Always flag for human review |
| `escalate_if_urgent` | boolean | Escalate urgent emails |

## Using Configuration in Code

### Loading Configuration

```python
from services.config_loader import get_config_loader

# Get singleton instance
config_loader = get_config_loader()

# Load categories
categories = config_loader.get_category_list()
# Returns: ['pricing_inquiry', 'order_cancellation', ...]

# Get category labels
labels_zh = config_loader.get_category_labels('zh')
# Returns: {'pricing_inquiry': '询价/报价', ...}

# Get keywords for a category
keywords = config_loader.get_category_keywords('pricing_inquiry')
# Returns: ['price', 'quote', 'quotation', ...]

# Get business/non-business hints
business_hints = config_loader.get_business_hints()
non_business_hints = config_loader.get_non_business_hints()

# Get thresholds
confidence_threshold = config_loader.get_global_threshold('confidence_threshold')
# Returns: 0.75

# Get routing rule
rule = config_loader.get_routing_rule('pricing_inquiry')
# Returns: {'auto_send_threshold': 0.85, 'description': '...', ...}

# Get retry configuration
retry_config = config_loader.get_retry_config()
# Returns: {'max_attempts': 3, 'delay_seconds': 1.0, ...}
```

### Reloading Configuration

Configuration is cached for performance. To reload after changes:

```python
config_loader = get_config_loader()
config_loader.reload()
```

### Validation

Validate configuration files:

```python
config_loader = get_config_loader()
try:
    config_loader.validate_config()
    print("Configuration is valid")
except ValueError as e:
    print(f"Configuration error: {e}")
```

## Configuration Validation

The system validates configuration on startup:

1. **Required fields**: All required fields must be present
2. **Threshold ranges**: All thresholds must be between 0.0 and 1.0
3. **Category references**: Routing rules must reference valid categories
4. **Data types**: Fields must have correct types (string, number, boolean)

### Common Validation Errors

**Missing required field:**
```
ValueError: Category missing required field 'keywords': {...}
```
**Solution:** Add the missing field to the category definition

**Invalid threshold value:**
```
ValueError: Invalid threshold value for 'confidence_threshold': 1.5
```
**Solution:** Ensure threshold is between 0.0 and 1.0

**Unknown category reference:**
```
ValueError: Routing rule 'unknown_category' references unknown category
```
**Solution:** Add the category to `categories.yaml` or remove the routing rule

## Best Practices

### 1. Version Control

Always commit configuration changes to version control:

```bash
git add backend/config/
git commit -m "Update confidence thresholds for pricing_inquiry"
```

### 2. Testing Configuration Changes

After modifying configuration:

1. Validate configuration:
   ```python
   from services.config_loader import get_config_loader
   get_config_loader().validate_config()
   ```

2. Run tests:
   ```bash
   pytest tests/unit/test_config_loader.py -v
   ```

3. Test with sample emails before deploying

### 3. Environment-Specific Configuration

For different environments (dev/staging/prod), use environment variables to override:

```python
# In config.py
CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', '0.75'))
```

Or maintain separate config files:
```
backend/config/
├── categories.yaml
├── thresholds.dev.yaml
├── thresholds.staging.yaml
└── thresholds.prod.yaml
```

### 4. Monitoring Threshold Changes

After adjusting thresholds, monitor:
- Auto-send rate (should it increase/decrease as expected?)
- Manual review queue size
- Classification accuracy
- Customer satisfaction

### 5. Gradual Threshold Adjustments

When changing thresholds:
- Make small incremental changes (±0.05)
- Monitor for 1-2 days before further adjustments
- Document the reason for each change

## Migration from Hardcoded Values

The system has been migrated from hardcoded values to external configuration:

**Before (hardcoded):**
```python
CATEGORIES = ["pricing_inquiry", "order_cancellation", ...]
CONFIDENCE_THRESHOLD = 0.75
```

**After (external config):**
```python
from services.config_loader import get_config_loader
config_loader = get_config_loader()
CATEGORIES = config_loader.get_category_list()
threshold = config_loader.get_global_threshold('confidence_threshold')
```

All services (`classification_service.py`, `reply_service.py`) now use the config loader.

## Troubleshooting

### Configuration not loading

**Error:** `FileNotFoundError: Categories config not found`

**Solution:** Ensure `backend/config/categories.yaml` exists

### Changes not taking effect

**Solution:** Restart the application or call `config_loader.reload()`

### YAML syntax errors

**Error:** `yaml.scanner.ScannerError: mapping values are not allowed here`

**Solution:** Check YAML syntax, ensure proper indentation (2 spaces)

### Invalid UTF-8 characters

**Solution:** Ensure files are saved with UTF-8 encoding

## Future Enhancements

Planned improvements to the configuration system:

1. **Hot reload**: Automatically reload configuration without restart
2. **Web UI**: Edit configuration through admin interface
3. **A/B testing**: Test different threshold configurations
4. **Configuration history**: Track changes over time
5. **Validation API**: Endpoint to validate configuration before applying
