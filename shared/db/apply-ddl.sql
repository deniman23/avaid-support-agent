create table public.migrations
(
    id        serial
        primary key,
    migration varchar(255) not null,
    batch     integer      not null
);
alter table public.migrations
    owner to admin;
create table public.users
(
    id                                bigserial
        primary key,
    name                              varchar(255)                                   not null,
    email                             varchar(255)                                   not null
        constraint users_email_unique
            unique,
    email_verified_at                 timestamp(0),
    password                          varchar(255)                                   not null,
    role                              varchar(255) default 'user'::character varying not null,
    is_active                         boolean      default true                      not null,
    remember_token                    varchar(100),
    created_at                        timestamp(0),
    updated_at                        timestamp(0),
    ms_account_id                     varchar(255),
    admin_comment                     text,
    is_pinned                         boolean      default false                     not null,
    privacy_consent_accepted_at       timestamp(0),
    telegram_bot_token                text,
    telegram_support_chat_id          bigint,
    telegram_webhook_secret           varchar(64),
    telegram_support_topic_id         bigint,
    telegram_support_admin_tg_user_id bigint
);
comment on column public.users.ms_account_id is 'MoySklad Account ID';
alter table public.users
    owner to admin;
create index users_ms_account_id_index
    on public.users (ms_account_id);
create table public.password_reset_tokens
(
    email      varchar(255) not null
        primary key,
    token      varchar(255) not null,
    created_at timestamp(0)
);
alter table public.password_reset_tokens
    owner to admin;
create table public.sessions
(
    id            varchar(255) not null
        primary key,
    user_id       bigint,
    ip_address    varchar(45),
    user_agent    text,
    payload       text         not null,
    last_activity integer      not null
);
alter table public.sessions
    owner to admin;
create index sessions_user_id_index
    on public.sessions (user_id);
create index sessions_last_activity_index
    on public.sessions (last_activity);
create table public.cache
(
    key        varchar(255) not null
        primary key,
    value      text         not null,
    expiration integer      not null
);
alter table public.cache
    owner to admin;
create table public.cache_locks
(
    key        varchar(255) not null
        primary key,
    owner      varchar(255) not null,
    expiration integer      not null
);
alter table public.cache_locks
    owner to admin;
create table public.jobs
(
    id           bigserial
        primary key,
    queue        varchar(255) not null,
    payload      text         not null,
    attempts     smallint     not null,
    reserved_at  integer,
    available_at integer      not null,
    created_at   integer      not null
);
alter table public.jobs
    owner to admin;
create index jobs_queue_index
    on public.jobs (queue);
create table public.job_batches
(
    id             varchar(255) not null
        primary key,
    name           varchar(255) not null,
    total_jobs     integer      not null,
    pending_jobs   integer      not null,
    failed_jobs    integer      not null,
    failed_job_ids text         not null,
    options        text,
    cancelled_at   integer,
    created_at     integer      not null,
    finished_at    integer
);
alter table public.job_batches
    owner to admin;
create table public.failed_jobs
(
    id         bigserial
        primary key,
    uuid       varchar(255)                           not null
        constraint failed_jobs_uuid_unique
            unique,
    connection text                                   not null,
    queue      text                                   not null,
    payload    text                                   not null,
    exception  text                                   not null,
    failed_at  timestamp(0) default CURRENT_TIMESTAMP not null
);
alter table public.failed_jobs
    owner to admin;
create table public.ms_sales_channels
(
    id            bigserial
        primary key,
    user_id       bigint                not null
        constraint ms_sales_channels_user_id_foreign
            references public.users
            on delete cascade,
    ms_id         varchar(255)          not null,
    name          varchar(255)          not null,
    description   text,
    type          varchar(255),
    external_code varchar(255),
    archived      boolean default false not null,
    shared        boolean default false not null,
    created_at    timestamp(0),
    updated_at    timestamp(0),
    constraint ms_sales_channels_user_id_ms_id_unique
        unique (user_id, ms_id)
);
alter table public.ms_sales_channels
    owner to admin;
create index ms_sales_channels_ms_id_index
    on public.ms_sales_channels (ms_id);
create table public.ms_organizations
(
    id             bigserial
        primary key,
    user_id        bigint                not null
        constraint ms_organizations_user_id_foreign
            references public.users
            on delete cascade,
    ms_id          varchar(255)          not null,
    name           varchar(255)          not null,
    description    text,
    code           varchar(255),
    external_code  varchar(255),
    archived       boolean default false not null,
    shared         boolean default false not null,
    legal_title    varchar(255),
    legal_address  text,
    actual_address text,
    inn            varchar(255),
    kpp            varchar(255),
    ogrn           varchar(255),
    okpo           varchar(255),
    email          varchar(255),
    phone          varchar(255),
    fax            varchar(255),
    payer_vat      boolean default true  not null,
    created_at     timestamp(0),
    updated_at     timestamp(0),
    constraint ms_organizations_user_id_ms_id_unique
        unique (user_id, ms_id)
);
alter table public.ms_organizations
    owner to admin;
