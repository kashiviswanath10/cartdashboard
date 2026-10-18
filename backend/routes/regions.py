"""
CartCompass-BI - Regional API Routes
Provides endpoints for regional sales performance and order volume.
"""

from flask import Blueprint, request, jsonify
from backend.services.analytics import get_regional_revenue

regions_bp = Blueprint("regions", __name__)


@regions_bp.route("/regions", methods=["GET"])
def fetch_regional_revenue():
    """
    GET /api/regions
    Optional Query Parameters:
    - start_date (YYYY-MM-DD)
    - end_date (YYYY-MM-DD)
    - status_mode ('delivered' [default], 'all_active', 'all')
    """
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    status_mode = request.args.get("status_mode", "delivered").lower()

    try:
        data = get_regional_revenue(
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
            "message": "An error occurred while fetching regional revenue."
        }), 500
