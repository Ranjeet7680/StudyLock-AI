# StudyLock AI — Security, Privacy & Threat Model Specification

Ref: StudyLock AI Architecture Specification Section 16

---

## 1. Threat Model & Mitigations

| Threat | Risk / Scenario | Architectural Mitigation |
|---|---|---|
| **Account Takeover** | Stolen or intercepted access tokens | Short-lived JWT (15-60 min) with refresh rotation, secure HTTP-only cookies/storage, revocation |
| **Cross-User Data Access (IDOR)** | Attacker guesses task or session UUID | Tenant-scoping on EVERY database query (`user_id == current_user.id`); automated IDOR regression tests |
| **Reward Fraud / Replay** | User replays session completion to mint unlimited XP | `reward_ledger.event_key` has a strict database `UNIQUE` constraint; transactions enforce single execution; bounded XP caps |
| **Local Data Exposure** | Lost device or unencrypted backups | Local database encryption, OS keychain/keystore integration, data minimization |
| **False Enforcement Claim** | OS permission revoked mid-session | Adapter continuous health polling transitions session to `DEGRADED` state with transparent UI notice |
| **Malicious Rule Input** | Malformed regex or ReDoS attack | Domain canonicalization, strict input length limits, safe pattern compilation with regex timeouts |
| **Unsafe Lock-In** | Student trapped in strict mode during emergency | Emergency exit is always available across mobile, desktop, and web with non-shaming neutral reason |

---

## 2. Privacy Baseline (Section 16.2)

1. **Zero Content Surveillance:**
   StudyLock AI never collects private messages, search queries, screen video, or keystrokes.
2. **Minimal Data Collection:**
   Only target domain/package rules, session timestamps, and user task titles are stored.
3. **Data Sovereignty & Portability:**
   A machine-readable JSON data export (`POST /api/v1/privacy/export`) is available at any time.
4. **Permanent Account Deletion:**
   Executing `POST /api/v1/privacy/delete-account` immediately cascades deletion of all tasks, schedules, sessions, rules, and ledger records.
