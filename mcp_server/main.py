from flask import Flask, request, jsonify, Response
import requests
import os
import json
from dotenv import load_dotenv
import secrets
from urllib.parse import urlencode
from datetime import datetime, timezone

load_dotenv()

app = Flask(__name__)

# Configuration for the main Campaign Crafter API
CAMPAIGN_CRAFTER_API_URL = "http://localhost:8000/api/v1"

# --- Root Endpoint ---
@app.route('/.well-known/oauth-authorization-server', methods=['GET'])
def oauth_discovery():
    """OAuth discovery endpoint for Claude"""
    base_url = f"http://127.0.0.1:{os.environ.get('PORT', 5001)}"
    return jsonify({
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/authorize",
        "token_endpoint": f"{base_url}/token",
        "registration_endpoint": f"{base_url}/register",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "password"],
        "token_endpoint_auth_methods_supported": ["none", "client_secret_post"]
    })

@app.before_request
def log_request():
    print(f"Request: {request.method} {request.path}")
    print(f"Headers: {dict(request.headers)}")
    if request.get_json(silent=True):
        print(f"JSON: {request.get_json()}")

@app.route('/', methods=['GET'])
def root():
    """Root endpoint that provides MCP server info"""
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
    base_url = f"http://127.0.0.1:{os.environ.get('PORT', 5001)}"
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


import secrets
from urllib.parse import urlencode

# In-memory storage for authorization codes, tokens, and clients
auth_codes = {}
clients = {}

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
    return f"Received authorization code: {code}. Now, exchange this for a token at /mcp/token.", 200


@app.route('/authorize', methods=['GET', 'POST'])
def authorize():
    if request.method == 'GET':
        client_id = request.args.get('client_id', '')
        redirect_uri = request.args.get('redirect_uri', '')
        response_type = request.args.get('response_type', '')
        state = request.args.get('state', '')

        # Log what Claude is sending
        print(f"OAuth request: client_id={client_id}, redirect_uri={redirect_uri}, state={state}")

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

    print(f"Redirecting to: {redirect_url}")
    return Response(status=302, headers={'Location': redirect_url})


# --- Authentication Endpoint ---
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
        redirect_uri = request.form.get('redirect_uri')
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
def get_token_from_api_key(api_key):
    """
    For this bridge, we'll assume the API key is the JWT token itself.
    In a real-world application, you would exchange the API key for a token.
    """
    return api_key

def authenticate_with_mcp_server(mcp_base_url, username, password):
    """
    Authenticates with the MCP server and returns the access token.
    """
    token_url = f"{mcp_base_url}/token"
    try:
        response = requests.post(token_url, data={"username": username, "password": password, "grant_type": "password"})
        response.raise_for_status()
        return response.json().get("access_token")
    except requests.exceptions.HTTPError as e:
        print(f"Authentication failed: {e.response.text}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred during authentication: {e}")
        return None

from functools import wraps

def requires_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for any of the supported authentication methods
        if (
            request.headers.get('Authorization') is None and
            request.headers.get('X-API-Key') is None and
            request.args.get('token') is None
        ):
            return jsonify({"error": "Authentication required"}), 401

        # The actual token validation or handshake is now handled in forward_request
        return f(*args, **kwargs)
    return decorated_function

def forward_request(method, path, **kwargs):
    """
    Forwards a request to the main Campaign Crafter API.
    Extracts token from various sources or performs a handshake for Basic Auth.
    """
    token = None
    auth_header = request.headers.get('Authorization')
    api_key = request.headers.get('X-API-Key')
    token_param = request.args.get('token')
    basic_auth = request.authorization

    if auth_header and auth_header.lower().startswith('bearer '):
        # Standard Bearer token
        token = auth_header
    elif api_key:
        # Custom API Key header
        token = f"Bearer {get_token_from_api_key(api_key)}"
    elif token_param:
        # Token in query parameter
        token = f"Bearer {token_param}"
    elif basic_auth:
        # Basic Auth: perform a handshake to get a token
        try:
            auth_response = requests.post(
                f"{CAMPAIGN_CRAFTER_API_URL}/auth/token",
                data={"username": basic_auth.username, "password": basic_auth.password}
            )
            auth_response.raise_for_status()
            token_data = auth_response.json()
            token = f"Bearer {token_data['access_token']}"
        except requests.exceptions.HTTPError as e:
            return jsonify(e.response.json()), e.response.status_code
        except (requests.exceptions.RequestException, KeyError) as e:
            return jsonify({"error": f"Failed to authenticate with backend: {str(e)}"}), 500

    if not token:
        return jsonify({"error": "Authentication required"}), 401

    url = f"{CAMPAIGN_CRAFTER_API_URL}{path}"
    # Remove 'token' from args if it exists, to avoid sending it to the backend
    forward_args = request.args.copy()
    forward_args.pop('token', None)

    headers = {
        'Authorization': token,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }

    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            params=forward_args,
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
@requires_auth
def create_campaign():
    return forward_request('POST', '/campaigns')

