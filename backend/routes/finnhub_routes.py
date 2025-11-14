from fastapi import APIRouter, HTTPException, status, Query
from typing import Optional, List
from schemas.finnhub import FinnhubFetchRequest, FinnhubFetchResponse
from controllers.finnhub_controller import fetch_data_from_finnhub_post, fetch_data_from_finnhub_get
from services.finnhub_service import safe_get_sync
from config.settings import settings

router = APIRouter(prefix="/finnhub", tags=["Finnhub"])

@router.post("/fetch-data", response_model=FinnhubFetchResponse, status_code=status.HTTP_200_OK)
async def fetch_data_post(request: FinnhubFetchRequest):
    return await fetch_data_from_finnhub_post(request)

@router.get("/fetch-data/{ticker}", response_model=FinnhubFetchResponse, status_code=status.HTTP_200_OK)
async def fetch_data_get(ticker: str, save_to_db: bool = Query(True, description="Whether to save the fetched data to the database")):
    return await fetch_data_from_finnhub_get(ticker, save_to_db)

@router.get("/quote/{symbol}")
async def get_quote(symbol: str):
    """Get current quote (price) for a symbol - works even when market is closed"""
    if not settings.FINNHUB_API_KEY:
        raise HTTPException(status_code=500, detail="FINNHUB_API_KEY not configured")
    
    url = f"https://finnhub.io/api/v1/quote"
    params = {
        "symbol": symbol.upper(),
        "token": settings.FINNHUB_API_KEY
    }
    
    data = safe_get_sync(url, params=params)
    if data is None:
        raise HTTPException(status_code=404, detail=f"No quote data found for {symbol}")
    
    return data

@router.post("/quotes")
async def get_multiple_quotes(symbols: List[str]):
    """Get quotes for multiple symbols at once with rate limiting"""
    if not settings.FINNHUB_API_KEY:
        raise HTTPException(status_code=500, detail="FINNHUB_API_KEY not configured")
    
    import asyncio
    import time
    
    def fetch_quote(symbol):
        url = f"https://finnhub.io/api/v1/quote"
        params = {
            "symbol": symbol.upper(),
            "token": settings.FINNHUB_API_KEY
        }
        return safe_get_sync(url, params=params)
    
    # Fetch quotes in batches to avoid rate limiting
    # Free tier allows ~60 calls/minute, so we'll do 5 at a time with 1 second delays
    quotes = {}
    batch_size = 5  # Smaller batches to avoid rate limits
    delay_between_batches = 1.0  # 1 second delay between batches (60 calls/minute = 1 call/second)
    
    print(f"Fetching quotes for {len(symbols)} symbols in batches of {batch_size}...")
    
    for i in range(0, len(symbols), batch_size):
        batch = symbols[i:i + batch_size]
        print(f"Fetching batch {i // batch_size + 1}/{(len(symbols) + batch_size - 1) // batch_size}: {batch}")
        
        # Fetch batch in parallel
        loop = asyncio.get_event_loop()
        results = await asyncio.gather(*[loop.run_in_executor(None, fetch_quote, symbol) for symbol in batch])
        
        # Format results
        successful = 0
        for j, symbol in enumerate(batch):
            if results[j]:
                quotes[symbol.upper()] = results[j]
                successful += 1
        
        print(f"Batch {i // batch_size + 1} complete: {successful}/{len(batch)} successful")
        
        # Add delay between batches to respect rate limits
        if i + batch_size < len(symbols):
            await asyncio.sleep(delay_between_batches)
    
    print(f"Quote fetching complete: {len(quotes)}/{len(symbols)} symbols retrieved")
    return quotes




