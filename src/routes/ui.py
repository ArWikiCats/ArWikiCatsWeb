# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, request

from logs_bot import view_logs, retrieve_logs_by_date

# Create the UI Blueprint
ui_bp = Blueprint('ui', __name__)


@ui_bp.route("/", methods=["GET"])
def render_index_page() -> str:
    return render_template("index.html")


@ui_bp.route("/logs", methods=["GET"])
def render_logs_view() -> str:
    # ---
    result = view_logs(request)
    # ---
    return render_template("logs.html", result=result)


@ui_bp.route("/no_result", methods=["GET"])
def render_no_results_page() -> str:
    # ---
    return render_template("no_result.html")


@ui_bp.route("/logs_by_day", methods=["GET"])
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


@ui_bp.route("/list", methods=["GET"])
def render_title_list() -> str:
    return render_template("list.html")


@ui_bp.route("/chart", methods=["GET"])
def render_chart() -> str:
    return render_template("chart.html")


@ui_bp.route("/chart2", methods=["GET"])
def render_chart2() -> str:
    return render_template("chart2.html")
