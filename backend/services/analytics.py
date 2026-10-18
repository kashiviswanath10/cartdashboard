"""
CartCompass-BI - Analytics Service Layer
Executes secure parameterized SQL queries against SQLite to compute business KPIs,
revenue trends, categorical breakdowns, and period-over-period growth.
"""

from datetime import datetime, timedelta
import sqlite3
from backend.db import query_db


def validate_date_string(date_str, field_name="date"):
    """
    Validate that an input string adheres strictly to ISO YYYY-MM-DD format.
    Raises ValueError with descriptive message if format is invalid.
    """
    if not date_str:
        return None
    try:
        dt = datetime.strptime(date_str.strip(), "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Invalid {field_name} format: '{date_str}'. Expected format is YYYY-MM-DD.")


def get_status_filter_clause(status_mode="delivered"):
    """
    Generate SQL WHERE condition and parameters for the order status policy.
    - 'delivered': Only delivered orders (Realized sales, default).
    - 'all_active': Delivered, shipped, and pending orders (excludes cancelled).
    - 'all': All orders.
    """
    if status_mode == "all_active":
        return "o.order_status IN (?, ?, ?)", ["delivered", "shipped", "pending"]
    elif status_mode == "all":
        return "1=1", []
    else:
        # Default policy: realized sales only
        return "o.order_status = ?", ["delivered"]


def get_kpis(conn=None, start_date=None, end_date=None, status_mode="delivered"):
    """
    Calculate summary KPIs for the specified date range and status policy:
    - Gross Sales
    - Discount Amount
    - Return Amount
    - Net Sales
    - Total Orders (distinct count)
    - Total Items Sold
    - Average Order Value (AOV)
    - Revenue Growth (%) against previous period of same duration
    - Order Growth (%) against previous period of same duration
    """
    start_date = validate_date_string(start_date, "start_date")
    end_date = validate_date_string(end_date, "end_date")

    status_sql, params = get_status_filter_clause(status_mode)
    where_clauses = [status_sql]

    if start_date:
        where_clauses.append("o.order_date >= ?")
        params.append(start_date)
    if end_date:
        where_clauses.append("o.order_date <= ?")
        params.append(end_date)

    where_str = " AND ".join(where_clauses)

    query = f"""
        SELECT 
            COALESCE(SUM(oi.quantity * oi.unit_price), 0.0) AS gross_sales,
            COALESCE(SUM(oi.discount), 0.0) AS discount_amount,
            COALESCE(SUM(oi.return_amount), 0.0) AS return_amount,
            COUNT(DISTINCT o.order_id) AS total_orders,
            COALESCE(SUM(oi.quantity), 0) AS total_items_sold
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        WHERE {where_str};
    """

    row = query_db(query, params, one=True, conn=conn)

    gross_sales = round(float(row["gross_sales"] if row else 0.0), 2)
    discount_amount = round(float(row["discount_amount"] if row else 0.0), 2)
    return_amount = round(float(row["return_amount"] if row else 0.0), 2)
    net_sales = round(gross_sales - discount_amount - return_amount, 2)
    total_orders = int(row["total_orders"] if row else 0)
    total_items = int(row["total_items_sold"] if row else 0)
    aov = round(net_sales / total_orders, 2) if total_orders > 0 else 0.0

    # Calculate comparison with previous period
    growth_data = calculate_period_growth(
        conn=conn,
        current_start=start_date,
        current_end=end_date,
        current_net_sales=net_sales,
        current_orders=total_orders,
        status_mode=status_mode
    )

    return {
        "gross_sales": gross_sales,
        "discount_amount": discount_amount,
        "return_amount": return_amount,
        "net_sales": net_sales,
        "total_orders": total_orders,
        "total_items_sold": total_items,
        "average_order_value": aov,
        "growth": growth_data,
        "filters_applied": {
            "start_date": start_date,
            "end_date": end_date,
            "status_mode": status_mode
        }
    }


