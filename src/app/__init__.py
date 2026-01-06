# -*- coding: utf-8 -*-
import sys

from flask import Flask, render_template
from flask_cors import CORS

from .routes import api_bp, ui_bp


def create_app() -> Flask:
    """Instantiate and configure the Flask application."""

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

    # Register the API Blueprint
    app.register_blueprint(api_bp)

    # Register the UI Blueprint
    app.register_blueprint(ui_bp)

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("error.html", tt="invalid_url", error=str(e)), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template("error.html", tt="unexpected_error", error=str(e)), 500

    return app
