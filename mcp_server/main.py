from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configuration for the main Campaign Crafter API
CAMPAIGN_CRAFTER_API_URL = "http://localhost:8000/api/v1"

# --- Helper Functions ---
def forward_request(method, path, **kwargs):
    """
    Forwards a request to the main Campaign Crafter API.
    """
    url = f"{CAMPAIGN_CRAFTER_API_URL}{path}"
    headers = {key: value for key, value in request.headers if key != 'Host'}

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

from flask import Response

# --- TOC and Title Generation Endpoints ---
@app.route('/mcp/campaigns/<int:campaign_id>/seed_sections_from_toc', methods=['POST'])
def seed_sections_from_toc(campaign_id):
    auto_populate = request.args.get('auto_populate', 'false').lower() == 'true'

    url = f"{CAMPAIGN_CRAFTER_API_URL}/campaigns/{campaign_id}/seed_sections_from_toc?auto_populate={auto_populate}"
    headers = {key: value for key, value in request.headers if key != 'Host'}

    try:
        # Use stream=True to handle the SSE stream
        response = requests.post(url, headers=headers, stream=True)

        def generate():
            for chunk in response.iter_content(chunk_size=1024):
                yield chunk

        return Response(generate(), content_type=response.headers['Content-Type'])

    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

@app.route('/mcp/campaigns/<int:campaign_id>/titles', methods=['POST'])
def generate_titles(campaign_id):
    return forward_request('POST', f'/campaigns/{campaign_id}/titles')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    app.run(port=port, debug=True)
