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
            "table_name": "logs",
        }
        value = defaults.get(key, default)
        if type and value is not None:
            return type(value)
        return value

    @patch("src.app.logs_db.logs_bot.load_data_manager")
    def test_view_logs_returns_dict_with_required_keys(
        self, mock_load_data_manager, mock_request
    ):
        """Test that view_logs returns a dict with expected keys."""
        from src.app.logs_db.logs_bot import view_logs_new
        from src.app.handler import view_logs_request_handler

        # Setup mock manager
        mock_manager = mock_load_data_manager.return_value
        mock_manager.get_logs.return_value = []
        mock_manager.count_all.return_value = 0
        mock_manager.sum_response_count.return_value = 0

        # Create a mock request with args
        mock_request.args.get.side_effect = self._mock_args_get

        result = view_logs_new(view_logs_request_handler(mock_request, ["logs", "list_logs"]))

        assert isinstance(result, dict)
        assert "logs" in result
        assert "tab" in result
        assert "status_table" in result

    @patch("src.app.logs_db.logs_bot.load_data_manager")
    def test_view_logs_pagination_defaults(self, mock_load_data_manager, mock_request):
        """Test that view_logs uses correct pagination defaults."""
        from src.app.logs_db.logs_bot import view_logs_new
        from src.app.handler import view_logs_request_handler

        # Setup mock manager
        mock_manager = mock_load_data_manager.return_value
        mock_manager.get_logs.return_value = []
        mock_manager.count_all.return_value = 0
        mock_manager.sum_response_count.return_value = 0

        mock_request.args.get.side_effect = self._mock_args_get

        view_logs_new(view_logs_request_handler(mock_request, ["logs", "list_logs"]))

        # Check that get_logs was called with default pagination (per_page=10)
        call_args = mock_manager.get_logs.call_args
        assert call_args[0][0] == 10  # per_page

    @patch("src.app.logs_db.logs_bot.load_data_manager")
    def test_view_logs_validates_table_name(self, mock_load_data_manager):
        """Test that view_logs validates table_name parameter."""
        from src.app.logs_db.logs_bot import view_logs_new
        from src.app.handler import view_logs_request_handler

        request = MagicMock()
        request.args.get = MagicMock(
            side_effect=lambda k, d=None, type=None: {
                "table_name": "invalid_table",
                "page": 1,
                "per_page": 10,
                "order": "desc",
                "order_by": "response_count",
                "day": "",
                "status": "",
            }.get(k, d)
        )

        # Setup mock manager
        mock_manager = mock_load_data_manager.return_value
        mock_manager.get_logs.return_value = []
        mock_manager.count_all.return_value = 0
        mock_manager.sum_response_count.return_value = 0

        result = view_logs_new(view_logs_request_handler(request, ["logs", "list_logs"]))

        # Should default to "logs" table
        assert result["tab"]["table_name"] == "logs"

    @patch("src.app.logs_db.logs_bot.load_data_manager")
    def test_view_logs_formats_request_data(self, mock_load_data_manager, mock_request):
        """Test that view_logs replaces underscores in request_data."""
        from src.app.logs_db.logs_bot import view_logs_new
        from src.app.handler import view_logs_request_handler

        mock_manager = mock_load_data_manager.return_value
        mock_manager.get_logs.return_value = [
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
        mock_manager.count_all.return_value = 1
        mock_manager.sum_response_count.return_value = 5

        result = view_logs_new(view_logs_request_handler(mock_request, ["logs", "list_logs"]))

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

    @patch("src.app.logs_db.logs_bot.load_data_manager")
    def test_view_logs_invalid_order_by_defaults_to_timestamp(
        self, mock_load_data_manager, mock_request
    ):
        """Test view_logs with invalid order_by defaults to timestamp."""
        from src.app.logs_db.logs_bot import view_logs_new
        from src.app.handler import view_logs_request_handler

        mock_manager = mock_load_data_manager.return_value
        mock_manager.get_logs.return_value = []
        mock_manager.count_all.return_value = 0
        mock_manager.sum_response_count.return_value = 0

        def mock_get(key, default=None, type=None):
            return {
                "page": 1,
                "per_page": 10,
                "order": "desc",
                "order_by": "invalid_column",
                "day": "",
                "status": "",
            }.get(key, default)

        mock_request.args.get = MagicMock(side_effect=mock_get)

        view_logs_new(view_logs_request_handler(mock_request, ["logs", "list_logs"]))

        # Should default to timestamp for order_by
        call_args = mock_manager.get_logs.call_args
        assert call_args[1]["order_by"] == "timestamp"


class TestRetrieveLogsByDateEdgeCases:
    """Tests for edge cases in view_logs_by_date function."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock Flask request object."""
        request = MagicMock()
        request.args = MagicMock()
        return request
