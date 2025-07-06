import re
import math # For floor function
from typing import List, Optional, Dict
from app import orm_models, crud
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
            block_content = "\n".join(map(str, block_content))

        # Remove any leading/trailing whitespace for the initial check
        processed_content_for_check = block_content.strip()

        # Case-insensitive check for "Table of Contents:"
        if processed_content_for_check.lower().startswith("table of contents:"):
            # Perform a case-insensitive replacement of the line starting with "Table of Contents:"
            # with the Homebrewery TOC tag.
            temp_toc_content = re.sub(
                r"^\s*table of contents:.*",  # Match from start of line
                "{{toc,wide,frame,box}}",    # Replacement
                block_content,               # Operate on original block_content
                count=1,
                flags=re.IGNORECASE | re.MULTILINE
            )

            # Process list items on the content.
            lines_for_list_processing = temp_toc_content.splitlines() # Handles various newline types

            final_processed_lines = []
            is_toc_tag_line_processed_for_list = False

            for line in lines_for_list_processing:
                # Check if the current line IS the TOC tag we just inserted.
                if "{{toc,wide,frame,box}}" in line and not is_toc_tag_line_processed_for_list:
                    final_processed_lines.append(line)
                    is_toc_tag_line_processed_for_list = True
                    continue

                # Process for list items
                if line.strip().startswith(("* ", "- ", "+ ")):
                    cleaned_line = re.sub(r"^\s*[\*\-\+]\s*", "", line).strip()
                    if cleaned_line:
                        final_processed_lines.append(f"- {cleaned_line}")
                elif line.strip():
                    final_processed_lines.append(line)

            return "\n".join(final_processed_lines)

        # If not a TOC block, apply other generic formatting
        current_text_to_format = block_content.strip()

        current_text_to_format = re.sub(r"^(Chapter\s*\d+|Section\s*\d+):", r"## \1", current_text_to_format, flags=re.IGNORECASE | re.MULTILINE)
        headers_to_format = ["Background", "Introduction", "Overview", "Synopsis", "Adventure Hook"]
        for header in headers_to_format:
            current_text_to_format = re.sub(rf"^{header}:", rf"## {header}", current_text_to_format, flags=re.IGNORECASE | re.MULTILINE)

        return current_text_to_format

    def _calculate_modifier(self, stat_value: Optional[int]) -> str:
        if stat_value is None:
            stat_value = 10 # Default to 10 if None for modifier calculation
        modifier = math.floor((stat_value - 10) / 2)
        return f"+{modifier}" if modifier >= 0 else str(modifier)

    def _format_character_complex_block(self, character: orm_models.Character) -> str:
        """
        Formats a single character's details into a Homebrewery Complex NPC stat block,
        similar to the "Elara Brightshield" example.
        """
        output = [] # Using a list to join lines at the end

        character_name_or_default = character.name if character.name and character.name.strip() else "Unnamed Character"
        output.append(f"### {character_name_or_default}\n")

        # 1. Image (outside main stat block)
        if character.image_urls and len(character.image_urls) > 0:
            image_url = character.image_urls[0]
            alt_text = f"{character.name} image" if character.name and character.name.strip() else "Character image"
            output.append(f"![]({image_url}){{width:325px}}\n") # Elara example uses 325px

        # 2. {{note}} Block
        note_content = "GM Notes: Add relevant plot hooks or secret information here."
        if character.notes_for_llm and character.notes_for_llm.strip():
            note_content = character.notes_for_llm.strip()
        output.append(f"{{{{note\n{note_content}\n}}}}\n:") # Added colon as per Elara example after note

        # 3. Descriptive Text (Appearance, Personality/Background)
        if character.appearance_description and character.appearance_description.strip():
            output.append(f"{character.appearance_description.strip()}\n")
        if character.description and character.description.strip():
            output.append(f"{character.description.strip()}\n")

        # Add a separator if there was descriptive text before the monster block
        if (character.appearance_description and character.appearance_description.strip()) or \
           (character.description and character.description.strip()):
            output.append(":\n")


        # 4. {{monster,frame ...}} Block
        output.append("{{monster,frame") # Not wide, similar to Elara's main stat block

        name = character.name if character.name and character.name.strip() else "Unnamed Character"
        output.append(f"## {name}")
        output.append(f"*Medium humanoid, alignment placeholder*") # Placeholder
        output.append(f"**Class**: Class placeholder (e.g., Warrior, Mage)") # Placeholder
        output.append("___")
        output.append(f"**Armor Class** :: AC placeholder (e.g., 16 (breastplate))") # Placeholder
        output.append(f"**Hit Points** :: HP placeholder (e.g., 58 (9d8 + 18))") # Placeholder
        output.append(f"**Speed** :: 30 ft.") # Placeholder
        output.append("___")

        # Stats Table
        stats = character.stats if character.stats else {}
        str_val = stats.get('strength', 10)
        dex_val = stats.get('dexterity', 10)
        con_val = stats.get('constitution', 10)
        int_val = stats.get('intelligence', 10)
        wis_val = stats.get('wisdom', 10)
        cha_val = stats.get('charisma', 10)

        output.append("|  STR  |  DEX  |  CON  |  INT  |  WIS  |  CHA  |")
        output.append("|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|")
        output.append(
            f"|  {str_val} ({self._calculate_modifier(str_val)}) "
            f"| {dex_val} ({self._calculate_modifier(dex_val)}) "
            f"| {con_val} ({self._calculate_modifier(con_val)}) "
            f"| {int_val} ({self._calculate_modifier(int_val)}) "
            f"| {wis_val} ({self._calculate_modifier(wis_val)}) "
            f"| {cha_val} ({self._calculate_modifier(cha_val)}) |"
        )
        output.append("___")

        output.append(f"**Saving Throws** :: Saving Throws placeholder (e.g., Wis +5, Cha +6)") # Placeholder
        output.append(f"**Skills** :: Skills placeholder (e.g., Perception +5, Persuasion +6)") # Placeholder
        output.append(f"**Senses** :: passive Perception placeholder (e.g., 15)") # Placeholder
        output.append(f"**Languages** :: Languages placeholder (e.g., Common, Celestial)") # Placeholder
        output.append(f"**Challenge** :: Challenge placeholder (e.g., 1 (200 XP))") # Placeholder
        output.append("___") # Elara example has this before spellcasting

        # Spellcasting (Placeholder)
        output.append("### Spellcasting")
        output.append("Spellcasting placeholder. This character might have spellcasting abilities. Define spell save DC, attack bonus, and prepared spells here if applicable.")
        output.append(":")
        output.append("**1st Level (X slots):** Spell 1, Spell 2")
        output.append("**2nd Level (Y slots):** Spell 3, Spell 4")
        output.append("\n")

        # Actions (Placeholder)
        output.append("### Actions")
        output.append("***Multiattack.*** Action placeholder (e.g., The character makes two melee attacks.)")
        output.append(":")
        output.append("***Weapon Name.*** *Melee or Ranged Weapon Attack:* Attack bonus placeholder to hit, reach/range placeholder, one target. *Hit:* Damage placeholder (e.g., 7 (1d8 + 3) piercing damage).")
        output.append("\n")

        # Bonus Actions (Placeholder - simplified from Elara)
        output.append("### Bonus Actions")
        output.append("***Bonus Action Name.*** Description of bonus action placeholder.")
        output.append("\n")

        # Features and Traits (Placeholder - simplified from Elara)
        output.append("### Features and Traits")
        output.append("***Feature Name.*** Description of feature or trait placeholder.")
        output.append("\n")

        # Reactions (Placeholder - simplified from Elara)
        output.append("### Reactions")
        output.append("***Reaction Name.*** Description of reaction placeholder.")

        output.append("}}") # End monster block

        return "\n".join(output)

    def _format_character_simple_block(self, character: orm_models.Character) -> str:
        """
        Formats a single character's details into a Homebrewery Simple NPC stat block (Harlan-style).
        """
        output = []
        character_name_or_default = character.name if character.name and character.name.strip() else "Unnamed Character"

        output.append(f"### {character_name_or_default}\n")

        if character.image_urls and len(character.image_urls) > 0:
            image_url = character.image_urls[0]
            alt_text = f"{character_name_or_default} image"
            output.append(f"![{alt_text}]({image_url}){{width:100%}}\n")

        output.append("{{monster,frame")
        output.append(f"## {character_name_or_default}")
        output.append(f"*Medium humanoid, alignment placeholder*")
        output.append("___")
        output.append(f"**Armor Class** :: 10 (Natural Armor)") # Placeholder
        output.append(f"**Hit Points** :: 10 (2d8+2)") # Placeholder
        output.append(f"**Speed** :: 30 ft.") # Placeholder
        output.append("___")

        stats_data = character.stats if character.stats else {}
        str_val = stats_data.get('strength', 10)
        dex_val = stats_data.get('dexterity', 10)
        con_val = stats_data.get('constitution', 10)
        int_val = stats_data.get('intelligence', 10)
        wis_val = stats_data.get('wisdom', 10)
        cha_val = stats_data.get('charisma', 10)

        output.append("|  STR  |  DEX  |  CON  |  INT  |  WIS  |  CHA  |")
        output.append("|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|")
        output.append(
            f"|  {str_val} ({self._calculate_modifier(str_val)}) "
            f"| {dex_val} ({self._calculate_modifier(dex_val)}) "
            f"| {con_val} ({self._calculate_modifier(con_val)}) "
            f"| {int_val} ({self._calculate_modifier(int_val)}) "
            f"| {wis_val} ({self._calculate_modifier(wis_val)}) "
            f"| {cha_val} ({self._calculate_modifier(cha_val)}) |"
        )
        output.append("___")

        personality = "Personality placeholder."
        if character.description and character.description.strip():
            first_sentence_match = re.match(r"^([^.!?]+[.!?])", character.description.strip())
            if first_sentence_match:
                extracted_personality = first_sentence_match.group(1).strip()
                if len(extracted_personality) < 150:
                    personality = extracted_personality
            elif len(character.description.strip()) < 150:
                 personality = character.description.strip()
        output.append(f"**Personality:** {personality}")

        output.append("}}")
        return "\n".join(output)

    async def format_campaign_for_homebrewery(self, campaign: orm_models.Campaign, sections: List[orm_models.CampaignSection], db: Session, current_user: UserModel) -> str: # Added db, current_user and async
        page_image_url = "https://www.gmbinder.com/images/b7OT9E4.png"
        stain_images = [
            "https://www.gmbinder.com/images/86T8EZC.png", 
            "https://www.gmbinder.com/images/cblLsoB.png",
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

        if campaign.concept:
            homebrewery_content.append("## Campaign Overview\n") 
            homebrewery_content.append(f"{campaign.concept.strip()}\n")
        
        homebrewery_content.append("\\page\n")

        sections_summary = "\n".join([s.title for s in sections if s.title])
        freshly_generated_hb_toc_string: Optional[str] = None

        if sections_summary:
            try:
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
                        model=model_id_for_llm
                    )
                else:
                    print(f"ERROR EXPORT: Could not get LLM service for provider '{provider_name_for_llm}' or model '{campaign.selected_llm_id}' for campaign {campaign.id}")

            except (LLMServiceUnavailableError, LLMGenerationError) as e:
                print(f"ERROR EXPORT: LLM error generating Homebrewery TOC for campaign {campaign.id}: {e}")
            except Exception as e:
                print(f"ERROR EXPORT: Unexpected error generating Homebrewery TOC for campaign {campaign.id}: {type(e).__name__} - {e}")
        else:
            print(f"INFO EXPORT: No sections with titles found for campaign {campaign.id}, skipping Homebrewery TOC generation.")

        if freshly_generated_hb_toc_string:
            processed_toc = self.process_block(freshly_generated_hb_toc_string)
            homebrewery_content.append(f"{processed_toc.strip()}\n")
            homebrewery_content.append("\\page\n")

            hb_toc_object_to_save = {"markdown_string": freshly_generated_hb_toc_string}
            try:
                from app.models import CampaignUpdate
                campaign_update_payload = CampaignUpdate(homebrewery_toc=hb_toc_object_to_save)
                await crud.update_campaign(db=db, campaign_id=campaign.id, campaign_update=campaign_update_payload)
                print(f"INFO EXPORT: Attempted to save newly generated Homebrewery TOC to DB for campaign {campaign.id}")
            except Exception as e:
                print(f"ERROR EXPORT: Failed to save newly generated Homebrewery TOC to DB for campaign {campaign.id}: {type(e).__name__} - {e}")
        else:
            print(f"INFO EXPORT: No Homebrewery TOC was generated or appended for campaign {campaign.id}.")

        for section in sections: 
            if section.title:
                homebrewery_content.append(f"## {section.title.strip()}\n")
            
            if section.content:
                homebrewery_content.append(f"{section.content.strip()}\n") 
            
            homebrewery_content.append("\\page\n") 

        if campaign.characters:
            homebrewery_content.append("\\page\n")
            homebrewery_content.append("## Dramatis Personae\n")

            for character in campaign.characters:
                if character.export_format_preference == 'simple':
                    homebrewery_content.append(self._format_character_simple_block(character))
                else:
                    homebrewery_content.append(self._format_character_complex_block(character))

                homebrewery_content.append("\\page\n")

        if stain_images:
            for i, stain_url in enumerate(stain_images):
                if (i + 1) % 3 == 0 :
                    homebrewery_content.append(f"{{{{stain:{stain_url}}}}}\n") 

        # Back Cover
        back_cover = self.BACK_COVER_TEMPLATE
        back_cover = back_cover.replace("https://--backcover url image--", "https://via.placeholder.com/816x1056.png?text=Back+Cover+Background")
        back_cover = back_cover.replace("BACKCOVER ONE-LINER", "An Unforgettable Adventure Awaits!")
        back_cover = back_cover.replace("ADD A CAMPAIGN COMMENTARY BLOCK HERE", "Author's notes and commentary on the campaign.")
        homebrewery_content.append(back_cover)

        return "\n\n".join(homebrewery_content)
