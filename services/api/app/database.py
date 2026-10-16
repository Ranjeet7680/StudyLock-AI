"""
StudyLock AI - Database Connection & Session Management
Ref: StudyLock AI Architecture Specification Section 12
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool
from .config import settings

connect_args = {}
poolclass = None

if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    if ":memory:" in settings.DATABASE_URL:
        poolclass = StaticPool
    else:
        # Ensure target directory exists for file-based SQLite
        try:
            if settings.DATABASE_URL.startswith("sqlite:////"):
                raw_path = settings.DATABASE_URL.replace("sqlite:////", "/")
                os.makedirs(os.path.dirname(raw_path), exist_ok=True)
            elif settings.DATABASE_URL.startswith("sqlite:///"):
                raw_path = settings.DATABASE_URL.replace("sqlite:///", "")
                d = os.path.dirname(raw_path)
                if d:
                    os.makedirs(d, exist_ok=True)
        except Exception:
            pass

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    poolclass=poolclass if poolclass else None,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
