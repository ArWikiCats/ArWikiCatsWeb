# -*- coding: utf-8 -*-
"""
Database migration script for adding date_only column.

This script is a one-time migration utility that adds the date_only column
to existing log tables if it doesn't exist, and backfills the column with
dates derived from existing timestamps.

Usage:
    Run as a standalone script:
        $ python -m app.logs_db.bot_update

    Or from the src directory:
        $ cd src && python -m app.logs_db.bot_update

Warning:
    This script should only need to be run once during initial deployment
    of the date_only feature. It is idempotent and safe to run multiple times.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Handle imports for both module execution and direct execution
try:
    from .bot import db_commit, init_db
except ImportError:
    # When running as a script directly
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from app.logs_db.bot import db_commit, init_db


def update_existing_records() -> None:
    """
    Backfill date_only column from timestamp for existing records.

    This function updates all records where date_only is NULL by
    extracting the date portion from the timestamp column.

    Affected Tables:
        - logs
        - list_logs
    """
    db_commit("UPDATE logs SET date_only = DATE(timestamp) WHERE date_only IS NULL")
    db_commit("UPDATE list_logs SET date_only = DATE(timestamp) WHERE date_only IS NULL")


def update_existing_tables() -> None:
    """
    Add date_only column to tables if it doesn't exist.

    This function attempts to add the date_only column to both
    log tables. If the column already exists, the ALTER TABLE
    statement will fail silently.

    Affected Tables:
        - logs
        - list_logs
    """
    try:
        db_commit("ALTER TABLE logs ADD COLUMN date_only DATE")
    except Exception as e:
        # Column likely already exists - this is expected
        print(f"Skipping 'date_only' column addition to logs table: {e}")

    try:
        db_commit("ALTER TABLE list_logs ADD COLUMN date_only DATE")
    except Exception as e:
        # Column likely already exists - this is expected
        print(f"Skipping 'date_only' column addition to list_logs table: {e}")


def main() -> None:
    """
    Run the database migration.

    This function:
    1. Initializes the database schema (creates tables if needed)
    2. Adds the date_only column if missing
    3. Backfills date_only from timestamp for existing records
    """
    print("Starting database migration...")

    init_db()
    print("Database schema initialized.")

    update_existing_tables()
    print("Table structure updated.")

    update_existing_records()
    print("Existing records backfilled.")

    print("Migration complete.")


if __name__ == "__main__":
    main()
