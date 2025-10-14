"""
FastAPI dependencies for authentication and authorization
"""

import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .services.firebase_service import verify_firebase_token

logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify Firebase token and return user info"""
    try:
        token = credentials.credentials
        user_info = await verify_firebase_token(token)
        return user_info
    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