create index ms_organizations_ms_id_index
    on public.ms_organizations (ms_id);
create table public.ms_warehouses
(
    id            bigserial
        primary key,
    user_id       bigint                not null
        constraint ms_warehouses_user_id_foreign
            references public.users
            on delete cascade,
    ms_id         varchar(255)          not null,
    name          varchar(255)          not null,
    description   text,
    code          varchar(255),
    external_code varchar(255),
    archived      boolean default false not null,
    shared        boolean default false not null,
    address       text,
    path_name     varchar(255),
    attributes    json,
    created_at    timestamp(0),
    updated_at    timestamp(0),
    constraint ms_warehouses_user_id_ms_id_unique
        unique (user_id, ms_id)
);
alter table public.ms_warehouses
    owner to admin;
create index ms_warehouses_ms_id_index
    on public.ms_warehouses (ms_id);
create table public.ms_projects
(
    id            bigserial
        primary key,
    user_id       bigint                not null
        constraint ms_projects_user_id_foreign
            references public.users
            on delete cascade,
    ms_id         varchar(255)          not null,
    name          varchar(255)          not null,
    description   text,
    code          varchar(255),
    external_code varchar(255),
    archived      boolean default false not null,
    shared        boolean default false not null,
    attributes    json,
    files         json,
    created_at    timestamp(0),
    updated_at    timestamp(0),
    constraint ms_projects_user_id_ms_id_unique
        unique (user_id, ms_id)
);
alter table public.ms_projects
    owner to admin;
create index ms_projects_ms_id_index
    on public.ms_projects (ms_id);
create table public.ms_counterparties
(
    id                   bigserial
        primary key,
    user_id              bigint                not null
        constraint ms_counterparties_user_id_foreign
            references public.users
            on delete cascade,
    ms_id                varchar(255)          not null,
    name                 varchar(255)          not null,
    company_type         varchar(255),
    legal_title          varchar(255),
    legal_address        text,
    actual_address       text,
    inn                  varchar(255),
    kpp                  varchar(255),
    ogrn                 varchar(255),
    ogrnip               varchar(255),
    okpo                 varchar(255),
    code                 varchar(255),
    external_code        varchar(255),
    phone                varchar(255),
    fax                  varchar(255),
    email                varchar(255),
    state_ms_id          varchar(255),
    price_type_ms_id     varchar(255),
    discount_card_number varchar(255),
    archived             boolean default false not null,
    shared               boolean default false not null,
    attributes           json,
    contact_persons      json,
    bank_accounts        json,
    files                json,
    tags                 json,
    created_at           timestamp(0),
    updated_at           timestamp(0),
    description          text,
    constraint ms_counterparties_user_id_ms_id_unique
        unique (user_id, ms_id)
);
alter table public.ms_counterparties
    owner to admin;
create index ms_counterparties_ms_id_index
    on public.ms_counterparties (ms_id);
create table public.ms_contracts
(
    id                         bigserial
        primary key,
    user_id                    bigint                not null
        constraint ms_contracts_user_id_foreign
            references public.users
            on delete cascade,
    ms_id                      varchar(255)          not null,
    name                       varchar(255)          not null,
    description                text,
    code                       varchar(255),
    external_code              varchar(255),
    archived                   boolean default false not null,
    shared                     boolean default false not null,
    moment                     timestamp(0),
    sum                        numeric(15, 2),
    contract_type              varchar(255),
    own_agent_ms_id            varchar(255),
    agent_ms_id                varchar(255),
    state_ms_id                varchar(255),
    organization_account_ms_id varchar(255),
    agent_account_ms_id        varchar(255),
    reward_type                varchar(255),
    reward_percent             numeric(15, 5),
    printed                    boolean default false not null,
    published                  boolean default false not null,
    attributes                 json,
    rate                       json,
    files                      json,
    created_at                 timestamp(0),
    updated_at                 timestamp(0),
    constraint ms_contracts_user_id_ms_id_unique
        unique (user_id, ms_id)
);
alter table public.ms_contracts
    owner to admin;
create index ms_contracts_ms_id_index
    on public.ms_contracts (ms_id);
