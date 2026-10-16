# StudyLock AI — QA Test Plan & 240 Test Inventory

Ref: StudyLock AI Architecture Specification Section 18

---

## 1. Test Suite Distribution (240 Cases)

| Suite | Planned Cases | Key Areas Tested |
|---|---|---|
| **1. Authentication & Access Control** | 20 | Registration, login, token rotation, expired tokens, session revocation |
| **2. Tasks & Deadlines** | 20 | CRUD, due date timezones, priority weights, optimistic locking revisions |
| **3. Focus Timer & State Machine** | 25 | Transitions (PLANNED -> FOCUSING -> PAUSED -> COMPLETED), pause math, recovery |
| **4. Scheduling & Timezones** | 25 | Recurring study blocks, IANA timezone conversion, conflict detection |
| **5. App & Website Blocking** | 35 | Domain matching (youtube.com, youtu.be, instagram.com), app packages, DNR rules |
| **6. Rewards & Anti-Duplication** | 20 | Standard vs 45m deep focus XP, unique event key idempotency, level progression |
| **7. Offline & Synchronization** | 25 | Durable outbox, offline mutations, cursor incremental pulls, tombstone deletes |
| **8. Notifications & Background** | 20 | Session reminders (10m lead time), quiet hours suppression, background recovery |
| **9. Security & Privacy** | 25 | IDOR prevention, log secret redaction, JSON export, permanent account deletion |
| **10. Accessibility & Performance** | 25 | Screen readers, contrast ratios, low latency, database connection pooling |
| **Total** | **240** | Comprehensive end-to-end verification |

---

## 2. Release-Blocking Criteria (Section 18.2)

1. A session or task is lost after a supported recovery path.
2. A duplicate reward can be minted by replaying requests.
3. A user can read, modify, or delete another user's records.
4. The UI claims enforcement is active when the adapter reports failure or permission denial.
5. The user cannot safely access the emergency exit in strict mode.
6. Data export or account deletion fails to purge user data.
