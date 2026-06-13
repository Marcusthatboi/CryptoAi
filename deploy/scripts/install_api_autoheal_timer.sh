#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="/opt/cryptoai"
SERVICE_SRC="$REPO_ROOT/deploy/vps/cryptoai-api-autoheal.service"
TIMER_SRC="$REPO_ROOT/deploy/vps/cryptoai-api-autoheal.timer"
HEAL_SCRIPT="$REPO_ROOT/deploy/scripts/autoheal_api_origin.sh"
REPORT_SCRIPT="$REPO_ROOT/deploy/scripts/api_autoheal_report.sh"

if [[ ! -f "$SERVICE_SRC" ]] || [[ ! -f "$TIMER_SRC" ]] || [[ ! -f "$HEAL_SCRIPT" ]] || [[ ! -f "$REPORT_SCRIPT" ]]; then
  echo "[FAIL] Expected files not found under $REPO_ROOT"
  echo "       Ensure this repository is deployed at /opt/cryptoai first."
  exit 1
fi

if [[ "$EUID" -eq 0 ]]; then
  SUDO=""
else
  SUDO="sudo"
fi

echo "[INFO] Installing auto-heal script"
$SUDO install -m 0755 "$HEAL_SCRIPT" /opt/cryptoai/deploy/scripts/autoheal_api_origin.sh
$SUDO install -m 0755 "$REPORT_SCRIPT" /opt/cryptoai/deploy/scripts/api_autoheal_report.sh

echo "[INFO] Installing systemd unit files"
$SUDO install -m 0644 "$SERVICE_SRC" /etc/systemd/system/cryptoai-api-autoheal.service
$SUDO install -m 0644 "$TIMER_SRC" /etc/systemd/system/cryptoai-api-autoheal.timer

echo "[INFO] Reloading systemd"
$SUDO systemctl daemon-reload

echo "[INFO] Enabling and starting timer"
$SUDO systemctl enable --now cryptoai-api-autoheal.timer

echo "[INFO] Running an immediate health check once"
$SUDO systemctl start cryptoai-api-autoheal.service

echo "[INFO] Timer status"
$SUDO systemctl status --no-pager cryptoai-api-autoheal.timer

echo "[PASS] Auto-heal timer installed"
echo "[INFO] Report helper: /opt/cryptoai/deploy/scripts/api_autoheal_report.sh"
