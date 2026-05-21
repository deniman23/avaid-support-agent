#!/usr/bin/env python3
"""Переиндекс одного .md в Avaid Rules (после правки KB)."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, "/app/api")

from app_factory import create_app
from core.rag.entities import ParentMode, Rule
from core.rag.index_processor.constant.index_type import IndexStructureType
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

TENANT_ID = "11aad9d2-e6a0-41fc-b8a1-5bf10ab4518f"
ACCOUNT_ID = "8416d7fe-259c-48ca-9a5c-be84f1a7e547"
DATASET_NAME = "Avaid Rules"
PROVIDER = "langgenius/ollama/ollama"
EMBED_MODEL = "nomic-embed-text"
KB = Path("/tmp/support-agent-kb/dify-kb")


def process_rule() -> ProcessRule:
    return ProcessRule(
        mode="custom",
        rules=Rule(
            pre_processing_rules=[
                {"id": "remove_extra_spaces", "enabled": True},
                {"id": "remove_urls_emails", "enabled": False},
            ],
            segmentation={"separator": "\n## ", "max_tokens": 800, "chunk_overlap": 80},
            parent_mode=ParentMode.FULL_DOC,
        ),
    )


def main() -> int:
    name = sys.argv[1] if len(sys.argv) > 1 else "tarify-i-billing.md"
    path = KB / name
    if not path.is_file():
        print(f"missing {path}", file=sys.stderr)
        return 1

    _, flask_app = create_app()
    with flask_app.app_context():
        account = db.session.get(Account, ACCOUNT_ID)
        dataset = db.session.scalar(
            select(Dataset).where(Dataset.name == DATASET_NAME, Dataset.tenant_id == TENANT_ID).limit(1)
        )
        if not account or not dataset:
            return 1
        account.set_tenant_id(TENANT_ID)

        old = db.session.scalar(
            select(Document).where(Document.dataset_id == dataset.id, Document.name == name).limit(1)
        )
        if old:
            DocumentService.delete_document(old)
            print(f"deleted old {name}")

        fs = FileService(db.engine)
        uf = fs.upload_file(
            filename=path.name,
            content=path.read_bytes(),
            mimetype="text/markdown",
            user=account,
            source="datasets",
        )
        kc = KnowledgeConfig(
            indexing_technique="high_quality",
            embedding_model_provider=PROVIDER,
            embedding_model=EMBED_MODEL,
            data_source=DataSource(
                info_list=InfoList(
                    data_source_type="upload_file",
                    file_info_list=FileInfo(file_ids=[uf.id]),
                )
            ),
            process_rule=process_rule(),
            doc_form=IndexStructureType.PARAGRAPH_INDEX,
            doc_language="Russian",
        )
        with patch("services.dataset_service.current_user", account):
            DocumentService.save_document_with_dataset_id(dataset, kc, account)
        print(f"reindexed {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
