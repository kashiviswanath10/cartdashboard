"""
CartCompass-BI - Flask Application Factory & Server
Main application entry point providing RESTful BI endpoints and serving the dashboard UI.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory, render_template_string

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.config import Config
from backend.db import close_db, get_db_connection, query_db
from backend.routes.kpis import kpis_bp
from backend.routes.revenue import revenue_bp
from backend.routes.categories import categories_bp
from backend.routes.regions import regions_bp
from backend.services.analytics import get_status_distribution


def create_app(config_class=Config):
    """
    Application Factory Pattern for CartCompass-BI.
    Configures database teardown, registers blueprints, and handles static frontend delivery.
    """
    app = Flask(
        __name__,
        static_folder=str(BASE_DIR / "frontend"),
        static_url_path=""
    )
    app.config.from_object(config_class)

    # Register Database teardown hook
    app.teardown_appcontext(close_db)

    # Register API Blueprints
    app.register_blueprint(kpis_bp, url_prefix="/api")
    app.register_blueprint(revenue_bp, url_prefix="/api")
    app.register_blueprint(categories_bp, url_prefix="/api")
    app.register_blueprint(regions_bp, url_prefix="/api")

    # Health Check Endpoint
    @app.route("/api/health", methods=["GET"])
    def health_check():
        try:
            conn = get_db_connection(app.config["DATABASE_PATH"])
            p_count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
            o_count = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
            i_count = conn.execute("SELECT COUNT(*) FROM order_items").fetchone()[0]
            conn.close()

            return jsonify({
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "database": {
                    "connected": True,
                    "engine": "SQLite",
                    "path": str(app.config["DATABASE_PATH"]),
                    "records": {
                        "products": p_count,
                        "orders": o_count,
                        "order_items": i_count
                    }
                },
                "service": "CartCompass-BI Engine",
                "version": "1.0.0"
            }), 200
        except Exception as e:
            return jsonify({
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "database": {
                    "connected": False,
                    "error": "Database connection or table verification failed."
                }
            }), 503

    # Order Status Distribution Endpoint
    @app.route("/api/status-distribution", methods=["GET"])
    def fetch_status_distribution():
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        try:
            data = get_status_distribution(start_date=start_date, end_date=end_date)
            return jsonify({
                "status": "success",
                "data": data
            }), 200
        except ValueError as e:
            return jsonify({"status": "error", "message": str(e)}), 400
        except Exception:
            return jsonify({"status": "error", "message": "Failed to fetch status distribution."}), 500

    # Static Matplotlib Charts Serving Endpoint
    @app.route("/api/chart-images/<path:filename>", methods=["GET"])
    def serve_chart_image(filename):
        outputs_dir = app.config.get("CHART_OUTPUTS_DIR", BASE_DIR / "analysis" / "outputs")
        return send_from_directory(str(outputs_dir), filename)

    # Root route - serves the dashboard
    @app.route("/", methods=["GET"])
    def serve_dashboard():
        frontend_dir = app.config.get("FRONTEND_DIR", BASE_DIR / "frontend")
        return send_from_directory(str(frontend_dir), "index.html")

    # Static frontend files (CSS, JS, Assets)
    @app.route("/<path:path>", methods=["GET"])
    def serve_frontend_static(path):
        frontend_dir = app.config.get("FRONTEND_DIR", BASE_DIR / "frontend")
        file_path = frontend_dir / path
        if file_path.exists() and file_path.is_file():
            return send_from_directory(str(frontend_dir), path)
        return jsonify({"status": "error", "message": f"Resource not found: {path}"}), 404

    # JSON Error Handlers for API endpoints
    @app.errorhandler(400)
    def bad_request(e):
        if request.path.startswith("/api/"):
            return jsonify({"status": "error", "error": "Bad Request", "message": str(e)}), 400
        return "Bad Request", 400

    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith("/api/"):
            return jsonify({"status": "error", "error": "Not Found", "message": "The requested API endpoint was not found."}), 404
        return "Not Found", 404

    @app.errorhandler(500)
    def internal_error(e):
        if request.path.startswith("/api/"):
            return jsonify({"status": "error", "error": "Internal Server Error", "message": "An unexpected server error occurred."}), 500
        return "Internal Server Error", 500

    return app


app = create_app()

if __name__ == "__main__":
    port = Config.PORT
    host = Config.HOST
    print(f"Starting CartCompass-BI on http://{host}:{port}")
    app.run(host=host, port=port, debug=Config.DEBUG)
