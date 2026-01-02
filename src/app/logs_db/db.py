# -*- coding: utf-8 -*-
"""

from .db import change_db_path, db_commit, init_db, fetch_all

"""
import os
import sqlite3
from pathlib import Path

HOME = os.getenv("HOME")
main_path = HOME + "/www/python/dbs" if HOME else Path(__file__).parent.parent.parent

db_path_main = {1: f"{str(main_path)}/new_logs.db"}


def change_db_path(file):
    # ---
    db_path = str(main_path) + f"/{file}"
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
        print(f"init_db Database error: {e}")
        return e


def init_db():
    query = """
        CREATE TABLE IF NOT EXISTS logs (
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

    query = """
        CREATE TABLE IF NOT EXISTS list_logs (
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


def fetch_all(query, params=[], fetch_one=False):
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
        print(f"Database error in view_logs: {e}")
        if "no such table" in str(e):
            init_db()
        logs = []

    return logs
