# Тарифы и доступ

Краткое описание возможностей Avaid (ветка dev, пакет `billingaccess`).

## Бизнес-логика (из комментариев и кода backend-go)
- UserHasServiceAccess — можно ли выполнять фоновые операции (синк заказов в МойСклад, Telegram-ленту).
- Логика совпадает с API hasPaidOrTrialBillingAccess.
- UserHasServiceAccessForShop проверяет доступ владельца магазина.
- HasActivePaidAccess — оплаченный период (active/grace) или действующая подписка решения в МойСклад.
- HasLegacyMoySkladAppPaidAccess — оплата только в subscription_data приложения.
- DefaultBillingConfig — минимальные настройки биллинга из окружения (для воркеров без полного Config).
- ParseExpiryFromMoySkladSubscriptionJSON извлекает срок окончания из subscription_data приложения МойСклад.

## Для агента поддержки
- Переводи логику кода в **шаги в интерфейсе Avaid**.
- Не цитируй имена функций пользователю.
- При вопросе «как работает» — этот документ важнее коротких FAQ-сценариев.