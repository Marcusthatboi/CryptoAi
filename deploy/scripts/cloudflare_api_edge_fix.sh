#!/usr/bin/env bash
set -euo pipefail

# One-shot Cloudflare fixer/verifier for api.dacryptobeast.com edge 502 issues.
#
# Modes:
#   verify (default): read-only checks + edge health probe
#   apply: enforce recommended settings, then run verify checks
#
# Required env vars:
#   CF_API_TOKEN: Cloudflare API token with DNS + Zone Settings edit permissions
#   CF_ZONE_ID: Cloudflare zone ID for dacryptobeast.com
#
# Optional env vars:
#   API_HOST (default: api.dacryptobeast.com)
#   EXPECTED_ORIGIN_IP (default: 34.70.44.250)

CF_API_BASE="https://api.cloudflare.com/client/v4"
API_HOST="${API_HOST:-api.dacryptobeast.com}"
EXPECTED_ORIGIN_IP="${EXPECTED_ORIGIN_IP:-34.70.44.250}"
MODE="${1:-verify}"

strip_cr() {
  printf '%s' "$1" | tr -d '\r'
}

CF_API_BASE="$(strip_cr "$CF_API_BASE")"
API_HOST="$(strip_cr "$API_HOST")"
EXPECTED_ORIGIN_IP="$(strip_cr "$EXPECTED_ORIGIN_IP")"
MODE="$(strip_cr "$MODE")"
CF_API_TOKEN="$(strip_cr "${CF_API_TOKEN:-}")"
CF_ZONE_ID="$(strip_cr "${CF_ZONE_ID:-}")"

if [[ -z "${CF_API_TOKEN:-}" || -z "${CF_ZONE_ID:-}" ]]; then
  echo "[FAIL] Missing required environment variables."
  echo "       Set CF_API_TOKEN and CF_ZONE_ID, then retry."
  exit 1
fi

if [[ "$MODE" != "verify" && "$MODE" != "apply" ]]; then
  echo "Usage: $0 [verify|apply]"
  exit 1
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

api_call() {
  local method="$1"
  local endpoint="$2"
  local body="${3:-}"
  local out_file="$4"
  local clean_endpoint
  local clean_body

  clean_endpoint="$(strip_cr "$endpoint")"
  clean_body="$(strip_cr "$body")"

  if [[ -n "$clean_body" ]]; then
    curl -sS -X "$method" "$CF_API_BASE$clean_endpoint" \
      -H "Authorization: Bearer $CF_API_TOKEN" \
      -H "Content-Type: application/json" \
      --data "$clean_body" > "$out_file"
  else
    curl -sS -X "$method" "$CF_API_BASE$clean_endpoint" \
      -H "Authorization: Bearer $CF_API_TOKEN" \
      -H "Content-Type: application/json" > "$out_file"
  fi

  python3 - "$out_file" <<'PY'
import json, sys
path = sys.argv[1]
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)
if not data.get("success", False):
    errs = data.get("errors", [])
    print("[FAIL] Cloudflare API call failed:", errs)
    sys.exit(2)
PY
}

get_dns_records() {
  api_call "GET" "/zones/$CF_ZONE_ID/dns_records?name=$API_HOST&per_page=100" "" "$tmp_dir/dns.json"
}

get_ssl_mode() {
  api_call "GET" "/zones/$CF_ZONE_ID/settings/ssl" "" "$tmp_dir/ssl.json"
}

get_tls_client_auth() {
  api_call "GET" "/zones/$CF_ZONE_ID/settings/tls_client_auth" "" "$tmp_dir/tls_client_auth.json"
}

enforce_dns() {
  get_dns_records

  python3 - "$tmp_dir/dns.json" "$API_HOST" "$EXPECTED_ORIGIN_IP" "$tmp_dir/plan.json" <<'PY'
import json, sys
path, api_host, expected_ip, plan_path = sys.argv[1:]
data = json.load(open(path, 'r', encoding='utf-8'))
records = data.get("result", [])

a_records = [r for r in records if r.get("type") == "A"]
aaaa_records = [r for r in records if r.get("type") == "AAAA"]
cname_records = [r for r in records if r.get("type") == "CNAME"]

plan = {
    "update_a": None,
    "create_a": False,
    "delete_ids": []
}

if a_records:
    primary = a_records[0]
    plan["update_a"] = primary.get("id")
    for rec in a_records[1:]:
        plan["delete_ids"].append(rec.get("id"))
else:
    plan["create_a"] = True

for rec in aaaa_records + cname_records:
    plan["delete_ids"].append(rec.get("id"))

json.dump(plan, open(plan_path, 'w', encoding='utf-8'))
PY

  local update_a_id
  update_a_id="$(python3 - "$tmp_dir/plan.json" <<'PY'
import json, sys
plan = json.load(open(sys.argv[1], 'r', encoding='utf-8'))
print(plan.get('update_a') or '')
PY
)"

  local create_a
  create_a="$(python3 - "$tmp_dir/plan.json" <<'PY'
import json, sys
plan = json.load(open(sys.argv[1], 'r', encoding='utf-8'))
print('true' if plan.get('create_a') else 'false')
PY
)"

  python3 - "$tmp_dir/plan.json" <<'PY' > "$tmp_dir/delete_ids.txt"
import json, sys
plan = json.load(open(sys.argv[1], 'r', encoding='utf-8'))
for rid in plan.get('delete_ids', []):
    if rid:
        print(rid)
