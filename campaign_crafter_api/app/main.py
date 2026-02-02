from fastapi import FastAPI
import logging
from fastapi.middleware.cors import CORSMiddleware # Added import
from contextlib import asynccontextmanager # Added for lifespan

# sys.path manipulation for 'utils' is no longer needed here.
# We will use a relative import for the seeding module.
from app.core.config import settings # Corrected
from app.core.seeding import seed_all_csv_data # Corrected
from app.db import init_db, SessionLocal, engine, Base # Corrected
from app import crud 
from app.api.endpoints import campaigns as campaigns_router
from app.api.endpoints import llm_management as llm_management_router
from app.api.endpoints import utility_endpoints as utility_router
from app.api.endpoints import image_generation as image_generation_router
from app.api.endpoints import import_data as import_data_router
from app.api.endpoints import users as users_router # New import for users
from app.api.endpoints import user_settings # Import for user_settings
from app.api.endpoints import data_tables # New import for data_tables
from app.api.endpoints import auth as auth_router # Import for auth
from app.api.endpoints import file_uploads as file_uploads_router # Import for file uploads
from app.api.endpoints import characters as characters_router # Import for characters

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Application startup: Initializing database...")
    # init_db() likely calls Base.metadata.create_all(bind=engine)
    # If not, or to be explicit, call it here:
    Base.metadata.create_all(bind=engine)
    logger.info(f"Database tables checked/created.")

    db = None
    try:
        db = SessionLocal()
        # Idempotency Check: Check if features table has any data.
        # If it's empty, assume no seeding has happened.
        existing_features = crud.get_features(db=db, limit=1)
        if not existing_features:
            logger.info(f"No existing features found, proceeding with data seeding...")
            seed_all_csv_data(db) # This function now handles both features and rolltables
            logger.info(f"Data seeding process completed.")
        else:
            logger.info(f"Data already exists (features found), skipping CSV data seeding.")

        yield # Application is ready to serve requests

    except Exception as e:
        logger.error(f"An error occurred during startup data seeding or application lifecycle: {e}")
    finally:
        if db:
            db.close()
            logger.info(f"Database session closed after startup/shutdown.")

app = FastAPI(title="Campaign Crafter API", version="0.1.0", lifespan=lifespan)

# origins = ["*"] # Removed this line

app.add_middleware( # Added middleware
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS, # Use the new setting
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers - IMPORTANT: More specific prefixes MUST come before generic ones
# to avoid route conflicts (e.g., /api/v1/features before /api/v1)
app.include_router(campaigns_router.router, prefix="/api/v1/campaigns", tags=["Campaigns"])
app.include_router(llm_management_router.router, prefix="/api/v1/llm", tags=["LLM Management"])
app.include_router(import_data_router.router, prefix="/api/v1/import", tags=["Import"])
app.include_router(users_router.router, prefix="/api/v1/users", tags=["Users"]) # Added users router
app.include_router(user_settings.router, prefix="/api/v1/users", tags=["User Settings"]) # Added user_settings router
app.include_router(auth_router.router, prefix="/api/v1/auth", tags=["Authentication"]) # Added auth router
app.include_router(data_tables.router_features, prefix="/api/v1/features", tags=["Features"])
app.include_router(data_tables.router_roll_tables, prefix="/api/v1/roll_tables", tags=["Rolltables"])
app.include_router(characters_router.router, prefix="/api/v1/characters", tags=["Characters"])
# Generic routers with /api/v1 prefix MUST come last
app.include_router(utility_router.router, prefix="/api/v1", tags=["Utilities"])
app.include_router(image_generation_router.router, prefix="/api/v1", tags=["Image Generation"]) 
app.include_router(file_uploads_router.router, prefix="/api/v1", tags=["File Uploads"]) # Added file_uploads router

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to Campaign Crafter API"}

if __name__ == "__main__":
    import uvicorn
    import os
    port_from_env = os.getenv("PORT", "8001")
    logger.info(f"Starting server on port {port_from_env}")
    uvicorn.run(app, host="0.0.0.0", port=int(port_from_env))
