"""
StudyLock AI - Schedules Router & Smart Planner
Ref: StudyLock AI Architecture Specification Section 8 & Section 13.2
"""
import json
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime, timezone, timedelta
from ..database import get_db
from ..models.models import Schedule, Task, User
from ..schemas.schemas import ScheduleCreate, ScheduleUpdate, ScheduleResponse
from ..core.auth import get_current_user
from ..core.errors import NotFoundException, ForbiddenException, ConflictException

# Import domain smart planner from schemas package
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))
from packages.schemas.planner import SmartPlanner, TaskPlanningCandidate, ScheduleBlock
from packages.schemas.enums import Priority, TaskStatus

router = APIRouter(prefix="/schedules", tags=["Schedules"])


@router.get("", response_model=List[ScheduleResponse])
def list_schedules(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    schedules = db.query(Schedule).filter(Schedule.user_id == current_user.id).all()
    results = []
    for s in schedules:
        rec = {}
        try:
            rec = json.loads(s.recurrence) if s.recurrence else {}
        except Exception:
            rec = {}
        results.append(
            ScheduleResponse(
                id=s.id,
                user_id=s.user_id,
                title=s.title,
                timezone=s.timezone,
                start_minute=s.start_minute,
                duration_minutes=s.duration_minutes,
                recurrence=rec,
                enabled=s.enabled,
                revision=s.revision,
                created_at=s.created_at
            )
        )
    return results


@router.post("", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
def create_schedule(
    payload: ScheduleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    schedule = Schedule(
        user_id=current_user.id,
        title=payload.title,
        timezone=payload.timezone,
        start_minute=payload.start_minute,
        duration_minutes=payload.duration_minutes,
        recurrence=json.dumps(payload.recurrence or {}),
        enabled=payload.enabled,
        revision=1
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)

    return ScheduleResponse(
        id=schedule.id,
        user_id=schedule.user_id,
        title=schedule.title,
        timezone=schedule.timezone,
        start_minute=schedule.start_minute,
        duration_minutes=schedule.duration_minutes,
        recurrence=payload.recurrence or {},
        enabled=schedule.enabled,
        revision=schedule.revision,
        created_at=schedule.created_at
    )


@router.patch("/{schedule_id}", response_model=ScheduleResponse)
def update_schedule(
    schedule_id: str,
    payload: ScheduleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise NotFoundException("Schedule not found")
    if schedule.user_id != current_user.id:
        raise ForbiddenException()

    if payload.expected_revision is not None and schedule.revision != payload.expected_revision:
        raise ConflictException(f"Stale schedule edit: current revision is {schedule.revision}")

    if payload.title is not None:
        schedule.title = payload.title
    if payload.timezone is not None:
        schedule.timezone = payload.timezone
    if payload.start_minute is not None:
        schedule.start_minute = payload.start_minute
    if payload.duration_minutes is not None:
        schedule.duration_minutes = payload.duration_minutes
    if payload.recurrence is not None:
        schedule.recurrence = json.dumps(payload.recurrence)
    if payload.enabled is not None:
        schedule.enabled = payload.enabled

    schedule.revision += 1
    db.commit()
    db.refresh(schedule)

    rec = {}
    try:
        rec = json.loads(schedule.recurrence) if schedule.recurrence else {}
    except Exception:
        pass

    return ScheduleResponse(
        id=schedule.id,
        user_id=schedule.user_id,
        title=schedule.title,
        timezone=schedule.timezone,
        start_minute=schedule.start_minute,
        duration_minutes=schedule.duration_minutes,
        recurrence=rec,
        enabled=schedule.enabled,
        revision=schedule.revision,
        created_at=schedule.created_at
    )


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(
    schedule_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise NotFoundException("Schedule not found")
    if schedule.user_id != current_user.id:
        raise ForbiddenException()

    db.delete(schedule)
    db.commit()
    return None


@router.get("/suggested-plan")
def get_suggested_plan(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Ranks pending tasks according to Spec Section 8.4 planning heuristics:
    score = 0.35 * deadline_urgency + 0.30 * user_priority + 0.20 * goal_importance + 0.15 * readiness
    and detects any schedule overlap conflicts.
    """
    tasks = db.query(Task).filter(
        Task.user_id == current_user.id,
        Task.deleted_at.is_(None),
        Task.status.in_(["todo", "in_progress"])
    ).all()

    candidates = []
    for t in tasks:
        p_enum = Priority(t.priority) if t.priority in {1, 2, 3, 4} else Priority.MEDIUM
        status_enum = TaskStatus(t.status) if t.status in TaskStatus._value2member_map_ else TaskStatus.TODO
        candidates.append(
            TaskPlanningCandidate(
                id=t.id,
                title=t.title,
                priority=p_enum,
                estimated_minutes=t.estimated_minutes or 30,
                due_at=t.due_at,
                status=status_enum,
                goal_importance=75 if t.priority >= 3 else 50,
                readiness=100
            )
        )

    ranked_tasks = SmartPlanner.rank_tasks(candidates)

    # Check schedule conflicts
    schedules = db.query(Schedule).filter(Schedule.user_id == current_user.id, Schedule.enabled.is_(True)).all()
    now = datetime.now(timezone.utc)
    blocks = []
    for s in schedules:
        start_time = now.replace(hour=s.start_minute // 60, minute=s.start_minute % 60, second=0, microsecond=0)
        end_time = start_time + timedelta(minutes=s.duration_minutes)
        blocks.append(ScheduleBlock(id=s.id, title=s.title, start_time=start_time, end_time=end_time, is_user_pinned=True))

    conflicts = SmartPlanner.detect_conflicts(blocks)

    return {
        "ranked_tasks": ranked_tasks,
        "conflicts": conflicts,
        "server_time": now.isoformat()
    }
