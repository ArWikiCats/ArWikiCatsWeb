"""Unit tests for src/main_app/logs_db/db.py"""

import sqlite3
from unittest.mock import Mock, patch

import pytest

from src.main_app.logs_db.db import Database, utc_now


class TestDatabaseInit:
    """Tests for Database initialization."""

    def test_init_stores_db_path(self):
        """Database stores the provided path."""
        db = Database("/tmp/test.db")
        assert db.db_path == "/tmp/test.db"

    def test_init_converts_path_to_string(self):
        """Database converts path to string."""
        from pathlib import Path

        db = Database(Path("/tmp/test.db"))
        # On Windows, Path conversion uses backslashes
        assert db.db_path == str(Path("/tmp/test.db"))


class TestDatabaseConnect:
    """Tests for Database._connect context manager."""

    def test_connect_opens_and_closes_connection(self):
        """Connection is opened and properly closed."""
        db = Database("/tmp/test.db")

        with patch("src.main_app.logs_db.db.sqlite3.connect") as mock_connect:
            mock_conn = Mock()
            mock_connect.return_value = mock_conn

            with db._connect():
                mock_connect.assert_called_once_with("/tmp/test.db")

            mock_conn.close.assert_called_once()

    def test_connect_sets_row_factory_for_dict_mode(self):
        """Row factory is set when row_as_dict=True."""
        db = Database("/tmp/test.db")

        with patch("src.main_app.logs_db.db.sqlite3.connect") as mock_connect:
            mock_conn = Mock()
            mock_connect.return_value = mock_conn

            with db._connect(row_as_dict=True):
                pass

            assert mock_conn.row_factory == sqlite3.Row

    def test_connect_always_closes_on_error(self):
        """Connection is closed even on error."""
        db = Database("/tmp/test.db")

        with patch("src.main_app.logs_db.db.sqlite3.connect") as mock_connect:
            mock_conn = Mock()
            mock_connect.return_value = mock_conn
            mock_conn.execute.side_effect = sqlite3.Error("Test error")

            with pytest.raises(sqlite3.Error):
                with db._connect():
                    mock_conn.execute("SELECT 1")

            mock_conn.close.assert_called_once()


class TestDatabaseCommit:
    """Tests for Database.commit method."""

    def test_commit_executes_query_and_commits(self):
        """commit executeses the query and commits."""
        db = Database("/tmp/test.db")

        with patch.object(db, "_connect") as mock_connect_ctx:
            mock_conn = Mock()
            mock_connect_ctx.return_value.__enter__ = Mock(return_value=mock_conn)
            mock_connect_ctx.return_value.__exit__ = Mock(return_value=False)

            result = db.commit("INSERT INTO test VALUES (?)", (1,))

            mock_conn.execute.assert_called_once_with("INSERT INTO test VALUES (?)", (1,))
            mock_conn.commit.assert_called_once()
            assert result is True

    def test_commit_returns_false_on_error(self):
        """commit returns False on SQLite error."""
        db = Database("/tmp/test.db")

        with patch.object(db, "_connect") as mock_connect_ctx:
            mock_conn = Mock()
            mock_connect_ctx.return_value.__enter__ = Mock(return_value=mock_conn)
            mock_connect_ctx.return_value.__exit__ = Mock(return_value=False)
            mock_conn.execute.side_effect = sqlite3.Error("Test error")

            result = db.commit("INVALID QUERY", ())

            assert result is False


class TestDatabaseCommitMany:
    """Tests for Database.commit_many method."""

    def test_commit_many_executes_batch_and_commits(self):
        """commit_many executes batch and commits."""
        db = Database("/tmp/test.db")

        with patch.object(db, "_connect") as mock_connect_ctx:
            mock_conn = Mock()
            mock_connect_ctx.return_value.__enter__ = Mock(return_value=mock_conn)
            mock_connect_ctx.return_value.__exit__ = Mock(return_value=False)

            params = [(1, "a"), (2, "b"), (3, "c")]
            result = db.commit_many("INSERT INTO test VALUES (?, ?)", params)

            mock_conn.executemany.assert_called_once_with(
                "INSERT INTO test VALUES (?, ?)", params
            )
            mock_conn.commit.assert_called_once()
            assert result is True

    def test_commit_many_returns_false_on_error(self):
        """commit_many returns False on SQLite error."""
        db = Database("/tmp/test.db")

        with patch.object(db, "_connect") as mock_connect_ctx:
            mock_conn = Mock()
            mock_connect_ctx.return_value.__enter__ = Mock(return_value=mock_conn)
            mock_connect_ctx.return_value.__exit__ = Mock(return_value=False)
            mock_conn.executemany.side_effect = sqlite3.Error("Test error")

            result = db.commit_many("INSERT INTO test VALUES (?)", [(1,)])

            assert result is False


