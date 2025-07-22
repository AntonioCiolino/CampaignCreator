#!/usr/bin/env python3
"""
Setup script for the Campaign Crafter MCP server.
"""
import os
import sys
import shutil
from pathlib import Path


def setup():
    """Set up the Campaign Crafter MCP server."""
    print("Setting up Campaign Crafter MCP server...")
    
    # Create .env file if it doesn't exist
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        print("Creating .env file from .env.example...")
        shutil.copy(env_example, env_file)
        print("Created .env file. Please edit it with your configuration.")
    
    # Check if Python version is compatible
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("Error: Python 3.8 or higher is required.")
        sys.exit(1)
    
    # Check if virtual environment is active
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("Warning: It's recommended to run this script in a virtual environment.")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Setup aborted.")
            sys.exit(0)
    
    # Install dependencies
    print("Installing dependencies...")
    os.system(f"{sys.executable} -m pip install -r requirements.txt")
    
    print("\nSetup complete! You can now run the server with:")
    print("python main.py")


if __name__ == "__main__":
    setup()