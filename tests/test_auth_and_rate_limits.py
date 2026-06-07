import unittest
from copy import deepcopy

from fastapi.testclient import TestClient

import backend.main as backend_main


class AuthAndRateLimitTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(backend_main.app)
        self.originals = {
            "get_db": backend_main.get_db,
            "authenticate_user": backend_main.authenticate_user,
            "get_user_by_id": backend_main.get_user_by_id,
            "resolve_optional_user_id": backend_main.resolve_optional_user_id,
            "rate_limit_buckets": backend_main.rate_limit_buckets,
            "RATE_LIMIT_WINDOWS": deepcopy(backend_main.RATE_LIMIT_WINDOWS),
            "generate_ai_response": backend_main.generate_ai_response,
        }
        backend_main.rate_limit_buckets.clear()

    def tearDown(self):
        backend_main.get_db = self.originals["get_db"]
        backend_main.authenticate_user = self.originals["authenticate_user"]
        backend_main.get_user_by_id = self.originals["get_user_by_id"]
        backend_main.resolve_optional_user_id = self.originals["resolve_optional_user_id"]
        backend_main.RATE_LIMIT_WINDOWS = self.originals["RATE_LIMIT_WINDOWS"]
        backend_main.generate_ai_response = self.originals["generate_ai_response"]
        backend_main.rate_limit_buckets.clear()
        backend_main.app.dependency_overrides = {}

    def test_login_response_includes_admin_metadata(self):
        async def fake_get_db():
            return object()

        async def fake_authenticate_user(_db, username, password):
            return {
                "_id": "admin-user",
                "username": username,
                "role": "admin",
                "is_admin": True,
                "password": password,
            }

        backend_main.get_db = fake_get_db
        backend_main.authenticate_user = fake_authenticate_user

        response = self.client.post("/auth/login", json={"username": "Admin", "password": "Admin1"})
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertTrue(payload["is_admin"])
        self.assertEqual(payload["role"], "admin")
        self.assertEqual(payload["username"], "Admin")

    def test_profile_response_includes_admin_metadata(self):
        async def fake_current_user():
            return "admin-user"

        async def fake_get_db():
            return object()

        async def fake_get_user_by_id(_db, user_id):
            self.assertEqual(user_id, "admin-user")
            return {
                "_id": "admin-user",
                "username": "Admin",
                "email": "admin@example.com",
                "role": "admin",
                "is_admin": True,
                "created_at": "2026-01-01T00:00:00",
                "updated_at": "2026-01-01T00:00:00",
            }

        backend_main.get_db = fake_get_db
        backend_main.get_user_by_id = fake_get_user_by_id
        backend_main.app.dependency_overrides[backend_main.get_current_user] = fake_current_user

        response = self.client.get("/auth/profile")
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertTrue(payload["is_admin"])
        self.assertEqual(payload["role"], "admin")

    def test_chat_rate_limit_returns_429_after_threshold(self):
        async def fake_optional_user_id(_authorization=None):
            return "load-test-user"

        backend_main.resolve_optional_user_id = fake_optional_user_id
        backend_main.generate_ai_response = lambda *_args, **_kwargs: "ok"
        backend_main.RATE_LIMIT_WINDOWS["chat"] = {"limit": 3, "window_seconds": 3600}

        last_response = None
        for _ in range(backend_main.RATE_LIMIT_WINDOWS["chat"]["limit"]):
            last_response = self.client.post(
                "/api/chat",
                json={"message": "hello", "context": "crypto"},
                headers={"Authorization": "Bearer fake"},
            )
            self.assertEqual(last_response.status_code, 200)

        limited_response = self.client.post(
            "/api/chat",
            json={"message": "hello", "context": "crypto"},
            headers={"Authorization": "Bearer fake"},
        )
        self.assertEqual(limited_response.status_code, 429)
        self.assertIn("Retry-After", limited_response.headers)
        self.assertIn("Rate limit exceeded for chat", limited_response.json()["detail"])

    def test_missing_auth_header_is_rejected(self):
        response = self.client.get("/auth/profile")
        self.assertEqual(response.status_code, 401)
        self.assertIn("Missing authorization header", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
