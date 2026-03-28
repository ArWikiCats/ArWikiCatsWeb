# -*- coding: utf-8 -*-
"""
Tests for database operations and edge cases.
"""
import sqlite3
from unittest.mock import patch

import pytest


class TestFetchLogsEdgeCases:
    """Tests for edge cases in fetch operations."""

    @pytest.fixture
    def temp_db(self, tmp_path):
        """Create a temporary database for testing."""
        db_file = tmp_path / "test_edge.db"
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

        conn.commit()
        conn.close()
        yield str(db_file)

    def test_fetch_all_empty_table(self, temp_db):
        """Test fetch_all on empty table returns empty list."""
        from src.app.logs_db import db

        with patch.object(db, 'get_db_path_main', return_value=temp_db):
            result = db.fetch_all("SELECT * FROM logs")
            assert result == []

    def test_fetch_all_with_special_characters(self, temp_db):
        """Test fetch_all handles special characters in data."""
        from src.app.logs_db import db

        with patch.object(db, 'get_db_path_main', return_value=temp_db):
            # Insert data with special characters
            db.db_commit(
                "INSERT INTO logs (endpoint, request_data, response_status, response_time) VALUES (?, ?, ?, ?)",
                ["/api/test", "Category:Test'Quote\"Double", "تصنيف:اختبار", 0.1]
            )

            result = db.fetch_all("SELECT * FROM logs")
            assert len(result) == 1
            assert "Quote" in result[0]["request_data"]

    def test_fetch_all_with_unicode(self, temp_db):
        """Test fetch_all handles Arabic and other unicode."""
        from src.app.logs_db import db

        with patch.object(db, 'get_db_path_main', return_value=temp_db):
            # Insert Arabic data
            db.db_commit(
                "INSERT INTO logs (endpoint, request_data, response_status, response_time) VALUES (?, ?, ?, ?)",
                ["/api/test", "تصنيف:اختبار_عربي", "تصنيف:نتيجة", 0.1]
            )

            result = db.fetch_all("SELECT * FROM logs")
            assert len(result) == 1
            assert "عربي" in result[0]["request_data"]


class TestDatabaseErrorHandling:
    """Tests for database error handling."""

    def test_db_commit_invalid_sql(self, tmp_path):
        """Test db_commit handles invalid SQL gracefully."""
        from src.app.logs_db import db

        db_file = tmp_path / "test_error.db"
        conn = sqlite3.connect(str(db_file))
        conn.close()

        with patch.object(db, 'get_db_path_main', return_value=str(db_file)):
            result = db.db_commit("INVALID SQL STATEMENT")
            # Should return the error, not True
            assert result is not True
            assert isinstance(result, sqlite3.Error)

    def test_fetch_all_handles_missing_table(self, tmp_path):
        """Test fetch_all behavior with missing table."""
        from src.app.logs_db import db

        db_file = tmp_path / "test_missing.db"
        conn = sqlite3.connect(str(db_file))
        conn.close()

        with patch.object(db, 'get_db_path_main', return_value=str(db_file)):
            # This should handle the error gracefully
            # The function may print an error or call init_db
            with patch("src.app.logs_db.db.init_db"):
                result = db.fetch_all("SELECT * FROM nonexistent_table")


class TestAllLogsEn2Ar:
    """Tests for all_logs_en2ar function."""

    @pytest.fixture
    def temp_db_with_logs(self, tmp_path):
        """Create temp database with log data."""
        db_file = tmp_path / "test_en2ar.db"
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
            "INSERT INTO logs (endpoint, request_data, response_status, date_only) VALUES (?, ?, ?, ?)",
            ["/api/test", "Category:Test1", "تصنيف:اختبار1", "2025-01-27"]
        )
        cursor.execute(
            "INSERT INTO logs (endpoint, request_data, response_status, date_only) VALUES (?, ?, ?, ?)",
            ["/api/test", "Category:Test2", "no_result", "2025-01-27"]
        )
        cursor.execute(
            "INSERT INTO logs (endpoint, request_data, response_status, date_only) VALUES (?, ?, ?, ?)",
            ["/api/test", "Category:Test3", "تصنيف:اختبار3", "2025-01-26"]
        )

        conn.commit()
        conn.close()
        yield str(db_file)

    def test_all_logs_en2ar_returns_dict(self, temp_db_with_logs):
        """Test all_logs_en2ar returns dictionary."""
        from src.app.logs_db import db, bot

        with patch.object(db, 'get_db_path_main', return_value=temp_db_with_logs):
            result = bot.all_logs_en2ar()
            assert isinstance(result, dict)
            assert len(result) == 3

    def test_all_logs_en2ar_with_day_filter(self, temp_db_with_logs):
        """Test all_logs_en2ar filters by day."""
        from src.app.logs_db import db, bot

        with patch.object(db, 'get_db_path_main', return_value=temp_db_with_logs):
            result = bot.all_logs_en2ar(day="2025-01-27")
            assert len(result) == 2

    def test_all_logs_en2ar_with_month_filter(self, temp_db_with_logs):
        """Test all_logs_en2ar filters by month."""
        from src.app.logs_db import db, bot

        with patch.object(db, 'get_db_path_main', return_value=temp_db_with_logs):
            result = bot.all_logs_en2ar(day="2025-01")
            assert len(result) == 3  # All in January


