import unittest
from fastapi.testclient import TestClient
from app.main import app

from app.core.config import settings

settings.allow_dev_auth = True
settings.app_env = "testing"
client = TestClient(app, headers={"Authorization": "Bearer test_dev_token"})


class TestBluCareAPI(unittest.TestCase):

    def test_health_probes(self):
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")

        ready_resp = client.get("/health/ready")
        self.assertEqual(ready_resp.status_code, 200)
        self.assertIn("qdrant", ready_resp.json())

    def test_legacy_start_session(self):
        response = client.post("/session/start", json={})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("thread_id", data)
        self.assertIn("message", data)

    def test_api_v1_start_session(self):
        response = client.post("/api/v1/session/start", json={"initial_message": "Hi, I have a fever."})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("thread_id", data)
        self.assertIn("message", data)

    def test_api_v1_list_sessions(self):
        response = client.get("/api/v1/session/list")
        self.assertEqual(response.status_code, 200)
        self.assertIn("sessions", response.json())

    def test_api_v1_nearby_ambulances(self):
        from unittest.mock import patch
        with patch(
            "app.facilities.service.HospitalScraper.scrape_facilities",
            return_value=[
                {
                    "name": "Test Hospital",
                    "latitude": 18.52,
                    "longitude": 73.85,
                    "facility_type": "hospital",
                    "phone": "+91 98765 43210",
                    "emergency": "yes",
                    "source_url": "https://maps.google.com/?cid=123",
                }
            ],
        ):
            response = client.get("/api/v1/hospitals/nearby?lat=18.5204&lng=73.8567")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["latitude"], 18.5204)
            self.assertIn("external_search", data)
            self.assertIn("google_maps", data["external_search"])
            self.assertGreater(len(data["providers"]), 0)

    def test_api_v1_user_profile(self):
        get_resp = client.get("/api/v1/user/profile")
        self.assertEqual(get_resp.status_code, 200)
        self.assertIn("email", get_resp.json())

        put_resp = client.put("/api/v1/user/profile", json={"name": "Test Patient"})
        self.assertEqual(put_resp.status_code, 200)
        self.assertEqual(put_resp.json()["name"], "Test Patient")

    def test_api_v1_user_settings(self):
        get_resp = client.get("/api/v1/user/settings")
        self.assertEqual(get_resp.status_code, 200)
        self.assertIn("selectedProtocol", get_resp.json())

    def test_message_validation(self):
        long_message = "A" * 3000
        response = client.post("/api/v1/session/message", json={"thread_id": "1234", "message": long_message})
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
