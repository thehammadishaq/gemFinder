from fastapi import APIRouter, HTTPException, status, Query
from typing import Optional
from schemas.finnhub import FinnhubFetchRequest, FinnhubFetchResponse
from controllers.finnhub_controller import fetch_data_from_finnhub_post, fetch_data_from_finnhub_get

router = APIRouter(prefix="/finnhub", tags=["Finnhub"])

@router.post("/fetch-data", response_model=FinnhubFetchResponse, status_code=status.HTTP_200_OK)
async def fetch_data_post(request: FinnhubFetchRequest):
    return await fetch_data_from_finnhub_post(request)

@router.get("/fetch-data/{ticker}", response_model=FinnhubFetchResponse, status_code=status.HTTP_200_OK)
async def fetch_data_get(ticker: str, save_to_db: bool = Query(True, description="Whether to save the fetched data to the database")):
    return await fetch_data_from_finnhub_get(ticker, save_to_db)




