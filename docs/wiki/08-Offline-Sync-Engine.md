# 08. Offline Sync Engine & Durable Outbox

StudyLock AI is designed from the ground up as a **local-first** application. All core study features—creating tasks, running focus timers, and modifying schedules—operate reliably offline.

---

## 📦 Durable Outbox Replication Architecture

When an action occurs offline, it is written immediately to a local SQLite/Room database and queued into a durable outbox table before asynchronous synchronization.

### Diagram 24: Local-First Durable Outbox Replication Architecture

```mermaid
sequenceDiagram
    autonumber
    actor Student as 🧑‍🎓 Student
    participant LocalDB as 💾 Local DB (Room / SQLite)
    participant Outbox as 📬 Durable Outbox Queue
    participant SyncWorker as 🔄 Sync Background Worker
    participant CloudAPI as ☁️ StudyLock Cloud API
    participant CloudDB as 🐘 Cloud PostgreSQL

    Student->>LocalDB: Create Task: "Study Operating Systems"
    LocalDB->>LocalDB: Insert task (id, revision=1, status='todo')
    LocalDB->>Outbox: Append change (op_id, entity='task', op='create', rev=1)
    Note over Student,Outbox: Network is offline... Changes remain safely queued!

    Note over SyncWorker: Network connection restored!
    SyncWorker->>Outbox: Read pending changes
    SyncWorker->>CloudAPI: POST /api/v1/sync/push (changes=[...])
    CloudAPI->>CloudDB: Verify ownership & apply idempotently
    CloudDB-->>CloudAPI: Accepted (op_id acknowledged)
    CloudAPI-->>SyncWorker: 200 OK (accepted_operations=[op_id])
    SyncWorker->>Outbox: Remove acknowledged items
    SyncWorker->>CloudAPI: GET /api/v1/sync/pull?cursor=last_sync_timestamp
    CloudAPI-->>SyncWorker: Return server changes made on other devices
    SyncWorker->>LocalDB: Merge server updates
```

---

## 🔀 Conflict Resolution & Monotonic Revision Merge

Editable entities (tasks, schedules, rules) carry monotonically increasing `revision` counters. Silent overwrites are prevented via revision comparisons.

### Diagram 25: Conflict Resolution & Monotonic Revision Merge

```mermaid
flowchart TD
    Incoming["Incoming Change via Sync (Incoming Revision)"] --> FetchServer["Fetch Server Entity (Current Server Revision)"]

    FetchServer --> Compare{"Incoming Rev > Server Rev?"}

    Compare --> |Yes: Clean Forward Update| ApplyMerge["Apply Field-Level Merge<br/>Update Server Entity<br/>Server Rev = Incoming Rev"]
    
    Compare --> |Equal: Idempotent Replay| AcknowledgeNoop["Acknowledge Operation as Success (No-op)"]
    
    Compare --> |No: Stale Revision Detected| ConflictRule{"Entity Type Conflict Strategy"}

    ConflictRule --> |Task / Schedule| UserConflict["Flag Conflict to User<br/>Preserve Both Edits (Draft Copy Created)"]
    ConflictRule --> |Preferences| LastWriteWins["Last-Write-Wins (Timestamp)"]
```

---

## 🪦 Soft Delete Tombstone Lifecycle

Deleting records offline creates soft-delete tombstones so that deletions propagate accurately to other synced devices rather than resurrecting deleted records.

### Diagram 26: Soft Delete Tombstone Lifecycle & Propagation

```mermaid
flowchart LR
    UserDelete["User Deletes Task"] --> SoftDelete["Mark task.deleted_at = now()<br/>task.revision++"]

    SoftDelete --> OutboxLog["Append Tombstone to sync_changes<br/>(operation='delete', entity_id=task.id)"]
    OutboxLog --> PushServer["Push to Server (/api/v1/sync/push)"]
    
    PushServer --> ServerTombstone["Server updates task.deleted_at = now()<br/>Default queries filter WHERE deleted_at IS NULL"]

    ServerTombstone --> PullDevices["Other Devices Pull via Cursor"]
    PullDevices --> LocalTombstone["Local DB deletes / marks deleted"]
    LocalTombstone --> PurgePolicy["Hard Purge after 30-day Retention Window"]
```
