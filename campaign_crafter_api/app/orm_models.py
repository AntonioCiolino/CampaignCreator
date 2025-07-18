from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, DateTime, Float, JSON, Table
from sqlalchemy.orm import relationship, Mapped, mapped_column # Ensure Mapped and mapped_column are imported
from sqlalchemy.sql import func # For default datetime
from typing import Optional, Dict # For Mapped[Optional[...]] and Dict type hint

from .db import Base # Import Base from app.db

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    full_name = Column(String, nullable=True)
    is_superuser = Column(Boolean, default=False)
    disabled = Column(Boolean, default=False)
    encrypted_openai_api_key = Column(String, nullable=True)
    encrypted_sd_api_key = Column(String, nullable=True)
    sd_engine_preference = Column(String, nullable=True)
    encrypted_gemini_api_key = Column(String, nullable=True)
    encrypted_other_llm_api_key = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True) # New field for user avatar

    campaigns = relationship("Campaign", back_populates="owner")
    llm_configs = relationship("LLMConfig", back_populates="owner")
    roll_tables = relationship("RollTable", back_populates="owner")

    @property
    def openai_api_key_provided(self) -> bool:
        return bool(self.encrypted_openai_api_key)

    @property
    def sd_api_key_provided(self) -> bool:
        return bool(self.encrypted_sd_api_key)

    @property
    def gemini_api_key_provided(self) -> bool:
        return bool(self.encrypted_gemini_api_key)

    @property
    def other_llm_api_key_provided(self) -> bool:
        return bool(self.encrypted_other_llm_api_key)

class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    initial_user_prompt = Column(Text, nullable=True)
    concept = Column(Text, nullable=True) # LLM-generated campaign overview
    homebrewery_toc = Column(JSON, nullable=True)
    display_toc = Column(JSON, nullable=True)
    homebrewery_export = Column(Text, nullable=True)
    badge_image_url = Column(String, nullable=True) # New field for campaign badge
    thematic_image_url = Column(String, nullable=True)
    thematic_image_prompt = Column(Text, nullable=True)
    selected_llm_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    temperature: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))

    # New Theme Properties
    theme_primary_color = Column(String, nullable=True)
    theme_secondary_color = Column(String, nullable=True)
    theme_background_color = Column(String, nullable=True)
    theme_text_color = Column(String, nullable=True)
    theme_font_family = Column(String, nullable=True)
    theme_background_image_url = Column(String, nullable=True)
    theme_background_image_opacity = Column(Float, nullable=True) # Store as float (e.g., 0.0 to 1.0)

    # New field for Mood Board
    mood_board_image_urls = Column(JSON, nullable=True)

    owner = relationship("User", back_populates="campaigns")
    sections = relationship("CampaignSection", back_populates="campaign", cascade="all, delete-orphan")
    characters = relationship(
        "Character",
        secondary='character_campaign_association', # Use the string name of the table
        back_populates="campaigns"
    )

class CampaignSection(Base):
    __tablename__ = "campaign_sections"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    order = Column(Integer, nullable=False, default=0)
    type = Column(String, nullable=True) # New field for section type
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    # images_json = Column(JSON, nullable=True) # Field removed

    campaign = relationship("Campaign", back_populates="sections")

class LLMConfig(Base):
    __tablename__ = "llm_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    api_key = Column(String, nullable=True) # In a real app, this should be encrypted
    api_url = Column(String, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="llm_configs")


class GeneratedImage(Base):
    __tablename__ = "generated_images"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True, nullable=False)
    image_url = Column(String, unique=True, nullable=False) # Permanent URL
    prompt = Column(Text, nullable=True)
    model_used = Column(String, nullable=True) # e.g., "dall-e-3", "stable-diffusion-v1-5"
    size = Column(String, nullable=True) # e.g., "1024x1024"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True) # Optional user link
    owner = relationship("User", backref="generated_images") # Define relationship to User


class Feature(Base):
    __tablename__ = "features"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    template = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    owner = relationship('User', backref='features')
    required_context = Column(JSON, nullable=True)  # Stores list of strings
    compatible_types = Column(JSON, nullable=True) # Stores list of strings
    feature_category = Column(String, nullable=True) # Stores category e.g., "FullSection", "Snippet"


class RollTable(Base):
    __tablename__ = "roll_tables"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    owner = relationship("User", back_populates="roll_tables")
    items = relationship("RollTableItem", back_populates="roll_table", cascade="all, delete-orphan")


class RollTableItem(Base):
    __tablename__ = "roll_table_items"

    id = Column(Integer, primary_key=True, index=True)
    min_roll = Column(Integer, nullable=False)
    max_roll = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)
    roll_table_id = Column(Integer, ForeignKey("roll_tables.id"), nullable=False)

    roll_table = relationship("RollTable", back_populates="items")

# Association table for Character and Campaign (many-to-many)
character_campaign_association = Table(
    'character_campaign_association', Base.metadata,
    Column('character_id', Integer, ForeignKey('characters.id'), primary_key=True),
    Column('campaign_id', Integer, ForeignKey('campaigns.id'), primary_key=True)
)

class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    appearance_description = Column(Text, nullable=True)
    image_urls = Column(JSON, nullable=True) # Storing list of strings as JSON
    video_clip_urls = Column(JSON, nullable=True) # Storing list of strings as JSON
    notes_for_llm = Column(Text, nullable=True)

    # Stats - stored as individual columns for querying, can be grouped in Pydantic model
    strength = Column(Integer, default=10)
    dexterity = Column(Integer, default=10)
    constitution = Column(Integer, default=10)
    intelligence = Column(Integer, default=10)
    wisdom = Column(Integer, default=10)
    charisma = Column(Integer, default=10)

    export_format_preference: Mapped[Optional[str]] = mapped_column(String, nullable=True, default='complex')

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", backref="characters") # backref creates `characters` on User

    # Many-to-many relationship with Campaign
    campaigns = relationship(
        "Campaign",
        secondary=character_campaign_association,
        back_populates="characters" # Requires 'characters' relationship on Campaign model
    )

    @property
    def stats(self) -> Dict[str, Optional[int]]:
        """Provides a dictionary view of the character's stats,
           compatible with the Pydantic CharacterStats model."""
        return {
            "strength": self.strength,
            "dexterity": self.dexterity,
            "constitution": self.constitution,
            "intelligence": self.intelligence,
            "wisdom": self.wisdom,
            "charisma": self.charisma,
        }

# Need to add 'characters' relationship to Campaign model
# This will be done in a separate step if modifying Campaign ORM is complex,
# or can be done now if simple. For now, assuming it will be added.
# Example of what to add to Campaign ORM model:
# characters = relationship(
# "Character",
# secondary=character_campaign_association,
# back_populates="campaigns"
# )

from sqlalchemy.schema import UniqueConstraint # Added for UniqueConstraint

# Chat Message Model - Re-architected to store conversation history as JSON
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True) # Still useful as a primary key for the row itself
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True) # Added user_id

    # conversation_history will store a list of message objects, e.g., [{"speaker": "user", "text": "...", "timestamp": "..."}, ...]
    conversation_history = Column(JSON, nullable=False, default=[]) # Stores the entire conversation as a JSON list/array
    memory_summary = Column(Text, nullable=True) # Stores the LLM-generated summary of older parts of the conversation

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()) # Tracks last update to this conversation log

    character = relationship("Character") # Simpler backref might be handled by SQLAlchemy or defined on Character if needed
    user = relationship("User") # Relationship to User

    __table_args__ = (
        UniqueConstraint('character_id', 'user_id', name='uq_character_user_conversation'),
    )
