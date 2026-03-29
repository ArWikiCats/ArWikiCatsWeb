"""Unit tests for src/main_app/config.py"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from src.main_app.config import (
    Settings,
    _format_rate_limit,
    _get_paths,
    get_settings,
)


class TestFormatRateLimit:
    """Tests for _format_rate_limit helper function."""

    def test_plain_number_appends_per_minute(self):
        """Plain numeric values get 'per minute' appended."""
        assert _format_rate_limit("200") == "200 per minute"
        assert _format_rate_limit("100") == "100 per minute"

    def test_whitespace_is_stripped(self):
        """Leading/trailing whitespace is handled correctly."""
        assert _format_rate_limit("  200  ") == "200 per minute"

    def test_already_formatted_value_unchanged(self):
        """Values already containing text are returned as-is."""
        assert _format_rate_limit("200 per minute") == "200 per minute"
        assert _format_rate_limit("100 per hour") == "100 per hour"

    def test_non_numeric_value_unchanged(self):
        """Non-numeric values are returned unchanged."""
        assert _format_rate_limit("default") == "default"


class TestGetPaths:
    """Tests for _get_paths function."""

    def test_default_path_is_valid_path(self):
        """Default DATABASE_PATH returns a valid path."""
        # This test just verifies the function works without DATABASE_PATH set
        # The actual path depends on the system's home directory
        with patch("src.main_app.config.os.getenv", return_value=""):
            path = _get_paths()
            # Verify it's a non-empty string
            assert isinstance(path, str)
            assert len(path) > 0

    def test_custom_database_path_via_env(self):
        """Custom DATABASE_PATH environment variable is respected."""
        with patch.dict(os.environ, {"DATABASE_PATH": "/tmp/custom/path/db.sqlite"}):
            path = _get_paths()
            # Use Path for cross-platform comparison
            assert Path(path) == Path("/tmp/custom/path/db.sqlite")

    def test_env_var_expands_user_home(self):
        """Environment variable with ~ expands correctly."""
        with patch.dict(os.environ, {"DATABASE_PATH": "~/my_custom.db"}):
            path = _get_paths()
            # Just verify it contains the filename
            assert "my_custom.db" in path

    def test_creates_parent_directory(self):
        """Parent directory is created if it doesn't exist."""
        with patch.dict(os.environ, {"DATABASE_PATH": "/tmp/test_dir/db.sqlite"}):
            path = _get_paths()
            assert Path(path).parent.exists()

    def test_creates_db_file_if_not_exists(self):
        """Database file is created if it doesn't exist."""
        with patch.dict(os.environ, {"DATABASE_PATH": "/tmp/test_new_db.sqlite"}):
            path = _get_paths()
            assert Path(path).exists()


class TestSettings:
    """Tests for Settings dataclass."""

    def test_default_values(self):
        """Settings dataclass has correct default values."""
        settings = Settings(
            db_path="/tmp/test.db",
            allowed_tables={"logs", "list_logs"},
        )
        assert settings.db_path == "/tmp/test.db"
        assert settings.allowed_tables == {"logs", "list_logs"}
        assert settings.pagination_window == 2
        assert settings.max_visible_pages == 4
        assert settings.rate_limit == "200 per minute"

    def test_frozen_dataclass(self):
        """Settings is a frozen dataclass (immutable)."""
        settings = Settings(
            db_path="/tmp/test.db",
            allowed_tables={"logs"},
        )
        with pytest.raises(Exception):
            settings.db_path = "/new/path"


class TestGetSettings:
    """Tests for get_settings function."""

    def setup_method(self):
        """Clear cache before each test."""
        get_settings.cache_clear()

    def teardown_method(self):
        """Clear cache after each test."""
        get_settings.cache_clear()

    def test_returns_settings_with_correct_values(self):
        """get_settings returns Settings with expected values."""
        settings = get_settings()
        assert settings.allowed_tables == {"logs", "list_logs"}
        assert settings.pagination_window == 2
        assert settings.max_visible_pages == 4

    def test_rate_limit_from_env(self):
        """Rate limit is read from RATE_LIMIT environment variable."""
        with patch.dict(os.environ, {"RATE_LIMIT": "500"}):
            settings = get_settings()
            assert settings.rate_limit == "500 per minute"

    def test_rate_limit_formatted_from_env(self):
        """Rate limit formatting is handled for pre-formatted values."""
        with patch.dict(os.environ, {"RATE_LIMIT": "100 per hour"}):
            settings = get_settings()
            assert settings.rate_limit == "100 per hour"

    def test_is_cached(self):
        """get_settings uses LRU cache."""
        first_call = get_settings()
        second_call = get_settings()
        assert first_call is second_call  # Same cached instance
