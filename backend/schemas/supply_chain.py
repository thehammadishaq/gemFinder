"""
Pydantic Schemas for Supply Chain API
Request and Response models for Supply Chain endpoints
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List


class SupplyChainRequest(BaseModel):
    """Schema for supply chain fetch request"""
    ticker: str = Field(..., description="Stock ticker symbol", example="AAPL")
    save_to_db: bool = Field(
        False,
        description="If true, save the fetched supply chain data to MongoDB after fetching"
    )
    generate_graph: bool = Field(
        True,
        description="If true, generate HTML graph visualization"
    )


class SupplyChainEntity(BaseModel):
    """Schema for supply chain entity (supplier, customer, etc.)"""
    name: str
    type: Optional[str] = None
    region: Optional[str] = None
    location: Optional[str] = None
    role: Optional[str] = None
    sector: Optional[str] = None
    notes: Optional[str] = None
    source: Optional[str] = None
    logo: Optional[str] = None
    amount: Optional[str] = None


class SupplyChainRisk(BaseModel):
    """Schema for supply chain risk"""
    risk: str
    impact: str
    notes: str


class SupplyChainData(BaseModel):
    """Schema for supply chain data structure"""
    company: str
    company_logo: Optional[str] = None
    suppliers: List[SupplyChainEntity] = []
    customers: List[SupplyChainEntity] = []
    manufacturing_partners: List[SupplyChainEntity] = []
    subcontractors: List[SupplyChainEntity] = []
    investments: List[SupplyChainEntity] = []
    risk_map: Optional[Dict[str, List[SupplyChainRisk]]] = None
    graph_network: Optional[Dict[str, Any]] = None
    sources: Optional[Dict[str, List[str]]] = None


class SupplyChainResponse(BaseModel):
    """Schema for supply chain response"""
    ticker: str
    data: SupplyChainData
    graph_file: Optional[str] = None
    graph_url: Optional[str] = None
    saved_to_db: bool = False
    profile_id: Optional[str] = None
    
    class Config:
        from_attributes = True

