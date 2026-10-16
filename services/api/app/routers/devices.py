"""
StudyLock AI - Devices Router & Enforcement Status
Ref: StudyLock AI Architecture Specification Section 6.5 & Section 13.2
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone
from ..database import get_db
from ..models.models import Device, User
from ..schemas.schemas import (
    DeviceRegisterRequest,
    DeviceResponse,
    DeviceHeartbeatRequest,
    EnforcementReportRequest
)
from ..core.auth import get_current_user
from ..core.errors import NotFoundException, ForbiddenException

router = APIRouter(prefix="/devices", tags=["Devices"])


@router.get("", response_model=List[DeviceResponse])
def list_devices(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Device).filter(Device.user_id == current_user.id).all()


@router.post("", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
def register_device(
    payload: DeviceRegisterRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    device = Device(
        user_id=current_user.id,
        platform=payload.platform.lower(),
        app_version=payload.app_version,
        last_sync_at=datetime.now(timezone.utc)
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


@router.post("/{device_id}/heartbeat")
def device_heartbeat(
    device_id: str,
    payload: DeviceHeartbeatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise NotFoundException("Device not found")
    if device.user_id != current_user.id:
        raise ForbiddenException()

    device.last_sync_at = datetime.now(timezone.utc)
    if payload.app_version:
        device.app_version = payload.app_version

    db.commit()
    return {"status": "ok", "last_sync_at": device.last_sync_at.isoformat()}


@router.post("/{device_id}/enforcement-report")
def report_enforcement(
    device_id: str,
    payload: EnforcementReportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise NotFoundException("Device not found")
    if device.user_id != current_user.id:
        raise ForbiddenException()

    return {
        "status": "acknowledged",
        "device_id": device_id,
        "enforcement_state": payload.enforcement_state,
        "applied_count": len(payload.rule_ids_applied),
        "failed_count": len(payload.rule_ids_failed),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
