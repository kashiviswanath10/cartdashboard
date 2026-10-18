"""
CartCompass-BI - Database Initialization & Sample Data Generator
Initializes SQLite database with schema and populates with realistic synthetic e-commerce data.
"""

import os
import sys
import csv
import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "cartcompass.db"
SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"
RAW_DATA_DIR = BASE_DIR / "data" / "raw"

# Fixed seed for reproducibility
RANDOM_SEED = 42

# Product Catalog Definition (28 products, 5 categories)
SAMPLE_PRODUCTS = [
    # Electronics
    (1, "Wireless Noise-Cancelling Headphones", "Electronics", 4999.00),
    (2, "Ultra HD 4K Smart TV 43\"", "Electronics", 24999.00),
    (3, "Mechanical Gaming Keyboard", "Electronics", 3499.00),
    (4, "Ergonomic Wireless Mouse", "Electronics", 1299.00),
    (5, "Fast Charging Power Bank 20000mAh", "Electronics", 1899.00),
    (6, "Portable Bluetooth Speaker", "Electronics", 2499.00),
    # Home & Kitchen
    (7, "Digital Air Fryer 4.5L", "Home & Kitchen", 5999.00),
    (8, "Stainless Steel Cookware Set (5-Piece)", "Home & Kitchen", 3799.00),
    (9, "Robotic Vacuum Cleaner", "Home & Kitchen", 18500.00),
    (10, "Electric Kettle 1.8L Stainless Steel", "Home & Kitchen", 1199.00),
    (11, "High-Speed Nutri-Blender 1000W", "Home & Kitchen", 4299.00),
    (12, "Orthopedic Memory Foam Pillow", "Home & Kitchen", 1499.00),
    # Fashion & Apparel
    (13, "Men's Stretch Slim Fit Chinos", "Fashion & Apparel", 1599.00),
    (14, "Women's Pure Cotton Printed Kurti", "Fashion & Apparel", 1299.00),
    (15, "Premium Washed Denim Jacket", "Fashion & Apparel", 2999.00),
    (16, "Lightweight Breathable Running Shoes", "Fashion & Apparel", 2799.00),
    (17, "Polarized Aviator Sunglasses", "Fashion & Apparel", 999.00),
    (18, "Genuine Full-Grain Leather Belt", "Fashion & Apparel", 799.00),
    # Beauty & Personal Care
    (19, "Vitamin C Brightening Face Serum 30ml", "Beauty & Personal Care", 699.00),
    (20, "Organic Moroccan Argan Oil Shampoo", "Beauty & Personal Care", 549.00),
    (21, "Sonic Electric Toothbrush Rechargeable", "Beauty & Personal Care", 1899.00),
    (22, "Oil-Free Hydrating Gel Moisturizer", "Beauty & Personal Care", 499.00),
    (23, "Complete Beard Care & Grooming Kit", "Beauty & Personal Care", 1199.00),
    # Sports & Fitness
    (24, "Anti-Skid Eco-Friendly Yoga Mat 6mm", "Sports & Fitness", 899.00),
    (25, "Adjustable Quick-Select Dumbbell Set 20kg", "Sports & Fitness", 4499.00),
    (26, "Insulated Stainless Steel Protein Shaker", "Sports & Fitness", 499.00),
    (27, "Heavy-Duty Resistance Loop Bands Set", "Sports & Fitness", 699.00),
    (28, "Waterproof Smart Fitness Tracker Band", "Sports & Fitness", 2199.00)
]

REGIONS = ["North", "South", "East", "West", "Central"]
STATUS_WEIGHTS = {
    "delivered": 0.72,
    "shipped": 0.12,
    "pending": 0.08,
    "cancelled": 0.08
}


