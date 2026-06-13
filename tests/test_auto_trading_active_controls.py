import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.routers import auto_trading_routes as routes


class FakeCursor:
    def __init__(self, docs):
        self.docs = list(docs)

    def sort(self, field, order):
        reverse = order == -1
        self.docs.sort(key=lambda doc: doc.get(field), reverse=reverse)
        return self

    async def to_list(self, length=None):
        if length is None:
            return list(self.docs)
        return list(self.docs)[:length]


class FakeCollection:
    def __init__(self, docs=None):
        self.docs = docs or []

    async def find_one(self, query):
        for doc in self.docs:
            if all(doc.get(k) == v for k, v in query.items()):
                return doc
        return None

    def find(self, query):
        status_filter = query.get("status", {}).get("$in", [])
        user_filter = query.get("user_id")
        rows = [
            doc
            for doc in self.docs
            if (user_filter is None or doc.get("user_id") == user_filter) and doc.get("status") in status_filter
        ]
        return FakeCursor(rows)

    async def update_one(self, query, update):
        target = await self.find_one(query)
        if not target:
            return
        for key, value in update.get("$set", {}).items():
            target[key] = value
        for key, value in update.get("$push", {}).items():
            target.setdefault(key, []).append(value)

    async def insert_one(self, payload):
        self.docs.append(payload)

    async def distinct(self, field, query=None):
        query = query or {}
        statuses = query.get("status", {}).get("$in")
        results = []
        for doc in self.docs:
            if statuses is not None and doc.get("status") not in statuses:
                continue
            if field in doc and doc[field] not in results:
                results.append(doc[field])
        return results


class FakeDB:
    def __init__(self, collection):
        self._collection = collection

    def __getitem__(self, name):
        if name != "auto_trades":
            raise KeyError(name)
        return self._collection


@pytest.fixture
def premium_subscription(monkeypatch):
    async def _premium_subscription(_db, _user):
        return {"tier": "premium"}

    monkeypatch.setattr(routes, "get_user_subscription", _premium_subscription)


@pytest.fixture
def app_factory():
    def _build_app(fake_db):
        app = FastAPI()

        async def _current_user():
            return "user-1"

        def _get_db():
            return fake_db

        app.include_router(routes.create_auto_trading_router(_current_user, _get_db))
        return app

    return _build_app


@pytest.mark.unit
def test_validate_stop_take_profit_buy_sell_rules():
    ok_buy = routes.validate_stop_take_profit("BUY", 90.0, 120.0, 100.0)
    ok_sell = routes.validate_stop_take_profit("SELL", 120.0, 90.0, 100.0)
    bad_buy = routes.validate_stop_take_profit("BUY", 105.0, 120.0, 100.0)
    bad_sell = routes.validate_stop_take_profit("SELL", 95.0, 90.0, 100.0)

    assert ok_buy is None
    assert ok_sell is None
    assert "BUY" in bad_buy
    assert "SELL" in bad_sell


@pytest.mark.unit
def test_adjust_stops_rejects_invalid_buy_levels(premium_subscription, app_factory, monkeypatch):
    trade = {
        "_id": "t1",
        "user_id": "user-1",
        "order_id": "ord-1",
        "symbol": "BTCUSDT",
        "action": "BUY",
        "status": "open",
        "quantity": 0.1,
        "stop_loss": 90.0,
        "take_profit": 110.0,
    }
    collection = FakeCollection([trade])
    app = app_factory(FakeDB(collection))
    client = TestClient(app)

    monkeypatch.setattr(routes, "get_current_market_price", lambda _symbol: 100.0)

    response = client.patch(
        "/api/auto-trading/trades/ord-1/stops",
        json={"stop_loss": 101.0, "take_profit": 120.0},
    )

    assert response.status_code == 400
    assert "BUY" in response.json().get("detail", "")


@pytest.mark.unit
def test_close_trade_retries_and_marks_closed(premium_subscription, app_factory, monkeypatch):
    trade = {
        "_id": "t2",
        "user_id": "user-1",
        "order_id": "ord-2",
        "symbol": "BTCUSDT",
        "action": "BUY",
        "status": "open",
        "quantity": 0.25,
    }
    collection = FakeCollection([trade])
    app = app_factory(FakeDB(collection))
    client = TestClient(app)

    def _mock_close_order(**_kwargs):
        return {"order_id": "close-123", "status": "FILLED"}, 2

    monkeypatch.setattr(routes, "place_market_order_with_retry", _mock_close_order)

    response = client.post("/api/auto-trading/trades/ord-2/close")

    assert response.status_code == 200
    payload = response.json()
    assert payload["close_order_status"] == "FILLED"
    assert payload["close_attempt_count"] == 2
    assert trade["status"] == "closed"


