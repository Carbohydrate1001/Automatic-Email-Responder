# Configuration Guide

## Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Flask
FLASK_SECRET_KEY=your-secret-key
FLASK_DEBUG=True
FLASK_PORT=5005

# Microsoft Azure AD
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_TENANT_ID=your-tenant-id
AZURE_REDIRECT_URI=http://localhost:5005/auth/callback

# OpenAI
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# Thresholds
CONFIDENCE_THRESHOLD=0.75
SEND_RETRY_MAX_ATTEMPTS=3
SEND_RETRY_DELAY_SECONDS=1.0
```

---

## YAML Configuration Files

### `config/categories.yaml`
Defines email categories, keywords, and labels.

- `categories`: List of category IDs
- `category_labels`: Display names per language (zh, en)
- `business_hints`: Keywords indicating business emails
- `non_business_hints`: Keywords indicating non-business emails

### `config/thresholds.yaml`
Controls auto-send confidence thresholds.

```yaml
global_defaults:
  confidence_threshold: 0.75
  auto_send_minimum_confidence: 0.80

category_thresholds:
  order_cancellation: 0.90    # Higher bar for cancellations
  pricing_inquiry: 0.85
  billing_invoice: 0.85
```

### `config/rubrics.yaml`
Scoring rubrics for classification and reply quality.

- `classification_rubric`: Dimensions for classification confidence
- `auto_send_rubric`: Dimensions for auto-send readiness
- `reply_quality_rubric`: Dimensions for reply validation

### `config/policies.yaml`
Forbidden patterns and policy rules for reply validation.

- `forbidden_patterns`: Regex patterns that block auto-send
- `approved_language_templates`: Pre-approved phrases
- `authority_limits`: What the system can/cannot commit to

---

## Tuning Guide

### Adjusting Auto-Send Rate
- Increase `auto_send_minimum_confidence` to reduce auto-sends
- Decrease category-specific thresholds to increase auto-sends for safe categories
- Run `scripts/threshold_optimization.py` with calibration data

### Adjusting Classification
- Update `categories.yaml` keywords for better business gate accuracy
- Modify classification prompts in `classification_service.py`
- Add new categories by extending `categories.yaml`

### Data Retention
- Edit `DEFAULT_RETENTION` in `scripts/data_retention.py`
- Run with `--dry-run` to preview before executing
