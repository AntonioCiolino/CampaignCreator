# Campaign Crafter MCP Server

This server provides a Model Context Protocol (MCP) interface for the Campaign Crafter API, allowing AI assistants like Claude and OpenAI to interact with the Campaign Crafter application.

## Features

- **Campaign Management**: Create, read, update, delete, and list campaigns
- **Character Management**: Create, read, update, delete, and list characters
- **Campaign Sections**: Create, read, update, delete, and list campaign sections
- **Character-Campaign Linking**: Link and unlink characters to/from campaigns
- **Generation Tools**: Generate table of contents and titles

## Setup

### Prerequisites

- Python 3.8 or higher
- Campaign Crafter API running on http://localhost:8000 (or configured URL)

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/campaign-crafter-mcp.git
   cd campaign-crafter-mcp
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your configuration:
   ```
   API_BASE_URL=http://127.0.0.1:8000
   MCP_SERVER_HOST=127.0.0.1
   MCP_SERVER_PORT=4000
   DEBUG=false
   ```

### Running the Server

Start the server with:

```bash
python main.py
```

Or use the provided start scripts:

```bash
# On Linux/macOS
./start.sh

# On Windows
start.bat
```

The server will be available at `http://127.0.0.1:4000/mcp/` (or your configured host/port).

## MCP Tools

The server provides the following MCP tools:

### Authentication

- `get_user_info`: Verify and return a valid authentication token

### Campaign Management

- `create_campaign`: Create a new campaign
- `get_campaign`: Get a specific campaign by ID
- `list_campaigns`: List all campaigns for the authenticated user
- `update_campaign`: Update a specific campaign
- `delete_campaign`: Delete a specific campaign

### Character Management

- `create_character`: Create a new character
- `get_character`: Get a specific character by ID
- `list_characters`: List all characters for the authenticated user
- `get_all_characters`: List all characters regardless of campaign
- `update_character`: Update a specific character
- `delete_character`: Delete a specific character

### Campaign Sections

- `create_campaign_section`: Create a new section for a campaign
- `list_campaign_sections`: List all sections for a campaign
- `get_campaign_section`: Get a specific section by ID
- `update_campaign_section`: Update a specific section
- `delete_campaign_section`: Delete a specific section

### Character-Campaign Linking

- `link_character_to_campaign`: Link a character to a campaign
- `unlink_character_from_campaign`: Unlink a character from a campaign

### Generation Tools

- `generate_toc`: Generate a table of contents for a campaign
- `generate_titles`: Generate titles for a campaign section

## Using with AI Assistants

### Claude

To use this MCP server with Claude, add it to your MCP configuration:

```json
{
  "mcpServers": {
    "campaign-crafter": {
      "command": "uvx",
      "args": ["campaign-crafter-mcp@latest"],
      "env": {
        "API_BASE_URL": "http://127.0.0.1:8000",
        "MCP_SERVER_HOST": "127.0.0.1",
        "MCP_SERVER_PORT": "4000"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

### OpenAI

To use this MCP server with OpenAI, follow their documentation for adding custom tools.

## Project Structure

```
mcp_server/
├── main.py                 # Entry point
├── requirements.txt        # Dependencies
├── .env                    # Environment variables (create this)
├── .env.example            # Example environment variables
├── README.md               # This file
├── start.sh                # Start script for Linux/macOS
├── start.bat               # Start script for Windows
├── src/                    # Source code
│   ├── models/             # Data models
│   │   └── schemas.py      # Pydantic models
│   ├── utils/              # Utilities
│   │   └── config.py       # Configuration utilities
│   └── server.py           # Server implementation with MCP tools
└── tests/                  # Tests
    ├── test_all_endpoints.py  # Comprehensive test
    ├── test_linking.py     # Character-campaign linking tests
    ├── test_rpc.py         # Basic RPC tests
    ├── test_sections.py    # Campaign section tests
    ├── test_titles.py      # Title generation tests
    └── test_toc.py         # TOC generation tests
```

## Testing

The `tests` directory contains test scripts for validating the MCP server functionality. These are live integration tests that interact with the actual Campaign Crafter API.

To run the tests:

```bash
python tests/test_all_endpoints.py
```

## Development

### Cleaning Cache Files

To clean up Python cache files, you can use the following commands:

```bash
# Remove __pycache__ directories
find . -name "__pycache__" -type d -not -path "*/venv/*" -exec rm -rf {} +

# Remove .pytest_cache directories
find . -name ".pytest_cache" -type d -exec rm -rf {} +

# Remove .pyc files
find . -name "*.pyc" -type f -not -path "*/venv/*" -exec rm -f {} +
```

A `.gitignore` file is included to prevent these cache files from being committed to the repository.

## License

[MIT License](LICENSE)