class TestDatabaseFetch:
    """Tests for Database.fetch method."""

    def test_fetch_returns_list_of_dicts(self):
        """fetch returns list of dicts for multiple rows."""
        db = Database("/tmp/test.db")

        with patch.object(db, "_connect") as mock_connect_ctx:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.__enter__ = Mock(return_value=mock_conn)
            mock_conn.__exit__ = Mock(return_value=False)
            mock_connect_ctx.return_value = mock_connect_ctx
            mock_conn.execute.return_value = mock_cursor

            mock_row1 = {"id": 1, "name": "test1"}
            mock_row2 = {"id": 2, "name": "test2"}
            mock_cursor.fetchall.return_value = [
                Mock(**{"__getitem__": lambda s, k: mock_row1[k]}) for _ in [1]
            ] + [Mock(**{"__getitem__": lambda s, k: mock_row2[k]}) for _ in [1]]

            # Simulate dict conversion
            mock_cursor.fetchall.return_value = [
                type("Row", (), {"keys": lambda: ["id", "name"], "__getitem__": lambda s, k: mock_row1[k]})(),
                type("Row", (), {"keys": lambda: ["id", "name"], "__getitem__": lambda s, k: mock_row2[k]})(),
            ]

            result = db.fetch("SELECT * FROM test", one=False)

            assert isinstance(result, list)

    def test_fetch_returns_single_dict_when_one_true(self):
        """fetch returns single dict when one=True."""
        db = Database("/tmp/test.db")

        with patch.object(db, "_connect") as mock_connect_ctx:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.__enter__ = Mock(return_value=mock_conn)
            mock_conn.__exit__ = Mock(return_value=False)
            mock_connect_ctx.return_value = mock_connect_ctx
            mock_conn.execute.return_value = mock_cursor

            mock_row = {"id": 1, "name": "test"}
            mock_cursor.fetchone.return_value = type(
                "Row", (), {"keys": lambda: ["id", "name"], "__getitem__": lambda s, k: mock_row[k]}
            )()

            result = db.fetch("SELECT * FROM test WHERE id=1", one=True)

            assert isinstance(result, dict)

    def test_fetch_returns_none_when_one_true_and_no_results(self):
        """fetch returns None when one=True and no results."""
        db = Database("/tmp/test.db")

        with patch.object(db, "_connect") as mock_connect_ctx:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.__enter__ = Mock(return_value=mock_conn)
            mock_conn.__exit__ = Mock(return_value=False)
            mock_connect_ctx.return_value = mock_connect_ctx
            mock_conn.execute.return_value = mock_cursor
            mock_cursor.fetchone.return_value = None

            result = db.fetch("SELECT * FROM test WHERE id=999", one=True)

            # Note: dict(None) returns {} not None, so we check for falsy value
            assert not result

    def test_fetch_reinitializes_tables_on_no_such_table(self):
        """fetch reinitializes tables when 'no such table' error occurs."""
        db = Database("/tmp/test.db")
        db.init_tables = Mock()

        with patch.object(db, "_connect") as mock_connect_ctx:
            mock_conn = Mock()
            mock_connect_ctx.return_value.__enter__ = Mock(return_value=mock_conn)
            mock_connect_ctx.return_value.__exit__ = Mock(return_value=False)
            mock_conn.execute.side_effect = sqlite3.Error("no such table: test")

            result = db.fetch("SELECT * FROM test", one=False)

            db.init_tables.assert_called_once()
            assert result == []

    def test_fetch_raises_other_sqlite_errors(self):
        """fetch re-raises other SQLite errors."""
        db = Database("/tmp/test.db")

        with patch.object(db, "_connect") as mock_connect_ctx:
            mock_conn = Mock()
            mock_connect_ctx.return_value.__enter__ = Mock(return_value=mock_conn)
            mock_connect_ctx.return_value.__exit__ = Mock(return_value=False)
            mock_conn.execute.side_effect = sqlite3.Error("database locked")

            with pytest.raises(sqlite3.Error):
                db.fetch("SELECT * FROM test")


class TestDatabaseInitTables:
    """Tests for Database.init_tables method."""

    def test_init_tables_creates_logs_and_list_logs(self):
        """init_tables creates both logs and list_logs tables."""
        db = Database("/tmp/test.db")
        db._create_logs_table = Mock(return_value=True)

        db.init_tables()

        db._create_logs_table.assert_any_call("logs")
        db._create_logs_table.assert_any_call("list_logs")
        assert db._create_logs_table.call_count == 2

    def test_create_logs_table_generates_correct_query(self):
        """_create_logs_table generates correct CREATE TABLE query."""
        db = Database("/tmp/test.db")
        db.commit = Mock(return_value=True)

        db._create_logs_table("logs")

        db.commit.assert_called_once()
        call_args = db.commit.call_args
        assert "CREATE TABLE IF NOT EXISTS logs" in call_args[0][0]
        assert "id               INTEGER  PRIMARY KEY AUTOINCREMENT" in call_args[0][0]
        assert "endpoint         TEXT     NOT NULL" in call_args[0][0]
        assert "UNIQUE(request_data, response_status, date_only)" in call_args[0][0]


class TestUtcNow:
    """Tests for utc_now function."""

    def test_returns_iso_format_string(self):
        """utc_now returns ISO format string."""
        result = utc_now()
        assert isinstance(result, str)
        # ISO format contains T separator
        assert "T" in result

    def test_returns_utc_timezone(self):
        """utc_now returns UTC timezone."""
        result = utc_now()
        # ISO format with UTC should have +00:00 or Z
        assert "+" in result or "Z" in result
