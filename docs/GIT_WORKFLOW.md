# Git: правки с ПК → деплой на сервер

Репозиторий — **`support-agent`**: промпт, база знаний, скрипты синхронизации с Dify, golden-тесты.  
Сам Dify (`/home/eternal/dify`) — отдельная установка через Docker; в git не кладём.

## Что в git, что нет

| В git | Не в git (остаётся на сервере) |
|-------|--------------------------------|
| `agents/support/prompts/system.md` | `.env` (секреты, Dify login) |
| `shared/knowledge/scenarios/`, `dify-kb/` | `shared/codebase/avaid_main-dev/` (клон кода) |
| `scripts/*.sh`, `*.py` | `shared/knowledge/codebase-raw/` (генерируется) |
| `tests/support-golden.json` | `shared/knowledge/.dify-index/` (генерируется) |

## 1. Один раз: remote (GitHub / GitLab)

На **сервере** уже есть локальный репозиторий. Создайте пустой репозиторий на GitHub (например `avaid-support-agent`) и привяжите:

```bash
cd /home/eternal/support-agent
git branch -M main
git remote add origin git@github.com:ВАШ_АККАУНТ/avaid-support-agent.git
git push -u origin main
```

## 2. На вашем компьютере

```bash
git clone git@github.com:ВАШ_АККАУНТ/avaid-support-agent.git
cd avaid-support-agent
cp .env.example .env   # только если поднимаете db-api локально
```

Редактируете в основном:

- `shared/knowledge/scenarios/` — сценарии FAQ
- `shared/knowledge/dify-kb/` — документы для Knowledge
- `agents/support/prompts/system.md` — системный промпт
- `tests/support-golden.json` — эталонные вопросы

Коммит и push:

```bash
git add -A
git commit -m "KB: уточнил автопривязку Ozon"
git push
```

## 3. На сервере (после push)

```bash
cd /home/eternal/support-agent
./scripts/server-pull-deploy.sh
```

Скрипт: `git pull` → `support-setup.sh` (копия в Dify + переиндекс KB + промпт) → golden-тесты.

Без тестов (быстрее):

```bash
RUN_GOLDEN=0 ./scripts/server-pull-deploy.sh
```

## 4. Агент Cursor на сервере

После push напишите в чат, например: **«задеплой изменения»** — агент выполнит `server-pull-deploy.sh` и сообщит результат тестов.

## Обновление исходников Go (codebase KB)

Если менялся код в `avaid_main-dev`:

```bash
# на сервере, вне git
cd /path/to/avaid_main-dev && git pull
cd /home/eternal/support-agent
CODEBASE_INDEX_MODE=raw ./scripts/support-setup.sh
```

## SSH-ключ для push с ПК

```bash
ssh-keygen -t ed25519 -C "your@email"
cat ~/.ssh/id_ed25519.pub   # добавить в GitHub → Settings → SSH keys
```
