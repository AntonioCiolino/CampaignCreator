from typing import Optional, List, Dict
from pydantic import BaseModel, HttpUrl # Added HttpUrl
from datetime import datetime # Added datetime

# Removed ImageData model

class LLMConfigBase(BaseModel):
    name: str
    api_key: Optional[str] = None
    api_url: Optional[str] = None

class LLMConfigCreate(LLMConfigBase):
    pass

class LLMConfig(LLMConfigBase):
    id: int
    owner_id: int # foreign key to User, will be added later

    class Config:
        from_attributes = True

class CampaignTitlesResponse(BaseModel):
    titles: List[str]

class CampaignSectionCreateInput(BaseModel):
    title: Optional[str] = None  # User can suggest a title for the section
    prompt: Optional[str] = None # User can provide a specific prompt/starting sentence for the section content
    model_id_with_prefix: Optional[str] = None # Changed field name
    type: Optional[str] = None   # New field for specifying section type on creation
    # 'order' will be determined by the backend or could be optionally suggested

class LLMGenerationRequest(BaseModel):
    prompt: str
    model_id_with_prefix: Optional[str] = None
    temperature: Optional[float] = 0.7  # Defaulting as per llm_service.py abstract method
    max_tokens: Optional[int] = 500     # Defaulting as per llm_service.py abstract method

