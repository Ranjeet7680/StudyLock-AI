"""
StudyLock AI - Focus Sessions Router & State Machine API
Ref: StudyLock AI Architecture Specification Section 7, 10, 13.2, 13.3
"""
import json
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.models import FocusSession, Task, RewardLedger, User
from ..schemas.schemas import (
    StartSessionRequest,
    StartSessionResponse,
    PauseSessionRequest,
    FinishSessionRequest,
    FinishSessionResponse,
    FocusSessionResponse
)
from ..core.auth import get_current_user
from ..core.errors import NotFoundException, ForbiddenException, StudyLockException
from ..core.idempotency import check_idempotency_key, record_idempotency_key

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))
from packages.schemas.state_machine import FocusSessionEngine
from packages.schemas.enums import SessionState, EnforcementState
from packages.schemas.rewards import RewardEngine, RewardEventDef

router = APIRouter(prefix="/sessions", tags=["Focus Sessions"])


@router.get("/active")
def get_active_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(FocusSession).filter(
        FocusSession.user_id == current_user.id,
        FocusSession.status.in_(["STARTING", "FOCUSING", "PAUSED", "BREAK", "DEGRADED"])
    ).first()
    if not session:
        return {"active": False, "session": None}
    return {
        "active": True,
        "session": {
            "session_id": session.id,
            "status": session.status,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "planned_minutes": session.planned_minutes,
            "actual_seconds": session.actual_seconds,
            "paused_seconds": session.paused_seconds,
            "interruptions": session.interruptions,
            "enforcement_state": session.enforcement_state,
            "task_id": session.task_id
        }
    }


