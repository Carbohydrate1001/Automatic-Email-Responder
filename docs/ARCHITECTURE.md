# System Architecture

## Overview

The Automatic Email Responder is a Flask-based system that automatically classifies incoming customer emails and generates appropriate replies for a logistics/trade company. It integrates with Microsoft Graph API for email access and OpenAI GPT-4o-mini for classification and reply generation.

## Architecture Diagram

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Microsoft   │────>│  Flask API   │────>│  Classification  │
│  Graph API   │     │  (app.py)    │     │  Service         │
│  (Outlook)   │<────│              │     │  (GPT-4o-mini)   │
└─────────────┘     └──────┬───────┘     └────────┬────────┘
                           │                       │
                    ┌──────┴───────┐        ┌──────┴────────┐
                    │   SQLite DB  │        │ Reply Service  │
                    │  (email_     │        │ (Templates +   │
                    │   system.db) │        │  GPT fallback) │
                    └──────────────┘        └───────────────┘
```

## Component Overview

### Core Services

| Component | File | Purpose |
|-----------|------|---------|
| Classification | `services/classification_service.py` | Two-stage email classification (business gate + category) |
| Reply Generation | `services/reply_service.py` | Template-based and GPT-powered reply generation |
| Scoring | `services/scoring_service.py` | Rubric-based confidence scoring and auto-send decisions |
| Validation | `services/validation_service.py` | Multi-stage reply quality validation |
| PII Detection | `services/pii_service.py` | PII detection and redaction |
| Language Detection | `services/language_service.py` | Chinese/English language detection |
| Config Loader | `services/config_loader.py` | YAML configuration management |
| Company Info | `services/company_info_service.py` | Product catalog access |
| Graph Service | `services/graph_service.py` | Microsoft Graph API integration |

### Infrastructure

| Component | File | Purpose |
|-----------|------|---------|
| Retry Handler | `utils/retry_handler.py` | Exponential backoff + circuit breaker |
| Logger | `utils/logger.py` | Structured JSON logging |
| A/B Testing | `utils/ab_testing.py` | Experiment framework |
| Health Checks | `api/health.py` | System health monitoring |
| Metrics API | `api/metrics.py` | Performance metrics endpoints |
| Audit Log | `models/audit_log.py` | Compliance audit trail |

### Data Flow

1. **Email Ingestion**: Graph API fetches unread emails from Outlook
2. **Business Gate**: GPT determines if email is business-related
3. **Classification**: GPT classifies into category (pricing, tracking, etc.)
4. **Scoring**: Rubric-based confidence assessment
5. **Reply Generation**: Template or GPT-based reply
6. **Validation**: Policy, hallucination, and quality checks
7. **Routing**: Auto-send (high confidence) or manual review
8. **Audit**: All actions logged to compliance audit trail

### Database Schema

```
emails (id, message_id, subject, sender, body, category, confidence,
        status, consent_status, pii_detected, pii_types, ...)

replies (id, email_id, reply_text, sent_at, validation_passed,
         reply_validation_scores, validation_issues, ...)

audit_log (id, email_id, action, operator, created_at)

compliance_audit_log (id, email_id, action, operator, details, ...)

experiments / experiment_assignments / experiment_events (A/B testing)
```

### Configuration Files

| File | Purpose |
|------|---------|
| `config/categories.yaml` | Email categories, keywords, labels |
| `config/rubrics.yaml` | Scoring rubrics and quality dimensions |
| `config/thresholds.yaml` | Confidence thresholds per category |
| `config/policies.yaml` | Forbidden patterns and policy rules |
