"""
Authentication router
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import logging

from ..services.firebase_service import firebase_service
from ..models.responses import TokenVerificationResponse, UserProfile

logger = logging.getLogger(__name__)

router = APIRouter()

class TokenVerificationRequest(BaseModel):
    token: str

@router.post("/verify-token", response_model=TokenVerificationResponse)
async def verify_token(request: TokenVerificationRequest):
    """
    Verify Firebase ID token and return user profile
    """
    try:
        user_info = await firebase_service.verify_token(request.token)
        
        user_profile = UserProfile(
            uid=user_info["uid"],
            email=user_info["email"],
            name=user_info.get("name"),
            plan=user_info.get("plan", "free"),
            created_at=user_info.get("created_at")
        )
        
        return TokenVerificationResponse(
            user=user_profile,
            valid=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
