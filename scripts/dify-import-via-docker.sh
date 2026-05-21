#!/usr/bin/env bash
# Импорт «Avaid Support» в Dify без пароля (через docker-api-1)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DSL="$ROOT/agents/support/dify/avaid-support-import.dsl.yml"

sg docker -c "docker cp '$DSL' docker-api-1:/tmp/avaid-support.dsl.yml"

sg docker -c 'docker exec docker-api-1 python -u -c "
import sys
sys.path.insert(0, \"/app/api\")
from app_factory import create_app
from extensions.ext_database import db
from models import Account
from services.app_dsl_service import AppDslService, ImportStatus
from sqlalchemy.orm import Session
from sqlalchemy import select
from models import App

account_id = \"8416d7fe-259c-48ca-9a5c-be84f1a7e547\"
tenant_id = \"11aad9d2-e6a0-41fc-b8a1-5bf10ab4518f\"
yaml_content = open(\"/tmp/avaid-support.dsl.yml\").read()
_, flask_app = create_app()
with flask_app.app_context():
    existing = db.session.scalar(select(App).where(App.name == \"Avaid Support\"))
    if existing:
        print(\"App already exists:\", existing.id)
        sys.exit(0)
    account = db.session.get(Account, account_id)
    account.set_tenant_id(tenant_id)
    with Session(db.engine, expire_on_commit=False) as session:
        svc = AppDslService(session)
        result = svc.import_app(account=account, import_mode=\"yaml-content\", yaml_content=yaml_content, name=\"Avaid Support\")
        if result.status == ImportStatus.PENDING:
            result = svc.confirm_import(account=account, import_id=result.import_id)
        if result.status == ImportStatus.FAILED:
            print(result); session.rollback(); sys.exit(2)
        session.commit()
        print(\"Created app:\", result.app_id)
"'

echo "Откройте http://localhost/apps — должно быть приложение «Avaid Support»"
