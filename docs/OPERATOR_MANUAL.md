# Operator Manual

## Daily Operations

### Monitoring System Health
```bash
curl http://localhost:5005/health
curl http://localhost:5005/metrics
```

### Reviewing Flagged Emails
Emails with `status = 'pending_review'` need human review. Access via:
- `GET /api/emails/list?status=pending_review`
- Approve: `POST /api/emails/{id}/approve`
- Reject: `POST /api/emails/{id}/reject`
- Edit: `POST /api/emails/{id}/edit`

### Checking Circuit Breakers
```bash
curl http://localhost:5005/health/circuit-breakers
```
If a circuit breaker is `OPEN`, the service is failing. It will auto-recover after the timeout period (default: 60s).

---

## Common Issues

### High Manual Review Rate
- Check `GET /metrics` for average confidence
- If confidence is low, review classification prompts
- Consider lowering thresholds for well-tested categories

### API Failures
- Check `GET /health/openai` for API status
- Review logs: `logs/app.log`
- Circuit breaker will auto-recover; fallback classification uses keywords

### PII Alerts
- Check `GET /metrics/pii` for PII detection rates
- High PII rate may indicate customers sharing sensitive data
- Review flagged emails and consider adding PII handling guidance

---

## Adjusting Thresholds

Edit `config/thresholds.yaml`:
```yaml
category_thresholds:
  pricing_inquiry: 0.80  # Lower = more auto-sends
```

Restart the application after changes.

---

## Data Retention

### Preview expired data
```bash
python scripts/data_retention.py --action delete --dry-run
```

### Execute cleanup
```bash
python scripts/data_retention.py --action delete
```

### GDPR right-to-be-forgotten
```bash
python scripts/data_retention.py --action forget --email user@example.com
```

### Export user data
```bash
python scripts/data_retention.py --action export --email user@example.com
```

---

## Generating Reports

### System evaluation
```bash
python scripts/evaluate_system.py --output reports/eval.json
```

### Calibration analysis
```bash
python scripts/calibration_analysis.py --dataset data/calibration_dataset.json
```
