# 07. Cryptographic Reward Ledger & Integrity

StudyLock AI treats user progression with cryptographic integrity. XP is not an arbitrarily editable profile counter; it is the derived sum of an immutable append-only event ledger.

---

## 🔒 Transactional Ledger & Anti-Duplication Pipeline

Every reward event requires a deterministic, unique event key. Database unique constraints and transactional execution guarantee that network retries or replay attacks can never mint duplicate XP.

### Diagram 21: Reward Ledger Transaction & Idempotency Pipeline

```mermaid
sequenceDiagram
    autonumber
    actor Client as 📱 Client App
    participant API as ⚡ Sessions Router
    participant Tx as 🔄 Database Transaction
    participant Ledger as 📜 reward_ledger Table
    participant Calc as 🧮 Level Calculator

    Client->>API: POST /api/v1/sessions/{id}/finish (Idempotency-Key)
    API->>API: Calculate actual net focus duration (excl. pauses)
    API->>API: Check eligibility (duration >= 80% planned)
    API->>API: Construct event_key = "EVT_SESSION_45M:" + session.id

    API->>Tx: BEGIN TRANSACTION
    Tx->>Ledger: INSERT INTO reward_ledger (event_key, user_id, xp_delta=40, reason)
    alt Key already exists (Replay / Duplicate Request)
        Ledger-->>Tx: UNIQUE CONSTRAINT VIOLATION!
        Tx-->>API: Rollback transaction (Zero duplicate XP minted)
    else First time completion
        Ledger-->>Tx: Insert successful
        Tx-->>API: COMMIT TRANSACTION
    end

    API->>Calc: SUM(xp_delta) FROM reward_ledger WHERE user_id = :uid
    Calc-->>API: Total XP: 185 XP (Level 2 Scholar)
    API-->>Client: 200 OK (xp_awarded=40, total_xp=185, level=2)
```

---

## 📈 Level Progression & Bounded XP Caps

To maintain game balance and eliminate unhealthy marathon farming, XP per session is bounded at 100 XP, with level thresholds scaling predictably.

### Diagram 22: Level Progression & Bounded XP Mathematical Curve

```mermaid
flowchart LR
    Session["Completed Focus Interval"] --> CalcXP["Compute Base XP:<br/>Standard (<45m): 25 XP<br/>Deep Focus (>=45m): 40 XP"]
    CalcXP --> CapCheck{"XP > MAX_XP_PER_SESSION (100)?"}
    CapCheck --> |Yes| ApplyCap["Cap at 100 XP"]
    CapCheck --> |No| KeepBase["Retain Calculated XP"]

    ApplyCap & KeepBase --> LedgerCommit["Append to reward_ledger"]
    LedgerCommit --> LevelProgression["Compute Level:<br/>Level N requires 100 * N XP"]

    LevelProgression --> L1["Level 1: 0 - 100 XP"]
    LevelProgression --> L2["Level 2: 101 - 300 XP"]
    LevelProgression --> L3["Level 3: 301 - 600 XP"]
    LevelProgression --> L4["Level N: Sum(100*i)"]
```

---

## 🔥 Streak Integrity & Rest Day Forgiveness

StudyLock AI rejects manipulative shame mechanics. Streaks reward learning consistency while providing built-in rest day forgiveness and recovery.

### Diagram 23: Streak Integrity, Grace Periods & Rest Day Forgiveness Flow

```mermaid
flowchart TD
    DayEnd["End of Study Day (23:59 Local Timezone)"] --> CheckFocus{"Qualified Focus Session Recorded Today?"}

    CheckFocus --> |Yes (>= 1 Session)| IncrementStreak["Streak Count++<br/>(Award Milestone Badge at 3, 7, 30 days)"]
    
    CheckFocus --> |No Session| CheckRestDay{"Is Today a Configured Rest Day<br/>OR Streak Freeze Available?"}

    CheckRestDay --> |Yes| Forgive["Maintain Active Streak Unchanged<br/>('Rest Day Honored')"]
    CheckRestDay --> |No| GracePeriod{"Within 24h Grace Period?"}

    GracePeriod --> |Yes| OfferCatchup["Prompt: 'Complete a 25-minute recovery session to preserve streak'"]
    GracePeriod --> |No| GentleReset["Reset to Day 1<br/>Encouraging copy: 'Consistency is built over time' (No shame copy)"]
```
