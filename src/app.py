"""WSGI entry point for SVG Translate."""

from __future__ import annotations

import sys
from app import create_app              # noqa: E402
from app.logs_db import init_db

app = create_app()

if __name__ == "__main__":
    init_db()
    debug = "debug" in sys.argv or "DEBUG" in sys.argv
    app.run(debug=debug)