@pytest.mark.unit
def test_close_trade_partial_fill_marks_close_submitted(premium_subscription, app_factory, monkeypatch):
    trade = {
        "_id": "t3",
        "user_id": "user-1",
        "order_id": "ord-3",
        "symbol": "ETHUSDT",
        "action": "SELL",
        "status": "open",
        "quantity": 1.5,
    }
    collection = FakeCollection([trade])
    app = app_factory(FakeDB(collection))
    client = TestClient(app)

    def _mock_close_order(**_kwargs):
        return {"order_id": "close-456", "status": "PARTIALLY_FILLED"}, 1

    monkeypatch.setattr(routes, "place_market_order_with_retry", _mock_close_order)

    response = client.post("/api/auto-trading/trades/ord-3/close")

    assert response.status_code == 200
    payload = response.json()
    assert payload["close_order_status"] == "PARTIALLY_FILLED"
    assert "awaiting full fill" in payload["message"]
    assert trade["status"] == "close_submitted"


@pytest.mark.unit
def test_active_trades_response_includes_reconciliation_summary(premium_subscription, app_factory, monkeypatch):
    trade = {
        "_id": "t4",
        "user_id": "user-1",
        "order_id": "ord-4",
        "symbol": "BTCUSDT",
        "action": "BUY",
        "status": "open",
        "quantity": 0.2,
    }
    collection = FakeCollection([trade])
    app = app_factory(FakeDB(collection))
    client = TestClient(app)

    async def _mock_reconcile(_user, _db):
        return {"checked": 1, "updated": 1, "failed": 0}

    monkeypatch.setattr(routes, "reconcile_user_trade_statuses", _mock_reconcile)

    response = client.get("/api/auto-trading/user/active-trades")

    assert response.status_code == 200
    payload = response.json()
    assert payload["reconciliation"] == {"checked": 1, "updated": 1, "failed": 0}


@pytest.mark.unit
def test_manual_reconcile_endpoint_returns_result(premium_subscription, app_factory, monkeypatch):
    collection = FakeCollection([])
    app = app_factory(FakeDB(collection))
    client = TestClient(app)

    async def _mock_reconcile(_user, _db):
        return {"checked": 3, "updated": 2, "failed": 1}

    monkeypatch.setattr(routes, "reconcile_user_trade_statuses", _mock_reconcile)

    response = client.post("/api/auto-trading/trades/reconcile")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["result"] == {"checked": 3, "updated": 2, "failed": 1}


@pytest.mark.unit
def test_reconcile_all_active_trade_statuses_aggregates_user_results(monkeypatch):
    docs = [
        {"user_id": "u1", "status": "submitted"},
        {"user_id": "u1", "status": "open"},
        {"user_id": "u2", "status": "close_submitted"},
        {"user_id": "u3", "status": "closed"},
    ]
    collection = FakeCollection(docs)
    db = FakeDB(collection)

    async def _mock_reconcile_user(user_id, _db, max_trades=100):
        if user_id == "u2":
            return {"checked": 2, "updated": 1, "failed": 1}
        return {"checked": 1, "updated": 1, "failed": 0}

    monkeypatch.setattr(routes, "reconcile_user_trade_statuses", _mock_reconcile_user)

    result = asyncio.run(routes.reconcile_all_active_trade_statuses(db))

    assert result == {
        "users_checked": 2,
        "users_failed": 0,
        "checked": 3,
        "updated": 2,
        "failed": 1,
    }


@pytest.mark.unit
def test_detect_stale_trade_states_counts_aged_records():
    now = datetime.now(timezone.utc)
    docs = [
        {
            "user_id": "u1",
            "status": "submitted",
            "created_at": now - timedelta(minutes=40),
            "updated_at": now - timedelta(minutes=35),
        },
        {
            "user_id": "u2",
            "status": "close_submitted",
            "created_at": now - timedelta(minutes=30),
            "updated_at": now - timedelta(minutes=25),
        },
        {
            "user_id": "u3",
            "status": "submitted",
            "created_at": now - timedelta(minutes=5),
            "updated_at": now - timedelta(minutes=3),
        },
    ]
    db = FakeDB(FakeCollection(docs))

    result = asyncio.run(
        routes.detect_stale_trade_states(
            db,
            stale_seconds=20 * 60,
            max_records=100,
        )
    )

    assert result["stale_count"] == 2
    assert result["by_status"]["submitted"] == 1
    assert result["by_status"]["close_submitted"] == 1


@pytest.mark.unit
def test_reconciliation_metrics_endpoint_returns_runtime_snapshot(premium_subscription, app_factory):
    app = app_factory(FakeDB(FakeCollection([])))
    client = TestClient(app)

    routes.record_reconciliation_run(result={"users_checked": 1, "users_failed": 0, "checked": 2, "updated": 2, "failed": 0}, duration_seconds=0.1, stale_summary={"stale_count": 0})
    response = client.get("/api/auto-trading/trades/reconciliation/metrics")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "metrics" in payload
    assert "user_stale_summary" in payload
