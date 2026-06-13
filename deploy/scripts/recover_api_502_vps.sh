#!/usr/bin/env bash
set -euo pipefail

# Recover API origin issues that surface as Cloudflare 502 on api.dacryptobeast.com.
# Run this script on the VPS host (not locally) from any directory.

STACK_DIR="/opt/cryptoai/deploy/vps"
COMPOSE_FILE="$STACK_DIR/docker-compose.vps.yml"
ENV_FILE="$STACK_DIR/.env.vps"

read_env_value() {
  local key="$1"
  local file="$2"
  [[ -f "$file" ]] || return 0
  awk -F '=' -v k="$key" '$1==k {print $2; exit}' "$file" | sed -E 's/^"|"$//g' | tr -d "\r"
}

resolve_domain() {
  local domain="$1"
  if command -v dig >/dev/null 2>&1; then
    dig +short A "$domain" | sed '/^$/d' | sort -u
    return 0
  fi

  if command -v getent >/dev/null 2>&1; then
    getent ahostsv4 "$domain" | awk '{print $1}' | sed '/^$/d' | sort -u
    return 0
  fi

  if command -v nslookup >/dev/null 2>&1; then
    nslookup "$domain" 2>/dev/null | awk '/^Address: /{print $2}' | sed '/^$/d' | sort -u
    return 0
  fi

  echo "(resolver unavailable: install dnsutils/bind-utils for dig)"
}

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "[FAIL] Missing compose file: $COMPOSE_FILE"
  echo "       Ensure the repository is deployed to /opt/cryptoai first."
  exit 1
fi

compose_cmd=(docker compose)
if [[ -f "$ENV_FILE" ]]; then
  compose_cmd+=(--env-file "$ENV_FILE")
fi
compose_cmd+=(-f "$COMPOSE_FILE")

APP_DOMAIN="$(read_env_value "APP_DOMAIN" "$ENV_FILE")"
API_DOMAIN="$(read_env_value "API_DOMAIN" "$ENV_FILE")"
APP_DOMAIN="${APP_DOMAIN:-dacryptobeast.com}"
API_DOMAIN="${API_DOMAIN:-api.dacryptobeast.com}"

echo "============================================================"
echo " CryptoAI API 502 Recovery"
echo "============================================================"

echo "[INFO] Checking current stack status"
"${compose_cmd[@]}" ps || true

echo
echo "[INFO] Tail backend logs"
"${compose_cmd[@]}" logs --tail=120 backend || true

echo
echo "[INFO] Tail caddy logs"
"${compose_cmd[@]}" logs --tail=120 caddy || true

echo
echo "[INFO] Rebuilding and restarting backend + caddy"
"${compose_cmd[@]}" up -d --build backend caddy

echo
echo "[INFO] Stack status after restart"
"${compose_cmd[@]}" ps

echo
echo "[INFO] Waiting briefly for upstream readiness"
sleep 5

echo
echo "[CHECK] DNS and Cloudflare edge sanity"
echo "app-domain=$APP_DOMAIN"
echo "api-domain=$API_DOMAIN"
echo "A/IPv4 for $APP_DOMAIN:"
resolve_domain "$APP_DOMAIN" || true
echo "A/IPv4 for $API_DOMAIN:"
resolve_domain "$API_DOMAIN" || true

trace_status="$(curl -sS -o /tmp/cryptoai_cf_trace.txt -w "%{http_code}" "https://$API_DOMAIN/cdn-cgi/trace" || true)"
if [[ "$trace_status" == "200" ]]; then
  echo "[OK] Cloudflare edge trace reachable for $API_DOMAIN"
  grep -E '^(h=|colo=|warp=|ts=)' /tmp/cryptoai_cf_trace.txt || true
else
  echo "[WARN] Cloudflare edge trace unavailable for $API_DOMAIN (status=$trace_status)"
fi

echo
echo "[CHECK] API health"
health_headers="$(mktemp)"
health_status="$(curl -sS -o /tmp/cryptoai_health_body.txt -D "$health_headers" -w "%{http_code}" "https://$API_DOMAIN/health" || true)"
echo "status=$health_status"
grep -iE '^(server|cf-ray|content-type|access-control-allow-origin|date):' "$health_headers" || true

echo
echo "[CHECK] CORS preflight on /auth/login"
preflight_headers="$(mktemp)"
preflight_status="$(curl -sS -o /tmp/cryptoai_preflight_body.txt -D "$preflight_headers" -w "%{http_code}" \
  -X OPTIONS "https://$API_DOMAIN/auth/login" \
  -H "Origin: https://$APP_DOMAIN" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: authorization,content-type" || true)"
echo "status=$preflight_status"
grep -iE '^(access-control-allow-origin|access-control-allow-methods|access-control-allow-headers|access-control-allow-credentials|vary):' "$preflight_headers" || true

echo
if [[ "$health_status" == "200" ]] && ([[ "$preflight_status" == "200" ]] || [[ "$preflight_status" == "204" ]]); then
  echo "[PASS] Origin recovered: health and preflight checks are good."
  exit 0
fi

echo "[WARN] Origin may still be unhealthy."
echo "       Next checks:"
echo "       1) ${compose_cmd[*]} logs --tail=300 backend"
echo "       2) ${compose_cmd[*]} logs --tail=300 caddy"
echo "       3) Confirm Cloudflare DNS/tunnel route for $API_DOMAIN points to active origin"
exit 1
