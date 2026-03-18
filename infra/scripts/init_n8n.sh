#!/usr/bin/env bash
set -euo pipefail

# n8n workflow import + Google Sheets credential setup
# Idempotent: skips if workflows already exist

COMPOSE="sudo docker compose -p bcsd-app --env-file .env -f infra/docker/docker-compose.yml"
N8N_CONTAINER="bcsd-app-n8n-1"
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
    count=$($COMPOSE exec -T n8n n8n list:workflow 2>/dev/null | grep -c "$name" || true)
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

activate_workflow() {
    local name="$1"
    local wf_id
    wf_id=$($COMPOSE exec -T n8n n8n list:workflow 2>/dev/null | grep "$name" | awk '{print $1}')
    if [ -z "$wf_id" ]; then
        echo "  WARNING: Could not find workflow '$name' to activate"
        return 1
    fi
    $COMPOSE exec -T n8n n8n update:workflow --id="$wf_id" --active=true
    echo "  Activated '$name' (id: $wf_id)"
}

setup_credential() {
    local existing
    existing=$($COMPOSE exec -T n8n n8n list:credential 2>/dev/null | grep -c "Google Sheets SA" || true)
    if [ "$existing" -gt 0 ]; then
        echo "  Google Sheets credential already exists — skipping"
        return 0
    fi
    echo "  Creating Google Sheets service account credential..."
    local cred_json
    cred_json=$(python3 -c "
import json, sys
sa = json.load(open('$GOOGLE_SERVICE_ACCOUNT_FILE'))
cred = [{
    'name': 'Google Sheets SA',
    'type': 'googleApi',
    'data': {
        'email': sa['client_email'],
        'privateKey': sa['private_key'],
        'impersonateUser': ''
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

echo "3. Importing workflows..."
import_workflow "/workflows/pg_sheets_sync.json" "PG → Sheets Sync (5min)"
import_workflow "/workflows/link_auto_expire.json" "Link Auto-Expiration (hourly)"

echo "4. Setting up Google Sheets credential..."
set -a; source .env; set +a
setup_credential

echo "5. Activating workflows..."
activate_workflow "PG → Sheets Sync"
activate_workflow "Link Auto-Expiration"

echo "=== n8n Init complete ==="
