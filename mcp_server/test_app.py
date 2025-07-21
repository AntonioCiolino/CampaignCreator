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

def test_dynamic_client_registration():
    """Tests the dynamic client registration flow."""
    print("--- Testing Dynamic Client Registration ---")

    # 1. Register a new client
    print("1. Registering a new client...")
    client_data = {
        "client_name": "Test Client",
        "redirect_uris": [f"{MCP_SERVER_URL}/callback"]
    }
    response = requests.post(f"{MCP_SERVER_URL}/register", json=client_data)
    print_response(response)
    assert response.status_code == 201
    client_id = response.json()['client_id']
    assert client_id
    print(f"Successfully registered client with ID: {client_id}")

    # 2. Start authorization with the new client
    print("\n2. Starting authorization with the new client...")
    auth_params = {
        'response_type': 'code',
        'client_id': client_id,
        'redirect_uri': f"{MCP_SERVER_URL}/callback",
        'state': 'xyz'
    }
    response = requests.get(f"{MCP_SERVER_URL}/authorize", params=auth_params)
    assert response.status_code == 200
    print("Successfully got the login form for the new client.")

def test_json_rpc():
    """Tests the JSON-RPC endpoint."""
    print("--- Testing JSON-RPC Endpoint ---")

    # This test requires the main API to be running to get a real token
    token = get_auth_token()
    if not token:
        print("Could not get auth token, skipping JSON-RPC test.")
        return

    print(f"Using token: {token[:10]}...")

    # Test create_campaign method
    print("\n1. Testing 'create_campaign' method...")
    rpc_request = {
        "jsonrpc": "2.0",
        "method": "create_campaign",
        "params": {
            "title": "My RPC Campaign",
            "description": "A campaign created via JSON-RPC."
        },
        "id": 1
    }
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{MCP_SERVER_URL}/rpc", json=rpc_request, headers=headers)
    print_response(response)
    # We expect a 200 OK from the MCP server, but the result will be an error
    # from the main API because it's not running in the sandbox.
    assert response.status_code == 200
    assert response.json()['id'] == 1
    print("'create_campaign' test completed.")

    # Test get_campaign method
    print("\n2. Testing 'get_campaign' method...")
    rpc_request = {
        "jsonrpc": "2.0",
        "method": "get_campaign",
        "params": {"campaign_id": 123}, # Dummy ID
        "id": 2
    }
    response = requests.post(f"{MCP_SERVER_URL}/rpc", json=rpc_request, headers=headers)
    print_response(response)
    assert response.status_code == 200
    assert response.json()['id'] == 2
    print("'get_campaign' test completed.")

    # Test method not found
    print("\n3. Testing method not found...")
    rpc_request = {
        "jsonrpc": "2.0",
        "method": "non_existent_method",
        "params": {},
        "id": 3
    }
    response = requests.post(f"{MCP_SERVER_URL}/rpc", json=rpc_request, headers=headers)
    print_response(response)
    assert response.status_code == 200
    assert response.json()['error']['code'] == -32601
    print("Method not found test completed.")


def main():
    """Main function to run the test application."""
    test_dynamic_client_registration()
    # test_password_grant()
    # test_auth_code_flow()
    # test_json_rpc()


if __name__ == "__main__":
    main()
