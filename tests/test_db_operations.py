# -*- coding: utf-8 -*-
"""
Tests for database operations and edge cases.
"""
import sqlite3
from unittest.mock import patch

import pytest

from src.main_app.logs_db.db import Database


class TestFetchLogsEdgeCases:
    """Tests for edge cases in fetch operations."""

    @pytest.fixture
    def temp_db(self, tmp_path):
        """Create a temporary database for testing."""
        db_file = tmp_path / "test_edge.db"
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()

        cursor.execute(
            """
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
        """
        )

        conn.commit()
        conn.close()
        yield str(db_file)

    @pytest.fixture
    def temp_db_instance(self, temp_db) -> Database:
        from src.main_app.logs_db.db import Database
        db_instance = Database(temp_db)
        return db_instance

    def test_fetch_all_empty_table(self, temp_db_instance):
        """Test fetch on empty table returns empty list."""
        result = temp_db_instance.fetch("SELECT * FROM logs")
        assert result == []

    def test_fetch_all_with_special_characters(self, temp_db_instance):
        """Test fetch handles special characters in data."""
        # Insert data with special characters
        temp_db_instance.commit(
            "INSERT INTO logs (endpoint, request_data, response_status, response_time) VALUES (?, ?, ?, ?)",
            ["/api/test", "Category:Test'Quote\"Double", "تصنيف:اختبار", 0.1],
        )

        result = temp_db_instance.fetch("SELECT * FROM logs")
        assert len(result) == 1
        assert "Quote" in result[0]["request_data"]

    def test_fetch_all_with_unicode(self, temp_db_instance):
        """Test fetch handles Arabic and other unicode."""
        # Insert Arabic data
        temp_db_instance.commit(
            "INSERT INTO logs (endpoint, request_data, response_status, response_time) VALUES (?, ?, ?, ?)",
            ["/api/test", "تصنيف:اختبار_عربي", "تصنيف:نتيجة", 0.1],
        )

        result = temp_db_instance.fetch("SELECT * FROM logs")
        assert len(result) == 1
        assert "عربي" in result[0]["request_data"]


class TestDatabaseErrorHandling:
    """Tests for database error handling."""

    def test_db_commit_invalid_sql(self, tmp_path):
        """Test commit handles invalid SQL gracefully."""
        from src.main_app.logs_db.db import Database

        db_file = tmp_path / "test_error.db"
        conn = sqlite3.connect(str(db_file))
        conn.close()

        db_instance = Database(str(db_file))
        result = db_instance.commit("INVALID SQL STATEMENT")
        # Should return False on error
        assert result is False

    def test_fetch_all_handles_missing_table(self, tmp_path):
        """Test fetch behavior with missing table."""
        from src.main_app.logs_db.db import Database

        db_file = tmp_path / "test_missing.db"
        conn = sqlite3.connect(str(db_file))
        conn.close()

        db_instance = Database(str(db_file))
        # This should handle the error gracefully and return empty list
        result = db_instance.fetch("SELECT * FROM nonexistent_table")
        assert result == []


class TestAllLogsEn2Ar:
    """Tests for all_logs_en2ar function."""

    @pytest.fixture
    def temp_db_with_logs(self, tmp_path):
        """Create temp database with log data."""
        db_file = tmp_path / "test_en2ar.db"
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()

        cursor.execute(
            """
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
        """
        )

        # Insert test data
        cursor.execute(
            "INSERT INTO logs (endpoint, request_data, response_status, date_only) VALUES (?, ?, ?, ?)",
            ["/api/test", "Category:Test1", "تصنيف:اختبار1", "2025-01-27"],
        )
        cursor.execute(
            "INSERT INTO logs (endpoint, request_data, response_status, date_only) VALUES (?, ?, ?, ?)",
            ["/api/test", "Category:Test2", "no_result", "2025-01-27"],
        )
        cursor.execute(
            "INSERT INTO logs (endpoint, request_data, response_status, date_only) VALUES (?, ?, ?, ?)",
            ["/api/test", "Category:Test3", "تصنيف:اختبار3", "2025-01-26"],
        )

        conn.commit()
        conn.close()
        yield str(db_file)

    @pytest.fixture
    def temp_manager(self, temp_db_with_logs):
        from src.main_app.logs_db.bot import LogsManager
        from src.main_app.logs_db.db import Database

        db_instance = Database(temp_db_with_logs)
        manager = LogsManager(db=db_instance, allowed_tables={})
        return manager

    def test_all_logs_en2ar_returns_dict(self, temp_manager):
        """Test all_logs_en2ar returns dictionary."""
        result = temp_manager.all_logs_en2ar()
        assert isinstance(result, dict)
        assert len(result) == 3

    def test_all_logs_en2ar_with_day_filter(self, temp_manager):
        """Test all_logs_en2ar filters by day."""
        result = temp_manager.all_logs_en2ar(day="2025-01-27")
        assert len(result) == 2

    def test_all_logs_en2ar_with_month_filter(self, temp_manager):
        """Test all_logs_en2ar filters by month."""
        result = temp_manager.all_logs_en2ar(day="2025-01")
        assert len(result) == 3  # All in January


