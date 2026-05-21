#!/usr/bin/env bash
# Добавить маркетплейсы_список.md в Avaid Rules + обновить промпт
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

RULES_FILE="$ROOT/shared/knowledge/rules/маркетплейсы_список.md"
if [[ ! -f "$RULES_FILE" ]]; then
  echo "Нет файла: $RULES_FILE"
  exit 1
fi

sg docker -c "docker cp '$RULES_FILE' docker-api-1:/tmp/маркетплейсы_список.md"
sg docker -c "docker cp '$ROOT/scripts/dify-add-rules-doc-docker.py' docker-api-1:/tmp/dify-add-rules-doc-docker.py"
sg docker -c "docker exec docker-api-1 python -u /tmp/dify-add-rules-doc-docker.py /tmp/маркетплейсы_список.md"

./scripts/dify-fix-agent.sh
echo "Готово: KB + промпт. Новый чат в Avaid Support."
