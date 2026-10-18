"""
CartCompass-BI - Data Cleaning & Validation Pipeline
Cleans raw CSV datasets, validates data integrity, enforces business constraints,
and exports clean datasets to data/processed/.
"""

import os
from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"


def load_raw_data():
    """Load products, orders, and order_items CSV files from data/raw/."""
    products_path = RAW_DIR / "products.csv"
    orders_path = RAW_DIR / "orders.csv"
    items_path = RAW_DIR / "order_items.csv"

    if not (products_path.exists() and orders_path.exists() and items_path.exists()):
        raise FileNotFoundError(
            f"Raw data files missing in {RAW_DIR}. Run database/init_db.py first."
        )

    products_df = pd.read_csv(products_path)
    orders_df = pd.read_csv(orders_path)
    items_df = pd.read_csv(items_path)

    return products_df, orders_df, items_df


def clean_and_validate(products_df, orders_df, items_df):
    """
    Perform comprehensive data cleaning, validation, and integrity checks:
    - Deduplicate primary keys
    - Validate date format (YYYY-MM-DD)
    - Validate order statuses
    - Enforce non-negative numerical fields (quantity, unit_price, discount, return_amount)
    - Ensure return_amount does not exceed net price before refund
    - Verify referential integrity between tables
    """
    validation_report = {
        "products_initial": len(products_df),
        "orders_initial": len(orders_df),
        "items_initial": len(items_df),
        "issues_fixed": []
    }

    # 1. Clean Products
    products_clean = products_df.drop_duplicates(subset=["product_id"]).copy()
    products_clean["product_id"] = products_clean["product_id"].astype(int)
    products_clean["product_name"] = products_clean["product_name"].astype(str).str.strip()
    products_clean["category"] = products_clean["category"].astype(str).str.strip()

    # 2. Clean Orders
    orders_clean = orders_df.drop_duplicates(subset=["order_id"]).copy()
    orders_clean["order_id"] = orders_clean["order_id"].astype(int)
    orders_clean["order_date"] = pd.to_datetime(orders_clean["order_date"], errors="coerce")
    
    # Drop records with invalid dates
    invalid_dates = orders_clean["order_date"].isna().sum()
    if invalid_dates > 0:
        validation_report["issues_fixed"].append(f"Dropped {invalid_dates} orders with invalid dates.")
        orders_clean = orders_clean.dropna(subset=["order_date"])

    orders_clean["order_date"] = orders_clean["order_date"].dt.strftime("%Y-%m-%d")
    orders_clean["order_status"] = orders_clean["order_status"].astype(str).str.strip().str.lower()
    orders_clean["region"] = orders_clean["region"].astype(str).str.strip()

    valid_statuses = {"delivered", "shipped", "pending", "cancelled"}
    invalid_status_mask = ~orders_clean["order_status"].isin(valid_statuses)
    if invalid_status_mask.sum() > 0:
        validation_report["issues_fixed"].append(
            f"Filtered {invalid_status_mask.sum()} orders with invalid status."
        )
        orders_clean = orders_clean[~invalid_status_mask]

    # 3. Clean Order Items
    items_clean = items_df.drop_duplicates(subset=["item_id"]).copy()
    items_clean["item_id"] = items_clean["item_id"].astype(int)
    items_clean["order_id"] = items_clean["order_id"].astype(int)
    items_clean["product_id"] = items_clean["product_id"].astype(int)

    # Validate referential integrity
    valid_order_ids = set(orders_clean["order_id"])
    valid_product_ids = set(products_clean["product_id"])

    orphan_items_mask = (
        ~items_clean["order_id"].isin(valid_order_ids) |
        ~items_clean["product_id"].isin(valid_product_ids)
    )
    if orphan_items_mask.sum() > 0:
        validation_report["issues_fixed"].append(
            f"Removed {orphan_items_mask.sum()} orphan order items."
        )
        items_clean = items_clean[~orphan_items_mask]

    # Enforce non-negative numeric constraints
    items_clean["quantity"] = items_clean["quantity"].astype(int).clip(lower=1)
    items_clean["unit_price"] = items_clean["unit_price"].astype(float).clip(lower=0.0)
    items_clean["discount"] = items_clean["discount"].astype(float).clip(lower=0.0)
    items_clean["return_amount"] = items_clean["return_amount"].astype(float).clip(lower=0.0)

    # Business rule: discount cannot exceed gross price (quantity * unit_price)
    gross_per_item = items_clean["quantity"] * items_clean["unit_price"]
    discount_excess_mask = items_clean["discount"] > gross_per_item
    if discount_excess_mask.sum() > 0:
        validation_report["issues_fixed"].append(
            f"Capped {discount_excess_mask.sum()} discounts that exceeded gross amount."
        )
        items_clean.loc[discount_excess_mask, "discount"] = gross_per_item[discount_excess_mask]

    # Business rule: return_amount cannot exceed (gross - discount)
    net_before_return = gross_per_item - items_clean["discount"]
    return_excess_mask = items_clean["return_amount"] > net_before_return
    if return_excess_mask.sum() > 0:
        validation_report["issues_fixed"].append(
            f"Capped {return_excess_mask.sum()} return amounts exceeding net item value."
        )
        items_clean.loc[return_excess_mask, "return_amount"] = net_before_return[return_excess_mask]

    # Non-delivered orders must not have return amounts
    orders_status_map = dict(zip(orders_clean["order_id"], orders_clean["order_status"]))
    item_status_series = items_clean["order_id"].map(orders_status_map)
    non_delivered_returns = (item_status_series != "delivered") & (items_clean["return_amount"] > 0)
    if non_delivered_returns.sum() > 0:
        validation_report["issues_fixed"].append(
            f"Zeroed {non_delivered_returns.sum()} invalid return amounts on non-delivered orders."
        )
        items_clean.loc[non_delivered_returns, "return_amount"] = 0.0

    validation_report["products_clean"] = len(products_clean)
    validation_report["orders_clean"] = len(orders_clean)
    validation_report["items_clean"] = len(items_clean)

    return products_clean, orders_clean, items_clean, validation_report


