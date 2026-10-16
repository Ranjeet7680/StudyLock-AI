"""
StudyLock AI - Security Tests: Cross-User Resource Isolation (IDOR Prevention)
Ref: StudyLock AI Architecture Specification Section 16.1 & Section 16.3
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
def user_a_headers(client):
    email = f"alpha_{uuid.uuid4().hex[:8]}@example.com"
    reg = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "PasswordAlpha123!",
        "display_name": "Student Alpha"
    })
    token = reg.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def user_b_headers(client):
    email = f"beta_{uuid.uuid4().hex[:8]}@example.com"
    reg = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "PasswordBeta123!",
        "display_name": "Student Beta"
    })
    token = reg.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_cannot_access_other_user_task(client, user_a_headers, user_b_headers):
    # User A creates a task
    t_res = client.post("/api/v1/tasks", headers=user_a_headers, json={
        "title": "Alpha Confidential Research",
        "subject": "Bioinformatics",
        "priority": 4
    })
    task_id = t_res.json()["id"]

    # User B attempts to read User A's task
    read_attempt = client.get(f"/api/v1/tasks/{task_id}", headers=user_b_headers)
    assert read_attempt.status_code == 403
    assert read_attempt.json()["error"]["code"] == "FORBIDDEN"

    # User B attempts to update User A's task
    update_attempt = client.patch(f"/api/v1/tasks/{task_id}", headers=user_b_headers, json={
        "title": "Tampered Title"
    })
    assert update_attempt.status_code == 403
    assert update_attempt.json()["error"]["code"] == "FORBIDDEN"

    # User B attempts to delete User A's task
    del_attempt = client.delete(f"/api/v1/tasks/{task_id}", headers=user_b_headers)
    assert del_attempt.status_code == 403
    assert del_attempt.json()["error"]["code"] == "FORBIDDEN"


def test_cannot_access_other_user_schedule(client, user_a_headers, user_b_headers):
    # User A creates a schedule
    s_res = client.post("/api/v1/schedules", headers=user_a_headers, json={
        "title": "Alpha Exam Block",
        "start_minute": 600,
        "duration_minutes": 90
    })
    schedule_id = s_res.json()["id"]

    # User B attempts to delete User A's schedule
    del_attempt = client.delete(f"/api/v1/schedules/{schedule_id}", headers=user_b_headers)
    assert del_attempt.status_code == 403
    assert del_attempt.json()["error"]["code"] == "FORBIDDEN"


def test_cannot_access_other_user_block_rule(client, user_a_headers, user_b_headers):
    # User A creates a block rule
    r_res = client.post("/api/v1/block-rules", headers=user_a_headers, json={
        "target_type": "domain",
        "target_value": "alpha-distraction.com"
    })
    rule_id = r_res.json()["id"]

    # User B attempts to delete User A's rule
    del_attempt = client.delete(f"/api/v1/block-rules/{rule_id}", headers=user_b_headers)
    assert del_attempt.status_code == 403
    assert del_attempt.json()["error"]["code"] == "FORBIDDEN"
