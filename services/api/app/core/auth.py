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
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedException("Missing or malformed Authorization header")

    token = authorization.split(" ")[1]
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise UnauthorizedException("Invalid or expired authentication token")

    user_id = payload["sub"]
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UnauthorizedException("User associated with token no longer exists")

    return user