create table public.moysklad_apps
(
    id                bigserial
        primary key,
    app_id            varchar(255)                                      not null,
    account_id        varchar(255)                                      not null,
    app_uid           varchar(255)                                      not null,
    account_name      varchar(255)                                      not null,
    status            varchar(255) default 'Unknown'::character varying not null,
    cause             varchar(255),
    access_token      text,
    settings          json,
    subscription_data json,
    user_id           bigint,
    created_at        timestamp(0),
    updated_at        timestamp(0),
    tariff_id         varchar(255),
    service_provider  varchar(32),
    constraint unique_app_account
        unique (app_id, account_id)
);
comment on column public.moysklad_apps.app_id is 'MoySklad App ID';
comment on column public.moysklad_apps.account_id is 'MoySklad Account ID';
comment on column public.moysklad_apps.app_uid is 'MoySklad App UID';
comment on column public.moysklad_apps.account_name is 'MoySklad Account Name';
comment on column public.moysklad_apps.status is 'App status';
comment on column public.moysklad_apps.cause is 'Activation/deactivation cause';
comment on column public.moysklad_apps.access_token is 'Access token for MoySklad JSON API';
comment on column public.moysklad_apps.settings is 'App settings configured by user';
comment on column public.moysklad_apps.subscription_data is 'Subscription information';
comment on column public.moysklad_apps.user_id is 'Associated user ID';
comment on column public.moysklad_apps.tariff_id is 'MoySklad Tariff ID';
comment on column public.moysklad_apps.service_provider is 'iframe = приложение МойСклад, go_saas = наш сайт (Go)';
alter table public.moysklad_apps
    owner to admin;
create index moysklad_apps_status_index
    on public.moysklad_apps (status);
create index moysklad_apps_user_id_index
    on public.moysklad_apps (user_id);
create index moysklad_apps_created_at_index
    on public.moysklad_apps (created_at);
create index moysklad_apps_service_provider_index
    on public.moysklad_apps (service_provider);
create table public.ms_products
(
    id                bigserial
        primary key,
    user_id           bigint                                         not null
        constraint ms_products_user_id_foreign
            references public.users
            on delete cascade,
    ms_id             varchar(255)                                   not null,
    name              varchar(255)                                   not null,
    description       text,
    article           varchar(255),
    code              varchar(255),
    external_code     varchar(255),
    product_type      varchar(255)                                   not null,
    parent_product_id varchar(255),
    archived          boolean          default false                 not null,
    shared            boolean          default false                 not null,
    weight            double precision,
    volume            double precision,
    uom_id            varchar(255),
    uom_name          varchar(255),
    vat               double precision,
    vat_enabled       boolean          default false                 not null,
    min_price         double precision,
    purchase_price    double precision,
    sale_price        double precision,
    stock             double precision default '0'::double precision not null,
    reserve           double precision default '0'::double precision not null,
    in_transit        double precision default '0'::double precision not null,
    quantity          double precision default '0'::double precision not null,
    attributes        json,
    images            json,
    barcodes          json,
    characteristics   json,
    created_at        timestamp(0),
    updated_at        timestamp(0),
    last_sync_at      timestamp(0),
    sale_prices       json,
    constraint ms_products_user_id_ms_id_unique
        unique (user_id, ms_id)
);
comment on column public.ms_products.last_sync_at is 'Время последней синхронизации товара с МойСклад';
comment on column public.ms_products.sale_prices is 'Все уровни цен из МойСклад (массив с priceType.id, priceType.name, value)';
alter table public.ms_products
    owner to admin;
create index ms_products_ms_id_index
    on public.ms_products (ms_id);
create index idx_ms_products_user_archived_name
    on public.ms_products (user_id, archived, name);
create index idx_ms_products_user_name
    on public.ms_products (user_id, name);
create index idx_ms_products_user_article
    on public.ms_products (user_id, article);
create index idx_ms_products_user_code
    on public.ms_products (user_id, code);
create index idx_ms_products_fulltext_search
    on public.ms_products using gin (to_tsvector('russian'::regconfig,
                                                 (((COALESCE(name, ''::character varying)::text || ' '::text) ||
                                                   COALESCE(article, ''::character varying)::text) || ' '::text) ||
                                                 COALESCE(code, ''::character varying)::text));
create index idx_ms_products_user_last_sync
    on public.ms_products (user_id, last_sync_at);
create table public.ms_product_stocks
(
    id              bigserial
        primary key,
    ms_product_id   bigint                                         not null
        constraint ms_product_stocks_ms_product_id_foreign
            references public.ms_products
            on delete cascade,
    ms_warehouse_id bigint                                         not null
        constraint ms_product_stocks_ms_warehouse_id_foreign
            references public.ms_warehouses
            on delete cascade,
    stock           double precision default '0'::double precision not null,
    reserve         double precision default '0'::double precision not null,
    in_transit      double precision default '0'::double precision not null,
    quantity        double precision default '0'::double precision not null,
    created_at      timestamp(0),
    updated_at      timestamp(0),
    constraint ms_product_stocks_ms_product_id_ms_warehouse_id_unique
        unique (ms_product_id, ms_warehouse_id)
);
alter table public.ms_product_stocks
    owner to admin;
create table public.ms_product_components
(
    id              bigserial
        primary key,
    ms_product_id   bigint                                         not null
        constraint ms_product_components_ms_product_id_foreign
            references public.ms_products
            on delete cascade,
    component_ms_id varchar(255)                                   not null,
    quantity        double precision default '1'::double precision not null,
    created_at      timestamp(0),
    updated_at      timestamp(0),
    constraint ms_product_components_ms_product_id_component_ms_id_unique
        unique (ms_product_id, component_ms_id)
);
alter table public.ms_product_components
    owner to admin;
