-- ============================================================
-- Order-to-Cash Relational Schema + Graph Projection Tables
-- ============================================================

-- Business Partners / Customers
CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    name TEXT,
    country TEXT,
    city TEXT,
    region TEXT,
    raw_json TEXT
);

CREATE TABLE IF NOT EXISTS addresses (
    address_id TEXT PRIMARY KEY,
    customer_id TEXT,
    street TEXT,
    city TEXT,
    postal_code TEXT,
    country TEXT,
    raw_json TEXT
);

CREATE TABLE IF NOT EXISTS plants (
    plant_id TEXT PRIMARY KEY,
    name TEXT,
    country TEXT,
    city TEXT,
    raw_json TEXT
);

CREATE TABLE IF NOT EXISTS products (
    product_id TEXT PRIMARY KEY,
    description TEXT,
    product_group TEXT,
    base_unit TEXT,
    raw_json TEXT
);

-- Sales Orders
CREATE TABLE IF NOT EXISTS sales_orders (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT,
    order_date TEXT,
    net_value REAL,
    currency TEXT,
    status TEXT,
    sales_org TEXT,
    raw_json TEXT
);

CREATE TABLE IF NOT EXISTS sales_order_items (
    item_id TEXT PRIMARY KEY,
    order_id TEXT,
    product_id TEXT,
    quantity REAL,
    net_value REAL,
    currency TEXT,
    raw_json TEXT
);

CREATE TABLE IF NOT EXISTS schedule_lines (
    id TEXT PRIMARY KEY,
    order_id TEXT,
    item_id TEXT,
    confirmed_qty REAL,
    delivery_date TEXT,
    raw_json TEXT
);

-- Deliveries
CREATE TABLE IF NOT EXISTS deliveries (
    delivery_id TEXT PRIMARY KEY,
    order_id TEXT,
    plant_id TEXT,
    delivery_date TEXT,
    actual_goods_movement_date TEXT,
    status TEXT,
    raw_json TEXT
);

CREATE TABLE IF NOT EXISTS delivery_items (
    item_id TEXT PRIMARY KEY,
    delivery_id TEXT,
    product_id TEXT,
    order_id TEXT,
    quantity REAL,
    raw_json TEXT
);

-- Billing Documents
CREATE TABLE IF NOT EXISTS billing_documents (
    billing_id TEXT PRIMARY KEY,
    order_id TEXT,
    delivery_id TEXT,
    customer_id TEXT,
    billing_date TEXT,
    net_value REAL,
    currency TEXT,
    status TEXT,
    cancelled INTEGER DEFAULT 0,
    raw_json TEXT
);

CREATE TABLE IF NOT EXISTS billing_items (
    item_id TEXT PRIMARY KEY,
    billing_id TEXT,
    product_id TEXT,
    quantity REAL,
    net_value REAL,
    currency TEXT,
    raw_json TEXT
);

CREATE TABLE IF NOT EXISTS billing_cancellations (
    cancellation_id TEXT PRIMARY KEY,
    original_billing_id TEXT,
    cancel_date TEXT,
    reason TEXT,
    raw_json TEXT
);

-- Journal Entries
CREATE TABLE IF NOT EXISTS journal_entries (
    entry_id TEXT PRIMARY KEY,
    billing_id TEXT,
    customer_id TEXT,
    posting_date TEXT,
    amount REAL,
    currency TEXT,
    account TEXT,
    raw_json TEXT
);

-- Payments
CREATE TABLE IF NOT EXISTS payments (
    payment_id TEXT PRIMARY KEY,
    customer_id TEXT,
    billing_id TEXT,
    journal_entry_id TEXT,
    payment_date TEXT,
    amount REAL,
    currency TEXT,
    raw_json TEXT
);

-- ============================================================
-- Graph Projection Tables
-- ============================================================

CREATE TABLE IF NOT EXISTS graph_nodes (
    node_id TEXT PRIMARY KEY,
    node_type TEXT NOT NULL,
    label TEXT,
    entity_key TEXT,
    metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS graph_edges (
    edge_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    edge_type TEXT NOT NULL,
    metadata_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_graph_edges_source ON graph_edges(source_id);
CREATE INDEX IF NOT EXISTS idx_graph_edges_target ON graph_edges(target_id);
CREATE INDEX IF NOT EXISTS idx_graph_nodes_type ON graph_nodes(node_type);
CREATE INDEX IF NOT EXISTS idx_billing_order ON billing_documents(order_id);
CREATE INDEX IF NOT EXISTS idx_billing_delivery ON billing_documents(delivery_id);
CREATE INDEX IF NOT EXISTS idx_je_billing ON journal_entries(billing_id);
CREATE INDEX IF NOT EXISTS idx_pay_billing ON payments(billing_id)
