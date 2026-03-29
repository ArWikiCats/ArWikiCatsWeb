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


def view_logs(request):

    page = request.args.get("page", 1, type=int)

    per_page = request.args.get("per_page", 10, type=int)
    order = request.args.get("order", "desc").upper()
    order_by = request.args.get("order_by", "response_count")

    day = request.args.get("day", "")

    status = request.args.get("status", "")
    like = request.args.get("like", "")

    table_name = request.args.get("table_name", "")

    if table_name not in settings.allowed_tables:
        table_name = "logs"

    # Validate values
    page = max(1, page)
    per_page = max(1, min(200, per_page))

    # Offset for pagination
    offset = (page - 1) * per_page

    result = _view_logs(page, per_page, order, order_by, day, status, like, table_name, offset)

    return result


def _view_logs(page, per_page, order, order_by, day, status, like, table_name, offset):
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

    _manager = load_data_manager()
    if order_by not in order_by_types:
        order_by = "timestamp"

    status_table = ["no_result"]

    status = status if (status in status_table or status == "Category") else ""

    logs = _manager.get_logs(
        per_page,
        offset,
        order,
        order_by=order_by,
        status=status,
        table_name=table_name,
        like=like,
        day=day
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

    total_logs = _manager.count_all(status=status, table_name=table_name, like=like)

    # Pagination calculations
    total_pages = (total_logs + per_page - 1) // per_page
    start_log = (page - 1) * per_page + 1
    end_log = min(page * per_page, total_logs)
    start_page = max(1, page - settings.pagination_window)
    end_page = min(start_page + settings.max_visible_pages, total_pages)
    start_page = max(1, end_page - settings.max_visible_pages)

    sum_all = _manager.sum_response_count(status=status, table_name=table_name, like=like)

    if status == "":
        status = "All"

    table_new = {
        "sum_all": f"{sum_all:,}",
        "table_name": table_name,
        "total_pages": total_pages,

        # summary
        "total_logs": f"{total_logs:,}",
        "start_log": start_log,
        "end_log": end_log,

        # pagination
        "start_page": start_page,
        "end_page": end_page,
        "per_page": per_page,

        "order": order,
        "order_by": order_by,
        "page": page,
        "status": status,
        "like": like,
        "day": day,
    }

    if "All" not in status_table:
        status_table.append("All")

    if "Category" not in status_table:
        status_table.append("Category")

    result = {
        "logs": log_list,
        "order_by_types": order_by_types,
        "tab": table_new,
        "status_table": status_table,
    }

    return result


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

        # summary
        "total_logs": f"{total_logs:,}",
        "start_log": start_log,
        "end_log": end_log,

        # pagination
        "start_page": start_page,
        "end_page": end_page,
        "per_page": data.per_page,

        "order": data.order,
        "order_by": data.order_by,
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
