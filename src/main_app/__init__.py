# -*- coding: utf-8 -*-
import os
from pathlib import Path

from flask import Blueprint, Flask, render_template
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from .config import settings
from .loader import load_database
from .logging_config import setup_logging
from .routes import Api_Blueprint, Ui_Blueprint

# Default log level can be overridden via LOG_LEVEL environment variable
log_level = os.getenv("LOG_LEVEL", "INFO")
setup_logging(
    level=log_level,
    name=Path(__file__).parent.name,
)


def create_app() -> Flask:
    """Instantiate and configure the Flask application."""
    # Create all required tables
    _db = load_database()
    _db.init_tables()

    # Create the Flask app
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )

    # Allow cross-origin requests (needed when calling this API from pages like https://ar.wikipedia.org)
    CORS(
        app,
        resources={r"/api/*": {"origins": ["https://ar.wikipedia.org", "https://www.ar.wikipedia.org"]}},
    )

    # Rate limiting to prevent abuse
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[settings.rate_limit],
        storage_uri="memory://",
    )
    limiter.init_app(app)

    # Request size limit (1MB max)
    app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024

    # CDN base URL for static assets (configurable via environment)
    app.config["CDN_BASE"] = os.getenv(
        "CDN_BASE",
        "https://tools-static.wmflabs.org/cdnjs/ajax/libs",
    )

    # Create the API Blueprint
    api_bp = Blueprint("api", __name__, url_prefix="/api")
    Api_Blueprint(api_bp, settings.allowed_tables)

    # Register the API Blueprint
    app.register_blueprint(api_bp)

    # Create the UI Blueprint
    ui_bp = Blueprint("ui", __name__)
    Ui_Blueprint(ui_bp, settings.allowed_tables)

    # Register the UI Blueprint
    app.register_blueprint(ui_bp)

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("error.html", tt="invalid_url", error=str(e)), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template("error.html", tt="unexpected_error", error=str(e)), 500

    return app
