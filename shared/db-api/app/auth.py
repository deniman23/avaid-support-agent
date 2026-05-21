import time
from collections import defaultdict
from typing import Annotated

from fastapi import Header, HTTPException, Query, Request

from app.config import settings
from app.db import fetch_one
from app.security import redact_log_email

_rate: dict[str, list[float]] = defaultdict(list)


def _check_rate(key: str) -> None:
    now = time.time()
    window = _rate[key]
    window[:] = [t for t in window if now - t < 60]
    if len(window) >= settings.rate_limit_per_minute:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    window.append(now)


async def require_api_key_only(
    x_support_api_key: Annotated[str | None, Header()] = None,
) -> None:
    """Только ключ Dify→db-api, без email (каталог тарифов и т.п.)."""
    if x_support_api_key != settings.support_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


async def require_support_auth(
    request: Request,
    x_support_api_key: Annotated[str | None, Header()] = None,
    x_dify_user_email: Annotated[str | None, Header()] = None,
    x_support_user_id: Annotated[str | None, Header()] = None,
    user_email: Annotated[str | None, Query(description="Email из Dify (user_email)")] = None,
) -> dict:
    if x_support_api_key != settings.support_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    session_email = (x_dify_user_email or user_email or "").strip().lower()
    if not session_email and not x_support_user_id:
        raise HTTPException(
            status_code=401,
            detail="User context required (header X-Dify-User-Email or query user_email)",
        )

    _check_rate(session_email or x_support_user_id or "anon")

    if x_support_user_id:
        user = fetch_one(
            "SELECT id, name, email, is_active, role FROM users WHERE id = %s",
            (int(x_support_user_id),),
        )
    else:
        email = session_email
        user = fetch_one(
            "SELECT id, name, email, is_active, role FROM users WHERE lower(email) = %s",
            (email,),
        )

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.get("is_active"):
        raise HTTPException(status_code=403, detail="Account inactive")

    request.state.user = user
    request.state.log_email = redact_log_email(user["email"])
    return user


def assert_shop_owner(user_id: int, shop_id: int) -> None:
    row = fetch_one("SELECT id FROM shops WHERE id = %s AND user_id = %s", (shop_id, user_id))
    if not row:
        raise HTTPException(status_code=403, detail="Shop access denied")


def assert_product_owner(user_id: int, product_id: int) -> int:
    row = fetch_one(
        """
        SELECT mp.id, mp.shop_id
        FROM marketplace_products mp
        JOIN shops s ON s.id = mp.shop_id
        WHERE mp.id = %s AND s.user_id = %s
        """,
        (product_id, user_id),
    )
    if not row:
        raise HTTPException(status_code=403, detail="Product access denied")
    return int(row["shop_id"])


def require_writes_enabled() -> None:
    if not settings.writes_enabled:
        raise HTTPException(status_code=403, detail="Write operations disabled (DB_API_MODE=readonly)")
