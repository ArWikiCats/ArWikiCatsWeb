# -*- coding: utf-8 -*-
"""

from .db import db_commit, init_db, fetch_all

"""
import logging
import sqlite3

from ..config import settings

logger = logging.getLogger(__name__)


def _get_db_path_main() -> str:
    db_path_main = settings.paths.db_path_main
    return db_path_main


def _validate_table_name(table_name: str) -> None:
    """Validate table name against whitelist to prevent SQL injection."""
    if table_name not in settings.allowed_tables:
        raise ValueError(f"Invalid table name: {table_name}")


def db_commit(query, params=[]):
    db_path_main = _get_db_path_main()
    conn = None
    try:
        conn = sqlite3.connect(str(db_path_main))
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return True

    except sqlite3.Error as e:
        logger.error(f"init_db Database error: {e}")
        return e
    finally:
        if conn:
            conn.close()


def _create_logs_table(table_name: str) -> None:
    """Create a logs table with the standard schema.

    Note: All timestamps are stored in UTC using SQLite's CURRENT_TIMESTAMP.
    The date_only field is derived from the timestamp using DATE('now') in UTC.
    """
    _validate_table_name(table_name)
    query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            endpoint TEXT NOT NULL,
            request_data TEXT NOT NULL,
            response_status TEXT NOT NULL,
            response_time REAL,
            response_count INTEGER DEFAULT 1,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            date_only DATE DEFAULT (DATE('now')),
            UNIQUE(request_data, response_status, date_only)
        );
        """
    db_commit(query)


def init_db():
    """Initialize the database by creating logs and list_logs tables."""
    _create_logs_table("logs")
    _create_logs_table("list_logs")


def fetch_all(query: str, params: list = None, fetch_one: bool = False):
    """Execute a query and fetch results.

    Args:
        query: SQL query to execute
        params: Query parameters (default: empty list)
        fetch_one: If True, fetch single row; otherwise fetch all rows

    Returns:
        When fetch_one=True: dict with row data, or None if no rows
        When fetch_one=False: list of dicts (empty list if no rows)
    """
    db_path_main = _get_db_path_main()

    if params is None:
        params = []
    conn = None
    try:
        conn = sqlite3.connect(str(db_path_main))
        # Set row factory to return rows as dictionaries
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Execute the query
        cursor.execute(query, params)

        # Fetch results
        if fetch_one:
            row = cursor.fetchone()
            logs = dict(row) if row else None  # Convert to dictionary
        else:
            rows = cursor.fetchall()
            logs = [dict(row) for row in rows]  # Convert all rows to dictionaries

    except sqlite3.Error as e:
        logger.error(f"Database error in view_logs: {e}")
        if "no such table" in str(e):
            init_db()
        logs = [] if not fetch_one else None
    finally:
        if conn:
            conn.close()

    return logs


__all__ = [
    "db_commit",
    "init_db",
    "fetch_all",
]
