# Заказы и уведомления

Краткое описание возможностей Avaid (ветка dev, пакет `ordernotify`).

## Бизнес-логика (из комментариев и кода backend-go)
- NotifyPhaseNew — уведомление «новый заказ»; NotifyPhaseBarcode — только этикетка (напр. Ozon awaiting_deliver).
- TryClaimTelegramOrderNotify вставляет claim; false если такой заказ+чат+фаза уже были (дубль по другому shop).
- ReleaseTelegramOrderNotifyClaim снимает claim после неуспешной отправки (чтобы можно было повторить).
- ShouldSkipTelegramNewOrderStatus — не слать «новый заказ» в Telegram для заведомо финальных/отменённых статусов.
- IsReadyToShip reports whether a marketplace order reached the first status where
- we want to send the Telegram "new order" notification.
- IsTransitionToReadyToShip reports whether the order just entered the first
- notification-eligible status.
- AlreadyTelegramNotified reports whether marketplace_orders.telegram_notified_at is set.
- MarkTelegramNotified sets telegram_notified_at after a successful Telegram delivery.

## Для агента поддержки
- Переводи логику кода в **шаги в интерфейсе Avaid**.
- Не цитируй имена функций пользователю.
- При вопросе «как работает» — этот документ важнее коротких FAQ-сценариев.