PY

  while IFS= read -r rid; do
    rid="$(strip_cr "$rid")"
    [[ -z "$rid" ]] && continue
    api_call "DELETE" "/zones/$CF_ZONE_ID/dns_records/$rid" "" "$tmp_dir/delete_$rid.json"
    echo "[OK] Deleted conflicting DNS record id=$rid"
  done < "$tmp_dir/delete_ids.txt"

  if [[ -n "$update_a_id" ]]; then
    api_call "PUT" "/zones/$CF_ZONE_ID/dns_records/$update_a_id" \
      "{\"type\":\"A\",\"name\":\"${API_HOST}\",\"content\":\"${EXPECTED_ORIGIN_IP}\",\"ttl\":1,\"proxied\":true}" \
      "$tmp_dir/update_a.json"
    echo "[OK] Updated A record for $API_HOST -> $EXPECTED_ORIGIN_IP (proxied=true)"
  elif [[ "$create_a" == "true" ]]; then
    api_call "POST" "/zones/$CF_ZONE_ID/dns_records" \
      "{\"type\":\"A\",\"name\":\"${API_HOST}\",\"content\":\"${EXPECTED_ORIGIN_IP}\",\"ttl\":1,\"proxied\":true}" \
      "$tmp_dir/create_a.json"
    echo "[OK] Created A record for $API_HOST -> $EXPECTED_ORIGIN_IP (proxied=true)"
  fi
}

enforce_ssl_settings() {
  api_call "PATCH" "/zones/$CF_ZONE_ID/settings/ssl" "{\"value\":\"strict\"}" "$tmp_dir/ssl_set.json"
  echo "[OK] Set SSL mode to strict"

  api_call "PATCH" "/zones/$CF_ZONE_ID/settings/tls_client_auth" "{\"value\":\"off\"}" "$tmp_dir/tls_client_auth_set.json"
  echo "[OK] Set tls_client_auth to off"
}

verify_state() {
  local failures=0

  get_dns_records
  get_ssl_mode
  get_tls_client_auth

  python3 - "$tmp_dir/dns.json" "$API_HOST" "$EXPECTED_ORIGIN_IP" > "$tmp_dir/dns_report.txt" <<'PY'
import json, sys
path, host, expected_ip = sys.argv[1:]
data = json.load(open(path, 'r', encoding='utf-8'))
records = data.get('result', [])
a = [r for r in records if r.get('type') == 'A']
aaaa = [r for r in records if r.get('type') == 'AAAA']
cname = [r for r in records if r.get('type') == 'CNAME']

ok = True

if len(a) != 1:
    ok = False
    print(f"[FAIL] Expected exactly 1 A record for {host}; found {len(a)}")
else:
    ar = a[0]
    content = ar.get('content')
    proxied = ar.get('proxied')
    if content != expected_ip:
        ok = False
        print(f"[FAIL] A record points to {content}, expected {expected_ip}")
    else:
        print(f"[OK] A record points to expected origin {content}")
    if proxied is not True:
        ok = False
        print("[FAIL] A record is not proxied (orange cloud required)")
    else:
        print("[OK] A record is proxied")

if aaaa:
    ok = False
    print(f"[FAIL] Found {len(aaaa)} AAAA record(s); remove unless origin IPv6 is explicitly configured")
else:
    print("[OK] No AAAA records present")

if cname:
    ok = False
    print(f"[FAIL] Found {len(cname)} CNAME record(s) for API host")
else:
    print("[OK] No CNAME records present")

print("RESULT=PASS" if ok else "RESULT=FAIL")
PY

  cat "$tmp_dir/dns_report.txt"
  if grep -q "RESULT=FAIL" "$tmp_dir/dns_report.txt"; then
    failures=$((failures + 1))
  fi

  local ssl_value
  ssl_value="$(python3 - "$tmp_dir/ssl.json" <<'PY'
import json, sys
print(json.load(open(sys.argv[1], 'r', encoding='utf-8')).get('result', {}).get('value', ''))
PY
)"

  if [[ "$ssl_value" == "strict" ]]; then
    echo "[OK] SSL mode is strict"
  else
    echo "[FAIL] SSL mode is '$ssl_value' (expected 'strict')"
    failures=$((failures + 1))
  fi

  local tls_client_auth
  tls_client_auth="$(python3 - "$tmp_dir/tls_client_auth.json" <<'PY'
import json, sys
print(json.load(open(sys.argv[1], 'r', encoding='utf-8')).get('result', {}).get('value', ''))
PY
)"

  if [[ "$tls_client_auth" == "off" ]]; then
    echo "[OK] Authenticated origin pulls (tls_client_auth) is off"
  else
    echo "[FAIL] tls_client_auth is '$tls_client_auth' (expected 'off' unless mTLS is intentionally configured)"
    failures=$((failures + 1))
  fi

  local edge_status
  edge_status="$(curl -sS -o "$tmp_dir/edge_body.txt" -D "$tmp_dir/edge_headers.txt" -w "%{http_code}" "https://$API_HOST/health" || true)"
  local edge_server
  edge_server="$(grep -i '^server:' "$tmp_dir/edge_headers.txt" | tail -n1 | awk -F': ' '{print $2}' | tr -d '\r' || true)"

  if [[ "$edge_status" == "200" && "${edge_server,,}" == "cloudflare" ]]; then
    echo "[OK] Cloudflare edge health is 200 (server=$edge_server)"
  else
    echo "[FAIL] Cloudflare edge health is $edge_status (server=${edge_server:-unknown})"
    failures=$((failures + 1))
  fi

  return "$failures"
}

echo "============================================================"
echo " Cloudflare API Edge ${MODE^^}"
echo " Host: $API_HOST"
echo " Expected origin IP: $EXPECTED_ORIGIN_IP"
echo "============================================================"

if [[ "$MODE" == "apply" ]]; then
  enforce_dns
  enforce_ssl_settings
fi

if verify_state; then
  echo "[PASS] Cloudflare API edge checks passed"
  exit 0
fi

echo "[FAIL] Cloudflare API edge checks failed"
exit 1
