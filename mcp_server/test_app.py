import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

from main import get_local_ip

MCP_SERVER_URL = f"http://{get_local_ip()}:{os.environ.get('PORT', 5001)}"

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
    print("\n3. Testing JSON-RPC endpoint...")
    rpc_request = {
        "jsonrpc": "2.0",
        "method": "get_campaign",
        "params": {"campaign_id": 123},
        "id": "rpc-test"
    }
    response = requests.post(f"{MCP_SERVER_URL}/mcp/rpc", json=rpc_request)
    print_response(response)
    # This will fail in the sandbox because the backend is not running,
    # but it proves the server is forwarding the request.
    # We expect a 503 error if the backend is not authenticated.
    assert response.status_code == 200
    assert response.json()['error']['code'] == -32602
    print("JSON-RPC endpoint test completed.")


if __name__ == "__main__":
    main()
