# Avaid Support Agent

Локальный агент поддержки Avaid для Dify + Ollama: правила, знания из кода, db-api (чтение + allowlist-запись), защита от утечек.

## Git (правки с ПК → сервер)

Репозиторий для настроек Dify и KB. Подробно: **[docs/GIT_WORKFLOW.md](docs/GIT_WORKFLOW.md)**.

```bash
# на сервере после вашего git push:
./scripts/server-pull-deploy.sh
```

## Быстрый старт

```bash
cd /home/eternal/support-agent
cp .env.example .env
./scripts/bootstrap.sh
```

Тестовый пользователь БД: `support@test.local` (см. `shared/db/seed.sql`).

## Структура

- `agents/support/` — промпт, Dify OpenAPI и шаблон приложения
- `shared/knowledge/scenarios/` — сценарии поддержки (источник ответов FAQ)
- `shared/knowledge/reference/` — справочники (+ legacy `rules/`)
- `shared/knowledge/style/` — законы тона
- `shared/knowledge/.dify-index/` — собранный индекс для Dify (`build-kb-index.py`)
- `shared/db-api/` — FastAPI (GET + PATCH рубильников/привязки)
- `shared/db/apply-ddl.sql` — реальная DDL
- `docs/security-tests.md` — red-team чеклист

## Docker

```bash
docker compose -f docker-compose.support.yml up -d --build
```

- Postgres: `localhost:5433`
- db-api: `http://localhost:8090` (docs: `/docs`)
- Сеть `docker_default` — для доступа из контейнеров Dify (`support-db-api:8090`)

## Dify — поддержка

```bash
./scripts/support-setup.sh       # KB → переиндекс → chat FAQ (без tools)
./scripts/run-golden-tests.sh    # регрессия эталонных вопросов
# tools по аккаунту: SUPPORT_ENABLE_ACCOUNT_TOOLS=1 ./scripts/dify-fix-agent.sh
```

Подробно: [docs/KB_AND_SUPPORT.md](docs/KB_AND_SUPPORT.md).

```bash
# Альтернатива через Studio API:
# В .env: DIFY_EMAIL, DIFY_PASSWORD
./scripts/dify-sync-to-studio.py
```

Скрипт создаёт в http://localhost:

- **Knowledge** — 3 датасета (Rules, Codebase, DB Schema)
- **Tools** — `avaid_support_db` (OpenAPI → db-api)
- **Apps** — «Avaid Support» (agent-chat + Ollama)

Дальше управляйте в UI: **[docs/DIFY_CONTROL.md](docs/DIFY_CONTROL.md)** — карта экранов, промпт, tools, publish, логи.

## Безопасность

- db-api: allowlist полей, scope по `user_id`, без `api_key`/`password`
- Промпт: блок SECURITY в `agents/support/prompts/system.md`
- KB: без сырого кода и секретов (`build-codebase-knowledge.py` фильтрует)

## Подключение реальной БД (read + write)

1. На prod выполните один раз (суперпользователь):

```bash
psql "$ADMIN_DATABASE_URL" -f shared/db/init-support-writer.sql
```

2. В `.env` укажите prod URL и режим:

```bash
DATABASE_URL=postgresql://support_writer:ПАРОЛЬ@HOST:5432/ИМЯ_БД
DB_API_MODE=readwrite   # или readonly — только GET
USE_MOCK_DB=0
```

3. Запуск без mock Postgres:

```bash
chmod +x scripts/connect-prod-db.sh
./scripts/connect-prod-db.sh
```

Запись только через фиксированные PATCH (рубильники `shops`, `sync_stocks`/`sync_prices`, привязка `ms_product_id`). Тарифы и `users.password` не меняются.

4. В Dify переимпортируйте OpenAPI tools: `./scripts/dify-complete-setup.sh`

## Безопасность prod

- db-api только во внутренней сети / VPN
- отдельная роль `support_writer`, не admin
- при риске отключите запись: `DB_API_MODE=readonly`
