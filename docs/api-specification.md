# StudyLock AI — API Specification

**Base URL:** `/api/v1`  
**Protocol:** HTTPS / JSON  
**Auth Header:** `Authorization: Bearer <JWT_ACCESS_TOKEN>`  
**Idempotency Header:** `Idempotency-Key: <UUID>`

---

## 1. Standard Error Schema

All API error responses conform to Section 13.4:

```json
{
  "error": {
    "code": "ENFORCEMENT_PERMISSION_REQUIRED",
    "message": "A required permission is not available on this device.",
    "request_id": "9491a938-16e5-4f40-8b1e-b8d4bb9292a8",
    "retryable": false
  }
}
```

---

## 2. Endpoint Catalogue

### Authentication (`/api/v1/auth`)
| Method | Path | Description |
|---|---|---|
| `POST` | `/auth/register` | Register new user account with hashed password |
| `POST` | `/auth/login` | Authenticate user, receive JWT access token |
| `GET` | `/auth/me` | Retrieve profile of authenticated user |

### Users (`/api/v1/users`)
| Method | Path | Description |
|---|---|---|
| `GET` | `/users/me` | Fetch user settings, timezone, display name |
| `PATCH` | `/users/me` | Update display name and IANA timezone |

### Devices (`/api/v1/devices`)
| Method | Path | Description |
|---|---|---|
| `GET` | `/devices` | List registered devices owned by user |
| `POST` | `/devices` | Register client platform instance |
| `POST` | `/devices/{id}/heartbeat` | Update device connectivity & app version |
| `POST` | `/devices/{id}/enforcement-report`| Report active, partial, or failed restrictions |

### Tasks (`/api/v1/tasks`)
| Method | Path | Description |
|---|---|---|
| `GET` | `/tasks` | List active tasks with filters (`status`, `subject`) |
| `POST` | `/tasks` | Create study task with priority and estimate |
| `GET` | `/tasks/{id}` | Read single task details |
| `PATCH` | `/tasks/{id}` | Update task with revision check (awards +20 XP on completion) |
| `DELETE`| `/tasks/{id}` | Soft-delete task for sync tombstone propagation |

### Schedules (`/api/v1/schedules`)
| Method | Path | Description |
|---|---|---|
| `GET` | `/schedules` | List recurring timetable blocks |
| `POST` | `/schedules` | Create recurring study schedule |
| `PATCH` | `/schedules/{id}` | Update schedule block timing / recurrence |
| `DELETE`| `/schedules/{id}` | Remove schedule block |
| `GET` | `/schedules/suggested-plan`| AI planner ranked tasks and conflict detection |

### Focus Sessions (`/api/v1/sessions`)
| Method | Path | Description |
|---|---|---|
| `POST` | `/sessions/start` | Initialize focus session and request OS restriction |
| `POST` | `/sessions/{id}/pause` | Pause timer, record interruption timestamp |
| `POST` | `/sessions/{id}/resume` | Resume session, compute cumulative pause time |
| `POST` | `/sessions/{id}/finish` | Transactionally complete session & mint XP ledger entry |
| `POST` | `/sessions/{id}/cancel` | Emergency exit with neutral log |
| `GET` | `/sessions` | Query session history (last 50) |

### Block Rules (`/api/v1/block-rules`)
| Method | Path | Description |
|---|---|---|
| `GET` | `/block-rules` | Query user block rules |
| `POST` | `/block-rules` | Create domain, package, or URL rule |
| `PATCH` | `/block-rules/{id}` | Update rule configuration |
| `DELETE`| `/block-rules/{id}` | Remove rule |
| `POST` | `/block-rules/test` | Simulate rule evaluation against candidate URL |

### Rewards & Gamification (`/api/v1/rewards`)
| Method | Path | Description |
|---|---|---|
| `GET` | `/rewards/ledger` | Query immutable XP ledger & calculated level |
| `GET` | `/rewards/achievements`| Query achievement catalog & unlock status |

### Analytics (`/api/v1/analytics`)
| Method | Path | Description |
|---|---|---|
| `GET` | `/analytics/weekly` | 7-day focus minutes, subjects, adherence |
| `GET` | `/analytics/dashboard`| Daily goal progress, today focus time, streak |

### Sync Engine (`/api/v1/sync`)
| Method | Path | Description |
|---|---|---|
| `POST` | `/sync/push` | Upload client outbox changes idempotently |
| `GET` | `/sync/pull` | Incremental pull after cursor timestamp |

### Privacy & Data Sovereignty (`/api/v1/privacy`)
| Method | Path | Description |
|---|---|---|
| `POST` | `/privacy/export` | Complete GDPR/CCPA machine-readable JSON export |
| `POST` | `/privacy/delete-account`| Cascade deletion of user and all related records |