def export_processed_data(products_clean, orders_clean, items_clean):
    """Save cleaned datasets into data/processed/."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    products_clean.to_csv(PROCESSED_DIR / "products_clean.csv", index=False)
    orders_clean.to_csv(PROCESSED_DIR / "orders_clean.csv", index=False)
    items_clean.to_csv(PROCESSED_DIR / "order_items_clean.csv", index=False)

    # Also build an integrated master analysis table
    master_df = items_clean.merge(orders_clean, on="order_id", how="inner")
    master_df = master_df.merge(products_clean, on="product_id", how="inner")

    master_df["gross_sales"] = master_df["quantity"] * master_df["unit_price"]
    master_df["net_sales"] = master_df["gross_sales"] - master_df["discount"] - master_df["return_amount"]
    master_df["year_month"] = pd.to_datetime(master_df["order_date"]).dt.strftime("%Y-%m")

    master_df.to_csv(PROCESSED_DIR / "ecommerce_master_clean.csv", index=False)
    print(f"Exported clean datasets to {PROCESSED_DIR}")
    return master_df


def run_pipeline():
    """Execute complete data cleaning and validation pipeline."""
    print("Loading raw datasets...")
    products, orders, items = load_raw_data()
    print("Running validation and business rule sanitization...")
    prod_c, ord_c, itm_c, report = clean_and_validate(products, orders, items)
    print("Validation Report:")
    print(f"  Products: {report['products_initial']} -> {report['products_clean']}")
    print(f"  Orders: {report['orders_initial']} -> {report['orders_clean']}")
    print(f"  Items: {report['items_initial']} -> {report['items_clean']}")
    if report["issues_fixed"]:
        for issue in report["issues_fixed"]:
            print(f"  * {issue}")
    else:
        print("  All records perfectly adhered to data integrity constraints.")

    master = export_processed_data(prod_c, ord_c, itm_c)
    return prod_c, ord_c, itm_c, master


if __name__ == "__main__":
    run_pipeline()
