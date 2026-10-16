# 06. Tasks & Study Planning

StudyLock AI links discrete learning objectives directly to focus sessions, bridging the gap between broad goals and daily study execution.

---

## 📋 Task Lifecycle & Transition Model

Tasks transition across distinct operational statuses with optimistic revision numbers supporting distributed synchronization.

### Diagram 19: Task Lifecycle & Transition Model

```mermaid
stateDiagram-v2
    [*] --> TODO: User Creates Task (rev 1)

    TODO --> IN_PROGRESS: Focus session launched with task
    TODO --> DONE: Manually marked complete (+20 XP)
    TODO --> ARCHIVED: Soft deleted or archived

    IN_PROGRESS --> DONE: Session completes task objective (+20 XP)
    IN_PROGRESS --> TODO: Session ends without finishing task
    IN_PROGRESS --> ARCHIVED: Dismissed

    DONE --> TODO: Reopened by explicit user choice
    DONE --> ARCHIVED: Archived after sprint completion

    ARCHIVED --> [*]: Tombstone propagated through sync
```

---

## 🔗 Task-Linked Focus Session Orchestration

When a learner initiates focus on a specific task, the system binds the session to the task entity, tracks cumulative study minutes, and auto-completes or logs progress.

### Diagram 20: Task-Linked Focus Session Orchestration

```mermaid
sequenceDiagram
    autonumber
    actor Learner as 🧑‍🎓 Student
    participant UI as 💻 Dashboard / Task Screen
    participant TasksAPI as 📋 Tasks Router
    participant SessAPI as ⏱️ Sessions Router
    participant Ledger as 🏆 Reward Ledger

    Learner->>UI: Selects "Distributed Systems Lab Review" -> Click Focus
    UI->>SessAPI: POST /api/v1/sessions/start (task_id, planned_minutes=45)
    SessAPI->>TasksAPI: Fetch task & update status -> IN_PROGRESS
    SessAPI-->>UI: Live Focus Session Active
    Note over UI,Learner: 45 Minutes of focused study...
    Learner->>UI: Click "Finish Session & Claim Reward"
    UI->>SessAPI: POST /api/v1/sessions/{id}/finish
    SessAPI->>Ledger: Transactional insert (+40 XP Deep Focus)
    SessAPI->>TasksAPI: Update task cumulative_minutes += 45
    alt Learner marks task fully completed
        SessAPI->>Ledger: Transactional insert (+20 XP Task Completion)
        SessAPI->>TasksAPI: Update task status -> DONE
    end
    SessAPI-->>UI: Return Session Summary & Total XP
    UI-->>Learner: Display Celebration Modal
```
