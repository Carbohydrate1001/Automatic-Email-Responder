# Developer Guide

## Project Structure

```
backend/
├── app.py                    # Flask application entry point
├── config.py                 # Environment configuration
├── config/                   # YAML configuration files
│   ├── categories.yaml       # Email categories and keywords
│   ├── rubrics.yaml          # Scoring rubrics
│   ├── thresholds.yaml       # Confidence thresholds
│   └── policies.yaml         # Policy rules
├── models/
│   ├── database.py           # SQLite schema and connection
│   └── audit_log.py          # Compliance audit logging
├── services/
│   ├── classification_service.py  # Email classification
│   ├── reply_service.py           # Reply generation + pipeline
│   ├── scoring_service.py         # Rubric-based scoring
│   ├── validation_service.py      # Reply quality validation
│   ├── pii_service.py             # PII detection/redaction
│   ├── language_service.py        # Language detection
│   ├── config_loader.py           # YAML config management
│   ├── company_info_service.py    # Product catalog
│   └── graph_service.py           # Microsoft Graph API
├── utils/
│   ├── retry_handler.py      # Retry + circuit breaker
│   ├── logger.py             # Structured logging
│   └── ab_testing.py         # A/B testing framework
├── api/
│   ├── health.py             # Health check endpoints
│   └── metrics.py            # Metrics endpoints
├── routes/                   # Flask route blueprints
├── scripts/                  # CLI tools and analysis scripts
├── tests/                    # Test suites
│   ├── unit/                 # Unit tests
│   ├── e2e/                  # End-to-end tests
│   ├── regression/           # Golden dataset regression
│   ├── integration/          # Integration tests
│   ├── edge_cases/           # Edge case tests
│   └── fixtures/             # Test data
└── docs/                     # Documentation
```

## Adding a New Email Category

1. Add the category ID to `config/categories.yaml` under `categories`
2. Add labels in `category_labels.zh` and `category_labels.en`
3. Add keywords to `business_hints` if applicable
4. Add a category-specific threshold in `config/thresholds.yaml`
5. Add a template reply method in `reply_service.py`
6. Add test cases in `tests/fixtures/sample_emails.py`
7. Add a golden dataset entry in `tests/regression/test_regression.py`

## Adding a New Service

1. Create `services/your_service.py` with a singleton pattern:
```python
_instance = None
def get_your_service():
    global _instance
    if _instance is None:
        _instance = YourService()
    return _instance
```
2. Add unit tests in `tests/unit/test_your_service.py`
3. Use `get_logger('your_service')` for structured logging

## Testing Guidelines

- All services use singleton pattern — mock at the module level
- Use `mock_config` fixture for environment variables
- Patch `CompanyInfoService` at `services.company_info_service.CompanyInfoService`
- Patch `OpenAI` at the importing module (e.g., `services.reply_service.OpenAI`)
- Target 80%+ coverage for new code
- Add regression tests for any new category or template
