"""Unit tests for src/main_app/logs_db/logs_view.py"""

from unittest.mock import Mock, patch

import pytest

from src.main_app.logs_db.logs_view import (
    LogsView,
    _build_date_index,
    _format_log_row,
)
from src.main_app.handler import ViewLogsRequestHandler


class TestFormatLogRow:
    """Tests for _format_log_row helper function."""

    def test_format_log_row_formats_correctly(self):
        """_format_log_row formats a raw DB row correctly."""
        raw_log = {
            "id": 1,
            "endpoint": "/api/test",
            "request_data": "test_data_with_underscores",
            "response_status": "success",
            "response_time": 0.123,
            "response_count": 5,
            "timestamp": "2025-01-15 14:30:45",
            "date_only": "2025-01-15",
        }

        result = _format_log_row(raw_log)

        assert result["id"] == 1
        assert result["endpoint"] == "/api/test"
        assert result["request_data"] == "test data with underscores"
        assert result["response_status"] == "success"
        assert result["response_time"] == 0.123
        assert result["response_count"] == 5
        assert result["timestamp"] == "14:30:45"
        assert result["date_only"] == "2025-01-15"

    def test_format_log_row_replaces_underscores(self):
        """_format_log_row replaces underscores with spaces."""
        raw_log = {
            "id": 1,
            "endpoint": "/api/test",
            "request_data": "hello_world_test",
            "response_status": "success",
            "response_time": 0.1,
            "response_count": 1,
            "timestamp": "2025-01-15 14:30:45",
            "date_only": "2025-01-15",
        }

        result = _format_log_row(raw_log)
        assert result["request_data"] == "hello world test"

    def test_format_log_row_extracts_time_only(self):
        """_format_log_row extracts only time from timestamp."""
        raw_log = {
            "id": 1,
            "endpoint": "/api/test",
            "request_data": "test",
            "response_status": "success",
            "response_time": 0.1,
            "response_count": 1,
            "timestamp": "2025-01-15 14:30:45",
            "date_only": "2025-01-15",
        }

        result = _format_log_row(raw_log)
        assert result["timestamp"] == "14:30:45"


class TestBuildDateIndex:
    """Tests for _build_date_index helper function."""

    def test_build_date_index_pivots_data(self):
        """_build_date_index pivots flat DB rows into per-day summary."""
        raw_data = [
            {"date_only": "2025-01-15", "status_group": "no_result", "title_count": 2, "count": 5},
            {"date_only": "2025-01-15", "status_group": "Category", "title_count": 3, "count": 10},
            {"date_only": "2025-01-16", "status_group": "no_result", "title_count": 1, "count": 3},
        ]

        result = _build_date_index(raw_data)

        assert len(result) == 2
        assert result[0]["day"] == "2025-01-15"
        assert result[0]["title_count"] == 5
        assert result[0]["results"]["no_result"] == 5
        assert result[0]["results"]["Category"] == 10
        assert result[0]["total"] == 15

    def test_build_date_index_sorts_by_day(self):
        """_build_date_index sorts results by day."""
        raw_data = [
            {"date_only": "2025-01-17", "status_group": "no_result", "title_count": 1, "count": 3},
            {"date_only": "2025-01-15", "status_group": "no_result", "title_count": 2, "count": 5},
            {"date_only": "2025-01-16", "status_group": "Category", "title_count": 3, "count": 10},
        ]

        result = _build_date_index(raw_data)

        assert result[0]["day"] == "2025-01-15"
        assert result[1]["day"] == "2025-01-16"
        assert result[2]["day"] == "2025-01-17"

    def test_build_date_index_empty_input(self):
        """_build_date_index returns empty list for empty input."""
        result = _build_date_index([])
        assert result == []

    def test_build_date_index_calculates_total(self):
        """_build_date_index calculates total correctly."""
        raw_data = [
            {"date_only": "2025-01-15", "status_group": "no_result", "title_count": 2, "count": 100},
            {"date_only": "2025-01-15", "status_group": "Category", "title_count": 3, "count": 200},
        ]

        result = _build_date_index(raw_data)
        assert result[0]["total"] == 300


class TestLogsViewInit:
    """Tests for LogsView initialization."""

    def test_init_stores_manager(self):
        """LogsView stores the manager."""
        mock_manager = Mock()
        view = LogsView(manager=mock_manager)
        assert view._m == mock_manager


