# 10. Observability, Deployment & Operations

StudyLock AI incorporates end-to-end monitoring, device health heartbeats, Docker multi-container composition, and automated Vercel/GitHub CI pipelines.

---

## 🚀 Observability & CI/CD Deployment Pipeline

From local code commit to cloud production deployment, automated pipelines validate types, run all 26 regression test suites, build Docker containers, and trigger instant Vercel previews.

### Diagram 30: Observability, Health Heartbeats & CI/CD Deployment Pipeline

```mermaid
flowchart TD
    subgraph DevPipeline["1. Development & Quality Gate"]
        Dev["Git Push to 'main'"] --> Lint["Linter & Typecheck (flake8 / mypy / eslint)"]
        Lint --> Pytest["Run Full Pytest Suite<br/>(26/26 Tests Passing: FSM, Rules, Sync, IDOR)"]
    end

    subgraph CD_Deploy["2. Continuous Deployment"]
        Pytest --> BuildDocker["Build Docker Images<br/>(infra/docker/Dockerfile.api & .web)"]
        Pytest --> VercelDeploy["Vercel 1-Click Static Deployment<br/>(outputDirectory: apps/web)"]
        BuildDocker --> Compose["Deploy Docker Compose Stack<br/>(API, Web, Postgres, Redis, Worker)"]
    end

    subgraph Observability["3. Live Observability & Telemetry"]
        Compose --> MetricsAPI["API Health Check (/health) & Latency Metrics"]
        Compose --> HeartbeatMon["Device Heartbeat Ingestion<br/>POST /api/v1/devices/{id}/heartbeat"]
        HeartbeatMon --> HealthMatrix["Platform Enforcement Health Matrix<br/>(Active / Partial / Degraded / Repair)"]
        MetricsAPI --> LogRedaction["Structured JSON Logs with Secret Redaction"]
    end

    DevPipeline --> CD_Deploy --> Observability
```

---

## 🛠️ Operations Runbook

### Health Checks
- **HTTP Health:** `GET http://127.0.0.1:8000/health`
  ```json
  {
    "status": "ok",
    "service": "StudyLock AI API",
    "version": "1.0.0",
    "environment": "development"
  }
  ```

### Zero-Downtime Database Migrations
- Schema updates utilize backward-compatible column defaults and revision numbers to support zero-downtime rolling upgrades.

### Redaction Rules
- Authentication tokens, passwords, and user task descriptions are strictly redacted before output to structured application logs.
