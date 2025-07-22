@echo off
REM Start the Campaign Crafter MCP server

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Run the server
python main.py