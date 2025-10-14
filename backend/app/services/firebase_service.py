"""
Firebase Authentication and Firestore service
"""

import json
import os
import logging
import pathlib
from typing import Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

import firebase_admin
from firebase_admin import credentials, auth, firestore
from fastapi import HTTPException, status

# Ensure environment variables are loaded
project_root = pathlib.Path(__file__).parent.parent.parent.parent
load_dotenv(project_root / '.env')

logger = logging.getLogger(__name__)

class FirebaseService:
    def __init__(self):
        self.app = None
        self.db = None
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK - PRODUCTION MODE ONLY"""
        service_account_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')
        if not service_account_json:
            raise ValueError("FIREBASE_SERVICE_ACCOUNT_JSON environment variable is required for production mode")
        
        logger.info("Initializing Firebase with production credentials...")
        
        try:
            # Parse service account JSON - handle all escape sequences and control characters
            logger.debug(f"Raw JSON length: {len(service_account_json)}")
            
            # Clean the JSON string by removing/replacing problematic characters
            # First, strip whitespace and BOM
            service_account_json = service_account_json.strip().strip('\ufeff')
            
            # Handle escape sequences in a more robust way
            # Use Python's built-in string decoding for proper handling
            try:
                # Try to decode escape sequences using Python's string_escape codec equivalent
                service_account_json = service_account_json.encode().decode('unicode_escape')
            except (UnicodeDecodeError, AttributeError):
                # Fallback to manual replacement if decode fails
                service_account_json = service_account_json.replace('\\\\n', '\n')
                service_account_json = service_account_json.replace('\\\\r', '\r')
                service_account_json = service_account_json.replace('\\\\t', '\t')
                service_account_json = service_account_json.replace('\\n', '\n')
                service_account_json = service_account_json.replace('\\r', '\r')
                service_account_json = service_account_json.replace('\\t', '\t')
            
            # Remove any remaining control characters that might cause JSON parsing issues
            import re
            # Remove control characters except newlines, carriage returns, and tabs
            service_account_json = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', service_account_json)
            
            logger.debug(f"Cleaned JSON length: {len(service_account_json)}")
            
            # Try to parse the JSON
            service_account_info = json.loads(service_account_json)
            
            # Validate required fields
            required_fields = ['type', 'project_id', 'private_key', 'client_email']
            for field in required_fields:
                if field not in service_account_info:
                    raise ValueError(f"Missing required field '{field}' in Firebase service account JSON")
            
            logger.info(f"Connecting to Firebase project: {service_account_info.get('project_id')}")
            
            cred = credentials.Certificate(service_account_info)
            
            # Initialize Firebase app if not already initialized
            if not firebase_admin._apps:
                self.app = firebase_admin.initialize_app(cred)
                logger.info("✅ Firebase app initialized successfully")
            else:
                self.app = firebase_admin.get_app()
                logger.info("✅ Using existing Firebase app")
            
            # Initialize Firestore
            self.db = firestore.client()
            logger.info("✅ Firestore client connected successfully")
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed at position {e.pos}: {str(e)}")
            # Log a sample of the problematic JSON for debugging (first 200 chars)
            sample = service_account_json[:200] + "..." if len(service_account_json) > 200 else service_account_json
            logger.error(f"JSON sample: {repr(sample)}")
            raise ValueError(f"Firebase service account JSON is malformed at position {e.pos}: {str(e)}")
        except Exception as e:
            logger.error(f"Firebase initialization failed: {str(e)}")
            raise RuntimeError(f"Failed to initialize Firebase: {str(e)}")
    
    async def verify_token(self, id_token: str) -> Dict[str, Any]:
        """Verify Firebase ID token and return user info - PRODUCTION MODE ONLY"""
        if not self.app:
            raise RuntimeError("Firebase is not initialized. Cannot verify tokens.")
        
        try:
            # Verify the ID token with Firebase
            decoded_token = auth.verify_id_token(id_token)
            uid = decoded_token['uid']
            email = decoded_token.get('email', '')
            name = decoded_token.get('name', '')
            
            logger.info(f"✅ Token verified successfully for user: {email}")
            
            # Get or create user profile in Firestore
            user_profile = await self.get_or_create_user_profile(uid, email, name)
            
            return user_profile
            
        except Exception as e:
            logger.error(f"Token verification failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
    
    async def get_or_create_user_profile(self, uid: str, email: str, name: str) -> Dict[str, Any]:
        """Get existing user profile or create new one - PRODUCTION MODE ONLY"""
        if not self.db:
            raise RuntimeError("Firestore is not initialized. Cannot access user profiles.")
        
        try:
            # Check if user exists in Firestore
            user_ref = self.db.collection('users').document(uid)
            user_doc = user_ref.get()
            
            if user_doc.exists:
                user_data = user_doc.to_dict()
                logger.info(f"✅ Retrieved existing user profile for: {email}")
                return {
                    "uid": uid,
                    "email": email,
                    "name": name,
                    "plan": user_data.get("plan", "free"),
                    "created_at": user_data.get("created_at")
                }
            else:
                # Create new user profile in Firestore
                user_data = {
                    "email": email,
                    "name": name,
                    "plan": "free",
                    "created_at": datetime.utcnow(),
                    "campaigns_created": 0,
                    "last_login": datetime.utcnow()
                }
                user_ref.set(user_data)
                logger.info(f"✅ Created new user profile for: {email}")
                
                return {
                    "uid": uid,
                    "email": email,
                    "name": name,
                    "plan": "free",
                    "created_at": user_data["created_at"].isoformat()
                }
                
        except Exception as e:
            logger.error(f"Firestore operation failed: {str(e)}")
            raise RuntimeError(f"Failed to access user profile in Firestore: {str(e)}")
    
    async def log_audit_event(self, user_id: str, event_type: str, details: Dict[str, Any]) -> str:
        """Log audit event to Firestore - PRODUCTION MODE ONLY"""
        if not self.db:
            raise RuntimeError("Firestore is not initialized. Cannot log audit events.")
        
        try:
            audit_data = {
                "user_id": user_id,
                "event_type": event_type,
                "details": details,
                "timestamp": datetime.utcnow(),
                "ip_address": details.get("ip_address", "unknown")
            }
            
            doc_ref = self.db.collection('audit_logs').add(audit_data)
            audit_id = doc_ref[1].id
            logger.info(f"✅ Audit event logged: {event_type} for user {user_id}")
            return audit_id
            
        except Exception as e:
            logger.error(f"Failed to log audit event: {str(e)}")
            raise RuntimeError(f"Failed to log audit event to Firestore: {str(e)}")

# Global instance
firebase_service = FirebaseService()

# Convenience function for dependency injection
async def verify_firebase_token(token: str) -> Dict[str, Any]:
    """Verify Firebase token - convenience function"""
    return await firebase_service.verify_token(token)