class CampaignSectionUpdateInput(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    order: Optional[int] = None # Optional: allow reordering
    type: Optional[str] = None # New field
    # Removed images field

class CampaignFullContentResponse(BaseModel):
    campaign_id: int
    title: Optional[str] # Title of the campaign
    full_content: str

class ModelInfo(BaseModel):
    id: str
    name: str
    model_type: str = "chat"  # Added model_type, defaulting to "chat"
    supports_temperature: bool = True  # Added supports_temperature, defaulting to True
    capabilities: List[str] = [] # Default changed to an empty list
    # Potentially add other fields like 'description' or 'type' in the future

class ModelListResponse(BaseModel):
    models: List[ModelInfo]

class CampaignSectionBase(BaseModel):
    title: Optional[str] = None
    content: str
    order: int # To maintain section order
    type: Optional[str] = None # New field

class CampaignSectionCreate(CampaignSectionBase):
    pass

class CampaignSection(CampaignSectionBase):
    id: int
    campaign_id: int # foreign key to Campaign
    # Removed images field

    class Config:
        from_attributes = True

class CampaignSectionListResponse(BaseModel):
    sections: List[CampaignSection] # Reuses the existing CampaignSection model

class RandomItemResponse(BaseModel):
    table_name: str
    item: Optional[str]

class TableNameListResponse(BaseModel):
    table_names: List[str]

class CampaignBase(BaseModel):
    title: str
    initial_user_prompt: Optional[str] = None
    badge_image_url: Optional[str] = None
    thematic_image_url: Optional[str] = None
    thematic_image_prompt: Optional[str] = None
    selected_llm_id: Optional[str] = None
    temperature: Optional[float] = None

    # New Theme Properties
    theme_primary_color: Optional[str] = None
    theme_secondary_color: Optional[str] = None
    theme_background_color: Optional[str] = None
    theme_text_color: Optional[str] = None
    theme_font_family: Optional[str] = None
    theme_background_image_url: Optional[str] = None
    theme_background_image_opacity: Optional[float] = None

    # New field for Mood Board
    mood_board_image_urls: Optional[List[str]] = None

class CampaignCreate(CampaignBase):
    initial_user_prompt: Optional[str] = None # Already in CampaignBase, ensuring it's seen as optional here too
    model_id_with_prefix_for_concept: Optional[str] = None
    skip_concept_generation: Optional[bool] = False # New field

class Campaign(CampaignBase):
    id: int
    owner_id: int # In a real app, this would be properly linked
    concept: Optional[str] = None # LLM-generated campaign overview
    homebrewery_toc: Optional[List[Dict[str, str]]] = None # NEW - To accept {"markdown_string": "..."}
    display_toc: Optional[List[Dict[str, str]]] = None # Should already be like this
    homebrewery_export: Optional[str] = None # Stores the homebrewery export
    sections: List['CampaignSection'] = [] # Assuming CampaignSection is defined elsewhere or properly forward referenced

    class Config:
        from_attributes = True

# Note: The duplicate CampaignSectionBase and CampaignSection definitions were removed.
# The first definitions encountered in the file are kept:
# class CampaignSectionBase(BaseModel):
#     title: Optional[str] = None
#     content: str
#     order: int # To maintain section order
#
# class CampaignSectionCreate(CampaignSectionBase):
#     pass
#
# class CampaignSection(CampaignSectionBase):
#     id: int
#     campaign_id: int # foreign key to Campaign
#
#     class Config:
#         orm_mode = True

class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str
    is_superuser: bool = False


class UserUpdate(BaseModel): # Changed from inheriting UserBase
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    disabled: Optional[bool] = None
    is_superuser: Optional[bool] = None
    sd_engine_preference: Optional[str] = None
    avatar_url: Optional[str] = None # New field for avatar URL

class CampaignUpdate(BaseModel): # Assuming CampaignUpdate is for PATCH, all fields optional
    title: Optional[str] = None
    initial_user_prompt: Optional[str] = None
    concept: Optional[str] = None
    homebrewery_toc: Optional[List[Dict[str, str]]] = None # NEW - To accept {"markdown_string": "..."}
    display_toc: Optional[List[Dict[str, str]]] = None # New field for display TOC
    homebrewery_export: Optional[str] = None
    badge_image_url: Optional[str] = None
    thematic_image_url: Optional[str] = None
    thematic_image_prompt: Optional[str] = None
    selected_llm_id: Optional[str] = None # Ensure it's part of CampaignUpdate for PATCH
    temperature: Optional[float] = None   # Ensure it's part of CampaignUpdate for PATCH

    # New Theme Properties (all optional)
    theme_primary_color: Optional[str] = None
    theme_secondary_color: Optional[str] = None
    theme_background_color: Optional[str] = None
    theme_text_color: Optional[str] = None
    theme_font_family: Optional[str] = None
    theme_background_image_url: Optional[str] = None
    theme_background_image_opacity: Optional[float] = None

    # New field for Mood Board (optional)
    mood_board_image_urls: Optional[List[str]] = None

# UserUpdate is now defined above CampaignUpdate

class User(UserBase): # For responses
    id: int
    disabled: bool
    is_superuser: bool
    openai_api_key_provided: Optional[bool] = None
    sd_api_key_provided: Optional[bool] = None
    sd_engine_preference: Optional[str] = None
    gemini_api_key_provided: Optional[bool] = None
    other_llm_api_key_provided: Optional[bool] = None
    avatar_url: Optional[str] = None # New field for avatar URL

    campaigns: List[Campaign] = []
    llm_configs: List[LLMConfig] = []

    class Config:
        from_attributes = True

class UserAPIKeyUpdate(BaseModel):
    openai_api_key: Optional[str] = None
    sd_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    other_llm_api_key: Optional[str] = None

# Feature Models
class FeatureBase(BaseModel):
    name: str
    template: str
    user_id: Optional[int] = None

class FeatureCreate(FeatureBase):
    pass

class FeatureUpdate(FeatureBase):
    name: Optional[str] = None
    template: Optional[str] = None

class Feature(FeatureBase):
    id: int

    class Config:
        from_attributes = True

# RollTableItem Models
class RollTableItemBase(BaseModel):
    min_roll: int
    max_roll: int
    description: str

class RollTableItemCreate(RollTableItemBase):
    pass

class RollTableItemUpdate(RollTableItemBase):
    min_roll: Optional[int] = None
    max_roll: Optional[int] = None
    description: Optional[str] = None

class RollTableItem(RollTableItemBase):
    id: int
    roll_table_id: int

    class Config:
        from_attributes = True

# RollTable Models
class RollTableBase(BaseModel):
    name: str
    description: Optional[str] = None
    user_id: Optional[int] = None

class RollTableCreate(RollTableBase):
    items: List[RollTableItemCreate]

class RollTableUpdate(RollTableBase):
    name: Optional[str] = None
    description: Optional[str] = None
    items: Optional[List[RollTableItemCreate]] = None

class RollTable(RollTableBase):
    id: int
    items: List[RollTableItem] = []
    user_id: Optional[int] = None

    class Config:
        from_attributes = True


# Pydantic model for representing file metadata from Azure Blob Storage
class BlobFileMetadata(BaseModel):
    name: str # This will store the base filename, e.g., "image.png"
    blob_name: str # This will store the full path in blob storage, e.g., "user_uploads/.../image.png"
    url: HttpUrl
    size: int  # Size in bytes
    last_modified: datetime
    content_type: Optional[str] = None

    class Config:
        from_attributes = True # Changed from orm_mode, as from_attributes is the Pydantic v2 equivalent for ORM compatibility

class LLMTextGenerationResponse(BaseModel):
    text: str  # Placeholder field; add more fields as needed

class FeaturePromptItem(BaseModel):
    name: str
    template: str

class FeaturePromptListResponse(BaseModel):
    features: List[FeaturePromptItem]

# Input model for regenerating a section
class SectionRegenerateInput(BaseModel):
    new_prompt: Optional[str] = None
    new_title: Optional[str] = None
    section_type: Optional[str] = None # E.g., "NPC", "Location", "Chapter/Quest", "Generic"
    model_id_with_prefix: Optional[str] = None


# Token models for authentication
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Character Models

class CharacterStats(BaseModel):
    strength: Optional[int] = 10
    dexterity: Optional[int] = 10
    constitution: Optional[int] = 10
    intelligence: Optional[int] = 10
    wisdom: Optional[int] = 10
    charisma: Optional[int] = 10

class CharacterBase(BaseModel):
    name: str
    description: Optional[str] = None
    appearance_description: Optional[str] = None
    image_urls: Optional[List[str]] = None
    video_clip_urls: Optional[List[str]] = None
    notes_for_llm: Optional[str] = None
    stats: Optional[CharacterStats] = None # Embed stats here

class CharacterCreate(CharacterBase):
    pass # All fields from CharacterBase are used for creation, stats can be provided optionally

class CharacterUpdate(BaseModel): # Separate model for updates
    name: Optional[str] = None
    description: Optional[str] = None
    appearance_description: Optional[str] = None
    image_urls: Optional[List[str]] = None
    video_clip_urls: Optional[List[str]] = None
    notes_for_llm: Optional[str] = None
    stats: Optional[CharacterStats] = None

class Character(CharacterBase):
    id: int
    owner_id: int
    # Campaigns will be a list of Campaign models, but handled via relationship in ORM
    # and potentially a separate response model if detailed campaign info is needed directly.

    class Config:
        from_attributes = True

class CharacterCampaignLink(BaseModel): # For linking/unlinking, might not be needed if using path params
    character_id: int
    campaign_id: int

# Update Campaign model to potentially include characters
# This might be done via a separate response model or by adding List[Character] to Campaign model
# For now, let's assume Character responses will list their campaigns if needed,
# and Campaign responses might list their characters.

# For Character Image Generation
class CharacterImageGenerationRequest(BaseModel):
    additional_prompt_details: Optional[str] = None
    model_name: Optional[str] = None  # Corresponds to ImageModelName: "dall-e", "stable-diffusion", "gemini"
    size: Optional[str] = None
    # Add other relevant params from ImageGenerationParams if needed, e.g., quality, steps, cfg_scale
    quality: Optional[str] = None # For DALL-E
    steps: Optional[int] = None # For Stable Diffusion
    cfg_scale: Optional[float] = None # For Stable Diffusion
    gemini_model_name: Optional[str] = None # Specific model for Gemini image gen

    # campaign_id: Optional[int] = None # If we want to associate the image with a campaign context during generation
                                     # For now, character images are global to the character.