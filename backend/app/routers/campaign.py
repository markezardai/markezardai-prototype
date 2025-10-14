"""
Campaign generation and publishing router
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request
import logging
from datetime import datetime

from ..models.requests import CampaignGenerationRequest, CampaignPublishRequest
from ..models.responses import CampaignGenerationResponse, CampaignPublishResponse, CampaignDraft, AdVariation, UntappedInterest
from ..services.ai_service import call_gemini, GeminiConfig
from ..services.meta_ads_service import meta_ads_service
from ..services.firebase_service import firebase_service
from ..dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/generate-campaign", response_model=CampaignGenerationResponse)
async def generate_campaign(
    request: CampaignGenerationRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate campaign using Gemini AI with untapped interests
    """
    try:
        logger.info(f"Generating campaign for platform: {request.platform}")
        
        product = request.product
        platform = request.platform.value
        budget = request.budget
        language = request.language
        goal = request.goal.value
        
        # Construct campaign generation prompt
        prompt = f"""
        Generate a comprehensive advertising campaign for this product:
        
        Product Details:
        - Name: {product.get('name', 'Unknown Product')}
        - Description: {product.get('description', 'No description')}
        - Price: ${product.get('price', 0)} {product.get('currency', 'USD')}
        - Category: {product.get('category', 'General')}
        
        Campaign Parameters:
        - Platform: {platform}
        - Budget: ${budget}/day
        - Language: {language}
        - Goal: {goal}
        
        Generate a JSON response with:
        {{
            "primary_copy": {{
                "headline": "compelling headline",
                "description": "engaging description",
                "cta": "call to action"
            }},
            "variations": [
                {{
                    "headline": "variation headline",
                    "description": "variation description", 
                    "cta": "variation cta"
                }}
            ],
            "creative_instructions": "detailed creative guidance",
            "untapped_interests": [
                {{
                    "interest": "specific interest name",
                    "success_score": 85,
                    "competition": "low|medium|high",
                    "reasoning": "why this interest has potential"
                }}
            ],
            "targeting_suggestions": {{
                "demographics": {{}},
                "behaviors": [],
                "lookalike_audiences": []
            }}
        }}
        
        Requirements:
        - Create 3 ad variations total (1 primary + 2 variations)
        - Generate at least 10 untapped interests with success scores 0-100
        - Focus on interests with low-medium competition
        - Provide detailed reasoning for each interest
        - Make copy compelling and platform-appropriate
        """
        
        # Call Gemini AI
        config = GeminiConfig(temperature=0.8, max_tokens=2500)
        try:
            campaign_result = await call_gemini(
                prompt=prompt,
                config=config,
                structured_output=True
            )
        except Exception as e:
            logger.error(f"Gemini AI call failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service temporarily unavailable"
            )
        
        if isinstance(campaign_result, dict) and "primary_copy" in campaign_result:
            # Parse the response with error handling
            try:
                primary_copy = AdVariation(**campaign_result["primary_copy"])
                
                variations = []
                for var_data in campaign_result.get("variations", []):
                    variations.append(AdVariation(**var_data))
                
                untapped_interests = []
                for interest_data in campaign_result.get("untapped_interests", []):
                    untapped_interests.append(UntappedInterest(**interest_data))
            except Exception as e:
                logger.error(f"Failed to parse campaign result: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to parse AI response"
                )
            
            campaign_draft = CampaignDraft(
                primary_copy=primary_copy,
                variations=variations,
                creative_instructions=campaign_result.get("creative_instructions", ""),
                untapped_interests=untapped_interests,
                targeting_suggestions=campaign_result.get("targeting_suggestions", {})
            )
            
            # Add budget and platform info to draft
            campaign_draft_dict = campaign_draft.dict()
            campaign_draft_dict.update({
                "budget": {"daily_budget": budget},
                "platform": platform,
                "goal": goal,
                "name": f"{product.get('name', 'Product')} - {platform.title()} Campaign"
            })
            
            return CampaignGenerationResponse(
                campaign_draft=campaign_draft,
                estimated_performance={
                    "estimated_daily_reach": int(budget * 100),  # Simple estimation
                    "estimated_ctr": 2.5,
                    "estimated_conversions": max(1, int(budget * 0.02)),
                    "confidence_score": min(95, 70 + len(untapped_interests))
                }
            )
        else:
            # Fallback campaign
            return CampaignGenerationResponse(
                campaign_draft=CampaignDraft(
                    primary_copy=AdVariation(
                        headline=f"Discover {product.get('name', 'Amazing Products')}",
                        description=f"Premium quality {product.get('category', 'products')} at unbeatable prices",
                        cta="Shop Now"
                    ),
                    variations=[
                        AdVariation(
                            headline=f"Transform Your Life with {product.get('name', 'Our Products')}",
                            description="Experience the difference quality makes",
                            cta="Learn More"
                        )
                    ],
                    creative_instructions="Use high-quality product images with lifestyle context",
                    untapped_interests=[
                        UntappedInterest(
                            interest="quality conscious consumers",
                            success_score=80,
                            competition="medium",
                            reasoning="Growing segment focused on product quality over price"
                        )
                    ],
                    targeting_suggestions={"demographics": {"age_range": "25-54"}}
                ),
                estimated_performance={
                    "estimated_daily_reach": int(budget * 100),
                    "estimated_ctr": 2.0,
                    "estimated_conversions": max(1, int(budget * 0.015)),
                    "confidence_score": 75
                }
            )
        
    except Exception as e:
        logger.error(f"Campaign generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Campaign generation failed: {str(e)}"
        )

