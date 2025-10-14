"""
Meta Ads API service with dry-run safety
"""

import os
import json
import logging
import pathlib
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import hashlib
from dotenv import load_dotenv

import aiohttp
import asyncio

# Ensure environment variables are loaded
project_root = pathlib.Path(__file__).parent.parent.parent.parent
load_dotenv(project_root / '.env')

logger = logging.getLogger(__name__)

class MetaAdsService:
    def __init__(self):
        self.access_token = os.getenv('META_ACCESS_TOKEN')
        self.ad_account_id = os.getenv('META_AD_ACCOUNT_ID')
        self.base_url = "https://graph.facebook.com/v18.0"
        self.session_timeout = 30
        
        if not self.access_token:
            raise ValueError("META_ACCESS_TOKEN environment variable is required for production mode")
        if not self.ad_account_id:
            raise ValueError("META_AD_ACCOUNT_ID environment variable is required for production mode")
        
        logger.info(f"✅ Meta Ads service initialized for account: {self.ad_account_id}")
    
    async def publish_campaign(
        self,
        campaign_draft: Dict[str, Any],
        publish_mode: str = "dry_run",
        confirm_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Publish campaign to Meta Ads
        
        Args:
            campaign_draft: Campaign data to publish
            publish_mode: 'dry_run' or 'go_live'
            confirm_token: Required for go_live mode
        
        Returns:
            Platform response with campaign details
        """
        try:
            if publish_mode == "go_live":
                if not confirm_token:
                    return {
                        "platform": "meta",
                        "status": "error",
                        "message": "Confirmation token required for live publishing",
                        "details": {"error_code": "MISSING_CONFIRM_TOKEN"}
                    }
                
                # Validate confirm token (in production, this would be a secure token)
                if not self._validate_confirm_token(confirm_token):
                    return {
                        "platform": "meta",
                        "status": "error",
                        "message": "Invalid confirmation token",
                        "details": {"error_code": "INVALID_CONFIRM_TOKEN"}
                    }
            
            if publish_mode == "dry_run":
                return await self._dry_run_publish(campaign_draft)
            else:
                return await self._live_publish(campaign_draft)
                
        except Exception as e:
            logger.error(f"Meta Ads publishing failed: {str(e)}")
            return {
                "platform": "meta",
                "status": "error",
                "message": f"Publishing failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    async def _dry_run_publish(self, campaign_draft: Dict[str, Any]) -> Dict[str, Any]:
        """Perform dry run validation without actual publishing"""
        try:
            # Validate campaign structure
            validation_errors = self._validate_campaign_draft(campaign_draft)
            if validation_errors:
                return {
                    "platform": "meta",
                    "status": "validation_failed",
                    "message": "Campaign validation failed",
                    "details": {"errors": validation_errors}
                }
            
            # Additional validation for required fields
            if not campaign_draft.get("name"):
                validation_errors.append("Campaign name is required")
            
            if validation_errors:
                return {
                    "platform": "meta",
                    "status": "validation_failed", 
                    "message": "Campaign validation failed",
                    "details": {"errors": validation_errors}
                }
            
            # Test API connectivity
            if await self._test_api_connection():
                return {
                    "platform": "meta",
                    "campaign_id": f"dry_run_{self._generate_campaign_id()}",
                    "status": "dry_run_success",
                    "message": "Campaign validated successfully - ready for live publishing",
                    "details": {
                        "estimated_daily_reach": self._estimate_reach(campaign_draft),
                        "estimated_daily_spend": campaign_draft.get("budget", {}).get("daily_budget", 0),
                        "targeting_audience_size": self._estimate_audience_size(campaign_draft),
                        "validation_passed": True
                    }
                }
            else:
                return {
                    "platform": "meta",
                    "status": "api_error",
                    "message": "API connection test failed",
                    "details": {"error": "Unable to connect to Meta Ads API"}
                }
                
        except Exception as e:
            logger.error(f"Dry run failed: {str(e)}")
            return {
                "platform": "meta",
                "status": "error",
                "message": f"Dry run failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    async def _live_publish(self, campaign_draft: Dict[str, Any]) -> Dict[str, Any]:
        """Publish campaign live to Meta Ads"""
        try:
            # Create campaign
            campaign_response = await self._create_campaign(campaign_draft)
            if not campaign_response.get("success"):
                return {
                    "platform": "meta",
                    "status": "campaign_creation_failed",
                    "message": "Failed to create campaign",
                    "details": campaign_response
                }
            
            campaign_id = campaign_response["id"]
            
            # Create ad set
            adset_response = await self._create_ad_set(campaign_id, campaign_draft)
            if not adset_response.get("success"):
                return {
                    "platform": "meta",
                    "status": "adset_creation_failed",
                    "message": "Failed to create ad set",
                    "details": adset_response
                }
            
            adset_id = adset_response["id"]
            
            # Create ads
            ads_response = await self._create_ads(adset_id, campaign_draft)
            if not ads_response.get("success"):
                return {
                    "platform": "meta",
                    "status": "ads_creation_failed",
                    "message": "Failed to create ads",
                    "details": ads_response
                }
            
            return {
                "platform": "meta",
                "campaign_id": campaign_id,
                "status": "live_published",
                "message": "Campaign published successfully",
                "details": {
                    "campaign_id": campaign_id,
                    "adset_id": adset_id,
                    "ad_ids": ads_response.get("ad_ids", []),
                    "published_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Live publishing failed: {str(e)}")
            return {
                "platform": "meta",
                "status": "error",
                "message": f"Live publishing failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    async def _create_campaign(self, campaign_draft: Dict[str, Any]) -> Dict[str, Any]:
        """Create Meta Ads campaign"""
        url = f"{self.base_url}/{self.ad_account_id}/campaigns"
        
        campaign_data = {
            "name": campaign_draft.get("name", "MarkezardAI Campaign"),
            "objective": self._map_objective(campaign_draft.get("goal", "conversions")),
            "status": "PAUSED",  # Start paused for safety
            "access_token": self.access_token
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.session_timeout)) as session:
            async with session.post(url, data=campaign_data) as response:
                result = await response.json()
                if response.status == 200 and result.get("id"):
                    return {"success": True, "id": result["id"]}
                else:
                    return {"success": False, "error": result}
    
    async def _create_ad_set(self, campaign_id: str, campaign_draft: Dict[str, Any]) -> Dict[str, Any]:
        """Create Meta Ads ad set"""
        url = f"{self.base_url}/{self.ad_account_id}/adsets"
        
        targeting = self._build_targeting(campaign_draft)
        budget = campaign_draft.get("budget", {})
        
        adset_data = {
            "name": f"{campaign_draft.get('name', 'Campaign')} - Ad Set",
            "campaign_id": campaign_id,
            "daily_budget": int(budget.get("daily_budget", 1000) * 100),  # Convert to cents
            "billing_event": "IMPRESSIONS",
            "optimization_goal": "CONVERSIONS",
            "targeting": json.dumps(targeting),
            "status": "PAUSED",
            "access_token": self.access_token
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.session_timeout)) as session:
            async with session.post(url, data=adset_data) as response:
                result = await response.json()
                if response.status == 200 and result.get("id"):
                    return {"success": True, "id": result["id"]}
                else:
                    return {"success": False, "error": result}
    
    async def _create_ads(self, adset_id: str, campaign_draft: Dict[str, Any]) -> Dict[str, Any]:
        """Create Meta Ads"""
        url = f"{self.base_url}/{self.ad_account_id}/ads"
        
        ad_ids = []
        primary_copy = campaign_draft.get("primary_copy", {})
        variations = campaign_draft.get("variations", [])
        
        # Create primary ad
        if primary_copy:
            ad_response = await self._create_single_ad(url, adset_id, primary_copy, "Primary")
            if ad_response.get("success"):
                ad_ids.append(ad_response["id"])
        
        # Create variation ads
        for i, variation in enumerate(variations[:2]):  # Limit to 2 variations
            ad_response = await self._create_single_ad(url, adset_id, variation, f"Variation {i+1}")
            if ad_response.get("success"):
                ad_ids.append(ad_response["id"])
        
        if ad_ids:
            return {"success": True, "ad_ids": ad_ids}
        else:
            return {"success": False, "error": "No ads created successfully"}
    
    async def _create_single_ad(self, url: str, adset_id: str, ad_copy: Dict[str, Any], name_suffix: str) -> Dict[str, Any]:
        """Create a single ad"""
        creative_data = {
            "object_story_spec": {
                "page_id": "your_page_id",  # This would be configured
                "link_data": {
                    "message": ad_copy.get("description", ""),
                    "link": "https://example.com",  # This would be the actual landing page
                    "name": ad_copy.get("headline", ""),
                    "call_to_action": {
                        "type": self._map_cta(ad_copy.get("cta", "LEARN_MORE"))
                    }
                }
            }
        }
        
        ad_data = {
            "name": f"MarkezardAI Ad - {name_suffix}",
            "adset_id": adset_id,
            "creative": json.dumps(creative_data),
            "status": "PAUSED",
            "access_token": self.access_token
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.session_timeout)) as session:
            async with session.post(url, data=ad_data) as response:
                result = await response.json()
                if response.status == 200 and result.get("id"):
                    return {"success": True, "id": result["id"]}
                else:
                    return {"success": False, "error": result}
    
    async def _test_api_connection(self) -> bool:
        """Test Meta Ads API connection"""
        try:
            url = f"{self.base_url}/me"
            params = {"access_token": self.access_token}
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(url, params=params) as response:
                    return response.status == 200
                    
        except Exception as e:
            logger.error(f"API connection test failed: {str(e)}")
            return False
    
    async def get_campaign_analytics(self, campaign_id: str) -> Dict[str, Any]:
        """Get campaign analytics from Meta Ads - PRODUCTION MODE ONLY"""
        try:
            url = f"{self.base_url}/{campaign_id}/insights"
            params = {
                "access_token": self.access_token,
                "fields": "impressions,clicks,spend,conversions,ctr,cpc",
                "date_preset": "last_7_days"
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.session_timeout)) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        result = await response.json()
                        data = result.get("data", [])
                        if data:
                            logger.info(f"✅ Retrieved analytics for campaign: {campaign_id}")
                            return self._parse_analytics_data(data[0])
                        else:
                            raise ValueError(f"No analytics data found for campaign: {campaign_id}")
                    else:
                        error_text = await response.text()
                        raise RuntimeError(f"Meta Ads API error {response.status}: {error_text}")
            
        except Exception as e:
            logger.error(f"Failed to get campaign analytics: {str(e)}")
            raise RuntimeError(f"Meta Ads analytics request failed: {str(e)}")
    
    def _validate_campaign_draft(self, campaign_draft: Dict[str, Any]) -> List[str]:
        """Validate campaign draft structure"""
        errors = []
        
        if not campaign_draft.get("primary_copy"):
            errors.append("Missing primary ad copy")
        
        primary_copy = campaign_draft.get("primary_copy", {})
        if not primary_copy.get("headline"):
            errors.append("Missing headline in primary copy")
        if not primary_copy.get("description"):
            errors.append("Missing description in primary copy")
        
        budget = campaign_draft.get("budget", {})
        if not budget.get("daily_budget") or budget.get("daily_budget", 0) <= 0:
            errors.append("Invalid or missing daily budget")
        
        return errors
    
    def _validate_confirm_token(self, token: str) -> bool:
        """Validate confirmation token for live publishing"""
        # In production, this would validate against a secure token store
        # For now, accept any non-empty token
        return bool(token and len(token) > 10)
    
    def _build_targeting(self, campaign_draft: Dict[str, Any]) -> Dict[str, Any]:
        """Build Meta Ads targeting from campaign draft"""
        targeting = {
            "geo_locations": {"countries": ["US"]},
            "age_min": 18,
            "age_max": 65
        }
        
        # Add interest targeting from untapped interests
        interests = campaign_draft.get("untapped_interests", [])
        if interests:
            targeting["interests"] = [
                {"id": str(hash(interest["interest"])), "name": interest["interest"]}
                for interest in interests[:10]  # Limit to 10 interests
            ]
        
        return targeting
    
    def _map_objective(self, goal: str) -> str:
        """Map campaign goal to Meta Ads objective"""
        mapping = {
            "awareness": "BRAND_AWARENESS",
            "traffic": "LINK_CLICKS",
            "conversions": "CONVERSIONS",
            "leads": "LEAD_GENERATION"
        }
        return mapping.get(goal, "CONVERSIONS")
    
    def _map_cta(self, cta: str) -> str:
        """Map CTA text to Meta Ads CTA type"""
        cta_lower = cta.lower()
        if "shop" in cta_lower or "buy" in cta_lower:
            return "SHOP_NOW"
        elif "learn" in cta_lower:
            return "LEARN_MORE"
        elif "sign" in cta_lower:
            return "SIGN_UP"
        else:
            return "LEARN_MORE"
    
    def _estimate_reach(self, campaign_draft: Dict[str, Any]) -> int:
        """Estimate daily reach for campaign"""
        budget = campaign_draft.get("budget", {}).get("daily_budget", 10)
        # Simple estimation: $1 = ~100 reach
        return int(budget * 100)
    
    def _estimate_audience_size(self, campaign_draft: Dict[str, Any]) -> int:
        """Estimate targeting audience size"""
        interests = campaign_draft.get("untapped_interests", [])
        base_size = 1000000  # 1M base
        
        # Reduce size based on number of interests (more specific = smaller audience)
        if interests:
            reduction_factor = max(0.1, 1 - (len(interests) * 0.1))
            base_size = int(base_size * reduction_factor)
        
        return base_size
    
    def _generate_campaign_id(self) -> str:
        """Generate a unique campaign ID"""
        timestamp = str(int(datetime.utcnow().timestamp()))
        hash_input = f"markezard_{timestamp}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:12]
    
    
    def _parse_analytics_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse analytics data from Meta Ads API"""
        return {
            "campaign_id": data.get("campaign_id", ""),
            "platform": "meta",
            "metrics": {
                "impressions": int(data.get("impressions", 0)),
                "clicks": int(data.get("clicks", 0)),
                "conversions": int(data.get("conversions", 0)),
                "spend": float(data.get("spend", 0)),
                "ctr": float(data.get("ctr", 0)),
                "cpc": float(data.get("cpc", 0)),
                "roas": float(data.get("conversions", 0)) * 50 / max(float(data.get("spend", 1)), 1)  # Estimated ROAS
            },
            "last_updated": datetime.utcnow().isoformat(),
            "data_source": "live"
        }

# Global instance
meta_ads_service = MetaAdsService()
