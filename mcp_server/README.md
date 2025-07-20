# MCP Server for Campaign Crafter

This server acts as a facade for the main Campaign Crafter API, providing a bridge for MCP (Mission Control Protocol) clients.

## Setup

1.  **Start the main Campaign Crafter API.** The MCP server depends on the main API, which must be running on `http://localhost:8000`.

2.  **Install the MCP server dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the MCP server:**
    ```bash
    python main.py
    ```

The MCP server will be available at `http://localhost:5001`.

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
