import unittest

from fastapi.testclient import TestClient

import backend.main as backend_main


class UATSmokeTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(backend_main.app)
        self.originals = {
            "get_db": backend_main.get_db,
            "create_user": backend_main.create_user,
            "authenticate_user": backend_main.authenticate_user,
            "get_user_by_id": backend_main.get_user_by_id,
            "get_current_user": backend_main.get_current_user,
        }

    def tearDown(self):
        backend_main.get_db = self.originals["get_db"]
        backend_main.create_user = self.originals["create_user"]
        backend_main.authenticate_user = self.originals["authenticate_user"]
        backend_main.get_user_by_id = self.originals["get_user_by_id"]
        backend_main.get_current_user = self.originals["get_current_user"]
        backend_main.app.dependency_overrides = {}

    def test_user_signup_login_and_profile_smoke_flow(self):
        async def fake_get_db():
            return object()

        async def fake_create_user(_db, username, _password, email):
            return {
                "_id": "user-123",
                "username": username,
                "email": email,
                "role": "user",
                "is_admin": False,
                "created_at": "2026-01-01T00:00:00",
                "updated_at": "2026-01-01T00:00:00",
            }

        async def fake_authenticate_user(_db, username, _password):
            return {
                "_id": "user-123",
                "username": username,
                "role": "user",
                "is_admin": False,
            }

        async def fake_get_user_by_id(_db, user_id):
            self.assertEqual(user_id, "user-123")
            return {
                "_id": "user-123",
                "username": "trader",
                "email": "trader@example.com",
                "role": "user",
                "is_admin": False,
                "created_at": "2026-01-01T00:00:00",
                "updated_at": "2026-01-01T00:00:00",
            }

        async def fake_current_user():
            return "user-123"

        backend_main.get_db = fake_get_db
        backend_main.create_user = fake_create_user
        backend_main.authenticate_user = fake_authenticate_user
        backend_main.get_user_by_id = fake_get_user_by_id
        backend_main.app.dependency_overrides[backend_main.get_current_user] = fake_current_user

        register_response = self.client.post(
            "/auth/register",
            json={"username": "trader", "password": "Trader123", "email": "trader@example.com"},
        )
        self.assertEqual(register_response.status_code, 200)
        register_payload = register_response.json()
        self.assertEqual(register_payload["username"], "trader")
        self.assertEqual(register_payload["role"], "user")

        login_response = self.client.post(
            "/auth/login",
            json={"username": "trader", "password": "Trader123"},
        )
        self.assertEqual(login_response.status_code, 200)
        login_payload = login_response.json()
        self.assertIn("access_token", login_payload)
        self.assertEqual(login_payload["username"], "trader")

        profile_response = self.client.get("/auth/profile")
        self.assertEqual(profile_response.status_code, 200)
        profile_payload = profile_response.json()
        self.assertEqual(profile_payload["username"], "trader")
        self.assertFalse(profile_payload["is_admin"])


if __name__ == "__main__":
    unittest.main()
