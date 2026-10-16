"""
StudyLock AI - SQLAlchemy Relational Core Models
Ref: StudyLock AI Architecture Specification Section 12 (Core Entities & Starter Schema)
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    SmallInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Index,
    CheckConstraint
)
from sqlalchemy.orm import relationship
from ..database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(100), nullable=False)
    timezone = Column(String(64), nullable=False, default="Asia/Kolkata")
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    devices = relationship("Device", back_populates="user", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    schedules = relationship("Schedule", back_populates="user", cascade="all, delete-orphan")
    focus_sessions = relationship("FocusSession", back_populates="user", cascade="all, delete-orphan")
    block_rules = relationship("BlockRule", back_populates="user", cascade="all, delete-orphan")
    reward_entries = relationship("RewardLedger", back_populates="user", cascade="all, delete-orphan")


class Device(Base):
    __tablename__ = "devices"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    platform = Column(String(32), nullable=False)  # android, ios, windows, macos, browser_extension
    app_version = Column(String(32), nullable=True)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    user = relationship("User", back_populates="devices")
    block_rules = relationship("BlockRule", back_populates="device")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    subject = Column(String(100), nullable=True)
    priority = Column(SmallInteger, nullable=False, default=2)  # 1: Low, 2: Med, 3: High, 4: Critical
    estimated_minutes = Column(Integer, nullable=True, default=30)
    due_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(24), nullable=False, default="todo")  # todo, in_progress, done, archived
    revision = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # Soft delete support for sync

    user = relationship("User", back_populates="tasks")

    __table_args__ = (
        Index("idx_tasks_user_status", "user_id", "status"),
        Index("idx_tasks_user_due", "user_id", "due_at"),
    )


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    timezone = Column(String(64), nullable=False, default="Asia/Kolkata")
    start_minute = Column(SmallInteger, nullable=False, default=540)  # Minute of the day (0..1439), e.g. 540 = 09:00
    duration_minutes = Column(Integer, nullable=False, default=45)
    recurrence = Column(Text, nullable=False, default="{}")  # JSON encoded recurrence rules
    enabled = Column(Boolean, nullable=False, default=True)
    revision = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    user = relationship("User", back_populates="schedules")


class FocusSession(Base):
    __tablename__ = "focus_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id = Column(String(36), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)
    device_id = Column(String(36), ForeignKey("devices.id", ondelete="SET NULL"), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    planned_minutes = Column(Integer, nullable=False, default=25)
    actual_seconds = Column(Integer, nullable=False, default=0)
    paused_seconds = Column(Integer, nullable=False, default=0)
    status = Column(String(24), nullable=False, default="PLANNED")
    enforcement_state = Column(String(32), nullable=False, default="ACTIVE")
    interruptions = Column(Integer, nullable=False, default=0)
    state_history = Column(Text, nullable=False, default="[]")  # JSON encoded transition logs

    user = relationship("User", back_populates="focus_sessions")

    __table_args__ = (
        Index("idx_sessions_user_started", "user_id", "started_at"),
    )


class BlockRule(Base):
    __tablename__ = "block_rules"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id = Column(String(36), ForeignKey("devices.id", ondelete="CASCADE"), nullable=True)
    target_type = Column(String(32), nullable=False)  # app_package, domain, url_pattern, supported_category
    target_value = Column(String(255), nullable=False)
    action = Column(String(16), nullable=False, default="block")  # block, allow, warn
    scope = Column(String(16), nullable=False, default="device")
    enabled = Column(Boolean, nullable=False, default=True)
    revision = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    user = relationship("User", back_populates="block_rules")
    device = relationship("Device", back_populates="block_rules")

    __table_args__ = (
        Index("idx_rules_user_device", "user_id", "device_id"),
    )


class RewardLedger(Base):
    __tablename__ = "reward_ledger"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(36), ForeignKey("focus_sessions.id", ondelete="SET NULL"), nullable=True)
    event_key = Column(String(255), nullable=False, unique=True, index=True)  # Idempotency constraint!
    xp_delta = Column(Integer, nullable=False)
    reason = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    user = relationship("User", back_populates="reward_entries")

    __table_args__ = (
        Index("idx_rewards_user_created", "user_id", "created_at"),
    )


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    code = Column(String(64), nullable=False, unique=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(String(255), nullable=False)
    icon = Column(String(32), nullable=False, default="🏆")
    xp_reward = Column(Integer, nullable=False, default=50)


class UserAchievement(Base):
    __tablename__ = "user_achievements"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    achievement_code = Column(String(64), nullable=False)
    unlocked_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        Index("idx_user_achievement_unique", "user_id", "achievement_code", unique=True),
    )


class SyncChange(Base):
    """
    Outbox log for offline-first delta synchronization (Spec Section 14).
    """
    __tablename__ = "sync_changes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id = Column(String(36), nullable=False)
    entity_type = Column(String(32), nullable=False)  # task, schedule, block_rule, session
    entity_id = Column(String(36), nullable=False)
    operation = Column(String(16), nullable=False)  # create, update, delete
    payload = Column(Text, nullable=False)
    revision = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class AuditEvent(Base):
    """
    Security-sensitive operation audit trail (Spec Section 12.1).
    """
    __tablename__ = "audit_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), nullable=True, index=True)
    action = Column(String(64), nullable=False)
    ip_address = Column(String(45), nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
