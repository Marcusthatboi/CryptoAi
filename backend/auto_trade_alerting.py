"""Alert dispatch helpers for auto-trade reconciliation monitoring."""

from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional

import requests

from backend.collaboration_integrations import send_to_platform
from backend.support_email import send_email


_LAST_ALERT_SENT_AT: Dict[str, float] = {}
_INCIDENT_STATE: Dict[str, Dict[str, Any]] = {}


def should_send_alert(alert_key: str, cooldown_seconds: int, *, now_timestamp: Optional[float] = None) -> bool:
    """Return True if alert key is outside cooldown window and can be emitted."""
    if cooldown_seconds <= 0:
        return True

    now_ts = float(now_timestamp) if now_timestamp is not None else datetime.now(timezone.utc).timestamp()
    last_ts = _LAST_ALERT_SENT_AT.get(alert_key)
    if last_ts is not None and (now_ts - last_ts) < float(cooldown_seconds):
        return False

    _LAST_ALERT_SENT_AT[alert_key] = now_ts
    return True


def dispatch_auto_trade_alert(
    *,
    alert_key: str,
    severity: str,
    summary: str,
    details: Dict[str, Any],
    enabled: bool,
    cooldown_seconds: int,
    webhook_url: str,
    platform: str,
    email_to: str,
    logger,
    requests_post: Callable[..., Any] = requests.post,
    send_platform_fn: Callable[[str, Dict[str, Any]], None] = send_to_platform,
    send_email_fn: Callable[[str, str, str, str], None] = send_email,
) -> Dict[str, Any]:
    """Dispatch an auto-trade alert through configured channels with cooldown protection."""
    result: Dict[str, Any] = {
        "sent": False,
        "suppressed": False,
        "channels": [],
        "errors": [],
    }

    if not enabled:
        result["suppressed"] = True
        return result

    if not should_send_alert(alert_key, cooldown_seconds):
        result["suppressed"] = True
        return result

    now_iso = datetime.now(timezone.utc).isoformat()
    severity_label = str(severity or "warning").upper()
    title = f"CryptoAI Auto-Trade Alert [{severity_label}]"
    detail_lines = [f"{key}: {value}" for key, value in (details or {}).items()]
    detail_text = "\n".join(detail_lines) if detail_lines else "No details"
    body = f"{title}\n\n{summary}\n\n{detail_text}\n\nTimestamp: {now_iso}"

    if webhook_url:
        try:
            response = requests_post(
                webhook_url,
                json={
                    "title": title,
                    "severity": severity_label,
                    "summary": summary,
                    "details": details,
                    "timestamp": now_iso,
                },
                timeout=8,
            )
            if getattr(response, "status_code", 500) >= 300:
                raise RuntimeError(f"status={getattr(response, 'status_code', 'unknown')} body={getattr(response, 'text', '')}")
            result["channels"].append("webhook")
        except Exception as exc:
            result["errors"].append(f"webhook:{exc}")
            logger.warning("Auto-trade webhook alert failed: %s", exc)

    if platform:
        try:
            send_platform_fn(
                platform,
                {
                    "title": title,
                    "summary": f"{summary}\n{detail_text}",
                    "symbol": "AUTOTRADE",
                    "url": "",
                    "requested_by": "system",
                },
            )
            result["channels"].append(f"platform:{platform}")
        except Exception as exc:
            result["errors"].append(f"platform:{exc}")
            logger.warning("Auto-trade platform alert failed (%s): %s", platform, exc)

    if email_to:
        try:
            send_email_fn(
                email_to,
                title,
                body,
                "",
            )
            result["channels"].append("email")
        except Exception as exc:
            result["errors"].append(f"email:{exc}")
            logger.warning("Auto-trade email alert failed: %s", exc)

    result["sent"] = bool(result["channels"])
    return result


