"""
StudyLock AI - Offline Mode & Synchronization Router
Ref: StudyLock AI Architecture Specification Section 14
"""
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.models import SyncChange, Task, Schedule, BlockRule, User
from ..schemas.schemas import SyncPushRequest, SyncPullResponse, SyncChangeItem
from ..core.auth import get_current_user

router = APIRouter(prefix="/sync", tags=["Offline & Sync Engine"])


@router.post("/push")
def push_offline_changes(
    payload: SyncPushRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Applies offline changes uploaded from the client outbox (Spec Section 14.1 & 14.3).
    Idempotent by operation_id and entity revision.
    """
    accepted_operations = []
    rejected_operations = []

    for change in payload.changes:
        try:
            # Check if this operation was already logged in sync_changes
            existing = db.query(SyncChange).filter(
                SyncChange.user_id == current_user.id,
                SyncChange.id == change.operation_id
            ).first()

            if existing:
                accepted_operations.append(change.operation_id)
                continue

            # Record in sync ledger
            sync_record = SyncChange(
                id=change.operation_id,
                user_id=current_user.id,
                device_id=change.device_id,
                entity_type=change.entity_type,
                entity_id=change.entity_id,
                operation=change.operation,
                payload=json.dumps(change.payload),
                revision=change.revision
            )
            db.add(sync_record)

            # Apply change based on entity type
            if change.entity_type == "task":
                task = db.query(Task).filter(Task.id == change.entity_id, Task.user_id == current_user.id).first()
                if change.operation == "create":
                    if not task:
                        task = Task(
                            id=change.entity_id,
                            user_id=current_user.id,
                            title=change.payload.get("title", "Untitled Task"),
                            description=change.payload.get("description"),
                            subject=change.payload.get("subject"),
                            priority=change.payload.get("priority", 2),
                            status=change.payload.get("status", "todo"),
                            revision=change.revision
                        )
                        db.add(task)
                elif change.operation == "update" and task:
                    # Merge if incoming revision is greater
                    if change.revision >= task.revision:
                        task.title = change.payload.get("title", task.title)
                        task.status = change.payload.get("status", task.status)
                        task.revision = change.revision
                elif change.operation == "delete" and task:
                    task.deleted_at = datetime.now(timezone.utc)
                    task.revision = change.revision

            db.commit()
            accepted_operations.append(change.operation_id)

        except Exception as e:
            db.rollback()
            rejected_operations.append({
                "operation_id": change.operation_id,
                "reason": str(e)
            })

    return {
        "status": "synchronized",
        "accepted_count": len(accepted_operations),
        "rejected_count": len(rejected_operations),
        "accepted_operations": accepted_operations,
        "rejected_operations": rejected_operations,
        "server_time": datetime.now(timezone.utc).isoformat()
    }


@router.get("/pull", response_model=SyncPullResponse)
def pull_changes(
    cursor: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Fetches incremental server changes after given cursor (Spec Section 13.2 & 14.3).
    """
    query = db.query(SyncChange).filter(SyncChange.user_id == current_user.id)
    if cursor:
        try:
            cursor_dt = datetime.fromisoformat(cursor)
            query = query.filter(SyncChange.created_at > cursor_dt)
        except Exception:
            pass

    records = query.order_by(SyncChange.created_at.asc()).limit(100).all()

    now_iso = datetime.now(timezone.utc).isoformat()
    next_cursor = records[-1].created_at.isoformat() if records else (cursor or now_iso)

    changes_list = []
    for r in records:
        try:
            p = json.loads(r.payload)
        except Exception:
            p = {}
        changes_list.append({
            "operation_id": r.id,
            "entity_type": r.entity_type,
            "entity_id": r.entity_id,
            "operation": r.operation,
            "payload": p,
            "revision": r.revision,
            "created_at": r.created_at.isoformat()
        })

    return SyncPullResponse(
        server_time=now_iso,
        next_cursor=next_cursor,
        changes=changes_list
    )
