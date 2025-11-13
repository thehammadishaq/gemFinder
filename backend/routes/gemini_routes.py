"""
Gemini Routes
API endpoints for Gemini scraping operations
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Optional
from controllers.gemini_controller import GeminiController
from schemas.gemini import GeminiProfileResponse, GeminiProfileRequest
from services.company_profile_service import CompanyProfileService
from schemas.company_profile import CompanyProfileCreate

router = APIRouter(prefix="/gemini", tags=["Gemini AI"])


@router.post("/fetch-profile", response_model=GeminiProfileResponse)
async def fetch_company_profile(
    request: GeminiProfileRequest,
    background_tasks: BackgroundTasks
):
    """
    Fetch company profile from Gemini AI and optionally save to database
    
    This endpoint:
    1. Opens Gemini AI in browser
    2. Sends comprehensive company profile query
    3. Extracts JSON response
    4. Optionally saves to MongoDB
    """
    controller = GeminiController()
    
    try:
        # Fetch profile from Gemini
        profile_data = await controller.fetch_company_profile(request.ticker)
        
        if not profile_data:
            raise HTTPException(
                status_code=500,
                detail="Failed to fetch company profile from Gemini"
            )
        
        # If save_to_db is True, save to MongoDB
        saved_profile = None
        if request.save_to_db:
            try:
                service = CompanyProfileService()
                existing_profile = await service.get_by_ticker(request.ticker.upper())
                
                if existing_profile:
                    # Update existing profile - save Gemini data separately
                    from schemas.company_profile import CompanyProfileUpdate
                    existing_data = existing_profile.data or {}
                    updated_data = {
                        **existing_data,
                        "Gemini": profile_data  # Save separately by source
                    }
                    saved_profile = await service.update_profile(
                        str(existing_profile.id),
                        CompanyProfileUpdate(data=updated_data)
                    )
                else:
                    # Create new profile with Gemini data
                    profile_create = CompanyProfileCreate(
                        ticker=request.ticker.upper(),
                        data={"Gemini": profile_data}  # Save separately by source
                    )
                    saved_profile = await service.create_profile(profile_create)
            except Exception as e:
                print(f"⚠️ Failed to save to database: {e}")
                # Continue even if save fails
        
        return GeminiProfileResponse(
            ticker=request.ticker.upper(),
            data=profile_data,
            saved_to_db=request.save_to_db and saved_profile is not None,
            profile_id=str(saved_profile.id) if saved_profile else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching profile: {str(e)}"
        )


@router.get("/fetch-profile/{ticker}", response_model=GeminiProfileResponse)
async def fetch_company_profile_get(
    ticker: str,
    save_to_db: bool = False
):
    """
    Fetch company profile from Gemini AI (GET endpoint)
    
    Query params:
    - save_to_db: If true, save profile to MongoDB after fetching
    """
    controller = GeminiController()
    
    try:
        profile_data = await controller.fetch_company_profile(ticker)
        
        if not profile_data:
            raise HTTPException(
                status_code=500,
                detail="Failed to fetch company profile from Gemini"
            )
        
        saved_profile = None
        if save_to_db:
            try:
                service = CompanyProfileService()
                existing_profile = await service.get_by_ticker(ticker.upper())
                
                if existing_profile:
                    # Update existing profile - save Gemini data separately
                    from schemas.company_profile import CompanyProfileUpdate
                    existing_data = existing_profile.data or {}
                    updated_data = {
                        **existing_data,
                        "Gemini": profile_data  # Save separately by source
                    }
                    saved_profile = await service.update_profile(
                        str(existing_profile.id),
                        CompanyProfileUpdate(data=updated_data)
                    )
                else:
                    # Create new profile with Gemini data
                    profile_create = CompanyProfileCreate(
                        ticker=ticker.upper(),
                        data={"Gemini": profile_data}  # Save separately by source
                    )
                    saved_profile = await service.create_profile(profile_create)
            except Exception as e:
                print(f"⚠️ Failed to save to database: {e}")
        
        return GeminiProfileResponse(
            ticker=ticker.upper(),
            data=profile_data,
            saved_to_db=save_to_db and saved_profile is not None,
            profile_id=str(saved_profile.id) if saved_profile else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching profile: {str(e)}"
        )

