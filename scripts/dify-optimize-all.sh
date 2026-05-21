#!/usr/bin/env bash
# Полная оптимизация Avaid Support для эффективного RAG
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> 1. Sync Claude KB (10 md)"
SRC="${CLAUDE_KB_SRC:-$HOME/Загрузки}"
DEST="$ROOT/shared/knowledge/dify-kb"
mkdir -p "$DEST"
for f in akcii-ozon-i-yarlyki avtoprivyazka moysklad-integraciya podklyuchenie-magazinov \
  tarify-i-billing telegram-uvedomleniya tovary-i-formuly-tsen tseny-i-ostatki vozvrat zakazy; do
  cp "$SRC/${f}.md" "$DEST/"
done
echo "   $(ls -1 "$DEST"/*.md | wc -l) files"

echo "==> 2. Pull embedding model (Ollama)"
sg docker -c "docker exec docker-ollama-1 ollama pull ${SUPPORT_EMBED_MODEL:-nomic-embed-text}" 2>&1 | tail -3

echo "==> 3. Copy scripts and KB to Dify API"
# Создаём папки внутри контейнера
sg docker -c "docker exec docker-api-1 mkdir -p /tmp/support-agent-kb/dify-kb /tmp/support-agent-kb/rules"
# Сценарные KB-файлы (dify-kb)
sg docker -c "docker cp '$ROOT/shared/knowledge/dify-kb/.' docker-api-1:/tmp/support-agent-kb/dify-kb/"
# Правила и справочники (rules) — тоже идут в один датасет Avaid Rules
sg docker -c "docker cp '$ROOT/shared/knowledge/rules/.' docker-api-1:/tmp/support-agent-kb/rules/"
sg docker -c "docker cp '$ROOT/agents/support/prompts/system.md' docker-api-1:/tmp/system.md"
sg docker -c "docker cp '$ROOT/scripts/dify-register-embedding-docker.py' docker-api-1:/tmp/dify-register-embedding-docker.py"
sg docker -c "docker cp '$ROOT/scripts/dify-optimize-kb-docker.py' docker-api-1:/tmp/dify-optimize-kb-docker.py"
sg docker -c "docker cp '$ROOT/scripts/dify-complete-setup-docker.py' docker-api-1:/tmp/dify-complete-setup-docker.py"
sg docker -c "docker cp '$ROOT/scripts/dify-relink-kb-to-app-docker.py' docker-api-1:/tmp/dify-relink-kb-to-app-docker.py"
sg docker -c "docker cp '$ROOT/scripts/dify-diagnose-kb-docker.py' docker-api-1:/tmp/dify-diagnose-kb-docker.py"

echo "==> 4. Register embedding + optimize KB"
sg docker -c "docker exec docker-api-1 python -u /tmp/dify-register-embedding-docker.py"
sg docker -c "docker exec docker-api-1 python -u /tmp/dify-optimize-kb-docker.py"

echo "==> 5. Link app (chat, Rules only, top_k=8, no score threshold)"
sg docker -c "docker exec -e SUPPORT_RETRIEVAL_TOP_K=8 -e SUPPORT_DATASET_MODE=rules_only -e SUPPORT_LLM_MODEL=qwen2.5:14b docker-api-1 python -u /tmp/dify-relink-kb-to-app-docker.py"

echo "==> 6. Wait indexing (~90s)"
sleep 90

echo "==> 7. Smoke tests"
export GOLDEN_TIMEOUT=300
GOLDEN_ONLY=no-email-faq,wb-prices,tariffs ./scripts/run-golden-tests.sh 2>/dev/null || python3 <<'PY'
import json, subprocess, urllib.request
sql = "SELECT token FROM api_tokens WHERE app_id='5005f9d9-2d02-4422-b7e2-bdf5a518414b' ORDER BY created_at DESC LIMIT 1;"
key = subprocess.check_output(['sg','docker','-c',f'docker exec docker-db_postgres-1 psql -U postgres -d dify -tAc "{sql}"'], text=True).strip()
for q in ['почему мои цены на WB не обновляются','Какие виды тарифов есть в Avaid?']:
    p = json.dumps({'inputs':{'user_email':''},'query':q,'response_mode':'blocking','user':'opt-test'}).encode()
    r = urllib.request.Request('http://localhost/v1/chat-messages', data=p, headers={'Authorization':f'Bearer {key}','Content-Type':'application/json'}, method='POST')
    with urllib.request.urlopen(r, timeout=300) as resp:
        b = json.loads(resp.read().decode())
    print('Q:', q)
    print('A:', (b.get('answer') or '')[:400])
    for x in (b.get('metadata',{}).get('retriever_resources') or [])[:3]:
        print(' ', x.get('document_name'))
    print('---')
PY

echo ""
echo "Готово. Проверьте Studio → Knowledge → Avaid Rules:"
echo "  Indexing: High Quality, Embedding: nomic-embed-text"
echo "  Retrieval: Hybrid, Top K: 8, score threshold: выключен"
echo "  Новый чат в Avaid Support (F5)"
echo ""
echo "Если агент всё ещё не читает KB — запустите диагностику:"
echo "  docker exec docker-api-1 python -u /tmp/dify-diagnose-kb-docker.py"
