"""
StudyLock AI - Analytics & Metrics Reporting Router
Ref: StudyLock AI Architecture Specification Section 11 & Section 13.2
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from ..database import get_db
from ..models.models import FocusSession, Task, Schedule, Device, User
from ..core.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/weekly")
def get_weekly_analytics(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Returns weekly focus metrics conforming to Spec Section 11.1 & 11.2:
    - Planned vs actual focus minutes
    - Completed vs cancelled sessions
    - Study time by subject
    - Tasks completed on time & overdue count
    - Interruption count
    """
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    # Focus sessions in past 7 days
    sessions = db.query(FocusSession).filter(
        FocusSession.user_id == current_user.id,
        FocusSession.started_at >= week_ago
    ).all()

    planned_minutes = sum(s.planned_minutes for s in sessions)
    actual_seconds = sum(s.actual_seconds for s in sessions if s.status == "COMPLETED")
    actual_minutes = actual_seconds // 60

    completed_sessions = [s for s in sessions if s.status == "COMPLETED"]
    cancelled_sessions = [s for s in sessions if s.status == "CANCELLED"]

    total_started = len(sessions)
    completion_rate = round((len(completed_sessions) / total_started * 100), 1) if total_started > 0 else 0.0
    total_interruptions = sum(s.interruptions for s in sessions)

    # Subject breakdown
    subject_map: Dict[str, int] = {}
    for s in completed_sessions:
        if s.task_id:
            task = db.query(Task).filter(Task.id == s.task_id).first()
            subject_name = task.subject if task and task.subject else "General Study"
        else:
            subject_name = "Self-Directed"
        subject_map[subject_name] = subject_map.get(subject_name, 0) + (s.actual_seconds // 60)

    # Task metrics
    all_tasks = db.query(Task).filter(
        Task.user_id == current_user.id,
        Task.deleted_at.is_(None)
    ).all()
    tasks_done = [t for t in all_tasks if t.status == "done"]
    tasks_overdue = [
        t for t in all_tasks
        if t.due_at and (t.due_at.replace(tzinfo=timezone.utc) if t.due_at.tzinfo is None else t.due_at) < now and t.status != "done"
    ]

    # Daily distribution (past 7 days)
    daily_stats: List[Dict[str, Any]] = []
    for day_idx in range(6, -1, -1):
        target_day = (now - timedelta(days=day_idx)).date()
        day_sessions = [
            s for s in completed_sessions
            if s.started_at.date() == target_day
        ]
        day_minutes = sum(s.actual_seconds for s in day_sessions) // 60
        daily_stats.append({
            "date": target_day.isoformat(),
            "day_name": target_day.strftime("%a"),
            "focus_minutes": day_minutes,
            "sessions_count": len(day_sessions)
        })

    return {
        "period": "past_7_days",
        "planned_minutes": planned_minutes,
        "actual_minutes": actual_minutes,
        "completed_sessions": len(completed_sessions),
        "cancelled_sessions": len(cancelled_sessions),
        "completion_rate_percent": completion_rate,
        "total_interruptions": total_interruptions,
        "subject_distribution": subject_map,
        "tasks_completed_count": len(tasks_done),
        "tasks_overdue_count": len(tasks_overdue),
        "daily_focus_trend": daily_stats
    }


@router.get("/dashboard")
def get_dashboard_summary(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Returns home dashboard summary (Spec Section 4.2 Home dashboard).
    """
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    today_sessions = db.query(FocusSession).filter(
        FocusSession.user_id == current_user.id,
        FocusSession.started_at >= today_start,
        FocusSession.status == "COMPLETED"
    ).all()

    today_focus_minutes = sum(s.actual_seconds for s in today_sessions) // 60
    daily_goal_minutes = 120  # default 2-hour daily goal

    # Pending priority tasks
    pending_tasks = db.query(Task).filter(
        Task.user_id == current_user.id,
        Task.deleted_at.is_(None),
        Task.status.in_(["todo", "in_progress"])
    ).order_by(Task.priority.desc(), Task.due_at.asc().nullslast()).limit(5).all()

    # Active schedules
    upcoming_schedules = db.query(Schedule).filter(
        Schedule.user_id == current_user.id,
        Schedule.enabled.is_(True)
    ).all()

    # Active connected devices
    devices = db.query(Device).filter(Device.user_id == current_user.id).all()

    return {
        "today_focus_minutes": today_focus_minutes,
        "daily_goal_minutes": daily_goal_minutes,
        "daily_goal_progress_percent": min(100, int((today_focus_minutes / daily_goal_minutes) * 100)),
        "streak_days": 3 if today_focus_minutes > 0 else 2,  # sample streak calculation
        "pending_tasks_count": len(pending_tasks),
        "pending_tasks": [
            {
                "id": t.id,
                "title": t.title,
                "priority": t.priority,
                "subject": t.subject,
                "due_at": t.due_at.isoformat() if t.due_at else None
            }
            for t in pending_tasks
        ],
        "active_devices_count": len(devices),
        "upcoming_schedules_count": len(upcoming_schedules)
    }
