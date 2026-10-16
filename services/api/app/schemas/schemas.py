"""
StudyLock AI - API Request and Response Pydantic Schemas
Ref: StudyLock AI Architecture Specification Section 13 (Endpoint Catalogue & Example Pydantic Request)
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from uuid import UUID


# --- AUTH & USER ---
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: str = Field(min_length=2, max_length=100)
    timezone: str = "Asia/Kolkata"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    display_name: str
    email: str


class UserResponse(BaseModel):
    id: str
    email: str
    display_name: str
    timezone: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    display_name: Optional[str] = Field(None, min_length=2, max_length=100)
    timezone: Optional[str] = None


# --- DEVICES ---
class DeviceRegisterRequest(BaseModel):
    platform: str  # android, ios, windows, macos, browser_extension
    app_version: Optional[str] = "1.0.0"


class DeviceResponse(BaseModel):
    id: str
    platform: str
    app_version: Optional[str]
    last_sync_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class DeviceHeartbeatRequest(BaseModel):
    app_version: Optional[str] = None
    battery_level: Optional[float] = None
    is_charging: Optional[bool] = None


class EnforcementReportRequest(BaseModel):
    enforcement_state: str  # ACTIVE, PARTIAL, PERMISSION_REQUIRED, FAILED
    rule_ids_applied: List[str] = Field(default_factory=list)
    rule_ids_failed: List[str] = Field(default_factory=list)
    failure_reason: Optional[str] = None


# --- TASKS ---
class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    subject: Optional[str] = None
    priority: int = Field(default=2, ge=1, le=4)
    estimated_minutes: int = Field(default=30, ge=1)
    due_at: Optional[datetime] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    subject: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=4)
    estimated_minutes: Optional[int] = Field(None, ge=1)
    due_at: Optional[datetime] = None
    status: Optional[str] = None  # todo, in_progress, done, archived
    expected_revision: Optional[int] = None  # For optimistic concurrency


class TaskResponse(BaseModel):
    id: str
    user_id: str
    title: str
    description: Optional[str]
    subject: Optional[str]
    priority: int
    estimated_minutes: Optional[int]
    due_at: Optional[datetime]
    status: str
    revision: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- SCHEDULES ---
class ScheduleCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    timezone: str = "Asia/Kolkata"
    start_minute: int = Field(ge=0, le=1439)
    duration_minutes: int = Field(ge=1, le=1440)
    recurrence: Optional[Dict[str, Any]] = Field(default_factory=dict)
    enabled: bool = True


class ScheduleUpdate(BaseModel):
    title: Optional[str] = None
    timezone: Optional[str] = None
    start_minute: Optional[int] = Field(None, ge=0, le=1439)
    duration_minutes: Optional[int] = Field(None, ge=1, le=1440)
    recurrence: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None
    expected_revision: Optional[int] = None


class ScheduleResponse(BaseModel):
    id: str
    user_id: str
    title: str
    timezone: str
    start_minute: int
    duration_minutes: int
    recurrence: Dict[str, Any]
    enabled: bool
    revision: int
    created_at: datetime

    class Config:
        from_attributes = True


# --- FOCUS SESSIONS (Section 13.3) ---
class StartSessionRequest(BaseModel):
    task_id: Optional[str] = None
    device_id: Optional[str] = None
    planned_minutes: int = Field(ge=1, le=240, default=25)
    schedule_id: Optional[str] = None
    strict_mode: bool = False


class StartSessionResponse(BaseModel):
    session_id: str
    status: str
    started_at: str
    expected_end_at: str
    enforcement_state: str
    planned_minutes: int


class PauseSessionRequest(BaseModel):
    reason: Optional[str] = "User requested pause"


class ResumeSessionRequest(BaseModel):
    pass


class FinishSessionRequest(BaseModel):
    notes: Optional[str] = None
    interruption_count: Optional[int] = 0


class FinishSessionResponse(BaseModel):
    session_id: str
    status: str
    planned_minutes: int
    actual_seconds: int
    actual_minutes: int
    xp_awarded: int
    reward_reason: str
    current_level: int
    total_xp: int


class FocusSessionResponse(BaseModel):
    id: str
    user_id: str
    task_id: Optional[str]
    device_id: Optional[str]
    started_at: datetime
    ended_at: Optional[datetime]
    planned_minutes: int
    actual_seconds: int
    paused_seconds: int
    status: str
    enforcement_state: str
    interruptions: int

    class Config:
        from_attributes = True


# --- BLOCK RULES ---
class BlockRuleCreate(BaseModel):
    target_type: str  # app_package, domain, url_pattern, supported_category
    target_value: str
    action: str = "block"  # block, allow, warn
    device_id: Optional[str] = None
    enabled: bool = True


class BlockRuleUpdate(BaseModel):
    target_value: Optional[str] = None
    action: Optional[str] = None
    enabled: Optional[bool] = None


class BlockRuleResponse(BaseModel):
    id: str
    user_id: str
    device_id: Optional[str]
    target_type: str
    target_value: str
    action: str
    enabled: bool
    revision: int
    created_at: datetime

    class Config:
        from_attributes = True


class TestRuleRequest(BaseModel):
    candidate: str  # e.g., 'https://www.youtube.com/watch?v=123' or 'discord.exe'


class TestRuleResponse(BaseModel):
    action: Optional[str]
    matched_rule_id: Optional[str]
    reason: str


# --- REWARDS & ACHIEVEMENTS ---
class RewardLedgerResponse(BaseModel):
    id: str
    session_id: Optional[str]
    event_key: str
    xp_delta: int
    reason: str
    created_at: datetime

    class Config:
        from_attributes = True


class AchievementResponse(BaseModel):
    code: str
    title: str
    description: str
    icon: str
    xp_reward: int
    is_unlocked: bool
    unlocked_at: Optional[datetime] = None


# --- SYNC (Section 14) ---
class SyncChangeItem(BaseModel):
    operation_id: str
    device_id: str
    entity_type: str  # task, schedule, block_rule, session
    entity_id: str
    operation: str  # create, update, delete
    payload: Dict[str, Any]
    revision: int


class SyncPushRequest(BaseModel):
    changes: List[SyncChangeItem]


class SyncPullResponse(BaseModel):
    server_time: str
    next_cursor: str
    changes: List[Dict[str, Any]]


# --- PRIVACY ---
class PrivacyExportResponse(BaseModel):
    user: Dict[str, Any]
    tasks: List[Dict[str, Any]]
    schedules: List[Dict[str, Any]]
    focus_sessions: List[Dict[str, Any]]
    block_rules: List[Dict[str, Any]]
    reward_ledger: List[Dict[str, Any]]
    exported_at: str
