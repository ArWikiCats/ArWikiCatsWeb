# -*- coding: utf-8 -*-
import time
from flask import Blueprint, request, Response
import json

import logs_db
import logs_bot

try:
    from ArWikiCats import batch_resolve_labels, resolve_arabic_category_label  # type: ignore
except ImportError:
    batch_resolve_labels = None
    resolve_arabic_category_label = None

# Create the API Blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')


def jsonify(data: dict) -> str:
    response_json = json.dumps(data, ensure_ascii=False, indent=4)
    return Response(response=response_json, content_type="application/json; charset=utf-8")


@api_bp.route("/logs_by_day", methods=["GET"])
def get_logs_by_day() -> str:
    result = logs_bot.retrieve_logs_by_date(request)
    result = result.get("logs", [])
    # ---
    return jsonify(result)


@api_bp.route("/all", methods=["GET"])
@api_bp.route("/all/<day>", methods=["GET"])
def get_logs_all(day=None) -> str:
    result = logs_bot.all_logs_en2ar(day)
    # ---
    return jsonify(result)


@api_bp.route("/category", methods=["GET"])
@api_bp.route("/category/<day>", methods=["GET"])
def get_logs_category(day=None) -> str:
    result = logs_bot.all_logs_en2ar(day)
    # ---
    if "no_result" in result:
        del result["no_result"]
    # ---
    return jsonify(result)


@api_bp.route("/no_result", methods=["GET"])
@api_bp.route("/no_result/<day>", methods=["GET"])
def get_logs_no_result(day=None) -> str:
    result = logs_bot.all_logs_en2ar(day)
    # ---
    if "data_result" in result:
        del result["data_result"]
    # ---
    return jsonify(result)


@api_bp.route("/status", methods=["GET"])
def get_status_table() -> str:
    result = logs_db.get_response_status()
    # ---
    return jsonify(result)


@api_bp.route("/<title>", methods=["GET"])
def get_title(title) -> str:
    # ---
    start_time = time.time()
    # ---
    # Check for User-Agent header
    if not request.headers.get("User-Agent"):
        response_status = "User-Agent missing"
        logs_db.log_request("/api/<title>", title, response_status, time.time() - start_time)
        return jsonify({"error": "User-Agent header is required"}), 400
    # ---
    if resolve_arabic_category_label is None:
        logs_db.log_request("/api/<title>", title, "error", time.time() - start_time)
        return jsonify({"error": "حدث خطأ أثناء تحميل المكتبة"})
    # ---
    label = resolve_arabic_category_label(title)
    # ---
    data = {"result": label}
    # ---
    delta = time.time() - start_time
    # ---
    data['sql'] = logs_db.log_request("/api/<title>", title, label or "no_result", delta)
    # ---
    return jsonify(data)


@api_bp.route("/list", methods=["POST"])
def get_titles():
    # ---
    start_time = time.time()
    data = request.get_json()
    titles = data.get("titles", [])
    # ---
    delta = time.time() - start_time
    # ---
    len_titles = len(titles)
    titles = list(set(titles))
    duplicates = len_titles - len(titles)
    # ---
    # Check for User-Agent header
    if not request.headers.get("User-Agent"):
        response_status = "User-Agent missing"
        logs_db.log_request("/api/list", titles, response_status, delta)
        return jsonify({"error": "User-Agent header is required"}), 400
    # ---
    # تأكد أن البيانات قائمة
    if not isinstance(titles, list):
        logs_db.log_request("/api/list", titles, "error", delta)
        return jsonify({"error": "بيانات غير صالحة"}), 400

    # print("get_titles:")
    # print(titles)

    if batch_resolve_labels is None:
        logs_db.log_request("/api/list", titles, "error", delta)
        return jsonify({"error": "حدث خطأ أثناء تحميل المكتبة"})
    # ---
    result = batch_resolve_labels(titles)
    # ---
    len_result = len(result.labels)
    # ---
    for x in result.no_labels:
        if x not in result.labels:
            result.labels[x] = ""
    # ---
    delta2 = time.time() - start_time
    # ---
    response_data = {"results": result.labels, "no_labs": len(result.no_labels), "with_labs": len_result, "duplicates": duplicates, "time": delta2}
    # ---
    # تحديد حالة الاستجابة
    response_status = "success" if len_result > 0 else "no_result"
    logs_db.log_request("/api/list", titles, response_status, delta2)
    # ---
    return jsonify(response_data)


@api_bp.route("/logs", methods=["GET"])
def logs_api():
    # ---
    result = logs_bot.view_logs(request)
    # ---
    return jsonify(result)
