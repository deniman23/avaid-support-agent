#!/usr/bin/env python3
"""
Синхронизация support-agent → Dify Studio (Knowledge, Tools, App).

После запуска всё видно в http://localhost:
  Knowledge — 3 датасета
  Tools — avaid_support_db
  Studio — приложение «Avaid Support»

Требуется в .env:
  DIFY_EMAIL=...
  DIFY_PASSWORD=...
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).parent))

from dify_client import DifyClient  # noqa: E402

DATASETS = [
    ("Avaid Rules", ROOT / "shared/knowledge/rules", "Правила и законы агента"),
    ("Avaid Codebase", ROOT / "shared/knowledge/codebase", "Знания из кода (выжимки)"),
    ("Avaid DB Schema", ROOT / "shared/docs/db-schema-for-agent.md", "Глоссарий БД для tools"),
]

APP_NAME = "Avaid Support"
TOOL_PROVIDER = "avaid_support_db"


def build_app_yaml(dataset_ids: list[str], pre_prompt: str) -> str:
    ds_block = ""
    for did in dataset_ids:
        ds_block += f"""
      - dataset:
          enabled: true
          id: {did}"""
    return f"""version: 0.6.0
kind: app
app:
  icon: "🛟"
  icon_background: '#E4FBCC'
  mode: agent-chat
  name: {APP_NAME}
  use_icon_as_answer_icon: false
model_config:
  agent_mode:
    enabled: true
    max_iteration: 5
    strategy: function_call
    tools: []
  dataset_configs:
    datasets:
      datasets:{ds_block if ds_block else " []"}
    retrieval_model: multiple
  file_upload:
    image:
      enabled: false
  model:
    completion_params:
      temperature: 0.3
      top_p: 0.9
    mode: chat
    name: qwen2.5:7b
    provider: langgenius/ollama/ollama
  opening_statement: |
    Здравствуйте! Я помогу с приложением Avaid.
    Опишите проблему: остатки, цены, заказы, настройка магазина, ошибка синхронизации, тариф.
  pre_prompt: |
{chr(10).join("    " + line for line in pre_prompt.splitlines())}
  suggested_questions:
    - Не обновляются остатки
    - Проблема с ценами
    - Заказ не подтверждается
    - Как подключить магазин
    - Ошибка синхронизации
  sensitive_word_avoidance:
    enabled: true
    type: moderation
    configs:
      - words: password
      - words: api_key
      - words: SELECT *
      - words: ignore instructions
"""


def main() -> int:
    email = os.environ.get("DIFY_EMAIL", "").strip()
    password = os.environ.get("DIFY_PASSWORD", "").strip()
    if not email or not password:
        print("Задайте DIFY_EMAIL и DIFY_PASSWORD в support-agent/.env", file=sys.stderr)
        print("Пример:", file=sys.stderr)
        print("  DIFY_EMAIL=itdanetolk@gmail.com", file=sys.stderr)
        print("  DIFY_PASSWORD=ваш_пароль_от_dify", file=sys.stderr)
        return 1

    client = DifyClient()
    print("==> Login Dify")
    client.login(email, password)

    print("==> Knowledge (3 датасета)")
    dataset_ids: list[str] = []
    for name, path, desc in DATASETS:
        print(f"--- {name}")
        if path.is_file():
            ds = client.find_dataset(name) or client.create_dataset(name, desc)
            did = ds["id"]
            existing = {d.get("name") for d in client.list_documents(did)}
            if path.name not in existing:
                fid = client.upload_file(path)
                client.add_documents(did, [fid])
                print(f"  indexed: {path.name}")
            else:
                print(f"  skip: {path.name}")
        else:
            did = client.sync_folder_to_dataset(name, path, desc)
        dataset_ids.append(did)
        print(f"  Studio: {client.base}/datasets/{did}")

    api_key = os.environ.get("SUPPORT_API_KEY", "change-me-local-dev-key")
    db_url = os.environ.get("DIFY_DB_API_URL", "http://host.docker.internal:8090")
    openapi_path = ROOT / "agents/support/dify/openapi-db-api.yaml"
    print("==> Tool provider (Custom API)")
    try:
        schema = openapi_path.read_text(encoding="utf-8")
        client.create_api_tool(TOOL_PROVIDER, schema, api_key, db_url)
        print(f"  Tool «{TOOL_PROVIDER}» создан/обновлён")
        print(f"  Studio: {client.base}/tools?category=api")
    except RuntimeError as e:
        if "already exists" in str(e).lower() or "409" in str(e):
            print(f"  Tool уже есть — настройте в Studio: Tools → API")
        else:
            print(f"  warning: {e}")

    pre_prompt = (ROOT / "agents/support/prompts/system.md").read_text(encoding="utf-8")
    yaml_content = build_app_yaml(dataset_ids, pre_prompt)

    apps = client.list_apps(APP_NAME)
    existing = next((a for a in apps if a.get("name") == APP_NAME), None)
    if existing:
        print(f"==> App «{APP_NAME}» уже есть: {client.base}/app/{existing['id']}/configuration")
        print("    Обновите промпт/KB/tools в Studio вручную или удалите app и перезапустите sync.")
    else:
        print("==> Import app «Avaid Support»")
        result = client.import_app_yaml(yaml_content, APP_NAME)
        status = result.get("status")
        if status == "pending":
            import_id = result.get("import_id") or result.get("id")
            if import_id:
                result = client.confirm_import(import_id)
        app_id = result.get("app_id")
        if app_id:
            print(f"  App: {client.base}/app/{app_id}/configuration")
            print(f"  Chat: {client.base}/app/{app_id}/overview")
        else:
            print(f"  import result: {result}")

    print()
    print("=== Где управлять в Dify ===")
    print(f"  Knowledge:  {client.base}/datasets")
    print(f"  Tools:      {client.base}/tools")
    print(f"  Apps:       {client.base}/apps")
    print()
    print("Дальше в Studio → Avaid Support:")
    print("  1. Agent → добавить tools из «avaid_support_db»")
    print("  2. Variables → user_email (для заголовка X-Dify-User-Email в tool)")
    print("  3. Publish → получить ссылку на чат")
    print()
    print("Подробно: docs/DIFY_CONTROL.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
