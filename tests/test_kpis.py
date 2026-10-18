"""
CartCompass-BI - Unit & Mathematical Tests for KPI Calculations
Validates business logic, mathematical formulas, discount/return handling,
cancelled order exclusion, and zero-denominator safety.
"""

import pytest
import pandas as pd
import numpy as np
from analysis.calculate_kpis import (
    calculate_summary_kpis,
    calculate_growth_rate,
    calculate_monthly_revenue,
    calculate_category_revenue,
    calculate_regional_revenue,
    filter_orders
)
from analysis.clean_data import clean_and_validate


@pytest.fixture
def sample_business_data():
    """
    Construct an in-memory sample dataset with known exact numbers:
    - Order 1: Delivered, 2 items (Item 1: 2 * 100 = 200, disc=20, ret=0; Item 2: 1 * 300 = 300, disc=0, ret=50) -> Net = 180 + 250 = 430
    - Order 2: Delivered, 1 item (Item 3: 1 * 500 = 500, disc=50, ret=0) -> Net = 450
    - Order 3: Cancelled, 1 item (Item 4: 1 * 1000 = 1000, disc=0, ret=0) -> Should be excluded!
    - Order 4: Shipped, 1 item (Item 5: 2 * 200 = 400, disc=40, ret=0) -> Net = 360
    """
    data = [
        # order_id, order_date, order_status, region, category, quantity, unit_price, discount, return_amount
        {
            "order_id": 1, "order_date": "2025-01-15", "order_status": "delivered",
            "region": "North", "category": "Electronics",
            "quantity": 2, "unit_price": 100.0, "discount": 20.0, "return_amount": 0.0,
            "gross_sales": 200.0, "net_sales": 180.0, "year_month": "2025-01"
        },
        {
            "order_id": 1, "order_date": "2025-01-15", "order_status": "delivered",
            "region": "North", "category": "Electronics",
            "quantity": 1, "unit_price": 300.0, "discount": 0.0, "return_amount": 50.0,
            "gross_sales": 300.0, "net_sales": 250.0, "year_month": "2025-01"
        },
        {
            "order_id": 2, "order_date": "2025-01-20", "order_status": "delivered",
            "region": "South", "category": "Home & Kitchen",
            "quantity": 1, "unit_price": 500.0, "discount": 50.0, "return_amount": 0.0,
            "gross_sales": 500.0, "net_sales": 450.0, "year_month": "2025-01"
        },
        {
            "order_id": 3, "order_date": "2025-02-10", "order_status": "cancelled",
            "region": "East", "category": "Electronics",
            "quantity": 1, "unit_price": 1000.0, "discount": 0.0, "return_amount": 0.0,
            "gross_sales": 1000.0, "net_sales": 1000.0, "year_month": "2025-02"
        },
        {
            "order_id": 4, "order_date": "2025-02-18", "order_status": "shipped",
            "region": "West", "category": "Fashion & Apparel",
            "quantity": 2, "unit_price": 200.0, "discount": 40.0, "return_amount": 0.0,
            "gross_sales": 400.0, "net_sales": 360.0, "year_month": "2025-02"
        }
    ]
    return pd.DataFrame(data)


def test_gross_and_net_sales_calculation(sample_business_data):
    """Verify Gross Sales and Net Sales formulas on delivered orders."""
    delivered = filter_orders(sample_business_data, status_mode="delivered")
    kpis = calculate_summary_kpis(delivered)

    # Order 1 (200 + 300 = 500 gross) + Order 2 (500 gross) = 1000 gross
    assert kpis["gross_sales"] == 1000.0
    # Discounts: 20 + 0 + 50 = 70
    assert kpis["discount_amount"] == 70.0
    # Returns: 0 + 50 + 0 = 50
    assert kpis["return_amount"] == 50.0
    # Net Sales = 1000 - 70 - 50 = 880
    assert kpis["net_sales"] == 880.0


