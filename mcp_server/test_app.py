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
    token = get_auth_token()
    if not token:
        print("Failed to get auth token. Aborting test.")
        return

    print(f"Successfully authenticated and got token: {token}")

    headers = {"Authorization": f"Bearer {token}"}

    # --- Try to access a protected endpoint ---
    print("Attempting to list campaigns (a protected endpoint)...")
    response = requests.get(f"{MCP_SERVER_URL}/campaigns", headers=headers)
    print_response(response)

    if response.status_code == 200:
        print("Successfully accessed protected endpoint.")
    else:
        print("Failed to access protected endpoint.")


if __name__ == "__main__":
    main()
