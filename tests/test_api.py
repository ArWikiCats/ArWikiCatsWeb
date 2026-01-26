# -*- coding: utf-8 -*-
"""
Tests for the API routes.
"""
import json
from unittest.mock import MagicMock, patch

import pytest


class TestJsonify:
    """Tests for the custom jsonify function."""

    def test_jsonify_returns_response(self):
        """Test that jsonify returns a Flask Response."""
        from src.app.routes.api import jsonify

        result = jsonify({"key": "value"})

        assert result.content_type == "application/json; charset=utf-8"

    def test_jsonify_handles_unicode(self):
        """Test that jsonify properly handles Arabic text."""
        from src.app.routes.api import jsonify

        data = {"result": "تصنيف:اختبار"}
        result = jsonify(data)

        # Ensure Arabic characters are not escaped
        assert "تصنيف" in result.get_data(as_text=True)

    def test_jsonify_formats_output(self):
        """Test that jsonify formats JSON with indentation."""
        from src.app.routes.api import jsonify

        data = {"key1": "value1", "key2": "value2"}
        result = jsonify(data)

        # Check for indentation (pretty print)
        response_text = result.get_data(as_text=True)
        assert "\n" in response_text


class TestCheckUserAgent:
    """Tests for the check_user_agent function."""

    @pytest.fixture
    def app_context(self):
        """Create Flask app context for testing."""
        from src.app import create_app
        app = create_app()
        with app.test_request_context():
            yield app

    def test_check_user_agent_missing(self, app_context):
        """Test that missing User-Agent returns error."""
        from flask import request
        from src.app.routes.api import check_user_agent

        with patch.object(request, 'headers', {"User-Agent": ""}):
            with patch("src.app.routes.api.log_request"):
                result = check_user_agent("/api/test", "data", 0)

        # Should return an error response
        assert result is not None

    def test_check_user_agent_present(self, app_context):
        """Test that present User-Agent returns None."""
        from flask import request
        from src.app.routes.api import check_user_agent

        with patch.object(request, 'headers', {"User-Agent": "TestAgent/1.0"}):
            result = check_user_agent("/api/test", "data", 0)

        assert result is None


class TestApiEndpoints:
    """Tests for API endpoints using Flask test client."""

    @pytest.fixture
    def client(self):
        """Create Flask test client."""
        from src.app import create_app
        app = create_app()
        app.config["TESTING"] = True
        with app.test_client() as client:
            yield client

    def test_logs_by_day_endpoint(self, client):
        """Test /api/logs_by_day endpoint."""
        with patch("src.app.logs_bot.retrieve_logs_by_date") as mock_retrieve:
            mock_retrieve.return_value = {"logs": []}

            response = client.get("/api/logs_by_day")

            assert response.status_code == 200
            assert response.content_type == "application/json; charset=utf-8"

    def test_status_endpoint(self, client):
        """Test /api/status endpoint."""
        with patch("src.app.routes.api.get_response_status") as mock_status:
            mock_status.return_value = ["no_result", "success"]

            response = client.get("/api/status")

            assert response.status_code == 200

    def test_logs_endpoint(self, client):
        """Test /api/logs endpoint."""
        with patch("src.app.logs_bot.view_logs") as mock_view_logs:
            mock_view_logs.return_value = {"logs": [], "tab": {}, "status_table": []}

            response = client.get("/api/logs")

            assert response.status_code == 200

    def test_all_endpoint_without_day(self, client):
        """Test /api/all endpoint without day parameter."""
        with patch("src.app.logs_bot.retrieve_logs_en_to_ar") as mock_retrieve:
            mock_retrieve.return_value = {
                "tab": {"sum_all": "0"},
                "no_result": [],
                "data_result": {}
            }

            response = client.get("/api/all")

            assert response.status_code == 200
            mock_retrieve.assert_called_once_with(None)

    def test_all_endpoint_with_day(self, client):
        """Test /api/all/<day> endpoint with day parameter."""
        with patch("src.app.logs_bot.retrieve_logs_en_to_ar") as mock_retrieve:
            mock_retrieve.return_value = {
                "tab": {"sum_all": "0"},
                "no_result": [],
                "data_result": {}
            }

            response = client.get("/api/all/2025-01-27")

            assert response.status_code == 200
            mock_retrieve.assert_called_once_with("2025-01-27")

    def test_category_endpoint(self, client):
        """Test /api/category endpoint."""
        with patch("src.app.logs_bot.retrieve_logs_en_to_ar") as mock_retrieve:
            mock_retrieve.return_value = {
                "tab": {"sum_all": "5"},
                "no_result": ["test"],
                "data_result": {"key": "value"}
            }

            response = client.get("/api/category")
            data = json.loads(response.get_data(as_text=True))

            assert response.status_code == 200
            # no_result should be removed for category endpoint
            assert "no_result" not in data

    def test_no_result_endpoint(self, client):
        """Test /api/no_result endpoint."""
        with patch("src.app.logs_bot.retrieve_logs_en_to_ar") as mock_retrieve:
            mock_retrieve.return_value = {
                "tab": {"sum_all": "5"},
                "no_result": ["test"],
                "data_result": {"key": "value"}
            }

            response = client.get("/api/no_result")
            data = json.loads(response.get_data(as_text=True))

            assert response.status_code == 200
            # data_result should be removed for no_result endpoint
            assert "data_result" not in data


