"""
StudyLock AI - Rewards & Achievements Router
Ref: StudyLock AI Architecture Specification Section 10 & Section 13.2
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from ..database import get_db
from ..models.models import RewardLedger, Achievement, UserAchievement, User
from ..schemas.schemas import RewardLedgerResponse, AchievementResponse
from ..core.auth import get_current_user

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))
from packages.schemas.rewards import RewardEngine

router = APIRouter(prefix="/rewards", tags=["Rewards & Gamification"])

DEFAULT_ACHIEVEMENTS = [
    {"code": "FIRST_SESSION", "title": "First Step", "description": "Complete your first timed focus session", "icon": "🌱", "xp_reward": 25},
    {"code": "DEEP_DIVE", "title": "Deep Diver", "description": "Complete a 45+ minute uninterrupted session", "icon": "🌊", "xp_reward": 40},
    {"code": "CONSISTENCY_3", "title": "Streak Starter", "description": "Study 3 days in a row", "icon": "🔥", "xp_reward": 75},
    {"code": "TASK_MASTER", "title": "Task Finisher", "description": "Complete 5 scheduled study tasks", "icon": "⚡", "xp_reward": 50},
    {"code": "ZEN_MODE", "title": "Digital Monk", "description": "Complete a session with 0 interruptions", "icon": "🧘", "xp_reward": 30},
]


@router.get("/ledger", response_model=Dict[str, Any])
def get_reward_ledger(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Returns ledger event history, calculated total XP, and current level progression.
    XP is derived from ledger events, never stored as a mutable counter (Spec Section 10.1).
    """
    entries = db.query(RewardLedger).filter(
        RewardLedger.user_id == current_user.id
    ).order_by(RewardLedger.created_at.desc()).all()

    total_xp = sum(e.xp_delta for e in entries)
    level_info = RewardEngine.calculate_level(total_xp)

    return {
        "user_id": current_user.id,
        "total_xp": total_xp,
        "level_info": level_info,
        "entries": [
            RewardLedgerResponse(
                id=e.id,
                session_id=e.session_id,
                event_key=e.event_key,
                xp_delta=e.xp_delta,
                reason=e.reason,
                created_at=e.created_at
            )
            for e in entries
        ]
    }


@router.get("/achievements", response_model=List[AchievementResponse])
def get_achievements(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    unlocked = db.query(UserAchievement).filter(UserAchievement.user_id == current_user.id).all()
    unlocked_map = {u.achievement_code: u.unlocked_at for u in unlocked}

    # Also automatically check if FIRST_SESSION should be unlocked based on ledger
    has_session = db.query(RewardLedger).filter(
        RewardLedger.user_id == current_user.id,
        RewardLedger.session_id.isnot(None)
    ).first()
    if has_session and "FIRST_SESSION" not in unlocked_map:
        unlocked_map["FIRST_SESSION"] = has_session.created_at

    response = []
    for a in DEFAULT_ACHIEVEMENTS:
        is_unlocked = a["code"] in unlocked_map
        response.append(
            AchievementResponse(
                code=a["code"],
                title=a["title"],
                description=a["description"],
                icon=a["icon"],
                xp_reward=a["xp_reward"],
                is_unlocked=is_unlocked,
                unlocked_at=unlocked_map.get(a["code"])
            )
        )
    return response
