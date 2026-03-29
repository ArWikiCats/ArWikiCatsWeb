"""Unit tests for src/main_app/logs_db/bot.py"""

import re
from unittest.mock import Mock, patch

import pytest

from src.main_app.logs_db.bot import LogsManager


class TestLogsManagerInit:
    """Tests for LogsManager initialization."""

    def test_init_stores_db_and_allowed_tables(self):
        """LogsManager stores db and allowed_tables."""
        mock_db = Mock()
        manager = LogsManager(db=mock_db, allowed_tables={"logs", "list_logs"})

        assert manager._db == mock_db
        assert manager.allowed_tables == {"logs", "list_logs"}


class TestLogsManagerValidation:
    """Tests for LogsManager validation methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock()
        self.manager = LogsManager(db=self.mock_db, allowed_tables={"logs", "list_logs"})

    def test_validate_table_valid(self):
        """_validate_table passes for valid table names."""
        # Should not raise
        self.manager._validate_table("logs")
        self.manager._validate_table("list_logs")

    def test_validate_table_invalid_raises(self):
        """_validate_table raises for invalid table names."""
        with pytest.raises(ValueError, match="Invalid table name"):
            self.manager._validate_table("invalid_table")

    def test_validate_order_valid(self):
        """_validate_order returns valid order values."""
        result = LogsManager._validate_order("ASC")
        assert result == "ASC"

        result = LogsManager._validate_order("DESC")
        assert result == "DESC"

    def test_validate_order_invalid_defaults_to_desc(self):
        """_validate_order returns DESC for invalid values."""
        result = LogsManager._validate_order("INVALID")
        assert result == "DESC"

        result = LogsManager._validate_order("asc")  # lowercase
        assert result == "DESC"

    def test_validate_order_by_valid(self):
        """_validate_order_by passes for valid column names."""
        # Should not raise for valid columns
        for col in LogsManager.ALLOWED_ORDER_BY_COLUMNS:
            self.manager._validate_order_by(col)

    def test_validate_order_by_invalid_raises(self):
        """_validate_order_by raises for invalid column names."""
        with pytest.raises(ValueError, match="Invalid order_by column"):
            self.manager._validate_order_by("invalid_column")

    def test_resolve_table_for_api_list(self):
        """_resolve_table returns 'list_logs' for /api/list endpoint."""
        result = LogsManager._resolve_table("/api/list")
        assert result == "list_logs"

    def test_resolve_table_for_other_endpoints(self):
        """_resolve_table returns 'logs' for other endpoints."""
        result = LogsManager._resolve_table("/api/something")
        assert result == "logs"

        result = LogsManager._resolve_table("/api/title")
        assert result == "logs"


class TestLogsManagerLogRequest:
    """Tests for LogsManager.log_request method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock()
        self.mock_db.commit = Mock(return_value=True)
        self.manager = LogsManager(db=self.mock_db, allowed_tables={"logs", "list_logs"})

    def test_log_request_inserts_into_correct_table(self):
        """log_request inserts into correct table based on endpoint."""
        self.manager.log_request(
            endpoint="/api/test",
            request_data="test_data",
            response_status="success",
            response_time=0.123,
        )

        self.mock_db.commit.assert_called_once()
        call_args = self.mock_db.commit.call_args[0]
        assert "INSERT INTO logs" in call_args[0]

    def test_log_request_uses_list_logs_for_api_list(self):
        """log_request uses list_logs table for /api/list endpoint."""
        self.manager.log_request(
            endpoint="/api/list",
            request_data=["title1", "title2"],
            response_status="success",
            response_time=0.456,
        )

        call_args = self.mock_db.commit.call_args[0]
        assert "INSERT INTO list_logs" in call_args[0]

    def test_log_request_rounds_response_time(self):
        """log_request rounds response_time to 3 decimal places."""
        self.manager.log_request(
            endpoint="/api/test",
            request_data="test",
            response_status="success",
            response_time=0.123456789,
        )

        call_args = self.mock_db.commit.call_args[0][1]
        assert call_args[-1] == 0.123  # rounded to 3 decimals

    def test_log_request_converts_status_to_string(self):
        """log_request converts response_status to string."""
        self.manager.log_request(
            endpoint="/api/test",
            request_data="test",
            response_status=200,  # int
            response_time=0.1,
        )

        call_args = self.mock_db.commit.call_args[0][1]
        assert call_args[2] == "200"

    def test_log_request_uses_upsert_query(self):
        """log_request uses UPSERT (ON CONFLICT) query."""
        self.manager.log_request(
            endpoint="/api/test",
            request_data="test",
            response_status="success",
            response_time=0.1,
        )

        call_args = self.mock_db.commit.call_args[0][0]
        assert "ON CONFLICT" in call_args
        assert "DO UPDATE SET" in call_args

    def test_log_request_returns_true_on_success(self):
        """log_request returns True on success."""
        self.mock_db.commit.return_value = True
        result = self.manager.log_request(
            endpoint="/api/test",
            request_data="test",
            response_status="success",
            response_time=0.1,
        )
        assert result is True

    def test_log_request_reinitializes_tables_on_failure(self):
        """log_request calls init_tables when commit fails."""
        self.mock_db.commit.return_value = False
        self.mock_db.init_tables = Mock()

        self.manager.log_request(
            endpoint="/api/test",
            request_data="test",
            response_status="success",
            response_time=0.1,
        )

        self.mock_db.init_tables.assert_called_once()


