import sys # Added import
from pathlib import Path # Added import
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # Added import

# Add project root to sys.path to allow importing from 'utils'
project_root = Path(__file__).resolve().parent.parent # main.py is in app/, so app/.parent is project root
sys.path.append(str(project_root))

from utils.migrate_csv_data import seed_all_csv_data # Added import
from .db import init_db, SessionLocal, engine, Base # Added SessionLocal, engine, Base
from app import crud # Added import
from app.api.endpoints import campaigns as campaigns_router
from app.api.endpoints import llm_management as llm_management_router
from app.api.endpoints import utility_endpoints as utility_router
from app.api.endpoints import image_generation as image_generation_router
from app.api.endpoints import import_data as import_data_router
from app.api.endpoints import users as users_router # New import for users
from app.api.endpoints import data_tables # New import for data_tables

app = FastAPI(title="Campaign Crafter API", version="0.1.0")

origins = [
    "http://localhost",
    "http://localhost:3000",
    # Potentially add your deployed frontend URL here in the future
]

app.add_middleware( # Added middleware
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    print("Application startup: Initializing database...")
    # init_db() likely calls Base.metadata.create_all(bind=engine)
    # If not, or to be explicit, call it here:
    Base.metadata.create_all(bind=engine)
    print("Database tables checked/created.")

    db = None
    try:
        db = SessionLocal()
        # Idempotency Check: Check if features table has any data.
        # If it's empty, assume no seeding has happened.
        existing_features = crud.get_features(db=db, limit=1)
        if not existing_features:
            print("No existing features found, proceeding with data seeding...")
            seed_all_csv_data(db) # This function now handles both features and rolltables
            print("Data seeding process completed.")
        else:
            print("Data already exists (features found), skipping CSV data seeding.")
    except Exception as e:
        print(f"An error occurred during startup data seeding: {e}")
    finally:
        if db:
            db.close()
            print("Database session closed after startup.")

# Include routers
app.include_router(campaigns_router.router, prefix="/api/v1/campaigns", tags=["Campaigns"])
app.include_router(llm_management_router.router, prefix="/api/v1/llm", tags=["LLM Management"])
app.include_router(utility_router.router, prefix="/api/v1/utils", tags=["Utilities"])
app.include_router(image_generation_router.router, prefix="/api/v1", tags=["Image Generation"]) 
app.include_router(import_data_router.router, prefix="/api/v1/import", tags=["Import"])
app.include_router(users_router.router, prefix="/api/v1/users", tags=["Users"]) # Added users router
app.include_router(data_tables.router_features, prefix="/api/v1/features", tags=["Features"])
app.include_router(data_tables.router_roll_tables, prefix="/api/v1/roll_tables", tags=["Rolltables"])

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to Campaign Crafter API"}
