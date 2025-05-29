from pydantic import BaseModel
from typing import Optional

class PrepareHomebreweryPostResponse(BaseModel):
    markdown_content: str
    homebrewery_new_url: str
    filename_suggestion: str
    notes: Optional[str] = "The 'markdown_content' is ready to be copied and pasted into a new Homebrewery brew. Use the URL provided to open the Homebrewery editor."

# You might also want to put other export-related Pydantic models here in the future.
