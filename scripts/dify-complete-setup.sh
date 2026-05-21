#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> Build KB index"
python3 "$ROOT/scripts/build-kb-index.py"

echo "==> Copy KB + scripts to docker-api-1"
sg docker -c "docker exec docker-api-1 mkdir -p /tmp/support-agent-kb/index"
sg docker -c "docker cp '$ROOT/shared/knowledge/.dify-index/.' docker-api-1:/tmp/support-agent-kb/index/"
sg docker -c "docker cp '$ROOT/agents/support/dify/openapi-db-api.yaml' docker-api-1:/tmp/openapi-db-api.yaml"
sg docker -c "docker cp '$ROOT/agents/support/prompts/system.md' docker-api-1:/tmp/system.md"
sg docker -c "docker cp '$ROOT/scripts/dify-complete-setup-docker.py' docker-api-1:/tmp/dify-complete-setup-docker.py"
sg docker -c "docker cp '$ROOT/scripts/dify-reindex-kb-docker.py' docker-api-1:/tmp/dify-reindex-kb-docker.py"

echo "==> Reindex + setup app"
sg docker -c "docker exec docker-api-1 python -u /tmp/dify-reindex-kb-docker.py"
sg docker -c "docker exec -e SUPPORT_ENABLE_ACCOUNT_TOOLS=0 docker-api-1 python -u /tmp/dify-complete-setup-docker.py"

echo ""
echo "Откройте http://localhost/apps → Avaid Support (F5, новый чат)"
