# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, request

from ..handler import view_logs_request_handler
from ..logs_db.logs_bot import retrieve_logs_by_date, view_logs_new


class Ui_Blueprint:
    def __init__(self, ui_bp: Blueprint, allowed_tables):
        self.allowed_tables = allowed_tables

        @ui_bp.route("/", methods=["GET"])
        def render_index_page() -> str:
            return render_template("index.html")

        @ui_bp.route("/logs", methods=["GET"])
        def render_logs_view() -> str:
            data = view_logs_request_handler(request, self.allowed_tables)
            result = view_logs_new(data)
            return render_template("logs.html", result=result)

        @ui_bp.route("/no_result", methods=["GET"])
        def render_no_results_page() -> str:
            return render_template("no_result.html")

        @ui_bp.route("/logs_by_day", methods=["GET"])
        def render_daily_logs() -> str:

            table_name = request.args.get("table_name", "")

            if table_name not in self.allowed_tables:
                table_name = "logs"

            result = retrieve_logs_by_date(table_name)

            return render_template(
                "logs_by_day.html",
                logs=result.get("logs", []),
                tab=result.get("tab", []),
                status_table=result.get("status_table", []),
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

        @ui_bp.route("/qids_batch_translate", methods=["GET"])
        def render_qids_batch_translate() -> str:
            return render_template("qids_batch_translate.html")
