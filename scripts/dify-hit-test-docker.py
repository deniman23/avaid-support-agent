#!/usr/bin/env python3
"""Hit testing для датасета Avaid Rules."""
from __future__ import annotations

import sys

sys.path.insert(0, "/app/api")

from app_factory import create_app
from extensions.ext_database import db
from models import Account
from models.dataset import Dataset
from services.hit_testing_service import HitTestingService
from sqlalchemy import select

TENANT_ID = "11aad9d2-e6a0-41fc-b8a1-5bf10ab4518f"
ACCOUNT_ID = "8416d7fe-259c-48ca-9a5c-be84f1a7e547"
DATASET_NAME = "Avaid Rules"


def main() -> int:
    queries = sys.argv[1:] or [
        "Какие виды тарифов есть в Avaid?",
        "тарифы Avaid",
        "почему мои цены на WB не обновляются",
    ]
    _, flask_app = create_app()
    with flask_app.app_context():
        dataset = db.session.scalar(
            select(Dataset).where(Dataset.name == DATASET_NAME, Dataset.tenant_id == TENANT_ID).limit(1)
        )
        account = db.session.get(Account, ACCOUNT_ID)
        if not dataset or not account:
            print("dataset or account missing", file=sys.stderr)
            return 1
        account.set_tenant_id(TENANT_ID)
        for q in queries:
            print(f"\nQ: {q}")
            resp = HitTestingService.retrieve(dataset, q, account, None, {}, limit=5)
            for rec in resp.get("records", [])[:5]:
                seg = rec.get("segment") or {}
                doc = rec.get("document") or {}
                print(f"  {rec.get('score', 0):.4f} {doc.get('name', '?')} | {(seg.get('content') or '')[:100]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
