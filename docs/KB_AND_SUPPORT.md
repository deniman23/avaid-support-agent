# База знаний и поддержка Avaid

## Принцип (актуально)

| Слой | Путь | Роль |
|------|------|------|
| **dify-kb** | `shared/knowledge/dify-kb/` | 10 сценариев с Claude (что/зачем/как/В-О) → **Avaid Rules** в Dify |
| `agents/support/prompts/system.md` | Один промпт: только KB, не выдумывать | |
| `shared/codebase/` | Исходники | Для разработки и обновления текстов, **не** в RAG чата |
| `shared/db-api` | Tools | Факты по аккаунту (с email) |

Импорт KB из `~/Загрузки`:

```bash
./scripts/import-claude-kb.sh
```

Dify: **только Avaid Rules**, `high_quality` + **nomic-embed-text**, **hybrid search**, `top_k=5`, без порога score.

Полная оптимизация RAG (embedding + переиндекс + привязка app):

```bash
./scripts/dify-optimize-all.sh
```

Переиндекс одного файла после правки:

```bash
docker cp shared/knowledge/dify-kb/FILE.md docker-api-1:/tmp/support-agent-kb/dify-kb/
docker exec docker-api-1 python -u /tmp/dify-reindex-one-doc-docker.py FILE.md
```

## Структура сценария

Шаблон: `shared/knowledge/_template/scenario.md`

Frontmatter: `marketplace`, `topic`, `synonyms`, `account_tools: false`.

## Команды

```bash
# Полная настройка + опционально golden
RUN_GOLDEN=1 ./scripts/support-setup.sh

# Только пересобрать KB локально
python3 scripts/build-kb-index.py

# Только промпт/режим приложения
./scripts/dify-fix-agent.sh

# Режим с tools по аккаунту (email)
SUPPORT_ENABLE_ACCOUNT_TOOLS=1 ./scripts/dify-fix-agent.sh

# Golden: 9 сценариев бизнес-логики (~20 мин на CPU)
GOLDEN_TIMEOUT=300 ./scripts/run-golden-tests.sh

# Подмножество кейсов
GOLDEN_ONLY=ozon-linking,wb-trade-types ./scripts/run-golden-tests.sh
```

## Цикл улучшения

1. Агент ошибся → смотрите citation / какой chunk подтянулся.
2. Правите **сценарий** или **reference** в git.
3. `./scripts/support-setup.sh` или reindex + `dify-fix-agent.sh`.
4. `./scripts/run-golden-tests.sh`.

Не дописывайте бизнес-исключения в `system.md`.

## Режимы Dify

- **FAQ (default):** `mode=chat`, `SUPPORT_ENABLE_ACCOUNT_TOOLS=0` — ответ из KB, без db-api.
- **Account:** `SUPPORT_ENABLE_ACCOUNT_TOOLS=1` — agent + tools, нужен email.
