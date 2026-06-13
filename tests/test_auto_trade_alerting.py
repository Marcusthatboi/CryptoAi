import types
import pytest

from backend import auto_trade_alerting as alerts


class DummyLogger:
    def warning(self, *_args, **_kwargs):
        return None


@pytest.fixture(autouse=True)
def _reset_alert_state():
    alerts._LAST_ALERT_SENT_AT.clear()
    alerts._INCIDENT_STATE.clear()


def test_dispatch_alert_sends_all_configured_channels():
    calls = {"webhook": 0, "platform": 0, "email": 0}

    def _mock_post(url, json, timeout):
        calls["webhook"] += 1
        return types.SimpleNamespace(status_code=200, text="ok")

    def _mock_platform(_platform, _data):
        calls["platform"] += 1

    def _mock_email(_to, _subject, _body, _reply_to):
        calls["email"] += 1

    result = alerts.dispatch_auto_trade_alert(
        alert_key="unit-all-channels",
        severity="warning",
        summary="summary",
        details={"a": 1},
        enabled=True,
        cooldown_seconds=1,
        webhook_url="https://example.test/webhook",
        platform="slack",
        email_to="ops@example.com",
        logger=DummyLogger(),
        requests_post=_mock_post,
        send_platform_fn=_mock_platform,
        send_email_fn=_mock_email,
    )

    assert result["sent"] is True
    assert calls == {"webhook": 1, "platform": 1, "email": 1}


def test_dispatch_alert_respects_cooldown():
    calls = {"webhook": 0}

    def _mock_post(url, json, timeout):
        calls["webhook"] += 1
        return types.SimpleNamespace(status_code=200, text="ok")

    first = alerts.dispatch_auto_trade_alert(
        alert_key="unit-cooldown",
        severity="warning",
        summary="summary",
        details={},
        enabled=True,
        cooldown_seconds=300,
        webhook_url="https://example.test/webhook",
        platform="",
        email_to="",
        logger=DummyLogger(),
        requests_post=_mock_post,
    )
    second = alerts.dispatch_auto_trade_alert(
        alert_key="unit-cooldown",
        severity="warning",
        summary="summary",
        details={},
        enabled=True,
        cooldown_seconds=300,
        webhook_url="https://example.test/webhook",
        platform="",
        email_to="",
        logger=DummyLogger(),
        requests_post=_mock_post,
    )

    assert first["sent"] is True
    assert second["suppressed"] is True
    assert calls["webhook"] == 1


def test_dispatch_alert_disabled_suppresses_send():
    calls = {"webhook": 0}

    def _mock_post(url, json, timeout):
        calls["webhook"] += 1
        return types.SimpleNamespace(status_code=200, text="ok")

    result = alerts.dispatch_auto_trade_alert(
        alert_key="unit-disabled",
        severity="warning",
        summary="summary",
        details={},
        enabled=False,
        cooldown_seconds=300,
        webhook_url="https://example.test/webhook",
        platform="",
        email_to="",
        logger=DummyLogger(),
        requests_post=_mock_post,
    )

    assert result["suppressed"] is True
    assert calls["webhook"] == 0


def test_process_incident_state_deduplicates_ongoing_and_sends_recovery():
    calls = {"webhook": 0}

    def _mock_post(url, json, timeout):
        calls["webhook"] += 1
        return types.SimpleNamespace(status_code=200, text="ok")

    opened = alerts.process_incident_state(
        incident_key="phase7-incident",
        is_active=True,
        active_severity="critical",
        active_summary="Incident active",
        active_details={"x": 1},
        enabled=True,
        cooldown_seconds=60,
        webhook_url="https://example.test/webhook",
        platform="",
        email_to="",
        logger=DummyLogger(),
        requests_post=_mock_post,
    )
    ongoing = alerts.process_incident_state(
        incident_key="phase7-incident",
        is_active=True,
        active_severity="critical",
        active_summary="Incident active",
        active_details={"x": 2},
        enabled=True,
        cooldown_seconds=60,
        webhook_url="https://example.test/webhook",
        platform="",
        email_to="",
        logger=DummyLogger(),
        requests_post=_mock_post,
    )
    recovered = alerts.process_incident_state(
        incident_key="phase7-incident",
        is_active=False,
        active_severity="critical",
        active_summary="Incident active",
        active_details={"x": 2},
        enabled=True,
        cooldown_seconds=60,
        webhook_url="https://example.test/webhook",
        platform="",
        email_to="",
        logger=DummyLogger(),
        requests_post=_mock_post,
        notify_on_recovery=True,
        recovery_summary="Incident recovered",
    )

    assert opened["event"] == "opened"
    assert ongoing["event"] == "ongoing_suppressed"
    assert ongoing["suppressed"] is True
    assert recovered["event"] == "recovered"
    assert calls["webhook"] == 2


def test_process_incident_state_recovery_noop_when_not_active():
    result = alerts.process_incident_state(
        incident_key="phase7-noop",
        is_active=False,
        active_severity="warning",
        active_summary="Incident active",
        active_details={},
        enabled=True,
        cooldown_seconds=60,
        webhook_url="",
        platform="",
        email_to="",
        logger=DummyLogger(),
    )

    assert result["event"] == "resolved_noop"
