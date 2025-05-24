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
    model: Optional[str] = None # LLM model to use for generating this section
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
    concept: Optional[str] = None # This will store the LLM-generated campaign overview

class CampaignCreate(BaseModel): # No longer inherits CampaignBase directly for more control
    title: str
    initial_user_prompt: str # Non-optional for creation

class Campaign(CampaignBase): # Inherits title, initial_user_prompt, concept
    id: int
    owner_id: int # foreign key to User, will be added later
    toc: Optional[str] = None
    homebrewery_export: Optional[str] = None # To store pre-generated export

    class Config:
        orm_mode = True

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

class UserBase(BaseModel): # Very basic for now
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool = True
    campaigns: List[Campaign] = []
    llm_configs: List[LLMConfig] = []

    class Config:
        orm_mode = True
