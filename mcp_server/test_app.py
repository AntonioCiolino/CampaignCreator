import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

MCP_SERVER_URL = f"http://localhost:{os.environ.get('PORT', 5001)}"

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

def main():
    """Main function to run the test application."""
    print("--- Testing MCP Server (Unauthenticated) ---")

    # Test root endpoint
    print("\n1. Testing root endpoint...")
    response = requests.get(MCP_SERVER_URL)
    print_response(response)
    assert response.status_code == 200
    assert response.json()['name'] == "campaign_crafter"
    print("Root endpoint test successful.")

    # Test /mcp endpoint
    print("\n2. Testing /mcp endpoint...")
    response = requests.get(f"{MCP_SERVER_URL}/mcp")
    print_response(response)
    assert response.status_code == 200
    assert response.json()['name'] == "Campaign Crafter"
    print("/mcp endpoint test successful.")

    # Test JSON-RPC endpoint
    print("\n3. Testing JSON-RPC endpoint (unauthenticated)...")
    rpc_request = {
        "jsonrpc": "2.0",
        "method": "get_campaign",
        "params": {"campaign_id": 123},
        "id": "rpc-test"
    }
    response = requests.post(f"{MCP_SERVER_URL}/mcp/rpc", json=rpc_request)
    print_response(response)
    # Since we are not providing any authentication, we expect an error.
    # The `requires_auth` decorator is gone, so the check is in `forward_request`.
    # `forward_request` will return a 401, which the json_rpc_endpoint will wrap.
    assert response.status_code == 200
    assert response.json()['error']['code'] == -32602
    assert "Authentication required" in response.json()['error']['message']['error']
    print("JSON-RPC endpoint unauthenticated test successful.")


if __name__ == "__main__":
    main()
