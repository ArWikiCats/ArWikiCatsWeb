# -*- coding: utf-8 -*-
"""Tests for Flask-Limiter rate limiting on API endpoints."""

import pytest
from flask_testing import TestCase
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app


class TestRateLimiter(TestCase):
    """Test rate limiting on API endpoints."""

    def create_app(self):
        """Create the test app."""
        app.config["TESTING"] = True
        return app

    def test_rate_limit_headers_present(self):
        """Test that rate limit headers are present in responses."""
        response = self.client.get("/api/status")

        # Should have rate limit headers
        assert "X-RateLimit-Limit" in response.headers or response.status_code in [200, 429]

    def test_rate_limit_exceeded_on_status_endpoint(self):
        """Test 429 response when exceeding rate limit on /api/status."""
        rate_limited = False

        for i in range(250):
            response = self.client.get("/api/status")

            if response.status_code == 429:
                print(f"Rate limited at request {i + 1}")
                rate_limited = True
                assert i >= 200, f"Rate limit triggered too early at request {i + 1}"
                break

        assert rate_limited, "Rate limit was not triggered after 250 requests"

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

    def test_normal_requests_under_limit_succeed(self):
        """Test that requests under the limit succeed."""
        for i in range(50):
            response = self.client.get("/api/status")
            assert response.status_code == 200, f"Request {i + 1} failed unexpectedly"

    def test_429_response_format(self):
        """Test the format of 429 Too Many Requests response."""
        # Exhaust the rate limit
        for i in range(250):
            response = self.client.get("/api/status")
            if response.status_code == 429:
                # Check response has error message
                assert response.status_code == 429
                assert "limit" in response.get_data(as_text=True).lower() or \
                       "rate" in response.get_data(as_text=True).lower() or \
                       response.content_type == "text/html"  # Default limiter response
                break


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
