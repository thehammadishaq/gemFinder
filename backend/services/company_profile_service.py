"""
Company Profile Service
Service layer for company profile business logic (MongoDB)
"""
from typing import List, Optional
from models.company_profile import CompanyProfile
from schemas.company_profile import (
    CompanyProfileCreate,
    CompanyProfileUpdate
)
from datetime import datetime


class CompanyProfileService:
    """Service for company profile operations"""
    
    async def create_profile(self, profile_data: CompanyProfileCreate) -> CompanyProfile:
        """Create a new company profile"""
        # Check if profile already exists
        existing = await self.get_by_ticker(profile_data.ticker)
        if existing:
            # Update existing profile
            return await self.update_profile(
                str(existing.id),
                CompanyProfileUpdate(data=profile_data.data)
            )
        
        # Create new profile
        db_profile = CompanyProfile(
            ticker=profile_data.ticker.upper(),
            data=profile_data.data,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        await db_profile.insert()
        return db_profile
    
    async def get_by_id(self, profile_id: str) -> Optional[CompanyProfile]:
        """Get company profile by ID"""
        try:
            return await CompanyProfile.get(profile_id)
        except Exception:
            return None
    
    async def get_by_ticker(self, ticker: str) -> Optional[CompanyProfile]:
        """Get company profile by ticker"""
        return await CompanyProfile.find_one(
            CompanyProfile.ticker == ticker.upper()
        )
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[CompanyProfile]:
        """Get all company profiles with pagination"""
        return await CompanyProfile.find_all().skip(skip).limit(limit).to_list()
    
    async def get_count(self) -> int:
        """Get total count of profiles"""
        return await CompanyProfile.find_all().count()
    
    async def update_profile(
        self,
        profile_id: str,
        profile_data: CompanyProfileUpdate
    ) -> Optional[CompanyProfile]:
        """Update company profile"""
        db_profile = await self.get_by_id(profile_id)
        if not db_profile:
            return None
        
        if profile_data.data is not None:
            db_profile.data = profile_data.data
            db_profile.updated_at = datetime.utcnow()
            await db_profile.save()
        
        return db_profile
    
    async def delete_profile(self, profile_id: str) -> bool:
        """Delete company profile"""
        db_profile = await self.get_by_id(profile_id)
        if not db_profile:
            return False
        
        await db_profile.delete()
        return True
    
    async def search_by_ticker(self, query: str) -> List[CompanyProfile]:
        """Search company profiles by ticker"""
        # MongoDB regex search (case-insensitive)
        from beanie.operators import Regex
        return await CompanyProfile.find(
            Regex(CompanyProfile.ticker, query, "i")  # "i" flag for case-insensitive
        ).to_list()
