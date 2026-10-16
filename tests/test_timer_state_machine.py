"""
StudyLock AI - Unit Tests: Focus Timer State Machine & Correctness
Ref: StudyLock AI Architecture Specification Section 7 & Section 18
"""
import pytest
from datetime import datetime, timezone, timedelta
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from packages.schemas.enums import SessionState, EnforcementState
from packages.schemas.state_machine import FocusSessionEngine


def test_initial_state():
    engine = FocusSessionEngine(
        session_id="sess-001",
        user_id="user-001",
        planned_minutes=25
    )
    assert engine.current_state == SessionState.PLANNED
    assert engine.started_at is None
    assert engine.calculate_actual_focus_seconds() == 0


def test_valid_lifecycle_transitions():
    engine = FocusSessionEngine(
        session_id="sess-002",
        user_id="user-001",
        planned_minutes=25
    )
    t0 = datetime(2026, 10, 16, 9, 0, 0, tzinfo=timezone.utc)
    
    # PLANNED -> STARTING
    assert engine.transition_to(SessionState.STARTING, at_time=t0)
    assert engine.current_state == SessionState.STARTING

    # STARTING -> FOCUSING
    t1 = t0 + timedelta(seconds=2)
    assert engine.transition_to(SessionState.FOCUSING, at_time=t1, enforcement_state=EnforcementState.ACTIVE)
    assert engine.current_state == SessionState.FOCUSING
    assert engine.started_at == t1
    assert engine.expected_end_at == t1 + timedelta(minutes=25)

    # FOCUSING -> PAUSED (Pause for 5 minutes)
    t2 = t1 + timedelta(minutes=10)
    assert engine.transition_to(SessionState.PAUSED, at_time=t2, reason="Short stretch")
    assert engine.current_state == SessionState.PAUSED
    assert engine.interruptions == 1

    # PAUSED -> FOCUSING (Resume)
    t3 = t2 + timedelta(minutes=5)
    assert engine.transition_to(SessionState.FOCUSING, at_time=t3)
    assert engine.current_state == SessionState.FOCUSING
    assert engine.cumulative_paused_seconds == 300  # 5 minutes paused

    # FOCUSING -> COMPLETED (Finish after 20 more minutes)
    t4 = t3 + timedelta(minutes=15)
    assert engine.transition_to(SessionState.COMPLETED, at_time=t4)
    assert engine.current_state == SessionState.COMPLETED
    assert engine.ended_at == t4

    # Net focus time:
    # Wall clock: t1 (09:00:02) to t4 (09:30:02) = 30 minutes = 1800 seconds
    # Paused: 300 seconds (5 minutes)
    # Net: 1800 - 300 = 1500 seconds (25 minutes)
    actual_seconds = engine.calculate_actual_focus_seconds(at_time=t4)
    assert actual_seconds == 1500
    assert actual_seconds == 25 * 60

    # Eligible for reward check (planned 25m, actual 25m = 100% >= 80%)
    eligible, reason = engine.is_eligible_for_reward(min_ratio=0.8)
    assert eligible is True


def test_invalid_transition_raises_error():
    engine = FocusSessionEngine(
        session_id="sess-003",
        user_id="user-001",
        planned_minutes=25
    )
    # Cannot jump directly from PLANNED to COMPLETED
    with pytest.raises(ValueError, match="Invalid state transition"):
        engine.transition_to(SessionState.COMPLETED)


def test_emergency_exit_and_cancellation():
    engine = FocusSessionEngine(
        session_id="sess-004",
        user_id="user-001",
        planned_minutes=45
    )
    t0 = datetime(2026, 10, 16, 10, 0, 0, tzinfo=timezone.utc)
    engine.transition_to(SessionState.STARTING, at_time=t0)
    engine.transition_to(SessionState.FOCUSING, at_time=t0)

    # Cancel after 5 minutes via emergency exit
    t1 = t0 + timedelta(minutes=5)
    engine.transition_to(SessionState.CANCELLED, at_time=t1, reason="Emergency exit early")
    assert engine.current_state == SessionState.CANCELLED
    
    # Ineligible for reward because session was cancelled
    eligible, reason = engine.is_eligible_for_reward()
    assert eligible is False
    assert "CANCELLED" in reason
