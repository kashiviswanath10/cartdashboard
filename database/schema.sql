-- CartCompass-BI Database Schema
-- SQLite Database Definition with Foreign Keys & Performance Indexes

PRAGMA foreign_keys = ON;

-- 1. Products Table
CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL
);

-- 2. Orders Table
CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY,
    order_date TEXT NOT NULL, -- Stored in ISO format YYYY-MM-DD
    order_status TEXT NOT NULL, -- 'delivered', 'shipped', 'pending', 'cancelled'
    region TEXT NOT NULL -- e.g., 'North', 'South', 'East', 'West', 'Central'
);

-- 3. Order Items Table
CREATE TABLE IF NOT EXISTS order_items (
    item_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    unit_price REAL NOT NULL CHECK(unit_price >= 0),
    discount REAL NOT NULL DEFAULT 0 CHECK(discount >= 0),
    return_amount REAL NOT NULL DEFAULT 0 CHECK(return_amount >= 0),
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- Indexes for performance optimization on frequent filtering and joins
CREATE INDEX IF NOT EXISTS idx_orders_order_date ON orders(order_date);
CREATE INDEX IF NOT EXISTS idx_orders_order_status ON orders(order_status);
CREATE INDEX IF NOT EXISTS idx_orders_region ON orders(region);
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
