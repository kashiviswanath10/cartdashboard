"""
CartCompass-BI - Application Configuration
Reads environment variables with secure defaults for local and production deployment.
"""

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent

class Config:
    """Base application configuration."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "cartcompass-dev-secret-key-default-2025")
    DATABASE_PATH = Path(os.environ.get("DATABASE_PATH", str(BASE_DIR / "cartcompass.db"))).resolve()
    DEFAULT_CURRENCY = os.environ.get("DEFAULT_CURRENCY", "₹")
    DEBUG = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1", "t")
    PORT = int(os.environ.get("PORT", 5000))
    HOST = os.environ.get("HOST", "127.0.0.1")
    FRONTEND_DIR = BASE_DIR / "frontend"
    CHART_OUTPUTS_DIR = BASE_DIR / "analysis" / "outputs"


class TestingConfig(Config):
    """Testing configuration with temporary database."""
    TESTING = True
    DEBUG = False
    DATABASE_PATH = BASE_DIR / "tests" / "test_cartcompass.db"
