# Автопривязка

Краткое описание возможностей Avaid (ветка dev, пакет `autolink`).

## Бизнес-логика (из комментариев и кода backend-go)
- DefaultRules — порядок правил по умолчанию (как в Laravel).
- Run выполняет автопривязку: непривязанные товары магазина (marketplace_products) к МойСклад (ms_products) по правилам.
- Возвращает количество привязанных товаров.
- buildMsAvitoAttrIndex строит индекс: нормализованный ID объявления Avito → ms_product_id.
- Читает пользовательское дополнительное поле «Avito» из ms_products.attributes.
- extractAvitoAttrValue ищет в массиве атрибутов МойСклад поле с именем «Avito» и возвращает его значение.
- Правила `DefaultRules`: avito-attribute, sku-article, offer-article, barcode-barcode, sku-code, offer-code, offer-name, name-name
- Известные ключи штрихкодов в ответе МойСклад (и часто в данных маркетплейсов).
- rulesNeedBarcodeIndex — есть ли правило barcode-*.
- buildMsBarcodeIndex: нормализованный штрихкод → id товара МС (первый выигрывает).
- ozonBarcodeAlternateNorms — Ozon часто отдаёт "OZN{sku}"; в МС хранят только цифры.
- marketplaceBarcodeNorms — уникальные нормализованные штрихкоды из JSON товара маркетплейса.
- Правила `msBarcodeObjectKeys`: ean13, ean8, code128, gtin, upc, barcode, code, value

## Для агента поддержки
- Переводи логику кода в **шаги в интерфейсе Avaid**.
- Не цитируй имена функций пользователю.
- При вопросе «как работает» — этот документ важнее коротких FAQ-сценариев.