# Deployment Guide

## Prerequisites

- Python 3.12+
- pip
- Microsoft Azure AD app registration (for Graph API)
- OpenAI API key

## Setup

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Initialize Database
The database is auto-initialized on first run. To manually initialize:
```python
from models.database import init_db
init_db()
```

### 4. Run the Application
```bash
python app.py
```
Server starts at `http://localhost:5005`.

---

## Production Checklist

- [ ] Set `FLASK_DEBUG=False`
- [ ] Set a strong `FLASK_SECRET_KEY`
- [ ] Configure real Azure AD credentials
- [ ] Configure real OpenAI API key
- [ ] Set appropriate confidence thresholds
- [ ] Review data retention periods
- [ ] Set up log rotation (configured for 10MB, 5 backups)
- [ ] Configure health check monitoring
- [ ] Set up database backups

---

## Running Tests

```bash
cd backend

# All tests
pytest -v

# Unit tests only
pytest tests/unit/ -v

# E2E tests
pytest tests/e2e/ -v

# Regression tests
pytest tests/regression/ -v

# With coverage
pytest --cov=. --cov-report=html
```

---

## Docker (Optional)

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5005
CMD ["python", "app.py"]
```

---

## Kubernetes Health Probes

```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 5005
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health/ready
    port: 5005
  initialDelaySeconds: 5
  periodSeconds: 5
```
