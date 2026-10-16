# StudyLock AI — Relational Database Schema Specification

StudyLock AI utilizes PostgreSQL in production with full backward-compatibility with SQLite for local-first testing and offline clients.

---

## 1. Entity-Relationship Diagram

```
+--------------------+            +--------------------+
|       users        | 1        * |      devices       |
+--------------------+------------+--------------------+
| id (PK, UUID)      |            | id (PK, UUID)      |
| email (Unique)     |            | user_id (FK)       |
| password_hash      |            | platform           |
| display_name       |            | app_version        |
| timezone           |            | last_sync_at       |
| created_at         |            +--------------------+
+---------+----------+
          | 1
          |
          +-----------------------+-----------------------+-----------------------+
          | *                     | *                     | *                     | *
+---------v----------+  +---------v----------+  +---------v----------+  +---------v----------+
|       tasks        |  |     schedules      |  |   focus_sessions   |  |   reward_ledger    |
+--------------------+  +--------------------+  +--------------------+  +--------------------+
| id (PK, UUID)      |  | id (PK, UUID)      |  | id (PK, UUID)      |  | id (PK, UUID)      |
| user_id (FK)       |  | user_id (FK)       |  | user_id (FK)       |  | user_id (FK)       |
| title              |  | title              |  | task_id (FK, Null) |  | session_id (FK)    |
| subject            |  | timezone           |  | started_at         |  | event_key (Unique) |
| priority (1..4)    |  | start_minute       |  | ended_at           |  | xp_delta           |
| estimated_minutes  |  | duration_minutes   |  | planned_minutes    |  | reason             |
| due_at             |  | recurrence (JSON)  |  | actual_seconds     |  | created_at         |
| status             |  | enabled            |  | paused_seconds     |  +--------------------+
| revision           |  | revision           |  | status             |
| deleted_at (Soft)  |  +--------------------+  | interruptions      |
+--------------------+                          +--------------------+
```

---

## 2. Table Definitions & Constraints

### 2.1 `users`
- `id`: `UUID PRIMARY KEY`
- `email`: `VARCHAR(255) UNIQUE NOT NULL`
- `password_hash`: `VARCHAR(255) NOT NULL` (PBKDF2-HMAC-SHA256 salted)
- `display_name`: `VARCHAR(100) NOT NULL`
- `timezone`: `VARCHAR(64) DEFAULT 'Asia/Kolkata'`
- `created_at`: `TIMESTAMPTZ DEFAULT now()`

### 2.2 `tasks`
- `id`: `UUID PRIMARY KEY`
- `user_id`: `UUID REFERENCES users(id) ON DELETE CASCADE`
- `title`: `VARCHAR(255) NOT NULL`
- `priority`: `SMALLINT CHECK (priority BETWEEN 1 AND 4)`
- `status`: `VARCHAR(24) DEFAULT 'todo'`
- `revision`: `INTEGER DEFAULT 1` (Optimistic concurrency)
- `deleted_at`: `TIMESTAMPTZ NULL` (Tombstone for sync propagation)

### 2.3 `focus_sessions`
- `id`: `UUID PRIMARY KEY`
- `user_id`: `UUID REFERENCES users(id) ON DELETE CASCADE`
- `task_id`: `UUID REFERENCES tasks(id) ON DELETE SET NULL`
- `started_at`: `TIMESTAMPTZ NOT NULL`
- `ended_at`: `TIMESTAMPTZ NULL`
- `planned_minutes`: `INTEGER CHECK (planned_minutes BETWEEN 1 AND 240)`
- `actual_seconds`: `INTEGER DEFAULT 0`
- `paused_seconds`: `INTEGER DEFAULT 0`
- `status`: `VARCHAR(24) DEFAULT 'PLANNED'`
- `interruptions`: `INTEGER DEFAULT 0`

### 2.4 `reward_ledger` (Section 10.1)
- `id`: `UUID PRIMARY KEY`
- `user_id`: `UUID REFERENCES users(id) ON DELETE CASCADE`
- `session_id`: `UUID REFERENCES focus_sessions(id) ON DELETE SET NULL`
- `event_key`: `VARCHAR(255) UNIQUE NOT NULL` (Prevents duplicate XP minting)
- `xp_delta`: `INTEGER NOT NULL`
- `reason`: `VARCHAR(255) NOT NULL`
- `created_at`: `TIMESTAMPTZ DEFAULT now()`

---

## 3. Indexing Strategy

- `CREATE INDEX idx_tasks_user_status ON tasks(user_id, status);`
- `CREATE INDEX idx_tasks_user_due ON tasks(user_id, due_at);`
- `CREATE INDEX idx_sessions_user_started ON focus_sessions(user_id, started_at DESC);`
- `CREATE INDEX idx_rules_user_device ON block_rules(user_id, device_id);`
- `CREATE INDEX idx_rewards_user_created ON reward_ledger(user_id, created_at DESC);`
