"""
Fundamentals Routes
API endpoints for Fundamentals scraping operations
"""
from fastapi import APIRouter, HTTPException, Query, status
from typing import Optional
from schemas.fundamentals import FundamentalsRequest, FundamentalsResponse
from controllers.fundamentals_controller import (
    fetch_fundamentals_from_gemini_post,
    fetch_fundamentals_from_gemini_get
)

router = APIRouter(prefix="/fundamentals", tags=["Fundamentals"])


@router.post("/fetch", response_model=FundamentalsResponse, status_code=status.HTTP_200_OK)
async def fetch_fundamentals_post(request: FundamentalsRequest):
    """
    Fetch fundamentals from Gemini AI (POST method)
    
    This endpoint:
    1. Opens Gemini AI in browser
    2. Sends comprehensive fundamentals query
    3. Extracts JSON response
    4. Optionally saves to MongoDB
    """
    return await fetch_fundamentals_from_gemini_post(request)


@router.get("/fetch/{ticker}", response_model=FundamentalsResponse, status_code=status.HTTP_200_OK)
async def fetch_fundamentals_get(
    ticker: str,
    save_to_db: bool = Query(True, description="Whether to save the fetched fundamentals to the database")
):
    """
    Fetch fundamentals from Gemini AI (GET method)
    
    Query params:
    - save_to_db: If true, save fundamentals to MongoDB after fetching
    """
    return await fetch_fundamentals_from_gemini_get(ticker, save_to_db)


