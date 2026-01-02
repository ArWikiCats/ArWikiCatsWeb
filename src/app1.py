"""
Used only in local development to run the app directly.
"""

from __future__ import annotations

import sys
sys.path.insert(0, "D:/categories_bot/make2_new")  # noqa: E402

from app import create_app              # noqa: E402
from app.logs_db import init_db

app = create_app()

if __name__ == "__main__":
    init_db()
    debug = "debug" in sys.argv or "DEBUG" in sys.argv
    app.run(debug=debug)
