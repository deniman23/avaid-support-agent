#!/usr/bin/env python3
"""Upload new markdown file(s) into existing Avaid Rules dataset."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, "/app/api")

from app_factory import create_app
from extensions.ext_database import db
from models import Account
from models.dataset import Dataset
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

TENANT_ID = "11aad9d2-e6a0-41fc-b8a1-5bf10ab4518f"
ACCOUNT_ID = "8416d7fe-259c-48ca-9a5c-be84f1a7e547"
DATASET_NAME = "Avaid Rules"


def main() -> int:
    paths = [Path(p) for p in sys.argv[1:]]
    if not paths:
        print("Usage: dify-add-rules-doc-docker.py /path/to/file.md ...", file=sys.stderr)
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
            print(f"Dataset {DATASET_NAME} not found", file=sys.stderr)
            return 1

        fs = FileService(db.engine)
        file_ids: list[str] = []
        for p in paths:
            uf = fs.upload_file(
                filename=p.name,
                content=p.read_bytes(),
                mimetype="text/markdown",
                user=account,
                source="datasets",
            )
            file_ids.append(uf.id)
            print(f"uploaded {p.name} -> {uf.id}")

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
        print(f"indexed into {DATASET_NAME} ({dataset.id})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
