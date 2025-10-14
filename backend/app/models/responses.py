"""
Pydantic models for API responses
"""

from pydantic import BaseModel, HttpUrl, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class HealthResponse(BaseModel):
    status: str
    message: str
    version: str

class UserProfile(BaseModel):
    uid: str
    email: str
    name: Optional[str] = None
    plan: str = "free"
    created_at: Optional[datetime] = None

class TokenVerificationResponse(BaseModel):
    user: UserProfile
    valid: bool

# Website Integration
class Product(BaseModel):
    id: str
    name: str
    description: str
    price: float
    currency: str
    images: List[HttpUrl]
    category: Optional[str] = None

class SiteMeta(BaseModel):
    title: str
    description: str
    logo: Optional[HttpUrl] = None
    favicon: Optional[HttpUrl] = None
    theme_colors: List[str] = []

class WebsiteIntegrationResponse(BaseModel):
    products: List[Product]
    site_meta: SiteMeta
    sample_images: List[HttpUrl]

# Website Analysis
class WebsiteAnalysisResponse(BaseModel):
    strengths: List[str]
    weaknesses: List[str]
    improvement_suggestions: List[str]
    product_positioning: str

# Platform Suggestions
class PlatformSuggestion(BaseModel):
    platform: str
    score: float
    rationale: str
    estimated_reach: int
    cost_effectiveness: str

class PlatformSuggestionsResponse(BaseModel):
    suggestions: List[PlatformSuggestion]

# Untapped Interests
class UntappedInterest(BaseModel):
    interest: str
    success_score: int = Field(ge=0, le=100)
    competition: str  # "low", "medium", "high"
    reasoning: str

# Campaign Generation
class AdVariation(BaseModel):
    headline: str
    description: str
    cta: str

class CampaignDraft(BaseModel):
    primary_copy: AdVariation
    variations: List[AdVariation]
    creative_instructions: str
    untapped_interests: List[UntappedInterest]
    targeting_suggestions: Dict[str, Any]

class CampaignGenerationResponse(BaseModel):
    campaign_draft: CampaignDraft
    estimated_performance: Dict[str, Any]

# Campaign Publishing
class PlatformResponse(BaseModel):
    platform: str
    campaign_id: Optional[str] = None
    status: str
    message: str
    details: Dict[str, Any] = {}

class CampaignPublishResponse(BaseModel):
    publish_mode: str
    platform_response: PlatformResponse
    audit_log_id: str

# Analytics
class CampaignMetrics(BaseModel):
    impressions: int
    clicks: int
    conversions: int
    spend: float
    ctr: float
    cpc: float
    roas: float

class CampaignAnalyticsResponse(BaseModel):
    campaign_id: str
    platform: str
    metrics: CampaignMetrics
    last_updated: datetime
    data_source: str  # "live", "cached", "simulated"
