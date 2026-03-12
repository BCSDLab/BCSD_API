#!/usr/bin/env bash
set -euo pipefail

if [ -f .env ]; then
    set -a; source .env; set +a
fi

COMPOSE="docker compose -f infra/docker/docker-compose.yml"
DOMAIN="${DOMAIN:?Set DOMAIN in .env}"
N8N_DOMAIN="${N8N_DOMAIN}"
FRONTEND_DOMAIN="${FRONTEND_DOMAIN}"

echo "=== Initial SSL Certificate Setup ==="

echo "1. Starting nginx for ACME challenge..."
$COMPOSE up -d nginx

echo "2. Requesting certificate for $DOMAIN..."
$COMPOSE run --rm certbot certonly \
    --webroot \
    -w /var/www/certbot \
    -d "$DOMAIN" \
    --register-unsafely-without-email \
    --agree-tos

if [ -n "$N8N_DOMAIN" ]; then
    echo "3. Requesting certificate for $N8N_DOMAIN..."
    $COMPOSE run --rm certbot certonly \
        --webroot \
        -w /var/www/certbot \
        -d "$N8N_DOMAIN" \
        --register-unsafely-without-email \
        --agree-tos
fi

if [ -n "$FRONTEND_DOMAIN" ]; then
    echo "4. Requesting certificate for $FRONTEND_DOMAIN (+ internal.bcsdlab.com)..."
    $COMPOSE run --rm certbot certonly \
        --webroot \
        -w /var/www/certbot \
        -d "$FRONTEND_DOMAIN" \
        -d internal.bcsdlab.com \
        --register-unsafely-without-email \
        --agree-tos
fi

echo "5. Reloading nginx with SSL..."
$COMPOSE exec nginx nginx -s reload

echo "=== SSL setup complete ==="
echo "Auto-renewal is handled by the certbot container."
