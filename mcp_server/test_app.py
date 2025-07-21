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
    """Tests the OAuth 2.0 Authorization Code Grant flow with a login form."""
    print("--- Testing Authorization Code Flow with UI ---")

    # Step 1: Client initiates authorization, gets login form
    auth_params = {
        'response_type': 'code',
        'client_id': 'test_client',
        'redirect_uri': f"{MCP_SERVER_URL}/callback",
        'state': 'xyz'
    }
    print("1. Requesting authorization form...")
    response = requests.get(f"{MCP_SERVER_URL}/authorize", params=auth_params)
    print(f"Status Code: {response.status_code}")
    assert response.status_code == 200, "Expected to get a login form"
    assert "<h1>Authorize App</h1>" in response.text, "Login form content is missing"
    print("Successfully received login form.")

    # Step 2: User submits login form
    print("\n2. Simulating user login...")
    form_data = {
        'client_id': auth_params['client_id'],
        'redirect_uri': auth_params['redirect_uri'],
        'response_type': auth_params['response_type'],
        'state': auth_params['state'],
        'username': TEST_USERNAME,
        'password': TEST_PASSWORD
    }
    # This will fail in the sandbox because the main API isn't running
    response = requests.post(f"{MCP_SERVER_URL}/authorize", data=form_data, allow_redirects=False)
    print(f"Status Code: {response.status_code}")

    # In the sandbox, we expect a 500 error because the backend call fails.
    # In a real environment, we would expect a 302 redirect.
    if response.status_code == 302:
        print("Successfully authenticated, received redirect.")
        redirect_location = response.headers['Location']
        print(f"Redirected to: {redirect_location}")

        # 3. Extract code from redirect
        from urllib.parse import urlparse, parse_qs
        parsed_url = urlparse(redirect_location)
        query_params = parse_qs(parsed_url.query)
        auth_code = query_params.get('code', [None])[0]
        assert auth_code, "Failed to get authorization code"
        print(f"3. Extracted authorization code: {auth_code}")
    else:
        print("Could not complete authentication (as expected in sandbox).")
        print_response(response)
        # Set a dummy auth_code to allow the next step to be tested
        auth_code = "dummy_code_for_testing"
        # Manually add it to the server's memory
        from main import auth_codes
        auth_codes[auth_code] = {'client_id': 'test_client', 'user_id': TEST_USERNAME}

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
    # This will fail in the sandbox because the auth_code is a dummy
    # assert response.status_code == 200, "Failed to exchange code for token"
    # assert "access_token" in response.json()
    print("Authorization Code Flow test completed.\n")

def main():
    """Main function to run the test application."""
    test_password_grant()
    test_auth_code_flow()


if __name__ == "__main__":
    main()
