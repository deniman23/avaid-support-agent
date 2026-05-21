# Telegram

Краткое описание возможностей Avaid (ветка dev, пакет `telegram`).

## Бизнес-логика (из комментариев и кода backend-go)
- Client — клиент Telegram Bot API.
- NewClient создаёт клиент Telegram.
- EscapeHTML экранирует текст для Telegram parse_mode=HTML.
- NormalizeChatID — добавляет @ к username если нужно.
- ResolveOrderChatID возвращает chat_id для уведомлений по заказам
- строго из настроек конкретного магазина (shops.telegram_chat_id).
- SendDocument отправляет документ в Telegram чат.
- SendDocumentBytes отправляет документ из байтов (для PDF в памяти).
- SendMessage отправляет текстовое сообщение в Telegram чат.
- SendMessageHTML отправляет сообщение с parse_mode=HTML.

## Для агента поддержки
- Переводи логику кода в **шаги в интерфейсе Avaid**.
- Не цитируй имена функций пользователю.
- При вопросе «как работает» — этот документ важнее коротких FAQ-сценариев.