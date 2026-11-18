import os
import sys
import uuid
import tempfile
from datetime import datetime, timezone
import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.main import app
from src.api.storage import get_storage
from src.config import EVIDENCE_DIR

client = TestClient(app)

def create_synthetic_mp4(filepath: str, num_frames: int = 16, fps: int = 30, width: int = 160, height: int = 120):
    """Creates a tiny valid synthetic MP4 file for testing."""
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(filepath, fourcc, fps, (width, height))
    for i in range(num_frames):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        cv2.circle(frame, (20 + (i * 5) % 120, 60), 15, (0, 0, 255), -1)
        out.write(frame)
    out.release()

@pytest.fixture(scope="module")
def setup_module():
    storage = get_storage()
    storage.initialize()
    os.makedirs(EVIDENCE_DIR, exist_ok=True)

class TestAuthAndDataPrivacy:
    user_a_token = None
    user_a_id = None
    user_a_email = f"agent.alpha.{uuid.uuid4().hex[:6]}@visioniq.io"

    user_b_token = None
    user_b_id = None
    user_b_email = f"agent.beta.{uuid.uuid4().hex[:6]}@visioniq.io"

    user_a_video_id = None
    user_b_video_id = None
    user_a_event_id = None
    user_a_snapshot_name = None

    def test_01_unauthenticated_requests_blocked(self):
        """Unauthenticated requests to protected endpoints return 401."""
        endpoints = [
            ("GET", "/api/auth/me"),
            ("GET", "/api/videos"),
            ("POST", "/api/videos/upload"),
            ("GET", "/api/events"),
            ("POST", "/api/chat/query"),
            ("GET", "/api/live/cameras"),
        ]
        for method, path in endpoints:
            if method == "GET":
                res = client.get(path)
            else:
                res = client.post(path)
            assert res.status_code == 401, f"{method} {path} should return 401 without auth"

    def test_02_registration_validation(self):
        """Validates input constraints and duplicate account rejection."""
        # Invalid email
        res = client.post("/api/auth/register", json={
            "name": "Invalid Email",
            "email": "not-an-email",
            "password": "validPassword123"
        })
        assert res.status_code == 400

        # Short password
        res = client.post("/api/auth/register", json={
            "name": "Short PW",
            "email": "short@visioniq.io",
            "password": "123"
        })
        assert res.status_code in (400, 422)

        # Successful registration of User A
        res = client.post("/api/auth/register", json={
            "name": "Agent Alpha",
            "email": TestAuthAndDataPrivacy.user_a_email,
            "password": "alphaPassword123"
        })
        assert res.status_code == 201
        data = res.json()
        assert "access_token" in data
        assert data["user"]["email"] == TestAuthAndDataPrivacy.user_a_email
        TestAuthAndDataPrivacy.user_a_token = data["access_token"]
        TestAuthAndDataPrivacy.user_a_id = data["user"]["id"]

        # Duplicate email registration rejected with 409
        dup_res = client.post("/api/auth/register", json={
            "name": "Imposter Alpha",
            "email": TestAuthAndDataPrivacy.user_a_email,
            "password": "anotherPassword123"
        })
        assert dup_res.status_code == 409

        # Register User B
        res_b = client.post("/api/auth/register", json={
            "name": "Agent Beta",
            "email": TestAuthAndDataPrivacy.user_b_email,
            "password": "betaPassword123"
        })
        assert res_b.status_code == 201
        data_b = res_b.json()
        TestAuthAndDataPrivacy.user_b_token = data_b["access_token"]
        TestAuthAndDataPrivacy.user_b_id = data_b["user"]["id"]

        assert TestAuthAndDataPrivacy.user_a_id != TestAuthAndDataPrivacy.user_b_id

    def test_03_login_and_me_endpoint(self):
        """Tests credentials validation and session restoration."""
        # Wrong password
        bad_login = client.post("/api/auth/login", json={
            "email": TestAuthAndDataPrivacy.user_a_email,
            "password": "wrongPassword"
        })
        assert bad_login.status_code == 401

        # Correct login
        good_login = client.post("/api/auth/login", json={
            "email": TestAuthAndDataPrivacy.user_a_email,
            "password": "alphaPassword123"
        })
        assert good_login.status_code == 200
        token = good_login.json()["access_token"]

        # Verify /api/auth/me with Bearer token
        me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_res.status_code == 200
        assert me_res.json()["id"] == TestAuthAndDataPrivacy.user_a_id

    def test_04_isolated_video_uploads(self):
        """User A and User B upload independent videos; listings are strictly partitioned."""
        headers_a = {"Authorization": f"Bearer {TestAuthAndDataPrivacy.user_a_token}"}
        headers_b = {"Authorization": f"Bearer {TestAuthAndDataPrivacy.user_b_token}"}

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_a:
            create_synthetic_mp4(tmp_a.name)
            tmp_a_path = tmp_a.name

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_b:
            create_synthetic_mp4(tmp_b.name)
            tmp_b_path = tmp_b.name

        try:
            # User A uploads
            with open(tmp_a_path, "rb") as f_a:
                up_a = client.post("/api/videos/upload", files={"file": ("cctv_alpha.mp4", f_a, "video/mp4")}, headers=headers_a)
            assert up_a.status_code == 201
            TestAuthAndDataPrivacy.user_a_video_id = up_a.json()["video_id"]

            # User B uploads
            with open(tmp_b_path, "rb") as f_b:
                up_b = client.post("/api/videos/upload", files={"file": ("cctv_beta.mp4", f_b, "video/mp4")}, headers=headers_b)
            assert up_b.status_code == 201
            TestAuthAndDataPrivacy.user_b_video_id = up_b.json()["video_id"]

            # User A lists videos: must contain ONLY User A's video
            list_a = client.get("/api/videos", headers=headers_a).json()
            ids_a = [v["video_id"] for v in list_a["videos"]]
            assert TestAuthAndDataPrivacy.user_a_video_id in ids_a
            assert TestAuthAndDataPrivacy.user_b_video_id not in ids_a

            # User B lists videos: must contain ONLY User B's video
            list_b = client.get("/api/videos", headers=headers_b).json()
            ids_b = [v["video_id"] for v in list_b["videos"]]
            assert TestAuthAndDataPrivacy.user_b_video_id in ids_b
            assert TestAuthAndDataPrivacy.user_a_video_id not in ids_b

        finally:
            if os.path.exists(tmp_a_path):
                os.remove(tmp_a_path)
            if os.path.exists(tmp_b_path):
                os.remove(tmp_b_path)

    def test_05_idor_protection_on_video_endpoints(self):
        """User B cannot access, status-poll, download, or delete User A's video."""
        headers_b = {"Authorization": f"Bearer {TestAuthAndDataPrivacy.user_b_token}"}
        target_vid = TestAuthAndDataPrivacy.user_a_video_id

        # Video status
        res_status = client.get(f"/api/videos/{target_vid}/status", headers=headers_b)
        assert res_status.status_code == 404

        # Video events
        res_events = client.get(f"/api/videos/{target_vid}/events", headers=headers_b)
        assert res_events.status_code == 404

        # Video download
        res_dl = client.get(f"/api/videos/{target_vid}/download", headers=headers_b)
        assert res_dl.status_code == 404

        # Video delete by User B
        res_del = client.delete(f"/api/videos/{target_vid}", headers=headers_b)
        assert res_del.status_code == 404

    def test_06_events_and_evidence_privacy(self):
        """Events created under User A's video inherit ownership and block User B from snapshots."""
        storage = get_storage()
        snap_id = str(uuid.uuid4())
        snap_filename = f"{snap_id}.jpg"
        snap_path = os.path.join(EVIDENCE_DIR, snap_filename)

        # Write genuine synthetic snapshot frame
        fake_frame = np.full((100, 100, 3), 128, dtype=np.uint8)
        cv2.imwrite(snap_path, fake_frame)

        TestAuthAndDataPrivacy.user_a_snapshot_name = snap_filename
        event_id = str(uuid.uuid4())
        TestAuthAndDataPrivacy.user_a_event_id = event_id

        # Save an event for User A
        storage.save_events(
            video_id=TestAuthAndDataPrivacy.user_a_video_id,
            events_data=[{
                "event_id": event_id,
                "video_id": TestAuthAndDataPrivacy.user_a_video_id,
                "activity_label": "Fighting",
                "confidence": 0.95,
                "start_timestamp": 1.0,
                "end_timestamp": 3.0,
                "start_time_formatted": "00:00:01",
                "end_time_formatted": "00:00:03",
                "evidence_snapshot": f"/api/evidence/{snap_filename}",
                "evidence_clip": None,
                "processing_status": "completed",
                "created_at": datetime.now(timezone.utc)
            }],
            user_id=TestAuthAndDataPrivacy.user_a_id
        )

        headers_a = {"Authorization": f"Bearer {TestAuthAndDataPrivacy.user_a_token}"}
        headers_b = {"Authorization": f"Bearer {TestAuthAndDataPrivacy.user_b_token}"}

        # User A lists events -> sees Fighting event
        res_ev_a = client.get("/api/events", headers=headers_a)
        assert res_ev_a.status_code == 200
        ev_ids_a = [e["event_id"] for e in res_ev_a.json()["events"]]
        assert event_id in ev_ids_a

        # User B lists events -> does NOT see Fighting event
        res_ev_b = client.get("/api/events", headers=headers_b)
        assert res_ev_b.status_code == 200
        ev_ids_b = [e["event_id"] for e in res_ev_b.json()["events"]]
        assert event_id not in ev_ids_b

        # Evidence Snapshot Access:
        # User A can load snapshot
        res_snap_a = client.get(f"/api/evidence/{snap_filename}", headers=headers_a)
        assert res_snap_a.status_code == 200
        assert res_snap_a.headers["content-type"] == "image/jpeg"

        # User B is blocked with 404 from loading User A's snapshot
        res_snap_b = client.get(f"/api/evidence/{snap_filename}", headers=headers_b)
        assert res_snap_b.status_code == 404

        # Also supports ?token= query parameter for User A
        res_snap_token = client.get(f"/api/evidence/{snap_filename}?token={TestAuthAndDataPrivacy.user_a_token}")
        assert res_snap_token.status_code == 200

    def test_07_ai_assistant_rag_privacy_isolation(self):
        """AI Assistant queries run by User B cannot discover User A's events."""
        headers_a = {"Authorization": f"Bearer {TestAuthAndDataPrivacy.user_a_token}"}
        headers_b = {"Authorization": f"Bearer {TestAuthAndDataPrivacy.user_b_token}"}

        # User A queries about fighting -> returns event
        chat_a = client.post("/api/chat/query", json={"query": "Show all fighting incidents"}, headers=headers_a)
        assert chat_a.status_code == 200
        res_a = chat_a.json()
        assert res_a["total"] >= 1
        assert any(e["event_id"] == TestAuthAndDataPrivacy.user_a_event_id for e in res_a["events"])

        # User B queries about fighting -> returns 0 events
        chat_b = client.post("/api/chat/query", json={"query": "Show all fighting incidents"}, headers=headers_b)
        assert chat_b.status_code == 200
        res_b = chat_b.json()
        assert res_b["total"] == 0
        assert len(res_b["events"]) == 0
        assert TestAuthAndDataPrivacy.user_a_event_id not in [e.get("event_id") for e in res_b["events"]]

    def test_08_deletion_and_cleanup_privacy(self):
        """User B cannot delete User A's events or videos; User A can delete their own."""
        headers_a = {"Authorization": f"Bearer {TestAuthAndDataPrivacy.user_a_token}"}
        headers_b = {"Authorization": f"Bearer {TestAuthAndDataPrivacy.user_b_token}"}
        ev_id = TestAuthAndDataPrivacy.user_a_event_id
        vid_id = TestAuthAndDataPrivacy.user_a_video_id

        # User B attempts to delete User A's event -> 404
        assert client.delete(f"/api/events/{ev_id}", headers=headers_b).status_code == 404

        # User A deletes their own event -> 200
        assert client.delete(f"/api/events/{ev_id}", headers=headers_a).status_code == 200

        # User A deletes their own video -> 200
        assert client.delete(f"/api/videos/{vid_id}", headers=headers_a).status_code == 200

        # Verify User A's video list is now empty of that video
        list_a_after = client.get("/api/videos", headers=headers_a).json()
        assert vid_id not in [v["video_id"] for v in list_a_after["videos"]]

        # User B's video is still preserved
        list_b = client.get("/api/videos", headers=headers_b).json()
        assert TestAuthAndDataPrivacy.user_b_video_id in [v["video_id"] for v in list_b["videos"]]
