"""
Supply Chain Routes
API endpoints for Supply Chain operations
"""
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from typing import Optional
from controllers.supply_chain_controller import SupplyChainController
from schemas.supply_chain import SupplyChainRequest, SupplyChainResponse, SupplyChainData
from services.company_profile_service import CompanyProfileService
from schemas.company_profile import CompanyProfileCreate
import os

router = APIRouter(prefix="/supply-chain", tags=["Supply Chain"])


@router.post("/fetch", response_model=SupplyChainResponse, status_code=status.HTTP_200_OK)
async def fetch_supply_chain_post(request: SupplyChainRequest):
    """
    Fetch supply chain data from Gemini AI and optionally generate graph (POST method)
    
    This endpoint:
    1. Opens Gemini AI in browser
    2. Sends comprehensive supply chain query
    3. Extracts JSON response
    4. Optionally generates HTML graph
    5. Optionally saves to MongoDB
    """
    controller = SupplyChainController()
    
    try:
        # Fetch supply chain data from Gemini
        supply_chain_data = await controller.fetch_supply_chain(request.ticker)
        
        if not supply_chain_data:
            raise HTTPException(
                status_code=500,
                detail="Failed to fetch supply chain data from Gemini"
            )
        
        # Generate graph if requested
        graph_file = None
        graph_url = None
        if request.generate_graph:
            graph_file = await controller.generate_graph(supply_chain_data, request.ticker)
            if graph_file:
                # Convert file path to URL (relative to static files or absolute path)
                # For now, return the filename - frontend can construct URL
                graph_url = f"/supply-chain-graphs/{os.path.basename(graph_file)}"
        
        # If save_to_db is True, save to MongoDB
        saved_profile = None
        if request.save_to_db:
            try:
                service = CompanyProfileService()
                existing_profile = await service.get_by_ticker(request.ticker.upper())
                
                if existing_profile:
                    # Update existing profile - save supply chain data separately
                    from schemas.company_profile import CompanyProfileUpdate
                    existing_data = existing_profile.data or {}
                    updated_data = {
                        **existing_data,
                        "SupplyChain": supply_chain_data  # Save separately by source
                    }
                    saved_profile = await service.update_profile(
                        str(existing_profile.id),
                        CompanyProfileUpdate(data=updated_data)
                    )
                else:
                    # Create new profile with supply chain data
                    profile_create = CompanyProfileCreate(
                        ticker=request.ticker.upper(),
                        data={"SupplyChain": supply_chain_data}  # Save separately by source
                    )
                    saved_profile = await service.create_profile(profile_create)
            except Exception as e:
                print(f"⚠️ Failed to save to database: {e}")
                # Continue even if save fails
        
        # Convert data to response schema
        supply_chain_data_obj = SupplyChainData(**supply_chain_data)
        
        return SupplyChainResponse(
            ticker=request.ticker.upper(),
            data=supply_chain_data_obj,
            graph_file=graph_file,
            graph_url=graph_url,
            saved_to_db=request.save_to_db and saved_profile is not None,
            profile_id=str(saved_profile.id) if saved_profile else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching supply chain: {str(e)}"
        )


@router.get("/fetch/{ticker}", response_model=SupplyChainResponse, status_code=status.HTTP_200_OK)
async def fetch_supply_chain_get(
    ticker: str,
    save_to_db: bool = Query(False, description="If true, save to MongoDB"),
    generate_graph: bool = Query(True, description="If true, generate HTML graph")
):
    """
    Fetch supply chain data from Gemini AI (GET endpoint)
    
    Query params:
    - save_to_db: If true, save profile to MongoDB after fetching
    - generate_graph: If true, generate HTML graph visualization
    """
    controller = SupplyChainController()
    
    try:
        # Fetch supply chain data from Gemini
        supply_chain_data = await controller.fetch_supply_chain(ticker)
        
        if not supply_chain_data:
            raise HTTPException(
                status_code=500,
                detail="Failed to fetch supply chain data from Gemini"
            )
        
        # Generate graph if requested
        graph_file = None
        graph_url = None
        if generate_graph:
            graph_file = await controller.generate_graph(supply_chain_data, ticker)
            if graph_file:
                graph_url = f"/supply-chain-graphs/{os.path.basename(graph_file)}"
        
        # If save_to_db is True, save to MongoDB
        saved_profile = None
        if save_to_db:
            try:
                service = CompanyProfileService()
                existing_profile = await service.get_by_ticker(ticker.upper())
                
                if existing_profile:
                    # Update existing profile - save supply chain data separately
                    from schemas.company_profile import CompanyProfileUpdate
                    existing_data = existing_profile.data or {}
                    updated_data = {
                        **existing_data,
                        "SupplyChain": supply_chain_data  # Save separately by source
                    }
                    saved_profile = await service.update_profile(
                        str(existing_profile.id),
                        CompanyProfileUpdate(data=updated_data)
                    )
                else:
                    # Create new profile with supply chain data
                    profile_create = CompanyProfileCreate(
                        ticker=ticker.upper(),
                        data={"SupplyChain": supply_chain_data}  # Save separately by source
                    )
                    saved_profile = await service.create_profile(profile_create)
            except Exception as e:
                print(f"⚠️ Failed to save to database: {e}")
        
        # Convert data to response schema
        supply_chain_data_obj = SupplyChainData(**supply_chain_data)
        
        return SupplyChainResponse(
            ticker=ticker.upper(),
            data=supply_chain_data_obj,
            graph_file=graph_file,
            graph_url=graph_url,
            saved_to_db=save_to_db and saved_profile is not None,
            profile_id=str(saved_profile.id) if saved_profile else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching supply chain: {str(e)}"
        )


@router.get("/graph/{ticker}", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def get_supply_chain_graph(ticker: str):
    """
    Generate and return HTML graph from MongoDB data (server-side rendering)
    
    This endpoint:
    1. Fetches supply chain data from MongoDB
    2. Generates HTML graph on-the-fly
    3. Returns HTML response
    
    Args:
        ticker: Stock ticker symbol (e.g., NVDA, AAPL)
        
    Returns:
        HTML response with interactive graph
    """
    controller = SupplyChainController()
    
    try:
        # Generate HTML from database data
        html_content = await controller.generate_graph_html_from_db(ticker.upper())
        
        if not html_content:
            raise HTTPException(
                status_code=404,
                detail=f"Supply chain data not found for ticker {ticker.upper()}. Please fetch the data first."
            )
        
        # Return HTML response with proper headers
        return HTMLResponse(
            content=html_content,
            headers={
                "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
                "Content-Type": "text/html; charset=utf-8"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating graph: {str(e)}"
        )

