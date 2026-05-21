#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

# shellcheck disable=SC1091
source .env 2>/dev/null || true

echo "==> Build codebase KB"
python3 scripts/build-codebase-knowledge.py

echo "==> Start support DB + db-api"
if command -v docker >/dev/null 2>&1; then
  if [[ "${USE_MOCK_DB:-1}" == "1" ]]; then
    docker compose -f docker-compose.support.yml up -d --build
    echo "Waiting for postgres..."
    sleep 8
    if docker exec support-db psql -U admin -d avaid_support -tAc \
      "SELECT 1 FROM pg_roles WHERE rolname='support_writer'" 2>/dev/null | grep -q 1; then
      :
    else
      echo "Applying support_writer role on mock DB..."
      docker exec -i support-db psql -U admin -d avaid_support \
        < "$ROOT/shared/db/init-support-writer.sql" || true
    fi
  else
    docker compose -f docker-compose.prod.yml up -d --build
    sleep 4
  fi
else
  echo "Docker not found — start manually: docker compose -f docker-compose.support.yml up -d --build"
fi

echo "==> Health check db-api"
for i in {1..15}; do
  if curl -sf http://localhost:8090/health >/dev/null 2>&1; then
    echo "db-api OK"
    break
  fi
  sleep 2
done

API_KEY="${SUPPORT_API_KEY:-change-me-local-dev-key}"
echo "==> API smoke test"
curl -sf -H "X-Support-Api-Key: $API_KEY" \
  -H "X-Dify-User-Email: support@test.local" \
  http://localhost:8090/support/shops | head -c 400
echo ""

echo "==> Ollama models (if ollama installed)"
if command -v ollama >/dev/null 2>&1; then
  ollama pull qwen2.5:14b || true
  ollama pull qwen2.5:7b || true
else
  echo "Install ollama and run: ollama pull qwen2.5:14b"
fi

echo ""
echo "==> Dify Studio (Knowledge + Tools + App)"
if [[ -x scripts/dify-complete-setup.sh ]]; then
  ./scripts/dify-complete-setup.sh || true
fi
