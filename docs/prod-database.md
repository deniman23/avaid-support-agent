# Подключение боевой PostgreSQL

## 1. Роль на сервере БД

От имени суперпользователя (один раз). Если имя БД не `avaid_support`, отредактируйте строку `GRANT CONNECT ON DATABASE` в файле.

```bash
psql "postgresql://admin:...@HOST:5432/my_project" -f shared/db/init-support-writer.sql
ALTER ROLE support_writer WITH PASSWORD 'надёжный-пароль';
```

## 2. `.env`

```env
USE_MOCK_DB=0
DATABASE_URL=postgresql://support_writer:надёжный-пароль@HOST:5432/my_project
DB_API_MODE=readwrite
SUPPORT_API_KEY=длинный-секрет-для-dify
```

Только чтение с prod: `DB_API_MODE=readonly` и пользователь `support_reader` (см. `init-support-reader.sql`).

## 3. Запуск db-api

```bash
./scripts/connect-prod-db.sh
```

Проверка: `curl -s http://localhost:8090/health` → `"database":"up"`.

## 4. Dify

Переимпорт tools с новыми PATCH-операциями:

```bash
./scripts/dify-complete-setup.sh
```

## Что можно менять через API

| PATCH | Поля |
|-------|------|
| `/support/shops/{id}/settings` | `sync_stock`, `sync_price`, `is_active`, `processes_new_orders` |
| `/support/products/{id}/sync` | `sync_stocks`, `sync_prices` |
| `/support/products/{id}/link` | `ms_product_id` (только свой user) |

Тарифы, пароли, `api_key` — **не** доступны.
