"""
CartCompass-BI - Static Report Chart Generator
Generates high-resolution Matplotlib visualizations and exports them to analysis/outputs/.
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
# Use non-interactive Agg backend for headless generation
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# Ensure Windows console encoding compatibility
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
OUTPUTS_DIR = BASE_DIR / "analysis" / "outputs"

# Modern, harmonious color palette
PRIMARY_BLUE = "#2563eb"
ACCENT_CYAN = "#06b6d4"
EMERALD_GREEN = "#10b981"
AMBER_ORANGE = "#f59e0b"
ROSE_RED = "#f43f5e"
INDIGO_PURPLE = "#6366f1"
DARK_GRAY = "#1e293b"
LIGHT_BG = "#f8fafc"
GRID_COLOR = "#e2e8f0"

PALETTE = [PRIMARY_BLUE, EMERALD_GREEN, AMBER_ORANGE, INDIGO_PURPLE, ROSE_RED, ACCENT_CYAN]


def apply_custom_style(ax, title, xlabel="", ylabel=""):
    """Apply modern visual theme to matplotlib axes."""
    ax.set_facecolor(LIGHT_BG)
    ax.figure.patch.set_facecolor("#ffffff")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#cbd5e1")
    ax.spines["bottom"].set_color("#cbd5e1")
    ax.tick_params(colors=DARK_GRAY, labelsize=10)
    ax.grid(color=GRID_COLOR, linestyle="--", linewidth=0.7, alpha=0.8)
    ax.set_axisbelow(True)

    ax.set_title(title, fontsize=14, fontweight="bold", pad=14, color=DARK_GRAY)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=11, fontweight="medium", labelpad=8, color=DARK_GRAY)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=11, fontweight="medium", labelpad=8, color=DARK_GRAY)


def generate_monthly_revenue_chart(df):
    """Generate monthly net revenue line chart with markers."""
    delivered_df = df[df["order_status"] == "delivered"]
    monthly = delivered_df.groupby("year_month").apply(
        lambda g: (g["quantity"] * g["unit_price"] - g["discount"] - g["return_amount"]).sum()
    ).reset_index(name="net_sales")

    fig, ax = plt.subplots(figsize=(10, 5.625), dpi=300)
    apply_custom_style(ax, "Monthly Net Revenue Trend (Realized Sales)", "Month", "Net Revenue (₹)")

    x = range(len(monthly))
    y = monthly["net_sales"]

    ax.plot(x, y, color=PRIMARY_BLUE, linewidth=2.5, marker="o", markersize=6, label="Net Revenue (₹)")
    ax.fill_between(x, y, color=PRIMARY_BLUE, alpha=0.10)

    ax.set_xticks(list(x))
    ax.set_xticklabels(monthly["year_month"], rotation=40, ha="right")

    # Format y-axis in Lakhs/Thousands
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda val, pos: f"₹{val/1000:,.0f}k"))

    # Annotate peak month
    max_idx = y.idxmax()
    ax.annotate(
        f"Peak: ₹{y[max_idx]:,.0f}",
        xy=(max_idx, y[max_idx]),
        xytext=(max_idx - 1, y[max_idx] * 1.05),
        arrowprops=dict(facecolor=DARK_GRAY, arrowstyle="->", lw=1),
        fontweight="bold",
        fontsize=9,
        color=DARK_GRAY
    )

    plt.tight_layout()
    chart_path = OUTPUTS_DIR / "monthly_revenue_trend.png"
    plt.savefig(chart_path)
    plt.close()
    return chart_path


def generate_category_revenue_chart(df):
    """Generate horizontal bar chart of net revenue by product category."""
    delivered_df = df[df["order_status"] == "delivered"].copy()
    delivered_df["item_net"] = (
        delivered_df["quantity"] * delivered_df["unit_price"] -
        delivered_df["discount"] - delivered_df["return_amount"]
    )
    cat_summary = delivered_df.groupby("category")["item_net"].sum().sort_values(ascending=True)

    fig, ax = plt.subplots(figsize=(10, 5.625), dpi=300)
    apply_custom_style(ax, "Revenue by Product Category (Delivered Orders)", "Net Revenue (₹)", "Category")

    bars = ax.barh(cat_summary.index, cat_summary.values, color=PALETTE[:len(cat_summary)], height=0.6)

    # Annotate bar values
    max_val = cat_summary.max()
    for bar in bars:
        width = bar.get_width()
        ax.text(
            width + (max_val * 0.015),
            bar.get_y() + bar.get_height() / 2,
            f"₹{width:,.0f}",
            va="center",
            ha="left",
            fontsize=9.5,
            fontweight="bold",
            color=DARK_GRAY
        )

    ax.set_xlim(0, max_val * 1.18)
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda val, pos: f"₹{val/1000:,.0f}k"))

    plt.tight_layout()
    chart_path = OUTPUTS_DIR / "category_revenue_distribution.png"
    plt.savefig(chart_path)
    plt.close()
    return chart_path


def generate_regional_performance_chart(df):
    """Generate bar chart comparing revenue and order volume by region."""
    delivered_df = df[df["order_status"] == "delivered"].copy()
    delivered_df["item_net"] = (
        delivered_df["quantity"] * delivered_df["unit_price"] -
        delivered_df["discount"] - delivered_df["return_amount"]
    )

    reg_summary = delivered_df.groupby("region").agg(
        net_sales=("item_net", "sum"),
        order_count=("order_id", "nunique")
    ).reset_index().sort_values("net_sales", ascending=False)

    fig, ax1 = plt.subplots(figsize=(10, 5.625), dpi=300)
    apply_custom_style(ax1, "Regional Performance: Net Sales & Orders", "Region", "Net Revenue (₹)")

    x = np.arange(len(reg_summary))
    width = 0.45

    rects = ax1.bar(x, reg_summary["net_sales"], width, color=PRIMARY_BLUE, alpha=0.9, label="Net Sales (₹)")
    ax1.yaxis.set_major_formatter(ticker.FuncFormatter(lambda val, pos: f"₹{val/1000:,.0f}k"))

    for rect in rects:
        height = rect.get_height()
        ax1.annotate(
            f"₹{height/1000:,.0f}k",
            xy=(rect.get_x() + rect.get_width() / 2, height),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
            color=DARK_GRAY
        )

    ax1.set_xticks(x)
    ax1.set_xticklabels(reg_summary["region"], fontweight="medium")
    ax1.set_ylim(0, reg_summary["net_sales"].max() * 1.15)

    plt.tight_layout()
    chart_path = OUTPUTS_DIR / "regional_performance.png"
    plt.savefig(chart_path)
    plt.close()
    return chart_path


def generate_order_status_chart(df):
    """Generate modern doughnut chart showing distribution of order statuses."""
    unique_orders = df.drop_duplicates(subset=["order_id"])
    status_counts = unique_orders["order_status"].value_counts()

    labels = [s.capitalize() for s in status_counts.index]
    counts = status_counts.values
    colors = [EMERALD_GREEN, PRIMARY_BLUE, AMBER_ORANGE, ROSE_RED][:len(labels)]

    fig, ax = plt.subplots(figsize=(10, 5.625), dpi=300)
    fig.patch.set_facecolor("#ffffff")

    wedges, texts, autotexts = ax.pie(
        counts,
        labels=labels,
        autopct="%1.1f%%",
        startangle=140,
        pctdistance=0.75,
        colors=colors,
        wedgeprops=dict(width=0.45, edgecolor="#ffffff", linewidth=2.5)
    )

    for text in texts:
        text.set_color(DARK_GRAY)
        text.set_fontsize(11)
        text.set_fontweight("medium")

    for autotext in autotexts:
        autotext.set_color("#ffffff")
        autotext.set_fontsize(10)
        autotext.set_fontweight("bold")

    ax.set_title("Overall Order Status Distribution", fontsize=14, fontweight="bold", pad=15, color=DARK_GRAY)

    # Center total count
    total_orders = sum(counts)
    ax.text(0, 0, f"Total\n{total_orders}\nOrders", ha="center", va="center", fontsize=11, fontweight="bold", color=DARK_GRAY)

    plt.tight_layout()
    chart_path = OUTPUTS_DIR / "order_status_breakdown.png"
    plt.savefig(chart_path)
    plt.close()
    return chart_path


def generate_period_comparison_chart(df):
    """
    Compare two equal 6-month periods:
    Period 1: 2025-01-01 to 2025-06-30 (H1 2025)
    Period 2: 2025-07-01 to 2025-12-31 (H2 2025)
    Shows Category Revenue side-by-side.
    """
    delivered_df = df[df["order_status"] == "delivered"].copy()
    delivered_df["item_net"] = (
        delivered_df["quantity"] * delivered_df["unit_price"] -
        delivered_df["discount"] - delivered_df["return_amount"]
    )

    p1 = delivered_df[(delivered_df["order_date"] >= "2025-01-01") & (delivered_df["order_date"] <= "2025-06-30")]
    p2 = delivered_df[(delivered_df["order_date"] >= "2025-07-01") & (delivered_df["order_date"] <= "2025-12-31")]

    categories = sorted(delivered_df["category"].unique())
    p1_rev = [p1[p1["category"] == c]["item_net"].sum() for c in categories]
    p2_rev = [p2[p2["category"] == c]["item_net"].sum() for c in categories]

    x = np.arange(len(categories))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 5.625), dpi=300)
    apply_custom_style(ax, "Period Comparison: H1 2025 vs H2 2025 Net Revenue by Category", "Category", "Net Revenue (₹)")

    rects1 = ax.bar(x - width/2, p1_rev, width, label="H1 2025 (Jan - Jun)", color="#94a3b8")
    rects2 = ax.bar(x + width/2, p2_rev, width, label="H2 2025 (Jul - Dec)", color=PRIMARY_BLUE)

    ax.set_xticks(x)
    ax.set_xticklabels(categories, rotation=20, ha="right", fontweight="medium")
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda val, pos: f"₹{val/1000:,.0f}k"))
    ax.legend(frameon=True, facecolor="#ffffff", edgecolor="#cbd5e1", fontsize=10)

    plt.tight_layout()
    chart_path = OUTPUTS_DIR / "period_comparison.png"
    plt.savefig(chart_path)
    plt.close()
    return chart_path


def run_all_charts():
    """Generate all 5 static analytical charts."""
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    master_path = PROCESSED_DIR / "ecommerce_master_clean.csv"
    if not master_path.exists():
        raise FileNotFoundError(f"Master clean data missing at {master_path}.")

    df = pd.read_csv(master_path)

    c1 = generate_monthly_revenue_chart(df)
    c2 = generate_category_revenue_chart(df)
    c3 = generate_regional_performance_chart(df)
    c4 = generate_order_status_chart(df)
    c5 = generate_period_comparison_chart(df)

    print(f"Generated 5 publication-ready static charts in {OUTPUTS_DIR}:")
    print(f"  1. {c1.name}")
    print(f"  2. {c2.name}")
    print(f"  3. {c3.name}")
    print(f"  4. {c4.name}")
    print(f"  5. {c5.name}")


if __name__ == "__main__":
    run_all_charts()
