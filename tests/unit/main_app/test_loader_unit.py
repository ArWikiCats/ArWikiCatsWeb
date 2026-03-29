"""Unit tests for src/main_app/loader.py"""

from unittest.mock import Mock, patch

import pytest

from src.main_app.loader import (
    load_database,
    load_data_manager,
    load_logs_view,
)
from src.main_app.logs_db.db import Database


class TestLoadDatabase:
    """Tests for load_database function."""

    def setup_method(self):
        """Clear cache before each test."""
        load_database.cache_clear()

    def teardown_method(self):
        """Clear cache after each test."""
        load_database.cache_clear()

    @patch("src.main_app.loader.Database")
    def test_creates_database_with_settings_db_path(self, mock_db_class):
        """Database is created with settings.db_path."""
        mock_db_instance = Mock(spec=Database)
        mock_db_class.return_value = mock_db_instance

        with patch("src.main_app.loader.settings") as mock_settings:
            mock_settings.db_path = "/tmp/test.db"
            result = load_database()

            mock_db_class.assert_called_once_with("/tmp/test.db")
            assert result == mock_db_instance

    def test_is_cached(self):
        """load_database uses LRU cache."""
        with patch("src.main_app.loader.Database") as mock_db_class:
            mock_db_instance = Mock(spec=Database)
            mock_db_class.return_value = mock_db_instance

            with patch("src.main_app.loader.settings") as mock_settings:
                mock_settings.db_path = "/tmp/test.db"

                first_call = load_database()
                second_call = load_database()

                assert first_call is second_call
                mock_db_class.assert_called_once()


class TestLoadDataManager:
    """Tests for load_data_manager function."""

    def setup_method(self):
        """Clear cache before each test."""
        load_data_manager.cache_clear()
        load_database.cache_clear()

    def teardown_method(self):
        """Clear cache after each test."""
        load_data_manager.cache_clear()
        load_database.cache_clear()

    @patch("src.main_app.loader.LogsManager")
    @patch("src.main_app.loader.load_database")
    def test_creates_logs_manager_with_db_and_allowed_tables(
        self, mock_load_db, mock_logs_manager_class
    ):
        """LogsManager is created with db and allowed_tables."""
        mock_db_instance = Mock(spec=Database)
        mock_load_db.return_value = mock_db_instance

        mock_manager_instance = Mock()
        mock_logs_manager_class.return_value = mock_manager_instance

        with patch("src.main_app.loader.settings") as mock_settings:
            mock_settings.allowed_tables = {"logs", "list_logs"}
            result = load_data_manager()

            mock_logs_manager_class.assert_called_once_with(
                db=mock_db_instance,
                allowed_tables={"logs", "list_logs"},
            )
            assert result == mock_manager_instance

    def test_uses_cached_load_database(self):
        """load_data_manager uses cached load_database."""
        with patch("src.main_app.loader.LogsManager") as mock_logs_manager_class:
            with patch(
                "src.main_app.loader.load_database"
            ) as mock_load_db:
                mock_db_instance = Mock(spec=Database)
                mock_load_db.return_value = mock_db_instance

                mock_manager_instance = Mock()
                mock_logs_manager_class.return_value = mock_manager_instance

                with patch("src.main_app.loader.settings") as mock_settings:
                    mock_settings.allowed_tables = {"logs"}

                    load_data_manager()
                    load_data_manager()

                    # load_database should be called twice but may use cache
                    assert mock_load_db.call_count >= 1

    def test_is_cached(self):
        """load_data_manager uses LRU cache."""
        with patch("src.main_app.loader.LogsManager") as mock_logs_manager_class:
            with patch("src.main_app.loader.load_database") as mock_load_db:
                mock_db_instance = Mock(spec=Database)
                mock_load_db.return_value = mock_db_instance

                mock_manager_instance = Mock()
                mock_logs_manager_class.return_value = mock_manager_instance

                with patch("src.main_app.loader.settings") as mock_settings:
                    mock_settings.allowed_tables = {"logs"}

                    first_call = load_data_manager()
                    second_call = load_data_manager()

                    assert first_call is second_call
                    mock_logs_manager_class.assert_called_once()


class TestLoadLogsView:
    """Tests for load_logs_view function."""

    def setup_method(self):
        """Clear cache before each test."""
        load_logs_view.cache_clear()
        load_data_manager.cache_clear()
        load_database.cache_clear()

    def teardown_method(self):
        """Clear cache after each test."""
        load_logs_view.cache_clear()
        load_data_manager.cache_clear()
        load_database.cache_clear()

    @patch("src.main_app.loader.LogsView")
    @patch("src.main_app.loader.load_data_manager")
    def test_creates_logs_view_with_manager(
        self, mock_load_manager, mock_logs_view_class
    ):
        """LogsView is created with manager."""
        mock_manager_instance = Mock()
        mock_load_manager.return_value = mock_manager_instance

        mock_view_instance = Mock()
        mock_logs_view_class.return_value = mock_view_instance

        result = load_logs_view()

        mock_logs_view_class.assert_called_once_with(manager=mock_manager_instance)
        assert result == mock_view_instance

    def test_is_cached(self):
        """load_logs_view uses LRU cache."""
        with patch("src.main_app.loader.LogsView") as mock_logs_view_class:
            with patch("src.main_app.loader.load_data_manager") as mock_load_manager:
                mock_manager_instance = Mock()
                mock_load_manager.return_value = mock_manager_instance

                mock_view_instance = Mock()
                mock_logs_view_class.return_value = mock_view_instance

                first_call = load_logs_view()
                second_call = load_logs_view()

                assert first_call is second_call
                mock_logs_view_class.assert_called_once()
