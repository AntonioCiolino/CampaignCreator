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


def main():
    """Main function to run the test application."""
    # --- Get auth token ---
    token = get_auth_token()
    if not token:
        print("Failed to get auth token. Aborting test.")
        return

    print(f"Successfully authenticated and got token: {token}")

    # --- Test Bearer token ---
    headers = {"Authorization": f"Bearer {token}"}
    print("\n1. Testing Bearer token...")
    response = requests.get(f"{MCP_SERVER_URL}/campaigns", headers=headers)
    print_response(response)
    assert response.status_code == 200, "Bearer token auth failed"
    print("Bearer token auth successful.")

    # --- Test query parameter ---
    print("\n2. Testing query parameter...")
    response = requests.get(f"{MCP_SERVER_URL}/campaigns?token={token}")
    print_response(response)
    assert response.status_code == 200, "Query parameter auth failed"
    print("Query parameter auth successful.")

    # --- Test Basic Auth ---
    print("\n3. Testing Basic Auth...")
    # The username is the token, password can be anything
    response = requests.get(f"{MCP_SERVER_URL}/campaigns", auth=(token, ''))
    print_response(response)
    assert response.status_code == 200, "Basic Auth failed"
    print("Basic Auth successful.")

    # --- Test custom API key header ---
    api_key_headers = {"X-API-Key": token}
    print("\n4. Testing custom API key header...")
    response = requests.get(f"{MCP_SERVER_URL}/campaigns", headers=api_key_headers)
    print_response(response)
    assert response.status_code == 200, "API key header auth failed"
    print("API key header auth successful.")

    # --- Test no auth ---
    print("\n5. Testing no auth...")
    response = requests.get(f"{MCP_SERVER_URL}/campaigns")
    print_response(response)
    assert response.status_code == 401, "No auth test failed"
    print("No auth test successful.")


if __name__ == "__main__":
    main()
