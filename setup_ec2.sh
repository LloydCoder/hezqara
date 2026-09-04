#!/bin/bash
# Carenova AI — EC2 Ubuntu Bootstrap Script
# Run on fresh EC2 instance: bash setup_ec2.sh
# EC2: AWS Stockholm (eu-north-1), Ubuntu 24.04 LTS

set -euo pipefail

echo "═══════════════════════════════════════════"
echo "  Carenova AI — EC2 Bootstrap"
echo "  EC2 Stockholm: 13.50.16.19 | Port: 8004"
echo "═══════════════════════════════════════════"

# ── System update ────────────────────────────────────────────────────────────
echo "► Updating system..."
sudo apt-get update -qq
sudo apt-get upgrade -y -qq

# ── Install Docker ────────────────────────────────────────────────────────────
echo "► Installing Docker..."
curl -fsSL https://get.docker.com | bash
sudo usermod -aG docker ubuntu
sudo systemctl enable docker
sudo systemctl start docker

# ── Install Docker Compose ────────────────────────────────────────────────────
echo "► Installing Docker Compose..."
sudo apt-get install -y docker-compose-plugin
docker compose version

# ── Install nginx ─────────────────────────────────────────────────────────────
echo "► Installing nginx..."
sudo apt-get install -y nginx
sudo systemctl enable nginx

# ── Install certbot ───────────────────────────────────────────────────────────
echo "► Installing certbot for SSL..."
sudo apt-get install -y certbot python3-certbot-nginx

# ── Install monitoring tools ──────────────────────────────────────────────────
echo "► Installing monitoring tools..."
sudo apt-get install -y htop curl jq git

# ── Firewall ──────────────────────────────────────────────────────────────────
echo "► Configuring firewall..."
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP (redirect to HTTPS)
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8004/tcp  # Carenova API (direct access for FusionOps)
# Internal only — not exposed:
# 6380 Redis
# 6381 FalkorDB
# 8005 Graphiti
# 3004 Frontend (served via nginx)
sudo ufw --force enable

# ── Clone repository ──────────────────────────────────────────────────────────
echo "► Setting up Carenova..."
if [ ! -d "/home/ubuntu/carenova" ]; then
    echo "  Clone the private repo first:"
    echo "  git clone git@github.com:Tinlance/carenova.git /home/ubuntu/carenova"
else
    echo "  Repo already exists — skipping clone"
fi

# ── nginx config ──────────────────────────────────────────────────────────────
echo "► Configuring nginx..."
sudo cp /home/ubuntu/carenova/infrastructure/docker/nginx/carenova.conf \
    /etc/nginx/sites-available/carenova
sudo ln -sf /etc/nginx/sites-available/carenova \
    /etc/nginx/sites-enabled/carenova
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

# ── SSL certificate ───────────────────────────────────────────────────────────
echo "► Obtaining SSL certificate..."
echo "  Run this after DNS is pointed at this server:"
echo "  sudo certbot --nginx -d carenova.tinlance.com --non-interactive --agree-tos -m lloyd@tinlance.com"

# ── systemd service ───────────────────────────────────────────────────────────
echo "► Installing systemd service..."
sudo cp /home/ubuntu/carenova/infrastructure/systemd/carenova.service \
    /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable carenova

# ── Environment file check ────────────────────────────────────────────────────
echo "► Checking environment..."
if [ ! -f "/home/ubuntu/carenova/backend/.env" ]; then
    echo "  ⚠️  .env file missing!"
    echo "  Copy and fill: cp backend/.env.example backend/.env"
    echo "  Required: ANTHROPIC_API_KEY, RETELL_API_KEY, ATHENA_CLIENT_ID,"
    echo "            SUPABASE_URL, LEMONSQUEEZY_API_KEY, STRIPE_SECRET_KEY,"
    echo "            CLERK_SECRET_KEY, PAYSTACK_SECRET_KEY"
fi

echo ""
echo "═══════════════════════════════════════════"
echo "  Bootstrap complete."
echo ""
echo "  Next steps:"
echo "  1. Fill in backend/.env"
echo "  2. Point DNS carenova.tinlance.com → 13.50.16.19"
echo "  3. sudo certbot --nginx -d carenova.tinlance.com"
echo "  4. sudo systemctl start carenova"
echo "  5. sudo systemctl status carenova"
echo ""
echo "  Health check: curl http://localhost:8004/health"
echo "  Logs: sudo journalctl -u carenova -f"
echo "═══════════════════════════════════════════"
