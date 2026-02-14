# -*- coding: utf-8 -*-
"""
Database access package for log storage and retrieval.

This package provides the data access layer for the ArWikiCats service,
handling all SQLite database operations for logging API requests and
retrieving analytics data.

Modules:
    db: Low-level database operations (connection, schema, raw queries)
    bot: High-level business operations (logging, retrieval, aggregation)

Public API:
    - log_request: Log an API request to the database
    - get_logs: Retrieve paginated log records
    - count_all: Count total log records
    - sum_response_count: Sum all response counts
    - get_response_status: Get unique status values
    - fetch_logs_by_date: Get daily statistics
    - all_logs_en2ar: Get English-to-Arabic mapping
    - change_db_path: Switch to a different database file
    - init_db: Initialize database schema

Example:
    >>> from logs_db import log_request, get_logs
    >>> log_request("/api/test", "Category:Test", "success", 0.123)
    True
    >>> logs = get_logs(per_page=10)
"""

from .bot import (
    all_logs_en2ar,
    change_db_path,
    count_all,
    db_commit,
    fetch_all,
    fetch_logs_by_date,
    get_logs,
    get_response_status,
    init_db,
    log_request,
    sum_response_count,
)

__all__ = [
    "all_logs_en2ar",
    "change_db_path",
    "count_all",
    "db_commit",
    "fetch_all",
    "fetch_logs_by_date",
    "get_logs",
    "get_response_status",
    "init_db",
    "log_request",
    "sum_response_count",
]
