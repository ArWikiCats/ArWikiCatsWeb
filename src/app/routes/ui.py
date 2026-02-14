# -*- coding: utf-8 -*-
"""
Web UI routes for the ArWikiCats service.

This module defines all UI-facing routes under the root URL prefix. It provides:
- Home page with category lookup interface
- Log viewing and analytics pages
- Batch processing interface

Architecture:
    This module handles HTTP request/response concerns for the web interface.
    Business logic is delegated to logs_bot.py. Templates are rendered using
    Jinja2, with dynamic data loaded via AJAX from the API endpoints.

Templates:
    - index.html: Main category lookup interface
    - logs.html: Log viewer with filtering and pagination
    - logs_by_day.html: Daily statistics dashboard
    - no_result.html: Categories with no Arabic equivalent
    - list.html: Batch category lookup interface
    - chart.html, chart2.html: Visualization pages
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flask import Blueprint, render_template, request

from ..logs_bot import retrieve_logs_by_date, view_logs

if TYPE_CHECKING:
    from flask.typing import ResponseReturnValue

# =============================================================================
# MODULE CONFIGURATION
# =============================================================================

#: UI Blueprint with no URL prefix (serves at root)
ui_bp = Blueprint("ui", __name__)


# =============================================================================
# PAGE ROUTES
# =============================================================================

@ui_bp.route("/", methods=["GET"])
def render_index_page() -> str:
    """
    Render the main home page.

    This is the primary interface for looking up single category labels.
    The page includes a form for entering English category names and
    displays the Arabic equivalent.

    Returns:
        str: Rendered HTML from index.html template.
    """
    return render_template("index.html")


@ui_bp.route("/logs", methods=["GET"])
def render_logs_view() -> ResponseReturnValue:
    """
    Render the log viewer page.

    Displays API request logs with filtering, sorting, and pagination.
    The page allows users to browse all logged requests and analyze
    usage patterns.

    Query Parameters:
        page: Page number (default: 1)
        per_page: Results per page (default: 10)
        order: Sort direction - "asc" or "desc"
        order_by: Column to sort by
        status: Filter by response status
        like: Fuzzy match pattern
        day: Date filter
        table_name: Table to query
        db_path: Database filename

    Returns:
        str: Rendered HTML from logs.html template with log data.
    """
    result = view_logs(request)
    return render_template("logs.html", result=result)


@ui_bp.route("/no_result", methods=["GET"])
def render_no_results_page() -> str:
    """
    Render the no-results page.

    Displays categories that did not have Arabic equivalents in the
    database. Useful for identifying gaps in the translation coverage.

    Returns:
        str: Rendered HTML from no_result.html template.
    """
    return render_template("no_result.html")


@ui_bp.route("/logs_by_day", methods=["GET"])
def render_daily_logs() -> str:
    """
    Render the daily statistics dashboard.

    Displays aggregated statistics grouped by date, showing trends
    in API usage and success rates over time.

    Query Parameters:
        db_path: Optional database filename
        table_name: Table to query (logs or list_logs)

    Returns:
        str: Rendered HTML from logs_by_day.html template.
    """
    result = retrieve_logs_by_date(request)
    return render_template(
        "logs_by_day.html",
        logs=result.get("logs", []),
        tab=result.get("tab", {}),
        status_table=result.get("status_table", []),
        dbs=result.get("dbs", []),
    )


@ui_bp.route("/list", methods=["GET"])
def render_title_list() -> str:
    """
    Render the batch lookup interface.

    Provides an interface for submitting multiple category names at once
    for bulk resolution. More efficient than individual requests for
    processing large numbers of categories.

    Returns:
        str: Rendered HTML from list.html template.
    """
    return render_template("list.html")


@ui_bp.route("/chart", methods=["GET"])
def render_chart() -> str:
    """
    Render the primary chart visualization page.

    Displays graphical representations of API usage statistics,
    including request volumes and success rates.

    Returns:
        str: Rendered HTML from chart.html template.
    """
    return render_template("chart.html")


@ui_bp.route("/chart2", methods=["GET"])
def render_chart2() -> str:
    """
    Render the secondary chart visualization page.

    Additional visualization views for API statistics with different
    chart types or data groupings.

    Returns:
        str: Rendered HTML from chart2.html template.
    """
    return render_template("chart2.html")
