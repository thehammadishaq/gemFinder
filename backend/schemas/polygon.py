from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class PolygonFetchRequest(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol to fetch profile for", example="AAPL")
    save_to_db: bool = Field(True, description="Whether to save the fetched profile to the database")

class PolygonFetchResponse(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol")
    data: Dict[str, Any] = Field(..., description="Fetched company profile data from Polygon.io")
    saved_to_db: bool = Field(..., description="Indicates if the profile was saved to the database")
    profile_id: Optional[str] = Field(None, description="ID of the saved profile if saved to DB")




