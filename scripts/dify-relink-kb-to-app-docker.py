#!/usr/bin/env python3
"""
Быстрая привязка существующих датасетов к приложению Avaid Support.
Не трогает документы и индекс — только обновляет app_model_config.

Запуск:
  docker cp scripts/dify-relink-kb-to-app-docker.py docker-api-1:/tmp/dify-relink-kb-to-app-docker.py
  docker exec docker-api-1 python -u /tmp/dify-relink-kb-to-app-docker.py

Опционально, чтобы подключить только Avaid Rules:
  docker exec -e SUPPORT_DATASET_MODE=rules_only docker-api-1 python -u /tmp/dify-relink-kb-to-app-docker.py

Переменные:
  SUPPORT_DATASET_MODE   rules_only (default) | full
  SUPPORT_RETRIEVAL_TOP_K  8 (default)
  SUPPORT_LLM_MODEL        mistral-large-latest (default)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, "/app/api")

from app_factory import create_app
from events.app_event import app_model_config_was_updated
from extensions.ext_database import db
from models import Account, App, AppModelConfig
from models.dataset import AppDatasetJoin, Dataset
from models.model import AppMode
from services.app_model_config_service import AppModelConfigService
from sqlalchemy import select

TENANT_ID = "11aad9d2-e6a0-41fc-b8a1-5bf10ab4518f"
ACCOUNT_ID = "8416d7fe-259c-48ca-9a5c-be84f1a7e547"
APP_NAME = "Avaid Support"
SYSTEM_PROMPT_PATH = Path("/tmp/system.md")

SUPPORT_DATASET_MODE = os.environ.get("SUPPORT_DATASET_MODE", "rules_only").strip().lower()
SUPPORT_LLM_MODEL = os.environ.get("SUPPORT_LLM_MODEL", "mistral-large-latest")
TOP_K = int(os.environ.get("SUPPORT_RETRIEVAL_TOP_K", "8"))

# Имена датасетов которые ищем в Dify по режиму
DATASET_NAMES_BY_MODE: dict[str, list[str]] = {
    "rules_only": ["Avaid Rules"],
    "full": ["Avaid Rules", "Avaid Codebase", "Avaid Billing", "Avaid DB Schema"],
    "rules_and_codebase": ["Avaid Rules", "Avaid Codebase"],
    "codebase_only": ["Avaid Codebase", "Avaid Billing"],
}


def load_system_prompt() -> str:
    if SYSTEM_PROMPT_PATH.is_file():
        return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    # fallback минимальный промпт если файл не скопирован
    return (
        "Ты — агент технической поддержки Avaid. Отвечай только на русском.\n"
        "Используй только информацию из базы знаний. Не выдумывай факты.\n"
        "Email пользователя: {{user_email}}. Если email пустой — отвечай только по KB."
    )


def get_dataset_ids(names: list[str]) -> list[str]:
    ids = []
    for name in names:
        ds = db.session.scalar(
            select(Dataset).where(Dataset.name == name, Dataset.tenant_id == TENANT_ID).limit(1)
        )
        if ds:
            ids.append(ds.id)
            print(f"  ✓ нашли датасет: {name}  ({ds.id})")
        else:
            print(f"  ✗ датасет не найден: {name}  (пропускаем)")
    return ids


def main() -> int:
    names = DATASET_NAMES_BY_MODE.get(SUPPORT_DATASET_MODE, ["Avaid Rules"])
    print(f"Режим: {SUPPORT_DATASET_MODE}  →  датасеты: {names}")

    _, flask_app = create_app()
    with flask_app.app_context():
        account = db.session.get(Account, ACCOUNT_ID)
        if not account:
            print("Аккаунт не найден", file=sys.stderr)
            return 1
        account.set_tenant_id(TENANT_ID)

        app = db.session.scalar(
            select(App).where(App.name == APP_NAME, App.tenant_id == TENANT_ID).limit(1)
        )
        if not app:
            print(f"Приложение '{APP_NAME}' не найдено", file=sys.stderr)
            return 1
        print(f"Приложение: {app.name}  ({app.id})  mode={app.mode}")

        # Находим датасеты
        dataset_ids = get_dataset_ids(names)
        if not dataset_ids:
            print("\n[ОШИБКА] Не найдено ни одного датасета!", file=sys.stderr)
            print("Сначала создайте KB:")
            print("  docker exec docker-api-1 python -u /tmp/dify-optimize-kb-docker.py")
            return 1

        # Обновляем AppDatasetJoin (физическая привязка)
        existing_joins = {
            j.dataset_id
            for j in db.session.scalars(
                select(AppDatasetJoin).where(AppDatasetJoin.app_id == app.id)
            ).all()
        }
        for did in dataset_ids:
            if did not in existing_joins:
                join = AppDatasetJoin(app_id=app.id, dataset_id=did)
                db.session.add(join)
                print(f"  + добавляем AppDatasetJoin: {did}")
            else:
                print(f"  = AppDatasetJoin уже есть: {did}")

        # Получаем текущий конфиг
        old_cfg = db.session.get(AppModelConfig, app.app_model_config_id)
        if not old_cfg:
            print("app_model_config не найден", file=sys.stderr)
            return 1

        config = old_cfg.to_dict()

        # Обновляем промпт
        config["pre_prompt"] = load_system_prompt()

        # Обновляем модель
        # Провайдер: Mistral AI (работает с РФ-серверов без VPN)
        config["model"] = {
            "provider": "mistralai",
            "name": SUPPORT_LLM_MODEL,
            "mode": "chat",
            "completion_params": {
                "temperature": 0.1,
                "top_p": 0.9,
                "max_tokens": 1024,
            },
        }

        # Обновляем dataset_configs — главное место где агент ищет KB
        config["dataset_configs"] = {
            "retrieval_model": "multiple",
            "top_k": TOP_K,
            "score_threshold_enabled": False,   # без порога — не отсекаем хорошие chunks
            "score_threshold": 0.0,
            "datasets": {
                "datasets": [
                    {"dataset": {"id": did, "enabled": True}} for did in dataset_ids
                ]
            },
        }
        config["retriever_resource"] = {"enabled": True}

        # Форма ввода email
        config["user_input_form"] = [
            {
                "text-input": {
                    "label": "Email",
                    "variable": "user_email",
                    "required": False,
                    "max_length": 255,
                    "default": "",
                }
            }
        ]

        # Режим: chat (без agent tools) — qwen/ollama часто не выполняет function_call
        agent_mode = config.get("agent_mode") or {}
        agent_mode["enabled"] = False
        agent_mode["tools"] = []
        config["agent_mode"] = agent_mode
        app_mode = AppMode.CHAT

        # Валидируем и сохраняем
        validated = AppModelConfigService.validate_configuration(TENANT_ID, config, app_mode)

        new_cfg = AppModelConfig(
            app_id=app.id,
            created_by=account.id,
            updated_by=account.id,
        )
        new_cfg.from_model_config_dict(validated)
        new_cfg.id = str(uuid4())
        db.session.add(new_cfg)
        app.app_model_config_id = new_cfg.id
        app.mode = app_mode
        app.updated_by = account.id
        db.session.flush()
        app_model_config_was_updated.send(app, app_model_config=new_cfg)
        db.session.commit()

        print(f"\n✓ Готово:")
        print(f"  mode={app_mode.value}")
        print(f"  datasets={len(dataset_ids)}  top_k={TOP_K}  score_threshold=off")
        print(f"  model={SUPPORT_LLM_MODEL}")
        print(f"  prompt={'system.md' if SYSTEM_PROMPT_PATH.is_file() else 'fallback'}")
        print("\nПерезагрузите Studio (F5) и откройте новый чат.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
