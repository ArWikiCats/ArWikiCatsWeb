"""WSGI entry point for SVG Translate."""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

load_dotenv()

# Allow custom path for categories_bot via environment variable
custom_path = os.getenv("ARWIKICATS_PATH", "")
if custom_path:
    sys.path.insert(0, custom_path)

from main_app import create_app  # noqa: E402

app = create_app()

if __name__ == "__main__":
    debug = any(arg.lower() == "debug" for arg in sys.argv)
    app.run(debug=debug)
