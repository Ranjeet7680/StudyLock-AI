"""
StudyLock AI - End-to-End API Integration Tests
Ref: StudyLock AI Architecture Specification Section 13, 14, 18
"""
import pytest
import sys
import os
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../services/api")))
from app.main import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


import uuid

@pytest.fixture(scope="module")
def auth_headers(client):
    email = f"tester_{uuid.uuid4().hex[:8]}@example.com"
    reg = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "StrongPassword123!",
        "display_name": "Integration Tester",
        "timezone": "Asia/Kolkata"
    })
    token = reg.json().get("access_token")
    return {"Authorization": f"Bearer {token}"}


def test_auth_and_profile_flow(client, auth_headers):
    # GET profile
    me = client.get("/api/v1/users/me", headers=auth_headers)
    assert me.status_code == 200
    assert me.json()["email"].startswith("tester_")

    # PATCH profile
    updated = client.patch("/api/v1/users/me", headers=auth_headers, json={
        "display_name": "Senior Tester"
    })
    assert updated.status_code == 200
    assert updated.json()["display_name"] == "Senior Tester"


def test_tasks_crud_and_optimistic_locking(client, auth_headers):
    # 1. Create Task
    create_res = client.post("/api/v1/tasks", headers=auth_headers, json={
        "title": "Solve 10 LeetCode Problems",
        "subject": "Algorithms",
        "priority": 3,
        "estimated_minutes": 60
    })
    assert create_res.status_code == 201
    task_id = create_res.json()["id"]
    revision = create_res.json()["revision"]

    # 2. Update Task
    update_res = client.patch(f"/api/v1/tasks/{task_id}", headers=auth_headers, json={
        "title": "Solve 15 LeetCode Problems",
        "expected_revision": revision
    })
    assert update_res.status_code == 200
    assert update_res.json()["revision"] == revision + 1

    # 3. Optimistic Concurrency Conflict (pass stale revision)
    conflict_res = client.patch(f"/api/v1/tasks/{task_id}", headers=auth_headers, json={
        "title": "Stale edit",
        "expected_revision": revision  # Stale! Current is revision + 1
    })
    assert conflict_res.status_code == 409
    assert conflict_res.json()["error"]["code"] == "CONFLICT"

    # 4. Soft Delete Task
    del_res = client.delete(f"/api/v1/tasks/{task_id}", headers=auth_headers)
    assert del_res.status_code == 204

    # 5. Verify Soft Deleted (not in default list)
    list_res = client.get("/api/v1/tasks", headers=auth_headers)
    ids = [t["id"] for t in list_res.json()]
    assert task_id not in ids


def test_sessions_lifecycle_and_reward_issuance(client, auth_headers):
    # 1. Start Session
    start_res = client.post("/api/v1/sessions/start", headers=auth_headers, json={
        "planned_minutes": 25
    })
    assert start_res.status_code == 201
    session_id = start_res.json()["session_id"]
    assert start_res.json()["status"] == "FOCUSING"

    # 2. Pause Session
    pause_res = client.post(f"/api/v1/sessions/{session_id}/pause", headers=auth_headers, json={
        "reason": "Water break"
    })
    assert pause_res.status_code == 200
    assert pause_res.json()["status"] == "PAUSED"

    # 3. Resume Session
    resume_res = client.post(f"/api/v1/sessions/{session_id}/resume", headers=auth_headers)
    assert resume_res.status_code == 200
    assert resume_res.json()["status"] == "FOCUSING"

    # 4. Finish Session (Transactionally issues XP)
    finish_res = client.post(f"/api/v1/sessions/{session_id}/finish", headers=auth_headers, json={
        "notes": "Session went great"
    })
    assert finish_res.status_code == 200
    data = finish_res.json()
    assert data["status"] == "COMPLETED"
    assert data["xp_awarded"] > 0
    assert data["total_xp"] > 0

    # 5. Check Ledger
    ledger_res = client.get("/api/v1/rewards/ledger", headers=auth_headers)
    assert ledger_res.status_code == 200
    assert len(ledger_res.json()["entries"]) > 0


def test_block_rules_and_simulator(client, auth_headers):
    # Create rule
    rule_res = client.post("/api/v1/block-rules", headers=auth_headers, json={
        "target_type": "domain",
        "target_value": "distraction-hub.com",
        "action": "block"
    })
    assert rule_res.status_code == 201

    # Test simulator endpoint
    sim_res = client.post("/api/v1/block-rules/test", headers=auth_headers, json={
        "candidate": "https://distraction-hub.com/feed"
    })
    assert sim_res.status_code == 200
    assert sim_res.json()["action"] == "block"


def test_analytics_endpoints(client, auth_headers):
    weekly = client.get("/api/v1/analytics/weekly", headers=auth_headers)
    assert weekly.status_code == 200
    assert "actual_minutes" in weekly.json()

    dash = client.get("/api/v1/analytics/dashboard", headers=auth_headers)
    assert dash.status_code == 200
    assert "daily_goal_progress_percent" in dash.json()


def test_privacy_export_flow(client, auth_headers):
    export_res = client.post("/api/v1/privacy/export", headers=auth_headers)
    assert export_res.status_code == 200
    data = export_res.json()
    assert "user" in data
    assert "tasks" in data
    assert "reward_ledger" in data
