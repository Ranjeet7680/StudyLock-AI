"""
StudyLock AI - Idempotency Key Manager
Ref: StudyLock AI Architecture Specification Section 13.1 & Section 14.3
"""
from typing import Dict, Any, Optional
import time

# In-memory store for idempotency keys (can be swapped with Redis in production)
_IDEMPOTENCY_STORE: Dict[str, Dict[str, Any]] = {}
TTL_SECONDS = 86400  # 24 hours retention


def check_idempotency_key(key: Optional[str]) -> Optional[Dict[str, Any]]:
    if not key:
        return None
    record = _IDEMPOTENCY_STORE.get(key)
    if not record:
        return None
    # Check expiry
    if time.time() - record["timestamp"] > TTL_SECONDS:
        del _IDEMPOTENCY_STORE[key]
        return None
    return record["response"]


def record_idempotency_key(key: Optional[str], response_data: Dict[str, Any]) -> None:
    if not key:
        return
    _IDEMPOTENCY_STORE[key] = {
        "timestamp": time.time(),
        "response": response_data
    }
