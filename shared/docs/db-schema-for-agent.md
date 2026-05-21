# Схема БД Avaid для агента поддержки

Глоссарий таблиц и полей для **внутреннего** использования (tools db-api). Клиенту **не называть** имена таблиц и полей (закон 3).

## billing_addons

Поля (без секретов): `id`, `user_id`, `references`, `on`, `addon_key`, `status`, `period_start`, `period_end`, `last_payment_id`, `references`, `on`, `created_at`, `updated_at`


## billing_subscriptions

Поля (без секретов): `user_id`, `references`, `on`, `billing_status`, `current_tariff_id`, `period_start`, `period_end`, `grace_until`, `last_payment_id`, `created_at`, `updated_at`, `auto_renew`, `tochka_consumer_id`, `tochka_subscription_operation_id`, `renewal_reminder_sent_at`, `comment`, `comment`, `comment`


## marketplace_orders

Поля (без секретов): `id`, `order_id`, `external_id`, `status`, `substatus`, `address`, `customer`, `creation_date`, `shipment_date`, `customer_price`, `payout`, `commission`, `subsidies`, `ms_order_id`, `ms_demand_id`, `return_id`, `references`, `on`, `shop_id`, `references`, `on`, `created_at`, `updated_at`, `delivery_date`, `items`, `missing_ms_item`, `has_archive_items`, `barcode_path`, `barcode_obtained_at`, `telegram_notified_at`, `comment`, `comment`


## marketplace_products

Поля (без секретов): `id`, `shop_id`, `references`, `on`, `marketplace_type`, `offer_id`, `name`, `ms_product_id`, `references`, `on`, `price`, `image`, `is_discounted`, `is_ucenka`, `user_formula`, `calculated_price`, `remove_from_actions`, `stock`, `data`, `created_at`, `updated_at`, `master_product_id`, `references`, `on`, `sync_stocks`, `sync_prices`, `exclude_from_promotions`, `discount`, `min_price`, `competitor_links`, `competitor_price`, `sku`, `search_vector`, `ms_price_level_id`, `comment`, `comment`, `comment`, `comment`

- **stock**, **sync_stocks**, **sync_prices** — остатки/цены на МП
- **ms_product_id** — привязка к МойСклад

## marketplace_returns

Поля (без секретов): `id`, `shop_id`, `references`, `on`, `external_id`, `order_external_id`, `order_id`, `shipment_status`, `refund_status`, `return_type`, `refund_amount`, `created_at_marketplace`, `updated_at_marketplace`, `created_at`, `updated_at`, `ms_return_id`


## master_products

Поля (без секретов): `id`, `user_id`, `references`, `on`, `master_offer_id`, `name`, `image_url`, `created_at`, `updated_at`


## moysklad_apps

Поля (без секретов): `id`, `app_id`, `account_id`, `app_uid`, `account_name`, `status`, `cause`, `settings`, `subscription_data`, `user_id`, `created_at`, `updated_at`, `tariff_id`, `service_provider`, `comment`, `comment`, `comment`, `comment`, `comment`, `comment`, `comment`, `comment`, `comment`, `comment`, `comment`, `comment`


## ms_organizations

Поля (без секретов): `id`, `user_id`, `references`, `on`, `ms_id`, `name`, `description`, `code`, `external_code`, `archived`, `shared`, `legal_title`, `legal_address`, `actual_address`, `inn`, `kpp`, `ogrn`, `okpo`, `email`, `phone`, `fax`, `payer_vat`, `created_at`, `updated_at`


## ms_product_stocks

Поля (без секретов): `id`, `ms_product_id`, `references`, `on`, `ms_warehouse_id`, `references`, `on`, `stock`, `reserve`, `in_transit`, `quantity`, `created_at`, `updated_at`


## ms_products

Поля (без секретов): `id`, `user_id`, `references`, `on`, `ms_id`, `name`, `description`, `article`, `code`, `external_code`, `product_type`, `parent_product_id`, `archived`, `shared`, `weight`, `volume`, `uom_id`, `uom_name`, `vat`, `vat_enabled`, `min_price`, `purchase_price`, `sale_price`, `stock`, `reserve`, `in_transit`, `quantity`, `attributes`, `images`, `barcodes`, `characteristics`, `created_at`, `updated_at`, `last_sync_at`, `sale_prices`, `comment`, `comment`


