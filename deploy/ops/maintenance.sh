#!/usr/bin/env bash
set -euo pipefail

SECURITY_SCAN=false
INCLUDE_BUILD=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --security-scan) SECURITY_SCAN=true; shift ;;
    --include-build) INCLUDE_BUILD=true; shift ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

cd "$(dirname "$0")/../.."

echo "Running backend test suite..."
python -m unittest discover -s tests -t . -p "test_*.py" -v

if [[ "$INCLUDE_BUILD" == "true" ]]; then
  echo "Running frontend production build..."
  (cd frontend && npm run build)
fi

if [[ "$SECURITY_SCAN" == "true" ]]; then
  echo "Running backend dependency security scan..."
  python -m pip_audit

  echo "Running frontend dependency security scan..."
  (cd frontend && npm audit --omit=dev --audit-level=high)
fi

echo "Maintenance checks completed successfully."
