#!/usr/bin/env python3
"""Переиндексация датасета: удалить документы, загрузить файлы из KB_SUBDIR (*.md, *.go)."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, "/app/api")

from app_factory import create_app
from extensions.ext_database import db
from models import Account
from models.dataset import Dataset, Document
from services.dataset_service import DatasetService, DocumentService
from services.entities.knowledge_entities.knowledge_entities import (
    DataSource,
    FileInfo,
    InfoList,
    KnowledgeConfig,
    ProcessRule,
)
from services.file_service import FileService
from sqlalchemy import select

import os

TENANT_ID = "11aad9d2-e6a0-41fc-b8a1-5bf10ab4518f"
ACCOUNT_ID = "8416d7fe-259c-48ca-9a5c-be84f1a7e547"
DATASET_NAME = os.environ.get("DIFY_DATASET_NAME", "Avaid Rules")
KB_SUBDIR = os.environ.get("DIFY_KB_SUBDIR", "index")
KB_INDEX = Path("/tmp/support-agent-kb") / KB_SUBDIR
KB_EXTENSIONS = tuple(
    x.strip().lstrip(".")
    for x in os.environ.get("DIFY_KB_EXTENSIONS", "md").split(",")
    if x.strip()
)


def upload_batch(account: Account, dataset: Dataset, paths: list[Path]) -> None:
    fs = FileService(db.engine)
    file_ids: list[str] = []
    for p in paths:
        if p.suffix in {".go", ".txt"}:
            mime = "text/plain"
        else:
            mime = "text/markdown"
        uf = fs.upload_file(
            filename=p.name,
            content=p.read_bytes(),
            mimetype=mime,
            user=account,
            source="datasets",
        )
        file_ids.append(uf.id)
        print(f"    upload {p.relative_to(KB_INDEX)}")
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


def collect_paths() -> list[Path]:
    if not KB_INDEX.is_dir():
        return []
    out: list[Path] = []
    for ext in KB_EXTENSIONS:
        out.extend(KB_INDEX.rglob(f"*.{ext}"))
    return sorted(set(out))


def main() -> int:
    paths = collect_paths()
    if not paths:
        print(f"No files (*.{','.join(KB_EXTENSIONS)}) in {KB_INDEX}", file=sys.stderr)
        return 1

    _, flask_app = create_app()
    with flask_app.app_context():
        account = db.session.get(Account, ACCOUNT_ID)
        if not account:
            return 1
        account.set_tenant_id(TENANT_ID)

        dataset = db.session.scalar(
            select(Dataset).where(Dataset.name == DATASET_NAME, Dataset.tenant_id == TENANT_ID).limit(1)
        )
        if not dataset:
            from services.dataset_service import DatasetService

            print(f"  create dataset {DATASET_NAME}")
            dataset = DatasetService.create_empty_dataset(
                tenant_id=TENANT_ID,
                name=DATASET_NAME,
                description=f"Auto-created for reindex ({DATASET_NAME})",
                indexing_technique="economy",
                account=account,
            )

        docs = db.session.scalars(select(Document).where(Document.dataset_id == dataset.id)).all()
        print(f"==> Delete {len(docs)} old documents from {DATASET_NAME}")
        for doc in docs:
            DocumentService.delete_document(doc)

        print(f"==> Index {len(paths)} files")
        for i in range(0, len(paths), 5):
            upload_batch(account, dataset, paths[i : i + 5])

        print(f"==> Done: {DATASET_NAME} ({dataset.id})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
