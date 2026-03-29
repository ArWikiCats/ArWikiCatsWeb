# -*- coding: utf-8 -*-
"""Manual test script for Flask-Limiter rate limiting.

Run this script to test rate limiting on your API endpoints.

Usage:
    python test_limiter_manual.py

Make sure your Flask app is running first:
    python src/app.py
"""

import requests
import sys

BASE_URL = "http://localhost:5000"


def test_endpoint(endpoint, method="GET", json_data=None, headers=None, limit=250):
    """Test rate limiting on a specific endpoint."""
    print(f"\n{'='*60}")
    print(f"Testing: {method} {endpoint}")
    print(f"{'='*60}")

    if headers is None:
        headers = {"User-Agent": "RateLimitTester"}

    rate_limited = False

    for i in range(limit):
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
            elif method == "POST":
                response = requests.post(
                    f"{BASE_URL}{endpoint}",
                    json=json_data,
                    headers=headers
                )

            status = response.status_code

            # Print progress every 20 requests
            if (i + 1) % 20 == 0:
                print(f"  Request {i + 1}: {status}")

            if status == 429:
                print(f"\n  [!] Rate limited at request {i + 1}!")
                print(f"  Response: {response.text[:200]}")

                # Show rate limit headers if available
                if "X-RateLimit-Limit" in response.headers:
                    print("\n  Rate Limit Headers:")
                    for header in ["X-RateLimit-Limit", "X-RateLimit-Remaining", "Retry-After"]:
                        if header in response.headers:
                            print(f"    {header}: {response.headers[header]}")

                rate_limited = True
                break

        except requests.exceptions.RequestException as e:
            print(f"\n  [!] Error at request {i + 1}: {e}")
            return False

    if not rate_limited:
        print(f"\n  [!] Rate limit NOT triggered after {limit} requests")
        return False

    return True


def main():
    """Run all rate limit tests."""
    print("Flask-Limiter Rate Limit Test")
    print("="*60)

    # Check if server is running
    try:
        response = requests.get(BASE_URL, timeout=5)
        print(f"Server is running: {BASE_URL}")
    except requests.exceptions.ConnectionError:
        print(f"\n[ERROR] Cannot connect to {BASE_URL}")
        print("Make sure your Flask app is running:")
        print("  python src/app.py")
        sys.exit(1)

    # Test different endpoints
    tests = [
        ("/api/status", "GET", None),
        ("/api/test_category", "GET", None),
        ("/api/list", "POST", {"titles": ["test"]}),
    ]

    results = []
    for endpoint, method, data in tests:
        result = test_endpoint(endpoint, method, data)
        results.append((endpoint, result))

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for endpoint, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  [{status}] {endpoint}")


if __name__ == "__main__":
    main()
