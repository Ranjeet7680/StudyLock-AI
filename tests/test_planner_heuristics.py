"""
StudyLock AI - Unit Tests: Planning Heuristics & Conflict Engine
Ref: StudyLock AI Architecture Specification Section 8 & Section 9
"""
import pytest
from datetime import datetime, timezone, timedelta
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from packages.schemas.enums import Priority, TaskStatus
from packages.schemas.planner import SmartPlanner, TaskPlanningCandidate, ScheduleBlock


def test_deadline_urgency_decay():
    now = datetime(2026, 10, 16, 12, 0, 0, tzinfo=timezone.utc)

    # Due in 1 hour -> 100
    u1 = SmartPlanner.calculate_deadline_urgency(now + timedelta(hours=1), now)
    assert u1 == 100.0

    # Due in 10 hours -> between 80 and 100
    u2 = SmartPlanner.calculate_deadline_urgency(now + timedelta(hours=10), now)
    assert 80.0 <= u2 <= 100.0

    # Due in 48 hours -> between 50 and 80
    u3 = SmartPlanner.calculate_deadline_urgency(now + timedelta(hours=48), now)
    assert 50.0 <= u3 <= 80.0

    # No deadline -> 10.0
    u4 = SmartPlanner.calculate_deadline_urgency(None, now)
    assert u4 == 10.0


def test_task_scoring_formula():
    now = datetime(2026, 10, 16, 12, 0, 0, tzinfo=timezone.utc)
    task = TaskPlanningCandidate(
        id="t-test",
        title="Physics Midterm Revision",
        priority=Priority.CRITICAL,  # 100.0
        estimated_minutes=60,
        due_at=now + timedelta(hours=1),  # urgency 100.0
        goal_importance=100,  # 100.0
        readiness=100  # 100.0
    )
    result = SmartPlanner.score_task(task, now)
    # Expected: 0.35*100 + 0.30*100 + 0.20*100 + 0.15*100 = 100.0
    assert result["score"] == 100.0
    assert "Approaching deadline" in result["explanation"]


def test_ranking_pinned_takes_precedence():
    now = datetime(2026, 10, 16, 12, 0, 0, tzinfo=timezone.utc)
    t1 = TaskPlanningCandidate(id="1", title="Low Urgent", priority=Priority.LOW, readiness=50)
    t2 = TaskPlanningCandidate(id="2", title="High Pinned", priority=Priority.MEDIUM, is_pinned=True)

    ranked = SmartPlanner.rank_tasks([t1, t2], now)
    assert ranked[0]["task_id"] == "2"  # Pinned is ranked first


def test_schedule_conflict_detection():
    now = datetime(2026, 10, 16, 14, 0, 0, tzinfo=timezone.utc)
    block_a = ScheduleBlock(
        id="b1",
        title="Math Class",
        start_time=now,
        end_time=now + timedelta(minutes=60),
        is_user_pinned=True
    )
    block_b = ScheduleBlock(
        id="b2",
        title="Auto Suggested Study Block",
        start_time=now + timedelta(minutes=30),  # Overlaps!
        end_time=now + timedelta(minutes=90),
        is_user_pinned=False
    )

    conflicts = SmartPlanner.detect_conflicts([block_a, block_b])
    assert len(conflicts) == 1
    assert conflicts[0]["priority_block"] == "b1"  # Pinned block prioritized
    assert "Shift block" in conflicts[0]["recommended_action"]
