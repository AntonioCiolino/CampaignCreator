from typing import Optional, List
from pydantic import BaseModel

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

class CampaignFullContentResponse(BaseModel):
    campaign_id: int
    title: Optional[str] # Title of the campaign
    full_content: str

class ModelInfo(BaseModel):
    id: str
    name: str
    capabilities: List[str] = ["chat"] # Default changed to ["chat"]
    # Potentially add other fields like 'description' or 'type' in the future

class ModelListResponse(BaseModel):
    models: List[ModelInfo]

class CampaignSectionBase(BaseModel):
    title: Optional[str] = None
    content: str
    order: int # To maintain section order

class CampaignSectionCreate(CampaignSectionBase):
    pass

class CampaignSection(CampaignSectionBase):
    id: int
    campaign_id: int # foreign key to Campaign

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
    selected_llm_id: Optional[str] = None
    temperature: Optional[float] = None

class CampaignCreate(CampaignBase):
    model_id_with_prefix_for_concept: Optional[str] = None

class Campaign(CampaignBase):
    id: int
    owner_id: int # In a real app, this would be properly linked
    concept: Optional[str] = None # LLM-generated campaign overview
    homebrewery_toc: Optional[str] = None # Renamed from toc
    display_toc: Optional[str] = None # New field for display TOC
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
    email: str
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str
    is_active: Optional[bool] = True # Default to True
    is_superuser: Optional[bool] = False # Default to False

class CampaignUpdate(BaseModel): # Assuming CampaignUpdate is for PATCH, all fields optional
    title: Optional[str] = None
    initial_user_prompt: Optional[str] = None
    concept: Optional[str] = None
    homebrewery_toc: Optional[str] = None # Renamed from toc
    display_toc: Optional[str] = None # New field for display TOC
    homebrewery_export: Optional[str] = None
    badge_image_url: Optional[str] = None
    selected_llm_id: Optional[str] = None # Ensure it's part of CampaignUpdate for PATCH
    temperature: Optional[float] = None   # Ensure it's part of CampaignUpdate for PATCH


class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None # For setting a new password
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None

class User(UserBase): # For responses
    id: int
    is_active: bool
    is_superuser: bool = False # Assuming ORM default or set value

    campaigns: List[Campaign] = []
    llm_configs: List[LLMConfig] = []

    class Config:
        from_attributes = True

# Feature Models
class FeatureBase(BaseModel):
    name: str
    template: str

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

class RollTableCreate(RollTableBase):
    items: List[RollTableItemCreate]

class RollTableUpdate(RollTableBase):
    name: Optional[str] = None
    description: Optional[str] = None
    items: Optional[List[RollTableItemCreate]] = None

class RollTable(RollTableBase):
    id: int
    items: List[RollTableItem] = []

    class Config:
        from_attributes = True

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
