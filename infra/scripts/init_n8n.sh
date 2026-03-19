#!/usr/bin/env bash
set -euo pipefail

# n8n workflow import + owner setup
# Idempotent: skips if already configured
# Credentials (Postgres, Google Sheets) must be set up manually in n8n UI

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

delete_workflow() {
    local name="$1"
    if ! workflow_exists "$name"; then
        return 0
    fi
    local wf_id
    wf_id=$($COMPOSE exec -T n8n n8n list:workflow 2>&1 | grep "$name" | awk -F'|' '{print $1}')
    echo "  Deleting old workflow '$name' (id: $wf_id)..."
    $COMPOSE exec -T n8n n8n delete:workflow --id="$wf_id" 2>&1 || true
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

echo "=== n8n Init ==="

echo "1. Starting n8n..."
$COMPOSE up -d --force-recreate n8n

echo "2. Waiting for n8n..."
if ! wait_n8n; then
    echo "FAIL: n8n did not become healthy"
    $COMPOSE logs --tail=20 n8n
    exit 1
fi

echo "3. Setting up owner account..."
setup_owner

echo "4. Replacing workflows..."
delete_workflow "Link Auto-Expiration (hourly)"
delete_workflow "Link Auto-Expiration (1min)"
delete_workflow "PG → Sheets Sync (5min)"

echo "5. Importing workflows..."
$COMPOSE exec -T n8n n8n import:workflow --input="/workflows/pg_sheets_sync.json" 2>&1
$COMPOSE exec -T n8n n8n import:workflow --input="/workflows/link_auto_expire.json" 2>&1

echo "=== n8n Init complete ==="
echo "NOTE: Set up Postgres + Google Sheets credentials in n8n UI if first deploy"