class TestFetchLogsByDate:
    """Tests for fetch_logs_by_date function."""

    @pytest.fixture
    def temp_db_grouped(self, tmp_path):
        """Create temp database with grouped log data."""
        db_file = tmp_path / "test_grouped.db"
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

        # Insert varied test data
        for i in range(5):
            cursor.execute(
                "INSERT INTO logs (endpoint, request_data, response_status, response_count, date_only) VALUES (?, ?, ?, ?, ?)",
                ["/api/test", f"Category:Test{i}", "no_result", 2, "2025-01-27"]
            )
        for i in range(3):
            cursor.execute(
                "INSERT INTO logs (endpoint, request_data, response_status, response_count, date_only) VALUES (?, ?, ?, ?, ?)",
                ["/api/test", f"Category:Arabic{i}", "تصنيف:نتيجة", 1, "2025-01-27"]
            )
        for i in range(2):
            cursor.execute(
                "INSERT INTO logs (endpoint, request_data, response_status, response_count, date_only) VALUES (?, ?, ?, ?, ?)",
                ["/api/test", f"Category:Yesterday{i}", "no_result", 1, "2025-01-26"]
            )

        conn.commit()
        conn.close()
        yield str(db_file)

    def test_fetch_logs_by_date_groups_correctly(self, temp_db_grouped):
        """Test fetch_logs_by_date groups by date and status."""
        from src.app.logs_db import db, bot

        with patch.object(db, 'get_db_path_main', return_value=temp_db_grouped):
            result = bot.fetch_logs_by_date()
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

        # Insert data with different statuses (need > 2 of each for it to appear)
        for i in range(5):
            cursor.execute(
                "INSERT INTO logs (endpoint, request_data, response_status) VALUES (?, ?, ?)",
                ["/api/test", f"data_{i}", "no_result"]
            )
        for i in range(3):
            cursor.execute(
                "INSERT INTO logs (endpoint, request_data, response_status) VALUES (?, ?, ?)",
                ["/api/test", f"success_data_{i}", "success"]
            )
        # Only 2 of this status - should not appear (need > 2)
        for i in range(2):
            cursor.execute(
                "INSERT INTO logs (endpoint, request_data, response_status) VALUES (?, ?, ?)",
                ["/api/test", f"rare_data_{i}", "rare_status"]
            )

        conn.commit()
        conn.close()
        yield str(db_file)

    def test_get_response_status_returns_list(self, temp_db_status):
        """Test get_response_status returns list of statuses."""
        from src.app.logs_db import db, bot

        with patch.object(db, 'get_db_path_main', return_value=temp_db_status):
            result = bot.get_response_status()
            assert isinstance(result, list)
            assert "no_result" in result
            assert "success" in result
            # rare_status should not appear (only 2 occurrences)
            assert "rare_status" not in result


class TestInitDb:
    """Tests for init_db function."""

    def test_init_db_creates_tables(self, tmp_path):
        """Test init_db creates both logs and list_logs tables."""
        from src.app.logs_db import db

        db_file = tmp_path / "test_init.db"

        with patch.object(db, 'get_db_path_main', return_value=str(db_file)):
            # Create a fresh database with no tables
            import sqlite3
            conn = sqlite3.connect(str(db_file))
            conn.close()

            # Run init_db
            db.init_db()

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
        """Test init_db can be called multiple times safely."""
        from src.app.logs_db import db

        db_file = tmp_path / "test_idempotent.db"

        with patch.object(db, 'get_db_path_main', return_value=str(db_file)):
            import sqlite3
            conn = sqlite3.connect(str(db_file))
            conn.close()

            # Run init_db twice
            db.init_db()
            db.init_db()

            # Should not fail and tables should exist
            conn = sqlite3.connect(str(db_file))
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()

            assert "logs" in tables
            assert "list_logs" in tables
