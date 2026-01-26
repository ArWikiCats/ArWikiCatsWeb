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

    @patch("src.app.logs_bot.logs_db")
    def test_view_logs_returns_dict_with_required_keys(self, mock_logs_db, mock_request):
        """Test that view_logs returns a dict with expected keys."""
        from src.app.logs_bot import view_logs

        # Setup mocks
        mock_logs_db.get_logs.return_value = []
        mock_logs_db.count_all.return_value = 0
        mock_logs_db.sum_response_count.return_value = 0
        mock_logs_db.get_response_status.return_value = ["no_result"]

        result = view_logs(mock_request)

        assert isinstance(result, dict)
        assert "logs" in result
        assert "tab" in result
        assert "status_table" in result

    @patch("src.app.logs_bot.logs_db")
    def test_view_logs_pagination_defaults(self, mock_logs_db, mock_request):
        """Test that view_logs uses correct pagination defaults."""
        from src.app.logs_bot import view_logs

        mock_logs_db.get_logs.return_value = []
        mock_logs_db.count_all.return_value = 0
        mock_logs_db.sum_response_count.return_value = 0

        result = view_logs(mock_request)

        # Check that get_logs was called with default pagination
        call_args = mock_logs_db.get_logs.call_args
        assert call_args[1]["per_page"] == 10 or call_args[0][0] == 10

    @patch("src.app.logs_bot.logs_db")
    def test_view_logs_validates_table_name(self, mock_logs_db):
        """Test that view_logs validates table_name parameter."""
        from src.app.logs_bot import view_logs

        request = MagicMock()
        request.args.get = MagicMock(side_effect=lambda k, d=None, type=None: {
            "table_name": "invalid_table",
            "page": 1,
            "per_page": 10,
            "order": "desc",
            "order_by": "response_count",
        }.get(k, d))

        mock_logs_db.get_logs.return_value = []
        mock_logs_db.count_all.return_value = 0
        mock_logs_db.sum_response_count.return_value = 0

        result = view_logs(request)

        # Should default to "logs" table
        assert result["tab"]["table_name"] == "logs"

    @patch("src.app.logs_bot.logs_db")
    def test_view_logs_formats_request_data(self, mock_logs_db, mock_request):
        """Test that view_logs replaces underscores in request_data."""
        from src.app.logs_bot import view_logs

        mock_logs_db.get_logs.return_value = [
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
        mock_logs_db.count_all.return_value = 1
        mock_logs_db.sum_response_count.return_value = 5

        result = view_logs(mock_request)

        assert len(result["logs"]) == 1
        assert "_" not in result["logs"][0]["request_data"]
        assert "Test Data Here" in result["logs"][0]["request_data"]


class TestRetrieveLogsByDate:
    """Tests for retrieve_logs_by_date function."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock Flask request object."""
        request = MagicMock()
        request.args.get = MagicMock(return_value=None)
        return request

    @patch("src.app.logs_bot.logs_db")
    def test_retrieve_logs_by_date_returns_dict(self, mock_logs_db, mock_request):
        """Test that retrieve_logs_by_date returns expected structure."""
        from src.app.logs_bot import retrieve_logs_by_date

        mock_logs_db.fetch_logs_by_date.return_value = []

        result = retrieve_logs_by_date(mock_request)

        assert isinstance(result, dict)
        assert "logs" in result
        assert "tab" in result
        assert "logs_data" in result

    @patch("src.app.logs_bot.logs_db")
    def test_retrieve_logs_by_date_aggregates_data(self, mock_logs_db, mock_request):
        """Test that retrieve_logs_by_date properly aggregates data by date."""
        from src.app.logs_bot import retrieve_logs_by_date

        mock_logs_db.fetch_logs_by_date.return_value = [
            {"date_only": "2025-01-27", "status_group": "no_result", "title_count": 5, "count": 10},
            {"date_only": "2025-01-27", "status_group": "Category", "title_count": 3, "count": 5},
            {"date_only": "2025-01-26", "status_group": "no_result", "title_count": 2, "count": 3},
        ]

        result = retrieve_logs_by_date(mock_request)

        assert len(result["logs"]) == 2  # Two unique days

        # Find the 2025-01-27 entry
        day_27 = next((log for log in result["logs"] if log["day"] == "2025-01-27"), None)
        assert day_27 is not None
        assert day_27["title_count"] == 8  # 5 + 3
        assert day_27["total"] == 15  # 10 + 5

    @patch("src.app.logs_bot.logs_db")
    def test_retrieve_logs_by_date_sorts_by_day(self, mock_logs_db, mock_request):
        """Test that logs are sorted by day."""
        from src.app.logs_bot import retrieve_logs_by_date

        mock_logs_db.fetch_logs_by_date.return_value = [
            {"date_only": "2025-01-27", "status_group": "no_result", "title_count": 1, "count": 1},
            {"date_only": "2025-01-25", "status_group": "no_result", "title_count": 1, "count": 1},
            {"date_only": "2025-01-26", "status_group": "no_result", "title_count": 1, "count": 1},
        ]

        result = retrieve_logs_by_date(mock_request)

        days = [log["day"] for log in result["logs"]]
        assert days == sorted(days)


class TestRetrieveLogsEnToAr:
    """Tests for retrieve_logs_en_to_ar function."""

    @patch("src.app.logs_bot.logs_db")
    def test_retrieve_logs_en_to_ar_separates_results(self, mock_logs_db):
        """Test that results are separated into no_result and data_result."""
        from src.app.logs_bot import retrieve_logs_en_to_ar

        mock_logs_db.all_logs_en2ar.return_value = {
            "Category:Test1": "تصنيف:اختبار1",
            "Category:Test2": "no_result",
            "Category:Test3": "تصنيف:اختبار3",
        }

        result = retrieve_logs_en_to_ar()

        assert len(result["no_result"]) == 1
        assert "Category:Test2" in result["no_result"]
        assert len(result["data_result"]) == 2
        assert "Category:Test1" in result["data_result"]
        assert "Category:Test3" in result["data_result"]

    @patch("src.app.logs_bot.logs_db")
    def test_retrieve_logs_en_to_ar_tab_counts(self, mock_logs_db):
        """Test that tab contains correct counts."""
        from src.app.logs_bot import retrieve_logs_en_to_ar

        mock_logs_db.all_logs_en2ar.return_value = {
            "Category:Test1": "تصنيف:اختبار1",
            "Category:Test2": "no_result",
            "Category:Test3": "تصنيف:اختبار3",
        }

        result = retrieve_logs_en_to_ar()

        assert result["tab"]["sum_all"] == "3"
        assert result["tab"]["sum_data_result"] == "2"
        assert result["tab"]["sum_no_result"] == "1"

    @patch("src.app.logs_bot.logs_db")
    def test_retrieve_logs_en_to_ar_with_day_parameter(self, mock_logs_db):
        """Test that day parameter is passed to the database function."""
        from src.app.logs_bot import retrieve_logs_en_to_ar

        mock_logs_db.all_logs_en2ar.return_value = {}

        retrieve_logs_en_to_ar(day="2025-01-27")

        mock_logs_db.all_logs_en2ar.assert_called_once_with(day="2025-01-27")

    @patch("src.app.logs_bot.logs_db")
    def test_retrieve_logs_en_to_ar_empty_results(self, mock_logs_db):
        """Test handling of empty results."""
        from src.app.logs_bot import retrieve_logs_en_to_ar

        mock_logs_db.all_logs_en2ar.return_value = {}

        result = retrieve_logs_en_to_ar()

        assert result["no_result"] == []
        assert result["data_result"] == {}
        assert result["tab"]["sum_all"] == "0"