class TestLogsViewViewLogs:
    """Tests for LogsView.view_logs method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_manager = Mock()
        self.view = LogsView(manager=self.mock_manager)

    def _create_handler(self, **kwargs):
        """Helper to create a ViewLogsRequestHandler with defaults."""
        params = {
            "page": 1,
            "per_page": 10,
            "order": "DESC",
            "order_by": "timestamp",
            "day": "",
            "status": "",
            "table_name": "logs",
        }
        params.update(kwargs)
        return ViewLogsRequestHandler(**params)

    def test_view_logs_calls_manager_get_logs(self):
        """view_logs calls manager.get_logs with correct params."""
        handler = self._create_handler(
            page=1,
            per_page=10,
            order="DESC",
            order_by="timestamp",
            status="no_result",
            table_name="logs",
            day="2025-01-15",
        )

        self.mock_manager.get_logs.return_value = []
        self.mock_manager.count_all.return_value = 0
        self.mock_manager.sum_response_count.return_value = 0

        self.view.view_logs(handler)

        self.mock_manager.get_logs.assert_called_once_with(
            per_page=10,
            offset=0,
            order="DESC",
            order_by="timestamp",
            status="no_result",
            table_name="logs",
            day="2025-01-15",
        )

    def test_view_logs_formats_log_rows(self):
        """view_logs formats each log row."""
        handler = self._create_handler()

        self.mock_manager.get_logs.return_value = [
            {
                "id": 1,
                "endpoint": "/api/test",
                "request_data": "test_data",
                "response_status": "success",
                "response_time": 0.1,
                "response_count": 1,
                "timestamp": "2025-01-15 14:30:45",
                "date_only": "2025-01-15",
            }
        ]
        self.mock_manager.count_all.return_value = 1
        self.mock_manager.sum_response_count.return_value = 1

        result = self.view.view_logs(handler)

        assert len(result["logs"]) == 1
        assert result["logs"][0]["request_data"] == "test data"

    def test_view_logs_calls_count_all(self):
        """view_logs calls manager.count_all."""
        handler = self._create_handler(
            status="Category",
            day="2025-01-15",
        )

        self.mock_manager.get_logs.return_value = []
        self.mock_manager.count_all.return_value = 100
        self.mock_manager.sum_response_count.return_value = 500

        self.view.view_logs(handler)

        self.mock_manager.count_all.assert_called_once_with(
            status="Category",
            table_name="logs",
            day="2025-01-15",
        )

    def test_view_logs_calls_sum_response_count(self):
        """view_logs calls manager.sum_response_count."""
        handler = self._create_handler()

        self.mock_manager.get_logs.return_value = []
        self.mock_manager.count_all.return_value = 100
        self.mock_manager.sum_response_count.return_value = 500

        self.view.view_logs(handler)

        self.mock_manager.sum_response_count.assert_called_once_with(
            status="",
            table_name="logs",
            day="",
        )

    def test_view_logs_pagination_calculation(self):
        """view_logs calculates pagination correctly."""
        handler = self._create_handler(page=1, per_page=10)

        self.mock_manager.get_logs.return_value = []
        self.mock_manager.count_all.return_value = 95
        self.mock_manager.sum_response_count.return_value = 200

        result = self.view.view_logs(handler)

        tab = result["tab"]
        assert tab["total_pages"] == 10
        assert tab["sum_all"] == "200"
        assert tab["total_logs"] == "95"
        assert tab["start_log"] == 1
        assert tab["end_log"] == 10

    def test_view_logs_returns_order_by_types(self):
        """view_logs returns order_by_types from handler."""
        handler = self._create_handler()

        self.mock_manager.get_logs.return_value = []
        self.mock_manager.count_all.return_value = 0
        self.mock_manager.sum_response_count.return_value = 0

        result = self.view.view_logs(handler)

        assert isinstance(result["order_by_types"], list)
        assert len(result["order_by_types"]) > 0

    def test_view_logs_returns_status_table(self):
        """view_logs returns status_table from handler."""
        handler = self._create_handler()

        self.mock_manager.get_logs.return_value = []
        self.mock_manager.count_all.return_value = 0
        self.mock_manager.sum_response_count.return_value = 0

        result = self.view.view_logs(handler)

        assert isinstance(result["status_table"], list)
        assert len(result["status_table"]) > 0


class TestLogsViewViewLogsByDate:
    """Tests for LogsView.view_logs_by_date method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_manager = Mock()
        self.view = LogsView(manager=self.mock_manager)

    def test_view_logs_by_date_calls_fetch_logs_by_date(self):
        """view_logs_by_date calls manager.fetch_logs_by_date."""
        self.mock_manager.fetch_logs_by_date.return_value = []

        self.view.view_logs_by_date(table_name="list_logs")

        self.mock_manager.fetch_logs_by_date.assert_called_once_with(table_name="list_logs")

    def test_view_logs_by_date_builds_index(self):
        """view_logs_by_date builds date index."""
        self.mock_manager.fetch_logs_by_date.return_value = [
            {"date_only": "2025-01-15", "status_group": "no_result", "title_count": 2, "count": 5},
        ]

        result = self.view.view_logs_by_date(table_name="logs")

        assert "logs" in result
        assert len(result["logs"]) == 1

    def test_view_logs_by_date_calculates_sum_all(self):
        """view_logs_by_date calculates sum_all."""
        self.mock_manager.fetch_logs_by_date.return_value = [
            {"date_only": "2025-01-15", "status_group": "no_result", "title_count": 2, "count": 5},
            {"date_only": "2025-01-15", "status_group": "Category", "title_count": 3, "count": 10},
        ]

        result = self.view.view_logs_by_date(table_name="logs")

        assert result["tab"]["sum_all"] == "15"

    def test_view_logs_by_date_returns_raw_data(self):
        """view_logs_by_date returns raw logs_data."""
        raw_data = [
            {"date_only": "2025-01-15", "status_group": "no_result", "title_count": 2, "count": 5},
        ]
        self.mock_manager.fetch_logs_by_date.return_value = raw_data

        result = self.view.view_logs_by_date(table_name="logs")

        assert result["logs_data"] == raw_data


