# -*- coding: utf-8 -*-
"""
Tests for the logs_view module.
"""
from unittest.mock import MagicMock, patch
from src.app.logs_db.logs_view import LogsView, _build_date_index


class TestRetrieveLogsByDate:
    """Tests for view_logs_by_date function."""

    def test_view_logs_by_date_returns_dict(self):
        """Test that view_logs_by_date returns expected structure."""
        mock_manager = MagicMock()
        mock_manager.fetch_logs_by_date.return_value = []
        viewer = LogsView(manager=mock_manager)

        result = viewer.view_logs_by_date(table_name="logs")

        assert isinstance(result, dict)
        assert "logs" in result
        assert "tab" in result
        assert "logs_data" in result

    def test_view_logs_by_date_aggregates_data(self):
        """Test that view_logs_by_date properly aggregates data by date."""
        mock_manager = MagicMock()
        mock_manager.fetch_logs_by_date.return_value = [
            {"date_only": "2025-01-27", "status_group": "no_result", "title_count": 5, "count": 10},
            {"date_only": "2025-01-27", "status_group": "Category", "title_count": 3, "count": 5},
            {"date_only": "2025-01-26", "status_group": "no_result", "title_count": 2, "count": 3},
        ]
        viewer = LogsView(manager=mock_manager)

        result = viewer.view_logs_by_date(table_name="logs")

        assert len(result["logs"]) == 2  # Two unique days

        # Find the 2025-01-27 entry
        day_27 = next((log for log in result["logs"] if log["day"] == "2025-01-27"), None)
        assert day_27 is not None
        assert day_27["title_count"] == 8  # 5 + 3
        assert day_27["total"] == 15  # 10 + 5

    def test_view_logs_by_date_sorts_by_day(self):
        """Test that logs are sorted by day."""
        mock_manager = MagicMock()
        mock_manager.fetch_logs_by_date.return_value = [
            {"date_only": "2025-01-27", "status_group": "no_result", "title_count": 1, "count": 1},
            {"date_only": "2025-01-25", "status_group": "no_result", "title_count": 1, "count": 1},
            {"date_only": "2025-01-26", "status_group": "no_result", "title_count": 1, "count": 1},
        ]
        viewer = LogsView(manager=mock_manager)

        result = viewer.view_logs_by_date(table_name="logs")

        days = [log["day"] for log in result["logs"]]
        assert days == sorted(days)


class TestRetrieveLogsEnToAr:
    """Tests for view_logs_en2ar function."""

    def test_view_logs_en2ar_separates_results(self):
        """Test that results are separated into no_result and data_result."""
        mock_manager = MagicMock()
        mock_manager.all_logs_en2ar.return_value = {
            "Category:Test1": "تصنيف:اختبار1",
            "Category:Test2": "no_result",
            "Category:Test3": "تصنيف:اختبار3",
        }
        viewer = LogsView(manager=mock_manager)

        result = viewer.view_logs_en2ar()

        assert len(result["no_result"]) == 1
        assert "Category:Test2" in result["no_result"]
        assert len(result["data_result"]) == 2
        assert "Category:Test1" in result["data_result"]
        assert "Category:Test3" in result["data_result"]

    def test_view_logs_en2ar_tab_counts(self):
        """Test that tab contains correct counts."""
        mock_manager = MagicMock()
        mock_manager.all_logs_en2ar.return_value = {
            "Category:Test1": "تصنيف:اختبار1",
            "Category:Test2": "no_result",
            "Category:Test3": "تصنيف:اختبار3",
        }
        viewer = LogsView(manager=mock_manager)

        result = viewer.view_logs_en2ar()

        assert result["tab"]["sum_all"] == "3"
        assert result["tab"]["sum_data_result"] == "2"
        assert result["tab"]["sum_no_result"] == "1"

    def test_view_logs_en2ar_with_day_parameter(self):
        """Test that day parameter is passed to the database function."""
        mock_manager = MagicMock()
        mock_manager.all_logs_en2ar.return_value = {}
        viewer = LogsView(manager=mock_manager)

        viewer.view_logs_en2ar(day="2025-01-27")

        mock_manager.all_logs_en2ar.assert_called_once_with(day="2025-01-27")

    def test_view_logs_en2ar_empty_results(self):
        """Test handling of empty results."""
        mock_manager = MagicMock()
        mock_manager.all_logs_en2ar.return_value = {}
        viewer = LogsView(manager=mock_manager)

        result = viewer.view_logs_en2ar()

        assert result["no_result"] == []
        assert result["data_result"] == {}
        assert result["tab"]["sum_all"] == "0"


class TestBuildDateIndex:
    """Tests for the _build_date_index helper function."""

    def test_build_date_index_aggregates_correctly(self):
        """Test that _build_date_index properly aggregates log data."""
        logs_data = [
            {"date_only": "2025-01-27", "status_group": "no_result", "title_count": 5, "count": 10},
            {"date_only": "2025-01-27", "status_group": "Category", "title_count": 3, "count": 5},
            {"date_only": "2025-01-26", "status_group": "no_result", "title_count": 2, "count": 3},
        ]

        result = _build_date_index(logs_data)

        assert len(result) == 2

        # Find the 2025-01-27 entry
        day_27 = next((log for log in result if log["day"] == "2025-01-27"), None)
        assert day_27 is not None
        assert day_27["title_count"] == 8  # 5 + 3
        assert day_27["total"] == 15  # 10 + 5
        assert day_27["results"]["no_result"] == 10
        assert day_27["results"]["Category"] == 5

    def test_build_date_index_sorts_by_day(self):
        """Test that _build_date_index sorts results by day."""
        logs_data = [
            {"date_only": "2025-01-27", "status_group": "no_result", "title_count": 1, "count": 1},
            {"date_only": "2025-01-25", "status_group": "no_result", "title_count": 1, "count": 1},
            {"date_only": "2025-01-26", "status_group": "no_result", "title_count": 1, "count": 1},
        ]

        result = _build_date_index(logs_data)

        days = [log["day"] for log in result]
        assert days == ["2025-01-25", "2025-01-26", "2025-01-27"]

    def test_build_date_index_empty_input(self):
        """Test that _build_date_index handles empty input."""
        result = _build_date_index([])
        assert result == []


