-- Run after apply-ddl.sql as superuser (admin)
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'support_reader') THEN
    CREATE ROLE support_reader LOGIN PASSWORD 'support_reader_pass';
  END IF;
END
$$;

GRANT CONNECT ON DATABASE avaid_support TO support_reader;
GRANT USAGE ON SCHEMA public TO support_reader;

GRANT SELECT ON TABLE
  users, shops, marketplace_products, ms_products, ms_product_stocks,
  marketplace_orders, marketplace_returns, order_history, task_events,
  billing_subscriptions, tariff_plans, moysklad_apps, master_products,
  ms_sales_channels, ms_organizations, ms_warehouses, user_tariff_overrides
TO support_reader;

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO support_reader;