@router.post("/publish-campaign", response_model=CampaignPublishResponse)
async def publish_campaign(
    request: CampaignPublishRequest,
    http_request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Publish campaign to advertising platform
    """
    try:
        logger.info(f"Publishing campaign to {request.platform} (mode: {request.publish_mode})")
        
        platform = request.platform.value
        publish_mode = request.publish_mode.value
        campaign_draft = request.campaign_draft
        confirm_token = request.confirm_token
        
        # Log audit event
        audit_details = {
            "platform": platform,
            "publish_mode": publish_mode,
            "campaign_name": campaign_draft.get("name", "Unknown"),
            "ip_address": http_request.client.host if http_request.client else "unknown",
            "user_agent": http_request.headers.get("user-agent", "unknown")
        }
        
        audit_log_id = await firebase_service.log_audit_event(
            user_id=current_user["uid"],
            event_type="campaign_publish_attempt",
            details=audit_details
        )
        
        # Route to appropriate platform service
        if platform == "meta":
            platform_response = await meta_ads_service.publish_campaign(
                campaign_draft=campaign_draft,
                publish_mode=publish_mode,
                confirm_token=confirm_token
            )
        else:
            # For other platforms, return mock response
            platform_response = {
                "platform": platform,
                "status": "not_implemented",
                "message": f"{platform.title()} integration not yet implemented",
                "details": {"mock_mode": True}
            }
        
        # Update audit log with result
        audit_details["result"] = platform_response["status"]
        await firebase_service.log_audit_event(
            user_id=current_user["uid"],
            event_type="campaign_publish_result",
            details=audit_details
        )
        
        return CampaignPublishResponse(
            publish_mode=publish_mode,
            platform_response=platform_response,
            audit_log_id=audit_log_id
        )
        
    except Exception as e:
        logger.error(f"Campaign publishing failed: {str(e)}")
        
        # Log error in audit
        try:
            await firebase_service.log_audit_event(
                user_id=current_user["uid"],
                event_type="campaign_publish_error",
                details={"error": str(e), "platform": request.platform.value}
            )
        except:
            pass
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Campaign publishing failed: {str(e)}"
        )
