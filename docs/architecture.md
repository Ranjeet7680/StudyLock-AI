# StudyLock AI — Complete Architecture Specification

StudyLock AI is a student productivity and focus platform combining a local focus engine with operating-system-specific restriction adapters, task/calendar scheduling, progress analytics, and a cryptographic reward ledger.

---

## 1. System Topology

```
+----------------------------------------------------------------------------------------------------+
|                                         StudyLock AI Cloud                                         |
|                                     FastAPI Modular Monolith                                       |
+--------------------------------------------------+-------------------------------------------------+
                                                   |
                   +-------------------------------+-------------------------------+
                   |                               |                               |
          [PostgreSQL Engine]              [Redis & Worker]              [Outbox Sync Ledger]
         Relational Core Data          Background Reminders & Jobs      Delta Synchronization
                   |                               |                               |
+------------------+-------------------------------+-------------------------------+-----------------+
|                                                  |                                                 |
|  CLIENT PLATFORMS                                |  RESTRICTION ADAPTERS                           |
|  1. Web Dashboard (Next.js / HTML5 + Tailwind)  |  1. Chrome/Edge WebExtension (DNR Rules)        |
|  2. Windows Desktop (Native Background Daemon)   |  2. Windows Host / Process Blocker Adapter      |
|  3. Android Companion (Kotlin, Compose, Room)    |  3. Android UsageStats & Accessibility Service   |
|  4. iOS Companion (SwiftUI, Screen Time)        |  4. iOS FamilyControls & ManagedSettings Shield |
+--------------------------------------------------+-------------------------------------------------+
```

---

## 2. Core Architectural Principles

1. **Honest Enforcement:**
   Show precisely which apps, websites, and platforms are protected and which are not. Never label a restriction "ACTIVE" solely because a timer is ticking.
2. **Local-First Reliability:**
   Timers and schedules survive ordinary app suspension, reboot, and network disconnection.
3. **User Agency & Non-Shaming:**
   Visible emergency exit with neutral exit logging ("session exited early"). Never shame students for pausing or exiting.
4. **Learning Over Screen Time:**
   Reward goal completion, learning consistency, and task follow-through rather than raw app-open duration.
5. **Privacy by Default:**
   Minimal data collection, zero browsing history logs, local data sovereignty, transparent export, and permanent deletion paths.

---

## 3. Focus Session State Machine

The session lifecycle is governed by a deterministic state engine:

```
          +-------------+
          |   PLANNED   |
          +------+------+
                 |
                 v
          +-------------+
          |  STARTING   |
          +------+------+
                 |
      +----------+----------+
      |                     |
      v                     v
+-----------+         +-----------+
| FOCUSING  |<------->|   PAUSED  |
+-----+-----+         +-----------+
      |
      +--------------> BREAK
      |
      +--------------> DEGRADED (Partial protection)
      |
      v
+-----------+
| COMPLETED | (Terminal - Triggers Transactional XP Ledger)
+-----------+
```

### Timer Correctness
- Timestamps (`started_at`, `ended_at`, `last_pause_at`) are persisted durably.
- Elapsed time is calculated dynamically:
  $$\text{Net Focus Seconds} = (\text{Current Time} - \text{Started At}) - \text{Cumulative Paused Seconds}$$
- Survives process death and system restarts without drifting counters.
