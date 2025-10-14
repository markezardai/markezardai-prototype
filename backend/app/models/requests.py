"""
Pydantic models for API requests
"""

from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, Dict, Any, List, Literal
from enum import Enum

class PlatformType(str, Enum):
    SHOPIFY = "shopify"
    WORDPRESS = "wordpress"
    CUSTOM = "custom"

class PublishMode(str, Enum):
    DRY_RUN = "dry_run"
    GO_LIVE = "go_live"

class AdPlatform(str, Enum):
    META = "meta"
    GOOGLE = "google"
    TIKTOK = "tiktok"
    LINKEDIN = "linkedin"
    X = "x"

class CampaignGoal(str, Enum):
    AWARENESS = "awareness"
    TRAFFIC = "traffic"
    CONVERSIONS = "conversions"
    LEADS = "leads"

# Website Integration
class WebsiteIntegrationRequest(BaseModel):
    platform: PlatformType
    url: HttpUrl
    oauth: Optional[Dict[str, Any]] = None

class WebsiteAnalysisRequest(BaseModel):
    site_data: Dict[str, Any]

# Campaign Generation
class CampaignGenerationRequest(BaseModel):
    product: Dict[str, Any]
    platform: AdPlatform
    budget: float = Field(gt=0, description="Campaign budget in USD")
    language: str = Field(default="en", description="Target language code")
    goal: CampaignGoal

class CampaignPublishRequest(BaseModel):
    campaign_draft: Dict[str, Any]
    platform: AdPlatform
    publish_mode: PublishMode = PublishMode.DRY_RUN
    confirm_token: Optional[str] = None

# Platform Suggestions
class PlatformSuggestionsRequest(BaseModel):
    product_type: Optional[str] = None

# Analytics
class CampaignAnalyticsRequest(BaseModel):
    campaign_id: str
    platform: AdPlatform
