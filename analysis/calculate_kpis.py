"""
CartCompass-BI - Business Intelligence KPI Calculations
Modular functions using Pandas/NumPy to calculate business metrics,
growth rates, and segment aggregations according to business rules.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

# Ensure Windows terminal can output UTF-8 symbols without charmap error
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"


def filter_orders(df, start_date=None, end_date=None, status_mode="delivered"):
    """
    Filter master DataFrame by date range and order status policy.
    
    Status modes:
    - 'delivered': Only delivered orders (Realized Revenue, default).
    - 'all_active': Delivered, shipped, and pending orders (excludes cancelled).
    - 'all': All orders including cancelled.
    """
    filtered = df.copy()

    # Filter by status
    if status_mode == "delivered":
        filtered = filtered[filtered["order_status"] == "delivered"]
    elif status_mode == "all_active":
        filtered = filtered[filtered["order_status"].isin(["delivered", "shipped", "pending"])]
    elif status_mode == "all":
        # All orders, no status filtering
        pass
    else:
        # Fallback to delivered for any unrecognized status mode
        filtered = filtered[filtered["order_status"] == "delivered"]

    # Filter by date range (order_date is ISO YYYY-MM-DD string)
    if start_date:
        filtered = filtered[filtered["order_date"] >= start_date]
    if end_date:
        filtered = filtered[filtered["order_date"] <= end_date]

    return filtered


def calculate_summary_kpis(df):
    """
    Calculate primary high-level business KPIs:
    - Gross Sales: Sum(quantity * unit_price)
    - Discount Amount: Sum(discount)
    - Return Amount: Sum(return_amount)
    - Net Sales: Gross Sales - Discount Amount - Return Amount
    - Total Orders: Distinct count of order_id
    - Average Order Value (AOV): Net Sales / Total Orders (0 if Total Orders == 0)
    """
    if df.empty:
        return {
            "gross_sales": 0.0,
            "discount_amount": 0.0,
            "return_amount": 0.0,
            "net_sales": 0.0,
            "total_orders": 0,
            "total_items_sold": 0,
            "average_order_value": 0.0
        }

    gross_sales = float(df["gross_sales"].sum())
    discount_amount = float(df["discount"].sum())
    return_amount = float(df["return_amount"].sum())
    net_sales = round(gross_sales - discount_amount - return_amount, 2)
    gross_sales = round(gross_sales, 2)
    discount_amount = round(discount_amount, 2)
    return_amount = round(return_amount, 2)

    total_orders = int(df["order_id"].nunique())
    total_items_sold = int(df["quantity"].sum())

    aov = round(net_sales / total_orders, 2) if total_orders > 0 else 0.0

    return {
        "gross_sales": gross_sales,
        "discount_amount": discount_amount,
        "return_amount": return_amount,
        "net_sales": net_sales,
        "total_orders": total_orders,
        "total_items_sold": total_items_sold,
        "average_order_value": aov
    }


def calculate_growth_rate(current_val, previous_val):
    """
    Calculate percentage growth: ((Current - Previous) / Previous) * 100
    Returns None if previous_val <= 0 or not available (safe zero-denominator handling).
    """
    if previous_val is None or previous_val <= 0:
        return None
    return round(((current_val - previous_val) / previous_val) * 100.0, 2)


def calculate_monthly_revenue(df):
    """
    Aggregate Net Sales, Gross Sales, Orders, and Discounts grouped by month (YYYY-MM).
    """
    if df.empty:
        return []

    # Group by year_month
    grouped = df.groupby("year_month").agg(
        gross_sales=("gross_sales", "sum"),
        discount_amount=("discount", "sum"),
        return_amount=("return_amount", "sum"),
        total_orders=("order_id", "nunique"),
        total_items=("quantity", "sum")
    ).reset_index()

    grouped["net_sales"] = (
        grouped["gross_sales"] - grouped["discount_amount"] - grouped["return_amount"]
    ).round(2)
    grouped["gross_sales"] = grouped["gross_sales"].round(2)
    grouped["discount_amount"] = grouped["discount_amount"].round(2)
    grouped["return_amount"] = grouped["return_amount"].round(2)
    grouped["aov"] = np.where(
        grouped["total_orders"] > 0,
        (grouped["net_sales"] / grouped["total_orders"]).round(2),
        0.0
    )

    # Sort chronologically
    grouped = grouped.sort_values("year_month")

    records = grouped.to_dict(orient="records")
    return records


def calculate_category_revenue(df):
    """
    Aggregate Net Sales, Gross Sales, Order Items, and Share by Product Category.
    """
    if df.empty:
        return []

    grouped = df.groupby("category").agg(
        gross_sales=("gross_sales", "sum"),
        discount_amount=("discount", "sum"),
        return_amount=("return_amount", "sum"),
        total_items=("quantity", "sum"),
        distinct_orders=("order_id", "nunique")
    ).reset_index()

    grouped["net_sales"] = (
        grouped["gross_sales"] - grouped["discount_amount"] - grouped["return_amount"]
    ).round(2)
    grouped["gross_sales"] = grouped["gross_sales"].round(2)
    grouped["discount_amount"] = grouped["discount_amount"].round(2)
    grouped["return_amount"] = grouped["return_amount"].round(2)

    total_net = grouped["net_sales"].sum()
    grouped["revenue_share_pct"] = np.where(
        total_net > 0,
        ((grouped["net_sales"] / total_net) * 100).round(2),
        0.0
    )

    grouped = grouped.sort_values("net_sales", ascending=False)
    return grouped.to_dict(orient="records")


def calculate_regional_revenue(df):
    """
    Aggregate Net Sales, Order Counts, and Average Order Value by Region.
    """
    if df.empty:
        return []

    grouped = df.groupby("region").agg(
        gross_sales=("gross_sales", "sum"),
        discount_amount=("discount", "sum"),
        return_amount=("return_amount", "sum"),
        total_orders=("order_id", "nunique"),
        total_items=("quantity", "sum")
    ).reset_index()

    grouped["net_sales"] = (
        grouped["gross_sales"] - grouped["discount_amount"] - grouped["return_amount"]
    ).round(2)
    grouped["gross_sales"] = grouped["gross_sales"].round(2)
    grouped["discount_amount"] = grouped["discount_amount"].round(2)
    grouped["return_amount"] = grouped["return_amount"].round(2)
    grouped["aov"] = np.where(
        grouped["total_orders"] > 0,
        (grouped["net_sales"] / grouped["total_orders"]).round(2),
        0.0
    )

    total_net = grouped["net_sales"].sum()
    grouped["revenue_share_pct"] = np.where(
        total_net > 0,
        ((grouped["net_sales"] / total_net) * 100).round(2),
        0.0
    )

    grouped = grouped.sort_values("net_sales", ascending=False)
    return grouped.to_dict(orient="records")


def calculate_status_distribution(master_df):
    """
    Calculate order status counts, share percentage, and total gross value.
    Uses unique orders to prevent duplicate counts from multi-item orders.
    """
    # Group by order_id first to get unique orders with their status
    unique_orders = master_df.drop_duplicates(subset=["order_id"])[["order_id", "order_status"]]
    status_counts = unique_orders["order_status"].value_counts().to_dict()
    total_orders = len(unique_orders)

    results = []
    for status, count in status_counts.items():
        results.append({
            "status": status,
            "order_count": int(count),
            "percentage": round((count / total_orders) * 100, 2) if total_orders > 0 else 0.0
        })

    return results


def run_kpi_analysis():
    """
    Read master clean dataset, compute all KPI summaries and breakdowns,
    and save outputs into data/processed/.
    """
    master_path = PROCESSED_DIR / "ecommerce_master_clean.csv"
    if not master_path.exists():
        raise FileNotFoundError(
            f"Master clean dataset missing at {master_path}. Run analysis/clean_data.py first."
        )

    df = pd.read_csv(master_path)
    
    # 1. Realized KPIs (Delivered orders)
    delivered_df = filter_orders(df, status_mode="delivered")
    kpis_delivered = calculate_summary_kpis(delivered_df)
    monthly_delivered = calculate_monthly_revenue(delivered_df)
    category_delivered = calculate_category_revenue(delivered_df)
    regional_delivered = calculate_regional_revenue(delivered_df)

    # 2. All Active KPIs (Delivered, Shipped, Pending)
    active_df = filter_orders(df, status_mode="all_active")
    kpis_active = calculate_summary_kpis(active_df)

    # 3. Overall Status Breakdown
    status_dist = calculate_status_distribution(df)

    # Export KPI summary
    summary_output = {
        "generated_at": datetime.now().isoformat(),
        "policy": {
            "default_mode": "delivered",
            "description": "Delivered orders represent finalized realized sales. Cancelled orders are excluded."
        },
        "realized_kpis": kpis_delivered,
        "all_active_kpis": kpis_active,
        "status_distribution": status_dist,
        "monthly_revenue": monthly_delivered,
        "category_revenue": category_delivered,
        "regional_revenue": regional_delivered
    }

    summary_file = PROCESSED_DIR / "kpis_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary_output, f, indent=2)

    # Export CSVs for easy report inspection
    pd.DataFrame(monthly_delivered).to_csv(PROCESSED_DIR / "monthly_revenue_summary.csv", index=False)
    pd.DataFrame(category_delivered).to_csv(PROCESSED_DIR / "category_revenue_summary.csv", index=False)
    pd.DataFrame(regional_delivered).to_csv(PROCESSED_DIR / "regional_revenue_summary.csv", index=False)

    print("KPI Analysis completed successfully:")
    print(f"  Realized Net Sales: ₹{kpis_delivered['net_sales']:,.2f}")
    print(f"  Total Delivered Orders: {kpis_delivered['total_orders']}")
    print(f"  Average Order Value: ₹{kpis_delivered['average_order_value']:,.2f}")
    print(f"  Total Discount Given: ₹{kpis_delivered['discount_amount']:,.2f}")
    print(f"  Total Returns Refunded: ₹{kpis_delivered['return_amount']:,.2f}")
    print(f"  Saved artifacts to {PROCESSED_DIR}")

    return summary_output


if __name__ == "__main__":
    run_kpi_analysis()
