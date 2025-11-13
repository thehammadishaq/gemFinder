"""
Company Profile Routes
API endpoints for company profile operations (MongoDB)
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from typing import List
import json

from controllers.company_profile_controller import CompanyProfileController
from schemas.company_profile import (
    CompanyProfileCreate,
    CompanyProfileResponse,
    CompanyProfileListResponse,
    CompanyProfileUpdate,
    SuccessResponse
)

router = APIRouter(prefix="/profiles", tags=["Company Profiles"])


@router.post("/", response_model=CompanyProfileResponse, status_code=201)
async def create_profile(profile_data: CompanyProfileCreate):
    """Create a new company profile"""
    controller = CompanyProfileController()
    profile = await controller.create_profile(profile_data)
    # Convert MongoDB document to response format
    return CompanyProfileResponse(
        id=str(profile.id),
        ticker=profile.ticker,
        data=profile.data,
        created_at=profile.created_at,
        updated_at=profile.updated_at
    )


@router.get("/", response_model=CompanyProfileListResponse)
async def get_all_profiles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get all company profiles with pagination"""
    controller = CompanyProfileController()
    profiles = await controller.get_all_profiles(skip=skip, limit=limit)
    total = await controller.get_count()
    
    # Convert MongoDB documents to response format
    profile_responses = [
        CompanyProfileResponse(
            id=str(p.id),
            ticker=p.ticker,
            data=p.data,
            created_at=p.created_at,
            updated_at=p.updated_at
        )
        for p in profiles
    ]
    
    return CompanyProfileListResponse(
        profiles=profile_responses,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit
    )


@router.get("/{profile_id}", response_model=CompanyProfileResponse)
async def get_profile(profile_id: str):
    """Get company profile by ID"""
    controller = CompanyProfileController()
    profile = await controller.get_profile(profile_id)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return CompanyProfileResponse(
        id=str(profile.id),
        ticker=profile.ticker,
        data=profile.data,
        created_at=profile.created_at,
        updated_at=profile.updated_at
    )


@router.get("/ticker/{ticker}", response_model=CompanyProfileResponse)
async def get_profile_by_ticker(ticker: str):
    """Get company profile by ticker symbol"""
    controller = CompanyProfileController()
    profile = await controller.get_profile_by_ticker(ticker)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return CompanyProfileResponse(
        id=str(profile.id),
        ticker=profile.ticker,
        data=profile.data,
        created_at=profile.created_at,
        updated_at=profile.updated_at
    )


@router.put("/{profile_id}", response_model=CompanyProfileResponse)
async def update_profile(
    profile_id: str,
    profile_data: CompanyProfileUpdate
):
    """Update company profile"""
    controller = CompanyProfileController()
    profile = await controller.update_profile(profile_id, profile_data)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return CompanyProfileResponse(
        id=str(profile.id),
        ticker=profile.ticker,
        data=profile.data,
        created_at=profile.created_at,
        updated_at=profile.updated_at
    )


@router.delete("/{profile_id}", response_model=SuccessResponse)
async def delete_profile(profile_id: str):
    """Delete company profile"""
    controller = CompanyProfileController()
    success = await controller.delete_profile(profile_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return SuccessResponse(message="Profile deleted successfully")


@router.post("/upload", response_model=CompanyProfileResponse, status_code=201)
async def upload_json_file(file: UploadFile = File(...)):
    """Upload company profile from JSON file"""
    # Validate file extension
    if not file.filename.endswith('.json'):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only JSON files are allowed."
        )
    
    # Read file content
    content = await file.read()
    
    try:
        # Parse JSON
        data = json.loads(content.decode('utf-8'))
        
        # Extract ticker from filename (e.g., gemini_company_profile_AAPL.json)
        filename = file.filename
        ticker = None
        
        # Try to extract ticker from filename
        if 'gemini_company_profile_' in filename:
            ticker = filename.replace('gemini_company_profile_', '').replace('.json', '').upper()
        elif 'company_profile_' in filename:
            ticker = filename.replace('company_profile_', '').replace('.json', '').upper()
        else:
            # Try to get ticker from data
            ticker = data.get('ticker') or data.get('Ticker')
        
        if not ticker:
            raise HTTPException(
                status_code=400,
                detail="Ticker symbol not found in filename or data"
            )
        
        # Create profile
        controller = CompanyProfileController()
        profile_data = CompanyProfileCreate(ticker=ticker, data=data)
        profile = await controller.create_profile(profile_data)
        
        return CompanyProfileResponse(
            id=str(profile.id),
            ticker=profile.ticker,
            data=profile.data,
            created_at=profile.created_at,
            updated_at=profile.updated_at
        )
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/{query}", response_model=List[CompanyProfileResponse])
async def search_profiles(query: str):
    """Search company profiles by ticker"""
    controller = CompanyProfileController()
    profiles = await controller.search_profiles(query)
    
    return [
        CompanyProfileResponse(
            id=str(p.id),
            ticker=p.ticker,
            data=p.data,
            created_at=p.created_at,
            updated_at=p.updated_at
        )
        for p in profiles
    ]
