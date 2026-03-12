"""HubSpot OAuth 2.0 utility"""
import os
import httpx
from fastapi import HTTPException, status
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class HubSpotOAuth:
    """Configuration and methods for HubSpot OAuth 2.0 flow"""
    
    def __init__(self):
        self.client_id = os.getenv("HUBSPOT_CLIENT_ID", "e699d30c-34a8-4632-ae42-19cdf484de89")
        self.client_secret = os.getenv("HUBSPOT_CLIENT_SECRET", "6db6c2c6-110f-4e7e-9f04-dc64870d4de6")
        self.app_id = os.getenv("HUBSPOT_APP_ID", "24418088")
        
        # Get redirect URI from env or construct from backend URL
        backend_url = os.getenv("REACT_APP_BACKEND_URL", "http://localhost:8001")
        self.redirect_uri = os.getenv("HUBSPOT_OAUTH_REDIRECT_URI", f"{backend_url}/api/hubspot/callback")
        
        self.auth_url = "https://app.hubspot.com/oauth/authorize"
        self.token_url = "https://api.hubapi.com/oauth/v1/token"
        
        # HubSpot OAuth scopes for CRM access
        self.scopes = [
            "crm.objects.contacts.read",
            "crm.objects.contacts.write",
            "crm.objects.companies.read",
            "crm.objects.deals.read"
        ]
        
        logger.info(f"HubSpot OAuth initialized with redirect_uri: {self.redirect_uri}")
    
    def get_authorization_url(self, state: str) -> str:
        """Generate HubSpot authorization URL for user consent"""
        scope_string = "%20".join(self.scopes)
        auth_url = (
            f"{self.auth_url}?"
            f"client_id={self.client_id}&"
            f"scope={scope_string}&"
            f"redirect_uri={self.redirect_uri}&"
            f"state={state}"
        )
        logger.info(f"Generated authorization URL with state: {state}")
        return auth_url
    
    async def exchange_code_for_token(self, code: str) -> Dict:
        """Exchange authorization code for access and refresh tokens"""
        logger.info(f"Exchanging code for token...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    self.token_url,
                    data={
                        "grant_type": "authorization_code",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "code": code,
                        "redirect_uri": self.redirect_uri,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                logger.info(f"Token exchange response status: {response.status_code}")
                
                if response.status_code != 200:
                    error_detail = response.text
                    logger.error(f"Token exchange failed: {error_detail}")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=f"Failed to exchange authorization code for token: {error_detail}"
                    )
                
                token_data = response.json()
                logger.info(f"Token exchange successful")
                return token_data
                
            except httpx.HTTPError as e:
                logger.error(f"HTTP error during token exchange: {e}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Failed to connect to HubSpot: {str(e)}"
                )
    
    async def refresh_access_token(self, refresh_token: str) -> Dict:
        """Refresh an expired access token using the refresh token"""
        logger.info("Refreshing access token...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    self.token_url,
                    data={
                        "grant_type": "refresh_token",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "refresh_token": refresh_token,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                if response.status_code != 200:
                    error_detail = response.text
                    logger.error(f"Token refresh failed: {error_detail}")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=f"Failed to refresh access token: {error_detail}"
                    )
                
                token_data = response.json()
                logger.info("Token refresh successful")
                return token_data
                
            except httpx.HTTPError as e:
                logger.error(f"HTTP error during token refresh: {e}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Failed to connect to HubSpot: {str(e)}"
                )
    
    async def get_account_info(self, access_token: str) -> Dict:
        """Get HubSpot account information"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    "https://api.hubapi.com/account-info/v3/api-usage/daily",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"Failed to get account info: {response.status_code}")
                    return {}
            except Exception as e:
                logger.warning(f"Error getting account info: {e}")
                return {}

# Singleton instance
hubspot_oauth = HubSpotOAuth()
