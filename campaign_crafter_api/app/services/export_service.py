import re
from typing import List, Optional
from app import orm_models # Assuming orm_models.py contains Campaign and CampaignSection

class HomebreweryExportService:

    @staticmethod
    def process_block(block_content: Optional[str]) -> str:
        if block_content is None:
            return ""
        
        # Remove any leading/trailing whitespace
        processed_content = block_content.strip()

        # Replace "Table of Contents:" with a Homebrewery TOC tag
        if "Table of Contents:" in processed_content:
            processed_content = processed_content.replace("Table of Contents:", "{{toc,wide,frame,box}}")
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

        # Replace "Chapter X:" or "Section X:" with Markdown H2 headings
        processed_content = re.sub(r"^(Chapter\s*\d+|Section\s*\d+):", r"## \1", processed_content, flags=re.IGNORECASE)
        
        # Replace "Background:" or similar headers with Markdown H2 headings
        headers_to_format = ["Background", "Introduction", "Overview", "Synopsis", "Adventure Hook"] # Add more as needed
        for header in headers_to_format:
            processed_content = re.sub(rf"^{header}:", rf"## {header}", processed_content, flags=re.IGNORECASE)

        # Add other specific formatting rules from CampaignCreator.py if needed
        # For example, handling specific keywords or patterns for bolding, italics, etc.
        # This version focuses on TOC and headers.

        return processed_content

    def format_campaign_for_homebrewery(self, campaign: orm_models.Campaign, sections: List[orm_models.CampaignSection]) -> str:
        # Style and page setup (adapted from CampaignCreator.py)
        # TODO: Make these configurable in the future
        page_image_url = "https://www.gmbinder.com/images/b7OT9E4.png" # Example URL
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

        # Campaign Concept (under a generic header, or user can format within concept)
        if campaign.concept:
            homebrewery_content.append("## Campaign Overview\n") # Or "Introduction", "Synopsis" etc.
            homebrewery_content.append(f"{campaign.concept}\n")
        
        homebrewery_content.append("\\page\n") # New page for TOC or main content

        # Table of Contents
        if campaign.toc:
            processed_toc = self.process_block(campaign.toc)
            homebrewery_content.append(processed_toc) # process_block handles {{toc,...}}
            homebrewery_content.append("\n\\page\n") # New page after TOC
        
        # Main Content - Sections
        for section in sections: # Assumes sections are pre-ordered
            # Process section title (if exists) using similar logic to process_block headers
            if section.title:
                homebrewery_content.append(f"## {section.title}\n")
            
            # Process section content - can be simple or use process_block if more complex rules are needed
            # For now, appending content directly. If sections contain "Chapter X:" etc., process_block would be better.
            # processed_section_content = self.process_block(section.content) 
            processed_section_content = section.content # Assuming content is mostly ready
            homebrewery_content.append(f"{processed_section_content}\n")
            homebrewery_content.append("\\page\n") # Page break after each section

        # Add stains (randomly or sequentially, as in original script)
        # This is a simplified version; original might have more complex logic for placing stains
        for i, stain_url in enumerate(stain_images):
            if i % 2 == 0: # Example: alternate pages or some other logic
                 homebrewery_content.append(f"{{{{background-image: {stain_url}}}}}\n")
            else:
                 homebrewery_content.append(f"{{{{stain:{stain_url}}}}}\n")


        return "\n".join(homebrewery_content)
