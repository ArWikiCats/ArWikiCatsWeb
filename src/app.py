# -*- coding: utf-8 -*-
import sys
from flask import Flask, render_template, request
from flask_cors import CORS

import logs_db
import logs_bot
from routes.api import api_bp

sys.argv.append("noprint")


app = Flask(__name__)
# Allow cross-origin requests (needed when calling this API from pages like https://ar.wikipedia.org)
CORS(
    app,
    resources={r"/api/*": {"origins": ["https://ar.wikipedia.org", "https://www.ar.wikipedia.org"]}},
)

# Register the API Blueprint
app.register_blueprint(api_bp)


@app.route("/logs", methods=["GET"])
def view_logs():
    # ---
    result = logs_bot.view_logs(request)
    # ---
    return render_template("logs.html", result=result)


@app.route("/no_result", methods=["GET"])
def no_result():
    # ---
    return render_template("no_result.html")


@app.route("/logs_by_day", methods=["GET"])
def logs_by_day():
    # ---
    result = logs_bot.logs_by_day(request)
    # ---
    return render_template(
        "logs_by_day.html",
        logs=result.get("logs", []),
        tab=result.get("tab", []),
        status_table=result.get("status_table", []),
        dbs=result.get("dbs", []),
    )


@app.route("/", methods=["GET"])
def main() -> str:
    return render_template("index.html")


@app.route("/list", methods=["GET"])
def titles() -> str:
    return render_template("list.html")


@app.route("/chart", methods=["GET"])
def charts() -> str:
    return render_template("chart.html")


@app.route("/x", methods=["GET"])
def charts2() -> str:
    return render_template("x.html")


@app.errorhandler(404)
def page_not_found(e):
    return render_template("error.html", tt="invalid_url", error=str(e)), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template("error.html", tt="unexpected_error", error=str(e)), 500


if __name__ == "__main__":
    logs_db.init_db()
    # ---
    debug = "debug" in sys.argv or "DEBUG" in sys.argv
    # ---
    app.run(debug=debug)
