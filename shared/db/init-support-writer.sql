-- Run on prod (or mock) as superuser after apply-ddl.sql.
-- Role for db-api with allowlisted UPDATE columns (no billing, no users.password).

DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'support_writer') THEN
    CREATE ROLE support_writer LOGIN PASSWORD 'support_writer_pass';
  END IF;
END
$$;

-- Replace avaid_support with your prod DB name when applying manually.
GRANT CONNECT ON DATABASE avaid_support TO support_writer;
GRANT USAGE ON SCHEMA public TO support_writer;

GRANT SELECT ON TABLE
  users, shops, marketplace_products, ms_products, ms_product_stocks,
  marketplace_orders, marketplace_returns, order_history, task_events,
  billing_subscriptions, tariff_plans, moysklad_apps, master_products,
  ms_sales_channels, ms_organizations, ms_warehouses, user_tariff_overrides
TO support_writer;

-- Shops: рубильники синхронизации (типичные правки поддержки)
GRANT UPDATE (sync_stock, sync_price, is_active, processes_new_orders, updated_at)
  ON shops TO support_writer;

-- Товары МП: флаги синка и привязка к МС (только в рамках своего user_id — проверяет API)
GRANT UPDATE (sync_stocks, sync_prices, ms_product_id, updated_at)
  ON marketplace_products TO support_writer;

-- Sequence usage for RETURNING id after updates (not needed for updates only)
