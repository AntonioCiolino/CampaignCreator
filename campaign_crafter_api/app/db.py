import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Try to get DATABASE_URL from environment, otherwise default to a local SQLite file for easier testing/dev startup
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL not found in environment, defaulting to SQLite: ./test_app_temp.db")
    DATABASE_URL = "sqlite:///./test_app_temp.db"

# For SQLite, connect_args might be needed if using check_same_thread=False, but default is fine for now.
engine_args = {}
if DATABASE_URL.startswith("sqlite"):
    engine_args["connect_args"] = {"check_same_thread": False} # Common for FastAPI + SQLite

engine = create_engine(DATABASE_URL, **engine_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Function to create database tables
def init_db():
    # Import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    from . import orm_models # noqa
    Base.metadata.create_all(bind=engine)

# Dependency to get DB session (can be used in path operations)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
