# 02. Focus Session Engine & State Machine

The core focus engine controls the study interval lifecycle, accounting for pauses, breaks, and emergency exits with mathematical precision.

---

## 🔄 Focus Session Finite State Machine

Sessions progress through deterministic states governed by the transitions defined in Section 7.1. Invalid transitions raise structured domain exceptions.

### Diagram 6: Focus Session Finite State Machine Transitions

```mermaid
stateDiagram-v2
    [*] --> PLANNED: Schedule or User Intent

    PLANNED --> STARTING: User clicks Start
    PLANNED --> CANCELLED: Dismissed before start

    STARTING --> FOCUSING: Restrictions verified ACTIVE
    STARTING --> DEGRADED: Partial restriction applied
    STARTING --> FAILED: Permission denied / crash

    FOCUSING --> PAUSED: User pauses session
    FOCUSING --> BREAK: Scheduled rest interval
    FOCUSING --> COMPLETED: Target time reached (>= 80%)
    FOCUSING --> CANCELLED: Emergency exit invoked

    PAUSED --> FOCUSING: Resumed (records pause delta)
    PAUSED --> CANCELLED: Exit during pause

    BREAK --> FOCUSING: Break finished, study resumes
    BREAK --> COMPLETED: Finished after final break
    BREAK --> CANCELLED: Exit during break

    DEGRADED --> FOCUSING: Permissions restored
    DEGRADED --> PAUSED: Paused during degraded
    DEGRADED --> COMPLETED: Completed with degraded status
    DEGRADED --> CANCELLED: Emergency exit

    COMPLETED --> [*]: Terminal (Mints XP to Ledger)
    CANCELLED --> [*]: Terminal (Neutral logging)
    FAILED --> [*]: Terminal (Offers retry)
```

---

## ⏱️ Monotonic Timer Math & Recovery

StudyLock AI never relies on a ticking counter or setInterval as the sole source of truth. Elapsed time is computed directly from durable timestamps to ensure resilience against app suspension, low-memory process kills, and system reboots.

### Diagram 7: Timer Correctness & Timestamp Recovery Algorithm

```mermaid
sequenceDiagram
    autonumber
    participant App as 📱 Mobile / Web App
    participant Clock as ⏰ Monotonic Clock
    participant Storage as 💾 Durable Storage (SQLite / Room)
    participant OS as ⚙️ Operating System

    App->>Clock: Read t0 (start timestamp)
    App->>Storage: Persist session(started_at=t0, planned_minutes=25, paused_seconds=0)
    Note over App,OS: User studies for 12 minutes...
    App->>Storage: Record pause event at t1
    Note over App,OS: OS kills app background process due to low memory!
    Note over App,OS: 3 minutes pass while app is completely dead...
    App->>App: User relaunches application
    App->>Storage: Load session(started_at=t0, paused_seconds=0, last_pause=t1)
    App->>Clock: Read t2 (current recovery timestamp)
    App->>App: Calculate elapsed = (t2 - t0) - (t2 - t1)
    Note over App: Zero time lost! Timer accurately resumes at 12:00 remaining!
```

$$\text{Net Focus Seconds} = \max\left(0, (\text{Current Time} - \text{Started At}) - \text{Cumulative Paused Seconds}\right)$$

---

## 🔒 Strict Mode Friction & Emergency Exit

Strict mode introduces friction against impulsive cancellation while guaranteeing that the user is never trapped.

### Diagram 8: Strict Mode Friction & Emergency Exit Flow

```mermaid
flowchart TD
    Focus["Active Focus Session (Strict Mode Enabled)"] --> UserExit["User clicks 'Emergency Exit'"]
    
    UserExit --> PromptModal["Display Friction Confirmation Modal<br/>(Explain that actual focus time will be saved, but completion reward requires full session)"]

    PromptModal --> |User Clicks 'Stay in Focus'| ReturnFocus["Resume Active Timer & Enforced Restrictions"]
    PromptModal --> |User Clicks 'Exit Session'| CancelAction["Execute Emergency Exit"]

    CancelAction --> OS_Restore["Adapter immediately restores all app & website access"]
    CancelAction --> AuditLog["Log neutral exit reason: 'session exited early' (No shame copy)"]
    CancelAction --> TerminalState["Session marked CANCELLED • Summary Screen Displayed"]
```
