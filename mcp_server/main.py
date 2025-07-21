from flask import Flask, request, jsonify, Response
import requests
import os
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


# --- Authentication Endpoint ---
@app.route('/mcp/token', methods=['POST'])
def login_for_access_token():
    """
    Authenticates with the main API and returns a JWT token.
    """
    try:
        # The client sends credentials as 'username' and 'password' in a form.
        # We need to forward this to the main API's /token endpoint.
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


# --- Helper Functions ---
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

def forward_request(method, path, **kwargs):
    """
    Forwards a request to the main Campaign Crafter API.
    Requires a valid JWT in the 'Authorization' header.
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Authorization header is missing"}), 401

    url = f"{CAMPAIGN_CRAFTER_API_URL}{path}"
    headers = {
        'Authorization': auth_header,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }

    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=request.get_json(silent=True),
            params=request.args,
            **kwargs
        )
        response.raise_for_status()
        # For DELETE requests, a 204 No Content might not have a JSON body
        if response.status_code == 204:
            return Response(status=204)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.HTTPError as e:
        return jsonify(e.response.json()), e.response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

# --- Campaign Endpoints ---
@app.route('/mcp/campaigns', methods=['POST'])
def create_campaign():
    return forward_request('POST', '/campaigns')

@app.route('/mcp/campaigns', methods=['GET'])
def list_campaigns():
    return forward_request('GET', '/campaigns')

@app.route('/mcp/campaigns/<int:campaign_id>', methods=['GET'])
def get_campaign(campaign_id):
    return forward_request('GET', f'/campaigns/{campaign_id}')

@app.route('/mcp/campaigns/<int:campaign_id>', methods=['PUT'])
def update_campaign(campaign_id):
    return forward_request('PUT', f'/campaigns/{campaign_id}')

@app.route('/mcp/campaigns/<int:campaign_id>', methods=['DELETE'])
def delete_campaign(campaign_id):
    return forward_request('DELETE', f'/campaigns/{campaign_id}')

# --- Character Endpoints ---
@app.route('/mcp/characters', methods=['POST'])
def create_character():
    return forward_request('POST', '/characters')

@app.route('/mcp/characters', methods=['GET'])
def list_characters():
    return forward_request('GET', '/characters')

@app.route('/mcp/characters/<int:character_id>', methods=['GET'])
def get_character(character_id):
    return forward_request('GET', f'/characters/{character_id}')

@app.route('/mcp/characters/<int:character_id>', methods=['PUT'])
def update_character(character_id):
    return forward_request('PUT', f'/characters/{character_id}')

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
    return forward_request('POST', f'/campaigns/{campaign_id}/sections')

@app.route('/mcp/campaigns/<int:campaign_id>/sections', methods=['GET'])
def list_campaign_sections(campaign_id):
    return forward_request('GET', f'/campaigns/{campaign_id}/sections')

@app.route('/mcp/campaigns/<int:campaign_id>/sections/<int:section_id>', methods=['PUT'])
def update_campaign_section(campaign_id, section_id):
    return forward_request('PUT', f'/campaigns/{campaign_id}/sections/{section_id}')

@app.route('/mcp/campaigns/<int:campaign_id>/sections/<int:section_id>', methods=['DELETE'])
def delete_campaign_section(campaign_id, section_id):
    return forward_request('DELETE', f'/campaigns/{campaign_id}/sections/{section_id}')

# --- TOC and Title Generation Endpoints ---
@app.route('/mcp/campaigns/<int:campaign_id>/toc', methods=['POST'])
def generate_toc(campaign_id):
    return forward_request('POST', f'/campaigns/{campaign_id}/toc')

@app.route('/mcp/campaigns/<int:campaign_id>/titles', methods=['POST'])
def generate_titles(campaign_id):
    return forward_request('POST', f'/campaigns/{campaign_id}/titles')

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
                    "method": "token",
                    "token_url": f"{base_url}/mcp/token",
                    "username_field": "username",
                    "password_field": "password"
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
