#!/usr/bin/env bash
set -euo pipefail

echo '--- docker ps ---'
sudo docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'

echo '--- backend ip ---'
sudo docker inspect vps-backend-1 | grep -m1 -A4 IPAddress

echo '--- container tcp 8002 ---'
sudo docker exec vps-backend-1 sh -c 'cat /proc/net/tcp | grep ":1F42 " || true'

echo '--- backend log tail ---'
sudo docker compose --env-file /opt/cryptoai/deploy/vps/.env.vps -f /opt/cryptoai/deploy/vps/docker-compose.vps.yml logs --tail=40 backend
