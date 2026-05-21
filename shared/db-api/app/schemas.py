from pydantic import BaseModel, Field


class ShopSettingsUpdate(BaseModel):
    sync_stock: bool | None = None
    sync_price: bool | None = None
    is_active: bool | None = None
    processes_new_orders: bool | None = None


class ProductSyncUpdate(BaseModel):
    sync_stocks: bool | None = None
    sync_prices: bool | None = None


class ProductLinkUpdate(BaseModel):
    ms_product_id: int = Field(..., ge=1)
