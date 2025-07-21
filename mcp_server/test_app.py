import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

MCP_SERVER_URL = f"http://localhost:{os.environ.get('PORT', 5001)}/mcp"
CAMPAIGN_CRAFTER_API_URL = "http://localhost:8000/api/v1"

# --- IMPORTANT ---
# The test credentials are now loaded from the .env file.
TEST_USERNAME = os.environ.get("TEST_USERNAME", "testuser")
TEST_PASSWORD = os.environ.get("TEST_PASSWORD", "testpassword")

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

def get_auth_token():
    """Gets an authentication token from the main API."""
    print("Getting auth token...")
    auth_data = {
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    }
    response = requests.post(f"{CAMPAIGN_CRAFTER_API_URL}/auth/token", data=auth_data)
    if response.status_code != 200:
        print("Failed to get auth token. Aborting test.")
        print_response(response)
        return None

    token_data = response.json()
    return token_data.get("access_token")


def main():
    """Main function to run the test application."""
    token = get_auth_token()
    if not token:
        return

    headers = {"Authorization": f"Bearer {token}"}

    # --- Create a new campaign ---
    print("Creating a new campaign...")
    campaign_data = {
        "title": "My Test Campaign",
        "description": "A campaign created for testing the MCP server.",
        "initial_user_prompt": "A dark fantasy world where the sun has been extinguished.",
        "skip_concept_generation": False,
    }
    response = requests.post(f"{MCP_SERVER_URL}/campaigns", json=campaign_data, headers=headers)
    print_response(response)
    campaign = response.json()
    campaign_id = campaign.get("id")

    if not campaign_id:
        print("Failed to create campaign. Aborting test.")
        return

    # --- Create a new character ---
    print("Creating a new character...")
    character_data = {
        "name": "Kaelen",
        "description": "A rogue with a mysterious past.",
        "appearance_description": "Tall and slender, with dark hair and a scar over his left eye.",
        "personality_description": "Witty and charming, but with a hint of sadness.",
        "background": "Grew up on the streets, fending for himself.",
        "notes_for_llm": "Kaelen is secretly a member of a royal family, but he doesn't know it yet.",
        "campaign_id": campaign_id
    }
    response = requests.post(f"{MCP_SERVER_URL}/characters", json=character_data, headers=headers)
    print_response(response)
    character = response.json()
    character_id = character.get("id")

    if not character_id:
        print("Failed to create character. Aborting test.")
        return

    # --- Link character to campaign ---
    print(f"Linking character {character_id} to campaign {campaign_id}...")
    response = requests.post(f"{MCP_SERVER_URL}/characters/{character_id}/campaigns/{campaign_id}", headers=headers)
    print_response(response)

    # --- Verify by getting the campaign and character ---
    print(f"Getting campaign {campaign_id}...")
    response = requests.get(f"{MCP_SERVER_URL}/campaigns/{campaign_id}", headers=headers)
    print_response(response)

    print(f"Getting character {character_id}...")
    response = requests.get(f"{MCP_SERVER_URL}/characters/{character_id}", headers=headers)
    print_response(response)

    # --- Create a new campaign section ---
    print(f"Creating a new section for campaign {campaign_id}...")
    section_data = {
        "title": "The Sunless Forest",
        "prompt": "Write a detailed description of a forest that has never seen the sun. Describe the flora and fauna that might live there.",
        "model_id_with_prefix": "openai/gpt-3.5-turbo",
        "type": "generic"
    }
    response = requests.post(f"{MCP_SERVER_URL}/campaigns/{campaign_id}/sections", json=section_data, headers=headers)
    print_response(response)
    section = response.json()
    section_id = section.get("id")

    if not section_id:
        print("Failed to create section. Aborting further tests.")
        return

    # --- Generate TOC for the campaign ---
    print(f"Generating TOC for campaign {campaign_id}...")
    toc_data = {
        "model_id_with_prefix": "openai/gpt-3.5-turbo",
        "prompt": "Generate a table of contents for a campaign about a sunless world."
    }
    response = requests.post(f"{MCP_SERVER_URL}/campaigns/{campaign_id}/toc", json=toc_data, headers=headers)
    print_response(response)
    toc = response.json()
    display_toc = toc.get("display_toc")

    if not display_toc:
        print("Failed to generate TOC. Aborting section creation test.")
        return

    # --- Create sections based on the TOC ---
    for i, item in enumerate(display_toc):
        title = item.get("title")
        if not title:
            continue

        print(f"Creating section: {title}")
        section_data = {
            "title": title,
            "prompt": f"Write a detailed description of {title} for a campaign about a sunless world.",
            "model_id_with_prefix": "openai/gpt-3.5-turbo",
            "type": item.get("type", "generic")
        }
        # Auto-populate every other section
        if i % 2 == 0:
            section_data["auto_populate"] = True

        response = requests.post(f"{MCP_SERVER_URL}/campaigns/{campaign_id}/sections", json=section_data, headers=headers)
        print_response(response)

    # --- Generate titles for the campaign ---
    print(f"Generating titles for campaign {campaign_id}...")
    titles_data = {
        "model_id_with_prefix": "openai/gpt-3.5-turbo",
        "prompt": "Generate a list of titles for a campaign about a sunless world."
    }
    response = requests.post(f"{MCP_SERVER_URL}/campaigns/{campaign_id}/titles", json=titles_data, headers=headers)
    print_response(response)
    titles = response.json().get("titles", [])

    if not titles:
        print("Failed to generate titles. Skipping title update.")
    else:
        # --- Pick a random title and update the campaign ---
        import random
        import re

        random_title = random.choice(titles)
        # Remove any leading numbers and special characters
        cleaned_title = re.sub(r"^\d+\.\s*", "", random_title)

        print(f"Updating campaign title to: {cleaned_title}")
        update_data = {"title": cleaned_title}
        response = requests.put(f"{MCP_SERVER_URL}/campaigns/{campaign_id}", json=update_data, headers=headers)
        print_response(response)


if __name__ == "__main__":
    main()