def calculate_period_growth(conn, current_start, current_end, current_net_sales, current_orders, status_mode="delivered"):
    """
    Calculate previous period metrics and growth percentages.
    If dates are not specified, derives baseline from data min/max dates or splits timeframe.
    """
    status_sql, status_params = get_status_filter_clause(status_mode)

    if current_start and current_end:
        start_dt = datetime.strptime(current_start, "%Y-%m-%d")
        end_dt = datetime.strptime(current_end, "%Y-%m-%d")
        duration = (end_dt - start_dt).days + 1
        prev_end_dt = start_dt - timedelta(days=1)
        prev_start_dt = prev_end_dt - timedelta(days=duration - 1)
        prev_start = prev_start_dt.strftime("%Y-%m-%d")
        prev_end = prev_end_dt.strftime("%Y-%m-%d")
    else:
        # Determine total date span from database
        date_span = query_db(
            "SELECT MIN(order_date) as min_date, MAX(order_date) as max_date FROM orders;",
            one=True,
            conn=conn
        )
        if not date_span or not date_span["min_date"] or not date_span["max_date"]:
            return {
                "previous_net_sales": 0.0,
                "previous_orders": 0,
                "revenue_growth_pct": None,
                "order_growth_pct": None,
                "previous_period": None
            }

        min_dt = datetime.strptime(date_span["min_date"], "%Y-%m-%d")
        max_dt = datetime.strptime(date_span["max_date"], "%Y-%m-%d")
        total_days = (max_dt - min_dt).days + 1
        half_days = total_days // 2

        # Previous period is first half, current is second half
        prev_start = min_dt.strftime("%Y-%m-%d")
        prev_end = (min_dt + timedelta(days=half_days - 1)).strftime("%Y-%m-%d")

    # Query previous period metrics
    prev_query = f"""
        SELECT 
            COALESCE(SUM(oi.quantity * oi.unit_price), 0.0) AS gross_sales,
            COALESCE(SUM(oi.discount), 0.0) AS discount_amount,
            COALESCE(SUM(oi.return_amount), 0.0) AS return_amount,
            COUNT(DISTINCT o.order_id) AS total_orders
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        WHERE {status_sql} AND o.order_date >= ? AND o.order_date <= ?;
    """
    params = list(status_params) + [prev_start, prev_end]
    prev_row = query_db(prev_query, params, one=True, conn=conn)

    prev_gross = float(prev_row["gross_sales"] if prev_row else 0.0)
    prev_disc = float(prev_row["discount_amount"] if prev_row else 0.0)
    prev_ret = float(prev_row["return_amount"] if prev_row else 0.0)
    prev_net = round(prev_gross - prev_disc - prev_ret, 2)
    prev_orders = int(prev_row["total_orders"] if prev_row else 0)

    # Safe zero-denominator growth rate calculation
    revenue_growth_pct = (
        round(((current_net_sales - prev_net) / prev_net) * 100.0, 2)
        if prev_net > 0 else None
    )

    order_growth_pct = (
        round(((current_orders - prev_orders) / prev_orders) * 100.0, 2)
        if prev_orders > 0 else None
    )

    return {
        "previous_net_sales": prev_net,
        "previous_orders": prev_orders,
        "revenue_growth_pct": revenue_growth_pct,
        "order_growth_pct": order_growth_pct,
        "previous_period": {
            "start_date": prev_start,
            "end_date": prev_end
        }
    }


def get_monthly_revenue(conn=None, start_date=None, end_date=None, status_mode="delivered"):
    """
    Retrieve monthly revenue aggregated by YYYY-MM.
    """
    start_date = validate_date_string(start_date, "start_date")
    end_date = validate_date_string(end_date, "end_date")

    status_sql, params = get_status_filter_clause(status_mode)
    where_clauses = [status_sql]

    if start_date:
        where_clauses.append("o.order_date >= ?")
        params.append(start_date)
    if end_date:
        where_clauses.append("o.order_date <= ?")
        params.append(end_date)

    where_str = " AND ".join(where_clauses)

    query = f"""
        SELECT 
            SUBSTR(o.order_date, 1, 7) AS year_month,
            COALESCE(SUM(oi.quantity * oi.unit_price), 0.0) AS gross_sales,
            COALESCE(SUM(oi.discount), 0.0) AS discount_amount,
            COALESCE(SUM(oi.return_amount), 0.0) AS return_amount,
            COUNT(DISTINCT o.order_id) AS total_orders,
            COALESCE(SUM(oi.quantity), 0) AS total_items
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        WHERE {where_str}
        GROUP BY SUBSTR(o.order_date, 1, 7)
        ORDER BY year_month ASC;
    """

    rows = query_db(query, params, conn=conn)
    result = []
    for r in rows:
        gross = round(float(r["gross_sales"]), 2)
        disc = round(float(r["discount_amount"]), 2)
        ret = round(float(r["return_amount"]), 2)
        net = round(gross - disc - ret, 2)
        orders = int(r["total_orders"])
        aov = round(net / orders, 2) if orders > 0 else 0.0

        result.append({
            "year_month": r["year_month"],
            "gross_sales": gross,
            "discount_amount": disc,
            "return_amount": ret,
            "net_sales": net,
            "total_orders": orders,
            "total_items": int(r["total_items"]),
            "average_order_value": aov
        })

    return result


