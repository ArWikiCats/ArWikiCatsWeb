# -*- coding: utf-8 -*-
"""
Tests for the logs_bot module.
"""
from unittest.mock import MagicMock, patch

import pytest


class TestViewLogs:
    """Tests for the view_logs function."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock Flask request object."""
        request = MagicMock()
        request.args = MagicMock()
        request.args.get = MagicMock(side_effect=self._mock_args_get)
        return request

    def _mock_args_get(self, key, default=None, type=None):
        """Default mock implementation for request.args.get."""
        defaults = {
            "db_path": None,
            "page": 1,
            "per_page": 10,
            "order": "desc",
            "order_by": "response_count",
            "day": "",
            "status": "",
            "like": "",
            "table_name": "logs",
        }
        value = defaults.get(key, default)
        if type and value is not None:
            return type(value)
        return value

    @patch("src.app.logs_db.logs_bot.sum_response_count")
    @patch("src.app.logs_db.logs_bot.count_all")
    @patch("src.app.logs_db.logs_bot.get_logs")
    def test_view_logs_returns_dict_with_required_keys(
        self, mock_get_logs, mock_count_all, mock_sum_response_count, mock_request
    ):
        """Test that view_logs returns a dict with expected keys."""
        from src.app.logs_db.logs_bot import view_logs

        # Setup mocks
        mock_get_logs.return_value = []
        mock_count_all.return_value = 0
        mock_sum_response_count.return_value = 0

        result = view_logs(mock_request)

        assert isinstance(result, dict)
        assert "logs" in result
        assert "tab" in result
        assert "status_table" in result

    @patch("src.app.logs_db.logs_bot.sum_response_count")
    @patch("src.app.logs_db.logs_bot.count_all")
    @patch("src.app.logs_db.logs_bot.get_logs")
    def test_view_logs_pagination_defaults(self, mock_get_logs, mock_count_all, mock_sum_response_count, mock_request):
        """Test that view_logs uses correct pagination defaults."""
        from src.app.logs_db.logs_bot import view_logs

        mock_get_logs.return_value = []
        mock_count_all.return_value = 0
        mock_sum_response_count.return_value = 0

        result = view_logs(mock_request)

        # Check that get_logs was called with default pagination
        call_args = mock_get_logs.call_args
        # per_page is passed as the first positional argument
        assert call_args[0][0] == 10

    @patch("src.app.logs_db.logs_bot.sum_response_count")
    @patch("src.app.logs_db.logs_bot.count_all")
    @patch("src.app.logs_db.logs_bot.get_logs")
    def test_view_logs_validates_table_name(self, mock_get_logs, mock_count_all, mock_sum_response_count):
        """Test that view_logs validates table_name parameter."""
        from src.app.logs_db.logs_bot import view_logs

        request = MagicMock()
        request.args.get = MagicMock(
            side_effect=lambda k, d=None, type=None: {
                "table_name": "invalid_table",
                "page": 1,
                "per_page": 10,
                "order": "desc",
                "order_by": "response_count",
            }.get(k, d)
        )

        mock_get_logs.return_value = []
        mock_count_all.return_value = 0
        mock_sum_response_count.return_value = 0

        result = view_logs(request)

        # Should default to "logs" table
        assert result["tab"]["table_name"] == "logs"

    @patch("src.app.logs_db.logs_bot.sum_response_count")
    @patch("src.app.logs_db.logs_bot.count_all")
    @patch("src.app.logs_db.logs_bot.get_logs")
    def test_view_logs_formats_request_data(self, mock_get_logs, mock_count_all, mock_sum_response_count, mock_request):
        """Test that view_logs replaces underscores in request_data."""
        from src.app.logs_db.logs_bot import view_logs

        mock_get_logs.return_value = [
            {
                "id": 1,
                "endpoint": "/api/test",
                "request_data": "Category:Test_Data_Here",
                "response_status": "success",
                "response_time": 0.1,
                "response_count": 5,
                "timestamp": "2025-01-27 10:30:00",
                "date_only": "2025-01-27",
            }
        ]
        mock_count_all.return_value = 1
        mock_sum_response_count.return_value = 5

        result = view_logs(mock_request)

        assert len(result["logs"]) == 1
        assert "_" not in result["logs"][0]["request_data"]
        assert "Test Data Here" in result["logs"][0]["request_data"]


class TestViewLogsEdgeCases:
    """Tests for edge cases in view_logs function."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock Flask request object."""
        request = MagicMock()
        request.args = MagicMock()
        return request

    @patch("src.app.logs_db.logs_bot.sum_response_count")
    @patch("src.app.logs_db.logs_bot.count_all")
    @patch("src.app.logs_db.logs_bot.get_logs")
    def test_view_logs_invalid_order_by_defaults_to_timestamp(
        self, mock_get_logs, mock_count_all, mock_sum_response_count, mock_request
    ):
        """Test view_logs with invalid order_by defaults to timestamp."""
        from src.app.logs_db.logs_bot import view_logs

        mock_get_logs.return_value = []
        mock_count_all.return_value = 0
        mock_sum_response_count.return_value = 0

        def mock_get(key, default=None, type=None):
            return {
                "page": 1,
                "per_page": 10,
                "order": "desc",
                "order_by": "invalid_column",
            }.get(key, default)

        mock_request.args.get = MagicMock(side_effect=mock_get)

        view_logs(mock_request)

        # Should default to timestamp for order_by
        call_args = mock_get_logs.call_args
        assert call_args[1]["order_by"] == "timestamp"


class TestRetrieveLogsByDateEdgeCases:
    """Tests for edge cases in retrieve_logs_by_date function."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock Flask request object."""
        request = MagicMock()
        request.args = MagicMock()
        return request
