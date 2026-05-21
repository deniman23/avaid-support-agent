#!/usr/bin/env bash
# Подтянуть модель в Ollama, зарегистрировать в Dify, переключить Avaid Support
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# qwen3:8b — быстрее 14b, умнее qwen2.5:7b; qwen3:14b — максимум качества
MODEL="${SUPPORT_LLM_MODEL:-qwen3:8b}"
TENANT="${DIFY_TENANT_ID:-11aad9d2-e6a0-41fc-b8a1-5bf10ab4518f}"

echo "==> Pull Ollama model: ${MODEL}"
sg docker -c "docker exec docker-ollama-1 ollama pull ${MODEL}"

echo "==> Register in Dify + switch Avaid Support"
sg docker -c "docker cp '$ROOT/scripts/dify-register-model.py' docker-api-1:/tmp/dify-register-model.py"
sg docker -c "docker exec -e SUPPORT_LLM_MODEL=${MODEL} -e DIFY_TENANT_ID=${TENANT} docker-api-1 python -u /tmp/dify-register-model.py"

sg docker -c "docker cp '$ROOT/scripts/dify-complete-setup-docker.py' docker-api-1:/tmp/dify-complete-setup-docker.py"
sg docker -c "docker cp '$ROOT/agents/support/prompts/system.md' docker-api-1:/tmp/system.md"
sg docker -c "docker exec -e DIFY_SETUP_PROMPT_ONLY=1 -e SUPPORT_LLM_MODEL=${MODEL} docker-api-1 python -u /tmp/dify-complete-setup-docker.py"

echo ""
echo "Готово. Модель приложения: ${MODEL}"
echo "Studio → Avaid Support → Model — проверьте. Новый чат (F5)."
