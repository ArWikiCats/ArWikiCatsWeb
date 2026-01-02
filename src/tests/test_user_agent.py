import requests
import json

# Base URL - adjust if your server runs on a different port
BASE_URL = "http://localhost:5000"


def test_api_without_user_agent():
    """Test that API endpoints correctly handle missing User-Agent header."""
    try:
        # Test single title endpoint
        title_response = requests.get(f"{BASE_URL}/api/Category:Yemen", headers={"User-Agent": ""})
        assert title_response.status_code == 400, "Single title endpoint should return 400 without User-Agent"
        assert "error" in title_response.json(), "Response should contain an error message"
        assert (
            "User-Agent header is required" in title_response.json()["error"]
        ), "Error should mention User-Agent requirement"

        # Test titles list endpoint
        data = {"titles": ["test_title1", "test_title2"]}
        list_response = requests.post(f"{BASE_URL}/api/list", json=data, headers={"User-Agent": ""})
        assert list_response.status_code == 400, "List endpoint should return 400 without User-Agent"
        assert "error" in list_response.json(), "Response should contain an error message"
        assert (
            "User-Agent header is required" in list_response.json()["error"]
        ), "Error should mention User-Agent requirement"

        print("All tests passed!")
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to the API server. Make sure it's running at", BASE_URL)
        raise


if __name__ == "__main__":
    # python3 I:\core\bots\ma\web\src\tests\test_user_agent.py
    test_api_without_user_agent()