create table public.ms_statuses
(
    id          bigserial
        primary key,
    user_id     bigint                not null
        constraint ms_statuses_user_id_foreign
            references public.users
            on delete cascade,
    ms_id       varchar(36)           not null,
    name        varchar(255)          not null,
    entity_type varchar(255)          not null,
    state_type  varchar(255),
    color       integer,
    is_default  boolean default false not null,
    created_at  timestamp(0),
    updated_at  timestamp(0),
    constraint ms_statuses_user_id_ms_id_unique
        unique (user_id, ms_id)
);
alter table public.ms_statuses
    owner to admin;
create index ms_statuses_ms_id_index
    on public.ms_statuses (ms_id);
create table public.shops
(
    id                                bigserial
        primary key,
    user_id                           bigint                                                     not null
        constraint shops_user_id_foreign
            references public.users
            on delete cascade,
    name                              varchar(255)                                               not null,
    marketplace                       varchar(255)                                               not null,
    type                              varchar(255)                                               not null,
    client_id                         varchar(255),
    campaign_id                       varchar(255),
    business_id                       varchar(255),
    api_key                           text                                                       not null,
    ms_organization_id                bigint
        constraint shops_ms_organization_id_foreign
            references public.ms_organizations
            on delete set null,
    ms_counterparty_id                bigint
        constraint shops_ms_counterparty_id_foreign
            references public.ms_counterparties
            on delete set null,
    ms_sales_channel_id               bigint
        constraint shops_ms_sales_channel_id_foreign
            references public.ms_sales_channels
            on delete set null,
    ms_warehouse_id                   bigint
        constraint shops_ms_warehouse_id_foreign
            references public.ms_warehouses
            on delete set null,
    ms_project_id                     bigint
        constraint shops_ms_project_id_foreign
            references public.ms_projects
            on delete set null,
    ms_contract_id                    bigint
        constraint shops_ms_contract_id_foreign
            references public.ms_contracts
            on delete set null,
    processes_new_orders              boolean      default false                                 not null,
    create_customer_orders            boolean      default false                                 not null,
    create_demands                    boolean      default false                                 not null,
    document_prices                   varchar(255),
    stock_sync_mode                   varchar(255) default 'single_warehouse'::character varying not null,
    warehouse_ids                     json,
    processes_returns                 boolean      default false                                 not null,
    ms_return_arrival_warehouse_id    bigint
        constraint shops_ms_return_arrival_warehouse_id_foreign
            references public.ms_warehouses
            on delete set null,
    ms_return_completion_warehouse_id bigint
        constraint shops_ms_return_completion_warehouse_id_foreign
            references public.ms_warehouses
            on delete set null,
    act_signing_frequency             varchar(255),
    is_active                         boolean      default true                                  not null,
    sort_order                        integer      default 0                                     not null,
    created_at                        timestamp(0),
    updated_at                        timestamp(0),
    sync_price                        boolean      default false                                 not null,
    sync_stock                        boolean      default false                                 not null,
    ozon_selected_warehouses          json,
    price_sync_type                   varchar(255) default 'shop'::character varying             not null
        constraint shops_price_sync_type_check
            check ((price_sync_type)::text = ANY
                   ((ARRAY ['shop'::character varying, 'cabinet'::character varying, 'both'::character varying])::text[])),
    customer_order_reserve            boolean      default false                                 not null,
    orders_from_warehouse_id          bigint,
    telegram_chat_id                  varchar(255),
    notification_settings             json,
    ms_price_level_id                 varchar(255),
    print_settings                    jsonb,
    wildberries_selected_warehouses   json,
    constraint unique_shop_identifier
        unique (user_id, marketplace, campaign_id)
);
comment on column public.shops.ozon_selected_warehouses is 'ID выбранных складов для работы с Ozon';
comment on column public.shops.ms_price_level_id is 'ID уровня цены из МойСклад по умолчанию для магазина';
comment on column public.shops.wildberries_selected_warehouses is 'ID выбранных складов WB для синхронизации остатков';
alter table public.shops
    owner to admin;
create index shops_marketplace_index
    on public.shops (marketplace);
create index shops_type_index
    on public.shops (type);
create table public.marketplace_returns
(
    id                     bigserial
        primary key,
    shop_id                bigint       not null
        constraint marketplace_returns_shop_id_foreign
            references public.shops
            on delete cascade,
    external_id            varchar(255) not null,
    order_external_id      varchar(255),
    order_id               bigint,
    shipment_status        varchar(255) not null,
    refund_status          varchar(255),
    return_type            varchar(255),
    refund_amount          numeric(15, 4),
    created_at_marketplace timestamp(0),
    updated_at_marketplace timestamp(0),
    raw                    json         not null,
    created_at             timestamp(0),
    updated_at             timestamp(0),
    ms_return_id           varchar(255),
    constraint unique_marketplace_return
        unique (shop_id, external_id)
);
alter table public.marketplace_returns
    owner to admin;