class TestLogsManagerApplyFilters:
    """Tests for LogsManager._apply_filters static method."""

    def test_apply_filters_no_filters(self):
        """_apply_filters returns original query when no filters provided."""
        query, params = LogsManager._apply_filters("SELECT * FROM logs", [])
        assert query == "SELECT * FROM logs"
        assert params == []

    def test_apply_filters_status_no_result(self):
        """_apply_filters adds condition for 'no_result' status."""
        query, params = LogsManager._apply_filters(
            "SELECT * FROM logs", [], status="no_result"
        )
        assert "response_status = ?" in query
        assert params == ["no_result"]

    def test_apply_filters_status_all_ignored(self):
        """_apply_filters ignores 'All' status (case insensitive)."""
        query, params = LogsManager._apply_filters(
            "SELECT * FROM logs", [], status="All"
        )
        assert "WHERE" not in query
        assert params == []

        query, params = LogsManager._apply_filters(
            "SELECT * FROM logs", [], status="all"
        )
        assert "WHERE" not in query

    def test_apply_filters_status_category(self):
        """_apply_filters handles 'Category' status with LIKE."""
        query, params = LogsManager._apply_filters(
            "SELECT * FROM logs", [], status="Category"
        )
        assert "response_status LIKE 'تصنيف%'" in query
        assert params == []

    def test_apply_filters_day_valid_date(self):
        """_apply_filters adds day filter for valid YYYY-MM-DD format."""
        query, params = LogsManager._apply_filters(
            "SELECT * FROM logs", [], day="2025-01-15"
        )
        assert "date_only = ?" in query
        assert params == ["2025-01-15"]

    def test_apply_filters_day_invalid_date_ignored(self):
        """_apply_filters ignores invalid day format."""
        query, params = LogsManager._apply_filters(
            "SELECT * FROM logs", [], day="invalid-date"
        )
        assert "WHERE" not in query
        assert params == []

    def test_apply_filters_combined_status_and_day(self):
        """_apply_filters combines status and day filters."""
        query, params = LogsManager._apply_filters(
            "SELECT * FROM logs", [], status="no_result", day="2025-01-15"
        )
        assert "WHERE" in query
        assert "AND" in query
        assert params == ["no_result", "2025-01-15"]


