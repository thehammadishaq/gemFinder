"""
Fundamentals Controller
Controller for Fundamentals scraping operations
"""
from services.fundamentals_scraper_service import fetch_fundamentals_from_gemini
from services.fundamentals_service import FundamentalsService
from schemas.fundamentals import FundamentalsRequest, FundamentalsResponse
from fastapi import HTTPException, status
from typing import Optional, Dict


class FundamentalsController:
    """Controller for Fundamentals scraping operations"""
    
    async def fetch_fundamentals(self, ticker: str) -> Optional[Dict]:
        """
        Fetch fundamentals from Gemini AI
        
        Args:
            ticker: Stock ticker symbol (e.g., AAPL, CIFR)
            
        Returns:
            Dict containing fundamentals data or None if failed
        """
        try:
            fundamentals_data = await fetch_fundamentals_from_gemini(ticker.upper())
            return fundamentals_data
        except Exception as e:
            print(f"❌ Error fetching fundamentals: {e}")
            return None


# Router functions (similar to gemini_controller.py)
async def fetch_fundamentals_from_gemini_post(request: FundamentalsRequest) -> FundamentalsResponse:
    """POST endpoint handler for fetching fundamentals"""
    ticker = request.ticker.upper()
    save_to_db = request.save_to_db
    
    print(f"Received request to fetch fundamentals for {ticker} from Gemini AI (POST)")
    
    try:
        controller = FundamentalsController()
        fundamentals_data = await controller.fetch_fundamentals(ticker)
        
        if not fundamentals_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No comprehensive fundamentals found for {ticker} from Gemini AI."
            )
        
        fundamentals_id = None
        if save_to_db:
            # Save fundamentals in CompanyProfile document under "Fundamentals" key
            from services.company_profile_service import CompanyProfileService
            from schemas.company_profile import CompanyProfileCreate, CompanyProfileUpdate
            
            company_profile_service = CompanyProfileService()
            existing_profile = await company_profile_service.get_by_ticker(ticker)
            
            if existing_profile:
                # Update existing profile - save Fundamentals data separately
                existing_data = existing_profile.data or {}
                updated_data = {
                    **existing_data,
                    "Fundamentals": fundamentals_data  # Save separately by source
                }
                updated_profile = await company_profile_service.update_profile(
                    str(existing_profile.id),
                    CompanyProfileUpdate(data=updated_data)
                )
                fundamentals_id = str(updated_profile.id) if updated_profile else None
                print(f"Updated existing profile for {ticker} in DB with Fundamentals data: {fundamentals_id}")
            else:
                # Create new profile with Fundamentals data
                new_profile = await company_profile_service.create_profile(
                    CompanyProfileCreate(ticker=ticker, data={"Fundamentals": fundamentals_data})
                )
                fundamentals_id = str(new_profile.id) if new_profile else None
                print(f"Created new profile for {ticker} in DB with Fundamentals data: {fundamentals_id}")
        
        return FundamentalsResponse(
            ticker=ticker,
            data=fundamentals_data,
            saved_to_db=save_to_db,
            fundamentals_id=fundamentals_id
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error fetching fundamentals: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching fundamentals: {e}"
        )


async def fetch_fundamentals_from_gemini_get(ticker: str, save_to_db: bool = True) -> FundamentalsResponse:
    """GET endpoint handler for fetching fundamentals"""
    ticker = ticker.upper()
    
    print(f"Received request to fetch fundamentals for {ticker} from Gemini AI (GET)")
    
    try:
        controller = FundamentalsController()
        fundamentals_data = await controller.fetch_fundamentals(ticker)
        
        if not fundamentals_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No comprehensive fundamentals found for {ticker} from Gemini AI."
            )
        
        fundamentals_id = None
        if save_to_db:
            # Save fundamentals in CompanyProfile document under "Fundamentals" key
            from services.company_profile_service import CompanyProfileService
            from schemas.company_profile import CompanyProfileCreate, CompanyProfileUpdate
            
            company_profile_service = CompanyProfileService()
            existing_profile = await company_profile_service.get_by_ticker(ticker)
            
            if existing_profile:
                # Update existing profile - save Fundamentals data separately
                existing_data = existing_profile.data or {}
                updated_data = {
                    **existing_data,
                    "Fundamentals": fundamentals_data  # Save separately by source
                }
                updated_profile = await company_profile_service.update_profile(
                    str(existing_profile.id),
                    CompanyProfileUpdate(data=updated_data)
                )
                fundamentals_id = str(updated_profile.id) if updated_profile else None
                print(f"Updated existing profile for {ticker} in DB with Fundamentals data: {fundamentals_id}")
            else:
                # Create new profile with Fundamentals data
                new_profile = await company_profile_service.create_profile(
                    CompanyProfileCreate(ticker=ticker, data={"Fundamentals": fundamentals_data})
                )
                fundamentals_id = str(new_profile.id) if new_profile else None
                print(f"Created new profile for {ticker} in DB with Fundamentals data: {fundamentals_id}")
        
        return FundamentalsResponse(
            ticker=ticker,
            data=fundamentals_data,
            saved_to_db=save_to_db,
            fundamentals_id=fundamentals_id
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error fetching fundamentals: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching fundamentals: {e}"
        )

