import unittest
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy

from fastapi.testclient import TestClient

import backend.main as backend_main


class SecurityAndLoadTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(backend_main.app)
        self.originals = {
            "resolve_optional_user_id": backend_main.resolve_optional_user_id,
            "generate_ai_response": backend_main.generate_ai_response,
            "RATE_LIMIT_WINDOWS": deepcopy(backend_main.RATE_LIMIT_WINDOWS),
            "get_db": backend_main.get_db,
            "get_user_by_id": backend_main.get_user_by_id,
            "get_current_user": backend_main.get_current_user,
        }
        backend_main.rate_limit_buckets.clear()

    def tearDown(self):
        backend_main.resolve_optional_user_id = self.originals["resolve_optional_user_id"]
        backend_main.generate_ai_response = self.originals["generate_ai_response"]
        backend_main.RATE_LIMIT_WINDOWS = self.originals["RATE_LIMIT_WINDOWS"]
        backend_main.get_db = self.originals["get_db"]
        backend_main.get_user_by_id = self.originals["get_user_by_id"]
        backend_main.get_current_user = self.originals["get_current_user"]
        backend_main.rate_limit_buckets.clear()
        backend_main.app.dependency_overrides = {}

    def test_admin_analytics_blocks_non_admin_users(self):
        async def fake_current_user():
            return "regular-user"

        async def fake_get_db():
            return object()

        async def fake_get_user_by_id(_db, _user_id):
            return {"username": "regular", "role": "user", "is_admin": False}

        backend_main.app.dependency_overrides[backend_main.get_current_user] = fake_current_user
        backend_main.get_db = fake_get_db
        backend_main.get_user_by_id = fake_get_user_by_id

        response = self.client.get("/api/subscription/analytics/overview")
        self.assertEqual(response.status_code, 403)
        self.assertIn("Admin access required", response.json().get("detail", ""))

    def test_chat_burst_load_enforces_rate_limit_under_concurrency(self):
        async def fake_optional_user_id(_authorization=None):
            return "burst-user"

        backend_main.resolve_optional_user_id = fake_optional_user_id
        backend_main.generate_ai_response = lambda *_args, **_kwargs: "ok"
        backend_main.RATE_LIMIT_WINDOWS["chat"] = {"limit": 6, "window_seconds": 3600}

        def send_chat_request():
            response = self.client.post(
                "/api/chat",
                json={"message": "load test ping", "context": "crypto"},
                headers={"Authorization": "Bearer fake"},
            )
            return response.status_code

        with ThreadPoolExecutor(max_workers=12) as executor:
            status_codes = list(executor.map(lambda _x: send_chat_request(), range(30)))

        allowed = status_codes.count(200)
        limited = status_codes.count(429)

        self.assertGreater(allowed, 0)
        self.assertGreater(limited, 0)
        self.assertLessEqual(allowed, 6)


if __name__ == "__main__":
    unittest.main()
