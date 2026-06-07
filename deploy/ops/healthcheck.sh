#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:8002}"
FRONTEND_URL="${2:-http://127.0.0.1:8080}"

check_endpoint() {
  local name="$1"
  local url="$2"
  local code
  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 8 "$url" || true)

  if [[ "$code" =~ ^2|3|401|403$ ]]; then
    echo "[UP]   $name ($url) -> $code"
    return 0
  fi

  echo "[DOWN] $name ($url) -> ${code:-n/a}"
  return 1
}

status=0
check_endpoint "backend-health" "$BASE_URL/health" || status=1
check_endpoint "backend-root" "$BASE_URL/" || status=1
check_endpoint "frontend" "$FRONTEND_URL" || status=1

exit $status
