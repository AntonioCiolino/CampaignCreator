"""
Pydantic models for the Campaign Crafter MCP server.
"""
from pydantic import BaseModel
from typing import Optional


class Campaign(BaseModel):
    """Campaign model for creating and updating campaigns."""
    title: str
    concept: str


class CharacterStats(BaseModel):
    """Character stats model."""
    strength: Optional[int] = None
    dexterity: Optional[int] = None
    constitution: Optional[int] = None
    intelligence: Optional[int] = None
    wisdom: Optional[int] = None
    charisma: Optional[int] = None


class Character(BaseModel):
    """Character model for creating and updating characters."""
    name: str
    concept: str
    description: Optional[str] = None
    appearance_description: Optional[str] = None
    stats: Optional[CharacterStats] = None
    campaign_id: Optional[int] = None


class CampaignSection(BaseModel):
    """Campaign section model for creating and updating sections."""
    title: str
    content: str
    campaign_id: int


class LinkCharacter(BaseModel):
    """Model for linking characters to campaigns."""
    campaign_id: int
    character_id: int


class GenerateToc(BaseModel):
    """Model for generating a table of contents."""
    campaign_id: int


class GenerateTitles(BaseModel):
    """Model for generating titles for a campaign section."""
    campaign_id: int
    section_id: int