-- Test data for local support-agent (password not used by db-api)
INSERT INTO users (id, name, email, password, role, is_active, created_at, updated_at)
VALUES (1, 'Тест Пользователь', 'support@test.local', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'user', true, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

INSERT INTO tariff_plans (slug, name, price_monthly, is_active, created_at, updated_at)
VALUES ('basic', 'Базовый', 990.00, true, NOW(), NOW())
ON CONFLICT (slug) DO NOTHING;

INSERT INTO shops (id, user_id, name, marketplace, type, api_key, is_active, sync_stock, sync_price, created_at, updated_at)
VALUES
  (1, 1, 'Ozon Тест', 'ozon', 'fbo', 'REDACTED_LOCAL', true, true, true, NOW(), NOW()),
  (2, 1, 'WB Тест', 'wildberries', 'fbs', 'REDACTED_LOCAL', true, false, true, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

INSERT INTO ms_products (id, user_id, ms_id, name, article, product_type, stock, quantity, last_sync_at, created_at, updated_at)
VALUES
  (1, 1, 'ms-guid-001', 'Товар МС 1', 'ART-001', 'product', 10, 10, NOW(), NOW(), NOW()),
  (2, 1, 'ms-guid-002', 'Товар МС 2', 'ART-002', 'product', 0, 0, NOW() - INTERVAL '2 days', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

INSERT INTO marketplace_products (id, shop_id, marketplace_type, offer_id, name, ms_product_id, price, stock, sync_stocks, sync_prices, created_at, updated_at)
VALUES
  (1, 1, 'ozon', 'OFFER-1', 'Ozon товар 1', 1, 999.00, 5, true, true, NOW(), NOW()),
  (2, 1, 'ozon', 'OFFER-2', 'Ozon товар без привязки', NULL, 500.00, 0, false, false, NOW(), NOW()),
  (3, 2, 'wildberries', 'SKU-WB-1', 'WB товар', 2, 1200.00, 0, true, true, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

INSERT INTO marketplace_orders (id, order_id, external_id, status, address, customer, creation_date, customer_price, payout, commission, subsidies, shop_id, created_at, updated_at)
VALUES
  (1, 'ORD-1', 'EXT-1', 'processing', '{}', '{}', NOW() - INTERVAL '1 day', 1000, 900, 100, '[]', 1, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

INSERT INTO task_events (id, user_id, title, description, status, error_message, show_in_notifications, created_at, updated_at)
VALUES
  (1, 1, 'Синхронизация остатков', 'Ozon shop 1', 'error', 'Timeout connecting to marketplace API', true, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

INSERT INTO billing_subscriptions (user_id, billing_status, current_tariff_id, period_start, period_end, created_at, updated_at)
VALUES (1, 'active', 'basic', NOW() - INTERVAL '5 days', NOW() + INTERVAL '25 days', NOW(), NOW())
ON CONFLICT (user_id) DO NOTHING;
