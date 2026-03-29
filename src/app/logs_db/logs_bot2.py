# -*- coding: utf-8 -*-

import functools

from ..config import settings
from .bot import LogsManager
from .db import Database


@functools.lru_cache(maxsize=1)
def load_data_manager() -> LogsManager:
    _manager = LogsManager(db=Database(settings.paths.db_path_main))
    return _manager


def view_logs_by_date(table_name):

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


def view_logs_en2ar(day=None):

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
