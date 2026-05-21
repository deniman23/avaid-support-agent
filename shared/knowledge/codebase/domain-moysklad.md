# МойСклад

Краткое описание возможностей Avaid (ветка dev, пакет `moysklad`).

## Бизнес-логика (из комментариев и кода backend-go)
- SetMoySkladAccessTokenCipher задаёт шифр для поля access_token (тесты / явная инициализация).
- InitAccessTokenEncryptionFromEnv включает AES-256-GCM, если задан MOYSKLAD_ACCESS_TOKEN_ENCRYPTION_KEY.
- Вызывать один раз на процесс (api, worker, scheduler, cli — везде, где читают/пишут moysklad_apps.access_token).
- EncryptMoySkladAccessTokenForStore шифрует токен перед INSERT/UPDATE (noop, если ключ не задан).
- SyncBundleComponents загружает состав комплектов из API МойСклад (entity/bundle/{id}/components)
- и записывает в ms_product_components. Соответствует SyncMoySkladBundleComponentsBatchJob + SyncMoySkladBundleComponentsJob.
- CalculateBundleStocks считает остатки комплектов по компонентам и пишет в ms_product_stocks и ms_products.
- Соответствует CalculateBundleStocksJob.
- Client HTTP-клиент для API МойСклад
- NewClient создаёт клиент с заданным токеном
- Get выполняет GET запрос к API
- GetEntityCount возвращает meta.size для эндпоинта (limit=1)
- Post выполняет POST запрос
- Put выполняет PUT запрос
- GetFirstRow выполняет GET с filter/limit и возвращает первый элемент из rows (для поиска по externalCode и т.д.)
- GetShipmentTemplate возвращает шаблон отгрузки по заказу покупателя (PUT entity/demand/new)
- CreateDemand создаёт отгрузку (POST entity/demand)
- GetReturnTemplate возвращает шаблон возврата по отгрузке (PUT entity/salesreturn/new)
- CreateSalesReturn создаёт возврат (POST entity/salesreturn)
- GetDemand возвращает отгрузку по ID (GET entity/demand/{id})
- GetCustomerOrder возвращает заказ покупателя по ID (GET entity/customerorder/{id})
- GetSalesReturn возвращает возврат покупателя по ID (GET entity/salesreturn/{id})
- readBody читает тело ответа и при Content-Encoding: gzip распаковывает его.
- Config конфигурация для API МойСклад
- SyncData выполняет полную синхронизацию основных данных МойСклад для пользователя.
- Соответствует SyncMoySkladDataJob в Laravel.
- Для сущностей с количеством > 1000 в PHP диспатчится SyncMoySkladEntityBatchJob; в Go пока синхронизируем только первые 1000.
- Entity endpoints и имена для синхронизации
- SyncEntities синхронизирует все сущности для пользователя (до 1000 записей каждого типа).
- Для больших объёмов Laravel диспатчит SyncMoySkladEntityBatchJob, который создаёт пагинированные SyncMoySkladEntityJob.
- SyncEntityPage синхронизирует одну страницу сущностей (offset, limit). Используется для пагинированной синхронизации.
- ErrBusiness — бизнес-ошибка (не ретраить задачу, считать выполненной)
- IsBusinessError проверяет, что ошибка — бизнес-логика (не ретраить)
- IsRateLimitOrNetwork проверяет 429 / таймаут / сеть (ретраить с задержкой)
- IsUnauthorizedAPIError — Remap 401 / ошибка 1056 (просроченный ключ). Повтор без смены токена бессмысленен.

## Для агента поддержки
- Переводи логику кода в **шаги в интерфейсе Avaid**.
- Не цитируй имена функций пользователю.
- При вопросе «как работает» — этот документ важнее коротких FAQ-сценариев.