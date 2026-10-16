# 01. System Architecture

StudyLock AI is architected as a **modular monolith** with platform-specific adapters and an offline-first data layer. This approach ensures high developer velocity, transactional consistency across sessions and reward ledger entries, and low operational overhead.

---

## 🏛️ Architectural Layers & Responsibilities

The system enforces strict boundary separations across presentation, domain logic, platform restriction adapters, and persistence engines.

### Diagram 3: Architectural Layers & Responsibilities

```mermaid
graph TB
    subgraph PresentationLayer["1. Presentation Layer"]
        P_Web["Next.js / HTML5 Dashboard<br/>(10 Screen Inventory)"]
        P_Ext["Browser Extension Popup & Redirect"]
        P_Mob["Native Mobile (Compose / SwiftUI)"]
    end

    subgraph DomainLayer["2. Domain Layer (Platform-Agnostic)"]
        D_Timer["Timer State Machine Engine"]
        D_Planner["Smart Planning Heuristic Scorer"]
        D_Rules["Precedence & Rule Evaluator"]
        D_Rewards["Reward Ledger Eligibility Engine"]
    end

    subgraph AdapterLayer["3. Platform Adapters"]
        A_DNR["declarativeNetRequest Adapter (MV3)"]
        A_Win["Windows Process Daemon Adapter"]
        A_And["Android UsageStats & Service Adapter"]
        A_IOS["iOS Screen Time Shield Adapter"]
    end

    subgraph PersistenceLayer["4. Persistence & Data"]
        DB_SQL["PostgreSQL / SQLite Core Tables"]
        DB_Ledger["Append-Only Cryptographic XP Ledger"]
        DB_Outbox["Durable Offline Outbox Sync Queue"]
    end

    PresentationLayer --> DomainLayer
    DomainLayer --> AdapterLayer
    DomainLayer --> PersistenceLayer
    AdapterLayer -.-> |Enforcement Status| DomainLayer
```

---

## ⚡ Request-Response & Command Pipeline

Commands such as starting focus, recording pauses, or completing sessions flow through standardized authentication, ownership verification, state transitions, and atomic ledger entries.

### Diagram 4: Component Interaction & Request-Response Pipeline

```mermaid
sequenceDiagram
    autonumber
    actor Student as 🧑‍🎓 Student
    participant UI as 💻 Web / Extension UI
    participant API as ⚡ FastAPI Monolith
    participant Auth as 🔒 Auth & Tenant Scope
    participant FSM as ⏱️ Focus Engine
    participant DB as 🐘 PostgreSQL / Ledger
    participant Adapter as 🛡️ OS Adapter

    Student->>UI: Click "Start Focus Session"
    UI->>API: POST /api/v1/sessions/start (Idempotency-Key)
    API->>Auth: Validate JWT & Verify Task Ownership
    Auth-->>API: Authorized (user_id confirmed)
    API->>FSM: Check Active Session Policy & Init
    FSM-->>API: State -> FOCUSING
    API->>Adapter: Request Distraction Restrictions
    Adapter-->>API: Status: ACTIVE
    API->>DB: Insert focus_sessions record
    DB-->>API: Committed
    API-->>UI: 201 Created (session_id, started_at, end_at)
    UI-->>Student: Display Live Ticking Timer & Active Shield
```

---

## 📦 Modular Monolith Domain Submodule Graph

All services share a common database engine and schema models, avoiding distributed transactions while maintaining strict logical boundaries.

### Diagram 5: Modular Monolith Domain Submodule Graph

```mermaid
flowchart LR
    subgraph CoreGateway["FastAPI Application Gateway (/api/v1)"]
        direction TB
        AuthM["Auth Router<br/>(JWT PBKDF2)"]
        UsersM["Users Router<br/>(Timezones)"]
        TasksM["Tasks Router<br/>(Optimistic Revisions)"]
        SchedM["Schedules Router<br/>(IANA Recurrence)"]
        SessM["Sessions Router<br/>(State Machine)"]
        RulesM["Rules Router<br/>(Precedence)"]
        RewM["Rewards Router<br/>(XP Ledger)"]
        SyncM["Sync Router<br/>(Outbox Deltas)"]
        PrivM["Privacy Router<br/>(GDPR Export)"]
    end

    subgraph SharedPersistence["Shared Relational Schema"]
        UsersT[(users)]
        TasksT[(tasks)]
        SchedulesT[(schedules)]
        SessionsT[(focus_sessions)]
        RulesT[(block_rules)]
        LedgerT[(reward_ledger)]
        SyncT[(sync_changes)]
    end

    AuthM & UsersM --> UsersT
    TasksM --> TasksT
    SchedM --> SchedulesT
    SessM --> SessionsT
    RulesM --> RulesT
    RewM --> LedgerT
    SyncM --> SyncT
```
