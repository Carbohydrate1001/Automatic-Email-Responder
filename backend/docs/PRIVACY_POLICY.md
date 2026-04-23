# Privacy Policy - Automatic Email Responder

**Version**: 1.0  
**Effective Date**: 2026-04-23  
**Last Updated**: 2026-04-23

---

## 1. Overview

This document describes the privacy and data protection measures implemented in the Automatic Email Responder system. The system processes customer emails for classification and automated reply generation in a logistics/trade business context.

---

## 2. Data Collection

### 2.1 What We Collect
- Email metadata: sender address, subject line, received timestamp
- Email body content
- Classification results: category, confidence score, reasoning
- Generated reply text
- Processing audit trail

### 2.2 What We Do NOT Collect
- Attachments or binary content
- Browser cookies or tracking data
- Third-party analytics data

---

## 3. PII Detection & Protection

### 3.1 Detected PII Types
The system automatically scans all incoming emails for:

| PII Type | Examples | Risk Level |
|----------|----------|------------|
| Email addresses | user@example.com | Low |
| Phone numbers | +86 138xxxx, (555) 123-4567 | Medium |
| Credit card numbers | 4111-xxxx-xxxx-1111 | High |
| Social Security Numbers | xxx-xx-6789 | High |
| Passport numbers | E12345678 | Medium |
| National ID numbers | Chinese 18-digit ID | Medium |

### 3.2 Redaction Levels
- **NONE**: No redaction (internal use only)
- **PARTIAL**: Mask middle characters (e.g., `j***@example.com`, `138****5678`)
- **FULL**: Replace with `[TYPE_REDACTED]` placeholder

### 3.3 PII Handling Rules
- PII is detected and flagged on all incoming emails
- Emails containing high-risk PII (credit cards, SSNs) are flagged for manual review
- PII is redacted before logging to prevent accidental exposure
- Auto-generated replies never include customer PII beyond what's necessary

---

## 4. Consent Management

### 4.1 Consent States
| Status | Description |
|--------|-------------|
| `GIVEN` | User has consented to automated processing |
| `WITHDRAWN` | User has withdrawn consent |
| `UNKNOWN` | Consent status not yet determined (default) |

### 4.2 Consent Enforcement
- Emails with `WITHDRAWN` consent are not auto-processed
- Users can withdraw consent at any time
- Consent withdrawal triggers data review for right-to-be-forgotten

---

## 5. Audit Logging

### 5.1 Logged Events
All system actions are recorded in an immutable, append-only audit log:

- `email_received` — New email ingested
- `classification` — Email classified into category
- `reply_generated` — Reply draft created
- `validation_passed` / `validation_failed` — Quality validation result
- `auto_sent` — Reply automatically sent
- `manual_review` — Email flagged for human review
- `pii_detected` — PII found in email content
- `pii_redacted` — PII redacted from content
- `data_deleted` — Data removed (retention or right-to-be-forgotten)
- `data_anonymized` — PII removed, metadata retained
- `data_exported` — User data exported (portability)
- `consent_given` / `consent_withdrawn` — Consent state changes

### 5.2 Audit Record Fields
- Timestamp, email ID, action type, operator, details (JSON), IP address, user agent

---

## 6. Data Retention

### 6.1 Retention Periods
| Data Type | Retention Period | Action at Expiry |
|-----------|-----------------|------------------|
| Emails | 365 days | Delete or anonymize |
| Replies | 365 days | Delete with parent email |
| Audit log | 730 days | Delete (compliance minimum) |
| PII data | 180 days | Anonymize |
| Anonymized data | 1095 days | Delete |

### 6.2 Retention Actions
- **Delete**: Permanently remove data and all related records
- **Anonymize**: Remove PII, retain metadata for analytics
- **Export**: Generate JSON export for data portability

### 6.3 Automated Cleanup
The `data_retention.py` script supports:
- Scheduled deletion of expired data
- Dry-run mode for previewing changes
- Retention status reporting

---

## 7. Right to Be Forgotten (GDPR Article 17)

Users can request complete deletion of their data:

1. All emails from the user are deleted
2. All generated replies are deleted
3. Audit log entries are anonymized (not deleted, for compliance)
4. A final audit entry records the deletion request

### Usage
```bash
python scripts/data_retention.py --action forget --email user@example.com
```

---

## 8. Data Portability (GDPR Article 20)

Users can request an export of all their data in machine-readable JSON format:

```bash
python scripts/data_retention.py --action export --email user@example.com --output export.json
```

Export includes: all emails, replies, classification results, and processing metadata.

---

## 9. Security Measures

- SQLite database with file-system level access control
- PII redaction in all log outputs
- Structured logging with no raw PII in log files
- Circuit breaker pattern prevents data exposure during API failures
- Input validation on all external data

---

## 10. Third-Party Services

| Service | Data Shared | Purpose |
|---------|-------------|---------|
| OpenAI API | Email subject + body (truncated) | Classification and reply generation |
| Microsoft Graph API | Reply text | Email sending |

- Email content sent to OpenAI is subject to OpenAI's data usage policy
- No PII is intentionally sent to third-party APIs beyond what's in the email content

---

## 11. Contact

For privacy-related inquiries or data requests, contact the system administrator.
