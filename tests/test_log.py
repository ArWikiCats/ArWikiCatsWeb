# filepath: d:\CatsOrg\web\tests\test_log.py
# -*- coding: utf-8 -*-
"""
Tests for the logs database functionality.
"""
import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest


class TestAddStatus:
    """Tests for the add_status function."""

    def test_add_status_with_status(self):
        """Test add_status adds correct WHERE clause for status."""
        from src.app.logs_db.bot import add_status

        query = "SELECT * FROM logs"
        params = []
        result_query, result_params = add_status(query, params, status="no_result")

        assert "WHERE" in result_query
        assert "response_status = ?" in result_query
        assert "no_result" in result_params

    def test_add_status_with_category(self):
        """Test add_status handles 'Category' status specially."""
        from src.app.logs_db.bot import add_status

        query = "SELECT * FROM logs"
        params = []
        result_query, result_params = add_status(query, params, status="Category")

        assert "WHERE" in result_query
        assert "response_status like 'تصنيف%'" in result_query
        assert len(result_params) == 0  # No params added for Category

    def test_add_status_with_like(self):
        """Test add_status adds LIKE clause correctly."""
        from src.app.logs_db.bot import add_status

        query = "SELECT * FROM logs"
        params = []
        result_query, result_params = add_status(query, params, like="test%")

        assert "WHERE" in result_query
        assert "response_status like ?" in result_query
        assert "test%" in result_params

    def test_add_status_with_valid_day(self):
        """Test add_status adds date filter for valid day format."""
        from src.app.logs_db.bot import add_status

        query = "SELECT * FROM logs"
        params = []
        result_query, result_params = add_status(query, params, day="2025-01-27")

        assert "WHERE" in result_query
        assert "date_only = ?" in result_query
        assert "2025-01-27" in result_params

    def test_add_status_with_invalid_day(self):
        """Test add_status ignores invalid day format."""
        from src.app.logs_db.bot import add_status

        query = "SELECT * FROM logs"
        params = []
        result_query, result_params = add_status(query, params, day="invalid-date")

        assert "date_only" not in result_query
        assert len(result_params) == 0

    def test_add_status_with_multiple_conditions(self):
        """Test add_status combines multiple conditions with AND."""
        from src.app.logs_db.bot import add_status

        query = "SELECT * FROM logs"
        params = []
        result_query, result_params = add_status(
            query, params, status="no_result", day="2025-01-27"
        )

        assert "WHERE" in result_query
        assert "AND" in result_query
        assert len(result_params) == 2

    def test_add_status_with_tuple_params(self):
        """Test add_status converts tuple params to list."""
        from src.app.logs_db.bot import add_status

        query = "SELECT * FROM logs"
        params = ()  # tuple instead of list
        result_query, result_params = add_status(query, params, status="no_result")

        assert isinstance(result_params, list)
        assert "no_result" in result_params


class TestDatabaseOperations:
    """Tests for database operations with a temporary database."""

    @pytest.fixture
    def temp_db(self, tmp_path):
        """Create a temporary database for testing."""
        db_file = tmp_path / "test_logs.db"
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()

        # Create logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint TEXT NOT NULL,
                request_data TEXT NOT NULL,
                response_status TEXT NOT NULL,
                response_time REAL,
                response_count INTEGER DEFAULT 1,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                date_only DATE DEFAULT (DATE('now')),
                UNIQUE(request_data, response_status, date_only)
            );
        """)

        # Create list_logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS list_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint TEXT NOT NULL,
                request_data TEXT NOT NULL,
                response_status TEXT NOT NULL,
                response_time REAL,
                response_count INTEGER DEFAULT 1,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                date_only DATE DEFAULT (DATE('now')),
                UNIQUE(request_data, response_status, date_only)
            );
        """)

        # Insert test data
        cursor.execute("""
            INSERT INTO logs (endpoint, request_data, response_status, response_time, response_count, date_only)
            VALUES ('/api/test', 'Category:Test', 'تصنيف:اختبار', 0.5, 10, '2025-01-27')
        """)
        cursor.execute("""
            INSERT INTO logs (endpoint, request_data, response_status, response_time, response_count, date_only)
            VALUES ('/api/test2', 'Category:Another', 'no_result', 0.3, 5, '2025-01-27')
        """)
        cursor.execute("""
            INSERT INTO logs (endpoint, request_data, response_status, response_time, response_count, date_only)
            VALUES ('/api/test3', 'Category:Third', 'success', 0.2, 3, '2025-01-26')
        """)

        conn.commit()
        conn.close()

        yield str(db_file)

    def test_fetch_all_returns_list(self, temp_db):
        """Test that fetch_all returns a list of dictionaries."""
        from src.app.logs_db import db

        # Patch the db_path_main to use our temp database
        original_path = db.db_path_main[1]
        db.db_path_main[1] = temp_db

        try:
            result = db.fetch_all("SELECT * FROM logs")
            assert isinstance(result, list)
            assert len(result) == 3
            assert all(isinstance(row, dict) for row in result)
        finally:
            db.db_path_main[1] = original_path

    def test_fetch_all_fetch_one(self, temp_db):
        """Test that fetch_all with fetch_one=True returns single dict."""
        from src.app.logs_db import db

        original_path = db.db_path_main[1]
        db.db_path_main[1] = temp_db

        try:
            result = db.fetch_all(
                "SELECT * FROM logs WHERE id = ?", [1], fetch_one=True
            )
            assert isinstance(result, dict)
            assert result["id"] == 1
        finally:
            db.db_path_main[1] = original_path

    def test_fetch_all_no_result(self, temp_db):
        """Test fetch_all returns empty list when no results."""
        from src.app.logs_db import db

        original_path = db.db_path_main[1]
        db.db_path_main[1] = temp_db

        try:
            result = db.fetch_all(
                "SELECT * FROM logs WHERE id = ?", [999]
            )
            assert result == []
        finally:
            db.db_path_main[1] = original_path

    def test_db_commit_success(self, temp_db):
        """Test that db_commit returns True on success."""
        from src.app.logs_db import db

        original_path = db.db_path_main[1]
        db.db_path_main[1] = temp_db

        try:
            result = db.db_commit(
                "INSERT INTO logs (endpoint, request_data, response_status, response_time) VALUES (?, ?, ?, ?)",
                ["/api/new", "NewData", "success", 0.1]
            )
            assert result is True
        finally:
            db.db_path_main[1] = original_path


