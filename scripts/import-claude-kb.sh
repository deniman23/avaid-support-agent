#!/usr/bin/env bash
# Импорт KB из ~/Загрузки (10 md с Claude) → Dify Avaid Rules, только сценарии
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="${CLAUDE_KB_SRC:-$HOME/Загрузки}"
DEST="$ROOT/shared/knowledge/dify-kb"

FILES=(
  akcii-ozon-i-yarlyki.md
  avtoprivyazka.md
  moysklad-integraciya.md
  podklyuchenie-magazinov.md
  tarify-i-billing.md
  telegram-uvedomleniya.md
  tovary-i-formuly-tsen.md
  tseny-i-ostatki.md
  vozvrat.md
  zakazy.md
)

echo "==> Copy Claude KB from $SRC"
mkdir -p "$DEST"
for f in "${FILES[@]}"; do
  if [[ ! -f "$SRC/$f" ]]; then
    echo "Missing: $SRC/$f" >&2
    exit 1
  fi
  cp "$SRC/$f" "$DEST/"
done
echo "   $(ls -1 "$DEST"/*.md | wc -l) files in $DEST"

echo "==> Upload to Dify API container"
sg docker -c "docker exec docker-api-1 mkdir -p /tmp/support-agent-kb/dify-kb"
sg docker -c "docker cp '$DEST/.' docker-api-1:/tmp/support-agent-kb/dify-kb/"
sg docker -c "docker cp '$ROOT/agents/support/prompts/system.md' docker-api-1:/tmp/system.md"
sg docker -c "docker cp '$ROOT/scripts/dify-reindex-kb-docker.py' docker-api-1:/tmp/dify-reindex-kb-docker.py"
sg docker -c "docker cp '$ROOT/scripts/dify-complete-setup-docker.py' docker-api-1:/tmp/dify-complete-setup-docker.py"

echo "==> Reindex Avaid Rules (replace all)"
sg docker -c "docker exec -e DIFY_DATASET_NAME='Avaid Rules' -e DIFY_KB_SUBDIR=dify-kb docker-api-1 python -u /tmp/dify-reindex-kb-docker.py"

echo "==> App: chat + только Avaid Rules, top_k=5"
sg docker -c "docker exec -e DIFY_SETUP_PROMPT_ONLY=1 -e SUPPORT_DATASET_MODE=rules_only -e SUPPORT_ENABLE_ACCOUNT_TOOLS=0 -e SUPPORT_LLM_MODEL=qwen2.5:14b docker-api-1 python -u /tmp/dify-complete-setup-docker.py"

echo ""
echo "Готово. Studio → Avaid Support → новый чат (F5)."
echo "Проверка: Knowledge → Avaid Rules → Hit testing → «почему цены на WB не обновляются»"
