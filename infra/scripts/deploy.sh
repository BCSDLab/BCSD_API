#!/usr/bin/env bash
set -euo pipefail

COMPOSE="sudo docker compose --env-file .env -f infra/docker/docker-compose.yml"
COMPOSE_DB="sudo docker compose --env-file .env -f infra/docker/docker-compose.db.yml"
NGINX_CONF="infra/docker/nginx.conf"
HEALTH_PATH="/openapi.json"
MAX_RETRIES=10

current_slot() {
    grep proxy_pass "$NGINX_CONF" | grep -q "api_blue" && echo "blue" || echo "green"
}

next_slot() {
    [ "$(current_slot)" = "blue" ] && echo "green" || echo "blue"
}

health_check() {
    local container="api-${1}"
    local retries=0
    while [ $retries -lt $MAX_RETRIES ]; do
        if $COMPOSE exec "$container" python -c \
            "import urllib.request; urllib.request.urlopen('http://localhost:8000${HEALTH_PATH}')" \
            > /dev/null 2>&1; then
            return 0
        fi
        retries=$((retries + 1))
        echo "  retry ${retries}/${MAX_RETRIES}..."
        sleep 3
    done
    return 1
}

check_credentials() {
    if [ ! -f .env ]; then
        echo "FAIL: .env not found (CI/CD should have uploaded it)"
        exit 1
    fi
    local sa_file
    sa_file=$(grep -m1 '^GOOGLE_SERVICE_ACCOUNT_FILE=' .env | cut -d= -f2-)
    if [ -z "$sa_file" ]; then
        echo "FAIL: GOOGLE_SERVICE_ACCOUNT_FILE not set in .env"
        exit 1
    fi
    if [ ! -f "$sa_file" ]; then
        echo "FAIL: $sa_file not found (CI/CD should have uploaded it)"
        exit 1
    fi
}

echo "=== BCSD API Blue-Green Deploy ==="

check_credentials

echo "0. Ensuring DB services..."
$COMPOSE_DB up -d

CURRENT=$(current_slot)
NEXT=$(next_slot)

echo "Current: $CURRENT → Deploying: $NEXT"

echo "1. Building $NEXT..."
$COMPOSE build "api-${NEXT}"

echo "2. Starting $NEXT + nginx..."
$COMPOSE up -d "api-${NEXT}" nginx

echo "3. Health check on api-${NEXT}..."
if ! health_check "$NEXT"; then
    echo "FAIL: $NEXT did not become healthy"
    echo "--- Container logs ---"
    $COMPOSE logs --tail=30 "api-${NEXT}"
    echo "--- Stopping failed container ---"
    $COMPOSE stop "api-${NEXT}"
    exit 1
fi

echo "4. Switching nginx → $NEXT"
sed -i "s/proxy_pass http:\/\/api_${CURRENT}/proxy_pass http:\/\/api_${NEXT}/" "$NGINX_CONF"
$COMPOSE exec nginx nginx -s reload

echo "5. Stopping old ($CURRENT)..."
$COMPOSE stop "api-${CURRENT}"

echo "=== Deploy complete: $NEXT is live ==="
