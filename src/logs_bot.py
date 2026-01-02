# -*- coding: utf-8 -*-

from pathlib import Path

import logs_db  # logs_db.change_db_path(file)

db_tables = ["logs", "list_logs"]


def view_logs(request):
    # ---
    db_path = request.args.get("db_path")
    # ---
    dbs = []
    # ---
    if db_path:
        dbs = logs_db.change_db_path(db_path)
        # ---
        db_path = db_path if db_path in dbs else "new_logs.db"
    # ---
    page = request.args.get("page", 1, type=int)
    # ---
    per_page = request.args.get("per_page", 10, type=int)
    order = request.args.get("order", "desc").upper()
    order_by = request.args.get("order_by", "response_count")
    # ---
    day = request.args.get("day", "")
    # ---
    status = request.args.get("status", "")
    like = request.args.get("like", "")
    # ---
    table_name = request.args.get("table_name", "")
    # ---
    if table_name not in db_tables:
        table_name = "logs"
    # ---
    # Validate values
    page = max(1, page)
    per_page = max(1, min(200, per_page))

    # Offset for pagination
    offset = (page - 1) * per_page
    # ---
    order_by_types = [
        "id",
        "endpoint",
        "request_data",
        "response_status",
        "response_time",
        "response_count",
        "timestamp",
        "date_only",
    ]
    # ---
    if order_by not in order_by_types:
        order_by = "timestamp"
    # ---
    # [{'response_status': 'no_result', 'numbers': 10066}, {'response_status': 'success', 'numbers': 12}
    # status_table = logs_db.get_response_status(table_name=table_name)
    status_table = ["no_result"]
    # ---
    status = status if (status in status_table or status == "Category") else ""
    # ---
    logs = logs_db.get_logs(
        per_page, offset, order, order_by=order_by, status=status, table_name=table_name, like=like, day=day
    )
    # ---
    # Convert to list of dicts
    log_list = []
    # ---
    for log in logs:
        # {'id': 1, 'endpoint': 'api', 'request_data': 'Category:1934-35 in Bulgarian football', 'response_status': 'true', 'response_time': 123123.0, 'response_count': 6, 'timestamp': '2025-04-10 01:08:58'}
        # ---
        request_data = log["request_data"].replace("_", " ")
        # ---
        # 2025-04-23 21:13:18
        timestamp = log["timestamp"].split(" ")[1]
        # ---
        log_list.append(
            {
                "id": log["id"],
                "endpoint": log["endpoint"],
                "request_data": request_data,
                "response_status": log["response_status"],
                "response_time": log["response_time"],
                "response_count": log["response_count"],
                "timestamp": timestamp,
                "date_only": log["date_only"],
            }
        )
    # ---
    total_logs = logs_db.count_all(status=status, table_name=table_name, like=like)
    # ---
    # Pagination calculations
    total_pages = (total_logs + per_page - 1) // per_page
    start_log = (page - 1) * per_page + 1
    end_log = min(page * per_page, total_logs)
    start_page = max(1, page - 2)
    end_page = min(start_page + 4, total_pages)
    start_page = max(1, end_page - 4)
    # ---
    sum_all = logs_db.sum_response_count(status=status, table_name=table_name, like=like)
    # ---
    if status == "":
        status = "All"
    # ---
    table_new = {
        "sum_all": f"{sum_all:,}",
        "db_path": db_path,
        "table_name": table_name,
        "total_pages": total_pages,
        "total_logs": f"{total_logs:,}",
        "start_log": start_log,
        "end_log": end_log,
        "start_page": start_page,
        "end_page": end_page,
        "order": order,
        "order_by": order_by,
        "per_page": per_page,
        "page": page,
        "status": status,
        "like": like,
        "day": day,
    }
    # ---
    if "All" not in status_table:
        status_table.append("All")
    # ---
    if "Category" not in status_table:
        status_table.append("Category")
    # ---
    result = {
        "dbs": dbs,
        "logs": log_list,
        "order_by_types": order_by_types,
        "tab": table_new,
        "status_table": status_table,
    }
    # ---
    return result


def logs_by_day(request):
    # ---
    db_path = request.args.get("db_path")
    # ---
    dbs = []
    # ---
    if db_path:
        dbs = logs_db.change_db_path(db_path)
        # ---
        db_path = db_path if db_path in dbs else "new_logs.db"
    # ---
    table_name = request.args.get("table_name", "")
    # ---
    if table_name not in db_tables:
        table_name = "logs"
    # ---
    logs_data = logs_db.logs_by_day(table_name=table_name)
    # ---
    data_logs = {}
    # ---
    # [ { "date_only": "2025-06-06", "status_group": "no_result", "count": 2 }, { "date_only": "2025-06-06", "status_group": "Category", "count": 1 } ]
    # ---
    for x in logs_data:
        day = x["date_only"]
        # ---
        data_logs.setdefault(day, {"day": day, "title_count": 0, "results": {"no_result": 0, "Category": 0}})
        # ---
        data_logs[day]["title_count"] += x["title_count"]
        # ---
        data_logs[day]["results"][x["status_group"]] = x["count"]
    # ---
    logs = []
    # ---
    sum_all = 0
    # ---
    for day, results_keys in data_logs.items():
        total = sum(results_keys["results"].values())
        sum_all += total
        # ---
        results_keys["total"] = total
        # ---
        logs.append(results_keys)
    # ---
    # sort logs by total
    # logs.sort(key=lambda x: x["total"], reverse=True)
    # ---
    # sort logs by day
    logs.sort(key=lambda x: x["day"], reverse=False)
    # ---
    data = {
        "dbs": dbs,
        "logs_data": logs_data,
        "logs": logs,
        "tab": {
            "sum_all": f"{sum_all:,}",
            "db_path": db_path,
            "table_name": table_name,
            # "order": order,
            # "order_by": order_by,
        },
    }
    # ---
    return data


def all_logs_en2ar(day=None):
    # ---
    logs_data = logs_db.all_logs_en2ar(day=day)
    # ---
    data_no_result = [x for x, v in logs_data.items() if v == "no_result"]
    data_result = {x: v for x, v in logs_data.items() if v != "no_result"}
    # ---
    sum_all = len(logs_data)
    # ---
    data = {
        "tab": {
            "sum_all": f"{sum_all:,}",
            "sum_data_result": f"{len(data_result):,}",
            "sum_no_result": f"{len(data_no_result):,}",
        },
        "no_result": data_no_result,
        "data_result": data_result,
    }
    # ---
    return data