class TestLogsManagerSumResponseCount:
    """Tests for LogsManager.sum_response_count method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock()
        self.manager = LogsManager(db=self.mock_db, allowed_tables={"logs", "list_logs"})

    def test_sum_response_count_validates_table(self):
        """sum_response_count validates table name."""
        with pytest.raises(ValueError):
            self.manager.sum_response_count(table_name="invalid")

    def test_sum_response_count_returns_zero_on_no_result(self):
        """sum_response_count returns 0 when no result."""
        self.mock_db.fetch.return_value = None
        result = self.manager.sum_response_count()
        assert result == 0

    def test_sum_response_count_returns_sum(self):
        """sum_response_count returns sum from database."""
        self.mock_db.fetch.return_value = {"count_all": 100}
        result = self.manager.sum_response_count()
        assert result == 100

    def test_sum_response_count_applies_filters(self):
        """sum_response_count applies status and day filters."""
        self.mock_db.fetch.return_value = {"count_all": 50}
        result = self.manager.sum_response_count(
            status="Category", day="2025-01-15"
        )
        assert result == 50


class TestLogsManagerCountAll:
    """Tests for LogsManager.count_all method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock()
        self.manager = LogsManager(db=self.mock_db, allowed_tables={"logs", "list_logs"})

    def test_count_all_validates_table(self):
        """count_all validates table name."""
        with pytest.raises(ValueError):
            self.manager.count_all(table_name="invalid")

    def test_count_all_returns_zero_on_no_result(self):
        """count_all returns 0 when no result."""
        self.mock_db.fetch.return_value = None
        result = self.manager.count_all()
        assert result == 0

    def test_count_all_returns_count(self):
        """count_all returns count from database."""
        self.mock_db.fetch.return_value = {"total": 42}
        result = self.manager.count_all()
        assert result == 42


class TestLogsManagerGetResponseStatus:
    """Tests for LogsManager.get_response_status method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock()
        self.manager = LogsManager(db=self.mock_db, allowed_tables={"logs", "list_logs"})

    def test_get_response_status_validates_table(self):
        """get_response_status validates table name."""
        with pytest.raises(ValueError):
            self.manager.get_response_status(table_name="invalid")

    def test_get_response_status_returns_list(self):
        """get_response_status returns list of statuses."""
        self.mock_db.fetch.return_value = [
            {"response_status": "no_result"},
            {"response_status": "Category"},
        ]
        result = self.manager.get_response_status()
        assert result == ["no_result", "Category"]

    def test_get_response_status_empty_result(self):
        """get_response_status returns empty list for no results."""
        self.mock_db.fetch.return_value = []
        result = self.manager.get_response_status()
        assert result == []


class TestLogsManagerGetLogs:
    """Tests for LogsManager.get_logs method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock()
        self.manager = LogsManager(db=self.mock_db, allowed_tables={"logs", "list_logs"})

    def test_get_logs_validates_table(self):
        """get_logs validates table name."""
        with pytest.raises(ValueError):
            self.manager.get_logs(table_name="invalid")

    def test_get_logs_validates_order_by(self):
        """get_logs validates order_by column."""
        with pytest.raises(ValueError):
            self.manager.get_logs(order_by="invalid_column")

    def test_get_logs_builds_query_with_ordering(self):
        """get_logs builds query with ORDER BY clause."""
        self.mock_db.fetch.return_value = []
        self.manager.get_logs(
            per_page=10,
            offset=20,
            order="ASC",
            order_by="timestamp",
        )

        self.mock_db.fetch.assert_called_once()
        call_args = self.mock_db.fetch.call_args[0][0]
        assert "ORDER BY timestamp ASC" in call_args
        assert "LIMIT ? OFFSET ?" in call_args

    def test_get_logs_applies_filters(self):
        """get_logs applies status and day filters."""
        self.mock_db.fetch.return_value = []
        self.manager.get_logs(
            status="no_result",
            day="2025-01-15",
        )

        call_args = self.mock_db.fetch.call_args[0]
        assert "WHERE" in call_args[0]

    def test_get_logs_returns_results(self):
        """get_logs returns results from database."""
        expected_results = [
            {"id": 1, "endpoint": "/api/test"},
            {"id": 2, "endpoint": "/api/list"},
        ]
        self.mock_db.fetch.return_value = expected_results
        result = self.manager.get_logs()
        assert result == expected_results


