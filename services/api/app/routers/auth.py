"""
StudyLock AI - Authentication Router
Ref: StudyLock AI Architecture Specification Section 13.2 & Section 16
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.models import User, Device
from ..schemas.schemas import RegisterRequest, LoginRequest, AuthTokenResponse, UserResponse
from ..core.security import hash_password, verify_password, create_access_token
from ..core.errors import StudyLockException, UnauthorizedException
from ..core.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=AuthTokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise StudyLockException(
            status_code=400,
            code="EMAIL_ALREADY_REGISTERED",
            message="An account with this email address already exists."
        )

    user = User(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        display_name=payload.display_name,
        timezone=payload.timezone
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.id, "email": user.email})
    return AuthTokenResponse(
        access_token=token,
        user_id=user.id,
        display_name=user.display_name,
        email=user.email
    )


@router.post("/login", response_model=AuthTokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise UnauthorizedException("Invalid email or password.")

    token = create_access_token({"sub": user.id, "email": user.email})
    return AuthTokenResponse(
        access_token=token,
        user_id=user.id,
        display_name=user.display_name,
        email=user.email
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