def generate_synthetic_data(num_orders=750, seed=RANDOM_SEED):
    """
    Generate synthetic raw CSV files for products, orders, and order_items.
    Spans 14 months (January 2025 to February 2026) for rich monthly trends.
    """
    random.seed(seed)
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    products_file = RAW_DATA_DIR / "products.csv"
    orders_file = RAW_DATA_DIR / "orders.csv"
    order_items_file = RAW_DATA_DIR / "order_items.csv"

    # 1. Write products.csv
    with open(products_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["product_id", "product_name", "category"])
        for p in SAMPLE_PRODUCTS:
            writer.writerow([p[0], p[1], p[2]])

    product_price_map = {p[0]: p[3] for p in SAMPLE_PRODUCTS}
    product_ids = [p[0] for p in SAMPLE_PRODUCTS]

    # Date range: 2025-01-01 to 2026-02-28 (14 full months)
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2026, 2, 28)
    total_days = (end_date - start_date).days

    statuses = list(STATUS_WEIGHTS.keys())
    weights = list(STATUS_WEIGHTS.values())

    orders_data = []
    order_items_data = []
    item_id_counter = 1

    for order_id in range(1, num_orders + 1):
        # Generate random date with seasonal uptick towards Q4/holidays
        rand_day_offset = random.randint(0, total_days)
        order_dt = start_date + timedelta(days=rand_day_offset)
        order_date_str = order_dt.strftime("%Y-%m-%d")

        status = random.choices(statuses, weights=weights, k=1)[0]
        region = random.choice(REGIONS)
        orders_data.append((order_id, order_date_str, status, region))

        # Each order has 1 to 4 distinct items
        num_items = random.choices([1, 2, 3, 4], weights=[0.50, 0.30, 0.14, 0.06], k=1)[0]
        selected_products = random.sample(product_ids, k=num_items)

        for prod_id in selected_products:
            base_price = product_price_map[prod_id]
            quantity = random.choices([1, 2, 3, 4], weights=[0.65, 0.22, 0.09, 0.04], k=1)[0]
            unit_price = round(base_price, 2)
            gross_item = quantity * unit_price

            # Discount logic: 40% chance of a discount, between 5% and 15% of gross
            if random.random() < 0.40:
                discount_pct = random.uniform(0.05, 0.15)
                discount = round(gross_item * discount_pct, 2)
            else:
                discount = 0.0

            # Return logic: Only delivered orders can have returns (~6% chance)
            # Return amount represents refund on that item, never exceeding (gross - discount)
            if status == "delivered" and random.random() < 0.06:
                max_return = gross_item - discount
                # Either full item refund or partial refund
                return_pct = random.choice([0.5, 1.0])
                return_amount = round(max_return * return_pct, 2)
            else:
                return_amount = 0.0

            order_items_data.append((
                item_id_counter,
                order_id,
                prod_id,
                quantity,
                unit_price,
                discount,
                return_amount
            ))
            item_id_counter += 1

    # 2. Write orders.csv
    with open(orders_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["order_id", "order_date", "order_status", "region"])
        for ord_row in orders_data:
            writer.writerow(ord_row)

    # 3. Write order_items.csv
    with open(order_items_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["item_id", "order_id", "product_id", "quantity", "unit_price", "discount", "return_amount"])
        for itm_row in order_items_data:
            writer.writerow(itm_row)

    print(f"Generated synthetic CSV datasets in {RAW_DATA_DIR}:")
    print(f"  - Products: {len(SAMPLE_PRODUCTS)}")
    print(f"  - Orders: {len(orders_data)}")
    print(f"  - Order Items: {len(order_items_data)}")


def get_db_connection(db_path=DATABASE_PATH):
    """
    Establish SQLite connection with foreign keys enabled and row factory.
    """
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def init_database(db_path=DATABASE_PATH, force_regenerate=False):
    """
    Create SQLite tables using schema.sql and populate them from raw CSV files.
    """
    products_csv = RAW_DATA_DIR / "products.csv"
    orders_csv = RAW_DATA_DIR / "orders.csv"
    order_items_csv = RAW_DATA_DIR / "order_items.csv"

    if force_regenerate or not (products_csv.exists() and orders_csv.exists() and order_items_csv.exists()):
        print("Raw CSV files missing or regeneration requested. Generating synthetic data...")
        generate_synthetic_data()

    if os.path.exists(db_path):
        os.remove(db_path)

    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # Read and apply schema
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    cursor.executescript(schema_sql)

    # Load products.csv
    with open(products_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        products_records = [
            (int(row["product_id"]), row["product_name"], row["category"])
            for row in reader
        ]
    cursor.executemany(
        "INSERT INTO products (product_id, product_name, category) VALUES (?, ?, ?);",
        products_records
    )

    # Load orders.csv
    with open(orders_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        orders_records = [
            (int(row["order_id"]), row["order_date"], row["order_status"], row["region"])
            for row in reader
        ]
    cursor.executemany(
        "INSERT INTO orders (order_id, order_date, order_status, region) VALUES (?, ?, ?, ?);",
        orders_records
    )

    # Load order_items.csv
    with open(order_items_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        order_items_records = [
            (
                int(row["item_id"]),
                int(row["order_id"]),
                int(row["product_id"]),
                int(row["quantity"]),
                float(row["unit_price"]),
                float(row["discount"]),
                float(row["return_amount"])
            )
            for row in reader
        ]
    cursor.executemany(
        """
        INSERT INTO order_items (item_id, order_id, product_id, quantity, unit_price, discount, return_amount)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """,
        order_items_records
    )

    conn.commit()

    # Verify counts
    p_count = cursor.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    o_count = cursor.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    i_count = cursor.execute("SELECT COUNT(*) FROM order_items").fetchone()[0]

    conn.close()

    print(f"Database successfully initialized at {db_path}!")
    print(f"  - Products loaded: {p_count}")
    print(f"  - Orders loaded: {o_count}")
    print(f"  - Order Items loaded: {i_count}")
    return p_count, o_count, i_count


if __name__ == "__main__":
    force = "--generate-raw" in sys.argv or "--force" in sys.argv
    init_database(force_regenerate=force)
