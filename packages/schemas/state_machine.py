"""
StudyLock AI - Focus Timer and Session State Machine
Ref: StudyLock AI Architecture Specification Section 7
"""
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from pydantic import BaseModel, Field

from .enums import SessionState, EnforcementState


# Valid state transitions defined in Spec Section 7.1
VALID_TRANSITIONS = {
    SessionState.PLANNED: {SessionState.STARTING, SessionState.CANCELLED},
    SessionState.STARTING: {SessionState.FOCUSING, SessionState.DEGRADED, SessionState.FAILED},
    SessionState.FOCUSING: {SessionState.PAUSED, SessionState.BREAK, SessionState.COMPLETED, SessionState.CANCELLED},
    SessionState.PAUSED: {SessionState.FOCUSING, SessionState.CANCELLED},
    SessionState.BREAK: {SessionState.FOCUSING, SessionState.COMPLETED, SessionState.CANCELLED},
    SessionState.DEGRADED: {SessionState.FOCUSING, SessionState.PAUSED, SessionState.COMPLETED, SessionState.CANCELLED},
    SessionState.COMPLETED: set(),  # Terminal
    SessionState.CANCELLED: set(),  # Terminal
    SessionState.FAILED: {SessionState.STARTING, SessionState.CANCELLED},
}


class StateTransitionRecord(BaseModel):
    from_state: SessionState
    to_state: SessionState
    timestamp: datetime
    reason: Optional[str] = None


class FocusSessionEngine(BaseModel):
    """
    Durable, deterministic Focus Session state engine.
    Ensures mathematical correctness of focus duration, pause accounting,
    and process-recovery from durable timestamps without relying on ticking counters.
    """
    session_id: str
    user_id: str
    planned_minutes: int = Field(ge=1, le=240)
    current_state: SessionState = SessionState.PLANNED
    enforcement_state: EnforcementState = EnforcementState.NOT_CONFIGURED
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    expected_end_at: Optional[datetime] = None
    last_pause_started_at: Optional[datetime] = None
    cumulative_paused_seconds: int = 0
    interruptions: int = 0
    transitions: List[StateTransitionRecord] = Field(default_factory=list)
    revision: int = 1

    def transition_to(
        self,
        new_state: SessionState,
        at_time: Optional[datetime] = None,
        reason: Optional[str] = None,
        enforcement_state: Optional[EnforcementState] = None
    ) -> bool:
        """
        Executes a validated state transition.
        """
        if at_time is None:
            at_time = datetime.now(timezone.utc)

        allowed = VALID_TRANSITIONS.get(self.current_state, set())
        if new_state not in allowed:
            raise ValueError(
                f"Invalid state transition: Cannot transition from {self.current_state} to {new_state}."
            )

        # Transition specifics
        old_state = self.current_state

        if new_state == SessionState.STARTING:
            pass

        elif new_state in {SessionState.FOCUSING, SessionState.DEGRADED}:
            if self.started_at is None:
                self.started_at = at_time
                self.expected_end_at = datetime.fromtimestamp(
                    at_time.timestamp() + (self.planned_minutes * 60),
                    tz=timezone.utc
                )
            # If resuming from PAUSED or BREAK, record paused duration
            if old_state in {SessionState.PAUSED, SessionState.BREAK} and self.last_pause_started_at:
                delta = int((at_time - self.last_pause_started_at).total_seconds())
                if delta > 0:
                    self.cumulative_paused_seconds += delta
                self.last_pause_started_at = None

        elif new_state in {SessionState.PAUSED, SessionState.BREAK}:
            self.last_pause_started_at = at_time
            self.interruptions += 1

        elif new_state in {SessionState.COMPLETED, SessionState.CANCELLED}:
            self.ended_at = at_time
            if old_state in {SessionState.PAUSED, SessionState.BREAK} and self.last_pause_started_at:
                delta = int((at_time - self.last_pause_started_at).total_seconds())
                if delta > 0:
                    self.cumulative_paused_seconds += delta
                self.last_pause_started_at = None

        if enforcement_state is not None:
            self.enforcement_state = enforcement_state

        self.current_state = new_state
        self.revision += 1
        self.transitions.append(
            StateTransitionRecord(
                from_state=old_state,
                to_state=new_state,
                timestamp=at_time,
                reason=reason
            )
        )
        return True

    def calculate_actual_focus_seconds(self, at_time: Optional[datetime] = None) -> int:
        """
        Calculates validated elapsed focus seconds strictly excluding pauses.
        Independent of system timer ticks; robust to process restarts.
        """
        if not self.started_at:
            return 0

        if at_time is None:
            at_time = datetime.now(timezone.utc)

        # Determine upper boundary
        end_boundary = self.ended_at if self.ended_at else at_time

        # If currently paused, pause time until current time must be excluded
        current_active_pause = 0
        if self.current_state in {SessionState.PAUSED, SessionState.BREAK} and self.last_pause_started_at:
            current_active_pause = max(0, int((at_time - self.last_pause_started_at).total_seconds()))

        total_wall_seconds = max(0, int((end_boundary - self.started_at).total_seconds()))
        net_focus_seconds = total_wall_seconds - self.cumulative_paused_seconds - current_active_pause
        return max(0, net_focus_seconds)

    def is_eligible_for_reward(self, min_ratio: float = 0.8) -> Tuple[bool, str]:
        """
        Validates if session qualifies for XP rewards.
        - Must be in COMPLETED state.
        - Net focus time must meet at least `min_ratio` (default 80%) of planned minutes.
        """
        if self.current_state != SessionState.COMPLETED:
            return False, f"Session is in {self.current_state} state, not COMPLETED"

        focus_seconds = self.calculate_actual_focus_seconds()
        required_seconds = int(self.planned_minutes * 60 * min_ratio)

        if focus_seconds < required_seconds:
            return False, f"Actual focus time ({focus_seconds}s) is below required {required_seconds}s ({int(min_ratio*100)}%)"

        return True, "Eligible"
