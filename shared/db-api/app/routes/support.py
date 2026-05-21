from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth import assert_shop_owner, require_api_key_only, require_support_auth
from app.db import fetch_all, fetch_one
from app.security import pick

router = APIRouter(prefix="/support", tags=["support"])

UserDep = Annotated[dict, Depends(require_support_auth)]
ApiKeyDep = Annotated[None, Depends(require_api_key_only)]

SHOP_FIELDS = [
    "id",
    "user_id",
    "name",
    "marketplace",
    "type",
    "is_active",
    "sync_stock",
    "sync_price",
    "processes_new_orders",
    "created_at",
    "updated_at",
]


@router.get("/users/lookup")
def users_lookup(user: UserDep, email: str = Query(..., min_length=3, max_length=255)):
    email = email.strip().lower()
    if email != user["email"].lower():
        raise HTTPException(status_code=403, detail="Email lookup only for session user")
    return pick(user, ["id", "name", "email", "is_active", "role"])


@router.get("/shops")
def list_shops(user: UserDep):
    rows = fetch_all(
        """
        SELECT id, user_id, name, marketplace, type, is_active, sync_stock, sync_price,
               processes_new_orders, created_at, updated_at
        FROM shops WHERE user_id = %s ORDER BY sort_order, id
        """,
        (user["id"],),
    )
    return [pick(r, SHOP_FIELDS) for r in rows]


@router.get("/stock/check")
def stock_check(user: UserDep, shop_id: int = Query(..., ge=1)):
    assert_shop_owner(user["id"], shop_id)
    shop = fetch_one(
        "SELECT id, name, sync_stock, is_active FROM shops WHERE id = %s AND user_id = %s",
        (shop_id, user["id"]),
    )
    products = fetch_all(
        """
        SELECT mp.id, mp.offer_id, mp.name, mp.stock, mp.sync_stocks, mp.ms_product_id,
               ms.stock AS ms_stock, ms.quantity AS ms_quantity, ms.last_sync_at
        FROM marketplace_products mp
        LEFT JOIN ms_products ms ON ms.id = mp.ms_product_id AND ms.user_id = %s
        WHERE mp.shop_id = %s
        ORDER BY mp.id
        LIMIT 50
        """,
        (user["id"], shop_id),
    )
    safe_products = [
        pick(
            p,
            [
                "id",
                "offer_id",
                "name",
                "stock",
                "sync_stocks",
                "ms_product_id",
                "ms_stock",
                "ms_quantity",
                "last_sync_at",
            ],
        )
        for p in products
    ]
    return {"shop": shop, "products": safe_products, "product_count": len(safe_products)}


@router.get("/stock/issues")
def stock_issues(user: UserDep, shop_id: int | None = None):
    sql = """
        SELECT s.id AS shop_id, s.name AS shop_name, s.sync_stock, s.is_active,
               mp.id AS product_id, mp.offer_id, mp.name AS product_name,
               mp.stock, mp.sync_stocks, mp.ms_product_id
        FROM shops s
        JOIN marketplace_products mp ON mp.shop_id = s.id
        WHERE s.user_id = %s
          AND (s.sync_stock = false OR s.is_active = false OR mp.sync_stocks = false OR mp.ms_product_id IS NULL)
    """
    params: tuple = (user["id"],)
    if shop_id:
        assert_shop_owner(user["id"], shop_id)
        sql += " AND s.id = %s"
        params = (user["id"], shop_id)
    sql += " ORDER BY s.id, mp.id LIMIT 50"
    rows = fetch_all(sql, params)
    return {"issues": rows, "count": len(rows)}


