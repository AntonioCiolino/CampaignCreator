import requests
import json

MCP_SERVER_URL = "http://localhost:5001/mcp"

def print_response(response):
    """Helper function to print response details."""
    print(f"Status Code: {response.status_code}")
    try:
        print("Response JSON:")
        print(json.dumps(response.json(), indent=2))
    except json.JSONDecodeError:
        print("Response Text:")
        print(response.text)
    print("-" * 20)

def main():
    """Main function to run the test application."""
    # --- Create a new user (for authentication) ---
    # In a real scenario, you would log in to get a token.
    # For this test, we assume the main API does not require authentication
    # or that the appropriate headers are passed through.

    # --- Create a new campaign ---
    print("Creating a new campaign...")
    campaign_data = {
        "name": "My Test Campaign",
        "description": "A campaign created for testing the MCP server."
    }
    response = requests.post(f"{MCP_SERVER_URL}/campaigns", json=campaign_data)
    print_response(response)
    campaign = response.json()
    campaign_id = campaign.get("id")

    if not campaign_id:
        print("Failed to create campaign. Aborting test.")
        return

    # --- Create a new character ---
    print("Creating a new character...")
    character_data = {
        "name": "Test Character",
        "description": "A character for our test campaign."
    }
    response = requests.post(f"{MCP_SERVER_URL}/characters", json=character_data)
    print_response(response)
    character = response.json()
    character_id = character.get("id")

    if not character_id:
        print("Failed to create character. Aborting test.")
        return

    # --- Link character to campaign ---
    print(f"Linking character {character_id} to campaign {campaign_id}...")
    response = requests.post(f"{MCP_SERVER_URL}/characters/{character_id}/campaigns/{campaign_id}")
    print_response(response)

    # --- Verify by getting the campaign and character ---
    print(f"Getting campaign {campaign_id}...")
    response = requests.get(f"{MCP_SERVER_URL}/campaigns/{campaign_id}")
    print_response(response)

    print(f"Getting character {character_id}...")
    response = requests.get(f"{MCP_SERVER_URL}/characters/{character_id}")
    print_response(response)

    # --- Create a new campaign section ---
    print(f"Creating a new section for campaign {campaign_id}...")
    section_data = {
        "title": "Test Section",
        "content": "This is a test section.",
        "prompt": "Write a short intro about a mysterious forest."
    }
    response = requests.post(f"{MCP_SERVER_URL}/campaigns/{campaign_id}/sections", json=section_data)
    print_response(response)
    section = response.json()
    section_id = section.get("id")

    if not section_id:
        print("Failed to create section. Aborting further tests.")
        return

    # --- Generate TOC for the campaign ---
    print(f"Generating TOC for campaign {campaign_id}...")
    response = requests.post(f"{MCP_SERVER_URL}/campaigns/{campaign_id}/toc", json={})
    print_response(response)

    # --- Generate titles for the campaign ---
    print(f"Generating titles for campaign {campaign_id}...")
    response = requests.post(f"{MCP_SERVER_URL}/campaigns/{campaign_id}/titles", json={})
    print_response(response)


if __name__ == "__main__":
    main()
