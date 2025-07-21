import os
import httpx
from fastmcp import FastMCP
from pydantic import BaseModel, Field

# --- Configuration ---
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

app = FastMCP()

class User(BaseModel):
    username: str

class State(BaseModel):
    user: User
    token: str

@app.mcp_authorize
async def authorize(token: str) -> State:
    """
    Authorizes a user based on a token and returns a session state.
    """
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/api/v1/users/me", headers=headers)
        if response.status_code == 200:
            user_data = response.json()
            return State(user=User(username=user_data.get("username")), token=token)
        else:
            raise Exception("Invalid token")

@app.tool()
async def list_campaigns(context: State) -> list:
    """
    Lists all campaigns for the authenticated user.
    """
    headers = {"Authorization": f"Bearer {context.token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/api/v1/campaigns", headers=headers)
        response.raise_for_status()
        return response.json()

class Campaign(BaseModel):
    title: str
    concept: str

@app.tool()
async def create_campaign(campaign: Campaign, context: State) -> dict:
    """
    Creates a new campaign.
    """
    headers = {"Authorization": f"Bearer {context.token}"}
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/api/v1/campaigns",
            headers=headers,
            json=campaign.model_dump(),
        )
        response.raise_for_status()
        return response.json()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=4000)
