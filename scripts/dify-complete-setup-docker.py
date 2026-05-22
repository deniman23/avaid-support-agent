#!/usr/bin/env python3
"""Full Dify setup inside docker-api-1: Knowledge + Tools + App linkage."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

sys.path.insert(0, "/app/api")

from app_factory import create_app
from events.app_event import app_model_config_was_updated
from extensions.ext_database import db
from models import Account, App, AppModelConfig
from models.dataset import AppDatasetJoin, Dataset
from services.dataset_service import DatasetService, DocumentService
from services.entities.knowledge_entities.knowledge_entities import (
    DataSource,
    FileInfo,
    InfoList,
    KnowledgeConfig,
    ProcessRule,
)
from services.file_service import FileService
from services.app_model_config_service import AppModelConfigService
from services.tools.api_tools_manage_service import ApiToolManageService
from core.tools.entities.tool_entities import ApiProviderSchemaType
from models.model import AppMode
from sqlalchemy import select

ACCOUNT_ID = "8416d7fe-259c-48ca-9a5c-be84f1a7e547"
TENANT_ID = "11aad9d2-e6a0-41fc-b8a1-5bf10ab4518f"
APP_NAME = "Avaid Support"
TOOL_PROVIDER = "avaid_support_db"
KB_ROOT = Path("/tmp/support-agent-kb")

DATASETS = [
    ("Avaid Rules", KB_ROOT / "index", "Сценарии и справочники Avaid (KB)"),
    ("Avaid Codebase", KB_ROOT / "codebase-raw", "Go-исходники backend-go (RAG)"),
    ("Avaid Billing", KB_ROOT / "codebase-billing", "Тарифы и billing (Go, узкий индекс)"),
    ("Avaid DB Schema", KB_ROOT / "schema", "Глоссарий БД"),
]
BILLING_DATASET_NAME = "Avaid Billing"
# rules_only (default, dify-kb) | codebase_only | rules_and_codebase | full
SUPPORT_DATASET_MODE = os.environ.get("SUPPORT_DATASET_MODE", "rules_only").strip().lower()
RULES_DATASET_NAME = "Avaid Rules"
CODEBASE_DATASET_NAME = "Avaid Codebase"

# Без email — факты из БД/кода
API_TOOLS_PUBLIC = ["supportTariffsCatalog"]

API_TOOLS_ACCOUNT = [
    "supportShops",
    "supportStockCheck",
    "supportStockIssues",
    "supportPricesCheck",
    "supportProductsUnlinked",
    "supportOrdersRecent",
    "supportSyncLastError",
    "supportBillingStatus",
    "supportShopSettingsUpdate",
    "supportProductSyncUpdate",
    "supportProductLinkMs",
]

API_TOOLS = API_TOOLS_PUBLIC + API_TOOLS_ACCOUNT

OPENAPI_PATH = Path("/tmp/openapi-db-api.yaml")
SYSTEM_PROMPT_PATH = Path("/tmp/system.md")
SUPPORT_API_KEY = "change-me-local-dev-key"
DB_API_URL = "http://support-db-api:8090"
# Mistral AI API — работает с РФ-серверов без VPN
SUPPORT_LLM_MODEL = os.environ.get("SUPPORT_LLM_MODEL", "mistral-large-latest")
# 1 = все tools (нужен email); 0 = только public tools (тарифы) + agent
SUPPORT_ENABLE_ACCOUNT_TOOLS = os.environ.get("SUPPORT_ENABLE_ACCOUNT_TOOLS", "0") == "1"


def active_tool_names() -> list[str]:
    if SUPPORT_ENABLE_ACCOUNT_TOOLS:
        return API_TOOLS
    return API_TOOLS_PUBLIC


def load_pre_prompt() -> str:
    if SYSTEM_PROMPT_PATH.is_file():
        return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    return (
        "Ты — агент поддержки Avaid. Отвечай ТОЛЬКО на русском. "
        "Email: {{user_email}}. В каждый tool передавай user_email={{user_email}}."
    )


def dataset_names_for_mode() -> list[str]:
    if SUPPORT_DATASET_MODE == "full":
        return [name for name, _, _ in DATASETS]
    if SUPPORT_DATASET_MODE == "rules_only":
        return [RULES_DATASET_NAME]
    if SUPPORT_DATASET_MODE == "rules_and_codebase":
        return [RULES_DATASET_NAME, CODEBASE_DATASET_NAME]
    return [CODEBASE_DATASET_NAME, BILLING_DATASET_NAME]


def selected_datasets() -> list[tuple[str, Path, str]]:
    names = set(dataset_names_for_mode())
    return [entry for entry in DATASETS if entry[0] in names]


def resolve_dataset_ids(account: Account) -> list[str]:
    """ID датасетов по режиму (создать датасет, если ещё нет)."""
    ids: list[str] = []
    with patch("services.dataset_service.current_user", account):
        for name, folder, desc in selected_datasets():
            existing = db.session.scalar(
                select(Dataset).where(Dataset.name == name, Dataset.tenant_id == TENANT_ID).limit(1)
            )
            if existing:
                ids.append(existing.id)
                print(f"  dataset: {name} ({existing.id})")
            else:
                ids.append(ensure_dataset(account, name, folder, desc))
    return ids


def upload_files(account: Account, paths: list[Path]) -> list[str]:
    fs = FileService(db.engine)
    ids: list[str] = []
    for p in paths:
        content = p.read_bytes()
        uf = fs.upload_file(
            filename=p.name,
            content=content,
            mimetype="text/markdown",
            user=account,
            source="datasets",
        )
        ids.append(uf.id)
        print(f"    uploaded {p.name} -> {uf.id}")
    return ids


def ensure_dataset(account: Account, name: str, folder: Path, description: str) -> str:
    existing = db.session.scalar(
        select(Dataset).where(Dataset.name == name, Dataset.tenant_id == TENANT_ID).limit(1)
    )
    if existing:
        print(f"  dataset exists: {name} ({existing.id})")
        return existing.id

    dataset = DatasetService.create_empty_dataset(
        tenant_id=TENANT_ID,
        name=name,
        description=description,
        indexing_technique="economy",
        account=account,
    )
    print(f"  created dataset: {name} ({dataset.id})")

    paths = sorted(folder.rglob("*.md")) if folder.is_dir() else []
    if not paths:
        print(f"  warning: no md in {folder}")
        return dataset.id

    # batch upload in chunks of 5
    for i in range(0, len(paths), 5):
        chunk = paths[i : i + 5]
        file_ids = upload_files(account, chunk)
        kc = KnowledgeConfig(
            indexing_technique="economy",
            data_source=DataSource(
                info_list=InfoList(
                    data_source_type="upload_file",
                    file_info_list=FileInfo(file_ids=file_ids),
                )
            ),
            process_rule=ProcessRule(mode="automatic"),
            doc_form="text_model",
            doc_language="Russian",
        )
        with patch("services.dataset_service.current_user", account):
            DocumentService.save_document_with_dataset_id(dataset, kc, account)
    return dataset.id


def ensure_api_tool(flask_app, user_id: str) -> list[dict]:
    schema = OPENAPI_PATH.read_text(encoding="utf-8")
    creds = {
        "auth_type": "api_key",
        "api_key_header": "X-Support-Api-Key",
        "api_key_value": SUPPORT_API_KEY,
    }
    icon = {"content": "🛟", "background": "#E4FBCC"}
    try:
        with flask_app.test_request_context("/console/api/setup"):
            ApiToolManageService.create_api_tool_provider(
                user_id,
                TENANT_ID,
                TOOL_PROVIDER,
                icon,
                creds,
                ApiProviderSchemaType.OPENAPI,
                schema,
                "",
                "Avaid support db-api",
                ["support", "avaid"],
            )
        print(f"  created API tool provider: {TOOL_PROVIDER}")
    except ValueError as e:
        if "already exists" in str(e):
            print(f"  updating API tool provider: {TOOL_PROVIDER}")
            with flask_app.test_request_context("/console/api/setup"):
                ApiToolManageService.update_api_tool_provider(
                    user_id,
                    TENANT_ID,
                    TOOL_PROVIDER,
                    TOOL_PROVIDER,
                    icon,
                    creds,
                    ApiProviderSchemaType.OPENAPI,
                    schema,
                    "",
                    "Avaid support db-api",
                    ["support", "avaid"],
                )
        else:
            raise

    from models.tools import ApiToolProvider  # noqa: WPS433

    provider = db.session.scalar(
        select(ApiToolProvider).where(
            ApiToolProvider.tenant_id == TENANT_ID, ApiToolProvider.name == TOOL_PROVIDER
        )
    )
    if not provider:
        raise RuntimeError(f"API provider {TOOL_PROVIDER} not found")
    provider_uuid = provider.id

    with flask_app.test_request_context("/console/api/setup"):
        tools_meta = ApiToolManageService.list_api_tool_provider_tools(
            user_id, TENANT_ID, TOOL_PROVIDER
        )
    agent_tools = []
    for tname in active_tool_names():
        meta = next((t for t in tools_meta if t.name == tname), None)
        label = meta.label.en_US if meta and hasattr(meta.label, "en_US") else tname
        agent_tools.append(
            {
                "enabled": True,
                "isDeleted": False,
                "notAuthor": False,
                "provider_id": provider_uuid,
                "provider_name": TOOL_PROVIDER,
                "provider_type": "api",
                "tool_label": label,
                "tool_name": tname,
                "tool_parameters": {
                    "user_email": {"type": "variable", "value": ["user_email"]},
                },
            }
        )
    return agent_tools


def link_app(account: Account, dataset_ids: list[str], api_agent_tools: list[dict]) -> None:
    app = db.session.scalar(select(App).where(App.name == APP_NAME, App.tenant_id == TENANT_ID).limit(1))
    if not app:
        raise RuntimeError(f"App {APP_NAME} not found")

    old_cfg = db.session.get(AppModelConfig, app.app_model_config_id)
    if not old_cfg:
        raise RuntimeError("App model config missing")

    config = old_cfg.to_dict()
    config["pre_prompt"] = load_pre_prompt()
    config["opening_statement"] = (
        "Здравствуйте! Я помогу с приложением Avaid.\n"
        "Для общих вопросов (функции, маркетплейсы, типы торговли) email не обязателен.\n"
        "Для проверки данных вашего аккаунта укажите email в поле выше."
    )
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
    config["dataset_configs"] = {
        "retrieval_model": "multiple",
        "top_k": int(os.environ.get("SUPPORT_RETRIEVAL_TOP_K", "8")),
        "score_threshold_enabled": os.environ.get("SUPPORT_SCORE_THRESHOLD_ENABLED", "0") == "1",
        "score_threshold": float(os.environ.get("SUPPORT_SCORE_THRESHOLD", "0.4")),
        "datasets": {
            "datasets": [
                {"dataset": {"id": did, "enabled": True}} for did in dataset_ids
            ]
        },
    }
    config["retriever_resource"] = {"enabled": True}
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
    agent_mode = config.get("agent_mode") or {}
    if SUPPORT_ENABLE_ACCOUNT_TOOLS:
        app_mode = AppMode.AGENT_CHAT
        agent_mode["enabled"] = True
        agent_mode["strategy"] = "function_call"
        agent_mode["max_iteration"] = 3
        agent_mode["tools"] = api_agent_tools
    else:
        # Qwen/Ollama часто не выполняет tools (пишет _icall_ текстом) — chat + RAG по коду
        app_mode = AppMode.CHAT
        agent_mode["enabled"] = False
        agent_mode["tools"] = []
    config["agent_mode"] = agent_mode

    validated = AppModelConfigService.validate_configuration(
        TENANT_ID, config, app_mode
    )

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
    tools_n = len(api_agent_tools)
    print(
        f"  linked app {app.id}: mode={app_mode.value}, datasets={len(dataset_ids)}, "
        f"api_tools={tools_n}, model={SUPPORT_LLM_MODEL}"
    )


def main() -> int:
    import os

    prompt_only = os.environ.get("DIFY_SETUP_PROMPT_ONLY") == "1"
    _, flask_app = create_app()
    with flask_app.app_context():
        account = db.session.get(Account, ACCOUNT_ID)
        if not account:
            print("Account not found", file=sys.stderr)
            return 1
        account.set_tenant_id(TENANT_ID)

        dataset_ids: list[str] = []
        app_id = db.session.scalar(select(App.id).where(App.name == APP_NAME, App.tenant_id == TENANT_ID))
        if not app_id:
            print(f"App {APP_NAME} not found", file=sys.stderr)
            return 1

        print(f"==> Knowledge datasets (mode={SUPPORT_DATASET_MODE})")
        if not prompt_only:
            if (KB_ROOT / "schema.md").is_file():
                schema_folder = next(
                    (p for n, p, _ in DATASETS if n == "Avaid DB Schema"), None
                )
                if schema_folder:
                    schema_folder.mkdir(parents=True, exist_ok=True)
                    dest = schema_folder / "db-schema-for-agent.md"
                    if not dest.exists():
                        dest.write_text((KB_ROOT / "schema.md").read_text(encoding="utf-8"))
        dataset_ids = resolve_dataset_ids(account)
        if prompt_only:
            print("==> Prompt/tools only (relink datasets to app config)")

        print("==> API tools")
        api_tools = ensure_api_tool(flask_app, account.id)

        print("==> Link to Avaid Support app")
        link_app(account, dataset_ids, api_tools)

        from sqlalchemy import func

        print("==> Done")
        n_ds = db.session.scalar(
            select(func.count()).select_from(Dataset).where(Dataset.tenant_id == TENANT_ID)
        )
        n_join = db.session.scalar(select(func.count()).select_from(AppDatasetJoin))
        print(f"  datasets: {n_ds}, app_dataset_joins: {n_join}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
