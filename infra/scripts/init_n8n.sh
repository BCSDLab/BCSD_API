#!/usr/bin/env bash
set -euo pipefail

# n8n init: owner setup + first-time workflow import only
# Workflows persist in n8n volume — reimport skipped if already exist
# Credentials set up manually in n8n UI on first deploy
# Workflow changes: edit in n8n UI, then export to workflows/*.json for versioning

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
    local id="$1"
    $COMPOSE exec -T n8n n8n list:workflow 2>&1 | grep -q "$id"
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

import_if_new() {
    local file="$1"
    local id="$2"
    if workflow_exists "$id"; then
        echo "  $id — already exists, skipping (edit in n8n UI)"
        return 0
    fi
    echo "  $id — first import"
    $COMPOSE exec -T n8n n8n import:workflow --input="$file" 2>&1
    $COMPOSE exec -T n8n n8n publish:workflow --id="$id" 2>&1 || true
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

echo "4. Importing workflows..."
# Force reimport to apply JSON changes (credential links via predefinedCredentialType)
$COMPOSE exec -T n8n n8n import:workflow --input="/workflows/pg_sheets_sync.json" 2>&1
$COMPOSE exec -T n8n n8n import:workflow --input="/workflows/link_auto_expire.json" 2>&1
$COMPOSE exec -T n8n n8n publish:workflow --id="pg-sheets-sync" 2>&1 || true
$COMPOSE exec -T n8n n8n publish:workflow --id="link-auto-expire" 2>&1 || true

echo "=== n8n Init complete ==="