def test_cancelled_order_exclusion(sample_business_data):
    """Verify that cancelled orders are strictly excluded from sales and order counts."""
    delivered = filter_orders(sample_business_data, status_mode="delivered")
    kpis_delivered = calculate_summary_kpis(delivered)

    # Cancelled Order 3 has gross 1000. It must not appear in delivered sales.
    assert kpis_delivered["gross_sales"] == 1000.0
    assert kpis_delivered["total_orders"] == 2

    # In all_active mode (delivered + shipped + pending), cancelled is still excluded!
    active = filter_orders(sample_business_data, status_mode="all_active")
    kpis_active = calculate_summary_kpis(active)
    # Delivered (1000) + Shipped (400) = 1400 gross. Cancelled (1000) excluded!
    assert kpis_active["gross_sales"] == 1400.0
    assert kpis_active["total_orders"] == 3


def test_distinct_order_counting(sample_business_data):
    """Verify multi-item orders are not counted multiple times."""
    delivered = filter_orders(sample_business_data, status_mode="delivered")
    # Order 1 has 2 items, Order 2 has 1 item -> Total distinct orders must be exactly 2
    kpis = calculate_summary_kpis(delivered)
    assert kpis["total_orders"] == 2
    assert kpis["total_items_sold"] == 4  # 2 + 1 + 1 = 4 items


def test_average_order_value(sample_business_data):
    """Verify AOV calculation: Net Sales / Total Orders."""
    delivered = filter_orders(sample_business_data, status_mode="delivered")
    kpis = calculate_summary_kpis(delivered)

    # Net Sales = 880.0, Total Orders = 2 -> AOV = 440.0
    expected_aov = round(880.0 / 2, 2)
    assert kpis["average_order_value"] == expected_aov

    # Empty dataset must safely return 0.0 without ZeroDivisionError
    empty_kpis = calculate_summary_kpis(pd.DataFrame(columns=sample_business_data.columns))
    assert empty_kpis["average_order_value"] == 0.0
    assert empty_kpis["total_orders"] == 0


def test_growth_rate_zero_denominator():
    """Verify growth rate handles zero, negative, and missing baselines safely."""
    # Normal positive growth: ((150 - 100) / 100) * 100 = 50.0%
    assert calculate_growth_rate(150.0, 100.0) == 50.0

    # Negative growth: ((80 - 100) / 100) * 100 = -20.0%
    assert calculate_growth_rate(80.0, 100.0) == -20.0

    # Zero baseline denominator: must return None (N/A), never throw ZeroDivisionError
    assert calculate_growth_rate(100.0, 0.0) is None
    assert calculate_growth_rate(100.0, -50.0) is None
    assert calculate_growth_rate(100.0, None) is None


def test_monthly_and_category_aggregation(sample_business_data):
    """Verify monthly and category aggregation logic."""
    delivered = filter_orders(sample_business_data, status_mode="delivered")
    monthly = calculate_monthly_revenue(delivered)
    categories = calculate_category_revenue(delivered)
    regions = calculate_regional_revenue(delivered)

    # Monthly check
    assert len(monthly) == 1
    assert monthly[0]["year_month"] == "2025-01"
    assert monthly[0]["net_sales"] == 880.0

    # Category check
    cat_names = [c["category"] for c in categories]
    assert "Electronics" in cat_names
    assert "Home & Kitchen" in cat_names

    # Shares must sum to 100%
    total_share = sum(c["revenue_share_pct"] for c in categories)
    assert pytest.approx(total_share, 0.1) == 100.0

    # Regional check
    reg_names = [r["region"] for r in regions]
    assert "North" in reg_names
    assert "South" in reg_names


def test_clean_and_validate_edge_cases():
    """Test data cleaning with invalid negative numbers and excessive refunds."""
    products = pd.DataFrame([{"product_id": 1, "product_name": "Test Prod", "category": "Gadgets"}])
    orders = pd.DataFrame([{"order_id": 1, "order_date": "2025-01-01", "order_status": "delivered", "region": "North"}])
    # Item with discount exceeding price, and return exceeding net
    items = pd.DataFrame([{
        "item_id": 1, "order_id": 1, "product_id": 1,
        "quantity": 1, "unit_price": 100.0, "discount": 150.0, "return_amount": 200.0
    }])

    p_clean, o_clean, i_clean, report = clean_and_validate(products, orders, items)
    # Discount should be capped at gross (100.0)
    assert i_clean.iloc[0]["discount"] == 100.0
    # Net before return becomes 0.0, so return_amount should be capped at 0.0
    assert i_clean.iloc[0]["return_amount"] == 0.0
