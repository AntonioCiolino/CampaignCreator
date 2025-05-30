from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .db import Base # Import Base from app.db

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)  # Added
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False) # Added

    campaigns = relationship("Campaign", back_populates="owner")
    llm_configs = relationship("LLMConfig", back_populates="owner")

class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    initial_user_prompt = Column(Text, nullable=True)
    concept = Column(Text, nullable=True) # LLM-generated campaign overview
    toc = Column(Text, nullable=True)
    homebrewery_export = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="campaigns")
    sections = relationship("CampaignSection", back_populates="campaign", cascade="all, delete-orphan")

class CampaignSection(Base):
    __tablename__ = "campaign_sections"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    order = Column(Integer, nullable=False, default=0)
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
