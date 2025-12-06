from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

class CampaignBase(BaseModel):
    name: str
    product_name: Optional[str] = None
    product_description: str
    target_industry: Optional[str] = None
    target_audience: Optional[str] = None
    company_size: Optional[str] = None
    target_regions: Optional[List[str]] = []

class CampaignCreate(CampaignBase):
    pass

class CampaignUpdate(BaseModel):
    """Schema for updating campaign - all fields optional"""
    name: Optional[str] = None
    product_name: Optional[str] = None
    product_description: Optional[str] = None
    target_industry: Optional[str] = None
    target_audience: Optional[str] = None
    company_size: Optional[str] = None
    target_regions: Optional[List[str]] = None

class CampaignResponse(CampaignBase):
    id: UUID
    status: str
    created_at: datetime
    product_analysis: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class LeadBase(BaseModel):
    company_name: str
    industry: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    
class LeadResponse(LeadBase):
    id: UUID
    ml_score: Optional[float] = None
    ml_confidence: Optional[float] = None
    score_explanation: Optional[List[Dict[str, Any]]] = None
    status: str

    class Config:
        from_attributes = True
