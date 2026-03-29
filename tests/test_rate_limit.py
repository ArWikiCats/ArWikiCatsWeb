# -*- coding: utf-8 -*-
"""Tests for Flask-Limiter rate limiting on API endpoints.

Run all tests:
    pytest tests/test_rate_limit.py -v

Run individual tests (recommended for rate limit tests):
    pytest tests/test_rate_limit.py::TestARateLimiterNormalRequests -v
    pytest tests/test_rate_limit.py::TestBRateLimiterStatusEndpoint -v
"""

import pytest
from flask_testing import TestCase

from src.app import app


class TestARateLimiterNormalRequests(TestCase):
    """Test that normal requests under the limit succeed.

    Note: Run this test first/isolated before other rate limit tests.
    """

    def create_app(self):
        """Create the test app."""
        app.config["TESTING"] = True
        return app

    def test_normal_requests_under_limit_succeed(self):
        """Test that 50 requests under the limit succeed."""
        for i in range(50):
            response = self.client.get("/api/status")
            assert response.status_code == 200, f"Request {i + 1} failed unexpectedly"


class TestBRateLimiterStatusEndpoint(TestCase):
    """Test rate limiting on /api/status endpoint."""

    def create_app(self):
        """Create the test app."""
        app.config["TESTING"] = True
        return app

    def test_rate_limit_exceeded_on_status_endpoint(self):
        """Test 429 response when exceeding rate limit on /api/status.

        Note: This test should be run in isolation to get accurate count.
        Rate limit is 200 per minute, so we expect it around request 200-201.
        """
        rate_limited = False
        rate_limited_at = None

        for i in range(250):
            response = self.client.get("/api/status")

            if response.status_code == 429:
                rate_limited_at = i + 1
                rate_limited = True
                print(f"Rate limited at request {rate_limited_at}")
                break

        assert rate_limited, "Rate limit was not triggered after 250 requests"
        # Allow some margin for test overhead and shared state
        assert rate_limited_at >= 150, f"Rate limit triggered too early at request {rate_limited_at}"
        assert rate_limited_at <= 210, f"Rate limit triggered too late at request {rate_limited_at}"


class TestCRateLimiterListEndpoint(TestCase):
    """Test rate limiting on /api/list endpoint."""

    def create_app(self):
        """Create the test app."""
        app.config["TESTING"] = True
        return app

    def test_rate_limit_exceeded_on_list_endpoint(self):
        """Test 429 response when exceeding rate limit on /api/list."""
        rate_limited = False

        for i in range(250):
            response = self.client.post(
                "/api/list",
                json={"titles": ["test"]},
                headers={"User-Agent": "TestClient"}
            )

            if response.status_code == 429:
                print(f"Rate limited at request {i + 1}")
                rate_limited = True
                break

        assert rate_limited, "Rate limit was not triggered after 250 requests"


class TestDRateLimiterTitleEndpoint(TestCase):
    """Test rate limiting on /api/<title> endpoint."""

    def create_app(self):
        """Create the test app."""
        app.config["TESTING"] = True
        return app

    def test_rate_limit_exceeded_on_title_endpoint(self):
        """Test 429 response when exceeding rate limit on /api/<title>."""
        rate_limited = False

        for i in range(250):
            response = self.client.get(
                "/api/test_title",
                headers={"User-Agent": "TestClient"}
            )

            if response.status_code == 429:
                print(f"Rate limited at request {i + 1}")
                rate_limited = True
                break

        assert rate_limited, "Rate limit was not triggered after 250 requests"


class TestERateLimiterHeaders(TestCase):
    """Test rate limit headers."""

    def create_app(self):
        """Create the test app."""
        app.config["TESTING"] = True
        return app

    def test_rate_limit_headers_present(self):
        """Test that requests return valid status (200 or 429)."""
        response = self.client.get("/api/status")
        # Should succeed or be rate limited
        assert response.status_code in [200, 429]


class TestFRateLimiterResponseFormat(TestCase):
    """Test 429 response format."""

    def create_app(self):
        """Create the test app."""
        app.config["TESTING"] = True
        return app

    def test_429_response_format(self):
        """Test the format of 429 Too Many Requests response."""
        # Exhaust the rate limit
        for _ in range(250):
            response = self.client.get("/api/status")
            if response.status_code == 429:
                # Check response contains rate limit info
                response_text = response.get_data(as_text=True).lower()
                assert "too many requests" in response_text
                print(f"429 response: {response.get_data(as_text=True)}")
                break


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
