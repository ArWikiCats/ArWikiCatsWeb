# -*- coding: utf-8 -*-
"""

from .db import change_db_path, db_commit, init_db, fetch_all

"""
import logging
import os
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

ALLOWED_TABLES = {"logs", "list_logs"}

# Database path configurable via DATABASE_PATH environment variable
# Defaults to ~/www/python/dbs for backwards compatibility
db_path_str = os.getenv("DATABASE_PATH", "")
if db_path_str:
    main_path = Path(db_path_str)
else:
    main_path = Path.home() / "www" / "python" / "dbs"

if not main_path.exists():
    main_path.mkdir(parents=True, exist_ok=True)

db_path_main = {1: str(main_path / "new_logs.db")}


def _validate_table_name(table_name: str) -> None:
    """Validate table name against whitelist to prevent SQL injection."""
    if table_name not in ALLOWED_TABLES:
        raise ValueError(f"Invalid table name: {table_name}")


def change_db_path(file):
    # ---
    db_path = str(main_path / file)
    # ---
    dbs_path = Path(main_path)
    # ---
    # list of files *.db in dbs_path
    dbs = [str(f.name) for f in dbs_path.glob("*.db") if f.is_file()]
    # ---
    if file in dbs and os.path.exists(db_path):
        db_path_main[1] = str(db_path)
    # ---
    return dbs


def db_commit(query, params=[]):
    try:
        with sqlite3.connect(db_path_main[1]) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
        conn.commit()
        return True

    except sqlite3.Error as e:
        logger.error(f"init_db Database error: {e}")
        return e


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
    if params is None:
        params = []
    try:
        with sqlite3.connect(db_path_main[1]) as conn:
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

    return logs