create index marketplace_returns_external_id_index
    on public.marketplace_returns (external_id);
create index marketplace_returns_order_external_id_index
    on public.marketplace_returns (order_external_id);
create index marketplace_returns_order_id_index
    on public.marketplace_returns (order_id);
create index marketplace_returns_shipment_status_index
    on public.marketplace_returns (shipment_status);
create index marketplace_returns_refund_status_index
    on public.marketplace_returns (refund_status);
create table public.master_products
(
    id              bigserial
        primary key,
    user_id         bigint       not null
        constraint master_products_user_id_foreign
            references public.users
            on delete cascade,
    master_offer_id varchar(255) not null,
    name            varchar(255),
    image_url       varchar(255),
    created_at      timestamp(0),
    updated_at      timestamp(0),
    constraint master_products_user_id_master_offer_id_unique
        unique (user_id, master_offer_id)
);
alter table public.master_products
    owner to admin;
create table public.marketplace_products
(
    id                      bigserial
        primary key,
    shop_id                 bigint                              not null
        constraint marketplace_products_shop_id_foreign
            references public.shops
            on delete cascade,
    marketplace_type        varchar(255)                        not null,
    offer_id                varchar(255)                        not null,
    name                    varchar(255)                        not null,
    ms_product_id           bigint
        constraint marketplace_products_ms_product_id_foreign
            references public.ms_products
            on delete set null,
    price                   numeric(10, 2) default '0'::numeric not null,
    image                   text,
    is_discounted           boolean        default false        not null,
    is_ucenka               boolean        default false        not null,
    user_formula            varchar(255),
    calculated_price        numeric(10, 2),
    remove_from_actions     boolean        default false        not null,
    stock                   integer        default 0            not null,
    data                    json,
    created_at              timestamp(0),
    updated_at              timestamp(0),
    master_product_id       bigint
        constraint marketplace_products_master_product_id_foreign
            references public.master_products
            on delete set null,
    sync_stocks             boolean        default false        not null,
    sync_prices             boolean        default false        not null,
    exclude_from_promotions boolean        default false        not null,
    discount                numeric(8, 2),
    min_price               double precision,
    competitor_links        json,
    competitor_price        double precision,
    sku                     varchar(255),
    search_vector           tsvector,
    ms_price_level_id       varchar(255),
    constraint marketplace_products_shop_id_marketplace_type_offer_id_unique
        unique (shop_id, marketplace_type, offer_id)
);
comment on column public.marketplace_products.data is 'Дополнительные данные о товаре из маркетплейса';
comment on column public.marketplace_products.competitor_links is 'Links to competitor products';
comment on column public.marketplace_products.competitor_price is 'Competitor price';
comment on column public.marketplace_products.ms_price_level_id is 'ID уровня цены из МойСклад для конкретного SKU (если null, используется уровень из shops)';
alter table public.marketplace_products
    owner to admin;
create index idx_shop_offer
    on public.marketplace_products (shop_id, offer_id);
create index idx_shop_name
    on public.marketplace_products (shop_id, name);
create index idx_shop_sku
    on public.marketplace_products (shop_id, sku);
create index idx_shop_offer_id
    on public.marketplace_products (shop_id, offer_id, id);
create index idx_marketplace_products_name_gin
    on public.marketplace_products using gin (to_tsvector('simple'::regconfig, name::text));
create index idx_marketplace_products_shop_id
    on public.marketplace_products (shop_id);
create index idx_marketplace_products_offer_sku
    on public.marketplace_products (offer_id, sku);
create index idx_shop_ms_product
    on public.marketplace_products (shop_id, ms_product_id);
create index idx_marketplace_products_shop_ms_product
    on public.marketplace_products (shop_id, ms_product_id);
create index marketplace_products_search_vector_idx
    on public.marketplace_products using gin (search_vector);
create trigger marketplace_products_search_vector_update
    before insert or update
    on public.marketplace_products
    for each row
execute procedure public.marketplace_products_search_vector_trigger();
create index master_products_master_offer_id_index
    on public.master_products (master_offer_id);
create table public.competitor_links
(
    id                     bigserial
        primary key,
    marketplace_product_id bigint            not null
        constraint competitor_links_marketplace_product_id_foreign
            references public.marketplace_products
            on delete cascade,
    url                    varchar(2000)     not null,
    marketplace            varchar(255)      not null,
    price                  numeric(10, 2),
    price_updated_at       timestamp(0),
    error_message          text,
    "order"                integer default 0 not null,
    created_at             timestamp(0),
    updated_at             timestamp(0)
);
comment on column public.competitor_links.marketplace is 'Название маркетплейса (yandex, wildberries, ozon, etc.)';
comment on column public.competitor_links.price is 'Последняя найденная цена';
comment on column public.competitor_links.price_updated_at is 'Время последнего обновления цены';
comment on column public.competitor_links.error_message is 'Последняя ошибка при получении цены';
comment on column public.competitor_links."order" is 'Порядок отображения';
alter table public.competitor_links
    owner to admin;
