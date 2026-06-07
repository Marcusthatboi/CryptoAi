import unittest
from typing import Any, Dict, List

from fastapi.testclient import TestClient

import backend.main as backend_main


class FakeFindCursor:
    def __init__(self, items: List[Dict[str, Any]]):
        self._items = items

    def sort(self, *_args, **_kwargs):
        return self

    async def to_list(self, length: int = 50):
        return self._items[:length]


class FakeUsersCollection:
    def __init__(self, items: List[Dict[str, Any]]):
        self._items = items
        self.last_query = None

    def find(self, query: Dict[str, Any]):
        self.last_query = query
        return FakeFindCursor(self._items)


class FakeSubscriptionsCollection:
    def __init__(self):
        self.last_update = None

    async def update_one(self, query: Dict[str, Any], update: Dict[str, Any]):
        self.last_update = {"query": query, "update": update}
        return type("Result", (), {"matched_count": 1})()


class FakeDB:
    def __init__(self, users: List[Dict[str, Any]]):
        self.users = FakeUsersCollection(users)
        self.subscriptions = FakeSubscriptionsCollection()

    def __getitem__(self, name: str):
        if name == "users":
            return self.users
        if name == "subscriptions":
            return self.subscriptions
        raise KeyError(name)


class AdminCustomerManagementTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(backend_main.app)
        self.originals = {
            "SUBSCRIPTION_AVAILABLE": backend_main.SUBSCRIPTION_AVAILABLE,
            "get_db": backend_main.get_db,
            "get_user_subscription": backend_main.get_user_subscription,
            "create_subscription": backend_main.create_subscription,
            "get_daily_signals_usage": backend_main.get_daily_signals_usage,
            "get_hourly_api_usage": backend_main.get_hourly_api_usage,
            "get_usage_limit": backend_main.get_usage_limit,
            "get_user_by_id": backend_main.get_user_by_id,
            "require_admin_user": backend_main.require_admin_user,
            "get_current_user": backend_main.get_current_user,
        }

        backend_main.SUBSCRIPTION_AVAILABLE = True

        self.user_docs = [
            {
                "_id": "user-1",
                "username": "alice",
                "email": "alice@example.com",
                "created_at": "2026-01-01T00:00:00",
                "updated_at": "2026-01-01T00:00:00",
                "portfolio": {"cash": 1200, "holdings": [{"symbol": "BTC"}], "total_value": 1500},
                "role": "user",
                "is_admin": False,
            },
            {
                "_id": "user-2",
                "username": "admin",
                "email": "admin@example.com",
                "created_at": "2026-01-02T00:00:00",
                "updated_at": "2026-01-02T00:00:00",
                "portfolio": {"cash": 800, "holdings": [], "total_value": 800},
                "role": "admin",
                "is_admin": True,
            },
        ]
        self.fake_db = FakeDB(self.user_docs)

        async def fake_get_db():
            return self.fake_db

        async def fake_get_subscription(_db, user_id):
            return {
                "user_id": user_id,
                "tier": "premium" if user_id == "user-2" else "free",
                "status": "active",
                "stripe_customer_id": None,
                "stripe_subscription_id": None,
                "cancel_at_period_end": False,
            }

        async def fake_create_subscription(_db, user_id, tier):
            return {
                "user_id": user_id,
                "tier": tier,
                "status": "active",
                "cancel_at_period_end": False,
            }

        async def fake_daily_usage(_db, user_id, _date_key):
            return 9 if user_id == "user-1" else 1

        async def fake_hourly_usage(_db, user_id, _hour_key):
            return 17 if user_id == "user-1" else 2

        def fake_usage_limit(tier, limit_type):
            values = {
                "free": {"signals_per_day": 10, "api_calls_per_hour": 20},
                "premium": {"signals_per_day": None, "api_calls_per_hour": 1000},
            }
            return values.get(tier, {}).get(limit_type)

        async def fake_get_user_by_id(_db, user_id):
            for user in self.user_docs:
                if user["_id"] == user_id:
                    return user
            return None

        async def fake_admin_user():
            return {"username": "Admin", "role": "admin", "is_admin": True}

        backend_main.get_db = fake_get_db
        backend_main.get_user_subscription = fake_get_subscription
        backend_main.create_subscription = fake_create_subscription
        backend_main.get_daily_signals_usage = fake_daily_usage
        backend_main.get_hourly_api_usage = fake_hourly_usage
        backend_main.get_usage_limit = fake_usage_limit
        backend_main.get_user_by_id = fake_get_user_by_id
        backend_main.app.dependency_overrides[backend_main.require_admin_user] = fake_admin_user

    def tearDown(self):
        backend_main.SUBSCRIPTION_AVAILABLE = self.originals["SUBSCRIPTION_AVAILABLE"]
        backend_main.get_db = self.originals["get_db"]
        backend_main.get_user_subscription = self.originals["get_user_subscription"]
        backend_main.create_subscription = self.originals["create_subscription"]
        backend_main.get_daily_signals_usage = self.originals["get_daily_signals_usage"]
        backend_main.get_hourly_api_usage = self.originals["get_hourly_api_usage"]
        backend_main.get_usage_limit = self.originals["get_usage_limit"]
        backend_main.get_user_by_id = self.originals["get_user_by_id"]
        backend_main.get_current_user = self.originals["get_current_user"]
        backend_main.app.dependency_overrides = {}

    def test_admin_customers_returns_customer_summaries(self):
        response = self.client.get("/api/admin/customers")
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertEqual(payload["count"], 2)
        self.assertEqual(payload["requested_by"], "Admin")
        first_customer = payload["customers"][0]
        self.assertIn("usage", first_customer)
        self.assertIn("portfolio", first_customer)
        self.assertIn("subscription", first_customer)

    def test_admin_customers_filters_by_tier(self):
        response = self.client.get("/api/admin/customers", params={"tier": "premium"})
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["customers"][0]["subscription"]["tier"], "premium")

    def test_admin_customers_supports_search_query(self):
        response = self.client.get("/api/admin/customers", params={"search": "alice"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.fake_db.users.last_query,
            {
                "$or": [
                    {"username": {"$regex": "alice", "$options": "i"}},
                    {"email": {"$regex": "alice", "$options": "i"}},
                ]
            },
        )

    def test_admin_customer_update_rejects_invalid_tier(self):
        response = self.client.patch("/api/admin/customers/user-1/subscription", json={"tier": "vip"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid subscription tier", response.json()["detail"])

    def test_admin_customer_update_persists_subscription_change(self):
        response = self.client.patch(
            "/api/admin/customers/user-1/subscription",
            json={"tier": "pro", "status": "cancelled"},
        )
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertEqual(payload["updated_by"], "Admin")
        self.assertEqual(self.fake_db.subscriptions.last_update["query"], {"user_id": "user-1"})
        self.assertEqual(self.fake_db.subscriptions.last_update["update"]["$set"]["tier"], "pro")
        self.assertTrue(self.fake_db.subscriptions.last_update["update"]["$set"]["cancel_at_period_end"])

    def test_admin_user_detection_supports_role_flag_and_username_fallback(self):
        self.assertTrue(backend_main.user_is_admin({"role": "admin"}))
        self.assertTrue(backend_main.user_is_admin({"is_admin": True}))
        self.assertTrue(backend_main.user_is_admin({"username": "Admin"}))
        self.assertFalse(backend_main.user_is_admin({"username": "alice", "role": "user"}))


if __name__ == "__main__":
    unittest.main()
