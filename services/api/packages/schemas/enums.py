"""
StudyLock AI - Core Domain Enums
Ref: StudyLock AI Architecture Specification Sections 6, 7, 9, 12
"""
from enum import Enum


class SessionState(str, Enum):
    PLANNED = "PLANNED"
    STARTING = "STARTING"
    FOCUSING = "FOCUSING"
    PAUSED = "PAUSED"
    BREAK = "BREAK"
    DEGRADED = "DEGRADED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class EnforcementState(str, Enum):
    NOT_CONFIGURED = "NOT_CONFIGURED"
    PERMISSION_REQUIRED = "PERMISSION_REQUIRED"
    APPLYING = "APPLYING"
    ACTIVE = "ACTIVE"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    UNSUPPORTED = "UNSUPPORTED"
    TEMPORARILY_UNAVAILABLE = "TEMPORARILY_UNAVAILABLE"


class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    ARCHIVED = "archived"


class Priority(int, Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class TargetType(str, Enum):
    APP_PACKAGE = "app_package"
    DOMAIN = "domain"
    URL_PATTERN = "url_pattern"
    SUPPORTED_CATEGORY = "supported_category"


class RuleAction(str, Enum):
    BLOCK = "block"
    ALLOW = "allow"
    WARN = "warn"


class RuleScope(str, Enum):
    DEVICE = "device"
    PROFILE = "profile"
    SCHEDULE = "schedule"


class DevicePlatform(str, Enum):
    ANDROID = "android"
    IOS = "ios"
    WINDOWS = "windows"
    MACOS = "macos"
    BROWSER_EXTENSION = "browser_extension"
    WEB_DASHBOARD = "web_dashboard"
