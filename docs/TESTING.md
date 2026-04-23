# Testing Infrastructure Setup Guide

## Installation

### 1. Install Testing Dependencies

Make sure you're in the MIS conda environment, then install the required packages:

```bash
# Activate MIS environment
conda activate MIS

# Install testing dependencies
pip install pytest pytest-cov pytest-mock Faker
```

### 2. Verify Installation

```bash
pytest --version
```

## Running Tests

### Run All Tests

```bash
cd backend
pytest tests/ -v
```

### Run with Coverage Report

```bash
cd backend
pytest tests/ -v --cov=services --cov=models --cov=routes --cov-report=term-missing --cov-report=html
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Edge case tests only
pytest tests/edge_cases/ -v
```

### Run Specific Test File

```bash
pytest tests/unit/test_classification_service.py -v
```

### Run Specific Test Function

```bash
pytest tests/unit/test_classification_service.py::TestClassificationService::test_classify_email_pricing_inquiry -v
```

## Test Structure

```
backend/tests/
├── __init__.py
├── conftest.py                          # Shared fixtures
├── fixtures/
│   ├── __init__.py
│   └── sample_emails.py                 # Sample email data
├── unit/
│   ├── __init__.py
│   ├── test_classification_service.py   # 30+ tests
│   ├── test_reply_service.py            # 40+ tests
│   └── test_company_info_service.py     # 30+ tests
├── integration/
│   ├── __init__.py
│   └── test_email_pipeline.py           # 10+ tests
└── edge_cases/
    ├── __init__.py
    ├── test_malformed_emails.py         # 20+ tests
    └── test_unicode_handling.py         # 15+ tests
```

## Coverage Goals

- **Target**: 70%+ coverage on critical paths
- **Critical Services**:
  - `services/classification_service.py`
  - `services/reply_service.py`
  - `services/company_info_service.py`

## Test Markers

Tests are organized with pytest markers:

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only edge case tests
pytest -m edge_case
```

## Troubleshooting

### Import Errors

If you get import errors, make sure you're running pytest from the `backend/` directory:

```bash
cd backend
pytest tests/
```

### Database Errors

Tests use temporary in-memory databases. If you see database errors, check that the `temp_db` fixture is being used correctly.

### Mock Errors

If OpenAI API mocks aren't working, verify that:
1. The `mock_config` fixture is applied
2. The service is using the mocked client

## Next Steps

After testing infrastructure is set up:

1. **Phase 1.2**: Configuration Externalization
2. **Phase 2.1**: Rubric-Guided Scoring
3. **Phase 2.2**: Category-Specific Thresholds

## CI/CD Integration

To integrate with GitHub Actions, create `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd backend
          pytest tests/ -v --cov=services --cov=models --cov=routes --cov-fail-under=70
```
