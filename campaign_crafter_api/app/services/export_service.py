import re
import json
from typing import List, Optional
from app import orm_models # Assuming orm_models.py contains Campaign and CampaignSection

class HomebreweryExportService:

    @staticmethod
    def process_block(block_content: Optional[str]) -> str:
        if block_content is None:
            return ""

        if isinstance(block_content, list):
            block_content = "\n".join(str(item) for item in block_content)
        elif isinstance(block_content, dict):
            block_content = json.dumps(block_content)
        
        # Remove any leading/trailing whitespace
        processed_content = block_content.strip()

        # Replace "Table of Contents:" with a Homebrewery TOC tag
        # This is specific to how TOC might be stored if it's a simple text block.
        if processed_content.strip().startswith("Table of Contents:"):
            processed_content = processed_content.replace("Table of Contents:", "{{toc,wide,frame,box}}", 1)
            # Further process list items if this is a TOC block
            lines = processed_content.split('\n')
            processed_lines = []
            for line in lines:
                if line.strip().startswith(("* ", "- ", "+ ")):
                    # Remove existing list marker, add Homebrewery list item format
                    cleaned_line = re.sub(r"^\s*[\*\-\+]\s*", "", line).strip()
                    processed_lines.append(f"- {cleaned_line}") 
                else:
                    processed_lines.append(line)
            processed_content = "\n".join(processed_lines)
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

        # Table of Contents
        # The campaign.homebrewery_toc field is expected to be a block of text that process_block can handle.
        # Users can manually create this, or it can be LLM-generated.
        if campaign.homebrewery_toc: # Use the new field name
            # process_block is designed for TOC-like structures.
            processed_toc = self.process_block(campaign.homebrewery_toc) # Use the new field name
            homebrewery_content.append(f"{processed_toc.strip()}\n")
            homebrewery_content.append("\\page\n") # Page break after TOC
        
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
