from fastapi import APIRouter, HTTPException, status
from typing import Optional, Dict, Any
from services.finnhub_service import get_all_finnhub_data
from schemas.finnhub import FinnhubFetchRequest, FinnhubFetchResponse
from schemas.company_profile import CompanyProfileCreate, CompanyProfileUpdate
from services.company_profile_service import CompanyProfileService

router = APIRouter()

class FinnhubController:
    """Controller for Finnhub operations"""

    async def fetch_all_data(self, ticker: str) -> Optional[Dict]:
        """
        Fetch all available data from Finnhub
        """
        try:
            data = await get_all_finnhub_data(ticker.upper())
            return data
        except Exception as e:
            print(f"❌ Error fetching data from Finnhub: {e}")
            return None

@router.post("/fetch-data", response_model=FinnhubFetchResponse, status_code=status.HTTP_200_OK)
async def fetch_data_from_finnhub_post(request: FinnhubFetchRequest):
    ticker = request.ticker.upper()
    save_to_db = request.save_to_db

    print(f"Received request to fetch data for {ticker} from Finnhub (POST)")

    try:
        controller = FinnhubController()
        data = await controller.fetch_all_data(ticker)

        if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No data found for {ticker} from Finnhub."
            )

        profile_id = None
        if save_to_db:
            company_profile_service = CompanyProfileService()
            existing_profile = await company_profile_service.get_by_ticker(ticker)

            if existing_profile:
                # Update existing profile - save Finnhub data separately
                existing_data = existing_profile.data or {}
                updated_data = {
                    **existing_data,
                    "Finnhub": data  # Save separately by source
                }
                updated_profile = await company_profile_service.update_profile(
                    str(existing_profile.id),
                    CompanyProfileUpdate(data=updated_data)
                )
                profile_id = str(updated_profile.id) if updated_profile else None
                print(f"Updated existing profile for {ticker} in DB with Finnhub data: {profile_id}")
            else:
                # Create new profile with Finnhub data
                new_profile = await company_profile_service.create_profile(
                    CompanyProfileCreate(ticker=ticker, data={"Finnhub": data})
                )
                profile_id = str(new_profile.id) if new_profile else None
                print(f"Created new profile for {ticker} in DB with Finnhub data: {profile_id}")

        return FinnhubFetchResponse(
            ticker=ticker,
            data=data,
            saved_to_db=save_to_db,
            profile_id=profile_id
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error fetching data from Finnhub: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching data from Finnhub: {e}"
        )

@router.get("/fetch-data/{ticker}", response_model=FinnhubFetchResponse, status_code=status.HTTP_200_OK)
async def fetch_data_from_finnhub_get(ticker: str, save_to_db: bool = True):
    ticker = ticker.upper()

    print(f"Received request to fetch data for {ticker} from Finnhub (GET)")

    try:
        controller = FinnhubController()
        data = await controller.fetch_all_data(ticker)

        if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No data found for {ticker} from Finnhub."
            )

        profile_id = None
        if save_to_db:
            company_profile_service = CompanyProfileService()
            existing_profile = await company_profile_service.get_by_ticker(ticker)

            if existing_profile:
                existing_data = existing_profile.data or {}
                updated_data = {
                    **existing_data,
                    "Finnhub": data
                }
                updated_profile = await company_profile_service.update_profile(
                    str(existing_profile.id),
                    CompanyProfileUpdate(data=updated_data)
                )
                profile_id = str(updated_profile.id) if updated_profile else None
                print(f"Updated existing profile for {ticker} in DB with Finnhub data: {profile_id}")
            else:
                new_profile = await company_profile_service.create_profile(
                    CompanyProfileCreate(ticker=ticker, data={"Finnhub": data})
                )
                profile_id = str(new_profile.id) if new_profile else None
                print(f"Created new profile for {ticker} in DB with Finnhub data: {profile_id}")

        return FinnhubFetchResponse(
            ticker=ticker,
            data=data,
            saved_to_db=save_to_db,
            profile_id=profile_id
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error fetching data from Finnhub: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching data from Finnhub: {e}"
        )




