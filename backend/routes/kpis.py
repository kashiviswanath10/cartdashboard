"""
CartCompass-BI - KPI API Routes
Provides endpoints for summary KPIs and performance indicators.
"""

from flask import Blueprint, request, jsonify
from backend.services.analytics import get_kpis

kpis_bp = Blueprint("kpis", __name__)


@kpis_bp.route("/kpis", methods=["GET"])
def fetch_kpis():
    """
    GET /api/kpis
    Optional Query Parameters:
    - start_date (YYYY-MM-DD)
    - end_date (YYYY-MM-DD)
    - status_mode ('delivered' [default], 'all_active', 'all')
    """
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    status_mode = request.args.get("status_mode", "delivered").lower()

    try:
        data = get_kpis(
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
            "message": "An error occurred while computing KPIs."
        }), 500
