"""
StudyLock AI - Planning Heuristics, Scoring & Calendar Engine
Ref: StudyLock AI Architecture Specification Section 8 & Section 9
"""
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from .enums import Priority, TaskStatus


class TaskPlanningCandidate(BaseModel):
    id: str
    title: str
    priority: Priority = Priority.MEDIUM
    estimated_minutes: int = 30
    due_at: Optional[datetime] = None
    status: TaskStatus = TaskStatus.TODO
    goal_importance: int = Field(default=50, ge=0, le=100)
    readiness: int = Field(default=100, ge=0, le=100)
    is_pinned: bool = False


class ScheduleBlock(BaseModel):
    id: str
    title: str
    start_time: datetime
    end_time: datetime
    is_user_pinned: bool = True
    task_id: Optional[str] = None


class SmartPlanner:
    """
    Implements deterministic planning score algorithm and conflict resolution.
    Score = 0.35 * deadline_urgency + 0.30 * user_priority + 0.20 * goal_importance + 0.15 * readiness
    """

    @staticmethod
    def calculate_deadline_urgency(due_at: Optional[datetime], now: Optional[datetime] = None) -> float:
        """
        Normalizes deadline urgency to 0..100 scale:
        - Overdue or due within 2 hours: 100
        - Due within 24 hours: 80 - 100
        - Due within 3 days: 50 - 80
        - Due within 7 days: 20 - 50
        - Due later or no deadline: 0 - 20
        """
        if not due_at:
            return 10.0

        if now is None:
            now = datetime.now(timezone.utc)

        diff_hours = (due_at - now).total_seconds() / 3600.0

        if diff_hours <= 2:
            return 100.0
        elif diff_hours <= 24:
            # Linear decay from 100 to 80
            return 80.0 + (1.0 - (diff_hours - 2) / 22.0) * 20.0
        elif diff_hours <= 72:
            # Linear decay from 80 to 50
            return 50.0 + (1.0 - (diff_hours - 24) / 48.0) * 30.0
        elif diff_hours <= 168:
            # Linear decay from 50 to 20
            return 20.0 + (1.0 - (diff_hours - 72) / 96.0) * 30.0
        else:
            return max(5.0, 20.0 - (diff_hours - 168) / 100.0)

    @staticmethod
    def calculate_priority_score(priority: Priority) -> float:
        """
        Normalizes Priority enum (1..4) to 0..100 scale:
        LOW (1) -> 25
        MEDIUM (2) -> 50
        HIGH (3) -> 75
        CRITICAL (4) -> 100
        """
        mapping = {
            Priority.LOW: 25.0,
            Priority.MEDIUM: 50.0,
            Priority.HIGH: 75.0,
            Priority.CRITICAL: 100.0
        }
        return mapping.get(priority, 50.0)

    @classmethod
    def score_task(cls, task: TaskPlanningCandidate, now: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Calculates composite score based on Spec Section 8.4.
        """
        urgency = cls.calculate_deadline_urgency(task.due_at, now)
        priority_score = cls.calculate_priority_score(task.priority)
        importance = float(task.goal_importance)
        readiness = float(task.readiness)

        composite_score = (
            (0.35 * urgency) +
            (0.30 * priority_score) +
            (0.20 * importance) +
            (0.15 * readiness)
        )

        # Reasoning explanation string for user transparency (Section 9.3)
        reasons = []
        if urgency >= 80:
            reasons.append("Approaching deadline")
        elif task.due_at:
            reasons.append("Has scheduled deadline")
        if task.priority >= Priority.HIGH:
            reasons.append("High priority rating")
        if importance >= 75:
            reasons.append("High goal importance")

        if not reasons:
            reasons.append("Routine scheduled study")

        return {
            "task_id": task.id,
            "title": task.title,
            "score": round(composite_score, 2),
            "breakdown": {
                "deadline_urgency": round(urgency, 1),
                "user_priority": round(priority_score, 1),
                "goal_importance": round(importance, 1),
                "readiness": round(readiness, 1),
            },
            "explanation": " • ".join(reasons)
        }

    @classmethod
    def rank_tasks(cls, tasks: List[TaskPlanningCandidate], now: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Ranks candidate tasks deterministically by planning score.
        Pinned tasks always take top slots.
        """
        active_tasks = [t for t in tasks if t.status in {TaskStatus.TODO, TaskStatus.IN_PROGRESS}]
        scored = [cls.score_task(t, now) for t in active_tasks]

        # Map back pinned status
        pinned_map = {t.id: t.is_pinned for t in active_tasks}
        scored.sort(key=lambda item: (pinned_map.get(item["task_id"], False), item["score"]), reverse=True)
        return scored

    @staticmethod
    def detect_conflicts(blocks: List[ScheduleBlock]) -> List[Dict[str, Any]]:
        """
        Detects schedule overlaps and proposes non-conflicting resolution.
        Spec Section 8.3:
        - Detect overlapping focus sessions and scheduled events.
        - Prioritize explicit user-pinned events over automatically suggested sessions.
        """
        conflicts = []
        # Sort blocks chronologically
        sorted_blocks = sorted(blocks, key=lambda b: b.start_time)

        for i in range(len(sorted_blocks)):
            for j in range(i + 1, len(sorted_blocks)):
                b1 = sorted_blocks[i]
                b2 = sorted_blocks[j]

                # Check for overlap: b1.start < b2.end and b2.start < b1.end
                if b1.start_time < b2.end_time and b2.start_time < b1.end_time:
                    # Conflict found!
                    pinned_block = b1 if b1.is_user_pinned else (b2 if b2.is_user_pinned else None)
                    move_block = b2 if b1.is_user_pinned else b1

                    conflicts.append({
                        "block_a": b1.id,
                        "block_b": b2.id,
                        "overlap_start": max(b1.start_time, b2.start_time).isoformat(),
                        "overlap_end": min(b1.end_time, b2.end_time).isoformat(),
                        "priority_block": pinned_block.id if pinned_block else b1.id,
                        "recommended_action": f"Shift block '{move_block.title}' after '{pinned_block.title if pinned_block else b1.title}'."
                    })
        return conflicts
