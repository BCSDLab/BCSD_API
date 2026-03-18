#!/usr/bin/env bash
set -euo pipefail

# n8n workflow import + owner setup + Postgres credential
# Idempotent: skips if already configured
# Google Sheets credential must be set up manually in n8n UI

COMPOSE="sudo docker compose -p bcsd-app --env-file .env -f infra/docker/docker-compose.yml"
MAX_RETRIES=15

wait_n8n() {
    local retries=0
    while [ $retries -lt $MAX_RETRIES ]; do
        if $COMPOSE exec -T n8n wget -qO- http://localhost:5678/healthz > /dev/null 2>&1; then
            return 0
        fi
        retries=$((retries + 1))
        echo "  n8n not ready, retry ${retries}/${MAX_RETRIES}..."
        sleep 2
    done
    return 1
}

workflow_exists() {
    local name="$1"
    local count
    count=$($COMPOSE exec -T n8n n8n list:workflow 2>&1 | grep -c "$name" || true)
    [ "$count" -gt 0 ]
}

import_workflow() {
    local file="$1"
    local name="$2"
    if workflow_exists "$name"; then
        echo "  Workflow '$name' already exists — skipping"
        return 0
    fi
    echo "  Importing '$name'..."
    $COMPOSE exec -T n8n n8n import:workflow --input="$file"
}

setup_owner() {
    set -a; source .env; set +a
    local port
    port=$(grep -m1 '^N8N_PORT=' .env | cut -d= -f2-)
    local status
    status=$(curl -sf "http://localhost:${port}/rest/settings" 2>/dev/null | python3 -c "
import json, sys
d = json.load(sys.stdin)
print('setup' if d.get('userManagement',{}).get('showSetupOnFirstLoad') else 'done')
" 2>/dev/null || echo "unknown")
    if [ "$status" != "setup" ]; then
        echo "  Owner already configured — skipping"
        return 0
    fi
    echo "  Creating owner account..."
    curl -sf -X POST "http://localhost:${port}/rest/owner/setup" \
        -H "Content-Type: application/json" \
        -d "{
            \"email\": \"${N8N_AUTH_USER}@bcsdlab.com\",
            \"firstName\": \"BCSD\",
            \"lastName\": \"Admin\",
            \"password\": \"${N8N_AUTH_PASSWORD}\"
        }" > /dev/null
    echo "  Owner created: ${N8N_AUTH_USER}@bcsdlab.com"
}

setup_pg_credential() {
    local existing
    existing=$($COMPOSE exec -T n8n n8n list:credential 2>&1 | grep -c "BCSD PostgreSQL" || true)
    if [ "$existing" -gt 0 ]; then
        echo "  Postgres credential already exists — skipping"
        return 0
    fi
    echo "  Creating Postgres credential from .env..."
    set -a; source .env; set +a
    local cred_json
    cred_json=$(python3 -c "
import json, sys, uuid
cred = [{
    'id': str(uuid.uuid4()),
    'name': 'BCSD PostgreSQL',
    'type': 'postgres',
    'data': {
        'host': '${POSTGRES_HOST:-postgres}',
        'port': ${POSTGRES_PORT:-5432},
        'database': '${POSTGRES_DB}',
        'user': '${POSTGRES_USER}',
        'password': '${POSTGRES_PASSWORD}',
        'ssl': 'disable'
    }
}]
json.dump(cred, sys.stdout)
")
    echo "$cred_json" | $COMPOSE exec -T n8n n8n import:credentials --input=/dev/stdin
}

echo "=== n8n Init ==="

echo "1. Starting n8n..."
$COMPOSE up -d n8n

echo "2. Waiting for n8n..."
if ! wait_n8n; then
    echo "FAIL: n8n did not become healthy"
    $COMPOSE logs --tail=20 n8n
    exit 1
fi

echo "3. Setting up owner account..."
setup_owner

echo "4. Setting up Postgres credential..."
setup_pg_credential

echo "5. Importing workflows..."
import_workflow "/workflows/pg_sheets_sync.json" "PG → Sheets Sync (5min)"
import_workflow "/workflows/link_auto_expire.json" "Link Auto-Expiration (hourly)"

echo "=== n8n Init complete ==="
echo "NOTE: Set up Google Sheets credential in n8n UI if first deploy"
