#!/usr/bin/env python3
"""
Диагностика Knowledge Base и привязки к приложению Avaid Support.
Запуск:
  docker cp scripts/dify-diagnose-kb-docker.py docker-api-1:/tmp/dify-diagnose-kb-docker.py
  docker exec docker-api-1 python -u /tmp/dify-diagnose-kb-docker.py
"""
from __future__ import annotations

import sys

sys.path.insert(0, "/app/api")

from app_factory import create_app
from extensions.ext_database import db
from models import App
from models.dataset import AppDatasetJoin, Dataset, Document
from sqlalchemy import select, func

TENANT_ID = "11aad9d2-e6a0-41fc-b8a1-5bf10ab4518f"
APP_NAME = "Avaid Support"


def main() -> int:
    _, flask_app = create_app()
    with flask_app.app_context():
        print("=" * 60)
        print("ДИАГНОСТИКА KNOWLEDGE BASE — Avaid Support")
        print("=" * 60)

        # --- Приложение ---
        app = db.session.scalar(
            select(App).where(App.name == APP_NAME, App.tenant_id == TENANT_ID).limit(1)
        )
        if not app:
            print(f"\n[ОШИБКА] Приложение '{APP_NAME}' не найдено!")
            print("  → Нужно создать приложение через Studio или запустить dify-complete-setup-docker.py")
            return 1
        print(f"\n[APP] {app.name}  id={app.id}  mode={app.mode}")
        cfg_id = app.app_model_config_id
        print(f"  app_model_config_id={cfg_id}")

        # --- Все датасеты тенанта ---
        datasets = db.session.scalars(
            select(Dataset).where(Dataset.tenant_id == TENANT_ID)
        ).all()
        print(f"\n[DATASETS] Всего датасетов в тенанте: {len(datasets)}")
        if not datasets:
            print("  [!] Датасетов нет — KB не создана.")
            print("  → Запустите: docker exec docker-api-1 python -u /tmp/dify-optimize-kb-docker.py")
        for ds in datasets:
            doc_count = db.session.scalar(
                select(func.count()).select_from(Document).where(Document.dataset_id == ds.id)
            )
            # проверяем привязку к приложению
            join = db.session.scalar(
                select(AppDatasetJoin).where(
                    AppDatasetJoin.dataset_id == ds.id,
                    AppDatasetJoin.app_id == app.id,
                )
            )
            linked = "✓ привязан к приложению" if join else "✗ НЕ привязан к приложению"
            print(f"\n  Dataset: {ds.name}")
            print(f"    id={ds.id}")
            print(f"    indexing={ds.indexing_technique}  embed={ds.embedding_model_provider}/{ds.embedding_model}")
            print(f"    documents={doc_count}")
            print(f"    retrieval={getattr(ds, 'retrieval_model_dict', {})}")
            print(f"    [{linked}]")

            # Показываем документы
            docs = db.session.scalars(
                select(Document).where(Document.dataset_id == ds.id).limit(20)
            ).all()
            for doc in docs:
                status = getattr(doc, "indexing_status", "?")
                tokens = getattr(doc, "tokens", "?")
                error = getattr(doc, "error", None)
                err_str = f"  ERROR: {error}" if error else ""
                print(f"      • {doc.name}  status={status}  tokens={tokens}{err_str}")

        # --- Привязки приложений к датасетам ---
        all_joins = db.session.scalars(
            select(AppDatasetJoin).where(AppDatasetJoin.app_id == app.id)
        ).all()
        print(f"\n[APP-DATASET JOINS] Привязано датасетов к приложению: {len(all_joins)}")
        if not all_joins:
            print("  [!] Приложение не подключено ни к одному датасету!")
            print("  → Запустите: docker exec docker-api-1 python -u /tmp/dify-complete-setup-docker.py")
            print("    или быстрый вариант:")
            print("    docker exec docker-api-1 python -u /tmp/dify-relink-kb-to-app-docker.py")
        for j in all_joins:
            ds = db.session.get(Dataset, j.dataset_id)
            ds_name = ds.name if ds else "???"
            print(f"  • dataset_id={j.dataset_id}  ({ds_name})")

        # --- app_model_config — проверяем dataset_configs ---
        from models import AppModelConfig
        cfg = db.session.get(AppModelConfig, cfg_id) if cfg_id else None
        if cfg:
            cfg_dict = cfg.to_dict()
            ds_cfg = cfg_dict.get("dataset_configs", {})
            retrieval_model = ds_cfg.get("retrieval_model", "?")
            top_k = ds_cfg.get("top_k", "?")
            score_enabled = ds_cfg.get("score_threshold_enabled", "?")
            score = ds_cfg.get("score_threshold", "?")
            datasets_in_cfg = ds_cfg.get("datasets", {}).get("datasets", [])
            print(f"\n[APP CONFIG] dataset_configs:")
            print(f"  retrieval_model={retrieval_model}  top_k={top_k}")
            print(f"  score_threshold_enabled={score_enabled}  score_threshold={score}")
            print(f"  датасетов в конфиге: {len(datasets_in_cfg)}")
            for d in datasets_in_cfg:
                did = d.get("dataset", {}).get("id", "?")
                enabled = d.get("dataset", {}).get("enabled", "?")
                ds_obj = db.session.get(Dataset, did)
                ds_name = ds_obj.name if ds_obj else "???"
                print(f"    • {did} ({ds_name})  enabled={enabled}")
            if not datasets_in_cfg:
                print("  [!] В конфиге приложения нет ни одного датасета!")
                print("  → Это главная причина, почему агент не читает KB.")
                print("  → Запустите: docker exec docker-api-1 python -u /tmp/dify-relink-kb-to-app-docker.py")
        else:
            print("\n[APP CONFIG] не найден — app_model_config_id пустой или записи нет")

        print("\n" + "=" * 60)
        print("ИТОГ:")
        has_datasets = len(datasets) > 0
        has_joins = len(all_joins) > 0
        has_cfg_datasets = cfg and len(cfg.to_dict().get("dataset_configs", {}).get("datasets", {}).get("datasets", [])) > 0

        if not has_datasets:
            print("  ✗ KB не создана → запустить dify-optimize-kb-docker.py")
        elif not has_joins:
            print("  ✗ KB не привязана к приложению → запустить dify-relink-kb-to-app-docker.py")
        elif not has_cfg_datasets:
            print("  ✗ В конфиге приложения пустой список датасетов → запустить dify-relink-kb-to-app-docker.py")
        else:
            print("  ✓ KB создана и привязана к приложению")
            # Проверяем индексацию
            bad_docs = []
            for ds in datasets:
                docs = db.session.scalars(
                    select(Document).where(Document.dataset_id == ds.id)
                ).all()
                for doc in docs:
                    status = getattr(doc, "indexing_status", "")
                    error = getattr(doc, "error", None)
                    if status != "completed" or error:
                        bad_docs.append((ds.name, doc.name, status, error))
            if bad_docs:
                print(f"  ! {len(bad_docs)} документов с проблемами индексации:")
                for ds_name, doc_name, status, error in bad_docs:
                    print(f"    [{ds_name}] {doc_name}: status={status}  error={error}")
                print("  → Проверьте, запущен ли ollama с nomic-embed-text: docker exec docker-ollama-1 ollama list")
            else:
                print("  ✓ Все документы проиндексированы")
                print("  → Если агент всё равно не отвечает по KB — запустите golden test:")
                print("     GOLDEN_ONLY=no-email-faq ./scripts/run-golden-tests.sh")
        print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
