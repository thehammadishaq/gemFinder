"""
Pydantic Schemas for Company Profile
Request and Response models for API endpoints
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class CompanyProfileBase(BaseModel):
    """Base company profile schema"""
    pass


class CompanyProfileCreate(BaseModel):
    """Schema for creating/uploading company profile"""
    ticker: str = Field(..., description="Stock ticker symbol", example="AAPL")
    data: Dict[str, Any] = Field(..., description="Company profile data")


class CompanyProfileResponse(BaseModel):
    """Schema for company profile response"""
    id: Optional[str] = Field(None, alias="_id")  # MongoDB uses _id
    ticker: str
    data: Dict[str, Any]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {
            # Handle MongoDB ObjectId serialization
            "ObjectId": str
        }


class CompanyProfileListResponse(BaseModel):
    """Schema for list of company profiles"""
    profiles: List[CompanyProfileResponse]
    total: int
    page: int
    page_size: int


class CompanyProfileUpdate(BaseModel):
    """Schema for updating company profile"""
    data: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Schema for error responses"""
    error: str
    detail: Optional[str] = None
    status_code: int


class SuccessResponse(BaseModel):
    """Schema for success responses"""
    message: str
    data: Optional[Dict[str, Any]] = None
