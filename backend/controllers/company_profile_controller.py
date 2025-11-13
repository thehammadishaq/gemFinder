"""
Company Profile Controller
Business logic for company profile operations (MongoDB)
"""
from typing import List, Optional
from models.company_profile import CompanyProfile
from schemas.company_profile import (
    CompanyProfileCreate,
    CompanyProfileUpdate
)
from services.company_profile_service import CompanyProfileService


class CompanyProfileController:
    """Controller for company profile operations"""
    
    def __init__(self):
        self.service = CompanyProfileService()
    
    async def create_profile(self, profile_data: CompanyProfileCreate) -> CompanyProfile:
        """Create a new company profile"""
        return await self.service.create_profile(profile_data)
    
    async def get_profile(self, profile_id: str) -> Optional[CompanyProfile]:
        """Get company profile by ID"""
        return await self.service.get_by_id(profile_id)
    
    async def get_profile_by_ticker(self, ticker: str) -> Optional[CompanyProfile]:
        """Get company profile by ticker"""
        return await self.service.get_by_ticker(ticker)
    
    async def get_all_profiles(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[CompanyProfile]:
        """Get all company profiles with pagination"""
        return await self.service.get_all(skip=skip, limit=limit)
    
    async def get_count(self) -> int:
        """Get total count of profiles"""
        return await self.service.get_count()
    
    async def update_profile(
        self,
        profile_id: str,
        profile_data: CompanyProfileUpdate
    ) -> Optional[CompanyProfile]:
        """Update company profile"""
        return await self.service.update_profile(profile_id, profile_data)
    
    async def delete_profile(self, profile_id: str) -> bool:
        """Delete company profile"""
        return await self.service.delete_profile(profile_id)
    
    async def search_profiles(self, query: str) -> List[CompanyProfile]:
        """Search company profiles by ticker"""
        return await self.service.search_by_ticker(query)