create index competitor_links_marketplace_product_id_order_index
    on public.competitor_links (marketplace_product_id, "order");
create table public.marketplace_orders
(
    id                   bigserial
        primary key,
    order_id             varchar(255)   not null,
    external_id          varchar(255)   not null,
    status               varchar(255)   not null,
    substatus            varchar(255),
    address              json           not null,
    customer             json           not null,
    creation_date        timestamp(0)   not null,
    shipment_date        timestamp(0),
    customer_price       numeric(10, 2) not null,
    payout               numeric(10, 2) not null,
    commission           numeric(10, 2) not null,
    subsidies            json           not null,
    ms_order_id          varchar(255),
    ms_demand_id         varchar(255),
    return_id            bigint
        constraint marketplace_orders_return_id_foreign
            references public.marketplace_returns
            on delete set null,
    shop_id              bigint         not null
        constraint marketplace_orders_shop_id_foreign
            references public.shops
            on delete cascade,
    created_at           timestamp(0),
    updated_at           timestamp(0),
    delivery_date        timestamp(0),
    items                json,
    missing_ms_item      boolean default false,
    has_archive_items    boolean default false,
    barcode_path         varchar(255),
    barcode_obtained_at  timestamp(0),
    telegram_notified_at timestamp(0),
    constraint marketplace_orders_shop_id_order_id_unique
        unique (shop_id, order_id)
);
comment on column public.marketplace_orders.missing_ms_item is 'Есть ли товары, отсутствующие в МойСклад';
comment on column public.marketplace_orders.has_archive_items is 'Есть ли архивные товары в заказе';
alter table public.marketplace_orders
    owner to admin;
create index marketplace_orders_external_id_index
    on public.marketplace_orders (external_id);
create index marketplace_orders_status_index
    on public.marketplace_orders (status);
create index marketplace_orders_ms_order_id_index
    on public.marketplace_orders (ms_order_id);
create index marketplace_orders_ms_demand_id_index
    on public.marketplace_orders (ms_demand_id);
create index marketplace_orders_creation_date_index
    on public.marketplace_orders (creation_date);
create index idx_orders_shop_creation
    on public.marketplace_orders (shop_id, creation_date);
create index idx_orders_shop_status
    on public.marketplace_orders (shop_id, status);
create index idx_orders_shop_id
    on public.marketplace_orders (shop_id, id);
create index idx_orders_search
    on public.marketplace_orders (order_id, external_id);
create index idx_orders_shop_archive_items
    on public.marketplace_orders (shop_id, has_archive_items);
create index marketplace_orders_barcode_path_index
    on public.marketplace_orders (barcode_path);
create table public.ozon_warehouses
(
    id                       bigserial
        primary key,
    shop_id                  bigint                not null
        constraint ozon_warehouses_shop_id_foreign
            references public.shops
            on delete cascade,
    warehouse_id             bigint                not null,
    name                     varchar(255)          not null,
    has_entrusted_acceptance boolean default false not null,
    is_rfbs                  boolean default false not null,
    can_print_act_in_advance boolean default false not null,
    has_postings_limit       boolean default false not null,
    is_karantin              boolean default false not null,
    is_kgt                   boolean default false not null,
    is_economy               boolean default false not null,
    is_timetable_editable    boolean default false not null,
    min_postings_limit       integer,
    postings_limit           integer,
    min_working_days         integer,
    status                   varchar(255)          not null,
    working_days             json,
    first_mile_type          json,
    created_at               timestamp(0),
    updated_at               timestamp(0),
    constraint ozon_warehouses_shop_id_warehouse_id_unique
        unique (shop_id, warehouse_id)
);
comment on column public.ozon_warehouses.warehouse_id is 'ID склада в Ozon';
comment on column public.ozon_warehouses.name is 'Название склада';
comment on column public.ozon_warehouses.status is 'Статус склада';
comment on column public.ozon_warehouses.working_days is 'Рабочие дни склада';
comment on column public.ozon_warehouses.first_mile_type is 'Тип первой мили';
alter table public.ozon_warehouses
    owner to admin;
create table public.order_history
(
    id          bigserial
        primary key,
    order_id    bigint       not null
        constraint order_history_order_id_foreign
            references public.marketplace_orders
            on delete cascade,
    event_type  varchar(255) not null,
    title       varchar(255) not null,
    description text,
    old_data    json,
    new_data    json,
    metadata    json,
    occurred_at timestamp(0) not null,
    created_at  timestamp(0),
    updated_at  timestamp(0)
);
alter table public.order_history
    owner to admin;
create index order_history_order_id_occurred_at_index
    on public.order_history (order_id, occurred_at);
