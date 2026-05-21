# Яндекс Маркет

Краткое описание возможностей Avaid (ветка dev, пакет `yandex`).

## Бизнес-логика (из комментариев и кода backend-go)
- Client — HTTP-клиент для API Яндекс.Маркет (Seller API).
- NewClient создаёт клиент для магазина (campaign_id и api_key из БД).
- get выполняет GET запрос к API.
- GetDeliveryLabels возвращает PDF баркодов для заказа (GET campaigns/{id}/orders/{id}/delivery/labels).
- post выполняет POST запрос.
- put выполняет PUT запрос.
- patch выполняет PATCH запрос.
- SetOrderProcessingStarted подтверждает заказ продавцом: PROCESSING + STARTED (PATCH .../orders/{id}/status).
- См. документацию Яндекс.Маркет: переход из PENDING («ожидает обработки продавцом»).
- GetOrders возвращает список заказов (GET /campaigns/{id}/orders).
- Параметры: fromDate, toDate в формате d-m-Y; limit; page_token.
- GetReturns возвращает список возвратов (GET /campaigns/{id}/returns).
- GetOrdersFinancialStats возвращает финансовую статистику по заказам (POST /campaigns/{id}/stats/orders).
- orderIDs — до 50 штук.
- GetOfferMappings возвращает маппинг офферов (товаров) для бизнеса. POST /businesses/{businessId}/offer-mappings.
- pageToken — токен следующей страницы (пустая строка для первой); limit — макс. 200.
- UpdateStocks отправляет остатки на маркетплейс. PUT /campaigns/{id}/offers/stocks.
- skus: [{ "sku": "offer_id", "items": [{ "count": N }] }].
- UpdatePricesBusiness обновляет цены в кабинете. POST /businesses/{id}/offer-prices/updates.
- offers: [{ "offerId": "...", "price": { "value": "1000", "currencyId": "RUR" } }].
- UpdatePricesCampaign обновляет цены в магазине. POST /campaigns/{id}/offer-prices/updates.
- ProcessOrder обрабатывает один заказ Yandex: сохраняет в marketplace_orders и ставит задачу МойСклад при необходимости.
- maybeAutoConfirmYandex вызывает PATCH статуса заказа в PROCESSING+STARTED при статусе PENDING.
- SyncProducts загружает товары из API offer-mappings и сохраняет в marketplace_products (постранично).
- SendStocks отправляет остатки на Яндекс.Маркет. Читает warehouse_ids, stock_sync_mode из shops; остатки из ms_product_stocks.
- EffectiveSendPriceRub — публичная обёртка для предпросмотра / тестов (то же, что в SendPrices).
- yandexEffectiveSendPriceRub — рубли для выгрузки цен (согласовано с ozonSendPriceRubles):
- calculated_price используем:
- 1. при непустой user_formula;
- 2. при режиме уровня «как в магазине», когда у магазина уровень не задан, но в общем каталоге есть calculated_price.
- SendPrices отправляет цены на Яндекс.Маркет (кабинет и/или магазин по price_sync_type).
- YandexShop — магазин Яндекс.Маркет из БД.
- ActiveYandexShopIDs возвращает ID магазинов Yandex с is_active = true (для планировщика).
- ActiveYandexShopIDsForStocks — магазины Yandex с включёнными is_active и sync_stock.
- ActiveYandexShopIDsForPrices — магазины Yandex с включёнными is_active и sync_price.

## Для агента поддержки
- Переводи логику кода в **шаги в интерфейсе Avaid**.
- Не цитируй имена функций пользователю.
- При вопросе «как работает» — этот документ важнее коротких FAQ-сценариев.