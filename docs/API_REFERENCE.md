# API Reference

## Base URL

```
http://localhost:5005
```

---

## Authentication

### `GET /auth/login`
Redirects to Microsoft Azure AD login.

### `GET /auth/callback`
OAuth2 callback handler. Stores tokens in session.

### `GET /auth/logout`
Clears session and logs out.

---

## Email Operations

### `GET /api/emails`
Fetch and process new emails from Outlook.

**Response**: List of processed email records with classification and reply.

### `GET /api/emails/list`
List all stored emails with optional filters.

**Query Parameters**:
- `status` — Filter by status (auto_sent, pending_review, ignored_no_reply)
- `category` — Filter by category
- `limit` — Max results (default: 50)
- `offset` — Pagination offset

### `POST /api/emails/{id}/approve`
Approve and send a pending email reply.

### `POST /api/emails/{id}/reject`
Reject a pending email reply.

### `POST /api/emails/{id}/edit`
Edit reply text before sending.

**Body**: `{"reply_text": "Updated reply..."}`

---

## Health Checks

### `GET /health`
Full system health check.

**Response** (200/207/503):
```json
{
  "status": "healthy|degraded|unhealthy",
  "checks": {"database": {...}, "openai_api": {...}, "graph_api": {...}},
  "circuit_breakers": {...}
}
```

### `GET /health/ready`
Kubernetes readiness probe. Returns 200 if database is accessible.

### `GET /health/live`
Kubernetes liveness probe. Always returns 200 if app is running.

### `GET /health/database`
Database connectivity check.

### `GET /health/openai`
OpenAI API connectivity check.

### `GET /health/circuit-breakers`
Circuit breaker states for all services.

---

## Metrics

### `GET /metrics`
Summary metrics for the system.

**Query Parameters**:
- `start_date` — ISO date (default: 30 days ago)
- `end_date` — ISO date (default: now)

**Response**:
```json
{
  "total_emails": 150,
  "auto_send_rate": 65.3,
  "average_confidence": 0.823,
  "status_distribution": {"auto_sent": 98, "pending_review": 42, ...},
  "category_breakdown": [{"category": "pricing_inquiry", "count": 45, ...}]
}
```

### `GET /metrics/timeseries`
Daily aggregated metrics for trend charts.

### `GET /metrics/quality`
Reply validation pass rates.

### `GET /metrics/pii`
PII detection rates.

---

## Company Info

### `GET /api/company/products`
List all products in the catalog.

### `POST /api/company/products`
Add a new product.

### `PUT /api/company/products/{id}`
Update a product.

### `DELETE /api/company/products/{id}`
Delete a product.
