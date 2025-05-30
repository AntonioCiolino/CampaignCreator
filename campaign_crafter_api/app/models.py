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
        orm_mode = True

class CampaignTitlesResponse(BaseModel):
    titles: List[str]

class CampaignSectionCreateInput(BaseModel):
    title: Optional[str] = None  # User can suggest a title for the section
    prompt: Optional[str] = None # User can provide a specific prompt/starting sentence for the section content
    model_id_with_prefix: Optional[str] = None # Changed field name
    # 'order' will be determined by the backend or could be optionally suggested

class LLMGenerationRequest(BaseModel):
    model: Optional[str] = None
    # temperature: Optional[float] = None # For future use

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
        orm_mode = True

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

class CampaignCreate(CampaignBase):
    model_id_with_prefix_for_concept: Optional[str] = None

class Campaign(CampaignBase):
    id: int
    owner_id: int # In a real app, this would be properly linked
    concept: Optional[str] = None # LLM-generated campaign overview
    toc: Optional[str] = None # LLM-generated table of contents
    homebrewery_export: Optional[str] = None # Stores the homebrewery export
    sections: List['CampaignSection'] = [] # Assuming CampaignSection is defined elsewhere or properly forward referenced

    class Config:
        orm_mode = True

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
        orm_mode = True

class LLMTextGenerationResponse(BaseModel):
    text: str  # Placeholder field; add more fields as needed