create table public.task_events
(
    id                    bigserial
        primary key,
    user_id               bigint                                            not null
        constraint task_events_user_id_foreign
            references public.users
            on delete cascade,
    title                 varchar(255)                                      not null,
    description           text,
    status                varchar(255) default 'pending'::character varying not null
        constraint task_events_status_check
            check ((status)::text = ANY
                   ((ARRAY ['pending'::character varying, 'running'::character varying, 'success'::character varying, 'error'::character varying])::text[])),
    entity_type           varchar(255),
    entity_id             bigint,
    entity_name           varchar(255),
    show_in_notifications boolean      default false                        not null,
    started_at            timestamp(0),
    completed_at          timestamp(0),
    duration              integer,
    metadata              json,
    error_message         text,
    created_at            timestamp(0),
    updated_at            timestamp(0)
);
alter table public.task_events
    owner to admin;
create index task_events_user_id_status_index
    on public.task_events (user_id, status);
create index task_events_user_id_show_in_notifications_index
    on public.task_events (user_id, show_in_notifications);
create index task_events_entity_type_entity_id_index
    on public.task_events (entity_type, entity_id);
create index task_events_created_at_index
    on public.task_events (created_at);
create table public.wildberries_warehouses
(
    id            bigserial
        primary key,
    shop_id       bigint                not null
        constraint wildberries_warehouses_shop_id_foreign
            references public.shops
            on delete cascade,
    warehouse_id  bigint                not null,
    office_id     bigint,
    name          varchar(255)          not null,
    cargo_type    smallint,
    delivery_type smallint,
    is_processing boolean default false not null,
    is_deleting   boolean default false not null,
    status        varchar(255),
    raw_data      json,
    created_at    timestamp(0),
    updated_at    timestamp(0),
    constraint wildberries_warehouses_shop_id_warehouse_id_unique
        unique (shop_id, warehouse_id)
);
alter table public.wildberries_warehouses
    owner to admin;
create table public.wildberries_price_tasks
(
    id              bigserial
        primary key,
    shop_id         bigint                         not null
        constraint wildberries_price_tasks_shop_id_foreign
            references public.shops
            on delete cascade,
    task_id         varchar(255),
    status          smallint default '0'::smallint not null,
    payload_count   integer  default 0             not null,
    payload         json,
    status_payload  json,
    errors          json,
    already_exists  boolean  default false         not null,
    processed_at    timestamp(0),
    last_checked_at timestamp(0),
    created_at      timestamp(0),
    updated_at      timestamp(0)
);
alter table public.wildberries_price_tasks
    owner to admin;
create index wildberries_price_tasks_shop_id_status_index
    on public.wildberries_price_tasks (shop_id, status);
create index wildberries_price_tasks_task_id_index
    on public.wildberries_price_tasks (task_id);
create table public.chat_messages
(
    id          bigserial
        primary key,
    user_id     bigint       not null
        constraint chat_messages_user_id_foreign
            references public.users
            on delete cascade,
    sender_id   bigint       not null
        constraint chat_messages_sender_id_foreign
            references public.users
            on delete cascade,
    sender_role varchar(255) not null
        constraint chat_messages_sender_role_check
            check ((sender_role)::text = ANY ((ARRAY ['admin'::character varying, 'user'::character varying])::text[])),
    body        text         not null,
    read_at     timestamp(0),
    created_at  timestamp(0),
    updated_at  timestamp(0)
);
alter table public.chat_messages
    owner to admin;
create table public.goose_db_version
(
    id         integer generated by default as identity
        primary key,
    version_id bigint                  not null,
    is_applied boolean                 not null,
    tstamp     timestamp default now() not null
);
alter table public.goose_db_version
    owner to admin;
create table public.billing_subscriptions
(
    user_id                          bigint                                                      not null
        primary key
        references public.users
            on delete cascade,
    billing_status                   varchar(32)              default 'trial'::character varying not null,
    current_tariff_id                varchar(64)              default ''::character varying      not null,
    period_start                     timestamp with time zone,
    period_end                       timestamp with time zone,
    grace_until                      timestamp with time zone,
    last_payment_id                  bigint,
    created_at                       timestamp with time zone default now()                      not null,
    updated_at                       timestamp with time zone default now()                      not null,
    auto_renew                       boolean                  default false                      not null,
    tochka_consumer_id               text,
    tochka_subscription_operation_id text,
    renewal_reminder_sent_at         timestamp with time zone
);
comment on column public.billing_subscriptions.auto_renew is 'When true and Tochka recurring is configured, scheduler attempts charge before period_end';
comment on column public.billing_subscriptions.tochka_consumer_id is 'Tochka consumerId after successful card payment (saveCard)';
comment on column public.billing_subscriptions.tochka_subscription_operation_id is 'Tochka acquiring subscription operation id for Charge Subscription API';
alter table public.billing_subscriptions
    owner to admin;
