#!/usr/bin/env python3
"""Create app API token for golden tests if missing."""
import sys

sys.path.insert(0, "/app/api")

from app_factory import create_app
from extensions.ext_database import db
from models.model import ApiToken, App
from sqlalchemy import func, select

APP_ID = "5005f9d9-2d02-4422-b7e2-bdf5a518414b"
TENANT_ID = "11aad9d2-e6a0-41fc-b8a1-5bf10ab4518f"


def main() -> int:
    _, flask_app = create_app()
    with flask_app.app_context():
        app = db.session.get(App, APP_ID)
        if not app:
            print("App not found", file=sys.stderr)
            return 1
        existing = db.session.scalar(
            select(ApiToken).where(ApiToken.app_id == APP_ID, ApiToken.type == "app").limit(1)
        )
        if existing:
            print(existing.token)
            return 0
        key = ApiToken.generate_api_key("app-", 24)
        tok = ApiToken()
        tok.app_id = APP_ID
        tok.tenant_id = TENANT_ID
        tok.token = key
        tok.type = "app"
        db.session.add(tok)
        db.session.commit()
        print(key)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