@router.post("/start", response_model=StartSessionResponse, status_code=status.HTTP_201_CREATED)
def start_session(
    payload: StartSessionRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check idempotency
    cached = check_idempotency_key(idempotency_key)
    if cached:
        return StartSessionResponse(**cached)

    # Check if there is already an active session
    active_existing = db.query(FocusSession).filter(
        FocusSession.user_id == current_user.id,
        FocusSession.status.in_(["STARTING", "FOCUSING", "PAUSED", "BREAK", "DEGRADED"])
    ).first()

    if active_existing:
        raise StudyLockException(
            status_code=409,
            code="ACTIVE_SESSION_EXISTS",
            message="An active focus session is already in progress. Finish or cancel it before starting a new one."
        )

    # Validate task ownership if specified
    if payload.task_id:
        task = db.query(Task).filter(Task.id == payload.task_id, Task.user_id == current_user.id).first()
        if not task:
            raise NotFoundException("Specified task not found or belongs to another user")

    now = datetime.now(timezone.utc)
    expected_end = now + timedelta(minutes=payload.planned_minutes)

    session = FocusSession(
        user_id=current_user.id,
        task_id=payload.task_id,
        device_id=payload.device_id,
        started_at=now,
        planned_minutes=payload.planned_minutes,
        actual_seconds=0,
        paused_seconds=0,
        status="FOCUSING",
        enforcement_state="ACTIVE",
        interruptions=0,
        state_history=json.dumps([{
            "from_state": "PLANNED",
            "to_state": "FOCUSING",
            "timestamp": now.isoformat(),
            "reason": "Session started"
        }])
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    resp_data = {
        "session_id": session.id,
        "status": session.status,
        "started_at": session.started_at.isoformat(),
        "expected_end_at": expected_end.isoformat(),
        "enforcement_state": session.enforcement_state,
        "planned_minutes": session.planned_minutes
    }

    if idempotency_key:
        record_idempotency_key(idempotency_key, resp_data)

    return StartSessionResponse(**resp_data)


@router.post("/{session_id}/pause")
def pause_session(
    session_id: str,
    payload: PauseSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(FocusSession).filter(FocusSession.id == session_id).first()
    if not session:
        raise NotFoundException("Focus session not found")
    if session.user_id != current_user.id:
        raise ForbiddenException()

    if session.status not in ["FOCUSING", "DEGRADED"]:
        raise StudyLockException(
            status_code=400,
            code="INVALID_STATE_TRANSITION",
            message=f"Cannot pause a session that is in '{session.status}' state."
        )

    now = datetime.now(timezone.utc)
    history = json.loads(session.state_history or "[]")
    history.append({
        "from_state": session.status,
        "to_state": "PAUSED",
        "timestamp": now.isoformat(),
        "reason": payload.reason
    })

    session.status = "PAUSED"
    session.interruptions += 1
    session.state_history = json.dumps(history)
    db.commit()
    db.refresh(session)

    return {"session_id": session.id, "status": session.status, "interruptions": session.interruptions}


@router.post("/{session_id}/resume")
def resume_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(FocusSession).filter(FocusSession.id == session_id).first()
    if not session:
        raise NotFoundException("Focus session not found")
    if session.user_id != current_user.id:
        raise ForbiddenException()

    if session.status not in ["PAUSED", "BREAK"]:
        raise StudyLockException(
            status_code=400,
            code="INVALID_STATE_TRANSITION",
            message=f"Cannot resume a session that is in '{session.status}' state."
        )

    now = datetime.now(timezone.utc)
    history = json.loads(session.state_history or "[]")
    
    # Calculate how long the pause was
    last_pause_ts = None
    for entry in reversed(history):
        if entry.get("to_state") in ["PAUSED", "BREAK"]:
            last_pause_ts = datetime.fromisoformat(entry["timestamp"])
            break

    if last_pause_ts:
        if last_pause_ts.tzinfo is None:
            last_pause_ts = last_pause_ts.replace(tzinfo=timezone.utc)
        pause_delta = int((now - last_pause_ts).total_seconds())
        if pause_delta > 0:
            session.paused_seconds += pause_delta

    history.append({
        "from_state": session.status,
        "to_state": "FOCUSING",
        "timestamp": now.isoformat(),
        "reason": "User resumed session"
    })

    session.status = "FOCUSING"
    session.state_history = json.dumps(history)
    db.commit()
    db.refresh(session)

    return {"session_id": session.id, "status": session.status, "paused_seconds": session.paused_seconds}


@router.post("/{session_id}/finish", response_model=FinishSessionResponse)
@router.post("/{session_id}/complete", response_model=FinishSessionResponse)
def finish_session(
    session_id: str,
    payload: FinishSessionRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submits session completion for transactional reward validation (Spec Section 10.1).
    Ensures mathematical correctness of focus duration and immutable XP ledgering.
    """
    cached = check_idempotency_key(idempotency_key)
    if cached:
        return FinishSessionResponse(**cached)

    session = db.query(FocusSession).filter(FocusSession.id == session_id).first()
    if not session:
        raise NotFoundException("Focus session not found")
    if session.user_id != current_user.id:
        raise ForbiddenException()

    if session.status in ["COMPLETED", "CANCELLED"]:
        raise StudyLockException(
            status_code=400,
            code="SESSION_ALREADY_TERMINATED",
            message=f"Session is already {session.status}."
        )

    now = datetime.now(timezone.utc)
    session.ended_at = now

    if session.status in ["PAUSED", "BREAK"]:
        history = json.loads(session.state_history or "[]")
        for entry in reversed(history):
            if entry.get("to_state") in ["PAUSED", "BREAK"]:
                p_ts = datetime.fromisoformat(entry["timestamp"])
                if p_ts.tzinfo is None:
                    p_ts = p_ts.replace(tzinfo=timezone.utc)
                session.paused_seconds += max(0, int((now - p_ts).total_seconds()))
                break

    # Calculate actual net focus duration strictly excluding pauses
    started_at = session.started_at
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)
    total_elapsed = int((now - started_at).total_seconds())
    net_focus_seconds = max(0, total_elapsed - session.paused_seconds)
    session.actual_seconds = net_focus_seconds
    session.status = "COMPLETED"

    if payload.interruption_count:
        session.interruptions = max(session.interruptions, payload.interruption_count)

    history = json.loads(session.state_history or "[]")
    history.append({
        "from_state": "FOCUSING",
        "to_state": "COMPLETED",
        "timestamp": now.isoformat(),
        "reason": "Session successfully completed"
    })
    session.state_history = json.dumps(history)

    # Reward calculation and transactional ledger insertion (Spec Section 10.1)
    reward_calc = RewardEngine.calculate_session_reward(session.planned_minutes, net_focus_seconds)
    xp_awarded = reward_calc["xp_delta"]
    reward_reason = reward_calc["reason"]

    event_key = RewardEngine.generate_session_event_key(session.id, reward_calc["prefix"])
    
    # Check if already rewarded (idempotency safety)
    existing_entry = db.query(RewardLedger).filter(RewardLedger.event_key == event_key).first()
    if not existing_entry and xp_awarded > 0:
        ledger_entry = RewardLedger(
            user_id=current_user.id,
            session_id=session.id,
            event_key=event_key,
            xp_delta=xp_awarded,
            reason=reward_reason
        )
        db.add(ledger_entry)

    # Check first session bonus
    first_session_key = f"EVT_FIRST_SESSION:{current_user.id}"
    has_first = db.query(RewardLedger).filter(RewardLedger.event_key == first_session_key).first()
    if not has_first:
        first_entry = RewardLedger(
            user_id=current_user.id,
            session_id=session.id,
            event_key=first_session_key,
            xp_delta=25,
            reason="First valid focus session milestone"
        )
        db.add(first_entry)
        xp_awarded += 25

    db.commit()

    # Query current total XP
    all_rewards = db.query(RewardLedger).filter(RewardLedger.user_id == current_user.id).all()
    total_xp = sum(r.xp_delta for r in all_rewards)
    level_info = RewardEngine.calculate_level(total_xp)

    resp_data = {
        "session_id": session.id,
        "status": session.status,
        "planned_minutes": session.planned_minutes,
        "actual_seconds": net_focus_seconds,
        "actual_minutes": net_focus_seconds // 60,
        "xp_awarded": xp_awarded,
        "reward_reason": reward_reason,
        "current_level": level_info["current_level"],
        "total_xp": total_xp
    }

    if idempotency_key:
        record_idempotency_key(idempotency_key, resp_data)

    return FinishSessionResponse(**resp_data)


@router.post("/{session_id}/cancel")
def cancel_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Emergency exit or user cancellation. Record neutral interruption reason (Spec Section 7.4).
    """
    session = db.query(FocusSession).filter(FocusSession.id == session_id).first()
    if not session:
        raise NotFoundException("Focus session not found")
    if session.user_id != current_user.id:
        raise ForbiddenException()

    now = datetime.now(timezone.utc)
    session.ended_at = now
    session.status = "CANCELLED"
    history = json.loads(session.state_history or "[]")
    history.append({
        "from_state": session.status,
        "to_state": "CANCELLED",
        "timestamp": now.isoformat(),
        "reason": "Session exited early via emergency exit"
    })
    session.state_history = json.dumps(history)
    db.commit()

    return {"session_id": session.id, "status": "CANCELLED", "message": "Session exited safely."}


@router.get("", response_model=List[FocusSessionResponse])
def list_sessions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(FocusSession).filter(
        FocusSession.user_id == current_user.id
    ).order_by(FocusSession.started_at.desc()).limit(50).all()
