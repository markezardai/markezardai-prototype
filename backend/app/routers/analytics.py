"""
Campaign analytics router
"""

from fastapi import APIRouter, HTTPException, Depends, status
import logging
from datetime import datetime

from ..models.requests import CampaignAnalyticsRequest
from ..models.responses import CampaignAnalyticsResponse, CampaignMetrics
from ..services.meta_ads_service import meta_ads_service
from ..dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/campaign-analytics", response_model=CampaignAnalyticsResponse)
async def get_campaign_analytics(
    campaign_id: str,
    platform: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get campaign analytics from advertising platform
    """
    try:
        logger.info(f"Getting analytics for campaign {campaign_id} on {platform}")
        
        # Route to appropriate platform service
        if platform.lower() == "meta":
            analytics_data = await meta_ads_service.get_campaign_analytics(campaign_id)
        else:
            # Mock analytics for other platforms
            analytics_data = {
                "campaign_id": campaign_id,
                "platform": platform,
                "metrics": {
                    "impressions": 8500,
                    "clicks": 210,
                    "conversions": 12,
                    "spend": 65.75,
                    "ctr": 2.47,
                    "cpc": 0.31,
                    "roas": 2.8
                },
                "last_updated": datetime.utcnow().isoformat(),
                "data_source": "mock"
            }
        
        # Parse metrics
        metrics_data = analytics_data.get("metrics", {})
        metrics = CampaignMetrics(
            impressions=metrics_data.get("impressions", 0),
            clicks=metrics_data.get("clicks", 0),
            conversions=metrics_data.get("conversions", 0),
            spend=metrics_data.get("spend", 0.0),
            ctr=metrics_data.get("ctr", 0.0),
            cpc=metrics_data.get("cpc", 0.0),
            roas=metrics_data.get("roas", 0.0)
        )
        
        return CampaignAnalyticsResponse(
            campaign_id=campaign_id,
            platform=platform,
            metrics=metrics,
            last_updated=datetime.fromisoformat(analytics_data.get("last_updated", datetime.utcnow().isoformat())),
            data_source=analytics_data.get("data_source", "unknown")
        )
        
    except Exception as e:
        logger.error(f"Analytics retrieval failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analytics retrieval failed: {str(e)}"
        )
