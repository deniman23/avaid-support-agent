#!/usr/bin/env bash
# Быстрое исправление: русский промпт + OpenAPI с user_email (без переиндексации KB)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

sg docker -c "docker compose -f docker-compose.support.yml up -d --build support-db-api" 2>/dev/null || \
  sg docker -c "docker compose -f $ROOT/docker-compose.support.yml up -d --build support-db-api"

sg docker -c "docker cp '$ROOT/agents/support/dify/openapi-db-api.yaml' docker-api-1:/tmp/openapi-db-api.yaml"
sg docker -c "docker cp '$ROOT/agents/support/prompts/system.md' docker-api-1:/tmp/system.md"
sg docker -c "docker cp '$ROOT/scripts/dify-complete-setup-docker.py' docker-api-1:/tmp/dify-complete-setup-docker.py"

echo "==> Rebuild db-api + update Dify agent (codebase + tariff tool)"
sg docker -c "docker compose -f docker-compose.support.yml up -d --build support-db-api" 2>/dev/null || true

echo "==> Update prompt + tools"
sg docker -c "docker exec -e DIFY_SETUP_PROMPT_ONLY=1 -e SUPPORT_DATASET_MODE=codebase_only -e SUPPORT_ENABLE_ACCOUNT_TOOLS=0 docker-api-1 python -u /tmp/dify-complete-setup-docker.py"

echo ""
echo "Готово. FAQ без email. Для tools по аккаунту: SUPPORT_ENABLE_ACCOUNT_TOOLS=1 $0"
echo "Полная пересборка KB: ./scripts/support-setup.sh"
