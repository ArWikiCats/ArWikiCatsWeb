# -*- coding: utf-8 -*-
import json
import functools
import time

from flask import Blueprint, Response, request

try:
    from ArWikiCats import batch_resolve_labels, resolve_arabic_category_label  # type: ignore
except ImportError:
    batch_resolve_labels = None
    resolve_arabic_category_label = None

from ..config import settings
from ..handler import view_logs_request_handler
from ..logs_db import Database, LogsManager, LogsView
from ..logs_db.logs_bot import view_logs_new
from ..logs_db.logs_bot2 import view_logs_by_date, view_logs_en2ar


@functools.lru_cache(maxsize=1)
def load_data_manager() -> LogsManager:
    _manager = LogsManager(db=Database(settings.paths.db_path_main))
    return _manager


@functools.lru_cache(maxsize=1)
def load_logs_view() -> LogsView:
    _manager = load_data_manager()
    _viewer = LogsView(manager=_manager)
    return _viewer


def jsonify(data: dict) -> str:
    response_json = json.dumps(data, ensure_ascii=False, indent=4)
    return Response(response=response_json, content_type="application/json; charset=utf-8")


def check_user_agent(endpoint, data, start_time):
    _manager = load_data_manager()
    if not request.headers.get("User-Agent"):
        response_status = "User-Agent missing"
        _manager.log_request(endpoint, data, response_status, time.time() - start_time)
        return jsonify({"error": "User-Agent header is required"}), 400
    return None


def get_logs_by_day(table_name) -> str:

    result = view_logs_by_date(table_name)
    result = result.get("logs", [])

    return jsonify(result)


def get_logs_all(day=None) -> str:
    _viewer = load_logs_view()
    result = _viewer.view_logs_en2ar(day)
    return jsonify(result)


def get_logs_category(day=None) -> str:
    _viewer = load_logs_view()
    result = _viewer.view_logs_en2ar(day)

    if "no_result" in result:
        del result["no_result"]

    return jsonify(result)


def get_logs_no_result(day=None) -> str:
    _viewer = load_logs_view()
    result = _viewer.view_logs_en2ar(day)

    if "data_result" in result:
        del result["data_result"]

    return jsonify(result)


def get_status_table() -> str:
    _manager = load_data_manager()
    result = _manager.get_response_status()
    return jsonify(result)


def get_title(title) -> str:

    # Validate title parameter
    if not title or len(title) > 500:
        return jsonify({"error": "Invalid title"}), 400

    start_time = time.time()

    _manager = load_data_manager()

    # Check for User-Agent header
    ua_check = check_user_agent("/api/<title>", title, start_time)
    if ua_check:
        return ua_check

    if resolve_arabic_category_label is None:
        _manager.log_request("/api/<title>", title, "error", time.time() - start_time)
        return jsonify({"error": "حدث خطأ أثناء تحميل المكتبة"}), 500

    label = resolve_arabic_category_label(title)

    data = {"result": label}

    delta = time.time() - start_time

    data["sql"] = _manager.log_request("/api/<title>", title, label or "no_result", delta)

    return jsonify(data)


def get_titles(data):
    start_time = time.time()

    _manager = load_data_manager()
    if not isinstance(data, dict):
        delta = time.time() - start_time
        _manager.log_request("/api/list", None, "error", delta)
        return jsonify({"error": "No valid JSON payload provided"}), 400

    titles = data.get("titles", [])
    # Check for User-Agent header
    ua_check = check_user_agent("/api/list", titles, start_time)
    if ua_check:
        return ua_check

    # تأكد أن البيانات قائمة
    if not isinstance(titles, list):
        delta = time.time() - start_time
        _manager.log_request("/api/list", titles, "error", delta)
        return jsonify({"error": "بيانات غير صالحة"}), 400

    delta = time.time() - start_time

    len_titles = len(titles)
    titles = list(set(titles))
    duplicates = len_titles - len(titles)

    if batch_resolve_labels is None:
        _manager.log_request("/api/list", titles, "error", delta)
        return jsonify({"error": "حدث خطأ أثناء تحميل المكتبة"}), 500

    result = batch_resolve_labels(titles)

    len_result = len(result.labels)

    for x in result.no_labels:
        if x not in result.labels:
            result.labels[x] = ""

    delta2 = time.time() - start_time

    response_data = {
        "results": result.labels,
        "no_labs": len(result.no_labels),
        "with_labs": len_result,
        "duplicates": duplicates,
        "time": delta2,
    }

    # تحديد حالة الاستجابة
    response_status = "success" if len_result > 0 else "no_result"
    _manager.log_request("/api/list", titles, response_status, delta2)

    return jsonify(response_data)


class Api_Blueprint:
    def __init__(self, api_bp: Blueprint, allowed_tables):
        self.allowed_tables = allowed_tables

        @api_bp.route("/logs", methods=["GET"])
        def logs_api():
            data = view_logs_request_handler(request, self.allowed_tables)
            result = view_logs_new(data)
            return jsonify(result)

        @api_bp.route("/list", methods=["POST"])
        def _get_titles():
            data = request.get_json(silent=True)
            return get_titles(data)

        @api_bp.route("/<title>", methods=["GET"])
        def _get_title(title) -> str:
            return get_title(title)

        @api_bp.route("/status", methods=["GET"])
        def _get_status_table() -> str:
            return get_status_table()

        @api_bp.route("/no_result", methods=["GET"])
        @api_bp.route("/no_result/<day>", methods=["GET"])
        def _get_logs_no_result(day=None) -> str:
            return get_logs_no_result(day=day)

        @api_bp.route("/logs_by_day", methods=["GET"])
        def _get_logs_by_day() -> str:

            table_name = request.args.get("table_name", "")

            if table_name not in self.allowed_tables:
                table_name = "logs"

            return get_logs_by_day(table_name)

        @api_bp.route("/all", methods=["GET"])
        @api_bp.route("/all/<day>", methods=["GET"])
        def _get_logs_all(day=None) -> str:
            return get_logs_all(day=day)

        @api_bp.route("/category", methods=["GET"])
        @api_bp.route("/category/<day>", methods=["GET"])
        def _get_logs_category(day=None) -> str:
            return get_logs_category(day=day)
