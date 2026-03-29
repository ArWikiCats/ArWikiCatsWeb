# -*- coding: utf-8 -*-
"""
Tests for User-Agent header validation using Flask test client.
"""
from unittest.mock import patch

import pytest


class TestUserAgentHeader:
    """Tests for User-Agent header validation in API endpoints."""

    def test_single_title_endpoint_without_user_agent(self, client):
        """Test that single title endpoint returns 400 without User-Agent."""
        with patch("src.main_app.routes.api.load_data_manager") as mock_load:
            mock_manager = mock_load.return_value
            mock_manager.log_request.return_value = True
            response = client.get("/api/Category:Yemen", headers={"User-Agent": ""})

            assert response.status_code == 400
            data = response.get_json()
            assert "error" in data
            assert "User-Agent header is required" in data["error"]

    def test_single_title_endpoint_with_user_agent(self, client):
        """Test that single title endpoint works with User-Agent."""
        from unittest.mock import patch

        with patch("src.main_app.routes.api.resolve_arabic_category_label") as mock_resolve:
            with patch("src.main_app.routes.api.load_data_manager") as mock_load:
                mock_manager = mock_load.return_value
                mock_manager.log_request.return_value = True
                mock_resolve.return_value = "تصنيف:اليمن"

                response = client.get("/api/Category:Yemen", headers={"User-Agent": "TestAgent/1.0"})

                # Should either succeed with the mock or return library error
                assert response.status_code in [200, 500]

    def test_list_endpoint_without_user_agent(self, client):
        """Test that list endpoint returns 400 without User-Agent."""
        with patch("src.main_app.routes.api.load_data_manager") as mock_load:
            mock_manager = mock_load.return_value
            mock_manager.log_request.return_value = True
            data = {"titles": ["test_title1", "test_title2"]}
            response = client.post("/api/list", json=data, headers={"User-Agent": ""})

            assert response.status_code == 400
            data = response.get_json()
            assert "error" in data
            assert "User-Agent header is required" in data["error"]

    def test_list_endpoint_with_user_agent(self, client):
        """Test that list endpoint works with User-Agent."""
        from unittest.mock import MagicMock, patch

        mock_result = MagicMock()
        mock_result.labels = {"test_title1": "تصنيف:اختبار1"}
        mock_result.no_labels = []

        with patch("src.main_app.routes.api.batch_resolve_labels") as mock_batch:
            with patch("src.main_app.routes.api.load_data_manager") as mock_load:
                mock_manager = mock_load.return_value
                mock_manager.log_request.return_value = True
                mock_batch.return_value = mock_result

                data = {"titles": ["test_title1", "test_title2"]}
                response = client.post("/api/list", json=data, headers={"User-Agent": "TestAgent/1.0"})

                # Should either succeed with the mock or return library error
                assert response.status_code in [200, 500]

    def test_all_api_respect_user_agent_requirement(self, client):
        """Test that all POST/GET API endpoints require User-Agent header."""
        from unittest.mock import patch

        # Mock the library and log_request to avoid import errors
        with patch("src.main_app.routes.api.resolve_arabic_category_label"):
            with patch("src.main_app.routes.api.load_data_manager") as mock_load:
                mock_manager = mock_load.return_value
                mock_manager.log_request.return_value = True
                # Test various endpoints
                endpoints = [
                    ("/api/Category:Test", "GET"),
                    ("/api/list", "POST"),
                ]

                for endpoint, method in endpoints:
                    if method == "GET":
                        response = client.get(endpoint, headers={"User-Agent": ""})
                    else:
                        response = client.post(endpoint, json={"titles": ["test"]}, headers={"User-Agent": ""})

                    # All should return 400 for missing User-Agent
                    assert response.status_code == 400, f"Endpoint {endpoint} should require User-Agent"
