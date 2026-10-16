"""
StudyLock AI - Python API Client Library
Ref: StudyLock AI Architecture Specification Section 23
"""
from typing import Dict, Any, Optional, List
import requests


class StudyLockClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000/api/v1", token: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.token = token

    def _headers(self, idempotency_key: Optional[str] = None) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        return headers

    def register(self, email: str, password: str, display_name: str, timezone: str = "Asia/Kolkata") -> Dict[str, Any]:
        resp = requests.post(f"{self.base_url}/auth/register", json={
            "email": email,
            "password": password,
            "display_name": display_name,
            "timezone": timezone
        })
        resp.raise_for_status()
        data = resp.json()
        self.token = data.get("access_token")
        return data

    def login(self, email: str, password: str) -> Dict[str, Any]:
        resp = requests.post(f"{self.base_url}/auth/login", json={"email": email, "password": password})
        resp.raise_for_status()
        data = resp.json()
        self.token = data.get("access_token")
        return data

    def get_me(self) -> Dict[str, Any]:
        resp = requests.get(f"{self.base_url}/users/me", headers=self._headers())
        resp.raise_for_status()
        return resp.json()

    def list_tasks(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {"status": status} if status else {}
        resp = requests.get(f"{self.base_url}/tasks", headers=self._headers(), params=params)
        resp.raise_for_status()
        return resp.json()

    def create_task(self, title: str, priority: int = 2, estimated_minutes: int = 30, subject: Optional[str] = None) -> Dict[str, Any]:
        resp = requests.post(f"{self.base_url}/tasks", headers=self._headers(), json={
            "title": title,
            "priority": priority,
            "estimated_minutes": estimated_minutes,
            "subject": subject
        })
        resp.raise_for_status()
        return resp.json()

    def start_session(self, planned_minutes: int = 25, task_id: Optional[str] = None, idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        resp = requests.post(f"{self.base_url}/sessions/start", headers=self._headers(idempotency_key), json={
            "planned_minutes": planned_minutes,
            "task_id": task_id
        })
        resp.raise_for_status()
        return resp.json()

    def pause_session(self, session_id: str, reason: str = "Break") -> Dict[str, Any]:
        resp = requests.post(f"{self.base_url}/sessions/{session_id}/pause", headers=self._headers(), json={"reason": reason})
        resp.raise_for_status()
        return resp.json()

    def resume_session(self, session_id: str) -> Dict[str, Any]:
        resp = requests.post(f"{self.base_url}/sessions/{session_id}/resume", headers=self._headers(), json={})
        resp.raise_for_status()
        return resp.json()

    def finish_session(self, session_id: str, idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        resp = requests.post(f"{self.base_url}/sessions/{session_id}/finish", headers=self._headers(idempotency_key), json={})
        resp.raise_for_status()
        return resp.json()

    def get_rewards_ledger(self) -> Dict[str, Any]:
        resp = requests.get(f"{self.base_url}/rewards/ledger", headers=self._headers())
        resp.raise_for_status()
        return resp.json()

    def get_weekly_analytics(self) -> Dict[str, Any]:
        resp = requests.get(f"{self.base_url}/analytics/weekly", headers=self._headers())
        resp.raise_for_status()
        return resp.json()
