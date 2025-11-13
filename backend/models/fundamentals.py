"""
Database Models for Fundamentals
Beanie ODM models for MongoDB
"""
from beanie import Document
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import Field


class Fundamentals(Document):
    """Fundamentals MongoDB document model"""
    
    ticker: str = Field(..., description="Stock ticker symbol", max_length=10)
    data: Dict[str, Any] = Field(..., description="Fundamentals data")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "fundamentals"  # Collection name
        indexes = [
            "ticker",  # Index on ticker field
        ]
    
    def __repr__(self):
        return f"<Fundamentals(ticker={self.ticker})>"
    
    async def update_timestamp(self):
        """Update the updated_at timestamp"""
        self.updated_at = datetime.utcnow()
        await self.save()


