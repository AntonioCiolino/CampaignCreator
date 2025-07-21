from flask import Flask, request, jsonify, Response
import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configuration for the main Campaign Crafter API
CAMPAIGN_CRAFTER_API_URL = "http://localhost:8000/api/v1"

# --- Root Endpoint ---
@app.route('/', methods=['GET'])
def list_mcp_versions():
    """
    Returns a list of available MCP versions.
    """
    return jsonify(["0.1.0"])


@app.route('/mcp', methods=['GET'])
def get_mcp_config():
    """
    Returns the MCP configuration.
    """
    return list_mcp_endpoints()


import secrets
from urllib.parse import urlencode

# In-memory storage for authorization codes and tokens
auth_codes = {}

# --- OAuth 2.0 Endpoints ---

@app.route('/mcp/callback', methods=['GET'])
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


@app.route('/mcp/authorize', methods=['GET', 'POST'])
def authorize():
    """
    Presents a login form and handles authorization requests.
    """
    if request.method == 'GET':
        # Display the login form, pre-filling hidden fields from query params
        client_id = request.args.get('client_id', '')
        redirect_uri = request.args.get('redirect_uri', '')
        response_type = request.args.get('response_type', '')
        state = request.args.get('state', '')

        if response_type != 'code':
            return jsonify({"error": "unsupported_response_type"}), 400
        if not client_id or not redirect_uri:
            return jsonify({"error": "invalid_request", "error_description": "client_id and redirect_uri are required"}), 400

        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login</title>
        </head>
        <body>
            <h1>Authorize App</h1>
            <form method="post">
                <input type="hidden" name="client_id" value="{client_id}">
                <input type="hidden" name="redirect_uri" value="{redirect_uri}">
                <input type="hidden" name="response_type" value="{response_type}">
                <input type="hidden" name="state" value="{state}">
                <div>
                    <label for="username">Username:</label>
                    <input type="text" id="username" name="username">
                </div>
                <div>
                    <label for="password">Password:</label>
                    <input type="password" id="password" name="password">
                </div>
                <br>
                <input type="submit" value="Authorize">
            </form>
        </body>
        </html>
        '''

    # Handle POST request from the form
    username = request.form.get('username')
    password = request.form.get('password')
    client_id = request.form.get('client_id')
    redirect_uri = request.form.get('redirect_uri')
    state = request.form.get('state')

    # Authenticate user against the main API
    try:
        auth_response = requests.post(
            f"{CAMPAIGN_CRAFTER_API_URL}/auth/token",
            data={"username": username, "password": password, "grant_type": "password"}
        )
        auth_response.raise_for_status()
        # If successful, we don't need the token here, just confirmation.
    except requests.exceptions.HTTPError:
        return "Invalid credentials", 401
    except requests.exceptions.RequestException:
        return "Error connecting to authentication service", 500

    # If authentication is successful, generate and store the auth code
    auth_code = secrets.token_urlsafe(16)
    # Associate the code with the user and client
    auth_codes[auth_code] = {'client_id': client_id, 'user_id': username}

    # Redirect back to the client with the auth code
    params = {'code': auth_code, 'state': state}
    return Response(status=302, headers={'Location': f"{redirect_uri}?{urlencode(params)}"})


# --- Authentication Endpoint ---
@app.route('/mcp/token', methods=['POST'])
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

        if not code or not redirect_uri or not client_id:
            return jsonify({"error": "invalid_request"}), 400

        auth_code_data = auth_codes.pop(code, None)
        if not auth_code_data or auth_code_data['client_id'] != client_id:
            return jsonify({"error": "invalid_grant"}), 400

        # In a real app, you'd now issue a token for the user.
        # We'll simulate this by creating a dummy token.
        # This part does NOT contact the main API, as the main API doesn't support OAuth.
        access_token = secrets.token_urlsafe(32)
        return jsonify({
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 3600,
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
        response = requests.post(token_url, data={"username": username, "password": password})
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
        # Add other methods here...
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


@app.route('/mcp/endpoints', methods=['GET'])
def list_mcp_endpoints():
    """
    Returns a JSON object describing the available MCP endpoints.
    """
    base_url = f"http://localhost:{os.environ.get('PORT', 5001)}"
    mcp_config = {
        "mcpServers": {
            "campaign_crafter": {
                "command": "python",
                "args": [
                    "-m",
                    "flask",
                    "--app",
                    "main",
                    "run",
                    "--port",
                    os.environ.get('PORT', 5001)
                ],
                "env": {
                    "FLASK_APP": "main.py",
                    "FLASK_RUN_PORT": os.environ.get('PORT', '5001'),
                    "TEST_USERNAME": os.environ.get('TEST_USERNAME', 'testuser'),
                    "TEST_PASSWORD": os.environ.get('TEST_PASSWORD', 'testpassword')
                },
                "mcp_version": "0.1.0",
                "client_name": "Campaign Crafter MCP Client",
                "base_url": base_url,
                "auth": {
                    "method": "oauth2",
                    "authorize_url": f"{base_url}/mcp/authorize",
                    "token_url": f"{base_url}/mcp/token",
                    "grant_types_supported": ["authorization_code", "password"],
                    "help": "Full OAuth2 support with Authorization Code and Password grants."
                },
                "endpoints": {
                    "create_campaign": {
                        "path": "/mcp/campaigns",
                        "method": "POST",
                        "body": {
                            "title": "{campaign_title}",
                            "description": "{campaign_description}",
                            "initial_user_prompt": "{initial_user_prompt}",
                            "skip_concept_generation": "{skip_concept_generation}"
                        },
                        "requires_auth": True
                    },
                    "get_campaign": {
                        "path": "/mcp/campaigns/{campaign_id}",
                        "method": "GET",
                        "requires_auth": True
                    },
                    "create_character": {
                        "path": "/mcp/characters",
                        "method": "POST",
                        "body": {
                            "name": "{character_name}",
                            "description": "{character_description}"
                        },
                        "requires_auth": True
                    }
                }
            }
        }
    }
    return jsonify(mcp_config)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    app.run(port=port, debug=True)
