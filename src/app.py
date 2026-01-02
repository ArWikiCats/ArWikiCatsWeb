# -*- coding: utf-8 -*-
import json
import sys
import time

from flask import Flask, Response, render_template, request
from flask_cors import CORS

import logs_bot
import logs_db

sys.argv.append("noprint")

try:
    from ArWikiCats import batch_resolve_labels, resolve_arabic_category_label
except ImportError:
    batch_resolve_labels = None
    resolve_arabic_category_label = None


app = Flask(__name__)
# Allow cross-origin requests (needed when calling this API from pages like https://ar.wikipedia.org)
CORS(
    app,
    resources={r"/api/*": {"origins": ["https://ar.wikipedia.org", "https://www.ar.wikipedia.org"]}},
)


def jsonify(data: dict) -> str:
    response_json = json.dumps(data, ensure_ascii=False, indent=4)
    return Response(response=response_json, content_type="application/json; charset=utf-8")


@app.route("/api/logs_by_day", methods=["GET"])
def get_logs_by_day() -> str:
    result = logs_bot.logs_by_day(request)
    result = result.get("logs", [])
    # ---
    return jsonify(result)


@app.route("/api/all", methods=["GET"])
@app.route("/api/all/<day>", methods=["GET"])
def get_logs_all(day=None) -> str:
    result = logs_bot.all_logs_en2ar(day)
    # ---
    return jsonify(result)


@app.route("/api/category", methods=["GET"])
@app.route("/api/category/<day>", methods=["GET"])
def get_logs_category(day=None) -> str:
    result = logs_bot.all_logs_en2ar(day)
    # ---
    if "no_result" in result:
        del result["no_result"]
    # ---
    return jsonify(result)


@app.route("/api/no_result", methods=["GET"])
@app.route("/api/no_result/<day>", methods=["GET"])
def get_logs_no_result(day=None) -> str:
    result = logs_bot.all_logs_en2ar(day)
    # ---
    if "data_result" in result:
        del result["data_result"]
    # ---
    return jsonify(result)


@app.route("/api/status", methods=["GET"])
def get_status_table() -> str:
    result = logs_db.get_response_status()
    # ---
    return jsonify(result)


@app.route("/api/<title>", methods=["GET"])
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
    data["sql"] = logs_db.log_request("/api/<title>", title, label or "no_result", delta)
    # ---
    return jsonify(data)


@app.route("/api/list", methods=["POST"])
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
    response_data = {
        "results": result.labels,
        "no_labs": len(result.no_labels),
        "with_labs": len_result,
        "duplicates": duplicates,
        "time": delta2,
    }
    # ---
    # تحديد حالة الاستجابة
    response_status = "success" if len_result > 0 else "no_result"
    logs_db.log_request("/api/list", titles, response_status, delta2)
    # ---
    return jsonify(response_data)


@app.route("/api/logs", methods=["GET"])
def logs_api():
    # ---
    result = logs_bot.view_logs(request)
    # ---
    return jsonify(result)


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
