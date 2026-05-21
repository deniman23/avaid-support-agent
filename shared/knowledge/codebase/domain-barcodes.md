# Штрихкоды и этикетки

Краткое описание возможностей Avaid (ветка dev, пакет `barcode`).

## Бизнес-логика (из комментариев и кода backend-go)
- Package barcode — генерация PDF с баркодами заказов (Ozon, Yandex, Wildberries, Avito).
- Используется API (скачивание) и worker (отправка в Telegram по расписанию).
- Order — заказ для печати баркода.
- Generator генерирует PDF с баркодами.
- LoadOrdersByUser загружает заказы для пользователя (API).
- LoadOrdersByUserWithMode загружает заказы для пользователя с учетом режима печати.
- LoadOrdersForShop загружает заказы для магазина (worker, по расписанию).
- LoadOrdersForShops загружает заказы для нескольких магазинов одного пользователя (один PDF в Telegram).
- printDownloadMaxRows — сколько последних заказов подгружать для кнопки «Баркоды» в UI.
- LoadOrdersForPrintDownload загружает заказы для POST /jwt/barcodes/print.
- GeneratePDF генерирует PDF с баркодами.
- GeneratePDFWithMode генерирует PDF: титульный лист-таблица (хронологический порядок) + баркоды.
- Для mode="orders" включаются только заказы с shipment_date = сегодня или завтра (по МСК).
- createOrderTableTitlePagePDF формирует первый лист PDF: таблица заказов в хронологическом порядке.
- Колонки: №, Маркетплейс, Магазин, Номер заказа, Товар, Кол-во, Дата отгрузки.
- Пути к DejaVu для титульных страниц (кириллица). Alpine: apk add ttf-dejavu
- dejavuFontPaths возвращает пути к regular и bold TTF для AddUTF8Font.

## Для агента поддержки
- Переводи логику кода в **шаги в интерфейсе Avaid**.
- Не цитируй имена функций пользователю.
- При вопросе «как работает» — этот документ важнее коротких FAQ-сценариев.