class TestLogRequest:
    """Tests for the log_request function."""

    @pytest.fixture
    def mock_db(self):
        """Mock database functions."""
        with patch("app.logs_db.bot.db_commit") as mock_commit:
            mock_commit.return_value = True
            yield mock_commit

    def test_log_request_rounds_response_time(self, mock_db):
        """Test that response_time is rounded to 3 decimal places."""
        from src.app.logs_db.bot import log_request

        log_request("/api/test", "test_data", "success", 0.123456789)

        # Check that the call was made with rounded time
        call_args = mock_db.call_args
        assert call_args[0][1][3] == 0.123  # 4th param is response_time

    def test_log_request_uses_logs_table(self, mock_db):
        """Test that non-list endpoints use the 'logs' table."""
        from src.app.logs_db.bot import log_request

        log_request("/api/test", "test_data", "success", 0.1)

        call_args = mock_db.call_args
        assert "logs" in call_args[0][0]
        assert "list_logs" not in call_args[0][0]

    def test_log_request_uses_list_logs_table(self, mock_db):
        """Test that /api/list endpoint uses 'list_logs' table."""
        from src.app.logs_db.bot import log_request

        log_request("/api/list", "test_data", "success", 0.1)

        call_args = mock_db.call_args
        assert "list_logs" in call_args[0][0]

    def test_log_request_converts_status_to_string(self, mock_db):
        """Test that response_status is converted to string."""
        from src.app.logs_db.bot import log_request

        log_request("/api/test", "test_data", 200, 0.1)

        call_args = mock_db.call_args
        assert call_args[0][1][2] == "200"  # 3rd param is response_status


