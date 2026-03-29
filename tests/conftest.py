# -*- coding: utf-8 -*-
"""
Pytest configuration for the tests directory.
"""
import functools
import os
import pytest


@pytest.fixture(scope="session", autouse=True)
def set_database_path_and_clear_cache(tmp_path_factory):
    """Set DATABASE_PATH environment variable for testing and clear loader cache."""
    db_file = tmp_path_factory.mktemp("db") / "test.db"
    os.environ["DATABASE_PATH"] = str(db_file)

    # Clear the lru_cache for load_database, load_data_manager, and load_logs_view
    # This must happen BEFORE any import of src.app to ensure fresh DB binding
    from src.main_app import loader
    loader.load_database.cache_clear()
    loader.load_data_manager.cache_clear()
    loader.load_logs_view.cache_clear()

    # Also clear the settings cache to pick up the new DATABASE_PATH
    from src.main_app import config
    config.get_settings.cache_clear()
    config.settings = config.get_settings()


@pytest.fixture
def client():
    """Create Flask test client."""
    from src.main_app import create_app

    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def logs_manager_factory():
    """Factory fixture to create LogsManager instances.

    Usage:
        def test_something(logs_manager_factory, tmp_path):
            db_file = tmp_path / "test.db"
            # ... setup database ...
            manager = logs_manager_factory(str(db_file))
    """
    from src.main_app.logs_db.bot import LogsManager
    from src.main_app.logs_db.db import Database

    def _create_manager(db_file, allowed_tables=None):
        if allowed_tables is None:
            allowed_tables = {"logs", "list_logs"}
        db_instance = Database(db_file)
        return LogsManager(db=db_instance, allowed_tables=allowed_tables)

    return _create_manager
