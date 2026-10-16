# StudyLock AI — Complete Cross-Platform Product Architecture & Implementation

StudyLock AI is a comprehensive, student-focused productivity system designed to reduce digital distraction while making study planning measurable, transparent, and motivating. It combines a local focus engine with operating-system-specific restriction adapters, task and calendar scheduling, progress analytics, and a cryptographic reward ledger.

---

## 🏛️ System Architecture Overview

```
                                  +------------------------------------+
                                  |           StudyLock AI             |
                                  |         FastAPI Monolith           |
                                  |          (/api/v1/...)             |
                                  +-----------------+------------------+
                                                    |
                   +--------------------------------+--------------------------------+
                   |                                |                                |
         [PostgreSQL / SQLite]               [Redis / Worker]              [Encrypted Sync Queue]
        Relational Core Ledger             Async Job Scheduling            Outbox & Tombstones
                   |                                |                                |
  +----------------+----------------+---------------+----------------+---------------+----------------+
  |                                 |                                |                                |
[Web Dashboard]           [Browser Extension]               [Desktop Helper]               [Mobile Clients]
Next.js 14 / React        Chrome/Edge Manifest V3           Windows / macOS Daemon         Android (Kotlin/Compose)
Tailwind + Full Screen    DeclarativeNetRequest             Native Process & Host          iOS (SwiftUI / ScreenTime)
Inventory & Analytics     distraction redirector            Blocking Adapters              Offline First + Room
```

---

## 📦 Directory Structure

```
studylock-ai/
  apps/
    android/                 # Native Android app (Kotlin, Compose, Room, WorkManager, Accessibility/UsageStats)
    ios/                     # Native iOS app (SwiftUI, FamilyControls, ManagedSettings, DeviceActivity)
    web/                     # Web dashboard (Next.js 14, Tailwind, TypeScript, Full Screen Inventory)
    desktop/                 # Windows/macOS desktop helper & native blocking daemon
    browser-extension/       # Manifest V3 extension for Chrome/Edge (domain & URL blocker)
  services/
    api/                     # FastAPI modular monolith (Auth, Devices, Tasks, Schedules, Sessions, Rules, Ledger, Sync)
    worker/                  # Background worker for notification dispatch and analytics aggregation
  packages/
    schemas/                 # Shared domain data models, state machines, and scoring heuristics
    api-client/              # Generated typed API client for Python and TypeScript
    design-system/           # Color tokens (calm navy/blue theme), typography, spacing, and icons
  infra/
    docker/                  # Dockerfile and docker-compose.yml for end-to-end stack
    deployment/              # CI/CD workflows and deployment configurations
    monitoring/              # Observability, Prometheus metrics, structured logging
  tests/
    unit/                    # Domain logic, timer math, recurrence, XP calculation
    integration/             # API transactions, cross-user auth, idempotency, outbox sync
    platform/                # Adapter behavior with mock OS
    security/                # IDOR checks, credential hygiene, log redaction
    e2e/                     # End-to-end full session lifecycle
  docs/                      # Comprehensive technical specifications & manuals
    architecture.md
    api-specification.md
    database-schema.md
    privacy-security.md
    test-plan.md
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ / 20+
- (Optional) Docker & Docker Compose

### 2. Backend API Setup
```bash
cd services/api
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
API docs available at: `http://127.0.0.1:8000/docs`

### 3. Web Dashboard Setup
```bash
cd apps/web
npm install
npm run dev
```
Interactive Web Dashboard available at: `http://localhost:3000`

### 4. Browser Extension Installation
1. Open Google Chrome or Microsoft Edge.
2. Navigate to `chrome://extensions/` or `edge://extensions/`.
3. Enable **Developer mode**.
4. Click **Load unpacked** and select `apps/browser-extension`.

### 5. Desktop Native Blocker Helper
```bash
cd apps/desktop
python helper.py
```

### 6. Run Test Suite
```bash
pytest tests/ -v
```
