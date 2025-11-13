"""
Polygon Controller
Controller for Polygon.io operations
"""
from services.polygon_service import get_company_profile_from_polygon
from services.company_profile_service import CompanyProfileService
from schemas.polygon import PolygonFetchRequest, PolygonFetchResponse
from schemas.company_profile import CompanyProfileCreate
from fastapi import HTTPException, status
from typing import Optional, Dict, Any


class PolygonController:
    """Controller for Polygon.io operations"""
    
    async def fetch_company_profile(self, ticker: str) -> Optional[Dict]:
        """
        Fetch company profile from Polygon.io
        
        Args:
            ticker: Stock ticker symbol (e.g., AAPL, CIFR)
            
        Returns:
            Dict containing company profile data or None if failed
        """
        try:
            profile_data = await get_company_profile_from_polygon(ticker.upper())
            return profile_data
        except Exception as e:
            print(f"❌ Error fetching company profile from Polygon.io: {e}")
            return None


# Router functions
async def fetch_profile_from_polygon_post(request: PolygonFetchRequest) -> PolygonFetchResponse:
    """POST endpoint handler for fetching profile from Polygon.io"""
    ticker = request.ticker.upper()
    save_to_db = request.save_to_db
    
    print(f"Received request to fetch profile for {ticker} from Polygon.io (POST)")
    
    try:
        controller = PolygonController()
        profile_data = await controller.fetch_company_profile(ticker)
        
        if not profile_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No profile found for {ticker} from Polygon.io."
            )
        
        profile_id = None
        if save_to_db:
            company_profile_service = CompanyProfileService()
            existing_profile = await company_profile_service.get_by_ticker(ticker)
            
            if existing_profile:
                # Update existing profile - save Polygon data separately
                from schemas.company_profile import CompanyProfileUpdate
                existing_data = existing_profile.data or {}
                # Save Polygon data under "Polygon" key
                updated_data = {
                    **existing_data,
                    "Polygon": profile_data  # Save separately by source
                }
                updated_profile = await company_profile_service.update_profile(
                    str(existing_profile.id),
                    CompanyProfileUpdate(data=updated_data)
                )
                profile_id = str(updated_profile.id) if updated_profile else None
                print(f"Updated existing profile for {ticker} in DB with Polygon data: {profile_id}")
            else:
                # Create new profile with Polygon data
                new_profile = await company_profile_service.create_profile(
                    CompanyProfileCreate(ticker=ticker, data={"Polygon": profile_data})
                )
                profile_id = str(new_profile.id) if new_profile else None
                print(f"Created new profile for {ticker} in DB with Polygon data: {profile_id}")
        
        return PolygonFetchResponse(
            ticker=ticker,
            data=profile_data,
            saved_to_db=save_to_db,
            profile_id=profile_id
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error fetching company profile from Polygon.io: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching company profile from Polygon.io: {e}"
        )


async def fetch_profile_from_polygon_get(ticker: str, save_to_db: bool = True) -> PolygonFetchResponse:
    """GET endpoint handler for fetching profile from Polygon.io"""
    ticker = ticker.upper()
    
    print(f"Received request to fetch profile for {ticker} from Polygon.io (GET)")
    
    try:
        controller = PolygonController()
        profile_data = await controller.fetch_company_profile(ticker)
        
        if not profile_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No profile found for {ticker} from Polygon.io."
            )
        
        profile_id = None
        if save_to_db:
            company_profile_service = CompanyProfileService()
            existing_profile = await company_profile_service.get_by_ticker(ticker)
            
            if existing_profile:
                from schemas.company_profile import CompanyProfileUpdate
                existing_data = existing_profile.data or {}
                # Save Polygon data under "Polygon" key
                updated_data = {
                    **existing_data,
                    "Polygon": profile_data  # Save separately by source
                }
                updated_profile = await company_profile_service.update_profile(
                    str(existing_profile.id),
                    CompanyProfileUpdate(data=updated_data)
                )
                profile_id = str(updated_profile.id) if updated_profile else None
                print(f"Updated existing profile for {ticker} in DB with Polygon data: {profile_id}")
            else:
                new_profile = await company_profile_service.create_profile(
                    CompanyProfileCreate(ticker=ticker, data={"Polygon": profile_data})
                )
                profile_id = str(new_profile.id) if new_profile else None
                print(f"Created new profile for {ticker} in DB with Polygon data: {profile_id}")
        
        return PolygonFetchResponse(
            ticker=ticker,
            data=profile_data,
            saved_to_db=save_to_db,
            profile_id=profile_id
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error fetching company profile from Polygon.io: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching company profile from Polygon.io: {e}"
        )