@app.route('/mcp/campaigns', methods=['GET'])
@requires_auth
def list_campaigns():
    return forward_request('GET', '/campaigns')

@app.route('/mcp/campaigns/<int:campaign_id>', methods=['GET'])
@requires_auth
def get_campaign(campaign_id):
    return forward_request('GET', f'/campaigns/{campaign_id}')

@app.route('/mcp/campaigns/<int:campaign_id>', methods=['PUT'])
@requires_auth
def update_campaign(campaign_id):
    return forward_request('PUT', f'/campaigns/{campaign_id}')

@app.route('/mcp/campaigns/<int:campaign_id>', methods=['DELETE'])
@requires_auth
def delete_campaign(campaign_id):
    return forward_request('DELETE', f'/campaigns/{campaign_id}')

# --- Character Endpoints ---
@app.route('/mcp/characters', methods=['POST'])
@requires_auth
def create_character():
    return forward_request('POST', '/characters')

@app.route('/mcp/characters', methods=['GET'])
@requires_auth
def list_characters():
    return forward_request('GET', '/characters')

@app.route('/mcp/characters/<int:character_id>', methods=['GET'])
@requires_auth
def get_character(character_id):
    return forward_request('GET', f'/characters/{character_id}')

@app.route('/mcp/characters/<int:character_id>', methods=['PUT'])
@requires_auth
def update_character(character_id):
    return forward_request('PUT', f'/characters/{character_id}')

@app.route('/mcp/characters/<int:character_id>', methods=['DELETE'])
@requires_auth
def delete_character(character_id):
    return forward_request('DELETE', f'/characters/{character_id}')

@app.route('/mcp/characters/<int:character_id>/campaigns/<int:campaign_id>', methods=['POST'])
@requires_auth
def link_character_to_campaign(character_id, campaign_id):
    return forward_request('POST', f'/characters/{character_id}/campaigns/{campaign_id}')

@app.route('/mcp/characters/<int:character_id>/campaigns/<int:campaign_id>', methods=['DELETE'])
@requires_auth
def unlink_character_from_campaign(character_id, campaign_id):
    return forward_request('DELETE', f'/characters/{character_id}/campaigns/{campaign_id}')

# --- Campaign Section Endpoints ---
@app.route('/mcp/campaigns/<int:campaign_id>/sections', methods=['POST'])
@requires_auth
def create_campaign_section(campaign_id):
    return forward_request('POST', f'/campaigns/{campaign_id}/sections')

@app.route('/mcp/campaigns/<int:campaign_id>/sections', methods=['GET'])
@requires_auth
def list_campaign_sections(campaign_id):
    return forward_request('GET', f'/campaigns/{campaign_id}/sections')

@app.route('/mcp/campaigns/<int:campaign_id>/sections/<int:section_id>', methods=['PUT'])
@requires_auth
def update_campaign_section(campaign_id, section_id):
    return forward_request('PUT', f'/campaigns/{campaign_id}/sections/{section_id}')

@app.route('/mcp/campaigns/<int:campaign_id>/sections/<int:section_id>', methods=['DELETE'])
@requires_auth
def delete_campaign_section(campaign_id, section_id):
    return forward_request('DELETE', f'/campaigns/{campaign_id}/sections/{section_id}')

# --- TOC and Title Generation Endpoints ---
@app.route('/mcp/campaigns/<int:campaign_id>/toc', methods=['POST'])
@requires_auth
def generate_toc(campaign_id):
    return forward_request('POST', f'/campaigns/{campaign_id}/toc')

@app.route('/mcp/campaigns/<int:campaign_id>/titles', methods=['POST'])
@requires_auth
def generate_titles(campaign_id):
    return forward_request('POST', f'/campaigns/{campaign_id}/titles')


def create_campaign_from_rpc(params):
    """Helper for create_campaign RPC method."""
    # Here you would map params to the arguments of your original forward_request call
    # This is a simplified example
    return forward_request('POST', '/campaigns', json=params)

def get_campaign_from_rpc(params):
    """Helper for get_campaign RPC method."""
    campaign_id = params.get('campaign_id')
    if not campaign_id:
        return {"error": "campaign_id is required"}, 400
    return forward_request('GET', f'/campaigns/{campaign_id}')

def update_campaign_from_rpc(params):
    """Helper for update_campaign RPC method."""
    campaign_id = params.get('campaign_id')
    if not campaign_id:
        return {"error": "campaign_id is required"}, 400
    return forward_request('PUT', f'/campaigns/{campaign_id}', json=params)

def delete_campaign_from_rpc(params):
    """Helper for delete_campaign RPC method."""
    campaign_id = params.get('campaign_id')
    if not campaign_id:
        return {"error": "campaign_id is required"}, 400
    return forward_request('DELETE', f'/campaigns/{campaign_id}')

def create_character_from_rpc(params):
    """Helper for create_character RPC method."""
    return forward_request('POST', '/characters', json=params)

def get_character_from_rpc(params):
    """Helper for get_character RPC method."""
    character_id = params.get('character_id')
    if not character_id:
        return {"error": "character_id is required"}, 400
    return forward_request('GET', f'/characters/{character_id}')