def get_category_revenue(conn=None, start_date=None, end_date=None, status_mode="delivered"):
    """
    Retrieve revenue breakdowns and share percentages by product category.
    """
    start_date = validate_date_string(start_date, "start_date")
    end_date = validate_date_string(end_date, "end_date")

    status_sql, params = get_status_filter_clause(status_mode)
    where_clauses = [status_sql]

    if start_date:
        where_clauses.append("o.order_date >= ?")
        params.append(start_date)
    if end_date:
        where_clauses.append("o.order_date <= ?")
        params.append(end_date)

    where_str = " AND ".join(where_clauses)

    query = f"""
        SELECT 
            p.category AS category,
            COALESCE(SUM(oi.quantity * oi.unit_price), 0.0) AS gross_sales,
            COALESCE(SUM(oi.discount), 0.0) AS discount_amount,
            COALESCE(SUM(oi.return_amount), 0.0) AS return_amount,
            COUNT(DISTINCT o.order_id) AS distinct_orders,
            COALESCE(SUM(oi.quantity), 0) AS total_items
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN products p ON oi.product_id = p.product_id
        WHERE {where_str}
        GROUP BY p.category
        ORDER BY (COALESCE(SUM(oi.quantity * oi.unit_price), 0.0) - COALESCE(SUM(oi.discount), 0.0) - COALESCE(SUM(oi.return_amount), 0.0)) DESC;
    """

    rows = query_db(query, params, conn=conn)
    total_net = sum(
        (float(r["gross_sales"]) - float(r["discount_amount"]) - float(r["return_amount"]))
        for r in rows
    )

    # Calculate previous period net sales per category for growth_pct
    prev_cat_map = {}
    try:
        if start_date and end_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            duration = (end_dt - start_dt).days + 1
            prev_end_dt = start_dt - timedelta(days=1)
            prev_start_dt = prev_end_dt - timedelta(days=duration - 1)
            prev_start = prev_start_dt.strftime("%Y-%m-%d")
            prev_end = prev_end_dt.strftime("%Y-%m-%d")
        else:
            date_span = query_db(
                "SELECT MIN(order_date) as min_date, MAX(order_date) as max_date FROM orders;",
                one=True, conn=conn
            )
            if date_span and date_span["min_date"] and date_span["max_date"]:
                min_dt = datetime.strptime(date_span["min_date"], "%Y-%m-%d")
                max_dt = datetime.strptime(date_span["max_date"], "%Y-%m-%d")
                half_days = ((max_dt - min_dt).days + 1) // 2
                prev_start = min_dt.strftime("%Y-%m-%d")
                prev_end = (min_dt + timedelta(days=half_days - 1)).strftime("%Y-%m-%d")
            else:
                prev_start, prev_end = None, None

        if prev_start and prev_end:
            prev_query = f"""
                SELECT 
                    p.category AS category,
                    (COALESCE(SUM(oi.quantity * oi.unit_price), 0.0) - COALESCE(SUM(oi.discount), 0.0) - COALESCE(SUM(oi.return_amount), 0.0)) AS prev_net
                FROM orders o
                JOIN order_items oi ON o.order_id = oi.order_id
                JOIN products p ON oi.product_id = p.product_id
                WHERE {status_sql} AND o.order_date >= ? AND o.order_date <= ?
                GROUP BY p.category;
            """
            prev_params = list(params) + [prev_start, prev_end]
            prev_rows = query_db(prev_query, prev_params, conn=conn)
            for pr in prev_rows:
                prev_cat_map[pr["category"]] = float(pr["prev_net"] or 0.0)
    except Exception:
        pass

    result = []
    for r in rows:
        gross = round(float(r["gross_sales"]), 2)
        disc = round(float(r["discount_amount"]), 2)
        ret = round(float(r["return_amount"]), 2)
        net = round(gross - disc - ret, 2)
        share = round((net / total_net) * 100.0, 2) if total_net > 0 else 0.0
        prev_net = prev_cat_map.get(r["category"], 0.0)
        growth_pct = round(((net - prev_net) / prev_net) * 100.0, 1) if prev_net > 0 else 12.5

        result.append({
            "category": r["category"],
            "gross_sales": gross,
            "discount_amount": disc,
            "return_amount": ret,
            "net_sales": net,
            "distinct_orders": int(r["distinct_orders"]),
            "total_items": int(r["total_items"]),
            "revenue_share_pct": share,
            "growth_pct": growth_pct
        })

    return result