@router.get("/prices/check")
def prices_check(user: UserDep, shop_id: int = Query(..., ge=1)):
    assert_shop_owner(user["id"], shop_id)
    shop = fetch_one(
        "SELECT id, name, sync_price, is_active FROM shops WHERE id = %s AND user_id = %s",
        (shop_id, user["id"]),
    )
    products = fetch_all(
        """
        SELECT id, offer_id, name, price, calculated_price, sync_prices,
               remove_from_actions, min_price, is_ucenka
        FROM marketplace_products WHERE shop_id = %s ORDER BY id LIMIT 50
        """,
        (shop_id,),
    )
    return {
        "shop": shop,
        "products": [
            pick(
                p,
                [
                    "id",
                    "offer_id",
                    "name",
                    "price",
                    "calculated_price",
                    "sync_prices",
                    "remove_from_actions",
                    "min_price",
                    "is_ucenka",
                ],
            )
            for p in products
        ],
    }


@router.get("/products/unlinked")
def products_unlinked(user: UserDep, shop_id: int = Query(..., ge=1)):
    assert_shop_owner(user["id"], shop_id)
    rows = fetch_all(
        """
        SELECT id, offer_id, name, stock, price
        FROM marketplace_products
        WHERE shop_id = %s AND ms_product_id IS NULL
        ORDER BY id LIMIT 50
        """,
        (shop_id,),
    )
    return {"unlinked": rows, "count": len(rows)}


@router.get("/orders/recent")
def orders_recent(user: UserDep, shop_id: int = Query(..., ge=1)):
    assert_shop_owner(user["id"], shop_id)
    rows = fetch_all(
        """
        SELECT id, order_id, external_id, status, substatus, creation_date,
               customer_price, barcode_path, missing_ms_item
        FROM marketplace_orders
        WHERE shop_id = %s
        ORDER BY creation_date DESC
        LIMIT 20
        """,
        (shop_id,),
    )
    return {"orders": rows}


@router.get("/returns/recent")
def returns_recent(user: UserDep, shop_id: int = Query(..., ge=1)):
    assert_shop_owner(user["id"], shop_id)
    rows = fetch_all(
        """
        SELECT id, external_id, shipment_status, refund_status, created_at, updated_at
        FROM marketplace_returns
        WHERE shop_id = %s
        ORDER BY created_at DESC NULLS LAST
        LIMIT 20
        """,
        (shop_id,),
    )
    return {"returns": rows}


@router.get("/sync/last-error")
def sync_last_error(user: UserDep):
    row = fetch_one(
        """
        SELECT id, title, status, error_message, entity_type, entity_name, created_at, completed_at
        FROM task_events
        WHERE user_id = %s AND status = 'error'
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (user["id"],),
    )
    return {"last_error": row}


@router.get("/tariffs/catalog")
def tariffs_catalog(_: ApiKeyDep):
    """Активные тарифы из tariff_plans — для ответов без email и без markdown."""
    rows = fetch_all(
        """
        SELECT slug, name, external_tariff_id, price_monthly, currency, is_active,
               sort_order, settings
        FROM tariff_plans
        WHERE is_active = true
        ORDER BY sort_order NULLS LAST, name
        """
    )
    plans = []
    for r in rows:
        settings = r.get("settings") or {}
        limits = settings.get("limits") if isinstance(settings, dict) else {}
        plans.append(
            {
                "slug": r.get("slug"),
                "name": r.get("name"),
                "price_monthly": float(r["price_monthly"]) if r.get("price_monthly") is not None else None,
                "currency": r.get("currency") or "RUB",
                "store_limit": limits.get("stores") if isinstance(limits, dict) else None,
                "product_limit": limits.get("products") if isinstance(limits, dict) else None,
            }
        )
    return {"plans": plans, "source": "database:tariff_plans"}


@router.get("/billing/status")
def billing_status(user: UserDep):
    sub = fetch_one(
        """
        SELECT billing_status, current_tariff_id, period_start, period_end, auto_renew
        FROM billing_subscriptions WHERE user_id = %s
        """,
        (user["id"],),
    )
    plan = None
    if sub and sub.get("current_tariff_id"):
        plan = fetch_one(
            "SELECT slug, name, price_monthly, is_active FROM tariff_plans WHERE slug = %s",
            (sub["current_tariff_id"],),
        )
    return {
        "subscription": sub,
        "tariff_plan": plan,
        "note": "Только справочная информация. Изменение тарифа и возвраты — через поддержку.",
    }
