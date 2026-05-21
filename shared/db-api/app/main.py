import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import settings
from app.routes import support, writes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("support-db-api")

AUDIT_PATH = Path("/var/log/support-db-api/audit.log")
AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Avaid Support DB API",
    version="1.1.0",
    docs_url="/docs",
    redoc_url=None,
    description="Support facts + allowlisted writes (shops rubilniki, product sync/link).",
)
app.include_router(support.router)
app.include_router(writes.router)


@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/support"):
        user = getattr(request.state, "user", None)
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "path": request.url.path,
            "method": request.method,
            "status": response.status_code,
            "user_id": user.get("id") if user else None,
            "email": getattr(request.state, "log_email", None),
            "query": dict(request.query_params),
        }
        try:
            with AUDIT_PATH.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError:
            logger.info("audit %s", entry)
    return response


@app.get("/health")
def health():
    from app.db import fetch_one

    db_ok = False
    try:
        fetch_one("SELECT 1 AS ok")
        db_ok = True
    except Exception:
        logger.exception("health db check failed")
    return {
        "status": "ok" if db_ok else "degraded",
        "database": "up" if db_ok else "down",
        "mode": settings.db_api_mode,
        "writes_enabled": settings.writes_enabled,
    }


@app.exception_handler(Exception)
def unhandled(_: Request, exc: Exception):
    logger.exception("unhandled")
    return JSONResponse(status_code=500, content={"detail": "Internal error"})