create table public.billing_payments
(
    id                         bigserial
        primary key,
    user_id                    bigint                                                             not null
        references public.users
            on delete cascade,
    inv_id                     bigint                                                             not null
        unique,
    status                     varchar(32)              default 'pending'::character varying      not null,
    amount_kopecks             bigint                                                             not null,
    currency                   varchar(8)               default 'RUB'::character varying          not null,
    tariff_id                  varchar(64)                                                        not null,
    period_months              integer                  default 1                                 not null,
    provider                   varchar(32)              default 'robokassa'::character varying    not null,
    shp_payload                jsonb,
    expires_at                 timestamp with time zone                                           not null,
    provider_fee_kopecks       bigint,
    provider_payment_method    text,
    provider_inc_curr_label    text,
    provider_email             text,
    callback_payload           jsonb,
    callback_received_at       timestamp with time zone,
    paid_at                    timestamp with time zone,
    created_at                 timestamp with time zone default now()                             not null,
    updated_at                 timestamp with time zone default now()                             not null,
    provider_order_id          text,
    provider_subscription_id   text,
    provider_profile_id        text,
    provider_attempt           integer,
    payment_status             text,
    payment_status_description text,
    failed_at                  timestamp with time zone,
    payment_kind               varchar(32)              default 'subscription'::character varying not null
);
alter table public.billing_payments
    owner to admin;
create index billing_payments_user_created_idx
    on public.billing_payments (user_id asc, created_at desc);
create index billing_payments_provider_order_idx
    on public.billing_payments (provider, provider_order_id);
create index billing_payments_provider_subscription_idx
    on public.billing_payments (provider, provider_subscription_id);
create table public.admin_remote_audit_logs
(
    id             bigserial
        primary key,
    actor_user_id  bigint                                       not null
        references public.users
            on delete cascade,
    actor_email    text                                         not null,
    action         text                                         not null,
    target_user_id bigint,
    success        boolean                  default false       not null,
    ip_address     text                     default ''::text    not null,
    user_agent     text                     default ''::text    not null,
    metadata       jsonb                    default '{}'::jsonb not null,
    created_at     timestamp with time zone default now()       not null
);
alter table public.admin_remote_audit_logs
    owner to admin;
create index idx_admin_remote_audit_logs_created_at
    on public.admin_remote_audit_logs (created_at desc);
create index idx_admin_remote_audit_logs_actor_user_id
    on public.admin_remote_audit_logs (actor_user_id asc, created_at desc);
create index idx_admin_remote_audit_logs_target_user_id
    on public.admin_remote_audit_logs (target_user_id asc, created_at desc);
create table public.tariff_plans
(
    id                 bigserial
        primary key,
    slug               text                                            not null
        unique,
    name               text                                            not null,
    external_tariff_id uuid
        unique,
    price_monthly      numeric(10, 2) default 0                        not null,
    currency           varchar(8)     default 'RUB'::character varying not null,
    is_active          boolean        default true                     not null,
    sort_order         integer        default 0                        not null,
    settings           jsonb          default '{}'::jsonb              not null,
    created_at         timestamp      default now()                    not null,
    updated_at         timestamp      default now()                    not null
);
alter table public.tariff_plans
    owner to admin;
create table public.user_tariff_overrides
(
    id                 bigserial
        primary key,
    user_id            bigint                        not null
        unique
        references public.users
            on delete cascade,
    discount_type      text,
    discount_value     numeric(10, 2),
    discount_starts_at timestamp,
    discount_ends_at   timestamp,
    capabilities       jsonb     default '{}'::jsonb not null,
    note               text,
    created_at         timestamp default now()       not null,
    updated_at         timestamp default now()       not null
);
alter table public.user_tariff_overrides
    owner to admin;
create table public.billing_addons
(
    id              bigserial
        primary key,
    user_id         bigint                                                       not null
        references public.users
            on delete cascade,
    addon_key       varchar(128)                                                 not null,
    status          varchar(32)              default 'active'::character varying not null,
    period_start    timestamp with time zone,
    period_end      timestamp with time zone,
    last_payment_id bigint
                                                                                 references public.billing_payments
                                                                                     on delete set null,
    created_at      timestamp with time zone default now()                       not null,
    updated_at      timestamp with time zone default now()                       not null,
    constraint billing_addons_user_addon_key
        unique (user_id, addon_key)
);
alter table public.billing_addons
    owner to admin;
create index billing_addons_user_status_idx
    on public.billing_addons (user_id, status);
create table public.billing_renewal_attempts
(
    id                bigserial
        primary key,
    user_id           bigint                                 not null
        references public.users
            on delete cascade,
    attempt_kind      varchar(32)                            not null,
    status            varchar(32)                            not null,
    provider_response jsonb,
    created_at        timestamp with time zone default now() not null
);
alter table public.billing_renewal_attempts
    owner to admin;
create index billing_renewal_attempts_user_created_idx
    on public.billing_renewal_attempts (user_id asc, created_at desc);
create table public.go_marketplace_api_monitor_notified
(
    id               bigserial
        primary key,
    channel_username varchar(128)                           not null,
    post_key         varchar(191)                           not null,
    created_at       timestamp with time zone default now() not null,
    constraint go_marketplace_api_monitor_notifi_channel_username_post_key_key
        unique (channel_username, post_key)
);
alter table public.go_marketplace_api_monitor_notified
    owner to admin;