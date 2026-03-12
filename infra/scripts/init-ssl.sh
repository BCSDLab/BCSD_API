#!/usr/bin/env bash
set -euo pipefail

if [ -f .env ]; then
    set -a; source .env; set +a
fi

NGINX_AVAILABLE="/etc/nginx/sites-available/bcsd-api.conf"
NGINX_ENABLED="/etc/nginx/sites-enabled/bcsd-api.conf"
DOMAIN="${DOMAIN:?Set DOMAIN in .env}"
N8N_DOMAIN="${N8N_DOMAIN}"
FRONTEND_DOMAIN="${FRONTEND_DOMAIN}"

DOMAINS="$DOMAIN"
[ -n "$N8N_DOMAIN" ] && DOMAINS="$DOMAINS $N8N_DOMAIN"
[ -n "$FRONTEND_DOMAIN" ] && DOMAINS="$DOMAINS $FRONTEND_DOMAIN internal.bcsdlab.com"

echo "=== Initial SSL Certificate Setup ==="

echo "1. Installing HTTP-only nginx config for ACME challenge..."
sudo mkdir -p /var/www/certbot
cat <<EOF | sudo tee "$NGINX_AVAILABLE" > /dev/null
server {
    listen 80;
    server_name $DOMAINS;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 444;
    }
}
EOF
sudo ln -sf "$NGINX_AVAILABLE" "$NGINX_ENABLED"
sudo nginx -t && sudo nginx -s reload

echo "2. Requesting certificate for $DOMAIN..."
sudo certbot certonly \
    --webroot \
    -w /var/www/certbot \
    -d "$DOMAIN" \
    --register-unsafely-without-email \
    --agree-tos

if [ -n "$N8N_DOMAIN" ]; then
    echo "3. Requesting certificate for $N8N_DOMAIN..."
    sudo certbot certonly \
        --webroot \
        -w /var/www/certbot \
        -d "$N8N_DOMAIN" \
        --register-unsafely-without-email \
        --agree-tos
fi

if [ -n "$FRONTEND_DOMAIN" ]; then
    echo "4. Requesting certificate for $FRONTEND_DOMAIN (+ internal.bcsdlab.com)..."
    sudo certbot certonly \
        --webroot \
        -w /var/www/certbot \
        -d "$FRONTEND_DOMAIN" \
        -d internal.bcsdlab.com \
        --register-unsafely-without-email \
        --agree-tos
fi

echo "5. Installing full nginx config with HTTPS..."
sudo cp infra/nginx/bcsd-api.conf "$NGINX_AVAILABLE"
sudo nginx -t && sudo nginx -s reload

echo "=== SSL setup complete ==="
echo "Auto-renewal: sudo certbot renew (via system cron/timer)"
