from fastapi import FastAPI
from .db import init_db
from app.api.endpoints import campaigns as campaigns_router
from app.api.endpoints import llm_management as llm_management_router
from app.api.endpoints import utility_endpoints as utility_router # Import the utility router

app = FastAPI(title="Campaign Crafter API", version="0.1.0")

@app.on_event("startup")
async def on_startup():
    # This will create tables if they don't exist.
    # In a production environment, you might use Alembic for migrations.
    init_db()

# Include routers
app.include_router(campaigns_router.router, prefix="/api/v1/campaigns", tags=["Campaigns"])
app.include_router(llm_management_router.router, prefix="/api/v1/llm", tags=["LLM Management"])
app.include_router(utility_router.router, prefix="/api/v1/utils", tags=["Utilities"]) # Include the utility router

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to Campaign Crafter API"}
