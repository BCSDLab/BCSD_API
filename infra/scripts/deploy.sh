#!/usr/bin/env bash
set -euo pipefail

COMPOSE="sudo docker compose -p bcsd-app --env-file .env -f infra/docker/docker-compose.yml"
COMPOSE_DB="sudo docker compose -p bcsd-db --env-file .env -f infra/docker/docker-compose.db.yml"
NGINX_TEMPLATE="infra/nginx/bcsd-api.conf.template"
NGINX_CONF="infra/nginx/bcsd-api.conf"
NGINX_AVAILABLE="/etc/nginx/sites-available/bcsd-api.conf"
NGINX_ENABLED="/etc/nginx/sites-enabled/bcsd-api.conf"
HEALTH_PATH="/openapi.json"
MAX_RETRIES=10
ENVSUBST_VARS='${API_BLUE_PORT} ${API_GREEN_PORT} ${N8N_PORT} ${FRONTEND_PORT} ${DOMAIN} ${N8N_DOMAIN} ${FRONTEND_DOMAIN}'

REQUIRED_VARS=(
    POSTGRES_USER POSTGRES_PASSWORD POSTGRES_DB
    GOOGLE_SERVICE_ACCOUNT_FILE GOOGLE_SHEETS_ID
    SYNC_TOKEN JWT_SECRET GOOGLE_CLIENT_ID
    API_BLUE_PORT API_GREEN_PORT N8N_PORT
)

current_slot() {
    grep proxy_pass "$NGINX_CONF" 2>/dev/null | grep -q "api_blue" && echo "blue" || echo "green"
}

next_slot() {
    [ "$(current_slot)" = "blue" ] && echo "green" || echo "blue"
}

health_check() {
    local port
    port=$(grep -m1 "^API_$(echo "$1" | tr '[:lower:]' '[:upper:]')_PORT=" .env | cut -d= -f2-)
    local retries=0
    while [ $retries -lt $MAX_RETRIES ]; do
        if curl -sf "http://localhost:${port}${HEALTH_PATH}" > /dev/null 2>&1; then
            return 0
        fi
        retries=$((retries + 1))
        echo "  retry ${retries}/${MAX_RETRIES}..."
        sleep 3
    done
    return 1
}

check_env() {
    if [ ! -f .env ]; then
        echo "FAIL: .env not found"
        exit 1
    fi
    set -a; source .env; set +a
    local missing=()
    for var in "${REQUIRED_VARS[@]}"; do
        if [ -z "${!var:-}" ]; then
            missing+=("$var")
        fi
    done
    if [ ${#missing[@]} -gt 0 ]; then
        echo "FAIL: Missing env vars: ${missing[*]}"
        exit 1
    fi
    if [ ! -f "$GOOGLE_SERVICE_ACCOUNT_FILE" ]; then
        echo "FAIL: $GOOGLE_SERVICE_ACCOUNT_FILE not found"
        exit 1
    fi
}

render_nginx() {
    envsubst "$ENVSUBST_VARS" < "$NGINX_TEMPLATE" > "$NGINX_CONF"
}

echo "=== BCSD API Blue-Green Deploy ==="

echo "0. Checking environment..."
check_env

echo "1. Ensuring DB services..."
$COMPOSE_DB up -d

render_nginx

CURRENT=$(current_slot)
NEXT=$(next_slot)

echo "Current: $CURRENT → Deploying: $NEXT"

echo "2. Building $NEXT..."
$COMPOSE build "api-${NEXT}"

echo "3. Running DB migrations..."
$COMPOSE run --rm --no-deps "api-${NEXT}" alembic upgrade head

echo "4. Seeding PG from Sheets (if empty)..."
$COMPOSE run --rm --no-deps "api-${NEXT}" python -m bcsd_api.sync.seed

echo "5. Starting $NEXT..."
$COMPOSE up -d --remove-orphans "api-${NEXT}"

echo "6. Health check on api-${NEXT}..."
if ! health_check "$NEXT"; then
    echo "FAIL: $NEXT did not become healthy"
    echo "--- Container logs ---"
    $COMPOSE logs --tail=30 "api-${NEXT}"
    echo "--- Stopping failed container ---"
    $COMPOSE stop "api-${NEXT}"
    exit 1
fi

echo "7. Switching nginx → $NEXT"
sed -i "s/proxy_pass http:\/\/api_${CURRENT}/proxy_pass http:\/\/api_${NEXT}/g" "$NGINX_CONF"
sudo mkdir -p /var/www/certbot
sudo cp "$NGINX_CONF" "$NGINX_AVAILABLE"
sudo ln -sf "$NGINX_AVAILABLE" "$NGINX_ENABLED"
sudo nginx -t && sudo nginx -s reload

echo "8. Stopping old ($CURRENT)..."
$COMPOSE stop "api-${CURRENT}"

echo "9. Initializing n8n..."
bash infra/scripts/init_n8n.sh

echo "=== Deploy complete: $NEXT is live ==="
