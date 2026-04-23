# API Module

This directory contains Flask API endpoints for the email responder system.

## Endpoints

### Health Check (`health.py`)

Health monitoring endpoints for system status:

- `GET /health` - Overall system health
- `GET /health/database` - Database connectivity
- `GET /health/openai` - OpenAI API connectivity
- `GET /health/graph` - Graph API connectivity
- `GET /health/circuit-breakers` - Circuit breaker states
- `GET /health/ready` - Readiness probe (Kubernetes)
- `GET /health/live` - Liveness probe (Kubernetes)

## Usage

```python
from flask import Flask
from api.health import health_bp

app = Flask(__name__)
app.register_blueprint(health_bp)
```

## Health Status Codes

- `200 OK` - System is healthy
- `207 Multi-Status` - System is degraded (some components unhealthy)
- `503 Service Unavailable` - System is unhealthy
