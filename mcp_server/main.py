from fastmcpsdk.server import MCPServer
from fastmcpsdk.methods import (
    create_campaign,
    get_campaign,
    update_campaign,
    delete_campaign,
    create_character,
    get_character,
    update_character,
    delete_character,
    link_character_to_campaign,
    unlink_character_from_campaign,
    create_campaign_section,
    list_campaign_sections,
    update_campaign_section,
    delete_campaign_section,
    generate_toc,
    generate_titles,
)
import os
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    server = MCPServer(
        mcp_server_url=os.environ.get("MCP_SERVER_URL", "http://localhost:5001"),
        campaign_crafter_url=os.environ.get("CAMPAIGN_CRAFTER_API_URL", "http://localhost:8000/api/v1"),
        campaign_crafter_username=os.environ.get("CAMPAIGN_CRAFTER_USERNAME"),
        campaign_crafter_password=os.environ.get("CAMPAIGN_CRAFTER_PASSWORD"),
    )

    server.add_methods([
        create_campaign,
        get_campaign,
        update_campaign,
        delete_campaign,
        create_character,
        get_character,
        update_character,
        delete_character,
        link_character_to_campaign,
        unlink_character_from_campaign,
        create_campaign_section,
        list_campaign_sections,
        update_campaign_section,
        delete_campaign_section,
        generate_toc,
        generate_titles,
    ])

    server.run()
