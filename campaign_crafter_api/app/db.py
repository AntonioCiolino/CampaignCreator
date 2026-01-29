from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings # Standardized

# DATABASE_URL is now managed by settings
# Handle Render.com's postgres:// URL format (SQLAlchemy requires postgresql://)
database_url = settings.DATABASE_URL
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

# For SQLite, connect_args might be needed if using check_same_thread=False, but default is fine for now.
engine_args = {}
if database_url.startswith("sqlite"):
    engine_args["connect_args"] = {"check_same_thread": False} # Common for FastAPI + SQLite

engine = create_engine(database_url, **engine_args)
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
