"""
StudyLock AI - Unit Tests: Rewards Engine & Ledger Integrity
Ref: StudyLock AI Architecture Specification Section 10
"""
import pytest
from datetime import date
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from packages.schemas.rewards import RewardEngine, MAX_XP_PER_SESSION


def test_session_reward_standard():
    # 25-minute completed session
    res = RewardEngine.calculate_session_reward(planned_minutes=25, actual_seconds=25 * 60)
    assert res["xp_delta"] == 25
    assert "Focus session completed" in res["reason"]


def test_session_reward_deep_45m():
    # 50-minute completed session (>= 45m deep focus)
    res = RewardEngine.calculate_session_reward(planned_minutes=50, actual_seconds=50 * 60)
    assert res["xp_delta"] == 40
    assert "45+" in res["reason"]


def test_reward_bounded_cap():
    # Attempting to mint unlimited XP from a 500-minute session
    res = RewardEngine.calculate_session_reward(planned_minutes=500, actual_seconds=500 * 60)
    assert res["xp_delta"] <= MAX_XP_PER_SESSION


def test_deterministic_idempotency_keys():
    # Re-running key generation for the same session ID yields identical keys
    key1 = RewardEngine.generate_session_event_key("session-abc", "EVT_SESSION_COMPLETED")
    key2 = RewardEngine.generate_session_event_key("session-abc", "EVT_SESSION_COMPLETED")
    assert key1 == key2
    assert key1 == "EVT_SESSION_COMPLETED:session-abc"

    daily_key = RewardEngine.generate_daily_goal_key("user-1", date(2026, 10, 16))
    assert daily_key == "EVT_DAILY_GOAL:user-1:2026-10-16"


def test_level_progression_calculation():
    # Level 1 starts at 0 XP
    l0 = RewardEngine.calculate_level(0)
    assert l0["current_level"] == 1

    # Level 1 requires 100 XP
    l1 = RewardEngine.calculate_level(150)
    # 150 XP: Level 1 completed (100 XP), Level 2 has 50 XP remaining (needs 200 XP)
    assert l1["current_level"] == 2
    assert l1["current_level_xp"] == 50
