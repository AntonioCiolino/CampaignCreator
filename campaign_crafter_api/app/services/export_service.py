import re
from typing import List, Optional, Dict # Added Dict
from app import orm_models, crud # Assuming orm_models.py contains Campaign and CampaignSection, added crud
from app.services.llm_factory import get_llm_service
from app.services.llm_service import LLMServiceUnavailableError, LLMGenerationError
from sqlalchemy.orm import Session
from app.models import User as UserModel # For current_user type hint

class HomebreweryExportService:
    FRONT_COVER_TEMPLATE = """{{frontCover}}

{{logo ![](/assets/naturalCritLogoRed.svg)}}

# TITLE
## SUBTITLE
___

{{banner BANNER_TEXT}}

{{footnote
 EPISODE_INFO
}}

![background image](https://onedrive.live.com/embed?resid=387fb00e5a1e24c8%2152521&authkey=%21APkOXzEAywQMAwA){position:absolute,bottom:0,left:0,width:100%}
\page"""

    BACK_COVER_TEMPLATE = """\\page
{{backCover}}

#

![background image](https://--backcover url image--){position:absolute,bottom:0,left:0,height:100%}


# BACKCOVER ONE-LINER

---

ADD A CAMPAIGN COMMENTARY BLOCK HERE

---

{{logo
![](/assets/naturalCritLogoWhite.svg)

VTCNP Enterprises
}}"""

    @staticmethod
    def process_block(block_content: Optional[str]) -> str:
        if block_content is None:
            return ""
        
        # If block_content is a list, join its elements into a single string
        if isinstance(block_content, list):
            block_content = "\n".join(map(str, block_content)) # Ensure all elements are strings

        # Remove any leading/trailing whitespace
        processed_content = block_content.strip()

        # Replace "Table of Contents:" with a Homebrewery TOC tag
        # This is specific to how TOC might be stored if it's a simple text block.
        if processed_content.strip().startswith("Table of Contents:"):
            processed_content = processed_content.replace("Table of Contents:", "{{toc,wide,frame,box}}", 1)
            # Further process list items if this is a TOC block
            lines = processed_content.split('\n') # Use escaped newline
            processed_lines = []
            for line in lines:
                if line.strip().startswith(("* ", "- ", "+ ")):
                    # Remove existing list marker, add Homebrewery list item format
                    cleaned_line = re.sub(r"^\s*[\*\-\+]\s*", "", line).strip()
                    processed_lines.append(f"- {cleaned_line}") 
                else:
                    processed_lines.append(line)
            processed_content = "\n".join(processed_lines) # Use escaped newline
            return processed_content # Return early as TOC block is special

        # Replace "Chapter X:" or "Section X:" at the start of a line with Markdown H2 headings
        # This is primarily for content that might be structured this way within the TOC block.
        processed_content = re.sub(r"^(Chapter\s*\d+|Section\s*\d+):", r"## \1", processed_content, flags=re.IGNORECASE | re.MULTILINE)
        
        # Replace "Background:" or similar headers at the start of a line with Markdown H2 headings
        # Also primarily for content within the TOC block if it includes such headers.
        headers_to_format = ["Background", "Introduction", "Overview", "Synopsis", "Adventure Hook"] # Add more as needed
        for header in headers_to_format:
            processed_content = re.sub(rf"^{header}:", rf"## {header}", processed_content, flags=re.IGNORECASE | re.MULTILINE)

        # Note: This process_block is mostly for basic formatting of a dedicated TOC block.
        # It's not intended for deep processing of general Markdown or complex section content.
        return processed_content

    def _format_character_for_export(self, character: orm_models.Character) -> str:
        """
        Formats a single character's details into a Markdown string for Homebrewery export.
        """
        char_parts = []
        char_parts.append(f"### {character.name}\n")

        # Accessing stats via the .stats property of the ORM model
        stats = character.stats
        if stats:
            stat_list = []
            for key, value in stats.items():
                if value is not None: # Only include stats that have a value
                    stat_list.append(f"- **{key.capitalize()}**: {value}")
            if stat_list:
                char_parts.append("**Stats:**\n" + "\n".join(stat_list) + "\n")

        if character.appearance_description and character.appearance_description.strip():
            char_parts.append(f"**Appearance:** {character.appearance_description.strip()}\n")

        if character.description and character.description.strip():
            char_parts.append(f"**Description:** {character.description.strip()}\n")

        # Add image if available - basic implementation, just lists URL
        # TODO: Future enhancement could be to format as `![alt text](url)` if appropriate
        # For now, just listing the first image URL if present.
        if character.image_urls and len(character.image_urls) > 0:
            char_parts.append(f"**Image:** {character.image_urls[0]}\n")

        return "\n".join(char_parts)

    async def format_campaign_for_homebrewery(self, campaign: orm_models.Campaign, sections: List[orm_models.CampaignSection], db: Session, current_user: UserModel) -> str: # Added db, current_user and async
        # TODO: Make page_image_url and stain_images configurable in the future, perhaps via campaign settings or user profile.
        page_image_url = "https://www.gmbinder.com/images/b7OT9E4.png" # Example URL for title page background
        stain_images = [
            "https://www.gmbinder.com/images/86T8EZC.png", 
            "https://www.gmbinder.com/images/cblLsoB.png",
            # Add more stain images if available in original script
        ]
        
        homebrewery_content = []

        # Front Cover
        front_cover = self.FRONT_COVER_TEMPLATE
        front_cover = front_cover.replace("TITLE", campaign.title if campaign.title else "Untitled Campaign")
        front_cover = front_cover.replace("SUBTITLE", "A Campaign Adventure")
        front_cover = front_cover.replace("BANNER_TEXT", "Exciting Banner Text!")
        front_cover = front_cover.replace("EPISODE_INFO", "Author to provide episode details here.")
        front_cover = front_cover.replace("https://onedrive.live.com/embed?resid=387fb00e5a1e24c8%2152521&authkey=%21APkOXzEAywQMAwA", "https://via.placeholder.com/816x1056.png?text=Front+Cover+Background")
        homebrewery_content.append(front_cover)

        # Title page style
        homebrewery_content.append("<style>")
        homebrewery_content.append("  .phb#p1{ text-align:center; }")
        homebrewery_content.append("  .phb#p1:after{ display:none; }")
        homebrewery_content.append("</style>\n")

        # Title
        homebrewery_content.append(f"# {campaign.title if campaign.title else 'Untitled Campaign'}\n")

        # Campaign Concept
        # Users should use Markdown within their concept. Homebrewery markers like \page or \column are also allowed.
        if campaign.concept:
            homebrewery_content.append("## Campaign Overview\n") 
            homebrewery_content.append(f"{campaign.concept.strip()}\n") # Strip to remove leading/trailing whitespace from the concept itself
        
        homebrewery_content.append("\\page\n") # Page break after concept/title page

        # Table of Contents - New Generation Logic
        sections_summary = "\n".join([s.title for s in sections if s.title])
        freshly_generated_hb_toc_string: Optional[str] = None

        if sections_summary: # Only attempt to generate if there are sections
            try:
                # Determine provider and model_id from campaign.selected_llm_id
                provider_name_for_llm = None
                model_id_for_llm = campaign.selected_llm_id
                if campaign.selected_llm_id and '/' in campaign.selected_llm_id:
                    provider_name_for_llm, model_id_for_llm = campaign.selected_llm_id.split('/', 1)

                llm_service = get_llm_service(
                    provider_name=provider_name_for_llm,
                    model_id_with_prefix=campaign.selected_llm_id
                )
                if llm_service:
                    print(f"INFO EXPORT: Generating Homebrewery TOC for campaign {campaign.id} using model {campaign.selected_llm_id}")
                    freshly_generated_hb_toc_string = await llm_service.generate_homebrewery_toc_from_sections(
                        sections_summary=sections_summary,
                        db=db,
                        current_user=current_user,
                        model=model_id_for_llm # Pass only the model part if provider was split
                    )
                else:
                    print(f"ERROR EXPORT: Could not get LLM service for provider '{provider_name_for_llm}' or model '{campaign.selected_llm_id}' for campaign {campaign.id}")

            except (LLMServiceUnavailableError, LLMGenerationError) as e:
                print(f"ERROR EXPORT: LLM error generating Homebrewery TOC for campaign {campaign.id}: {e}")
            except Exception as e: # Catch any other unexpected errors
                print(f"ERROR EXPORT: Unexpected error generating Homebrewery TOC for campaign {campaign.id}: {type(e).__name__} - {e}")
        else:
            print(f"INFO EXPORT: No sections with titles found for campaign {campaign.id}, skipping Homebrewery TOC generation.")

        if freshly_generated_hb_toc_string:
            processed_toc = self.process_block(freshly_generated_hb_toc_string)
            homebrewery_content.append(f"{processed_toc.strip()}\n")
            homebrewery_content.append("\\page\n") # Page break after TOC

            # Save the newly generated TOC back to the database
            hb_toc_object_to_save = {"markdown_string": freshly_generated_hb_toc_string}
            try:
                # This assumes crud.update_campaign_homebrewery_toc will be created/adapted
                # to handle updating only this field.
                # For now, we'll use a more general update and rely on Pydantic model validation for structure.
                # This might be problematic if campaign.homebrewery_toc is not Optional[Dict[str,str]] in CampaignUpdate model.
                # Let's assume a specific CRUD function or that CampaignUpdate model is correctly structured for this.

                # Placeholder for actual CRUD call, as it needs specific design
                # For this subtask, we are focusing on the service logic.
                # A direct call to crud.update_campaign might be too broad if we only want to update the TOC.
                # We will assume a more targeted (hypothetical) CRUD function for now:
                # crud.update_campaign_homebrewery_toc(db=db, campaign_id=campaign.id, homebrewery_toc_content=hb_toc_object_to_save)

                # To make this runnable without a new CRUD method yet, we can try to update using existing CampaignUpdate
                # This requires CampaignUpdate Pydantic model to accept homebrewery_toc as Dict[str, str]
                from app.models import CampaignUpdate # Local import for this block
                campaign_update_payload = CampaignUpdate(homebrewery_toc=hb_toc_object_to_save)
                await crud.update_campaign(db=db, campaign_id=campaign.id, campaign_update=campaign_update_payload)
                print(f"INFO EXPORT: Attempted to save newly generated Homebrewery TOC to DB for campaign {campaign.id}")
            except Exception as e:
                print(f"ERROR EXPORT: Failed to save newly generated Homebrewery TOC to DB for campaign {campaign.id}: {type(e).__name__} - {e}")
        else:
            print(f"INFO EXPORT: No Homebrewery TOC was generated or appended for campaign {campaign.id}.")

        # Main Content - Sections
        # Sections are iterated in their given order.
        # Users should use Markdown for formatting within section content.
        # Homebrewery-specific markers like \page and \column within section.content will be passed through
        # and should be interpreted by Homebrewery.
        for section in sections: 
            if section.title:
                homebrewery_content.append(f"## {section.title.strip()}\n")
            
            if section.content:
                # Append section content directly. Homebrewery will parse its Markdown.
                # Ensure content ends with a newline for separation, but strip existing trailing whitespace from content.
                homebrewery_content.append(f"{section.content.strip()}\n") 
            
            # Add a Homebrewery page break after each section.
            # If users include \page within their section content for finer control, that will also take effect.
            homebrewery_content.append("\\page\n") 

        # Character Appendix Section (Dramatis Personae)
        if campaign.characters: # Check if there are any characters linked to the campaign
            homebrewery_content.append("\\page\n") # Start characters on a new page
            homebrewery_content.append("## Dramatis Personae\n")
            for character in campaign.characters:
                homebrewery_content.append(self._format_character_for_export(character))
                homebrewery_content.append("\n") # Add a little space between characters
            homebrewery_content.append("\\page\n") # Page break after the character appendix

        # Add decorative stains (example implementation)
        # This part can be made more sophisticated, e.g., user-selectable stains, random placement, etc.
        if stain_images: # Only add stains if configured
            for i, stain_url in enumerate(stain_images):
                # Simple logic: add a stain every few pages, or specific pages.
                # This example adds them somewhat arbitrarily.
                if (i + 1) % 3 == 0 : # Example: on 3rd, 6th, etc. "page" (logical block here)
                    homebrewery_content.append(f"{{{{stain:{stain_url}}}}}\n") 
                # Could also use background-image for full page stains on certain pages:
                # elif (i + 1) % 5 == 0:
                #     homebrewery_content.append(f"{{{{background-image: {stain_url}}}}}\n")

        # Back Cover
        back_cover = self.BACK_COVER_TEMPLATE
        back_cover = back_cover.replace("https://--backcover url image--", "https://via.placeholder.com/816x1056.png?text=Back+Cover+Background")
        back_cover = back_cover.replace("BACKCOVER ONE-LINER", "An Unforgettable Adventure Awaits!")
        back_cover = back_cover.replace("ADD A CAMPAIGN COMMENTARY BLOCK HERE", "Author's notes and commentary on the campaign.")
        homebrewery_content.append(back_cover)

        return "\n\n".join(homebrewery_content) # Use double newline to ensure separation of major blocks
