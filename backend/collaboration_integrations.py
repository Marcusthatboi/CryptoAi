"""Collaboration platform webhook integrations for sharing analysis."""

import os
import requests
from typing import Dict

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
TEAMS_WEBHOOK_URL = os.getenv("TEAMS_WEBHOOK_URL", "")
GOOGLE_CHAT_WEBHOOK_URL = os.getenv("GOOGLE_CHAT_WEBHOOK_URL", "")


def get_platform_statuses() -> Dict:
    """Return configuration and readiness status for supported platforms."""
    return {
        "slack": {
            "configured": bool(SLACK_WEBHOOK_URL),
            "status": "configured" if SLACK_WEBHOOK_URL else "not_configured"
        },
        "teams": {
            "configured": bool(TEAMS_WEBHOOK_URL),
            "status": "configured" if TEAMS_WEBHOOK_URL else "not_configured"
        },
        "google_chat": {
            "configured": bool(GOOGLE_CHAT_WEBHOOK_URL),
            "status": "configured" if GOOGLE_CHAT_WEBHOOK_URL else "not_configured"
        }
    }


def _post_json(webhook_url: str, payload: Dict) -> None:
    if not webhook_url:
        raise RuntimeError("Webhook URL is not configured")

    response = requests.post(webhook_url, json=payload, timeout=8)
    if response.status_code >= 300:
        raise RuntimeError(f"Webhook post failed with status {response.status_code}: {response.text}")


def _build_text_message(data: Dict) -> str:
    title = data.get("title", "CryptoAI Analysis")
    summary = data.get("summary", "")
    symbol = data.get("symbol", "")
    link = data.get("url", "")
    requested_by = data.get("requested_by", "unknown")

    lines = [
        f"{title}",
        f"Symbol: {symbol}" if symbol else "",
        summary,
        f"Requested by: {requested_by}",
        f"Details: {link}" if link else ""
    ]

    return "\n".join([line for line in lines if line])


def send_to_platform(platform: str, data: Dict) -> None:
    """Send analysis payload to configured collaboration platform webhook."""
    platform_key = str(platform or "").strip().lower()
    message_text = _build_text_message(data)

    if platform_key == "slack":
        _post_json(SLACK_WEBHOOK_URL, {
            "text": message_text,
            "unfurl_links": True,
            "mrkdwn": True
        })
        return

    if platform_key == "teams":
        _post_json(TEAMS_WEBHOOK_URL, {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.4",
                        "body": [
                            {"type": "TextBlock", "text": data.get("title", "CryptoAI Analysis"), "weight": "Bolder", "size": "Medium"},
                            {"type": "TextBlock", "text": message_text, "wrap": True}
                        ]
                    }
                }
            ]
        })
        return

    if platform_key in {"google_chat", "google-workspace", "workspace", "google"}:
        _post_json(GOOGLE_CHAT_WEBHOOK_URL, {
            "text": message_text
        })
        return

    raise RuntimeError(f"Unsupported platform: {platform}")


def send_test_message(platform: str, requested_by: str) -> None:
    """Send standardized test message to selected platform."""
    send_to_platform(platform, {
        "title": "CryptoAI Integration Test",
        "summary": "This is a test message from CryptoAI integrations settings.",
        "symbol": "TEST",
        "url": "",
        "requested_by": requested_by
    })
