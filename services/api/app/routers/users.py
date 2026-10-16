"""
StudyLock AI - Users Router
Ref: StudyLock AI Architecture Specification Section 13.2
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.models import User
from ..schemas.schemas import UserResponse, UserUpdate
from ..core.auth import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
def get_user_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_user_profile(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if payload.display_name is not None:
        current_user.display_name = payload.display_name
    if payload.timezone is not None:
        current_user.timezone = payload.timezone

    db.commit()
    db.refresh(current_user)
    return current_user
