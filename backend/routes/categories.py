"""
CartCompass-BI - Category API Routes
Provides endpoints for product category revenue analysis and share breakdown.
"""

from flask import Blueprint, request, jsonify
from backend.services.analytics import get_category_revenue

categories_bp = Blueprint("categories", __name__)


@categories_bp.route("/categories", methods=["GET"])
def fetch_category_revenue():
    """
    GET /api/categories
    Optional Query Parameters:
    - start_date (YYYY-MM-DD)
    - end_date (YYYY-MM-DD)
    - status_mode ('delivered' [default], 'all_active', 'all')
    """
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    status_mode = request.args.get("status_mode", "delivered").lower()

    try:
        data = get_category_revenue(
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
            "message": "An error occurred while fetching category revenue."
        }), 500