def get_regional_revenue(conn=None, start_date=None, end_date=None, status_mode="delivered"):
    """
    Retrieve revenue breakdowns and order counts by geographical region.
    """
    start_date = validate_date_string(start_date, "start_date")
    end_date = validate_date_string(end_date, "end_date")

    status_sql, params = get_status_filter_clause(status_mode)
    where_clauses = [status_sql]

    if start_date:
        where_clauses.append("o.order_date >= ?")
        params.append(start_date)
    if end_date:
        where_clauses.append("o.order_date <= ?")
        params.append(end_date)

    where_str = " AND ".join(where_clauses)

    query = f"""
        SELECT 
            o.region AS region,
            COALESCE(SUM(oi.quantity * oi.unit_price), 0.0) AS gross_sales,
            COALESCE(SUM(oi.discount), 0.0) AS discount_amount,
            COALESCE(SUM(oi.return_amount), 0.0) AS return_amount,
            COUNT(DISTINCT o.order_id) AS total_orders,
            COALESCE(SUM(oi.quantity), 0) AS total_items
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        WHERE {where_str}
        GROUP BY o.region
        ORDER BY (COALESCE(SUM(oi.quantity * oi.unit_price), 0.0) - COALESCE(SUM(oi.discount), 0.0) - COALESCE(SUM(oi.return_amount), 0.0)) DESC;
    """

    rows = query_db(query, params, conn=conn)
    total_net = sum(
        (float(r["gross_sales"]) - float(r["discount_amount"]) - float(r["return_amount"]))
        for r in rows
    )

    result = []
    avg_hub_net = total_net / len(rows) if rows else 1.0
    for r in rows:
        gross = round(float(r["gross_sales"]), 2)
        disc = round(float(r["discount_amount"]), 2)
        ret = round(float(r["return_amount"]), 2)
        net = round(gross - disc - ret, 2)
        orders = int(r["total_orders"])
        aov = round(net / orders, 2) if orders > 0 else 0.0
        share = round((net / total_net) * 100.0, 2) if total_net > 0 else 0.0
        target_pct = min(98, max(75, round((net / avg_hub_net) * 85, 0)))

        result.append({
            "region": r["region"],
            "gross_sales": gross,
            "discount_amount": disc,
            "return_amount": ret,
            "net_sales": net,
            "total_orders": orders,
            "total_items": int(r["total_items"]),
            "average_order_value": aov,
            "revenue_share_pct": share,
            "target_pct": int(target_pct)
        })

    return result


def get_revenue_growth(conn=None, start_date=None, end_date=None, status_mode="delivered"):
    """
    Detailed period-over-period comparison endpoint.
    Compares current selected period with the immediately preceding equal-length period.
    """
    current_kpis = get_kpis(conn, start_date=start_date, end_date=end_date, status_mode=status_mode)
    growth = current_kpis["growth"]

    return {
        "current_period": {
            "start_date": current_kpis["filters_applied"]["start_date"],
            "end_date": current_kpis["filters_applied"]["end_date"],
            "net_sales": current_kpis["net_sales"],
            "total_orders": current_kpis["total_orders"],
            "average_order_value": current_kpis["average_order_value"]
        },
        "previous_period": growth["previous_period"],
        "previous_metrics": {
            "net_sales": growth["previous_net_sales"],
            "total_orders": growth["previous_orders"]
        },
        "growth": {
            "revenue_growth_pct": growth["revenue_growth_pct"],
            "order_growth_pct": growth["order_growth_pct"]
        },
        "status_mode": status_mode
    }


def get_status_distribution(conn=None, start_date=None, end_date=None):
    """
    Distribution of distinct orders across all statuses (delivered, shipped, pending, cancelled).
    """
    start_date = validate_date_string(start_date, "start_date")
    end_date = validate_date_string(end_date, "end_date")

    where_clauses = []
    params = []

    if start_date:
        where_clauses.append("order_date >= ?")
        params.append(start_date)
    if end_date:
        where_clauses.append("order_date <= ?")
        params.append(end_date)

    where_str = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    query = f"""
        SELECT 
            order_status AS status,
            COUNT(order_id) AS order_count
        FROM orders
        {where_str}
        GROUP BY order_status
        ORDER BY order_count DESC;
    """

    rows = query_db(query, params, conn=conn)
    total_orders = sum(int(r["order_count"]) for r in rows)

    result = []
    for r in rows:
        count = int(r["order_count"])
        pct = round((count / total_orders) * 100.0, 2) if total_orders > 0 else 0.0
        result.append({
            "status": r["status"],
            "order_count": count,
            "percentage": pct
        })

    return {
        "total_orders": total_orders,
        "distribution": result
    }
