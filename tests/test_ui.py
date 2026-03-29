# -*- coding: utf-8 -*-
"""
Tests for the UI routes.
"""
from unittest.mock import MagicMock, patch

import pytest


class TestUIRoutes:
    """Tests for UI Blueprint routes."""

    def test_index_page(self, client):
        """Test that index page renders successfully."""
        response = client.get("/")

        assert response.status_code == 200

    def test_logs_page(self, client):
        """Test that logs page renders with mocked data."""
        with patch("src.app.routes.ui.load_logs_view") as mock_load_view:
            with patch("src.app.routes.ui.view_logs_request_handler") as mock_handler:
                mock_handler.return_value = MagicMock()
                mock_viewer = MagicMock()
                mock_viewer.view_logs.return_value = {
                    "logs": [],
                    "tab": {
                        "sum_all": "0",
                        "total_pages": 1,
                        "total_logs": "0",
                        "start_log": 0,
                        "end_log": 0,
                        "start_page": 1,
                        "end_page": 1,
                        "order": "DESC",
                        "order_by": "response_count",
                        "per_page": 10,
                        "page": 1,
                        "status": "All",
                        "day": "",
                        "table_name": "logs",
                    },
                    "order_by_types": ["id", "timestamp"],
                    "status_table": ["All"],
                }
                mock_load_view.return_value = mock_viewer

                response = client.get("/logs")

                assert response.status_code == 200

    def test_no_result_page(self, client):
        """Test that no_result page renders successfully."""
        response = client.get("/no_result")

        assert response.status_code == 200

    def test_logs_by_day_page(self, client):
        """Test that logs_by_day page renders with mocked data."""
        with patch("src.app.routes.ui.load_logs_view") as mock_load_view:
            mock_viewer = MagicMock()
            mock_viewer.view_logs_by_date.return_value = {
                "logs": [],
                "tab": {"sum_all": "0", "table_name": "logs"},
                "status_table": [],
            }
            mock_load_view.return_value = mock_viewer

            response = client.get("/logs_by_day")

            assert response.status_code == 200

    def test_list_page(self, client):
        """Test that list page renders successfully."""
        response = client.get("/list")

        assert response.status_code == 200

    def test_chart_page(self, client):
        """Test that chart page renders successfully."""
        response = client.get("/chart")

        assert response.status_code == 200

    def test_chart2_page(self, client):
        """Test that chart2 page renders successfully."""
        response = client.get("/chart2")

        assert response.status_code == 200


class TestUIWithQueryParams:
    """Tests for UI routes with query parameters."""

    def test_logs_page_with_pagination(self, client):
        """Test logs page with pagination parameters."""
        with patch("src.app.routes.ui.load_logs_view") as mock_load_view:
            with patch("src.app.routes.ui.view_logs_request_handler") as mock_handler:
                mock_handler.return_value = MagicMock()
                mock_viewer = MagicMock()
                mock_viewer.view_logs.return_value = {
                    "logs": [],
                    "tab": {
                        "sum_all": "100",
                        "total_pages": 10,
                        "total_logs": "100",
                        "start_log": 11,
                        "end_log": 20,
                        "start_page": 1,
                        "end_page": 5,
                        "order": "DESC",
                        "order_by": "response_count",
                        "per_page": 10,
                        "page": 2,
                        "status": "All",
                        "day": "",
                        "table_name": "logs",
                    },
                    "order_by_types": ["id", "timestamp"],
                    "status_table": ["All"],
                }
                mock_load_view.return_value = mock_viewer

                response = client.get("/logs?page=2&per_page=10")

                assert response.status_code == 200
                mock_viewer.view_logs.assert_called_once()

    def test_logs_page_with_status_filter(self, client):
        """Test logs page with status filter."""
        with patch("src.app.routes.ui.load_logs_view") as mock_load_view:
            with patch("src.app.routes.ui.view_logs_request_handler") as mock_handler:
                mock_handler.return_value = MagicMock()
                mock_viewer = MagicMock()
                mock_viewer.view_logs.return_value = {
                    "logs": [],
                    "tab": {
                        "sum_all": "50",
                        "total_pages": 5,
                        "total_logs": "50",
                        "start_log": 1,
                        "end_log": 10,
                        "start_page": 1,
                        "end_page": 5,
                        "order": "DESC",
                        "order_by": "response_count",
                        "per_page": 10,
                        "page": 1,
                        "status": "no_result",
                        "day": "",
                        "table_name": "logs",
                    },
                    "order_by_types": ["id", "timestamp"],
                    "status_table": ["All", "no_result"],
                }
                mock_load_view.return_value = mock_viewer

                response = client.get("/logs?status=no_result")

                assert response.status_code == 200

    def test_logs_by_day_with_table_name(self, client):
        """Test logs_by_day page with table_name parameter."""
        with patch("src.app.routes.ui.load_logs_view") as mock_load_view:
            mock_viewer = MagicMock()
            mock_viewer.view_logs_by_date.return_value = {
                "logs": [],
                "tab": {"sum_all": "0", "table_name": "list_logs"},
                "status_table": [],
            }
            mock_load_view.return_value = mock_viewer

            response = client.get("/logs_by_day?table_name=list_logs")

            assert response.status_code == 200


class TestErrorHandling:
    """Tests for error handling in UI routes."""

    def test_404_error(self, client):
        """Test that 404 errors are handled."""
        response = client.get("/nonexistent-page")

        assert response.status_code == 404
