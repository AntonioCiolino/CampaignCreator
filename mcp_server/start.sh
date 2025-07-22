#!/bin/bash
# Start the Campaign Crafter MCP server

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the server
python main.py