# -*- coding: utf-8 -*-

import functools

from ..config import settings
from ..handler import ViewLogsRequestHandler
from .bot import LogsManager
from .db import Database


@functools.lru_cache(maxsize=1)
def load_data_manager() -> LogsManager:
    _manager = LogsManager(db=Database(settings.paths.db_path_main))
    return _manager


def view_logs_new(data: ViewLogsRequestHandler):

    _manager = load_data_manager()
    status_table = ["no_result", "All", "Category"]

    logs = _manager.get_logs(
        data.per_page,
        data.offset,
        data.order,
        order_by=data.order_by,
        status=data.status,
        table_name=data.table_name,
        like=data.like,
        day=data.day,
    )

    # Convert to list of dicts
    log_list = []

    for log in logs:
        # {'id': 1, 'endpoint': 'api', 'request_data': 'Category:1934-35 in Bulgarian football', 'response_status': 'true', 'response_time': 123123.0, 'response_count': 6, 'timestamp': '2025-04-10 01:08:58'}
        request_data = log["request_data"].replace("_", " ")

        # 2025-04-23 21:13:18
        timestamp = log["timestamp"].split(" ")[1]

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

    total_logs = _manager.count_all(status=data.status, table_name=data.table_name, like=data.like)

    # Pagination calculations
    total_pages = (total_logs + data.per_page - 1) // data.per_page
    start_log = (data.page - 1) * data.per_page + 1
    end_log = min(data.page * data.per_page, total_logs)
    start_page = max(1, data.page - settings.pagination_window)
    end_page = min(start_page + settings.max_visible_pages, total_pages)
    start_page = max(1, end_page - settings.max_visible_pages)

    sum_all = _manager.sum_response_count(status=data.status, table_name=data.table_name, like=data.like)

    status = data.status or "All"

    table_new = {
        "sum_all": f"{sum_all:,}",
        "table_name": data.table_name,
        "total_pages": total_pages,
        "total_logs": f"{total_logs:,}",
        "start_log": start_log,
        "end_log": end_log,
        "start_page": start_page,
        "end_page": end_page,
        "order": data.order,
        "order_by": data.order_by,
        "per_page": data.per_page,
        "page": data.page,
        "status": status,
        "like": data.like,
        "day": data.day,
    }

    result = {
        "logs": log_list,
        "order_by_types": data.order_by_types,
        "tab": table_new,
        "status_table": status_table,
    }

    return result


def retrieve_logs_by_date(table_name):

    _manager = load_data_manager()

    logs_data = _manager.fetch_logs_by_date(table_name=table_name)

    data_logs = {}

    # [ { "date_only": "2025-06-06", "status_group": "no_result", "count": 2 }, { "date_only": "2025-06-06", "status_group": "Category", "count": 1 } ]

    for x in logs_data:
        day = x["date_only"]

        data_logs.setdefault(day, {"day": day, "title_count": 0, "results": {"no_result": 0, "Category": 0}})

        data_logs[day]["title_count"] += x["title_count"]

        data_logs[day]["results"][x["status_group"]] = x["count"]

    logs = []

    sum_all = 0

    for day, results_keys in data_logs.items():
        total = sum(results_keys["results"].values())
        sum_all += total

        results_keys["total"] = total

        logs.append(results_keys)

    # sort logs by total
    # logs.sort(key=lambda x: x["total"], reverse=True)

    # sort logs by day
    logs.sort(key=lambda x: x["day"], reverse=False)

    data = {
        "logs_data": logs_data,
        "logs": logs,
        "tab": {
            "sum_all": f"{sum_all:,}",
            "table_name": table_name,
            # "order": order,
            # "order_by": order_by,
        },
    }

    return data


def retrieve_logs_en_to_ar(day=None):

    _manager = load_data_manager()

    logs_data = _manager.all_logs_en2ar(day=day)

    data_no_result = [x for x, v in logs_data.items() if v == "no_result"]
    data_result = {x: v for x, v in logs_data.items() if v != "no_result"}

    sum_all = len(logs_data)

    data = {
        "tab": {
            "sum_all": f"{sum_all:,}",
            "sum_data_result": f"{len(data_result):,}",
            "sum_no_result": f"{len(data_no_result):,}",
        },
        "no_result": data_no_result,
        "data_result": data_result,
    }

    return data
