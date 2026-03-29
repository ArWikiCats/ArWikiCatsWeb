# -*- coding: utf-8 -*-
"""
Pytest configuration for the tests directory.
"""
import os
import pytest


@pytest.fixture(scope="session", autouse=True)
def set_database_path(tmp_path_factory):
    """Set DATABASE_PATH environment variable for testing."""
    db_file = tmp_path_factory.mktemp("db") / "test.db"
    os.environ["DATABASE_PATH"] = str(db_file)


@pytest.fixture
def client():
    """Create Flask test client."""
    from src.app import create_app

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
    from src.app.logs_db.bot import LogsManager
    from src.app.logs_db.db import Database

    def _create_manager(db_file, allowed_tables=None):
        if allowed_tables is None:
            allowed_tables = {"logs", "list_logs"}
        db_instance = Database(db_file)
        return LogsManager(db=db_instance, allowed_tables=allowed_tables)

    return _create_manager
