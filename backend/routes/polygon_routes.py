"""
Polygon Routes
API endpoints for Polygon.io operations
"""
from fastapi import APIRouter, HTTPException, status, Query
from typing import Optional
from schemas.polygon import PolygonFetchRequest, PolygonFetchResponse
from controllers.polygon_controller import fetch_profile_from_polygon_post, fetch_profile_from_polygon_get

router = APIRouter(prefix="/polygon", tags=["Polygon.io"])

@router.post("/fetch-profile", response_model=PolygonFetchResponse, status_code=status.HTTP_200_OK)
async def fetch_profile_post(request: PolygonFetchRequest):
    return await fetch_profile_from_polygon_post(request)

@router.get("/fetch-profile/{ticker}", response_model=PolygonFetchResponse, status_code=status.HTTP_200_OK)
async def fetch_profile_get(ticker: str, save_to_db: bool = Query(True, description="Whether to save the fetched profile to the database")):
    return await fetch_profile_from_polygon_get(ticker, save_to_db)




