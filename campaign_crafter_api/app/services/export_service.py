import json # re is no longer used in this file
from typing import List, Optional
from app import orm_models # Assuming orm_models.py contains Campaign and CampaignSection

class HomebreweryExportService:

    @staticmethod
    def process_block(block_content: Optional[str]) -> str:
        if block_content is None:
            return ""

        if isinstance(block_content, list):
            if block_content and isinstance(block_content[0], dict):
                # It's a list of dictionaries, extract titles
                processed_titles = []
                for item in block_content:
                    if isinstance(item, dict):
                        processed_titles.append(str(item.get('title', '')))
                    else:
                        # Handle unexpected non-dict items in a list of dicts
                        processed_titles.append(str(item))
                block_content = "\n".join(processed_titles)
            else:
                # It's a list of something else (e.g., strings), join them directly
                block_content = "\n".join(str(item) for item in block_content)
        elif isinstance(block_content, dict):
            block_content = json.dumps(block_content)
        
        # At this point, block_content should be a string.
        # Convert to string just in case it's some other scalar type (e.g. int, float)
        if not isinstance(block_content, str):
            block_content = str(block_content)

        # Define known Homebrewery opening tags/patterns
        known_patterns = [
            '{{toc', '{{style', '{{cover', '{{frontCover',
            '{{note', '{{descriptive', '{{wide', '{{monster',
            '<style', '{{columnBreak', '{{pageNumber', '\\page'
            # Added more common patterns like columnBreak, pageNumber, and \page itself
        ]

        stripped_content = block_content.strip()

        # Check if the content starts with any known Homebrewery patterns
        is_known_block = False
        for pattern in known_patterns:
            if stripped_content.startswith(pattern):
                is_known_block = True
                break

        if is_known_block:
            # If it's a known Homebrewery block, return it stripped, but otherwise as-is.
            return stripped_content
        else:
            # For any other content, just return it stripped.
            # All previous regex replacements for lists, chapters, etc., are removed.
            return stripped_content

    def format_campaign_for_homebrewery(self, campaign: orm_models.Campaign, sections: List[orm_models.CampaignSection]) -> str:
        # TODO: Make page_image_url and stain_images configurable in the future, perhaps via campaign settings or user profile.
        page_image_url = "https://www.gmbinder.com/images/b7OT9E4.png" # Example URL for title page background
        stain_images = [
            "https://www.gmbinder.com/images/86T8EZC.png", 
            "https://www.gmbinder.com/images/cblLsoB.png",
            # Add more stain images if available in original script
        ]
        
        homebrewery_content = []

        # Title page style
        homebrewery_content.append("<style>")
        homebrewery_content.append("  .phb#p1{ text-align:center; }")
        homebrewery_content.append("  .phb#p1:after{ display:none; }")
        homebrewery_content.append("</style>\n")
        homebrewery_content.append(f"![background]({page_image_url})\n") # Background image for title page

        # Title
        homebrewery_content.append(f"# {campaign.title if campaign.title else 'Untitled Campaign'}\n")

        # Campaign Concept
        # Users should use Markdown within their concept. Homebrewery markers like \page or \column are also allowed.
        if campaign.concept:
            homebrewery_content.append("## Campaign Overview\n") 
            homebrewery_content.append(f"{campaign.concept.strip()}\n") # Strip to remove leading/trailing whitespace from the concept itself
        
        homebrewery_content.append("\\page\n") # Page break after concept/title page
        homebrewery_content.append("{{pageNumber,auto}}\n")

        # Table of Contents
        # The campaign.homebrewery_toc field is expected to be a block of text that process_block can handle.
        # Users can manually create this, or it can be LLM-generated.
        if campaign.homebrewery_toc: # Use the new field name
            # process_block is designed for TOC-like structures.
            processed_toc = self.process_block(campaign.homebrewery_toc) # Use the new field name
            homebrewery_content.append(f"{processed_toc.strip()}\n")
            homebrewery_content.append("\\page\n") # Page break after TOC
            homebrewery_content.append("{{pageNumber,auto}}\n")
        
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
            homebrewery_content.append("{{pageNumber,auto}}\n")

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

        return "\n\n".join(homebrewery_content) # Use double newline to ensure separation of major blocks