def get_incident_state_snapshot() -> Dict[str, Dict[str, Any]]:
    """Return a shallow copy of in-memory incident state."""
    return {key: dict(value) for key, value in _INCIDENT_STATE.items()}


def process_incident_state(
    *,
    incident_key: str,
    is_active: bool,
    active_severity: str,
    active_summary: str,
    active_details: Dict[str, Any],
    enabled: bool,
    cooldown_seconds: int,
    webhook_url: str,
    platform: str,
    email_to: str,
    logger,
    notify_on_recovery: bool = True,
    recovery_severity: str = "info",
    recovery_summary: Optional[str] = None,
    requests_post: Callable[..., Any] = requests.post,
    send_platform_fn: Callable[[str, Dict[str, Any]], None] = send_to_platform,
    send_email_fn: Callable[[str, str, str, str], None] = send_email,
) -> Dict[str, Any]:
    """Emit opening/recovery alerts while deduplicating ongoing incident alerts."""
    now_iso = datetime.now(timezone.utc).isoformat()
    state = _INCIDENT_STATE.get(incident_key, {
        "active": False,
        "opened_at": None,
        "closed_at": None,
        "last_change_at": None,
        "last_details": None,
    })
    was_active = bool(state.get("active"))

    if is_active:
        state["last_details"] = dict(active_details or {})
        if was_active:
            state["last_change_at"] = state.get("last_change_at") or now_iso
            _INCIDENT_STATE[incident_key] = state
            return {
                "event": "ongoing_suppressed",
                "incident_key": incident_key,
                "sent": False,
                "suppressed": True,
            }

        state["active"] = True
        state["opened_at"] = now_iso
        state["closed_at"] = None
        state["last_change_at"] = now_iso
        _INCIDENT_STATE[incident_key] = state

        dispatch_result = dispatch_auto_trade_alert(
            alert_key=f"incident:{incident_key}:open",
            severity=active_severity,
            summary=active_summary,
            details={**(active_details or {}), "incident_key": incident_key, "incident_event": "opened"},
            enabled=enabled,
            cooldown_seconds=cooldown_seconds,
            webhook_url=webhook_url,
            platform=platform,
            email_to=email_to,
            logger=logger,
            requests_post=requests_post,
            send_platform_fn=send_platform_fn,
            send_email_fn=send_email_fn,
        )
        dispatch_result["event"] = "opened"
        dispatch_result["incident_key"] = incident_key
        return dispatch_result

    state["last_details"] = dict(active_details or state.get("last_details") or {})
    if not was_active:
        state["active"] = False
        state["last_change_at"] = state.get("last_change_at") or now_iso
        _INCIDENT_STATE[incident_key] = state
        return {
            "event": "resolved_noop",
            "incident_key": incident_key,
            "sent": False,
            "suppressed": False,
        }

    state["active"] = False
    state["closed_at"] = now_iso
    state["last_change_at"] = now_iso
    _INCIDENT_STATE[incident_key] = state

    if not notify_on_recovery:
        return {
            "event": "resolved_suppressed",
            "incident_key": incident_key,
            "sent": False,
            "suppressed": True,
        }

    resolved_summary = recovery_summary or f"Incident recovered: {incident_key}"
    dispatch_result = dispatch_auto_trade_alert(
        alert_key=f"incident:{incident_key}:recovered",
        severity=recovery_severity,
        summary=resolved_summary,
        details={
            **(active_details or {}),
            "incident_key": incident_key,
            "incident_event": "recovered",
            "opened_at": state.get("opened_at"),
            "closed_at": state.get("closed_at"),
        },
        enabled=enabled,
        cooldown_seconds=cooldown_seconds,
        webhook_url=webhook_url,
        platform=platform,
        email_to=email_to,
        logger=logger,
        requests_post=requests_post,
        send_platform_fn=send_platform_fn,
        send_email_fn=send_email_fn,
    )
    dispatch_result["event"] = "recovered"
    dispatch_result["incident_key"] = incident_key
    return dispatch_result
