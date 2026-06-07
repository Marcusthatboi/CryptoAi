#!/usr/bin/env bash
set -euo pipefail

USE_HA=true
BUILD=true

while [[ $# -gt 0 ]]; do
  case "$1" in
    --prod-only) USE_HA=false; shift ;;
    --no-build) BUILD=false; shift ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

cd "$(dirname "$0")/../.."

COMPOSE_FILE="docker-compose.ha.yml"
if [[ "$USE_HA" == "false" ]]; then
  COMPOSE_FILE="docker-compose.prod.yml"
fi

if [[ ! -f ".env" ]]; then
  echo "Missing .env file. Copy .env.example to .env and configure secrets first."
  exit 1
fi

if [[ "$BUILD" == "true" ]]; then
  docker compose -f "$COMPOSE_FILE" up --build -d
else
  docker compose -f "$COMPOSE_FILE" up -d
fi

docker compose -f "$COMPOSE_FILE" ps
echo "Deployment completed."
