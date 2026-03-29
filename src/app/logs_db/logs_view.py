# -*- coding: utf-8 -*-
"""
from .logs_view import LogsView
"""
import functools
import logging

from ..config import settings
from ..handler import ViewLogsRequestHandler
from .bot import LogsManager
from .db import Database

logger = logging.getLogger(__name__)


# ── singleton factory ───────────────────────────────────────────────────────

@functools.lru_cache(maxsize=1)
def _get_manager() -> LogsManager:
    return LogsManager(db=Database(settings.paths.db_path_main))


# ── helpers ─────────────────────────────────────────────────────────────────

def _format_log_row(log: dict) -> dict:
    """Normalise a raw DB row into a clean display-ready dict."""
    return {
        "id": log["id"],
        "endpoint": log["endpoint"],
        "request_data": log["request_data"].replace("_", " "),
        "response_status": log["response_status"],
        "response_time": log["response_time"],
        "response_count": log["response_count"],
        "timestamp": log["timestamp"].split(" ")[1],   # keep HH:MM:SS only
        "date_only": log["date_only"],
    }


def _build_date_index(logs_data: list[dict]) -> list[dict]:
    """
    Pivot flat DB rows into a per-day summary list.

    Input:  [{"date_only": "2025-06-06", "status_group": "no_result", "count": 2}, …]
    Output: [{"day": "2025-06-06", "title_count": N, "total": N, "results": {…}}, …]
    """
    index: dict[str, dict] = {}

    for row in logs_data:
        day = row["date_only"]
        index.setdefault(
            day,
            {"day": day, "title_count": 0, "results": {"no_result": 0, "Category": 0}},
        )
        index[day]["title_count"] += row["title_count"]
        index[day]["results"][row["status_group"]] = row["count"]

    result = []
    for entry in index.values():
        entry["total"] = sum(entry["results"].values())
        result.append(entry)

    result.sort(key=lambda x: x["day"])
    return result


# ── main class ──────────────────────────────────────────────────────────────

class LogsView:
    """
    Presentation layer for logs data.
    Transforms raw LogsManager output into view-ready payloads.
    """

    def __init__(self, manager: LogsManager = None):
        self._m = manager or _get_manager()

    # ────────────────────────── paginated logs ──────────────────────────

    def view_logs(self, data: ViewLogsRequestHandler) -> dict:
        """
        Return a fully-prepared payload for the paginated logs view.

        Keys: logs, order_by_types, status_table, tab
        """
        logs = [
            _format_log_row(row)
            for row in self._m.get_logs(
                per_page=data.per_page,
                offset=data.offset,
                order=data.order,
                order_by=data.order_by,
                status=data.status,
                table_name=data.table_name,
                day=data.day,
            )
        ]

        total_logs = self._m.count_all(status=data.status, table_name=data.table_name)
        sum_all = self._m.sum_response_count(status=data.status, table_name=data.table_name)

        # ── pagination ──
        total_pages = (total_logs + data.per_page - 1) // data.per_page
        start_page = max(1, data.page - settings.pagination_window)
        end_page = min(start_page + settings.max_visible_pages, total_pages)
        start_page = max(1, end_page - settings.max_visible_pages)

        return {
            "logs": logs,
            "order_by_types": data.order_by_types,
            "status_table": data.status_table,
            "tab": {
                "sum_all": f"{sum_all:,}",
                "table_name": data.table_name,
                "total_logs": f"{total_logs:,}",
                "total_pages": total_pages,
                "start_log": (data.page - 1) * data.per_page + 1,
                "end_log": min(data.page * data.per_page, total_logs),
                "start_page": start_page,
                "end_page": end_page,
                "per_page": data.per_page,
                "order": data.order,
                "order_by": data.order_by,
                "page": data.page,
                "status": data.status or "All",
                "day": data.day,
            },
        }

    # ──────────────────────────── by date ───────────────────────────────

    def view_logs_by_date(self, table_name: str) -> dict:
        """
        Return aggregated per-day log counts.

        Keys: logs_data (raw), logs (pivoted), tab
        """
        logs_data = self._m.fetch_logs_by_date(table_name=table_name)
        logs = _build_date_index(logs_data)
        sum_all = sum(entry["total"] for entry in logs)

        return {
            "logs_data": logs_data,
            "logs": logs,
            "tab": {
                "sum_all": f"{sum_all:,}",
                "table_name": table_name,
            },
        }

    # ──────────────────────────── en → ar ───────────────────────────────

    def view_logs_en2ar(self, day: str = None) -> dict:
        """
        Return a split view of translated vs untranslated log entries.

        Keys: no_result, data_result, tab
        """
        all_logs = self._m.all_logs_en2ar(day=day)
        no_result = [k for k, v in all_logs.items() if v == "no_result"]
        data_result = {k: v for k, v in all_logs.items() if v != "no_result"}

        return {
            "no_result": no_result,
            "data_result": data_result,
            "tab": {
                "sum_all": f"{len(all_logs):,}",
                "sum_data_result": f"{len(data_result):,}",
                "sum_no_result": f"{len(no_result):,}",
            },
        }

    # ───────────────────────── dunder helpers ───────────────────────────

    def __repr__(self) -> str:
        return f"LogsView(manager={self._m!r})"


__all__ = ["LogsView"]
