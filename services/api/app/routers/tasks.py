"""
StudyLock AI - Tasks Router
Ref: StudyLock AI Architecture Specification Section 9 & Section 13.2
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from ..database import get_db
from ..models.models import Task, User, RewardLedger
from ..schemas.schemas import TaskCreate, TaskUpdate, TaskResponse
from ..core.auth import get_current_user
from ..core.errors import NotFoundException, ForbiddenException, ConflictException

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("", response_model=List[TaskResponse])
def list_tasks(
    status: Optional[str] = Query(None),
    subject: Optional[str] = Query(None),
    include_archived: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Task).filter(Task.user_id == current_user.id, Task.deleted_at.is_(None))
    if status:
        query = query.filter(Task.status == status)
    elif not include_archived:
        query = query.filter(Task.status != "archived")

    if subject:
        query = query.filter(Task.subject == subject)

    return query.order_by(Task.due_at.asc().nullslast(), Task.priority.desc()).all()


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = Task(
        user_id=current_user.id,
        title=payload.title,
        description=payload.description,
        subject=payload.subject,
        priority=payload.priority,
        estimated_minutes=payload.estimated_minutes,
        due_at=payload.due_at,
        status="todo",
        revision=1
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(Task.id == task_id, Task.deleted_at.is_(None)).first()
    if not task:
        raise NotFoundException("Task not found")
    if task.user_id != current_user.id:
        raise ForbiddenException()
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: str,
    payload: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(Task.id == task_id, Task.deleted_at.is_(None)).first()
    if not task:
        raise NotFoundException("Task not found")
    if task.user_id != current_user.id:
        raise ForbiddenException()

    # Optimistic concurrency check (Spec Section 12.3)
    if payload.expected_revision is not None and task.revision != payload.expected_revision:
        raise ConflictException(
            f"Task revision conflict: Current revision is {task.revision}, but update specified {payload.expected_revision}."
        )

    previous_status = task.status

    if payload.title is not None:
        task.title = payload.title
    if payload.description is not None:
        task.description = payload.description
    if payload.subject is not None:
        task.subject = payload.subject
    if payload.priority is not None:
        task.priority = payload.priority
    if payload.estimated_minutes is not None:
        task.estimated_minutes = payload.estimated_minutes
    if payload.due_at is not None:
        task.due_at = payload.due_at
    if payload.status is not None:
        task.status = payload.status

    task.revision += 1
    task.updated_at = datetime.now(timezone.utc)

    # If completed just now, award task completion XP idempotently (Spec Section 10)
    if previous_status != "done" and task.status == "done":
        event_key = f"EVT_TASK_COMPLETED:{task.id}"
        existing_reward = db.query(RewardLedger).filter(RewardLedger.event_key == event_key).first()
        if not existing_reward:
            ledger_entry = RewardLedger(
                user_id=current_user.id,
                session_id=None,
                event_key=event_key,
                xp_delta=20,
                reason=f"Completed task: {task.title}"
            )
            db.add(ledger_entry)

    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(Task.id == task_id, Task.deleted_at.is_(None)).first()
    if not task:
        raise NotFoundException("Task not found")
    if task.user_id != current_user.id:
        raise ForbiddenException()

    # Soft delete supports sync propagation via tombstones (Spec Section 12.3 & 14.3)
    task.deleted_at = datetime.now(timezone.utc)
    task.revision += 1
    db.commit()
    return None
