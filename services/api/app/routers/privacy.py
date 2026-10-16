"""
StudyLock AI - Privacy, Data Export & Account Deletion Router
Ref: StudyLock AI Architecture Specification Section 16 & Section 13.2
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Dict, Any
from ..database import get_db
from ..models.models import (
    User,
    Task,
    Schedule,
    FocusSession,
    BlockRule,
    RewardLedger,
    Device,
    AuditEvent
)
from ..schemas.schemas import PrivacyExportResponse
from ..core.auth import get_current_user

router = APIRouter(prefix="/privacy", tags=["Privacy & Data Sovereignty"])


@router.post("/export", response_model=PrivacyExportResponse)
def export_user_data(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Exports full user account records in machine-readable JSON format (Spec Section 16.2).
    """
    tasks = db.query(Task).filter(Task.user_id == current_user.id).all()
    schedules = db.query(Schedule).filter(Schedule.user_id == current_user.id).all()
    sessions = db.query(FocusSession).filter(FocusSession.user_id == current_user.id).all()
    rules = db.query(BlockRule).filter(BlockRule.user_id == current_user.id).all()
    rewards = db.query(RewardLedger).filter(RewardLedger.user_id == current_user.id).all()

    # Record audit event
    audit = AuditEvent(
        user_id=current_user.id,
        action="DATA_EXPORT_REQUESTED",
        metadata_json='{"format": "json"}'
    )
    db.add(audit)
    db.commit()

    return PrivacyExportResponse(
        user={
            "id": current_user.id,
            "email": current_user.email,
            "display_name": current_user.display_name,
            "timezone": current_user.timezone,
            "created_at": current_user.created_at.isoformat()
        },
        tasks=[
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "subject": t.subject,
                "priority": t.priority,
                "status": t.status,
                "due_at": t.due_at.isoformat() if t.due_at else None
            }
            for t in tasks
        ],
        schedules=[
            {
                "id": s.id,
                "title": s.title,
                "start_minute": s.start_minute,
                "duration_minutes": s.duration_minutes,
                "timezone": s.timezone,
                "enabled": s.enabled
            }
            for s in schedules
        ],
        focus_sessions=[
            {
                "id": fs.id,
                "started_at": fs.started_at.isoformat(),
                "ended_at": fs.ended_at.isoformat() if fs.ended_at else None,
                "planned_minutes": fs.planned_minutes,
                "actual_seconds": fs.actual_seconds,
                "status": fs.status,
                "interruptions": fs.interruptions
            }
            for fs in sessions
        ],
        block_rules=[
            {
                "id": r.id,
                "target_type": r.target_type,
                "target_value": r.target_value,
                "action": r.action,
                "enabled": r.enabled
            }
            for r in rules
        ],
        reward_ledger=[
            {
                "id": rl.id,
                "event_key": rl.event_key,
                "xp_delta": rl.xp_delta,
                "reason": rl.reason,
                "created_at": rl.created_at.isoformat()
            }
            for rl in rewards
        ],
        exported_at=datetime.now(timezone.utc).isoformat()
    )


@router.post("/delete-account", status_code=status.HTTP_200_OK)
def delete_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Permanently deletes user account and cascades removal of all tasks,
    schedules, sessions, rules, and devices (Spec Section 16.2).
    """
    user_id = current_user.id
    db.delete(current_user)
    db.commit()

    return {
        "status": "deleted",
        "user_id": user_id,
        "message": "Account and all associated records have been permanently deleted.",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
