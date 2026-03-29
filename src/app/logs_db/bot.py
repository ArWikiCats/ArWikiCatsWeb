# -*- coding: utf-8 -*-
"""
from .logs_db.bot import LogsManager
"""
import logging
import re

from ..config import settings
from .db import Database

logger = logging.getLogger(__name__)


class LogsManager:
    """
    Professional logs manager.
    Handles logging requests, querying, and aggregating log data.
    """

    ALLOWED_ORDERS = {"ASC", "DESC"}

    def __init__(self, db: Database = None):
        self._db = db or Database(settings.paths.db_path_main)

    # ─────────────────────────── validation ────────────────────────────

    def _validate_table(self, table_name: str) -> None:
        """Whitelist check to prevent SQL injection via table names."""
        if table_name not in settings.allowed_tables:
            raise ValueError(f"Invalid table name: {table_name!r}")

    @staticmethod
    def _validate_order(order: str) -> str:
        """Normalize ORDER direction — fallback to DESC if invalid."""
        return order if order in LogsManager.ALLOWED_ORDERS else "DESC"

    @staticmethod
    def _resolve_table(endpoint: str) -> str:
        return "list_logs" if endpoint == "/api/list" else "logs"

    # ──────────────────────────── write ────────────────────────────────

    def log_request(
        self,
        endpoint: str,
        request_data: str,
        response_status,
        response_time: float,
    ) -> bool:
        """
        Insert or update a log record for a given request.
        Uses UPSERT (ON CONFLICT) to increment counters on duplicates.
        """
        table_name = self._resolve_table(endpoint)
        response_time = round(response_time, 3)
        response_status = str(response_status)

        query = f"""
            INSERT INTO {table_name} (
                endpoint, request_data, response_status, response_time, date_only
            )
            VALUES (?, ?, ?, ?, DATE('now'))
            ON CONFLICT(request_data, response_status, date_only) DO UPDATE SET
                response_count = response_count + 1,
                response_time  = excluded.response_time,
                timestamp      = CURRENT_TIMESTAMP
        """
        success = self._db.commit(query, (endpoint, str(request_data), response_status, response_time))

        if not success:
            logger.error("[LogsManager] Failed to log request: %s %s", endpoint, request_data)
            self._db.init_tables()

        return success

    # ──────────────────────── query builder ────────────────────────────

    @staticmethod
    def _apply_filters(
        query: str,
        params: list,
        *,
        status: str = "",
        like: str = "",
        day: str = "",
    ) -> tuple[str, list]:
        """
        Append WHERE clauses for status / like / day filters.
        Mutates and returns (query, params).
        """
        conditions = []

        if status:
            if status == "Category":
                conditions.append("response_status LIKE 'تصنيف%'")
            elif status.lower() != "all":
                conditions.append("response_status = ?")
                params.append(status)
        elif like:
            conditions.append("response_status LIKE ?")
            params.append(like)

        if day and re.match(r"\d{4}-\d{2}-\d{2}", day):
            conditions.append("date_only = ?")
            params.append(day)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        return query, params

    # ──────────────────────────── read ─────────────────────────────────

    def sum_response_count(
        self,
        status: str = "",
        table_name: str = "logs",
        like: str = "",
    ) -> int:
        """Return the total sum of response_count matching the given filters."""
        self._validate_table(table_name)
        query, params = self._apply_filters(
            f"SELECT SUM(response_count) AS count_all FROM {table_name}",
            [],
            status=status,
            like=like,
        )
        result = self._db.fetch(query, params, one=True)
        return (result or {}).get("count_all") or 0

    def count_all(
        self,
        status: str = "",
        table_name: str = "logs",
        like: str = "",
    ) -> int:
        """Return the number of rows matching the given filters."""
        self._validate_table(table_name)
        query, params = self._apply_filters(
            f"SELECT COUNT(*) AS total FROM {table_name}",
            [],
            status=status,
            like=like,
        )
        result = self._db.fetch(query, params, one=True)
        return (result or {}).get("total") or 0

    def get_response_status(self, table_name: str = "logs") -> list[str]:
        """Return distinct response statuses that appear more than twice."""
        self._validate_table(table_name)
        query = f"""
            SELECT response_status
            FROM   {table_name}
            GROUP  BY response_status
            HAVING COUNT(*) > 2
        """
        rows = self._db.fetch(query, ())
        return [row["response_status"] for row in rows]

    def get_logs(
        self,
        per_page: int = 10,
        offset: int = 0,
        order: str = "DESC",
        order_by: str = "timestamp",
        status: str = "",
        table_name: str = "logs",
        like: str = "",
        day: str = "",
    ) -> list[dict]:
        """Return a paginated, optionally-filtered page of log rows."""
        self._validate_table(table_name)
        order = self._validate_order(order)

        query, params = self._apply_filters(
            f"SELECT * FROM {table_name} ",
            [],
            status=status,
            like=like,
            day=day,
        )
        query += f" ORDER BY {order_by} {order} LIMIT ? OFFSET ?"
        params.extend([per_page, offset])

        return self._db.fetch(query, params)

    def fetch_logs_by_date(self, table_name: str = "logs") -> list[dict]:
        """
        Return daily aggregated counts grouped by date and status.
        Arabic statuses starting with 'تصنيف' are normalised to 'Category'.
        """
        self._validate_table(table_name)
        query = f"""
            SELECT
                date_only,
                CASE
                    WHEN response_status LIKE 'تصنيف%' THEN 'Category'
                    ELSE response_status
                END AS status_group,
                COUNT(request_data)   AS title_count,
                SUM(response_count)   AS count
            FROM   {table_name}
            GROUP  BY date_only, status_group
            ORDER  BY date_only
        """
        return self._db.fetch(query, ())

    def all_logs_en2ar(self, day: str = None) -> dict[str, str]:
        """
        Return a {request_data: response_status} mapping, optionally filtered
        by a full date (YYYY-MM-DD) or year-month (YYYY-MM).
        """
        query = "SELECT request_data, response_status FROM logs"
        params: list = []

        if day:
            if re.match(r"\d{4}-\d{2}-\d{2}", day):
                query += " WHERE date_only = ?"
                params.append(day)
            elif re.match(r"\d{4}-\d{2}", day):
                query += " WHERE strftime('%Y-%m', date_only) = ?"
                params.append(day)

        query += " GROUP BY request_data, response_status ORDER BY request_data"

        logger.debug("[LogsManager] all_logs_en2ar query=%s params=%s", query, params)
        rows = self._db.fetch(query, params)
        return {row["request_data"]: row["response_status"] for row in rows}

    # ───────────────────────── dunder helpers ──────────────────────────

    def __repr__(self) -> str:
        return f"LogsManager(db={self._db!r})"


__all__ = [
    "LogsManager",
]
