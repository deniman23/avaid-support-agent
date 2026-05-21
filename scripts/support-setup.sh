#!/usr/bin/env bash
# Полная настройка: Rules + Codebase (сырой Go) → Dify → chat FAQ
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# raw = индекс .go из avaid_main-dev (без domain-autolink.md)
# summaries = старые выжимки domain-*.md
CODEBASE_INDEX_MODE="${CODEBASE_INDEX_MODE:-raw}"

echo "==> 1. Build KB from scenarios (UI FAQ, опционально)"
python3 scripts/build-kb-index.py

if [[ "$CODEBASE_INDEX_MODE" == "raw" ]]; then
  echo "==> 2. Prepare Go sources for Dify (backend-go, без domain-*.md)"
  python3 scripts/prepare-codebase-raw-for-dify.py
  CODEBASE_SRC="codebase-raw"
  CODEBASE_EXT="txt"
else
  echo "==> 2. Build markdown summaries from Go (legacy)"
  python3 scripts/build-codebase-knowledge.py
  CODEBASE_SRC="codebase"
  CODEBASE_EXT="md"
fi

echo "==> 3. Copy to Dify API container"
sg docker -c "docker exec docker-api-1 mkdir -p /tmp/support-agent-kb/index /tmp/support-agent-kb/${CODEBASE_SRC} /tmp/support-agent-kb/codebase-billing"
sg docker -c "docker cp '$ROOT/shared/knowledge/.dify-index/.' docker-api-1:/tmp/support-agent-kb/index/"
sg docker -c "docker cp '$ROOT/shared/knowledge/${CODEBASE_SRC}/.' docker-api-1:/tmp/support-agent-kb/${CODEBASE_SRC}/"
sg docker -c "docker cp '$ROOT/shared/knowledge/codebase-billing/.' docker-api-1:/tmp/support-agent-kb/codebase-billing/"
sg docker -c "docker cp '$ROOT/agents/support/dify/openapi-db-api.yaml' docker-api-1:/tmp/openapi-db-api.yaml"
sg docker -c "docker cp '$ROOT/agents/support/prompts/system.md' docker-api-1:/tmp/system.md"
sg docker -c "docker cp '$ROOT/scripts/dify-complete-setup-docker.py' docker-api-1:/tmp/dify-complete-setup-docker.py"
sg docker -c "docker cp '$ROOT/scripts/dify-reindex-kb-docker.py' docker-api-1:/tmp/dify-reindex-kb-docker.py"

echo "==> 4. Reindex Avaid Rules"
sg docker -c "docker exec -e DIFY_DATASET_NAME='Avaid Rules' -e DIFY_KB_SUBDIR=index docker-api-1 python -u /tmp/dify-reindex-kb-docker.py"

echo "==> 5. Reindex Avaid Codebase (${CODEBASE_INDEX_MODE})"
sg docker -c "docker exec -e DIFY_DATASET_NAME='Avaid Codebase' -e DIFY_KB_SUBDIR=${CODEBASE_SRC} -e DIFY_KB_EXTENSIONS=${CODEBASE_EXT} docker-api-1 python -u /tmp/dify-reindex-kb-docker.py"

echo "==> 5b. Reindex Avaid Billing (тарифы из Go)"
sg docker -c "docker exec -e DIFY_DATASET_NAME='Avaid Billing' -e DIFY_KB_SUBDIR=codebase-billing -e DIFY_KB_EXTENSIONS=txt docker-api-1 python -u /tmp/dify-reindex-kb-docker.py"

echo "==> 6. Link app: chat + Codebase + Billing (без account tools)"
sg docker -c "docker exec -e DIFY_SETUP_PROMPT_ONLY=1 -e SUPPORT_DATASET_MODE=codebase_only -e SUPPORT_ENABLE_ACCOUNT_TOOLS=0 -e SUPPORT_LLM_MODEL=qwen2.5:14b docker-api-1 python -u /tmp/dify-complete-setup-docker.py"

sg docker -c "docker cp '$ROOT/scripts/dify-ensure-app-token-docker.py' docker-api-1:/tmp/dify-ensure-app-token-docker.py"
sg docker -c "docker exec docker-api-1 python -u /tmp/dify-ensure-app-token-docker.py" >/dev/null 2>&1 || true

if [[ "${RUN_GOLDEN:-0}" == "1" ]]; then
  echo "==> 7. Golden tests (wait ~60s for indexing)"
  sleep 60
  ./scripts/run-golden-tests.sh
fi

RULES_N=$(find shared/knowledge/.dify-index -name '*.md' | wc -l)
CODE_N=$(find "shared/knowledge/${CODEBASE_SRC}" -type f | wc -l)
echo ""
echo "Готово. Avaid Support: Rules ($RULES_N) + Codebase ($CODE_N files, mode=$CODEBASE_INDEX_MODE)"
echo "  Исходники: shared/codebase/avaid_main-dev"
echo "  Переиндекс: ./scripts/support-setup.sh"
