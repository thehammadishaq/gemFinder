"""
Fundamentals Service
Service layer for fundamentals business logic (MongoDB)
"""
from typing import List, Optional
from models.fundamentals import Fundamentals
from schemas.fundamentals import FundamentalsRequest
from datetime import datetime


class FundamentalsService:
    """Service for fundamentals operations"""
    
    async def create_fundamentals(self, ticker: str, data: dict) -> Fundamentals:
        """Create a new fundamentals record"""
        # Check if fundamentals already exists
        existing = await self.get_by_ticker(ticker)
        if existing:
            # Update existing fundamentals
            existing.data = data
            existing.updated_at = datetime.utcnow()
            await existing.save()
            return existing
        
        # Create new fundamentals
        db_fundamentals = Fundamentals(
            ticker=ticker.upper(),
            data=data,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        await db_fundamentals.insert()
        return db_fundamentals
    
    async def get_by_id(self, fundamentals_id: str) -> Optional[Fundamentals]:
        """Get fundamentals by ID"""
        try:
            return await Fundamentals.get(fundamentals_id)
        except Exception:
            return None
    
    async def get_by_ticker(self, ticker: str) -> Optional[Fundamentals]:
        """Get fundamentals by ticker"""
        return await Fundamentals.find_one(
            Fundamentals.ticker == ticker.upper()
        )
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Fundamentals]:
        """Get all fundamentals with pagination"""
        return await Fundamentals.find_all().skip(skip).limit(limit).to_list()
    
    async def get_count(self) -> int:
        """Get total count of fundamentals"""
        return await Fundamentals.find_all().count()
    
    async def update_fundamentals(
        self,
        fundamentals_id: str,
        data: dict
    ) -> Optional[Fundamentals]:
        """Update fundamentals"""
        db_fundamentals = await self.get_by_id(fundamentals_id)
        if not db_fundamentals:
            return None
        
        db_fundamentals.data = data
        db_fundamentals.updated_at = datetime.utcnow()
        await db_fundamentals.save()
        
        return db_fundamentals
    
    async def delete_fundamentals(self, fundamentals_id: str) -> bool:
        """Delete fundamentals"""
        db_fundamentals = await self.get_by_id(fundamentals_id)
        if not db_fundamentals:
            return False
        
        await db_fundamentals.delete()
        return True
    
    async def search_by_ticker(self, query: str) -> List[Fundamentals]:
        """Search fundamentals by ticker"""
        # MongoDB regex search (case-insensitive)
        from beanie.operators import Regex
        return await Fundamentals.find(
            Regex(Fundamentals.ticker, query, "i")  # "i" flag for case-insensitive
        ).to_list()