def update_character_from_rpc(params):
    """Helper for update_character RPC method."""
    character_id = params.get('character_id')
    if not character_id:
        return {"error": "character_id is required"}, 400
    return forward_request('PUT', f'/characters/{character_id}', json=params)

def delete_character_from_rpc(params):
    """Helper for delete_character RPC method."""
    character_id = params.get('character_id')
    if not character_id:
        return {"error": "character_id is required"}, 400
    return forward_request('DELETE', f'/characters/{character_id}')

def link_character_to_campaign_from_rpc(params):
    """Helper for link_character_to_campaign RPC method."""
    character_id = params.get('character_id')
    campaign_id = params.get('campaign_id')
    if not character_id or not campaign_id:
        return {"error": "character_id and campaign_id are required"}, 400
    return forward_request('POST', f'/characters/{character_id}/campaigns/{campaign_id}')

def unlink_character_from_campaign_from_rpc(params):
    """Helper for unlink_character_from_campaign RPC method."""
    character_id = params.get('character_id')
    campaign_id = params.get('campaign_id')
    if not character_id or not campaign_id:
        return {"error": "character_id and campaign_id are required"}, 400
    return forward_request('DELETE', f'/characters/{character_id}/campaigns/{campaign_id}')

def create_campaign_section_from_rpc(params):
    """Helper for create_campaign_section RPC method."""
    campaign_id = params.get('campaign_id')
    if not campaign_id:
        return {"error": "campaign_id is required"}, 400
    return forward_request('POST', f'/campaigns/{campaign_id}/sections', json=params)

def list_campaign_sections_from_rpc(params):
    """Helper for list_campaign_sections RPC method."""
    campaign_id = params.get('campaign_id')
    if not campaign_id:
        return {"error": "campaign_id is required"}, 400
    return forward_request('GET', f'/campaigns/{campaign_id}/sections')

def update_campaign_section_from_rpc(params):
    """Helper for update_campaign_section RPC method."""
    campaign_id = params.get('campaign_id')
    section_id = params.get('section_id')
    if not campaign_id or not section_id:
        return {"error": "campaign_id and section_id are required"}, 400
    return forward_request('PUT', f'/campaigns/{campaign_id}/sections/{section_id}', json=params)

def delete_campaign_section_from_rpc(params):
    """Helper for delete_campaign_section RPC method."""
    campaign_id = params.get('campaign_id')
    section_id = params.get('section_id')
    if not campaign_id or not section_id:
        return {"error": "campaign_id and section_id are required"}, 400
    return forward_request('DELETE', f'/campaigns/{campaign_id}/sections/{section_id}')

def generate_toc_from_rpc(params):
    """Helper for generate_toc RPC method."""
    campaign_id = params.get('campaign_id')
    if not campaign_id:
        return {"error": "campaign_id is required"}, 400
    return forward_request('POST', f'/campaigns/{campaign_id}/toc', json=params)

def generate_titles_from_rpc(params):
    """Helper for generate_titles RPC method."""
    campaign_id = params.get('campaign_id')
    if not campaign_id:
        return {"error": "campaign_id is required"}, 400
    return forward_request('POST', f'/campaigns/{campaign_id}/titles', json=params)


# --- JSON-RPC Endpoint ---
@app.route('/mcp/rpc', methods=['POST'])
@requires_auth
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
        if method == 'create_campaign':
            response_data, status_code = create_campaign_from_rpc(params)
        elif method == 'get_campaign':
            response_data, status_code = get_campaign_from_rpc(params)
        elif method == 'update_campaign':
            response_data, status_code = update_campaign_from_rpc(params)
        elif method == 'delete_campaign':
            response_data, status_code = delete_campaign_from_rpc(params)
        elif method == 'create_character':
            response_data, status_code = create_character_from_rpc(params)
        elif method == 'get_character':
            response_data, status_code = get_character_from_rpc(params)
        elif method == 'update_character':
            response_data, status_code = update_character_from_rpc(params)
        elif method == 'delete_character':
            response_data, status_code = delete_character_from_rpc(params)
        elif method == 'link_character_to_campaign':
            response_data, status_code = link_character_to_campaign_from_rpc(params)
        elif method == 'unlink_character_from_campaign':
            response_data, status_code = unlink_character_from_campaign_from_rpc(params)
        elif method == 'create_campaign_section':
            response_data, status_code = create_campaign_section_from_rpc(params)
        elif method == 'list_campaign_sections':
            response_data, status_code = list_campaign_sections_from_rpc(params)
        elif method == 'update_campaign_section':
            response_data, status_code = update_campaign_section_from_rpc(params)
        elif method == 'delete_campaign_section':
            response_data, status_code = delete_campaign_section_from_rpc(params)
        elif method == 'generate_toc':
            response_data, status_code = generate_toc_from_rpc(params)
        elif method == 'generate_titles':
            response_data, status_code = generate_titles_from_rpc(params)
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
    port = int(os.environ.get("PORT", 5001))
    app.run(port=port, debug=True)
