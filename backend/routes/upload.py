"""
CartCompass-BI - Data Ingestion & Dataset Upload Blueprint
Handles user-uploaded CSV / Excel datasets, validates and normalizes schemas,
repopulates SQLite database, executes data pipeline, and regenerates KPI summaries and charts.
"""

import io
import shutil
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
from flask import Blueprint, jsonify, request, send_file, current_app

from backend.db import get_db_connection
from database.init_db import init_database
from analysis.clean_data import run_pipeline
from analysis.calculate_kpis import run_kpi_analysis
from analysis.generate_charts import run_all_charts

upload_bp = Blueprint("upload", __name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SAMPLE_TEMPLATE_PATH = BASE_DIR / "data" / "sample_ecommerce_data.csv"
OUTPUTS_DIR = BASE_DIR / "analysis" / "outputs"
ASSETS_CHARTS_DIR = BASE_DIR / "frontend" / "assets" / "charts"

# Flexible column mapping dictionary to support various CSV schemas
COLUMN_SYNONYMS = {
    "order_id": ["order_id", "order id", "order", "orderid", "transaction_id", "order_number", "id"],
    "order_date": ["order_date", "order date", "date", "orderdate", "transaction_date", "created_at", "purchase_date"],
    "order_status": ["order_status", "order status", "status", "orderstatus", "fulfillment_status", "state"],
    "region": ["region", "hub", "territory", "location", "zone", "area", "city"],
    "product_name": ["product_name", "product name", "product", "item_name", "item", "title", "product_title", "description"],
    "category": ["category", "product_category", "catalog", "vertical", "department", "type", "group"],
    "quantity": ["quantity", "qty", "units", "count", "volume", "qty_sold"],
    "unit_price": ["unit_price", "unit price", "price", "unitprice", "selling_price", "item_price", "amount", "rate"],
    "discount": ["discount", "discount_amount", "discount amount", "promo", "promo_discount", "rebate", "concession"],
    "return_amount": ["return_amount", "return amount", "refund", "refund_amount", "returns", "refunded"]
}


def normalize_columns(df):
    """Map arbitrary column headers to standard schema names."""
    col_map = {}
    normalized_cols = {str(col).strip().lower(): col for col in df.columns}

    for standard_col, synonyms in COLUMN_SYNONYMS.items():
        for syn in synonyms:
            if syn in normalized_cols:
                col_map[normalized_cols[syn]] = standard_col
                break

    df = df.rename(columns=col_map)
    return df


@upload_bp.route("/upload", methods=["POST"])
def upload_dataset():
    """
    Ingest a user-provided CSV or Excel file, sanitize and normalize columns,
    re-seed SQLite database, compute KPIs, and refresh all static and dynamic visualizations.
    """
    if "file" not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded. Please select a CSV or Excel file."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"status": "error", "message": "Selected filename is empty."}), 400

    filename = file.filename.lower()
    if not (filename.endswith(".csv") or filename.endswith(".xlsx") or filename.endswith(".xls")):
        return jsonify({
            "status": "error",
            "message": "Unsupported file format. Please upload a .csv, .xlsx, or .xls file."
        }), 400

    try:
        # 1. Parse File into DataFrame
        if filename.endswith(".csv"):
            try:
                df = pd.read_csv(file.stream, encoding="utf-8")
            except UnicodeDecodeError:
                file.stream.seek(0)
                try:
                    df = pd.read_csv(file.stream, encoding="utf-8-sig")
                except UnicodeDecodeError:
                    file.stream.seek(0)
                    df = pd.read_csv(file.stream, encoding="latin-1")
        else:
            df = pd.read_excel(file.stream)

        if df.empty:
            return jsonify({"status": "error", "message": "The uploaded file contains no data rows."}), 400

        # 2. Normalize and check required fields
        df = normalize_columns(df)

        # Check required columns
        if "unit_price" not in df.columns:
            return jsonify({
                "status": "error",
                "message": "Missing required price column (e.g. 'unit_price', 'price', or 'amount')."
            }), 400

        # Auto-fill missing optional columns with sensible defaults
        if "order_id" not in df.columns:
            df["order_id"] = range(1, len(df) + 1)

        if "order_date" not in df.columns:
            df["order_date"] = datetime.now().strftime("%Y-%m-%d")

        if "order_status" not in df.columns:
            df["order_status"] = "delivered"

        if "region" not in df.columns:
            df["region"] = "Central"

        if "product_name" not in df.columns:
            if "category" in df.columns:
                df["product_name"] = df["category"].astype(str) + " Item"
            else:
                df["product_name"] = "Commercial Item"

        if "category" not in df.columns:
            df["category"] = "General"

        if "quantity" not in df.columns:
            df["quantity"] = 1

        if "discount" not in df.columns:
            df["discount"] = 0.0

        if "return_amount" not in df.columns:
            df["return_amount"] = 0.0

        # 3. Clean and sanitize data types
        df["order_id"] = df["order_id"].astype(str).str.strip()
        # Fallback numeric order id if needed
        order_id_map = {orig: idx + 1 for idx, orig in enumerate(df["order_id"].unique())}
        df["db_order_id"] = df["order_id"].map(order_id_map)

        # Standardize dates
        parsed_dates = pd.to_datetime(df["order_date"], errors="coerce")
        df["order_date"] = parsed_dates.dt.strftime("%Y-%m-%d").fillna(datetime.now().strftime("%Y-%m-%d"))

        # Standardize order statuses
        status_synonyms = {
            "completed": "delivered",
            "fulfilled": "delivered",
            "success": "delivered",
            "dispatched": "shipped",
            "in transit": "shipped",
            "processing": "pending",
            "open": "pending",
            "refunded": "cancelled",
            "void": "cancelled"
        }
        df["order_status"] = df["order_status"].astype(str).str.strip().str.lower().map(
            lambda s: status_synonyms.get(s, s if s in ["delivered", "shipped", "pending", "cancelled"] else "delivered")
        )

        # Standardize text
        df["region"] = df["region"].astype(str).str.strip().str.title().replace({"": "Central", "Nan": "Central"})
        df["category"] = df["category"].astype(str).str.strip().str.title().replace({"": "General", "Nan": "General"})
        df["product_name"] = df["product_name"].astype(str).str.strip().replace({"": "Standard Item", "Nan": "Standard Item"})

        # Standardize numeric values
        df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(1).astype(int).clip(lower=1)
        df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce").fillna(0.0).astype(float).clip(lower=0.0)
        df["discount"] = pd.to_numeric(df["discount"], errors="coerce").fillna(0.0).astype(float).clip(lower=0.0)
        df["return_amount"] = pd.to_numeric(df["return_amount"], errors="coerce").fillna(0.0).astype(float).clip(lower=0.0)

        # Prevent refund from exceeding line item amount
        line_gross = df["quantity"] * df["unit_price"]
        max_allowed_refund = np.maximum(0.0, line_gross - df["discount"])
        df["return_amount"] = np.minimum(df["return_amount"], max_allowed_refund)

        # 4. Generate Relational Data Structures
        # Unique Products
        products_df = df[["product_name", "category"]].drop_duplicates().reset_index(drop=True)
        products_df["product_id"] = range(1, len(products_df) + 1)

        product_id_map = {
            (row["product_name"], row["category"]): row["product_id"]
            for _, row in products_df.iterrows()
        }
        df["product_id"] = [
            product_id_map.get((p, c), 1)
            for p, c in zip(df["product_name"], df["category"])
        ]

        # Unique Orders
        orders_df = df[["db_order_id", "order_date", "order_status", "region"]].drop_duplicates(subset=["db_order_id"]).reset_index(drop=True)
        orders_df = orders_df.rename(columns={"db_order_id": "order_id"})

        # Order Items
        items_df = pd.DataFrame({
            "item_id": range(1, len(df) + 1),
            "order_id": df["db_order_id"],
            "product_id": df["product_id"],
            "quantity": df["quantity"],
            "unit_price": df["unit_price"],
            "discount": df["discount"],
            "return_amount": df["return_amount"]
        })

        # 5. Overwrite Raw CSVs and SQLite Database
        raw_dir = BASE_DIR / "data" / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        products_df.to_csv(raw_dir / "products.csv", index=False)
        orders_df.to_csv(raw_dir / "orders.csv", index=False)
        items_df.to_csv(raw_dir / "order_items.csv", index=False)

        # Update SQLite database
        db_path = current_app.config.get("DATABASE_PATH", BASE_DIR / "cartcompass.db")
        conn = get_db_connection(db_path)
        cursor = conn.cursor()

        cursor.execute("PRAGMA foreign_keys = OFF;")
        cursor.execute("DELETE FROM order_items;")
        cursor.execute("DELETE FROM orders;")
        cursor.execute("DELETE FROM products;")

        # Insert products
        cursor.executemany(
            "INSERT INTO products (product_id, product_name, category) VALUES (?, ?, ?);",
            [(int(r["product_id"]), str(r["product_name"]), str(r["category"])) for _, r in products_df.iterrows()]
        )

        # Insert orders
        cursor.executemany(
            "INSERT INTO orders (order_id, order_date, order_status, region) VALUES (?, ?, ?, ?);",
            [(int(r["order_id"]), str(r["order_date"]), str(r["order_status"]), str(r["region"])) for _, r in orders_df.iterrows()]
        )

        # Insert order_items
        cursor.executemany(
            "INSERT INTO order_items (item_id, order_id, product_id, quantity, unit_price, discount, return_amount) VALUES (?, ?, ?, ?, ?, ?, ?);",
            [(int(r["item_id"]), int(r["order_id"]), int(r["product_id"]), int(r["quantity"]), float(r["unit_price"]), float(r["discount"]), float(r["return_amount"])) for _, r in items_df.iterrows()]
        )

        cursor.execute("PRAGMA foreign_keys = ON;")
        conn.commit()
        conn.close()

        # 6. Execute Processing & Chart Pipelines
        run_pipeline()
        run_kpi_analysis()
        run_all_charts()

        # Copy generated 16:9 charts to frontend assets
        ASSETS_CHARTS_DIR.mkdir(parents=True, exist_ok=True)
        for img_file in OUTPUTS_DIR.glob("*.png"):
            shutil.copy(img_file, ASSETS_CHARTS_DIR / img_file.name)

        # 7. Formulate Summary Stats for Client Response
        total_gross = float((items_df["quantity"] * items_df["unit_price"]).sum())
        total_discount = float(items_df["discount"].sum())
        total_return = float(items_df["return_amount"].sum())
        total_net = float(total_gross - total_discount - total_return)

        delivered_mask = df["order_status"] == "delivered"
        delivered_net = float((
            (df.loc[delivered_mask, "quantity"] * df.loc[delivered_mask, "unit_price"]) -
            df.loc[delivered_mask, "discount"] -
            df.loc[delivered_mask, "return_amount"]
        ).sum())

        return jsonify({
            "status": "success",
            "message": "Dataset successfully uploaded, processed, and applied to all dashboard views!",
            "summary": {
                "total_records": len(df),
                "total_orders": len(orders_df),
                "total_items": len(items_df),
                "total_products": len(products_df),
                "categories": sorted(list(products_df["category"].unique())),
                "regions": sorted(list(orders_df["region"].unique())),
                "gross_sales": round(total_gross, 2),
                "net_sales": round(delivered_net, 2),
                "date_range": {
                    "start": str(orders_df["order_date"].min()),
                    "end": str(orders_df["order_date"].max())
                }
            }
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Data processing failed: {str(e)}"
        }), 500


@upload_bp.route("/template/sample-csv", methods=["GET"])
def download_sample_template():
    """Download pre-formatted sample CSV template for testing data upload."""
    if not SAMPLE_TEMPLATE_PATH.exists():
        return jsonify({"status": "error", "message": "Sample template file not found."}), 404

    return send_file(
        str(SAMPLE_TEMPLATE_PATH),
        mimetype="text/csv",
        as_attachment=True,
        download_name="cartcompass_sample_template.csv"
    )


@upload_bp.route("/reset-demo", methods=["POST"])
def reset_to_benchmark():
    """Reset the database and analytics pipeline back to the default synthetic benchmark dataset."""
    try:
        init_database(force_regenerate=True)
        run_pipeline()
        run_kpi_analysis()
        run_all_charts()

        ASSETS_CHARTS_DIR.mkdir(parents=True, exist_ok=True)
        for img_file in OUTPUTS_DIR.glob("*.png"):
            shutil.copy(img_file, ASSETS_CHARTS_DIR / img_file.name)

        return jsonify({
            "status": "success",
            "message": "Database and visual analytics successfully restored to default benchmark dataset (750 orders)."
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to reset demo dataset: {str(e)}"
        }), 500
