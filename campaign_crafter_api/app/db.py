import logging # Add logging import
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool  # Import NullPool
from app.core.config import settings # Standardized

# Configure basic logging
# Consider moving this to a central logging configuration if you have one
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# DATABASE_URL is now managed by settings

engine_args = {
    "poolclass": NullPool
}

# For psycopg2, to disable prepared statements when using transaction pooling
# and ensure the public schema is in the search path.
# This is only relevant for PostgreSQL.
if settings.DATABASE_URL.startswith("postgresql"):
    # Ensure connect_args exists before trying to add to it
    if "connect_args" not in engine_args:
        engine_args["connect_args"] = {}
    # Using 'options' is a way to pass command-line options to the backend connection
    # statement_cache_size=0 disables prepared statements for psycopg2
    # search_path=public ensures the public schema is used.
    engine_args["connect_args"]["options"] = "-c search_path=public -c statement_cache_size=0"
elif settings.DATABASE_URL.startswith("sqlite"):
    # For SQLite, connect_args might be needed if using check_same_thread=False
    if "connect_args" not in engine_args:
        engine_args["connect_args"] = {}
    engine_args["connect_args"]["check_same_thread"] = False

engine = create_engine(settings.DATABASE_URL, **engine_args)
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
    logger.info("DB Session: Attempting to open new session.")
    db = SessionLocal()
    logger.info(f"DB Session {id(db)}: Opened.")
    try:
        yield db
    finally:
        logger.info(f"DB Session {id(db)}: Closing session.")
        db.close()
        logger.info(f"DB Session {id(db)}: Closed.")