class TestLogsViewViewLogsEn2Ar:
    """Tests for LogsView.view_logs_en2ar method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_manager = Mock()
        self.view = LogsView(manager=self.mock_manager)

    def test_view_logs_en2ar_calls_all_logs_en2ar(self):
        """view_logs_en2ar calls manager.all_logs_en2ar."""
        self.mock_manager.all_logs_en2ar.return_value = {
            "title1": "result1",
            "title2": "no_result",
        }

        self.view.view_logs_en2ar()

        self.mock_manager.all_logs_en2ar.assert_called_once_with(day=None)

    def test_view_logs_en2ar_with_day_filter(self):
        """view_logs_en2ar passes day filter to manager."""
        self.mock_manager.all_logs_en2ar.return_value = {}

        self.view.view_logs_en2ar(day="2025-01-15")

        self.mock_manager.all_logs_en2ar.assert_called_once_with(day="2025-01-15")

    def test_view_logs_en2ar_separates_no_result(self):
        """view_logs_en2ar separates no_result from data_result."""
        self.mock_manager.all_logs_en2ar.return_value = {
            "title1": "result1",
            "title2": "result2",
            "title3": "no_result",
            "title4": "no_result",
        }

        result = self.view.view_logs_en2ar()

        assert result["no_result"] == ["title3", "title4"]
        assert result["data_result"] == {"title1": "result1", "title2": "result2"}

    def test_view_logs_en2ar_calculates_counts(self):
        """view_logs_en2ar calculates correct counts."""
        self.mock_manager.all_logs_en2ar.return_value = {
            "title1": "result1",
            "title2": "result2",
            "title3": "no_result",
        }

        result = self.view.view_logs_en2ar()

        tab = result["tab"]
        assert tab["sum_all"] == "3"
        assert tab["sum_data_result"] == "2"
        assert tab["sum_no_result"] == "1"

    def test_view_logs_en2ar_empty_results(self):
        """view_logs_en2ar handles empty results."""
        self.mock_manager.all_logs_en2ar.return_value = {}

        result = self.view.view_logs_en2ar()

        assert result["no_result"] == []
        assert result["data_result"] == {}
        assert result["tab"]["sum_all"] == "0"


class TestLogsViewRepr:
    """Tests for LogsView.__repr__ method."""

    def test_repr_returns_string(self):
        """__repr__ returns a string representation."""
        mock_manager = Mock()
        view = LogsView(manager=mock_manager)
        repr_str = repr(view)
        assert isinstance(repr_str, str)
        assert "LogsView" in repr_str
