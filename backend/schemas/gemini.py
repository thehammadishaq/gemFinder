"""
Pydantic Schemas for Gemini API
Request and Response models for Gemini endpoints
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional


class GeminiProfileRequest(BaseModel):
    """Schema for Gemini profile fetch request"""
    ticker: str = Field(..., description="Stock ticker symbol", example="AAPL")
    save_to_db: bool = Field(
        False,
        description="If true, save the fetched profile to MongoDB after fetching"
    )


class GeminiProfileResponse(BaseModel):
    """Schema for Gemini profile response"""
    ticker: str
    data: Dict[str, Any]
    saved_to_db: bool = False
    profile_id: Optional[str] = None
    
    class Config:
        from_attributes = True

