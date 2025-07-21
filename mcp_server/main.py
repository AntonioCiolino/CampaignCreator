# IMPORTANT: Do not delete the REST endpoints in this file.
# They are used by the MCP server to forward requests to the main API.

from flask import Flask, request, jsonify, Response
import requests
import os
import json
from dotenv import load_dotenv
import secrets
from urllib.parse import urlencode
from datetime import datetime, timezone
import sys
import socket

load_dotenv()

app = Flask(__name__)

# Configuration for the main Campaign Crafter API
CAMPAIGN_CRAFTER_API_URL = "http://localhost:8000/api/v1"
BACKEND_TOKEN = None

# In-memory storage for authorization codes, tokens, and clients
auth_codes = {}
clients = {}

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

# --- /.well-known/oauth-authorization-server Endpoint ---
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

# --- Root Endpoint ---
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

# --- /mcp Endpoint ---
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

# --- OAuth 2.0 Endpoints ---
@app.route('/register', methods=['POST'])
def register_client():
    """
    Dynamically registers a new client.
    """
    client_info = request.get_json()
    if not client_info or 'client_name' not in client_info or 'redirect_uris' not in client_info:
        return jsonify({"error": "invalid_client_metadata"}), 400

    client_id = secrets.token_urlsafe(16)
    clients[client_id] = {
        "client_name": client_info["client_name"],
        "redirect_uris": client_info["redirect_uris"],
        "client_id_issued_at": datetime.now(timezone.utc).timestamp()
    }

    return jsonify({
        "client_id": client_id,
        "client_name": client_info["client_name"],
        "redirect_uris": client_info["redirect_uris"],
        "grant_types": ["authorization_code"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "none"
    }), 201

@app.route('/callback', methods=['GET'])
def callback():
    """
    The client's redirect URI. Handles the auth code from the authorize endpoint.
    This is for demonstration; a real client would handle this.
    """
    code = request.args.get('code')
    if not code:
        return "Error: No code provided.", 400

    # Here, a real client would exchange the code for a token
    return f"Received authorization code: {code}. Now, exchange this for a token at /token.", 200

@app.route('/authorize', methods=['GET', 'POST'])
def authorize():
    if request.method == 'GET':
        client_id = request.args.get('client_id', '')
        redirect_uri = request.args.get('redirect_uri', '')
        response_type = request.args.get('response_type', '')
        state = request.args.get('state', '')

        # Log what Claude is sending
        print(f"OAuth request: client_id={client_id}, redirect_uri={redirect_uri}, state={state}", file=sys.stderr)

        if response_type != 'code':
            return jsonify({"error": "unsupported_response_type"}), 400
        if not client_id or not redirect_uri:
            return jsonify({"error": "invalid_request"}), 400

        if client_id not in clients:
            return jsonify({"error": "unauthorized_client"}), 400

        if redirect_uri not in clients[client_id]["redirect_uris"]:
            return jsonify({"error": "invalid_request", "error_description": "redirect_uri does not match client's registered URIs"}), 400

        # Store the original redirect_uri for later
        session_id = secrets.token_urlsafe(16)
        auth_codes[f"session_{session_id}"] = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'state': state
        }

        return f'''
        <!DOCTYPE html>
        <html>
        <head><title>Login</title></head>
        <body>
            <h1>Authorize Campaign Crafter</h1>
            <form method="post">
                <input type="hidden" name="session_id" value="{session_id}">
                <div>
                    <label for="username">Username:</label>
                    <input type="text" id="username" name="username" required>
                </div>
                <div>
                    <label for="password">Password:</label>
                    <input type="password" id="password" name="password" required>
                </div>
                <br>
                <input type="submit" value="Authorize">
            </form>
        </body>
        </html>
        '''

    # Handle POST
    session_id = request.form.get('session_id')
    session_data = auth_codes.get(f"session_{session_id}")

    if not session_data:
        return "Invalid session", 400

    username = request.form.get('username')
    password = request.form.get('password')

    # Authenticate with backend
    try:
        auth_response = requests.post(
            f"{CAMPAIGN_CRAFTER_API_URL}/auth/token",
            data={"username": username, "password": password, "grant_type": "password"}
        )
        auth_response.raise_for_status()
        backend_token = auth_response.json().get('access_token')
    except requests.exceptions.HTTPError:
        return "Invalid credentials", 401
    except requests.exceptions.RequestException:
        return "Error connecting to authentication service", 500

    # Generate auth code
    auth_code = secrets.token_urlsafe(16)
    auth_codes[auth_code] = {
        'client_id': session_data['client_id'],
        'user_id': username,
        'backend_token': backend_token
    }

    # Clean up session
    del auth_codes[f"session_{session_id}"]

    # Redirect back to Claude
    params = {'code': auth_code, 'state': session_data['state']}
    redirect_url = f"{session_data['redirect_uri']}?{urlencode(params)}"

    print(f"Redirecting to: {redirect_url}", file=sys.stderr)
    return Response(status=302, headers={'Location': redirect_url})

@app.route('/token', methods=['POST'])
def token():
    """
    Handles token requests for both password and authorization_code grant types.
    """
    grant_type = request.form.get('grant_type')

    if grant_type == 'password':
        # Forward username/password to the main API's token endpoint
        try:
            response = requests.post(
                f"{CAMPAIGN_CRAFTER_API_URL}/auth/token",
                data=request.form
            )
            response.raise_for_status()
            return jsonify(response.json()), response.status_code
        except requests.exceptions.HTTPError as e:
            return jsonify(e.response.json()), e.response.status_code
        except requests.exceptions.RequestException as e:
            return jsonify({"error": str(e)}), 500

    elif grant_type == 'authorization_code':
        code = request.form.get('code')
        client_id = request.form.get('client_id')

        if not code or not client_id:
            return jsonify({"error": "invalid_request"}), 400

        if client_id not in clients:
            return jsonify({"error": "unauthorized_client"}), 400

        auth_code_data = auth_codes.pop(code, None)

        if not auth_code_data or auth_code_data['client_id'] != client_id:
            return jsonify({"error": "invalid_grant"}), 400

        # Return the backend token we stored earlier
        return jsonify({
            "access_token": auth_code_data['backend_token'],
            "token_type": "bearer",
            "user_id": auth_code_data['user_id']
        })

    else:
        return jsonify({"error": "unsupported_grant_type"}), 400


# --- Helper Functions ---
def forward_request(method, path, **kwargs):
    """
    Forwards a request to the main Campaign Crafter API.
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return {"error": "Authentication required"}, 401

    if not BACKEND_TOKEN:
        return {"error": "Backend not authenticated"}, 503

    headers = {
        'Authorization': f"Bearer {BACKEND_TOKEN}",
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
        use_reloader=False
    )
