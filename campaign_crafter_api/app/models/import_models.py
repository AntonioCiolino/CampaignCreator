from pydantic import BaseModel
from typing import List, Optional, Dict

class SectionStructure(BaseModel):
    title: Optional[str] = None
    content: str
    order: Optional[int] = None # Optional: if order is provided in the import

class CampaignStructure(BaseModel):
    title: str
    concept: Optional[str] = None
    toc: Optional[str] = None
    sections: List[SectionStructure]

# For JSON import, we might receive:
# 1. A single CampaignStructure object.
# 2. A list of SectionStructure objects (to be added to an existing campaign or a new one).
# We'll need to handle this flexibility in the service.

class ImportErrorDetail(BaseModel):
    file_name: Optional[str] = None # For Zip imports
    item_identifier: Optional[str] = None # e.g., title of a section that failed
    error: str

class ImportSummaryResponse(BaseModel):
    message: str = "Import process completed."
    imported_campaigns_count: int = 0
    imported_sections_count: int = 0
    created_campaign_ids: List[int] = [] # IDs of newly created campaigns
    updated_campaign_ids: List[int] = [] # IDs of campaigns to which sections were added
    errors: List[ImportErrorDetail] = []

    # Example of how to provide a more detailed summary
    # class CampaignImportResult(BaseModel):
    #     campaign_id: int
    #     title: str
    #     imported_sections: int
    #     status: str # e.g. "Created", "Updated"
    # campaign_results: List[CampaignImportResult] = []
