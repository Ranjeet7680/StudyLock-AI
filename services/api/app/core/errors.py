"""
StudyLock AI - Standardized Error Handling & Exception Types
Ref: StudyLock AI Architecture Specification Section 13.4
"""
from typing import Optional
from fastapi import Request
from fastapi.responses import JSONResponse
import uuid


class StudyLockException(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        retryable: bool = False,
        details: Optional[dict] = None
    ):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.retryable = retryable
        self.details = details or {}
        super().__init__(message)


class NotFoundException(StudyLockException):
    def __init__(self, message: str = "Requested resource not found"):
        super().__init__(status_code=404, code="NOT_FOUND", message=message, retryable=False)


class UnauthorizedException(StudyLockException):
    def __init__(self, message: str = "Invalid authentication credentials"):
        super().__init__(status_code=401, code="UNAUTHORIZED", message=message, retryable=False)


class ForbiddenException(StudyLockException):
    def __init__(self, message: str = "You do not have access to this resource"):
        super().__init__(status_code=403, code="FORBIDDEN", message=message, retryable=False)


class ConflictException(StudyLockException):
    def __init__(self, message: str = "Resource conflict or stale revision detected"):
        super().__init__(status_code=409, code="CONFLICT", message=message, retryable=True)


class PermissionRequiredException(StudyLockException):
    def __init__(self, message: str = "A required permission is not available on this device."):
        super().__init__(
            status_code=400,
            code="ENFORCEMENT_PERMISSION_REQUIRED",
            message=message,
            retryable=False
        )


async def studylock_exception_handler(request: Request, exc: StudyLockException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "request_id": request_id,
                "retryable": exc.retryable
            }
        }
    )
