# -*- coding: utf-8 -*-
"""
Flask application factory module.

This module provides the application factory pattern for creating Flask
application instances. It handles:
- Blueprint registration
- CORS configuration
- Error handler registration
- Logging setup

Architecture:
    The application factory pattern allows for:
    - Multiple application instances (useful for testing)
    - Deferred configuration
    - Easier testing with different configs

Example:
    >>> from app import create_app
    >>> app = create_app()
    >>> app.run()
"""

from __future__ import annotations

from pathlib import Path

from flask import Flask, render_template
from flask_cors import CORS

from .logging_config import setup_logging
from .routes import api_bp, ui_bp

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

# Initialize logging when the module is imported
setup_logging(
    level="DEBUG",
    name=Path(__file__).parent.name,
)


# =============================================================================
# APPLICATION FACTORY
# =============================================================================

def create_app() -> Flask:
    """
    Create and configure the Flask application instance.

    This function implements the application factory pattern, creating a new
    Flask application with all necessary configuration, blueprints, and error
    handlers registered.

    Configuration:
        - Template folder: ../templates (relative to this file)
        - Static folder: ../static (relative to this file)
        - CORS: Enabled for ar.wikipedia.org on /api/* routes

    Registered Blueprints:
        - api_bp: REST API endpoints at /api/*
        - ui_bp: Web UI endpoints at /

    Error Handlers:
        - 404: Renders error.html with "invalid_url" message
        - 500: Renders error.html with "unexpected_error" message

    Returns:
        Flask: Configured Flask application instance ready to run.

    Example:
        >>> app = create_app()
        >>> client = app.test_client()
        >>> response = client.get('/')
        >>> response.status_code
        200
    """
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )

    # Configure CORS for API routes
    # This allows the API to be called from Arabic Wikipedia pages
    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": [
                    "https://ar.wikipedia.org",
                    "https://www.ar.wikipedia.org",
                ],
            },
        },
    )

    # Register the API Blueprint (handles /api/* routes)
    app.register_blueprint(api_bp)

    # Register the UI Blueprint (handles /* routes)
    app.register_blueprint(ui_bp)

    # Register error handlers
    @app.errorhandler(404)
    def page_not_found(error: Exception) -> tuple[str, int]:
        """
        Handle 404 Not Found errors.

        Args:
            error: The exception that triggered the error handler.

        Returns:
            tuple[str, int]: Rendered error page and HTTP status code.
        """
        return render_template("error.html", tt="invalid_url", error=str(error)), 404

    @app.errorhandler(500)
    def internal_server_error(error: Exception) -> tuple[str, int]:
        """
        Handle 500 Internal Server Error.

        Args:
            error: The exception that triggered the error handler.

        Returns:
            tuple[str, int]: Rendered error page and HTTP status code.
        """
        return render_template("error.html", tt="unexpected_error", error=str(error)), 500

    return app
