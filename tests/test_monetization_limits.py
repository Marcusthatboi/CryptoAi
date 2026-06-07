import unittest
from typing import Any, Dict, List

import pandas as pd
from fastapi import HTTPException
from fastapi.testclient import TestClient

import backend.main as backend_main


class AsyncIterList:
    def __init__(self, items: List[Dict[str, Any]]):
        self.items = items

    def __aiter__(self):
        self._idx = 0
        return self

    async def __anext__(self):
        if self._idx >= len(self.items):
            raise StopAsyncIteration
        item = self.items[self._idx]
        self._idx += 1
        return item


class FakeAggregateCursor:
    def __init__(self, items: List[Dict[str, Any]]):
        self._items = items
        self._idx = 0

    def __aiter__(self):
        self._idx = 0
        return self

    async def __anext__(self):
        if self._idx >= len(self._items):
            raise StopAsyncIteration
        item = self._items[self._idx]
        self._idx += 1
        return item

    async def to_list(self, length: int = 1):
        return self._items[:length]


class FakeCollection:
    def __init__(self, aggregate_items: List[Dict[str, Any]] = None, count_value: int = 0):
        self._aggregate_items = aggregate_items or []
        self._count_value = count_value

    def aggregate(self, pipeline):
        return FakeAggregateCursor(self._aggregate_items)

    async def count_documents(self, query):
        return self._count_value


class FakeDB:
    def __init__(self):
        self._collections = {
            "subscriptions": FakeCollection(
                aggregate_items=[{"_id": "free", "count": 2}, {"_id": "pro", "count": 1}],
                count_value=1,
            ),
            "usage_counters": FakeCollection(count_value=3),
            "usage_counters_hourly": FakeCollection(count_value=2),
        }

    def __getitem__(self, name: str):
        return self._collections[name]


class MonetizationLimitsTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(backend_main.app)
        self.originals = {
            "SUBSCRIPTION_AVAILABLE": backend_main.SUBSCRIPTION_AVAILABLE,
            "resolve_optional_user_id": backend_main.resolve_optional_user_id,
            "resolve_subscription_tier": backend_main.resolve_subscription_tier,
            "get_usage_limit": backend_main.get_usage_limit,
            "get_daily_signals_usage": backend_main.get_daily_signals_usage,
            "increment_daily_signals_usage": backend_main.increment_daily_signals_usage,
            "get_hourly_api_usage": backend_main.get_hourly_api_usage,
            "increment_hourly_api_usage": backend_main.increment_hourly_api_usage,
            "get_db": backend_main.get_db,
            "load_price_data": backend_main.load_price_data,
            "analyze_multiple_trends": backend_main.analyze_multiple_trends,
            "check_ollama_health": backend_main.check_ollama_health,
            "get_user_subscription": backend_main.get_user_subscription,
            "create_subscription": backend_main.create_subscription,
            "get_user_by_id": backend_main.get_user_by_id,
            "require_admin_user": backend_main.require_admin_user,
            "get_current_user": backend_main.get_current_user,
        }

        backend_main.SUBSCRIPTION_AVAILABLE = True

        async def fake_user_id(_authorization=None):
            return "user-1"

        async def fake_tier(_authorization=None):
            return "free"

        def fake_get_usage_limit(_tier, limit_type):
            limits = {
                "signals_per_day": 10,
                "api_calls_per_hour": 20,
                "history_days": 0,
            }
            return limits.get(limit_type)

        async def fake_get_db():
            return FakeDB()

        async def fake_get_subscription(_db, _user_id):
            return {"tier": "free", "status": "active"}

        async def fake_create_subscription(_db, user_id, tier):
            return {"user_id": user_id, "tier": tier, "status": "active"}

        backend_main.resolve_optional_user_id = fake_user_id
        backend_main.resolve_subscription_tier = fake_tier
        backend_main.get_usage_limit = fake_get_usage_limit
        backend_main.get_db = fake_get_db
        backend_main.get_user_subscription = fake_get_subscription
        backend_main.create_subscription = fake_create_subscription

        backend_main.load_price_data = lambda _path: pd.DataFrame(
            [{"id": "bitcoin", "price": 50000, "timestamp": pd.Timestamp("2026-01-01T00:00:00")}]
        )
        backend_main.analyze_multiple_trends = lambda _df, sma_window=5: [
            {
                "crypto_id": "bitcoin",
                "price_change_percent": 2.5,
                "trend": "UPTREND",
                "current_price": 50000,
            }
        ]
        backend_main.check_ollama_health = lambda: False

        async def noop_increment(*args, **kwargs):
            return None

        backend_main.increment_daily_signals_usage = noop_increment
        backend_main.increment_hourly_api_usage = noop_increment

    def tearDown(self):
        backend_main.SUBSCRIPTION_AVAILABLE = self.originals["SUBSCRIPTION_AVAILABLE"]
        backend_main.resolve_optional_user_id = self.originals["resolve_optional_user_id"]
        backend_main.resolve_subscription_tier = self.originals["resolve_subscription_tier"]
        backend_main.get_usage_limit = self.originals["get_usage_limit"]
        backend_main.get_daily_signals_usage = self.originals["get_daily_signals_usage"]
        backend_main.increment_daily_signals_usage = self.originals["increment_daily_signals_usage"]
        backend_main.get_hourly_api_usage = self.originals["get_hourly_api_usage"]
        backend_main.increment_hourly_api_usage = self.originals["increment_hourly_api_usage"]
        backend_main.get_db = self.originals["get_db"]
        backend_main.load_price_data = self.originals["load_price_data"]
        backend_main.analyze_multiple_trends = self.originals["analyze_multiple_trends"]
        backend_main.check_ollama_health = self.originals["check_ollama_health"]
        backend_main.get_user_subscription = self.originals["get_user_subscription"]
        backend_main.create_subscription = self.originals["create_subscription"]
        backend_main.get_user_by_id = self.originals["get_user_by_id"]
        backend_main.require_admin_user = self.originals["require_admin_user"]
        backend_main.get_current_user = self.originals["get_current_user"]
        backend_main.app.dependency_overrides = {}

    def test_recommendations_daily_limit_returns_403_and_retry_after(self):
        async def daily_exhausted(_db, _user_id, _date_key):
            return 10

        async def hourly_ok(_db, _user_id, _hour_key):
            return 0

        backend_main.get_daily_signals_usage = daily_exhausted
        backend_main.get_hourly_api_usage = hourly_ok

        response = self.client.get(
            "/api/recommendations",
            params={"count": 5},
            headers={"Authorization": "Bearer fake"},
        )

        self.assertEqual(response.status_code, 403)
        self.assertIn("Retry-After", response.headers)
        self.assertIn("daily signal limit", response.json().get("detail", ""))

    def test_recommendations_hourly_limit_returns_429_and_retry_after(self):
        async def daily_ok(_db, _user_id, _date_key):
            return 0

        async def hourly_exhausted(_db, _user_id, _hour_key):
            return 20

        backend_main.get_daily_signals_usage = daily_ok
        backend_main.get_hourly_api_usage = hourly_exhausted

        response = self.client.get(
            "/api/recommendations",
            params={"count": 5},
            headers={"Authorization": "Bearer fake"},
        )

        self.assertEqual(response.status_code, 429)
        self.assertIn("Retry-After", response.headers)
        self.assertIn("hourly API limit", response.json().get("detail", ""))

    def test_recommendations_success_includes_reset_metadata(self):
        async def daily_ok(_db, _user_id, _date_key):
            return 1

        async def hourly_ok(_db, _user_id, _hour_key):
            return 1

        backend_main.get_daily_signals_usage = daily_ok
        backend_main.get_hourly_api_usage = hourly_ok

        response = self.client.get(
            "/api/recommendations",
            params={"count": 2},
            headers={"Authorization": "Bearer fake"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("daily_reset_at", payload)
        self.assertIn("hourly_reset_at", payload)
        self.assertIn("api_calls_used_this_hour", payload)
        self.assertIn("signals_used_today", payload)

    def test_usage_summary_includes_reset_metadata(self):
        async def fake_current_user():
            return "user-1"

        async def daily_usage(_db, _user_id, _date_key):
            return 4

        async def hourly_usage(_db, _user_id, _hour_key):
            return 3

        backend_main.app.dependency_overrides[backend_main.get_current_user] = fake_current_user
        backend_main.get_daily_signals_usage = daily_usage
        backend_main.get_hourly_api_usage = hourly_usage

        response = self.client.get("/api/subscription/usage-summary")
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertIn("daily_reset_at", payload)
        self.assertIn("hourly_reset_at", payload)
        self.assertIn("api_calls_used_this_hour", payload)
        self.assertEqual(payload.get("signals_used_today"), 4)

    def test_admin_analytics_forbidden_for_non_admin(self):
        async def fake_current_user():
            return "user-2"

        async def fake_get_db_for_admin_check():
            return FakeDB()

        async def fake_get_user_by_id(_db, _user_id):
            return {"username": "regular_user"}

        backend_main.app.dependency_overrides[backend_main.get_current_user] = fake_current_user
        backend_main.get_db = fake_get_db_for_admin_check
        backend_main.get_user_by_id = fake_get_user_by_id

        response = self.client.get("/api/subscription/analytics/overview")
        self.assertEqual(response.status_code, 403)

    def test_admin_analytics_success_for_admin(self):
        async def fake_admin_user():
            return {"username": "Admin"}

        backend_main.app.dependency_overrides[backend_main.require_admin_user] = fake_admin_user

        response = self.client.get("/api/subscription/analytics/overview")
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertIn("subscriptions", payload)
        self.assertIn("usage", payload)
        self.assertIn("window_days", payload)


if __name__ == "__main__":
    unittest.main()