class TestCountAll:
    """Tests for the count_all function."""

    @pytest.fixture
    def temp_db_with_data(self, tmp_path):
        """Create a temp database with test data."""
        db_file = tmp_path / "test_count.db"
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint TEXT NOT NULL,
                request_data TEXT NOT NULL,
                response_status TEXT NOT NULL,
                response_time REAL,
                response_count INTEGER DEFAULT 1,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                date_only DATE DEFAULT (DATE('now'))
            );
        """)

        # Insert 5 rows with no_result, 3 with success
        for i in range(5):
            cursor.execute(
                "INSERT INTO logs (endpoint, request_data, response_status, response_time) VALUES (?, ?, ?, ?)",
                ["/api/test", f"data_{i}", "no_result", 0.1]
            )
        for i in range(3):
            cursor.execute(
                "INSERT INTO logs (endpoint, request_data, response_status, response_time) VALUES (?, ?, ?, ?)",
                ["/api/test", f"success_data_{i}", "success", 0.1]
            )

        conn.commit()
        conn.close()
        yield str(db_file)

    def test_count_all_total(self, temp_db_with_data):
        """Test count_all returns total count without filters."""
        from src.app.logs_db import db, bot

        original_path = db.db_path_main[1]
        db.db_path_main[1] = temp_db_with_data

        try:
            result = bot.count_all()
            assert result == 8
        finally:
            db.db_path_main[1] = original_path

    def test_count_all_with_status(self, temp_db_with_data):
        """Test count_all with status filter."""
        from src.app.logs_db import db, bot

        original_path = db.db_path_main[1]
        db.db_path_main[1] = temp_db_with_data

        try:
            result = bot.count_all(status="no_result")
            assert result == 5
        finally:
            db.db_path_main[1] = original_path


class TestGetLogs:
    """Tests for the get_logs function."""

    @pytest.fixture
    def temp_db_for_logs(self, tmp_path):
        """Create a temp database for logs testing."""
        db_file = tmp_path / "test_get_logs.db"
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint TEXT NOT NULL,
                request_data TEXT NOT NULL,
                response_status TEXT NOT NULL,
                response_time REAL,
                response_count INTEGER DEFAULT 1,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                date_only DATE DEFAULT (DATE('now'))
            );
        """)

        # Insert test data with different response_counts
        for i in range(15):
            cursor.execute(
                "INSERT INTO logs (endpoint, request_data, response_status, response_time, response_count) VALUES (?, ?, ?, ?, ?)",
                ["/api/test", f"data_{i}", "success", 0.1, i + 1]
            )

        conn.commit()
        conn.close()
        yield str(db_file)

    def test_get_logs_pagination(self, temp_db_for_logs):
        """Test get_logs respects pagination parameters."""
        from src.app.logs_db import db, bot

        original_path = db.db_path_main[1]
        db.db_path_main[1] = temp_db_for_logs

        try:
            result = bot.get_logs(per_page=5, offset=0)
            assert len(result) == 5
        finally:
            db.db_path_main[1] = original_path

    def test_get_logs_order_desc(self, temp_db_for_logs):
        """Test get_logs orders DESC by default."""
        from src.app.logs_db import db, bot

        original_path = db.db_path_main[1]
        db.db_path_main[1] = temp_db_for_logs

        try:
            result = bot.get_logs(per_page=5, offset=0, order="DESC", order_by="response_count")
            # Should be ordered by response_count descending
            counts = [row["response_count"] for row in result]
            assert counts == sorted(counts, reverse=True)
        finally:
            db.db_path_main[1] = original_path

    def test_get_logs_order_asc(self, temp_db_for_logs):
        """Test get_logs can order ASC."""
        from src.app.logs_db import db, bot

        original_path = db.db_path_main[1]
        db.db_path_main[1] = temp_db_for_logs

        try:
            result = bot.get_logs(per_page=5, offset=0, order="ASC", order_by="response_count")
            counts = [row["response_count"] for row in result]
            assert counts == sorted(counts)
        finally:
            db.db_path_main[1] = original_path

    def test_get_logs_invalid_order_defaults_to_desc(self, temp_db_for_logs):
        """Test get_logs defaults to DESC for invalid order."""
        from src.app.logs_db import db, bot

        original_path = db.db_path_main[1]
        db.db_path_main[1] = temp_db_for_logs

        try:
            result = bot.get_logs(per_page=5, offset=0, order="INVALID", order_by="response_count")
            counts = [row["response_count"] for row in result]
            assert counts == sorted(counts, reverse=True)
        finally:
            db.db_path_main[1] = original_path


class TestSumResponseCount:
    """Tests for sum_response_count function."""

    @pytest.fixture
    def temp_db_for_sum(self, tmp_path):
        """Create temp database for sum testing."""
        db_file = tmp_path / "test_sum.db"
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint TEXT NOT NULL,
                request_data TEXT NOT NULL,
                response_status TEXT NOT NULL,
                response_time REAL,
                response_count INTEGER DEFAULT 1,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                date_only DATE DEFAULT (DATE('now'))
            );
        """)

        # Insert test data
        cursor.execute(
            "INSERT INTO logs (endpoint, request_data, response_status, response_count) VALUES (?, ?, ?, ?)",
            ["/api/test", "data_1", "success", 10]
        )
        cursor.execute(
            "INSERT INTO logs (endpoint, request_data, response_status, response_count) VALUES (?, ?, ?, ?)",
            ["/api/test", "data_2", "success", 20]
        )
        cursor.execute(
            "INSERT INTO logs (endpoint, request_data, response_status, response_count) VALUES (?, ?, ?, ?)",
            ["/api/test", "data_3", "no_result", 5]
        )

        conn.commit()
        conn.close()
        yield str(db_file)

    def test_sum_response_count_total(self, temp_db_for_sum):
        """Test sum_response_count returns total sum."""
        from src.app.logs_db import db, bot

        original_path = db.db_path_main[1]
        db.db_path_main[1] = temp_db_for_sum

        try:
            result = bot.sum_response_count()
            assert result == 35  # 10 + 20 + 5
        finally:
            db.db_path_main[1] = original_path

    def test_sum_response_count_with_status(self, temp_db_for_sum):
        """Test sum_response_count with status filter."""
        from src.app.logs_db import db, bot

        original_path = db.db_path_main[1]
        db.db_path_main[1] = temp_db_for_sum

        try:
            result = bot.sum_response_count(status="success")
            assert result == 30  # 10 + 20
        finally:
            db.db_path_main[1] = original_path


class TestChangeDbPath:
    """Tests for change_db_path function."""

    def test_change_db_path_returns_list_of_dbs(self, tmp_path):
        """Test that change_db_path returns list of .db files."""
        from src.app.logs_db import db

        # Create some test db files
        (tmp_path / "test1.db").touch()
        (tmp_path / "test2.db").touch()
        (tmp_path / "not_a_db.txt").touch()

        original_main_path = db.main_path
        db.main_path = tmp_path

        try:
            result = db.change_db_path("test1.db")
            assert isinstance(result, list)
            assert "test1.db" in result
            assert "test2.db" in result
            assert "not_a_db.txt" not in result
        finally:
            db.main_path = original_main_path
