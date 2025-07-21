# IMPORTANT: Do not delete the REST endpoints in this file.
# They are used by the MCP server to forward requests to the main API.

import socket
from flask import Flask, request, jsonify, Response
import requests
import os
import json
from dotenv import load_dotenv
import secrets
from urllib.parse import urlencode
from datetime import datetime, timezone
import sys
load_dotenv()

app = Flask(__name__)

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

# Configuration for the main Campaign Crafter API
CAMPAIGN_CRAFTER_API_URL = "http://localhost:8000/api/v1"
BACKEND_TOKEN = None

def authenticate_with_backend():
    """Authenticates with the main API and stores the token."""
    global BACKEND_TOKEN
    username = os.environ.get("CAMPAIGN_CRAFTER_USERNAME")
    password = os.environ.get("CAMPAIGN_CRAFTER_PASSWORD")

    if not username or not password:
        print("CAMPAIGN_CRAFTER_USERNAME and CAMPAIGN_CRAFTER_PASSWORD environment variables are not set. Cannot authenticate with the backend.", file=sys.stderr)
        return

    try:
        response = requests.post(
            f"{CAMPAIGN_CRAFTER_API_URL}/auth/token",
            data={"username": username, "password": password, "grant_type": "password"}
        )
        response.raise_for_status()
        BACKEND_TOKEN = response.json()["access_token"]
        print("Successfully authenticated with the backend.", file=sys.stderr)
    except requests.exceptions.RequestException as e:
        print(f"Failed to authenticate with the backend: {e}", file=sys.stderr)

# --- Root Endpoint ---
@app.route('/.well-known/oauth-authorization-server', methods=['GET'])
def oauth_discovery():
    """OAuth discovery endpoint for Claude"""
    base_url = f"http://{get_local_ip()}:{os.environ.get('PORT', 5001)}"
    return jsonify({
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/authorize",
        "token_endpoint": f"{base_url}/token",
        "registration_endpoint": f"{base_url}/register",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "password"],
        "token_endpoint_auth_methods_supported": ["none", "client_secret_post"]
    })

@app.route('/', methods=['GET', 'POST'])
def root():
    """
    Root endpoint that provides MCP server info or handles MCP requests.
    """
    if request.method == 'POST':
        # Assume it's an MCP request and forward to the RPC endpoint
        return json_rpc_endpoint()

    # Otherwise, return server info for GET requests
    return jsonify({
        "name": "campaign_crafter",
        "version": "1.0.0",
        "protocol": "mcp",
    })


@app.route('/mcp', methods=['GET'])
def get_mcp_config():
    """
    Returns the server's capabilities.
    """
    base_url = f"http://{get_local_ip()}:{os.environ.get('PORT', 5001)}"
    return jsonify({
        "name": "Campaign Crafter",
        "version": "1.0.0",
        "protocol": "mcp",
        "auth_schemes": [
            {
                "type": "oauth2",
                "url": f"{base_url}/.well-known/oauth-authorization-server"
            }
        ],
        "methods": [
            "create_campaign",
            "get_campaign",
            "update_campaign",
            "delete_campaign",
            "create_character",
            "get_character",
            "update_character",
            "delete_character",
            "link_character_to_campaign",
            "unlink_character_from_campaign",
            "create_campaign_section",
            "list_campaign_sections",
            "update_campaign_section",
            "delete_campaign_section",
            "generate_toc",
            "generate_titles",
        ]
    })





# --- Helper Functions ---

def forward_request(method, path, **kwargs):
    """
    Forwards a request to the main Campaign Crafter API.
    """
    if not BACKEND_TOKEN:
        return {"error": "Backend not authenticated"}, 503

    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return {"error": "Authentication required"}, 401

    headers = {
        'Authorization': auth_header,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }

    url = f"{CAMPAIGN_CRAFTER_API_URL}{path}"

    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            **kwargs
        )
        response.raise_for_status()
        # For DELETE requests, a 204 No Content might not have a JSON body
        if response.status_code == 204:
            return {}, 204
        return response.json(), response.status_code
    except requests.exceptions.HTTPError as e:
        return e.response.json(), e.response.status_code
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}, 500





# --- Campaign Endpoints ---
@app.route('/mcp/campaigns', methods=['POST'])
def create_campaign():
    return forward_request('POST', '/campaigns', json=request.get_json())

@app.route('/mcp/campaigns', methods=['GET'])
def list_campaigns():
    return forward_request('GET', '/campaigns')

@app.route('/mcp/campaigns/<int:campaign_id>', methods=['GET'])
def get_campaign(campaign_id):
    return forward_request('GET', f'/campaigns/{campaign_id}')

@app.route('/mcp/campaigns/<int:campaign_id>', methods=['PUT'])
def update_campaign(campaign_id):
    return forward_request('PUT', f'/campaigns/{campaign_id}', json=request.get_json())

@app.route('/mcp/campaigns/<int:campaign_id>', methods=['DELETE'])
def delete_campaign(campaign_id):
    return forward_request('DELETE', f'/campaigns/{campaign_id}')

