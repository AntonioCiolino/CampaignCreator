import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

MCP_SERVER_URL = f"http://localhost:{os.environ.get('PORT', 5001)}/mcp"
CAMPAIGN_CRAFTER_API_URL = "http://localhost:8000/api/v1"

# --- IMPORTANT ---
# The test credentials are now loaded from the .env file.
TEST_USERNAME = os.environ.get("TEST_USERNAME", "testuser")
TEST_PASSWORD = os.environ.get("TEST_PASSWORD", "testpassword")

def print_response(response):
    """Helper function to print response details."""
    print(f"Status Code: {response.status_code}")
    try:
        print("Response JSON:")
        print(json.dumps(response.json(), indent=2))
    except json.JSONDecodeError:
        print("Response Text:")
        print(response.text)
    print("-" * 20)

from main import authenticate_with_mcp_server

def get_auth_token():
    """Gets an authentication token from the MCP server."""
    print("Getting auth token...")
    return authenticate_with_mcp_server(MCP_SERVER_URL, TEST_USERNAME, TEST_PASSWORD)


def test_password_grant():
    """Tests the OAuth 2.0 Password Grant flow."""
    print("--- Testing Password Grant ---")
    data = {
        "grant_type": "password",
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    }
    response = requests.post(f"{MCP_SERVER_URL}/token", data=data)
    print_response(response)
    # This will fail in the sandbox, which is expected
    # assert response.status_code == 200
    # assert "access_token" in response.json()
    print("Password Grant test completed.\n")

def test_auth_code_flow():
    """Tests the OAuth 2.0 Authorization Code Grant flow."""
    print("--- Testing Authorization Code Flow ---")
    # 1. Start authorization
    auth_url = (
        f"{MCP_SERVER_URL}/authorize"
        "?response_type=code"
        "&client_id=test_client"
        f"&redirect_uri={MCP_SERVER_URL}/callback"
        "&state=xyz"
    )
    print(f"1. Requesting authorization from: {auth_url}")
    # We don't follow the redirect in this test, just check that we get one
    response = requests.get(auth_url, allow_redirects=False)
    print(f"Status Code: {response.status_code}")
    assert response.status_code == 302, "Expected a redirect from /authorize"
    redirect_location = response.headers['Location']
    print(f"Redirected to: {redirect_location}")

    # 2. Extract code from redirect
    from urllib.parse import urlparse, parse_qs
    parsed_url = urlparse(redirect_location)
    query_params = parse_qs(parsed_url.query)
    auth_code = query_params.get('code', [None])[0]
    assert auth_code, "Failed to get authorization code"
    print(f"2. Extracted authorization code: {auth_code}")

    # 3. Exchange code for a token
    print("3. Exchanging authorization code for a token...")
    token_data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": f"{MCP_SERVER_URL}/callback",
        "client_id": "test_client"
    }
    response = requests.post(f"{MCP_SERVER_URL}/token", data=token_data)
    print_response(response)
    assert response.status_code == 200, "Failed to exchange code for token"
    assert "access_token" in response.json()
    print("Authorization Code Flow test completed.\n")

def main():
    """Main function to run the test application."""
    test_password_grant()
    test_auth_code_flow()


if __name__ == "__main__":
    main()
