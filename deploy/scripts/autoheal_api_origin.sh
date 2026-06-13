#!/usr/bin/env bash
set -euo pipefail

STACK_DIR="/opt/cryptoai/deploy/vps"
COMPOSE_FILE="$STACK_DIR/docker-compose.vps.yml"
ENV_FILE="$STACK_DIR/.env.vps"
LOCK_FILE="/tmp/cryptoai-api-autoheal.lock"
STATE_DIR="/tmp/cryptoai-api-autoheal-state"
FAIL_COUNT_FILE="$STATE_DIR/consecutive_failures"
LAST_RESTART_FILE="$STATE_DIR/last_restart_epoch"

MAX_CONSECUTIVE_FAILURES="${AUTOHEAL_MAX_CONSECUTIVE_FAILURES:-3}"
RESTART_COOLDOWN_SEC="${AUTOHEAL_RESTART_COOLDOWN_SEC:-600}"

exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [INFO] Auto-heal already running, skipping"
  exit 0
fi

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [WARN] Missing compose file: $COMPOSE_FILE"
  exit 0
fi

mkdir -p "$STATE_DIR"

read_int_file() {
  local path="$1"
  if [[ -f "$path" ]]; then
    tr -dc '0-9' < "$path"
  else
    echo "0"
  fi
}

write_int_file() {
  local path="$1"
  local value="$2"
  printf '%s\n' "$value" > "$path"
}

read_env_value() {
  local key="$1"
  local file="$2"
  [[ -f "$file" ]] || return 0
  awk -F '=' -v k="$key" '$1==k {print $2; exit}' "$file" | sed -E 's/^"|"$//g' | tr -d "\r"
}

API_DOMAIN="$(read_env_value "API_DOMAIN" "$ENV_FILE")"
API_DOMAIN="${API_DOMAIN:-api.dacryptobeast.com}"
HEALTH_URL="https://$API_DOMAIN/health"

compose_cmd=(docker compose)
if [[ -f "$ENV_FILE" ]]; then
  compose_cmd+=(--env-file "$ENV_FILE")
fi
compose_cmd+=(-f "$COMPOSE_FILE")

check_health() {
  curl -sS -o /dev/null -w "%{http_code}" --max-time 12 "$HEALTH_URL" || true
}

status_1="$(check_health)"
if [[ "$status_1" == "200" ]]; then
  write_int_file "$FAIL_COUNT_FILE" 0
  echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [OK] Health is 200"
  exit 0
fi

sleep 3
status_2="$(check_health)"
if [[ "$status_2" == "200" ]]; then
  write_int_file "$FAIL_COUNT_FILE" 0
  echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [OK] Health recovered on retry"
  exit 0
fi

failures="$(read_int_file "$FAIL_COUNT_FILE")"
if [[ -z "$failures" ]]; then
  failures=0
fi
failures=$((failures + 1))
write_int_file "$FAIL_COUNT_FILE" "$failures"

if (( failures < MAX_CONSECUTIVE_FAILURES )); then
  echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [WARN] Health failing (status1=$status_1, status2=$status_2); consecutive_failures=$failures threshold=$MAX_CONSECUTIVE_FAILURES"
  exit 0
fi

now_epoch="$(date +%s)"
last_restart_epoch="$(read_int_file "$LAST_RESTART_FILE")"
seconds_since_restart=$((now_epoch - last_restart_epoch))

if (( seconds_since_restart < RESTART_COOLDOWN_SEC )); then
  echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [WARN] Restart threshold met but cooldown active (remaining=$((RESTART_COOLDOWN_SEC - seconds_since_restart))s, failures=$failures)"
  exit 0
fi

echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [WARN] Restart threshold met (failures=$failures); restarting backend+caddy"
write_int_file "$LAST_RESTART_FILE" "$now_epoch"
"${compose_cmd[@]}" restart backend caddy

sleep 5
status_3="$(check_health)"
if [[ "$status_3" == "200" ]]; then
  write_int_file "$FAIL_COUNT_FILE" 0
  echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [PASS] Health restored after restart"
  exit 0
fi

echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [FAIL] Health still failing after restart (status=$status_3)"
"${compose_cmd[@]}" logs --tail=80 backend || true
"${compose_cmd[@]}" logs --tail=80 caddy || true
exit 0
