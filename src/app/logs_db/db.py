# -*- coding: utf-8 -*-
"""
from .db import Database
"""
import logging
import sqlite3
from contextlib import contextmanager
from typing import Any

logger = logging.getLogger(__name__)


class Database:
    """
    Professional SQLite database manager.
    Handles connections, table creation, commits, and fetching.
    """

    def __init__(self, db_path: str):
        self.db_path = str(db_path)

    # ─────────────────────────── connection ────────────────────────────

    @contextmanager
    def _connect(self, row_as_dict: bool = False):
        """Context manager: opens a connection and guarantees closure."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            if row_as_dict:
                conn.row_factory = sqlite3.Row
            yield conn
        except sqlite3.Error as e:
            logger.error(f"[Database] Connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    # ──────────────────────────── commit ───────────────────────────────

    def commit(self, query: str, params: list | tuple = ()) -> bool:
        """
        Execute a write query (INSERT / UPDATE / DELETE / CREATE …).

        Returns:
            True on success, False on failure.
        """
        try:
            with self._connect() as conn:
                conn.execute(query, params)
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"[Database] Commit error: {e}")
            return False

    def commit_many(self, query: str, params_seq: list[list | tuple]) -> bool:
        """
        Execute a write query for multiple rows in a single transaction.

        Returns:
            True on success, False on failure.
        """
        try:
            with self._connect() as conn:
                conn.executemany(query, params_seq)
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"[Database] Commit-many error: {e}")
            return False

    # ──────────────────────────── fetch ────────────────────────────────

    def fetch(
        self,
        query: str,
        params: list | tuple = (),
        one: bool = False,
    ) -> list[dict[str, Any]] | dict[str, Any] | None:
        """
        Execute a SELECT query and return results as plain dicts.

        Args:
            query:  SQL SELECT statement.
            params: Bind parameters.
            one:    If True return a single dict (or None); otherwise a list.

        Returns:
            dict | None   when one=True
            list[dict]    when one=False  (empty list if no rows)
        """
        try:
            with self._connect(row_as_dict=True) as conn:
                cursor = conn.execute(query, params)
                if one:
                    row = cursor.fetchone()
                    return dict(row) if row else None
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"[Database] Fetch error: {e}")
            if "no such table" in str(e):
                logger.warning("[Database] Table missing — re-initialising schema.")
                self.init_tables()
            return None if one else []

    # ────────────────────────── table creation ─────────────────────────

    def _create_logs_table(self, table_name: str) -> bool:
        """
        Create a standard logs table if it does not already exist.
        All timestamps are stored in UTC via SQLite's CURRENT_TIMESTAMP.
        """
        query = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id               INTEGER  PRIMARY KEY AUTOINCREMENT,
                endpoint         TEXT     NOT NULL,
                request_data     TEXT     NOT NULL,
                response_status  TEXT     NOT NULL,
                response_time    REAL,
                response_count   INTEGER  DEFAULT 1,
                timestamp        DATETIME DEFAULT CURRENT_TIMESTAMP,
                date_only        DATE     DEFAULT (DATE('now')),
                UNIQUE(request_data, response_status, date_only)
            );
        """
        return self.commit(query)

    def init_tables(self) -> None:
        """Create all required tables (idempotent — safe to call repeatedly)."""
        self._create_logs_table("logs")
        self._create_logs_table("list_logs")
        logger.info("[Database] Tables initialised.")

    # ───────────────────────── dunder helpers ──────────────────────────

    def __repr__(self) -> str:
        return f"Database(path={self.db_path!r})"


__all__ = [
    "Database",
]