class TestLogsManagerFetchLogsByDate:
    """Tests for LogsManager.fetch_logs_by_date method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock()
        self.manager = LogsManager(db=self.mock_db, allowed_tables={"logs", "list_logs"})

    def test_fetch_logs_by_date_validates_table(self):
        """fetch_logs_by_date validates table name."""
        with pytest.raises(ValueError):
            self.manager.fetch_logs_by_date(table_name="invalid")

    def test_fetch_logs_by_date_returns_results(self):
        """fetch_logs_by_date returns results from database."""
        expected_results = [
            {"date_only": "2025-01-15", "status_group": "no_result", "title_count": 5, "count": 10},
        ]
        self.mock_db.fetch.return_value = expected_results
        result = self.manager.fetch_logs_by_date()
        assert result == expected_results

    def test_fetch_logs_by_date_groups_by_category(self):
        """fetch_logs_by_date normalizes Arabic statuses to 'Category'."""
        # The SQL query handles the CASE WHEN for 'تصنيف%' -> 'Category'
        self.mock_db.fetch.return_value = [
            {"date_only": "2025-01-15", "status_group": "Category", "title_count": 3, "count": 6},
        ]
        result = self.manager.fetch_logs_by_date()
        assert len(result) == 1
        assert result[0]["status_group"] == "Category"


class TestLogsManagerAllLogsEn2Ar:
    """Tests for LogsManager.all_logs_en2ar method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock()
        self.manager = LogsManager(db=self.mock_db, allowed_tables={"logs", "list_logs"})

    def test_all_logs_en2ar_no_day_filter(self):
        """all_logs_en2ar works without day filter."""
        self.mock_db.fetch.return_value = [
            {"request_data": "title1", "response_status": "result1"},
            {"request_data": "title2", "response_status": "no_result"},
        ]
        result = self.manager.all_logs_en2ar()
        assert "title1" in result
        assert "title2" in result

    def test_all_logs_en2ar_with_full_date(self):
        """all_logs_en2ar filters by full date YYYY-MM-DD."""
        self.mock_db.fetch.return_value = []
        self.manager.all_logs_en2ar(day="2025-01-15")

        call_args = self.mock_db.fetch.call_args[0]
        assert "date_only = ?" in call_args[0]

    def test_all_logs_en2ar_with_year_month(self):
        """all_logs_en2ar filters by year-month YYYY-MM."""
        self.mock_db.fetch.return_value = []
        self.manager.all_logs_en2ar(day="2025-01")

        call_args = self.mock_db.fetch.call_args[0]
        assert "strftime('%Y-%m', date_only) = ?" in call_args[0]

    def test_all_logs_en2ar_invalid_day_ignored(self):
        """all_logs_en2ar ignores invalid day format."""
        self.mock_db.fetch.return_value = [
            {"request_data": "title1", "response_status": "result1"},
        ]
        result = self.manager.all_logs_en2ar(day="invalid")
        # Should still return results (no filter applied)
        assert len(result) == 1

    def test_all_logs_en2ar_prefers_non_no_result(self):
        """all_logs_en2ar prefers non-'no_result' status for duplicates."""
        self.mock_db.fetch.return_value = [
            {"request_data": "title1", "response_status": "no_result"},
            {"request_data": "title1", "response_status": "actual_result"},
        ]
        result = self.manager.all_logs_en2ar()
        assert result["title1"] == "actual_result"

    def test_all_logs_en2ar_returns_dict(self):
        """all_logs_en2ar returns dict mapping."""
        self.mock_db.fetch.return_value = [
            {"request_data": "title1", "response_status": "result1"},
        ]
        result = self.manager.all_logs_en2ar()
        assert isinstance(result, dict)
        assert result == {"title1": "result1"}
