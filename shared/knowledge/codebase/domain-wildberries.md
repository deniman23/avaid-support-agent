# Wildberries

Краткое описание возможностей Avaid (ветка dev, пакет `wildberries`).

## Бизнес-логика (из комментариев и кода backend-go)
- FBSClient — HTTP-клиент для API Wildberries FBS (marketplace-api).
- NewFBSClient создаёт клиент FBS (api_key из БД — токен авторизации).
- get выполняет GET запрос к FBS API.
- post выполняет POST запрос.
- put выполняет PUT запрос.
- patch выполняет PATCH запрос.
- GetSupplies возвращает список поставок FBS (GET /api/v3/supplies).
- CreateSupply создаёт новую поставку (POST /api/v3/supplies). Ответ 201 и поле id.
- AddOrdersToSupply добавляет сборочные задания в поставку (PATCH /api/marketplace/v3/supplies/{id}/orders), перевод new → confirm.
- GetWarehouses возвращает список складов WB (GET /api/v3/warehouses).
- GetNewOrders возвращает новые сборочные задания FBS (GET /api/v3/orders/new).
- GetOrders возвращает задания за период (GET /api/v3/orders) с limit, next, dateFrom, dateTo.
- GetOrderStatuses возвращает статусы по списку ID (POST /api/v3/orders/status).
- GetOrderSticker возвращает PNG стикера для одного заказа (POST /api/v3/orders/stickers).
- GetReturnClaims получает заявки возвратов покупателей (GET /api/v1/claims).
- UpdateStocks обновляет остатки на складе WB. PUT /api/v3/stocks/{warehouseId}.
- stocks: [{ "chrtId": int64, "amount": N }], макс. 1000 за запрос (sku больше не принимается).
- ——— DBW (marketplace-api.wildberries.ru/api/v3/dbw) ———
- DBWClient — клиент API Wildberries DBW (тот же хост, другой путь).
- NewDBWClient создаёт клиент DBW (тот же api_key).
- GetNewOrders возвращает новые сборочные задания DBW (GET /api/v3/dbw/orders/new).
- GetCompletedOrders возвращает завершённые задания DBW (GET /api/v3/dbw/orders).
- GetOrderStatuses возвращает статусы DBW (POST /api/v3/dbw/orders/status).
- ContentClient — клиент Wildberries Content API (карточки товаров).
- NewContentClient создаёт клиент Content API (api_key из БД).
- GetCardsList запрашивает список карточек с пагинацией по cursor (POST /content/v2/get/cards/list).
- settings: cursor { limit, nmID?, updatedAt? }, filter { withPhoto?: -1 }.
- ProcessOrder обрабатывает один заказ WB (FBS, DBW, DBS): сохраняет в marketplace_orders и ставит задачу МойСклад при необходимости.
- maybeAutoConfirmWB подтверждает новое сборочное задание на маркетплейсе (см. документацию WB API).
- buildFBWOrderRow строит OrderRow из ответа statistics API (FBW заказы).
- SyncProducts загружает карточки из WB Content API и записывает/обновляет marketplace_products (как в Laravel).
- Карточки с массивом sizes разворачиваются в отдельные строки по каждому размеру (SKU/штрихкод), см. ProductDTO::fromWildberriesSizeResponse на main.
- wbProductRowsFromCard разворачивает WB-карточку: по строке на каждый size при непустом sizes; иначе одна строка как раньше.
- WBChrtIDFromProductDataJSON извлекает chrtId размера из сохранённого JSON marketplace_products.data (карточка WB).
- WBShop — магазин Wildberries из БД (для FBS достаточно api_key и type).

## Для агента поддержки
- Переводи логику кода в **шаги в интерфейсе Avaid**.
- Не цитируй имена функций пользователю.
- При вопросе «как работает» — этот документ важнее коротких FAQ-сценариев.