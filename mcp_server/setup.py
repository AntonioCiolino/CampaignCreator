#!/usr/bin/env python3
"""
Helper script to set up MCP configuration for Campaign Crafter
"""

import json
import os
import platform
import sys
from pathlib import Path

def get_claude_config_path():
    """Get the Claude Desktop config file path for this OS"""
    system = platform.system()
    
    if system == "Windows":
        return Path(os.environ["APPDATA"]) / "Claude" / "claude_desktop_config.json"
    elif system == "Darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    else:  # Linux
        return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"

def get_python_command():
    """Get the correct Python command for this system"""
    # Try to determine the right Python command
    try:
        import subprocess
        result = subprocess.run([sys.executable, "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            return sys.executable
    except:
        pass
    
    # Fallback
    return "python3" if platform.system() != "Windows" else "python"

def main():
    # Get the absolute path to the MCP script
    script_path = Path(__file__).parent / "main.py"
    if not script_path.exists():
        print(f"❌ MCP script not found at: {script_path}")
        print("Make sure main.py is in the same directory as this script.")
        return
    
    # Get config file path
    config_path = get_claude_config_path()
    
    # Create the configuration
    config = {
        "mcpServers": {
            "campaign-crafter": {
                "command": get_python_command(),
                "args": [str(script_path.absolute())],
                "env": {
                    "CAMPAIGN_CRAFTER_API_URL": "http://localhost:8000/api/v1",
                    "CAMPAIGN_CRAFTER_USERNAME": "your_username",
                    "CAMPAIGN_CRAFTER_PASSWORD": "your_password"
                }
            }
        }
    }
    
    # Create directory if it doesn't exist
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing config if it exists
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                existing_config = json.load(f)
            
            # Merge with existing config
            if "mcpServers" not in existing_config:
                existing_config["mcpServers"] = {}
            
            existing_config["mcpServers"]["campaign-crafter"] = config["mcpServers"]["campaign-crafter"]
            config = existing_config
            
        except json.JSONDecodeError:
            print(f"⚠️  Existing config file has invalid JSON. Creating new one.")
    
    # Write the configuration
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ MCP configuration written to: {config_path}")
    print(f"📁 Script path: {script_path.absolute()}")
    print(f"🐍 Python command: {get_python_command()}")
    print()
    print("📝 Next steps:")
    print("1. Edit the config file to add your actual username/password")
    print("2. Restart Claude Desktop")
    print("3. Test with: 'List my campaigns'")
    print()
    print(f"Config file contents:")
    print(json.dumps(config, indent=2))

if __name__ == "__main__":
    main()