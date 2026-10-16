"""
StudyLock AI - Video Fast Processing & Download Integration Tests
Ref: StudyLock AI Architecture Specification Section 13, 14
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


def test_video_process_submission_and_status(client):
    # 1. Start video processing job
    res = client.post("/api/v1/video/process", json={
        "title": "Calculus Lecture Fast Process",
        "preset": "ultra_fast",
        "speed_factor": 1.5,
        "resolution": "1080p"
    })
    assert res.status_code == 201
    data = res.json()
    assert "job_id" in data
    assert data["status"] in ("processing", "completed")
    assert "progress_percent" in data
    assert "current_stage" in data
    job_id = data["job_id"]

    # 2. Poll job status
    status_res = client.get(f"/api/v1/video/status/{job_id}")
    assert status_res.status_code == 200
    st_data = status_res.json()
    assert st_data["job_id"] == job_id
    assert 0 <= st_data["progress_percent"] <= 100
    assert "download_url" in st_data

    # 3. Download the full video
    dl_res = client.get(f"/api/v1/video/download/{job_id}")
    assert dl_res.status_code == 200
    assert "video/webm" in dl_res.headers.get("content-type", "")
    assert "attachment" in dl_res.headers.get("content-disposition", "")
    assert len(dl_res.content) > 1000  # Non-empty playable video payload
