"""
Website integration and analysis router
"""

from fastapi import APIRouter, HTTPException, Depends, status
import logging

from ..models.requests import WebsiteIntegrationRequest, WebsiteAnalysisRequest, PlatformSuggestionsRequest
from ..models.responses import WebsiteIntegrationResponse, WebsiteAnalysisResponse, PlatformSuggestionsResponse
from ..services.website_service import website_service
from ..services.ai_service import call_gemini, GeminiConfig
from ..dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/integrate-website", response_model=WebsiteIntegrationResponse)
async def integrate_website(
    request: WebsiteIntegrationRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Integrate with a website and extract products and metadata
    """
    try:
        logger.info(f"Integrating website: {request.url} (platform: {request.platform})")
        
        result = await website_service.integrate_website(
            platform=request.platform.value,
            url=str(request.url),
            oauth=request.oauth
        )
        
        logger.info(f"Successfully integrated website: {len(result.products)} products found")
        return result
        
    except Exception as e:
        logger.error(f"Website integration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Website integration failed: {str(e)}"
        )

@router.post("/analyse-website", response_model=WebsiteAnalysisResponse)
async def analyse_website(
    request: WebsiteAnalysisRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Analyze website data using Gemini AI
    """
    try:
        logger.info("Analyzing website data with Gemini AI")
        
        # Construct analysis prompt
        site_data = request.site_data
        products = site_data.get("products", [])
        site_meta = site_data.get("site_meta", {})
        
        prompt = f"""
        Analyze this e-commerce website and provide insights:
        
        Website: {site_meta.get('title', 'Unknown')}
        Description: {site_meta.get('description', 'No description')}
        
        Products ({len(products)} total):
        {chr(10).join([f"- {p.get('name', 'Unknown')}: {p.get('description', 'No description')[:100]}..." for p in products[:5]])}
        
        Please provide a JSON response with:
        {{
            "strengths": ["strength1", "strength2", ...],
            "weaknesses": ["weakness1", "weakness2", ...],
            "improvement_suggestions": ["suggestion1", "suggestion2", ...],
            "product_positioning": "detailed positioning analysis"
        }}
        """
        
        # Call Gemini AI
        config = GeminiConfig(temperature=0.7, max_tokens=1500)
        analysis_result = await call_gemini(
            prompt=prompt,
            config=config,
            structured_output=True
        )
        
        if isinstance(analysis_result, dict) and "strengths" in analysis_result:
            return WebsiteAnalysisResponse(
                strengths=analysis_result.get("strengths", []),
                weaknesses=analysis_result.get("weaknesses", []),
                improvement_suggestions=analysis_result.get("improvement_suggestions", []),
                product_positioning=analysis_result.get("product_positioning", "")
            )
        else:
            # Fallback response
            return WebsiteAnalysisResponse(
                strengths=["Professional website design", "Clear product catalog"],
                weaknesses=["Limited analysis available", "API integration needed"],
                improvement_suggestions=["Add customer reviews", "Improve SEO optimization"],
                product_positioning="Products appear to target quality-conscious consumers"
            )
        
    except Exception as e:
        logger.error(f"Website analysis failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Website analysis failed: {str(e)}"
        )

@router.get("/platform-suggestions", response_model=PlatformSuggestionsResponse)
async def get_platform_suggestions(
    product_type: str = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get platform suggestions based on product type
    """
    try:
        logger.info(f"Getting platform suggestions for product type: {product_type}")
        
        # Construct platform analysis prompt
        prompt = f"""
        Analyze the best advertising platforms for this product type: {product_type or 'general e-commerce products'}
        
        Consider factors like:
        - Target audience demographics
        - Platform reach and engagement
        - Cost effectiveness
        - Ad format suitability
        - Competition levels
        
        Provide a JSON response with platform suggestions:
        {{
            "suggestions": [
                {{
                    "platform": "Meta",
                    "score": 85,
                    "rationale": "Excellent targeting options and visual ad formats",
                    "estimated_reach": 2500000,
                    "cost_effectiveness": "high"
                }},
                ...
            ]
        }}
        
        Include platforms: Meta, Google, TikTok, LinkedIn, X (Twitter)
        Score each platform 0-100 based on suitability.
        """
        
        # Call Gemini AI
        config = GeminiConfig(temperature=0.6, max_tokens=1200)
        suggestions_result = await call_gemini(
            prompt=prompt,
            config=config,
            structured_output=True
        )
        
        if isinstance(suggestions_result, dict) and "suggestions" in suggestions_result:
            return PlatformSuggestionsResponse(
                suggestions=suggestions_result["suggestions"]
            )
        else:
            # Fallback suggestions
            return PlatformSuggestionsResponse(
                suggestions=[
                    {
                        "platform": "Meta",
                        "score": 90,
                        "rationale": "Excellent visual ad formats and precise targeting",
                        "estimated_reach": 2500000,
                        "cost_effectiveness": "high"
                    },
                    {
                        "platform": "Google",
                        "score": 85,
                        "rationale": "High-intent search traffic and shopping ads",
                        "estimated_reach": 1800000,
                        "cost_effectiveness": "high"
                    },
                    {
                        "platform": "TikTok",
                        "score": 75,
                        "rationale": "Great for reaching younger demographics",
                        "estimated_reach": 1200000,
                        "cost_effectiveness": "medium"
                    }
                ]
            )
        
    except Exception as e:
        logger.error(f"Platform suggestions failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Platform suggestions failed: {str(e)}"
        )
