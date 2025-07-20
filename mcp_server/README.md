# MCP Server for Campaign Crafter

This server acts as a facade for the main Campaign Crafter API, providing a bridge for MCP (Model Context Protocol) clients.

## Setup

1.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\\Scripts\\activate`
    ```

2.  **Start the main Campaign Crafter API.** The MCP server depends on the main API, which must be running on `http://localhost:8000`.

3.  **Install the MCP server dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the MCP server:**
    ```bash
    python main.py
    ```

The MCP server will be available at the port specified in your `.env` file (default is `http://localhost:5001`).

The `test_app.py` script uses credentials from the `.env` file to authenticate with the main API. Make sure to update the `TEST_USERNAME` and `TEST_PASSWORD` variables in your `.env` file with the credentials of a valid test user.

## API Documentation

All endpoints are prefixed with `/mcp`.

### Campaigns

*   **Create Campaign:** `POST /campaigns`
    *   **Body:** JSON object with `name` (string) and `description` (string).
    *   **Example:** `curl -X POST -H "Content-Type: application/json" -d '{"name": "My New Campaign", "description": "A test campaign."}' http://localhost:5001/mcp/campaigns`

*   **List Campaigns:** `GET /campaigns`
    *   **Example:** `curl http://localhost:5001/mcp/campaigns`

*   **Get Campaign:** `GET /campaigns/<campaign_id>`
    *   **Example:** `curl http://localhost:5001/mcp/campaigns/1`

*   **Update Campaign:** `PUT /campaigns/<campaign_id>`
    *   **Body:** JSON object with `name` and/or `description`.
    *   **Example:** `curl -X PUT -H "Content-Type: application/json" -d '{"name": "My Updated Campaign"}' http://localhost:5001/mcp/campaigns/1`

*   **Delete Campaign:** `DELETE /campaigns/<campaign_id>`
    *   **Example:** `curl -X DELETE http://localhost:5001/mcp/campaigns/1`

### Characters

*   **Create Character:** `POST /characters`
    *   **Body:** JSON object with `name` (string) and `description` (string).
    *   **Example:** `curl -X POST -H "Content-Type: application/json" -d '{"name": "My New Character", "description": "A test character."}' http://localhost:5001/mcp/characters`

*   **List Characters:** `GET /characters`
    *   **Example:** `curl http://localhost:5001/mcp/characters`

*   **Get Character:** `GET /characters/<character_id>`
    *   **Example:** `curl http://localhost:5001/mcp/characters/1`

*   **Update Character:** `PUT /characters/<character_id>`
    *   **Body:** JSON object with `name` and/or `description`.
    *   **Example:** `curl -X PUT -H "Content-Type: application/json" -d '{"name": "My Updated Character"}' http://localhost:5001/mcp/characters/1`

*   **Delete Character:** `DELETE /characters/<character_id>`
    *   **Example:** `curl -X DELETE http://localhost:5001/mcp/characters/1`

*   **Link Character to Campaign:** `POST /characters/<character_id>/campaigns/<campaign_id>`
    *   **Example:** `curl -X POST http://localhost:5001/mcp/characters/1/campaigns/1`

*   **Unlink Character from Campaign:** `DELETE /characters/<character_id>/campaigns/<campaign_id>`
    *   **Example:** `curl -X DELETE http://localhost:5001/mcp/characters/1/campaigns/1`

### Campaign Sections

*   **Create Campaign Section:** `POST /campaigns/<campaign_id>/sections`
    *   **Body:** JSON object with `title` (string), `content` (string), and `prompt` (string).
    *   **Example:** `curl -X POST -H "Content-Type: application/json" -d '{"title": "New Section", "content": "...", "prompt": "Write about a thing"}' http://localhost:5001/mcp/campaigns/1/sections`

*   **List Campaign Sections:** `GET /campaigns/<campaign_id>/sections`
    *   **Example:** `curl http://localhost:5001/mcp/campaigns/1/sections`

*   **Update Campaign Section:** `PUT /campaigns/<campaign_id>/sections/<section_id>`
    *   **Body:** JSON object with `title` and/or `content`.
    *   **Example:** `curl -X PUT -H "Content-Type: application/json" -d '{"title": "Updated Section"}' http://localhost:5001/mcp/campaigns/1/sections/1`

*   **Delete Campaign Section:** `DELETE /campaigns/<campaign_id>/sections/<section_id>`
    *   **Example:** `curl -X DELETE http://localhost:5001/mcp/campaigns/1/sections/1`

### Table of Contents (TOC) and Title Generation

*   **Generate TOC:** `POST /campaigns/<campaign_id>/toc`
    *   **Body:** Empty JSON object `{}`.
    *   **Example:** `curl -X POST http://localhost:5001/mcp/campaigns/1/toc`

*   **Generate Titles:** `POST /campaigns/<campaign_id>/titles`
    *   **Body:** Empty JSON object `{}`.
    *   **Example:** `curl -X POST http://localhost:5001/mcp/campaigns/1/titles`
