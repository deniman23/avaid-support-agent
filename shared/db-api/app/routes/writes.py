from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.auth import (
    assert_product_owner,
    assert_shop_owner,
    require_support_auth,
    require_writes_enabled,
)
from app.db import execute_returning, fetch_one
from app.routes.support import SHOP_FIELDS
from app.schemas import ProductLinkUpdate, ProductSyncUpdate, ShopSettingsUpdate
from app.security import pick

router = APIRouter(prefix="/support", tags=["support-writes"])

UserDep = Annotated[dict, Depends(require_support_auth)]
WritesDep = Annotated[None, Depends(require_writes_enabled)]


@router.patch("/shops/{shop_id}/settings")
def update_shop_settings(
    shop_id: int,
    body: ShopSettingsUpdate,
    user: UserDep,
    _: WritesDep,
):
    assert_shop_owner(user["id"], shop_id)
    fields = body.model_dump(exclude_none=True)
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    allowed = {"sync_stock", "sync_price", "is_active", "processes_new_orders"}
    if not set(fields).issubset(allowed):
        raise HTTPException(status_code=400, detail="Field not allowed")

    sets = ", ".join(f"{k} = %s" for k in fields)
    params = tuple(fields.values()) + (shop_id, user["id"])
    row = execute_returning(
        f"""
        UPDATE shops SET {sets}, updated_at = NOW()
        WHERE id = %s AND user_id = %s
        RETURNING id, user_id, name, marketplace, type, is_active, sync_stock, sync_price,
                  processes_new_orders, created_at, updated_at
        """,
        params,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Shop not found")
    return {"shop": pick(row, SHOP_FIELDS), "updated": list(fields.keys())}


@router.patch("/products/{product_id}/sync")
def update_product_sync(
    product_id: int,
    body: ProductSyncUpdate,
    user: UserDep,
    _: WritesDep,
):
    assert_product_owner(user["id"], product_id)
    fields = body.model_dump(exclude_none=True)
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    if not set(fields).issubset({"sync_stocks", "sync_prices"}):
        raise HTTPException(status_code=400, detail="Field not allowed")

    sets = ", ".join(f"{k} = %s" for k in fields)
    params = tuple(fields.values()) + (product_id,)
    row = execute_returning(
        f"""
        UPDATE marketplace_products mp
        SET {sets}, updated_at = NOW()
        FROM shops s
        WHERE mp.id = %s AND mp.shop_id = s.id AND s.user_id = %s
        RETURNING mp.id, mp.shop_id, mp.offer_id, mp.name, mp.sync_stocks, mp.sync_prices, mp.ms_product_id
        """,
        params + (user["id"],),
    )
    if not row:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"product": row, "updated": list(fields.keys())}


@router.patch("/products/{product_id}/link")
def link_product_to_ms(
    product_id: int,
    body: ProductLinkUpdate,
    user: UserDep,
    _: WritesDep,
):
    assert_product_owner(user["id"], product_id)
    ms = fetch_one(
        "SELECT id FROM ms_products WHERE id = %s AND user_id = %s",
        (body.ms_product_id, user["id"]),
    )
    if not ms:
        raise HTTPException(status_code=400, detail="ms_product_id not found for this user")

    row = execute_returning(
        """
        UPDATE marketplace_products mp
        SET ms_product_id = %s, updated_at = NOW()
        FROM shops s
        WHERE mp.id = %s AND mp.shop_id = s.id AND s.user_id = %s
        RETURNING mp.id, mp.shop_id, mp.offer_id, mp.name, mp.ms_product_id, mp.sync_stocks, mp.sync_prices
        """,
        (body.ms_product_id, product_id, user["id"]),
    )
    if not row:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"product": row}
