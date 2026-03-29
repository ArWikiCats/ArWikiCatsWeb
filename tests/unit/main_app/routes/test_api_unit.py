"""Unit tests for src/main_app/routes/api.py"""

import json
from unittest.mock import Mock, patch

import pytest

from src.main_app.routes.api import (
    Api_Blueprint,
    get_logs_all,
    get_logs_by_day,
    get_logs_category,
    get_logs_no_result,
    get_status_table,
    jsonify,
    logs_api,
)


class TestJsonify:
    """Tests for jsonify helper function."""

    def test_jsonify_returns_response_with_json_content(self):
        """jsonify returns a Response with JSON content."""
        data = {"key": "value", "number": 42}
        response = jsonify(data)

        # Check content type
        assert response.content_type == "application/json; charset=utf-8"

        # Check data is correctly serialized (response is bytes)
        expected = json.dumps(data, ensure_ascii=False, indent=4)
        assert response.get_data(as_text=True) == expected

    def test_jsonify_handles_unicode(self):
        """jsonify handles unicode characters correctly."""
        data = {"result": "تصنيف", "arabic": "العربية"}
        response = jsonify(data)

        response_text = response.get_data(as_text=True)
        assert "تصنيف" in response_text
        assert "العربية" in response_text


class TestGetLogsByDay:
    """Tests for get_logs_by_day function."""

    def test_get_logs_by_day_returns_json(self):
        """get_logs_by_day returns JSON response."""
        with patch("src.main_app.routes.api.load_logs_view") as mock_load_view:
            mock_viewer = Mock()
            mock_viewer.view_logs_by_date.return_value = {
                "logs": [{"day": "2025-01-15", "total": 10}]
            }
            mock_load_view.return_value = mock_viewer

            response = get_logs_by_day("logs")

            assert response.content_type == "application/json; charset=utf-8"


class TestGetLogsAll:
    """Tests for get_logs_all function."""

    def test_get_logs_all_returns_json(self):
        """get_logs_all returns JSON response."""
        with patch("src.main_app.routes.api.load_logs_view") as mock_load_view:
            mock_viewer = Mock()
            mock_viewer.view_logs_en2ar.return_value = {
                "no_result": ["title1"],
                "data_result": {"title2": "result2"},
            }
            mock_load_view.return_value = mock_viewer

            response = get_logs_all()

            assert response.content_type == "application/json; charset=utf-8"

    def test_get_logs_all_with_day(self):
        """get_logs_all passes day parameter."""
        with patch("src.main_app.routes.api.load_logs_view") as mock_load_view:
            mock_viewer = Mock()
            mock_viewer.view_logs_en2ar.return_value = {}
            mock_load_view.return_value = mock_viewer

            get_logs_all(day="2025-01-15")

            mock_viewer.view_logs_en2ar.assert_called_once_with("2025-01-15")


class TestGetLogsCategory:
    """Tests for get_logs_category function."""

    def test_get_logs_category_excludes_no_result(self):
        """get_logs_category excludes no_result from response."""
        with patch("src.main_app.routes.api.load_logs_view") as mock_load_view:
            mock_viewer = Mock()
            mock_viewer.view_logs_en2ar.return_value = {
                "no_result": ["title1"],
                "data_result": {"title2": "result2"},
            }
            mock_load_view.return_value = mock_viewer

            response = get_logs_category()

            assert response.content_type == "application/json; charset=utf-8"
            data = json.loads(response.get_data(as_text=True))
            assert "no_result" not in data


class TestGetLogsNoResult:
    """Tests for get_logs_no_result function."""

    def test_get_logs_no_result_excludes_data_result(self):
        """get_logs_no_result excludes data_result from response."""
        with patch("src.main_app.routes.api.load_logs_view") as mock_load_view:
            mock_viewer = Mock()
            mock_viewer.view_logs_en2ar.return_value = {
                "no_result": ["title1"],
                "data_result": {"title2": "result2"},
            }
            mock_load_view.return_value = mock_viewer

            response = get_logs_no_result()

            data = json.loads(response.get_data(as_text=True))
            assert "data_result" not in data


class TestGetStatusTable:
    """Tests for get_status_table function."""

    def test_get_status_table_returns_json(self):
        """get_status_table returns JSON response."""
        with patch("src.main_app.routes.api.load_data_manager") as mock_load_manager:
            mock_manager = Mock()
            mock_manager.get_response_status.return_value = ["no_result", "Category"]
            mock_load_manager.return_value = mock_manager

            response = get_status_table()

            assert response.content_type == "application/json; charset=utf-8"
            data = json.loads(response.get_data(as_text=True))
            assert data == ["no_result", "Category"]


class TestLogsApi:
    """Tests for logs_api function."""

    def test_logs_api_returns_json(self):
        """logs_api returns JSON response."""
        mock_handler = Mock()
        mock_handler.per_page = 10
        mock_handler.offset = 0
        mock_handler.order = "DESC"
        mock_handler.order_by = "timestamp"
        mock_handler.status = ""
        mock_handler.table_name = "logs"
        mock_handler.day = ""

        with patch("src.main_app.routes.api.load_logs_view") as mock_load_view:
            mock_viewer = Mock()
            mock_viewer.view_logs.return_value = {
                "logs": [],
                "tab": {"total_pages": 0},
            }
            mock_load_view.return_value = mock_viewer

            response = logs_api(mock_handler)

            assert response.content_type == "application/json; charset=utf-8"


class TestApiBlueprint:
    """Tests for Api_Blueprint class."""

    def test_api_blueprint_registers_routes(self):
        """Api_Blueprint registers all API routes."""
        mock_bp = Mock()
        routes_registered = []

        def route_decorator(path, methods=None):
            def inner(func):
                routes_registered.append({"path": path, "methods": methods})
                return func
            return inner

        mock_bp.route = route_decorator

        Api_Blueprint(mock_bp, allowed_tables={"logs", "list_logs"})

        # Check that routes were registered
        paths = [r["path"] for r in routes_registered]
        assert "/logs" in paths
        assert "/list" in paths
        assert "/<title>" in paths
        assert "/status" in paths
        assert "/no_result" in paths
        assert "/logs_by_day" in paths
        assert "/all" in paths
        assert "/category" in paths
