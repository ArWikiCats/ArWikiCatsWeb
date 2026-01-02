# -*- coding: utf-8 -*-
import sys
from flask import Flask, render_template
from flask_cors import CORS
from routes.api import api_bp
from routes.ui import ui_bp

from logs_db import init_db

app = Flask(__name__)
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


if __name__ == "__main__":
    init_db()
    # ---
    debug = "debug" in sys.argv or "DEBUG" in sys.argv
    # ---
    app.run(debug=debug)
