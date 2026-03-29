# -*- coding: utf-8 -*-
"""
Pytest configuration for the tests directory.
"""
import pytest


@pytest.fixture
def client():
    """Create Flask test client."""
    from src.app import create_app

    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client
