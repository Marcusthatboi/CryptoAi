#!/usr/bin/env bash
set -euo pipefail

STACK_DIR="/opt/cryptoai/deploy/vps"
COMPOSE_FILE="$STACK_DIR/docker-compose.vps.yml"
ENV_FILE="$STACK_DIR/.env.vps"

SINCE_WINDOW="${1:-24 hours ago}"

compose_cmd=(docker compose)
if [[ -f "$ENV_FILE" ]]; then
  compose_cmd+=(--env-file "$ENV_FILE")
fi
compose_cmd+=(-f "$COMPOSE_FILE")

echo "============================================================"
echo " CryptoAI Auto-Heal Incident Report"
echo "============================================================"
echo "window=$SINCE_WINDOW"
echo

echo "[INFO] Timer state"
systemctl status --no-pager cryptoai-api-autoheal.timer || true

echo
echo "[INFO] Last auto-heal service runs"
systemctl status --no-pager cryptoai-api-autoheal.service || true

echo
echo "[INFO] Journal summary counts"
warn_count="$(journalctl -u cryptoai-api-autoheal.service --since "$SINCE_WINDOW" --no-pager | grep -c '\[WARN\]' || true)"
fail_count="$(journalctl -u cryptoai-api-autoheal.service --since "$SINCE_WINDOW" --no-pager | grep -c '\[FAIL\]' || true)"
pass_count="$(journalctl -u cryptoai-api-autoheal.service --since "$SINCE_WINDOW" --no-pager | grep -c '\[PASS\]' || true)"
ok_count="$(journalctl -u cryptoai-api-autoheal.service --since "$SINCE_WINDOW" --no-pager | grep -c '\[OK\]' || true)"
echo "OK=$ok_count PASS=$pass_count WARN=$warn_count FAIL=$fail_count"

echo
echo "[INFO] Recent auto-heal journal entries"
journalctl -u cryptoai-api-autoheal.service --since "$SINCE_WINDOW" --no-pager -n 200 || true

echo
echo "[INFO] Backend logs (tail)"
"${compose_cmd[@]}" logs --tail=120 backend || true

echo
echo "[INFO] Caddy logs (tail)"
"${compose_cmd[@]}" logs --tail=120 caddy || true