# --- Character Endpoints ---
@app.route('/mcp/characters', methods=['POST'])
def create_character():
    return forward_request('POST', '/characters', json=request.get_json())

@app.route('/mcp/characters', methods=['GET'])
def list_characters():
    return forward_request('GET', '/characters')

@app.route('/mcp/characters/<int:character_id>', methods=['GET'])
def get_character(character_id):
    return forward_request('GET', f'/characters/{character_id}')

@app.route('/mcp/characters/<int:character_id>', methods=['PUT'])
def update_character(character_id):
    return forward_request('PUT', f'/characters/{character_id}', json=request.get_json())

@app.route('/mcp/characters/<int:character_id>', methods=['DELETE'])
def delete_character(character_id):
    return forward_request('DELETE', f'/characters/{character_id}')

@app.route('/mcp/characters/<int:character_id>/campaigns/<int:campaign_id>', methods=['POST'])
def link_character_to_campaign(character_id, campaign_id):
    return forward_request('POST', f'/characters/{character_id}/campaigns/{campaign_id}')

@app.route('/mcp/characters/<int:character_id>/campaigns/<int:campaign_id>', methods=['DELETE'])
def unlink_character_from_campaign(character_id, campaign_id):
    return forward_request('DELETE', f'/characters/{character_id}/campaigns/{campaign_id}')

# --- Campaign Section Endpoints ---
@app.route('/mcp/campaigns/<int:campaign_id>/sections', methods=['POST'])
def create_campaign_section(campaign_id):
    return forward_request('POST', f'/campaigns/{campaign_id}/sections', json=request.get_json())

@app.route('/mcp/campaigns/<int:campaign_id>/sections', methods=['GET'])
def list_campaign_sections(campaign_id):
    return forward_request('GET', f'/campaigns/{campaign_id}/sections')

@app.route('/mcp/campaigns/<int:campaign_id>/sections/<int:section_id>', methods=['PUT'])
def update_campaign_section(campaign_id, section_id):
    return forward_request('PUT', f'/campaigns/{campaign_id}/sections/{section_id}', json=request.get_json())

@app.route('/mcp/campaigns/<int:campaign_id>/sections/<int:section_id>', methods=['DELETE'])
def delete_campaign_section(campaign_id, section_id):
    return forward_request('DELETE', f'/campaigns/{campaign_id}/sections/{section_id}')

# --- TOC and Title Generation Endpoints ---
@app.route('/mcp/campaigns/<int:campaign_id>/toc', methods=['POST'])
def generate_toc(campaign_id):
    return forward_request('POST', f'/campaigns/{campaign_id}/toc', json=request.get_json())

@app.route('/mcp/campaigns/<int:campaign_id>/titles', methods=['POST'])
def generate_titles(campaign_id):
    return forward_request('POST', f'/campaigns/{campaign_id}/titles', json=request.get_json())


# --- JSON-RPC Endpoint ---
@app.route('/mcp/rpc', methods=['POST'])
def json_rpc_endpoint():
    try:
        data = request.get_json()
        if not data or "jsonrpc" not in data or "method" not in data:
            raise ValueError("Invalid JSON-RPC request")

        jsonrpc = data["jsonrpc"]
        method = data["method"]
        params = data.get("params", {})
        request_id = data.get("id")

        if jsonrpc != "2.0":
            raise ValueError("Invalid JSON-RPC version")

        # Dispatch to the correct function based on the method
        if method in [
            "create_campaign",
            "get_campaign",
            "update_campaign",
            "delete_campaign",
            "create_character",
            "get_character",
            "update_character",
            "delete_character",
            "link_character_to_campaign",
            "unlink_character_from_campaign",
            "create_campaign_section",
            "list_campaign_sections",
            "update_campaign_section",
            "delete_campaign_section",
            "generate_toc",
            "generate_titles",
        ]:
            path = f"/{method.replace('_', '/')}"
            http_method = "POST" if "create" in method or "generate" in method or "link" in method else "GET"
            if "update" in method:
                http_method = "PUT"
            if "delete" in method or "unlink" in method:
                http_method = "DELETE"

            response_data, status_code = forward_request(http_method, path, json=params)
        else:
            return jsonify({"jsonrpc": "2.0", "error": {"code": -32601, "message": f"Method '{method}' not found"}, "id": request_id})

        if status_code >= 400:
            return jsonify({"jsonrpc": "2.0", "error": {"code": -32602, "message": response_data}, "id": request_id})
        else:
            return jsonify({"jsonrpc": "2.0", "result": response_data, "id": request_id})

    except (ValueError, json.JSONDecodeError) as e:
        return jsonify({"jsonrpc": "2.0", "error": {"code": -32700, "message": f"Parse error: {e}"}, "id": None})
    except Exception as e:
        return jsonify({"jsonrpc": "2.0", "error": {"code": -32603, "message": f"Internal error: {e}"}, "id": request_id})



if __name__ == '__main__':
    authenticate_with_backend()
    port = int(os.environ.get("PORT", 5001))
    app.run(
        host='0.0.0.0',
        port=port,
        threaded=True,  # Handle multiple connections
        use_reloader=False  # Prevent connection issues during development
    )
