"""
Authentication module for the Data Flywheel Chatbot.
Provides centralized bearer token verification for protected endpoints.
"""

from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import os

security = HTTPBearer()

def verify_bearer_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    Verify bearer token for protected endpoints.
    
    Args:
        credentials: HTTP authorization credentials from Security dependency
        
    Raises:
        RuntimeError: If APP_TOKEN is missing in production environment
        HTTPException: If token is invalid or missing
    """
    token = os.getenv("APP_TOKEN")
    if not token:
        env = os.getenv("ENV", "development")
        if env == "production":
            raise RuntimeError("APP_TOKEN must be set in production")
        return  # dev: allow missing token
    if credentials is None or credentials.credentials != token:
        raise HTTPException(status_code=403, detail="Invalid or missing token")
