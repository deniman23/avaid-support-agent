# Ozon

Краткое описание возможностей Avaid (ветка dev, пакет `ozon`).

## Бизнес-логика (из комментариев и кода backend-go)
- Client — HTTP-клиент для API Ozon Seller.
- NewClient создаёт клиент с учётными данными магазина.
- validateClientID проверяет, что Client-Id — непустая строка с положительным целым (Ozon API требование).
- doHTTP — GET/POST с ретраями при 429/503 и сетевых сбоях.
- get выполняет GET запрос к API Ozon.
- post выполняет POST запрос к API Ozon.
- GetFBSOrders возвращает список FBS заказов (v3/posting/fbs/list).
- GetFBSOrder возвращает один FBS заказ по posting_number.
- GetOrdersByStatusChangeDate возвращает заказы за период по дате изменения статуса.
- GetFBOOrders возвращает список FBO заказов.
- ShipFBSV4 подтверждает сборку FBS-отправления и переводит его в awaiting_deliver (POST /v4/posting/fbs/ship).
- products: элементы [{ "product_id": int, "quantity": int }] внутри одной упаковки, как в документации Ozon Seller API.
- GetPackageLabel возвращает PDF баркода для FBS отправления (POST /v2/posting/fbs/package-label).
- GetFBOOrder возвращает один FBO заказ по posting_number.
- GetReturns возвращает список возвратов (v1/returns/list).
- params может содержать filter (visual_status_change_moment: {time_from, time_to}, return_schema), limit, last_id.
- GetWarehouses возвращает список складов Ozon.
- С 2026-04 Ozon отключил /v1/warehouse/list (obsolete method),
- поэтому используем актуальный /v2/warehouse/list.
- GetFinanceReportForPosting возвращает финансовый отчёт по отправлению.
- GetProducts возвращает список товаров (v3/product/list).
- GetProductInfo возвращает детальную информацию о товарах по product_id.
- GetStocks возвращает остатки по товарам.
- msStockByMsProductID агрегирует quantity из ms_product_stocks по складам магазина (как Laravel SyncOzonStocksChunkJob).
- getShopOzonSelectedWarehouseIDs — JSON shops.ozon_selected_warehouses (как Laravel getOzonSelectedWarehouses).
- getOzonWarehouseIDsForStocks: сначала выбранные склады в настройках магазина, иначе все из ozon_warehouses.
- AggregatedMSStockForShop — остатки МС по товарам (warehouse_ids + stock_sync_mode), как при отправке на Ozon.
- ProcessOrder обрабатывает один заказ Ozon: сохраняет в marketplace_orders и ставит задачу МойСклад при необходимости.
- rawOrder — сырой ответ API (result для FBS/FBO get или элемент postings для list).
- isNewOrder — true для нового заказа, false для обновления существующего.
- maybeAutoShipFBS вызывает POST /v4/posting/fbs/ship при переходе в awaiting_packaging, если включено processes_new_orders.
- Без флага отправление не переводится в awaiting_deliver автоматически (ожидается действие в ЛК Ozon).
- POST /v2/products/stocks: stocks — 1..100 элементов.
- SyncProducts: list + info/list + info/stocks.
- jsonScalarToSKUString приводит sku из JSON (строка или число) к строке для БД и автопривязки.

## Для агента поддержки
- Переводи логику кода в **шаги в интерфейсе Avaid**.
- Не цитируй имена функций пользователю.
- При вопросе «как работает» — этот документ важнее коротких FAQ-сценариев.