class TestFetchLogsByDate:
    """Tests for fetch_logs_by_date function."""

    @pytest.fixture
    def temp_db_grouped(self, tmp_path):
        """Create temp database with grouped log data."""
        db_file = tmp_path / "test_grouped.db"
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()

        cursor.execute(
            """
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
        """
        )

        # Insert varied test data
        for i in range(5):
            cursor.execute(
                "INSERT INTO logs (endpoint, request_data, response_status, response_count, date_only) VALUES (?, ?, ?, ?, ?)",
                ["/api/test", f"Category:Test{i}", "no_result", 2, "2025-01-27"],
            )
        for i in range(3):
            cursor.execute(
                "INSERT INTO logs (endpoint, request_data, response_status, response_count, date_only) VALUES (?, ?, ?, ?, ?)",
                ["/api/test", f"Category:Arabic{i}", "تصنيف:نتيجة", 1, "2025-01-27"],
            )
        for i in range(2):
            cursor.execute(
                "INSERT INTO logs (endpoint, request_data, response_status, response_count, date_only) VALUES (?, ?, ?, ?, ?)",
                ["/api/test", f"Category:Yesterday{i}", "no_result", 1, "2025-01-26"],
            )

        conn.commit()
        conn.close()
        yield str(db_file)

    @pytest.fixture
    def manager(self, temp_db_grouped):
        """Create LogsManager instance for testing."""
        from src.main_app.logs_db.bot import LogsManager
        from src.main_app.logs_db.db import Database

        db_instance = Database(temp_db_grouped)
        return LogsManager(db=db_instance, allowed_tables={"logs"})

    def test_fetch_logs_by_date_groups_correctly(self, manager):
        """Test fetch_logs_by_date groups by date and status."""
        result = manager.fetch_logs_by_date()
        assert isinstance(result, list)
        # Should have grouped entries
        assert len(result) > 0


class TestGetResponseStatus:
    """Tests for get_response_status function."""

    @pytest.fixture
    def temp_db_status(self, tmp_path):
        """Create temp database with various statuses."""
        db_file = tmp_path / "test_status.db"
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()

        cursor.execute(
            """
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
        """
        )

        # Insert data with different statuses (need > 2 of each for it to appear)
        for i in range(5):
            cursor.execute(
                "INSERT INTO logs (endpoint, request_data, response_status) VALUES (?, ?, ?)",
                ["/api/test", f"data_{i}", "no_result"],
            )
        for i in range(3):
            cursor.execute(
                "INSERT INTO logs (endpoint, request_data, response_status) VALUES (?, ?, ?)",
                ["/api/test", f"success_data_{i}", "success"],
            )
        # Only 2 of this status - should not appear (need > 2)
        for i in range(2):
            cursor.execute(
                "INSERT INTO logs (endpoint, request_data, response_status) VALUES (?, ?, ?)",
                ["/api/test", f"rare_data_{i}", "rare_status"],
            )

        conn.commit()
        conn.close()
        yield str(db_file)

    @pytest.fixture
    def manager(self, temp_db_status):
        """Create LogsManager instance for testing."""
        from src.main_app.logs_db.bot import LogsManager
        from src.main_app.logs_db.db import Database

        db_instance = Database(temp_db_status)
        return LogsManager(db=db_instance, allowed_tables={"logs"})

    def test_get_response_status_returns_list(self, manager):
        """Test get_response_status returns list of statuses."""
        result = manager.get_response_status()
        assert isinstance(result, list)
        assert "no_result" in result
        assert "success" in result
        # rare_status should not appear (only 2 occurrences)
        assert "rare_status" not in result


class TestInitDb:
    """Tests for init_tables function."""

    def test_init_db_creates_tables(self, tmp_path):
        """Test init_tables creates both logs and list_logs tables."""
        from src.main_app.logs_db.db import Database

        db_file = tmp_path / "test_init.db"

        # Create a fresh database with no tables
        conn = sqlite3.connect(str(db_file))
        conn.close()

        # Run init_tables
        db_instance = Database(str(db_file))
        db_instance.init_tables()

        # Verify tables were created
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        assert "logs" in tables
        assert "list_logs" in tables

        # Verify logs table structure
        cursor.execute("PRAGMA table_info(logs)")
        log_columns = {row[1]: row[2] for row in cursor.fetchall()}
        assert "id" in log_columns
        assert "endpoint" in log_columns
        assert "request_data" in log_columns
        assert "response_status" in log_columns

        conn.close()

    def test_init_db_is_idempotent(self, tmp_path):
        """Test init_tables can be called multiple times safely."""
        from src.main_app.logs_db.db import Database

        db_file = tmp_path / "test_idempotent.db"

        conn = sqlite3.connect(str(db_file))
        conn.close()

        # Run init_tables twice
        db_instance = Database(str(db_file))
        db_instance.init_tables()
        db_instance.init_tables()

        # Should not fail and tables should exist
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        assert "logs" in tables
        assert "list_logs" in tables
