from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, DateTime, Float, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column # Ensure Mapped and mapped_column are imported
from sqlalchemy.sql import func # For default datetime
from typing import Optional # For Mapped[Optional[...]]

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

    campaigns = relationship("Campaign", back_populates="owner")
    llm_configs = relationship("LLMConfig", back_populates="owner")
    roll_tables = relationship("RollTable", back_populates="owner")

class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    initial_user_prompt = Column(Text, nullable=True)
    concept = Column(Text, nullable=True) # LLM-generated campaign overview
    homebrewery_toc = Column(JSON, nullable=True) # Changed from Text to JSON
    display_toc = Column(JSON, nullable=True) # Changed from Text to JSON
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

class CampaignSection(Base):
    __tablename__ = "campaign_sections"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    order = Column(Integer, nullable=False, default=0)
    type = Column(String, nullable=True) # New field for section type
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))

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
