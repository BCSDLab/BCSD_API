#!/usr/bin/env bash
set -euo pipefail

if [ -f .env ]; then
    set -a; source .env; set +a
fi

NGINX_AVAILABLE="/etc/nginx/sites-available/bcsd-api.conf"
NGINX_ENABLED="/etc/nginx/sites-enabled/bcsd-api.conf"
CERT_NAME="bcsdlab.com"
DOMAIN="${DOMAIN:?Set DOMAIN in .env}"
N8N_DOMAIN="${N8N_DOMAIN}"
FRONTEND_DOMAIN="${FRONTEND_DOMAIN}"

DOMAIN_ARGS="-d $DOMAIN"
SERVER_NAMES="$DOMAIN"
[ -n "$N8N_DOMAIN" ] && DOMAIN_ARGS="$DOMAIN_ARGS -d $N8N_DOMAIN" && SERVER_NAMES="$SERVER_NAMES $N8N_DOMAIN"
[ -n "$FRONTEND_DOMAIN" ] && DOMAIN_ARGS="$DOMAIN_ARGS -d $FRONTEND_DOMAIN -d internal.bcsdlab.com" && SERVER_NAMES="$SERVER_NAMES $FRONTEND_DOMAIN internal.bcsdlab.com"

echo "=== Initial SSL Certificate Setup ==="

echo "1. Installing HTTP-only nginx config for ACME challenge..."
sudo mkdir -p /var/www/certbot
cat <<EOF | sudo tee "$NGINX_AVAILABLE" > /dev/null
server {
    listen 80;
    server_name $SERVER_NAMES;

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

echo "2. Requesting certificate for: $SERVER_NAMES"
sudo certbot certonly \
    --webroot \
    -w /var/www/certbot \
    --cert-name "$CERT_NAME" \
    $DOMAIN_ARGS \
    --register-unsafely-without-email \
    --agree-tos

echo "3. Installing full nginx config with HTTPS..."
sudo cp infra/nginx/bcsd-api.conf "$NGINX_AVAILABLE"
sudo nginx -t && sudo nginx -s reload

echo "=== SSL setup complete ==="
echo "Auto-renewal: sudo certbot renew (via system cron/timer)"
