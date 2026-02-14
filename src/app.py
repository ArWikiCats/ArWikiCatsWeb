"""
WSGI entry point for ArWikiCats web service.

This module serves as the main entry point for the Flask application,
suitable for both development and production deployments (e.g., on
Wikimedia Toolforge).

Usage:
    Development:
        $ cd src && python app.py           # Production mode
        $ cd src && python app.py debug     # Debug mode with auto-reload

    Production (via Flask CLI):
        $ flask --app src.app run --debug

    WSGI Server (gunicorn):
        $ gunicorn src.app:app

Environment:
    The application uses the following environment variables:
    - HOME: Used to determine the database storage location on Toolforge
             ($HOME/www/python/dbs/). Falls back to local directory if not set.
"""

from __future__ import annotations

import sys

from app import create_app  # noqa: E402 module level import
from app.logs_db import init_db  # noqa: E402 module level import

# Create the Flask application instance
app = create_app()

if __name__ == "__main__":
    """
    Run the development server.

    Initializes the database if needed and starts the Flask development
    server. Debug mode can be enabled by passing 'debug' as a command
    line argument.
    """
    # Ensure database tables exist
    init_db()

    # Check for debug mode
    debug = any(arg.lower() == "debug" for arg in sys.argv)

    # Run the server
    app.run(debug=debug)