class TestTitleEndpoint:
    """Tests for the /api/<title> endpoint."""

    @pytest.fixture
    def client(self):
        """Create Flask test client."""
        from src.app import create_app
        app = create_app()
        app.config["TESTING"] = True
        with app.test_client() as client:
            yield client

    def test_title_endpoint_without_user_agent(self, client):
        """Test title endpoint returns 400 without User-Agent."""
        with patch("src.app.routes.api.log_request"):
            response = client.get(
                "/api/Category:Test",
                headers={"User-Agent": ""}
            )

            assert response.status_code == 400

    def test_title_endpoint_with_user_agent(self, client):
        """Test title endpoint works with User-Agent."""
        with patch("src.app.routes.api.resolve_arabic_category_label") as mock_resolve:
            with patch("src.app.routes.api.log_request", return_value="test"):
                mock_resolve.return_value = "تصنيف:اختبار"

                response = client.get(
                    "/api/Category:Test",
                    headers={"User-Agent": "TestAgent/1.0"}
                )

                assert response.status_code == 200
                data = json.loads(response.get_data(as_text=True))
                assert "result" in data

    def test_title_endpoint_library_not_loaded(self, client):
        """Test title endpoint handles library not loaded."""
        with patch("src.app.routes.api.resolve_arabic_category_label", None):
            with patch("src.app.routes.api.log_request"):
                response = client.get(
                    "/api/Category:Test",
                    headers={"User-Agent": "TestAgent/1.0"}
                )

                assert response.status_code == 500


class TestListEndpoint:
    """Tests for the /api/list POST endpoint."""

    @pytest.fixture
    def client(self):
        """Create Flask test client."""
        from src.app import create_app
        app = create_app()
        app.config["TESTING"] = True
        with app.test_client() as client:
            yield client

    def test_list_endpoint_without_user_agent(self, client):
        """Test list endpoint returns 400 without User-Agent."""
        with patch("src.app.routes.api.log_request"):
            response = client.post(
                "/api/list",
                json={"titles": ["test1", "test2"]},
                headers={"User-Agent": ""}
            )

            assert response.status_code == 400

    def test_list_endpoint_invalid_data(self, client):
        """Test list endpoint handles invalid data."""
        with patch("src.app.routes.api.log_request"):
            response = client.post(
                "/api/list",
                json={"titles": "not_a_list"},
                headers={"User-Agent": "TestAgent/1.0"}
            )

            assert response.status_code == 400

    def test_list_endpoint_success(self, client):
        """Test list endpoint with valid data."""
        mock_result = MagicMock()
        mock_result.labels = {"Category:Test1": "تصنيف:اختبار1"}
        mock_result.no_labels = []

        with patch("src.app.routes.api.batch_resolve_labels") as mock_batch:
            with patch("src.app.routes.api.log_request"):
                mock_batch.return_value = mock_result

                response = client.post(
                    "/api/list",
                    json={"titles": ["Category:Test1"]},
                    headers={"User-Agent": "TestAgent/1.0"}
                )

                assert response.status_code == 200
                data = json.loads(response.get_data(as_text=True))
                assert "results" in data
                assert "with_labs" in data

    def test_list_endpoint_removes_duplicates(self, client):
        """Test list endpoint removes duplicate titles."""
        mock_result = MagicMock()
        mock_result.labels = {"Category:Test1": "تصنيف:اختبار1"}
        mock_result.no_labels = []

        with patch("src.app.routes.api.batch_resolve_labels") as mock_batch:
            with patch("src.app.routes.api.log_request"):
                mock_batch.return_value = mock_result

                response = client.post(
                    "/api/list",
                    json={"titles": ["Category:Test1", "Category:Test1", "Category:Test1"]},
                    headers={"User-Agent": "TestAgent/1.0"}
                )

                assert response.status_code == 200
                data = json.loads(response.get_data(as_text=True))
                assert data["duplicates"] == 2

    def test_list_endpoint_library_not_loaded(self, client):
        """Test list endpoint handles library not loaded."""
        with patch("src.app.routes.api.batch_resolve_labels", None):
            with patch("src.app.routes.api.log_request"):
                response = client.post(
                    "/api/list",
                    json={"titles": ["test"]},
                    headers={"User-Agent": "TestAgent/1.0"}
                )

                assert response.status_code == 500
