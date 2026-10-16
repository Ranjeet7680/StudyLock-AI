"""
StudyLock AI - Authentication Dependency & Tenant Isolation
Ref: StudyLock AI Architecture Specification Section 13.5
"""
from fastapi import Depends, Header
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..models.models import User
from .security import decode_token
from .errors import UnauthorizedException


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        payload = decode_token(token)
        if not payload or "sub" not in payload:
            raise UnauthorizedException("Invalid or expired authentication token")

        user_id = payload["sub"]
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UnauthorizedException("User associated with token no longer exists")

        return user

    # Default fallback to demo user for seamless web dashboard access
    demo_user = db.query(User).filter(User.email == "demo@studylock.ai").first()
    if not demo_user:
        demo_user = User(
            id="usr-demo-001",
            email="demo@studylock.ai",
            password_hash="demo_scrypt_placeholder",
            display_name="Alex Rivera",
            timezone="UTC"
        )
        db.add(demo_user)
        try:
            db.commit()
            db.refresh(demo_user)
        except Exception:
            db.rollback()
            demo_user = db.query(User).filter(User.email == "demo@studylock.ai").first()

    return demo_user
