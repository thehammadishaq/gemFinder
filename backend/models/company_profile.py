"""
Database Models for Company Profile
Beanie ODM models for MongoDB
"""
from beanie import Document
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import Field


class CompanyProfile(Document):
    """Company Profile MongoDB document model"""
    
    ticker: str = Field(..., description="Stock ticker symbol", max_length=10)
    data: Dict[str, Any] = Field(..., description="Company profile data")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "company_profiles"  # Collection name
        indexes = [
            "ticker",  # Index on ticker field
        ]
    
    def __repr__(self):
        return f"<CompanyProfile(ticker={self.ticker})>"
    
    async def update_timestamp(self):
        """Update the updated_at timestamp"""
        self.updated_at = datetime.utcnow()
        await self.save()
