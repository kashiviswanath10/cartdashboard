"""
CartCompass-BI - Revenue API Routes
Provides endpoints for monthly revenue trends and period-over-period growth metrics.
"""

from flask import Blueprint, request, jsonify
from backend.services.analytics import get_monthly_revenue, get_revenue_growth

revenue_bp = Blueprint("revenue", __name__)


@revenue_bp.route("/revenue/monthly", methods=["GET"])
def fetch_monthly_revenue():
    """
    GET /api/revenue/monthly
    Optional Query Parameters:
    - start_date (YYYY-MM-DD)
    - end_date (YYYY-MM-DD)
    - status_mode ('delivered' [default], 'all_active', 'all')
    """
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    status_mode = request.args.get("status_mode", "delivered").lower()

    try:
        data = get_monthly_revenue(
            start_date=start_date,
            end_date=end_date,
            status_mode=status_mode
        )
        return jsonify({
            "status": "success",
            "count": len(data),
            "data": data
        }), 200
    except ValueError as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "An error occurred while fetching monthly revenue."
        }), 500


@revenue_bp.route("/revenue/growth", methods=["GET"])
def fetch_revenue_growth():
    """
    GET /api/revenue/growth
    Compares current period with preceding equal-length period.
    Optional Query Parameters:
    - start_date (YYYY-MM-DD)
    - end_date (YYYY-MM-DD)
    - status_mode ('delivered' [default], 'all_active', 'all')
    """
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    status_mode = request.args.get("status_mode", "delivered").lower()

    try:
        data = get_revenue_growth(
            start_date=start_date,
            end_date=end_date,
            status_mode=status_mode
        )
        return jsonify({
            "status": "success",
            "data": data
        }), 200
    except ValueError as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "An error occurred while calculating revenue growth."
        }), 500
