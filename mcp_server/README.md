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

*   **Seed Sections from TOC:** `POST /campaigns/<campaign_id>/seed_sections_from_toc`
    *   **Query Parameters:**
        *   `auto_populate` (boolean, optional): If `true`, the server will automatically generate content for the sections as they are created.
    *   **Returns:** A Server-Sent Events (SSE) stream with the progress of the section creation.
    *   **Example:** `curl -N http://localhost:5001/mcp/campaigns/1/seed_sections_from_toc?auto_populate=true`

*   **Generate Titles:** `POST /campaigns/<campaign_id>/titles`
    *   **Body:** Empty JSON object `{}`.
    *   **Example:** `curl -X POST http://localhost:5001/mcp/campaigns/1/titles`

## Connecting to the API

You can connect to the MCP server using any HTTP client. Here are some examples using `curl` and Python's `requests` library.

### Authentication

First, you'll need to get an authentication token from the main Campaign Crafter API.

**`curl`:**
```bash
curl -X POST -d "username=testuser&password=testpassword" http://localhost:8000/api/v1/auth/token
```

**Python:**
```python
import requests

auth_data = {
    "username": "testuser",
    "password": "testpassword"
}
response = requests.post("http://localhost:8000/api/v1/auth/token", data=auth_data)
token = response.json()["access_token"]
```

### Making Authenticated Requests

Once you have an access token, include it in the `Authorization` header of your requests to the MCP server.

**`curl`:**
```bash
curl -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>" http://localhost:5001/mcp/campaigns
```

**Python:**
```python
headers = {"Authorization": f"Bearer {token}"}
response = requests.get("http://localhost:5001/mcp/campaigns", headers=headers)
print(response.json())
```

## Connecting to an MCP Client (e.g., Claude)

This MCP server includes a discovery endpoint that allows clients to dynamically discover the available endpoints and their parameters. To connect a client like Claude, you can point it to the `/mcp/endpoints` endpoint.

**Discovery Endpoint:** `GET /mcp/endpoints`

This will return a JSON object describing the available endpoints, which the client can use to configure itself.

**Example:**
```bash
curl http://localhost:5001/mcp/endpoints
```
