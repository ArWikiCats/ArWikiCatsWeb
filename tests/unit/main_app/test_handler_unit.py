"""Unit tests for src/main_app/handler.py"""

from unittest.mock import Mock

import pytest

from src.main_app.handler import (
    ViewLogsRequestHandler,
    view_logs_request_handler,
)


class TestViewLogsRequestHandler:
    """Tests for ViewLogsRequestHandler dataclass."""

    def test_default_values(self):
        """Default values are set correctly."""
        handler = ViewLogsRequestHandler(
            page=1,
            per_page=10,
            order="DESC",
            order_by="timestamp",
            day="",
            status="",
            table_name="logs",
        )
        assert handler.page == 1
        assert handler.per_page == 10
        assert handler.order == "DESC"
        assert handler.order_by == "timestamp"
        assert handler.day == ""
        assert handler.status == ""
        assert handler.table_name == "logs"

    def test_page_minimum_is_one(self):
        """Page is clamped to minimum of 1."""
        handler = ViewLogsRequestHandler(
            page=0,
            per_page=10,
            order="DESC",
            order_by="timestamp",
            day="",
            status="",
            table_name="logs",
        )
        assert handler.page == 1

        handler = ViewLogsRequestHandler(
            page=-5,
            per_page=10,
            order="DESC",
            order_by="timestamp",
            day="",
            status="",
            table_name="logs",
        )
        assert handler.page == 1

    def test_per_page_clamped_between_1_and_200(self):
        """per_page is clamped to range [1, 200]."""
        handler = ViewLogsRequestHandler(
            page=1,
            per_page=0,
            order="DESC",
            order_by="timestamp",
            day="",
            status="",
            table_name="logs",
        )
        assert handler.per_page == 1

        handler = ViewLogsRequestHandler(
            page=1,
            per_page=500,
            order="DESC",
            order_by="timestamp",
            day="",
            status="",
            table_name="logs",
        )
        assert handler.per_page == 200

    def test_invalid_order_defaults_to_desc(self):
        """Invalid order value defaults to DESC."""
        handler = ViewLogsRequestHandler(
            page=1,
            per_page=10,
            order="INVALID",
            order_by="timestamp",
            day="",
            status="",
            table_name="logs",
        )
        assert handler.order == "DESC"

    def test_valid_order_preserved(self):
        """Valid order values are preserved."""
        handler = ViewLogsRequestHandler(
            page=1,
            per_page=10,
            order="ASC",
            order_by="timestamp",
            day="",
            status="",
            table_name="logs",
        )
        assert handler.order == "ASC"

    def test_invalid_order_by_defaults_to_timestamp(self):
        """Invalid order_by defaults to timestamp."""
        handler = ViewLogsRequestHandler(
            page=1,
            per_page=10,
            order="DESC",
            order_by="invalid_column",
            day="",
            status="",
            table_name="logs",
        )
        assert handler.order_by == "timestamp"

    def test_valid_order_by_preserved(self):
        """Valid order_by values are preserved."""
        handler = ViewLogsRequestHandler(
            page=1,
            per_page=10,
            order="DESC",
            order_by="response_count",
            day="",
            status="",
            table_name="logs",
        )
        assert handler.order_by == "response_count"

    def test_invalid_status_defaults_to_empty(self):
        """Invalid status defaults to empty string."""
        handler = ViewLogsRequestHandler(
            page=1,
            per_page=10,
            order="DESC",
            order_by="timestamp",
            day="",
            status="invalid_status",
            table_name="logs",
        )
        assert handler.status == ""

    def test_valid_status_preserved(self):
        """Valid status values are preserved."""
        handler = ViewLogsRequestHandler(
            page=1,
            per_page=10,
            order="DESC",
            order_by="timestamp",
            day="",
            status="no_result",
            table_name="logs",
        )
        assert handler.status == "no_result"

    def test_offset_calculation(self):
        """Offset is calculated correctly from page and per_page."""
        handler = ViewLogsRequestHandler(
            page=1,
            per_page=10,
            order="DESC",
            order_by="timestamp",
            day="",
            status="",
            table_name="logs",
        )
        assert handler.offset == 0

        handler = ViewLogsRequestHandler(
            page=3,
            per_page=20,
            order="DESC",
            order_by="timestamp",
            day="",
            status="",
            table_name="logs",
        )
        assert handler.offset == 40  # (3-1) * 20

    def test_order_by_types_property(self):
        """order_by_types returns sorted list of allowed columns."""
        handler = ViewLogsRequestHandler(
            page=1,
            per_page=10,
            order="DESC",
            order_by="timestamp",
            day="",
            status="",
            table_name="logs",
        )
        order_by_types = handler.order_by_types
        assert isinstance(order_by_types, list)
        assert order_by_types == sorted(handler.ALLOWED_ORDER_BY)

    def test_status_table_property(self):
        """status_table returns sorted list of allowed statuses."""
        handler = ViewLogsRequestHandler(
            page=1,
            per_page=10,
            order="DESC",
            order_by="timestamp",
            day="",
            status="",
            table_name="logs",
        )
        status_table = handler.status_table
        assert isinstance(status_table, list)
        assert status_table == sorted(handler.ALLOWED_STATUS)


class TestViewLogsRequestHandlerFunction:
    """Tests for view_logs_request_handler function."""

    def test_default_values(self):
        """Default values are extracted correctly."""
        request = Mock()
        request.args.get = Mock(side_effect=lambda key, default, type=None: default)

        allowed_tables = {"logs", "list_logs"}
        handler = view_logs_request_handler(request, allowed_tables)

        assert handler.page == 1
        assert handler.per_page == 10
        assert handler.order == "DESC"
        assert handler.order_by == "response_count"
        assert handler.day == ""
        assert handler.status == ""
        assert handler.table_name == "logs"

    def test_custom_values_extracted(self):
        """Custom values are extracted from request."""
        request = Mock()
        request.args.get = Mock(
            side_effect=lambda key, default, type=None: {
                "page": 5,
                "per_page": 50,
                "order": "ASC",
                "order_by": "id",
                "day": "2025-01-15",
                "status": "Category",
                "table_name": "logs",
            }.get(key, default)
        )

        allowed_tables = {"logs", "list_logs"}
        handler = view_logs_request_handler(request, allowed_tables)

        assert handler.page == 5
        assert handler.per_page == 50
        assert handler.order == "ASC"
        assert handler.order_by == "id"
        assert handler.day == "2025-01-15"
        assert handler.status == "Category"
        assert handler.table_name == "logs"

    def test_invalid_table_name_defaults_to_logs(self):
        """Invalid table_name defaults to 'logs'."""
        request = Mock()
        request.args.get = Mock(
            side_effect=lambda key, default, type=None: {
                "table_name": "invalid_table",
            }.get(key, default)
        )

        allowed_tables = {"logs", "list_logs"}
        handler = view_logs_request_handler(request, allowed_tables)

        assert handler.table_name == "logs"

    def test_valid_table_name_accepted(self):
        """Valid table_name is accepted."""
        request = Mock()
        request.args.get = Mock(
            side_effect=lambda key, default, type=None: {
                "table_name": "list_logs",
            }.get(key, default)
        )

        allowed_tables = {"logs", "list_logs"}
        handler = view_logs_request_handler(request, allowed_tables)

        assert handler.table_name == "list_logs"
