# -*- coding: utf-8 -*-
import sys
from flask import Flask, render_template, request
from flask_cors import CORS
from routes.api import api_bp

from logs_db import init_db
from logs_bot import view_logs, retrieve_logs_by_date

app = Flask(__name__)
# Allow cross-origin requests (needed when calling this API from pages like https://ar.wikipedia.org)
CORS(
    app,
    resources={r"/api/*": {"origins": ["https://ar.wikipedia.org", "https://www.ar.wikipedia.org"]}},
)

# Register the API Blueprint
app.register_blueprint(api_bp)


@app.route("/no_result", methods=["GET"])
def render_no_results_page() -> str:
    # ---
    return render_template("no_result.html")


@app.route("/logs_by_day", methods=["GET"])
def render_daily_logs() -> str:
    # ---
    result = retrieve_logs_by_date(request)
    # ---
    return render_template(
        "logs_by_day.html",
        logs=result.get("logs", []),
        tab=result.get("tab", []),
        status_table=result.get("status_table", []),
        dbs=result.get("dbs", []),
    )


@app.route("/", methods=["GET"])
def render_index_page() -> str:
    return render_template("index.html")


@app.route("/logs", methods=["GET"])
def render_logs_view() -> str:
    # ---
    result = view_logs(request)
    # ---
    return render_template("logs.html", result=result)


@app.route("/list", methods=["GET"])
def render_title_list() -> str:
    return render_template("list.html")


@app.route("/chart", methods=["GET"])
def render_chart() -> str:
    return render_template("chart.html")


@app.route("/chart2", methods=["GET"])
def render_chart2() -> str:
    return render_template("chart2.html")


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
