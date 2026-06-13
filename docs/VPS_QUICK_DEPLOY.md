# VPS Quick Deploy (Efficient Path)

This is the fastest production path for 24/7 uptime using Docker Compose + Caddy.

## 1) Provision VPS

Recommended size: 2 vCPU / 4 GB RAM (Ubuntu 24.04).

Open ports in cloud firewall:
- 22 (SSH)
- 80 (HTTP)
- 443 (HTTPS)

## 2) DNS

Create A records:
- `dacryptobeast.com` -> `YOUR_VPS_IP`
- `api.dacryptobeast.com` -> `YOUR_VPS_IP`

For first TLS issuance, keep Cloudflare proxy set to DNS-only (gray cloud).
You can enable proxy later after certificates are issued.

## 3) Install Docker on VPS

```bash
sudo apt update && sudo apt -y upgrade
sudo apt -y install docker.io docker-compose-v2 git ufw
sudo usermod -aG docker $USER
newgrp docker
sudo ufw allow OpenSSH
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable
```

## 4) Deploy application

```bash
cd /opt
sudo git clone <YOUR_REPO_URL> cryptoai
sudo chown -R $USER:$USER /opt/cryptoai
cd /opt/cryptoai/deploy/vps
cp .env.vps.example .env.vps
nano .env.vps
```

Set at least:
- `APP_DOMAIN`
- `API_DOMAIN`
- `LETSENCRYPT_EMAIL`
- `SECRET_KEY` (64+ random chars)
- provider keys and Stripe keys you use

Start stack:

```bash
cd /opt/cryptoai/deploy/vps
docker compose --env-file .env.vps -f docker-compose.vps.yml up -d --build
```

## 5) Enable auto-start on reboot

```bash
sudo cp /opt/cryptoai/deploy/vps/cryptoai.service /etc/systemd/system/cryptoai.service
sudo systemctl daemon-reload
sudo systemctl enable cryptoai
sudo systemctl start cryptoai
sudo systemctl status cryptoai --no-pager
```

## 6) Verify

```bash
curl -I https://dacryptobeast.com
curl https://api.dacryptobeast.com/health
```

## 7) Updates (single command)

```bash
cd /opt/cryptoai
git pull
cd /opt/cryptoai/deploy/vps
docker compose --env-file .env.vps -f docker-compose.vps.yml up -d --build
```

## Troubleshooting

Show logs:

```bash
cd /opt/cryptoai/deploy/vps
docker compose --env-file .env.vps -f docker-compose.vps.yml logs -f caddy backend frontend
```

Restart stack:

```bash
cd /opt/cryptoai/deploy/vps
docker compose --env-file .env.vps -f docker-compose.vps.yml restart
```

## Environment variables

APP_DOMAIN=dacryptobeast.com
API_DOMAIN=api.dacryptobeast.com
LETSENCRYPT_EMAIL=your-real-email
SECRET_KEY=your-strong-secret
APP_ENV=production
ENVIRONMENT=production
DB_NAME=cryptoai
MONGODB_URL=mongodb://mongo:27017
FRONTEND_ALLOWED_ORIGINS=https://dacryptobeast.com,https://www.dacryptobeast.com
