#!/usr/bin/env python3
"""Оптимизация Avaid Rules: high_quality + hybrid + chunk 800 + переиндекс."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, "/app/api")

from app_factory import create_app
from core.rag.entities import ParentMode, Rule
from core.rag.index_processor.constant.index_type import IndexStructureType
from core.rag.retrieval.retrieval_methods import RetrievalMethod
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
    RetrievalModel,
)
from services.file_service import FileService
from services.model_provider_service import ModelProviderService
from sqlalchemy import select

TENANT_ID = "11aad9d2-e6a0-41fc-b8a1-5bf10ab4518f"
ACCOUNT_ID = "8416d7fe-259c-48ca-9a5c-be84f1a7e547"
DATASET_NAME = "Avaid Rules"
KB_INDEX = Path("/tmp/support-agent-kb/dify-kb")
PROVIDER = "langgenius/ollama/ollama"
EMBED_MODEL = os.environ.get("SUPPORT_EMBED_MODEL", "nomic-embed-text")
CHUNK_SIZE = int(os.environ.get("SUPPORT_CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.environ.get("SUPPORT_CHUNK_OVERLAP", "80"))


def process_rule_custom() -> ProcessRule:
    return ProcessRule(
        mode="custom",
        rules=Rule(
            pre_processing_rules=[
                {"id": "remove_extra_spaces", "enabled": True},
                {"id": "remove_urls_emails", "enabled": False},
            ],
            segmentation={
                "separator": "\n## ",
                "max_tokens": CHUNK_SIZE,
                "chunk_overlap": CHUNK_OVERLAP,
            },
            parent_mode=ParentMode.FULL_DOC,
        ),
    )


def retrieval_model_hybrid() -> RetrievalModel:
    return RetrievalModel(
        search_method=RetrievalMethod.HYBRID_SEARCH,
        reranking_enable=False,
        top_k=5,
        score_threshold_enabled=False,
        score_threshold=0.0,
    )


def upload_batch(account: Account, dataset: Dataset, paths: list[Path]) -> None:
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
        print(f"    upload {p.name}")
    kc = KnowledgeConfig(
        indexing_technique="high_quality",
        embedding_model_provider=PROVIDER,
        embedding_model=EMBED_MODEL,
        data_source=DataSource(
            info_list=InfoList(
                data_source_type="upload_file",
                file_info_list=FileInfo(file_ids=file_ids),
            )
        ),
        process_rule=process_rule_custom(),
        doc_form=IndexStructureType.PARAGRAPH_INDEX,
        doc_language="Russian",
    )
    with patch("services.dataset_service.current_user", account):
        DocumentService.save_document_with_dataset_id(dataset, kc, account)


def main() -> int:
    paths = sorted(KB_INDEX.glob("*.md")) if KB_INDEX.is_dir() else []
    if not paths:
        print(f"No md in {KB_INDEX}", file=sys.stderr)
        return 1

    _, flask_app = create_app()
    with flask_app.app_context():
        account = db.session.get(Account, ACCOUNT_ID)
        if not account:
            return 1
        account.set_tenant_id(TENANT_ID)

        print("==> Register embedding default")
        mps = ModelProviderService()
        try:
            mps.update_default_model_of_model_type(TENANT_ID, "text-embedding", PROVIDER, EMBED_MODEL)
        except Exception as e:
            print(f"  warn default embedding: {e}")

        dataset = db.session.scalar(
            select(Dataset).where(Dataset.name == DATASET_NAME, Dataset.tenant_id == TENANT_ID).limit(1)
        )
        if not dataset:
            print(f"Dataset {DATASET_NAME} missing", file=sys.stderr)
            return 1

        print(f"==> Update dataset {DATASET_NAME} -> high_quality + hybrid")
        with patch("services.dataset_service.current_user", account):
            DatasetService.update_dataset(
                dataset.id,
                {
                    "indexing_technique": "high_quality",
                    "embedding_model_provider": PROVIDER,
                    "embedding_model": EMBED_MODEL,
                    "retrieval_model": retrieval_model_hybrid().model_dump(),
                },
                account,
            )

        db.session.refresh(dataset)
        print(
            f"  indexing={dataset.indexing_technique} "
            f"embed={dataset.embedding_model_provider}/{dataset.embedding_model}"
        )

        docs = db.session.scalars(select(Document).where(Document.dataset_id == dataset.id)).all()
        print(f"==> Delete {len(docs)} documents, reindex {len(paths)} with chunk={CHUNK_SIZE}")
        for doc in docs:
            DocumentService.delete_document(doc)

        for i in range(0, len(paths), 5):
            upload_batch(account, dataset, paths[i : i + 5])

        print(f"==> Done {DATASET_NAME} ({dataset.id})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
