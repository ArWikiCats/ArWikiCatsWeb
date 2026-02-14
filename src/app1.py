"""
Local development entry point for ArWikiCats web service.

This module is an alternative entry point for local development only.
It allows running the application directly with additional debug options.

WARNING: Do not use this file in production. Use app.py instead.

Usage:
    $ cd src && python app1.py           # Production mode
    $ cd src && python app1.py debug     # Debug mode
    $ cd src && python app1.py DEBUG     # Debug mode (alternative)
"""

from __future__ import annotations

import sys

# Note: The following line was removed as it contained a hardcoded absolute path.
# If you need to add a custom module path, use a relative path or environment variable:
# sys.path.insert(0, str(Path(__file__).parent.parent / "custom_module"))

from app import create_app  # noqa: E402 module level import
from app.logs_db import init_db  # noqa: E402 module level import

# Create the Flask application instance
app = create_app()


def main() -> None:
    """
    Run the development server.

    Initializes the database if needed and starts the Flask development
    server. Debug mode can be enabled by passing 'debug' or 'DEBUG' as
    a command line argument.
    """
    # Ensure database tables exist
    init_db()

    # Check for debug mode (case-insensitive)
    debug = "debug" in sys.argv or "DEBUG" in sys.argv

    # Run the server
    app.run(debug=debug)


if __name__ == "__main__":
    main()
