"""
StudyLock AI - Rewards, Streaks & Cryptographic Event Ledger
Ref: StudyLock AI Architecture Specification Section 10
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, date
from pydantic import BaseModel, Field


class RewardEventDef:
    FIRST_SESSION = {"key_prefix": "EVT_FIRST_SESSION", "xp": 25, "reason": "First valid focus session completed"}
    STANDARD_SESSION = {"key_prefix": "EVT_SESSION_COMPLETED", "xp": 25, "reason": "Focus session completed"}
    LONG_SESSION_45M = {"key_prefix": "EVT_SESSION_45M", "xp": 40, "reason": "Deep focus 45+ minute session completed"}
    DAILY_GOAL_REACHED = {"key_prefix": "EVT_DAILY_GOAL", "xp": 50, "reason": "Daily study goal achieved"}
    THREE_DAY_STREAK = {"key_prefix": "EVT_STREAK_3DAY", "xp": 75, "reason": "Three consecutive days study streak"}
    WEEKLY_GOAL_REACHED = {"key_prefix": "EVT_WEEKLY_GOAL", "xp": 150, "reason": "Weekly focus milestone reached"}
    TASK_COMPLETED = {"key_prefix": "EVT_TASK_COMPLETED", "xp": 20, "reason": "Task goal achieved"}


# Bounded maximum XP per single session to prevent gaming / reward manipulation (Section 10.2 & 22)
MAX_XP_PER_SESSION = 100
MAX_XP_PER_DAY = 500


class RewardLedgerEntry(BaseModel):
    id: str
    user_id: str
    session_id: Optional[str] = None
    event_key: str
    xp_delta: int
    reason: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RewardEngine:
    """
    Reward calculation and event_key generation engine.
    Ensures idempotency through deterministic event keys.
    """

    @staticmethod
    def generate_session_event_key(session_id: str, event_type: str) -> str:
        """
        Unique deterministic key per session event.
        Guarantees that re-submitting the same session completion will violate
        the UNIQUE constraint on reward_ledger.event_key.
        """
        return f"{event_type}:{session_id}"

    @staticmethod
    def generate_daily_goal_key(user_id: str, day_date: date) -> str:
        """
        Unique key per day for daily goal achievement.
        """
        return f"{RewardEventDef.DAILY_GOAL_REACHED['key_prefix']}:{user_id}:{day_date.isoformat()}"

    @staticmethod
    def generate_task_completion_key(task_id: str) -> str:
        return f"{RewardEventDef.TASK_COMPLETED['key_prefix']}:{task_id}"

    @classmethod
    def calculate_session_reward(cls, planned_minutes: int, actual_seconds: int) -> Dict[str, Any]:
        """
        Calculates eligible XP for a completed session.
        Applies bounds and thresholds defined in Spec Section 10.
        """
        actual_minutes = actual_seconds // 60

        if actual_minutes >= 45:
            base_xp = RewardEventDef.LONG_SESSION_45M["xp"]
            reason = RewardEventDef.LONG_SESSION_45M["reason"]
            prefix = RewardEventDef.LONG_SESSION_45M["key_prefix"]
        else:
            base_xp = RewardEventDef.STANDARD_SESSION["xp"]
            reason = RewardEventDef.STANDARD_SESSION["reason"]
            prefix = RewardEventDef.STANDARD_SESSION["key_prefix"]

        # Ensure XP doesn't exceed cap
        capped_xp = min(base_xp, MAX_XP_PER_SESSION)

        return {
            "xp_delta": capped_xp,
            "reason": reason,
            "prefix": prefix,
            "actual_minutes": actual_minutes
        }

    @staticmethod
    def calculate_level(total_xp: int) -> Dict[str, Any]:
        """
        Calculates user level based on total XP using gentle progression:
        Level N requires 100 * N XP.
        """
        level = 1
        xp_remaining = total_xp
        required_for_next = 100

        while xp_remaining >= required_for_next:
            xp_remaining -= required_for_next
            level += 1
            required_for_next = level * 100

        progress_pct = int((xp_remaining / required_for_next) * 100) if required_for_next > 0 else 0

        return {
            "current_level": level,
            "total_xp": total_xp,
            "current_level_xp": xp_remaining,
            "next_level_required_xp": required_for_next,
            "level_progress_percent": progress_pct
        }
