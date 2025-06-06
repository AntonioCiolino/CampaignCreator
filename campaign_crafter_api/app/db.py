from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .core.config import settings # Added import

# DATABASE_URL is now managed by settings

# For SQLite, connect_args might be needed if using check_same_thread=False, but default is fine for now.
engine_args = {}
if settings.DATABASE_URL.startswith("sqlite"): # Use settings.DATABASE_URL
    engine_args["connect_args"] = {"check_same_thread": False} # Common for FastAPI + SQLite

engine = create_engine(settings.DATABASE_URL, **engine_args) # Use settings.DATABASE_URL
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