## ms_sales_channels

Поля (без секретов): `id`, `user_id`, `references`, `on`, `ms_id`, `name`, `description`, `type`, `external_code`, `archived`, `shared`, `created_at`, `updated_at`


## ms_warehouses

Поля (без секретов): `id`, `user_id`, `references`, `on`, `ms_id`, `name`, `description`, `code`, `external_code`, `archived`, `shared`, `address`, `path_name`, `attributes`, `created_at`, `updated_at`


## order_history

Поля (без секретов): `id`, `order_id`, `references`, `on`, `event_type`, `title`, `description`, `old_data`, `new_data`, `metadata`, `occurred_at`, `created_at`, `updated_at`


## ozon_warehouses

Поля (без секретов): `id`, `shop_id`, `references`, `on`, `warehouse_id`, `name`, `has_entrusted_acceptance`, `is_rfbs`, `can_print_act_in_advance`, `has_postings_limit`, `is_karantin`, `is_kgt`, `is_economy`, `is_timetable_editable`, `min_postings_limit`, `postings_limit`, `min_working_days`, `status`, `working_days`, `first_mile_type`, `created_at`, `updated_at`, `comment`, `comment`, `comment`, `comment`, `comment`


## shops

Поля (без секретов): `id`, `user_id`, `references`, `on`, `name`, `marketplace`, `type`, `client_id`, `campaign_id`, `business_id`, `ms_organization_id`, `references`, `on`, `ms_counterparty_id`, `references`, `on`, `ms_sales_channel_id`, `references`, `on`, `ms_warehouse_id`, `references`, `on`, `ms_project_id`, `references`, `on`, `ms_contract_id`, `references`, `on`, `processes_new_orders`, `create_customer_orders`, `create_demands`, `document_prices`, `stock_sync_mode`, `warehouse_ids`, `processes_returns`, `ms_return_arrival_warehouse_id`, `references`, `on`, `ms_return_completion_warehouse_id`, `references`, …

- **sync_stock** — рубильник остатков на магазин
- **sync_price** — рубильник цен
- **is_active** — магазин включён

## tariff_plans

Поля (без секретов): `id`, `slug`, `name`, `external_tariff_id`, `price_monthly`, `currency`, `is_active`, `sort_order`, `settings`, `created_at`, `updated_at`


## task_events

Поля (без секретов): `id`, `user_id`, `references`, `on`, `title`, `description`, `status`, `entity_type`, `entity_id`, `entity_name`, `show_in_notifications`, `started_at`, `completed_at`, `duration`, `metadata`, `error_message`, `created_at`, `updated_at`


## user_tariff_overrides

Поля (без секретов): `id`, `user_id`, `references`, `on`, `discount_type`, `discount_value`, `discount_starts_at`, `discount_ends_at`, `capabilities`, `note`, `created_at`, `updated_at`


## users

Поля (без секретов): `id`, `name`, `email`, `email_verified_at`, `role`, `is_active`, `created_at`, `updated_at`, `ms_account_id`, `admin_comment`, `is_pinned`, `privacy_consent_accepted_at`, `telegram_bot_token`, `telegram_support_chat_id`, `telegram_webhook_secret`, `telegram_support_topic_id`, `telegram_support_admin_tg_user_id`, `comment`


## wildberries_warehouses

Поля (без секретов): `id`, `shop_id`, `references`, `on`, `warehouse_id`, `office_id`, `name`, `cargo_type`, `delivery_type`, `is_processing`, `is_deleting`, `status`, `raw_data`, `created_at`, `updated_at`


## Запрещено возвращать клиенту

`password`, `api_key`, токены, `raw`, `payload`, `callback_payload`.

## Legacy (не использовать в tools)

`migrations`, `jobs`, `sessions`, `cache`, `failed_jobs`.