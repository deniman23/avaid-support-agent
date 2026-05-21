# Управление агентом в Dify Studio

**Dify — главная панель управления.** Файлы в `support-agent/` — исходники для синхронизации; править поведение удобнее в Studio, чтобы всё было на виду.

## Быстрая синхронизация в Studio

```bash
cd /home/eternal/support-agent
# В .env укажите DIFY_EMAIL и DIFY_PASSWORD
./scripts/dify-sync-to-studio.py
```

После скрипта откройте http://localhost

---

## Карта интерфейса

| Что контролировать | Где в Dify | URL |
|--------------------|------------|-----|
| **Правила, законы, тарифы** | Knowledge → **Avaid Rules** | http://localhost/datasets |
| **Знания из кода** | Knowledge → **Avaid Codebase** | http://localhost/datasets |
| **Схема БД (внутр.)** | Knowledge → **Avaid DB Schema** | http://localhost/datasets |
| **Промпт, модель, память** | Studio → **Avaid Support** → Prompt / Model | http://localhost/apps |
| **Tools (остатки, заказы…)** | Studio → Agent → Tools | внутри приложения |
| **API к db-api** | Tools → Custom → **avaid_support_db** | http://localhost/tools |
| **Переменные чата** | Studio → Variables (`user_email`) | внутри приложения |
| **Публикация чата** | Studio → Publish | внутри приложения |
| **Диалоги и логи** | Logs / Annotations | внутри приложения |
| **Модель Ollama** | Settings → Model Provider | http://localhost/plugins |

---

## 1. Knowledge (семантическая память)

**Путь:** левое меню → **Knowledge**

Три датасета (создаёт `dify-sync-to-studio.py`):

1. **Avaid Rules** — 8 MD + законы  
2. **Avaid Codebase** — выжимки из Go  
3. **Avaid DB Schema** — глоссарий для агента  

**Что можно делать в UI:**

- Просмотр чанков, hit testing («проверка поиска»)
- Добавить/удалить документ
- Изменить chunk size, rerank
- Переиндексировать после правки файлов на диске → снова запустить sync-скрипт

**Обновление с диска:**

```bash
python3 scripts/build-codebase-knowledge.py   # после изменения zip
./scripts/dify-sync-to-studio.py              # залить в Dify
```

---

## 2. Tools — db-api (факты из БД)

**Путь:** **Tools** → вкладка **API** → **avaid_support_db**

| Параметр | Значение |
|----------|----------|
| Server URL | `http://host.docker.internal:8090` (Dify в Docker) |
| Auth header | `X-Support-Api-Key` = из `support-agent/.env` → `SUPPORT_API_KEY` |

**В приложении Avaid Support:**

Studio → **Agent** → **Tools** → включить нужные:

- `supportShops`, `supportStockCheck`, `supportStockIssues`
- `supportPricesCheck`, `supportOrdersRecent`, `supportBillingStatus`
- и т.д.

**Заголовок пользователя** (чтобы не видеть чужие данные):

В настройках tool или в **Variables** приложения:

- Переменная `user_email` (обязательная в чате)
- Custom header: `X-Dify-User-Email` = `{{user_email}}` (синтаксис переменных Dify в вашей версии)

Тестовый email для локали: `support@test.local`

---

## 3. Приложение Avaid Support

**Путь:** **Studio** → **Avaid Support**

### Prompt

Вкладка **Prompt** — системные инструкции (из `agents/support/prompts/system.md`).

Редактируйте здесь: тон, SECURITY, сценарии. Файл на диске — только backup; **источник правды — Dify**.

### Model

- Provider: **Ollama**
- Model: `qwen2.5:14b` (или `7b`)
- Temperature: ~0.3

### Knowledge retrieval

В Agent включены 3 датасета. Настройки:

- Top K: 4
- Score threshold: по желанию

### Agent

- Strategy: Function calling  
- Max iterations: 5  
- Tools: db-api + retrieval  

### Features

| Функция | Рекомендация |
|---------|----------------|
| File upload | **Выключить** |
| Opening statement | Приветствие + подсказки |
| Suggested questions | Остатки, цены, заказы… |
| Sensitive words | password, api_key, SELECT *, ignore instructions |

### Variables

| Имя | Назначение |
|-----|------------|
| `user_email` | Идентификация клиента для db-api |
| `shop_id` | (опционально) после уточнения в диалоге |

### Publish

**Publish** → Web App → ссылка на чат (локально `http://localhost/...`).

---

## 4. Мониторинг

- **Logs** — все диалоги  
- **Annotations** — разметка плохих ответов  
- db-api аудит: `docker logs support-db-api` или volume `support_audit`

---

## 5. Двусторонняя работа: диск ↔ Dify

| Задача | Где править |
|--------|-------------|
| Тон, законы, SECURITY | **Dify Prompt** (или rules MD + sync) |
| Новый сценарий в KB | `shared/knowledge/rules/` + sync |
| Обновить знания из кода | `build-codebase-knowledge.py` + sync |
| Новый endpoint БД | `shared/db-api/` + OpenAPI + Tools в Dify |
| Модель / температура | **Dify Model** |

---

## 6. Checklist «всё под контролем»

- [ ] В Knowledge видны 3 датасета с документами  
- [ ] Hit testing по «остатки» находит `общие_правила`  
- [ ] В Tools есть `avaid_support_db`, тест tool возвращает JSON  
- [ ] В Apps есть **Avaid Support**, mode Agent  
- [ ] В Agent подключены tools и 3 KB  
- [ ] Publish открывается, тест с `support@test.local`  
- [ ] Red-team из `docs/security-tests.md` — без утечек  
