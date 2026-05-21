# Настройка Dify «Avaid Support»

## 1. Knowledge (3 датасета)

| Имя | Путь |
|-----|------|
| Avaid Rules | `shared/knowledge/rules/` |
| Avaid Codebase | `shared/knowledge/codebase/` |
| Avaid DB Schema | `shared/docs/db-schema-for-agent.md` |

Индексация: высокий quality, chunk ~500–800 tokens.

## 2. Tool db-api

Studio → Tools → Import OpenAPI → `agents/support/dify/openapi-db-api.yaml`

- Server URL: `http://support-db-api:8090` (из Docker Dify) или `http://host.docker.internal:8090`
- Custom headers:
  - `X-Support-Api-Key`: значение из `.env` (`SUPPORT_API_KEY`)
  - `X-Dify-User-Email`: `{{user_email}}` (conversation variable)

## 3. Agent app

- Mode: **Agent Chat**
- Model: Ollama **qwen2.5:14b** (качество ↑; 7b быстрее, но чаще галлюцинирует)

Переключение модели одной командой:

```bash
./scripts/dify-upgrade-model.sh
# или другая: SUPPORT_LLM_MODEL=qwen2.5:32b ./scripts/dify-upgrade-model.sh
```
- System prompt: вставить `agents/support/prompts/system.md`
- Knowledge: все 3 датасета
- Tools: все эндпоинты OpenAPI
- Variables: `user_email` (required) — для теста `support@test.local`
- File upload: **off**
- Sensitive words: см. `agents/support/dify/avaid-support.yml`

## 4. Publish

`http://localhost` → приложение **Avaid Support**

## 5. Проверка

`docs/security-tests.md` и `scripts/test-api.sh`
