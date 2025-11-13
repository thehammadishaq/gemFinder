"""
Pydantic Schemas for Fundamentals API
Request and Response models for Fundamentals endpoints
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional


class FundamentalsRequest(BaseModel):
    """Schema for Fundamentals fetch request"""
    ticker: str = Field(..., description="Stock ticker symbol", example="AAPL")
    save_to_db: bool = Field(
        False,
        description="If true, save the fetched fundamentals to MongoDB after fetching"
    )


class FundamentalsResponse(BaseModel):
    """Schema for Fundamentals response"""
    ticker: str
    data: Dict[str, Any]
    saved_to_db: bool = False
    fundamentals_id: Optional[str] = None
    
    class Config:
        from_attributes = True


