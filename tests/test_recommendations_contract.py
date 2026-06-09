import unittest

import pandas as pd
from fastapi.testclient import TestClient

import backend.main as backend_main


class RecommendationsContractTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(backend_main.app)
        self.originals = {
            "SUBSCRIPTION_AVAILABLE": backend_main.SUBSCRIPTION_AVAILABLE,
            "resolve_optional_user_id": backend_main.resolve_optional_user_id,
            "resolve_subscription_tier": backend_main.resolve_subscription_tier,
            "enforce_rate_limit": backend_main.enforce_rate_limit,
            "check_ollama_health": backend_main.check_ollama_health,
            "load_price_data": backend_main.load_price_data,
            "analyze_multiple_trends": backend_main.analyze_multiple_trends,
            "build_top_recommendation_universe": backend_main.build_top_recommendation_universe,
        }

        backend_main.SUBSCRIPTION_AVAILABLE = False

        async def fake_user_id(_authorization=None):
            return None

        async def fake_tier(_authorization=None):
            return "free"

        async def fake_enforce_rate_limit(_feature, _actor):
            return None

        backend_main.resolve_optional_user_id = fake_user_id
        backend_main.resolve_subscription_tier = fake_tier
        backend_main.enforce_rate_limit = fake_enforce_rate_limit
        backend_main.check_ollama_health = lambda: False

        backend_main.load_price_data = lambda _path: pd.DataFrame(
            [
                {"id": "bitcoin", "price": 50000, "timestamp": pd.Timestamp("2026-01-01T00:00:00")},
                {"id": "ethereum", "price": 2500, "timestamp": pd.Timestamp("2026-01-01T00:00:00")},
                {"id": "dogecoin", "price": 0.1, "timestamp": pd.Timestamp("2026-01-01T00:00:00")},
            ]
        )

        backend_main.analyze_multiple_trends = lambda _df, sma_window=5: [
            {
                "crypto_id": "bitcoin",
                "price_change_percent": 2.1,
                "trend": "UPTREND",
                "current_price": 50000,
            },
            {
                "crypto_id": "ethereum",
                "price_change_percent": 1.2,
                "trend": "UPTREND",
                "current_price": 2500,
            },
            {
                "crypto_id": "dogecoin",
                "price_change_percent": 5.3,
                "trend": "UPTREND",
                "current_price": 0.1,
            },
        ]

    def tearDown(self):
        backend_main.SUBSCRIPTION_AVAILABLE = self.originals["SUBSCRIPTION_AVAILABLE"]
        backend_main.resolve_optional_user_id = self.originals["resolve_optional_user_id"]
        backend_main.resolve_subscription_tier = self.originals["resolve_subscription_tier"]
        backend_main.enforce_rate_limit = self.originals["enforce_rate_limit"]
        backend_main.check_ollama_health = self.originals["check_ollama_health"]
        backend_main.load_price_data = self.originals["load_price_data"]
        backend_main.analyze_multiple_trends = self.originals["analyze_multiple_trends"]
        backend_main.build_top_recommendation_universe = self.originals["build_top_recommendation_universe"]

    def test_recommendations_response_contains_required_shape(self):
        async def fake_universe(limit=10):
            return [
                {"crypto_id": "bitcoin", "symbol": "BTC", "score": 99.0, "sources": ["coingecko"]},
                {"crypto_id": "ethereum", "symbol": "ETH", "score": 88.0, "sources": ["coingecko"]},
            ]

        backend_main.build_top_recommendation_universe = fake_universe

        response = self.client.get("/api/recommendations", params={"count": 5})
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertIn("recommendations", payload)
        self.assertIn("candidate_universe", payload)
        self.assertIn("reasoning", payload)
        self.assertIn("risk_level", payload)

    def test_recommendations_are_clamped_to_top_universe_symbols(self):
        async def fake_universe(limit=10):
            return [
                {"crypto_id": "bitcoin", "symbol": "BTC", "score": 99.0, "sources": ["coingecko"]},
                {"crypto_id": "ethereum", "symbol": "ETH", "score": 88.0, "sources": ["coingecko"]},
            ]

        backend_main.build_top_recommendation_universe = fake_universe

        response = self.client.get("/api/recommendations", params={"count": 10})
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        universe_symbols = {str(item.get("symbol", "")).upper() for item in payload.get("candidate_universe", [])}
        recommendation_symbols = {str(item.get("symbol", "")).upper() for item in payload.get("recommendations", [])}

        self.assertTrue(universe_symbols)
        self.assertTrue(recommendation_symbols.issubset(universe_symbols))


if __name__ == "__main__":
    unittest.main()
