from typing import Optional, Dict
import httpx
import logging
from urllib.parse import urlencode
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone, timedelta

from config import config
from models.email_account import EmailAccount
from models.calendar import CalendarProvider

logger = logging.getLogger(__name__)

class OAuthService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    def get_google_auth_url(self, state: str) -> str:
        """Get Google OAuth authorization URL - uses dynamic redirect URI"""
        params = {
            'client_id': config.GOOGLE_CLIENT_ID,
            'redirect_uri': config.get_dynamic_redirect_uri('google'),
            'response_type': 'code',
            'scope': 'openid email https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/calendar',
            'access_type': 'offline',
            'prompt': 'consent',
            'state': state
        }
        return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    
    def get_microsoft_auth_url(self, state: str) -> str:
        """Get Microsoft OAuth authorization URL - uses dynamic redirect URI"""
        params = {
            'client_id': config.MICROSOFT_CLIENT_ID,
            'redirect_uri': config.get_dynamic_redirect_uri('microsoft'),
            'response_type': 'code',
            'scope': 'openid email https://graph.microsoft.com/User.Read https://graph.microsoft.com/Mail.Read https://graph.microsoft.com/Mail.Send https://graph.microsoft.com/Calendars.ReadWrite offline_access',
            'state': state,
            'prompt': 'consent'
        }
        return f"https://login.microsoftonline.com/{config.MICROSOFT_TENANT_ID}/oauth2/v2.0/authorize?{urlencode(params)}"
    
    async def exchange_google_code(self, code: str) -> Optional[Dict]:
        """Exchange Google authorization code for tokens - uses dynamic redirect URI"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    'https://oauth2.googleapis.com/token',
                    data={
                        'code': code,
                        'client_id': config.GOOGLE_CLIENT_ID,
                        'client_secret': config.GOOGLE_CLIENT_SECRET,
                        'redirect_uri': config.get_dynamic_redirect_uri('google'),
                        'grant_type': 'authorization_code'
                    }
                )
            
            if response.status_code == 200:
                data = response.json()
                
                # Calculate token expiry
                expires_in = data.get('expires_in', 3600)
                expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
                
                return {
                    'access_token': data['access_token'],
                    'refresh_token': data.get('refresh_token'),
                    'token_expires_at': expires_at.isoformat()
                }
            else:
                logger.error(f"Google token exchange failed: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error exchanging Google code: {e}")
            return None
    
    async def exchange_microsoft_code(self, code: str) -> Optional[Dict]:
        """Exchange Microsoft authorization code for tokens - uses dynamic redirect URI"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f'https://login.microsoftonline.com/{config.MICROSOFT_TENANT_ID}/oauth2/v2.0/token',
                    data={
                        'code': code,
                        'client_id': config.MICROSOFT_CLIENT_ID,
                        'client_secret': config.MICROSOFT_CLIENT_SECRET,
                        'redirect_uri': config.get_dynamic_redirect_uri('microsoft'),
                        'grant_type': 'authorization_code'
                    }
                )
            
            if response.status_code == 200:
                data = response.json()
                
                expires_in = data.get('expires_in', 3600)
                expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
                
                return {
                    'access_token': data['access_token'],
                    'refresh_token': data.get('refresh_token'),
                    'token_expires_at': expires_at.isoformat()
                }
            else:
                logger.error(f"Microsoft token exchange failed: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error exchanging Microsoft code: {e}")
            return None
    
    async def refresh_google_token(self, refresh_token: str) -> Optional[Dict]:
        """Refresh Google access token"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    'https://oauth2.googleapis.com/token',
                    data={
                        'refresh_token': refresh_token,
                        'client_id': config.GOOGLE_CLIENT_ID,
                        'client_secret': config.GOOGLE_CLIENT_SECRET,
                        'grant_type': 'refresh_token'
                    }
                )
            
            if response.status_code == 200:
                data = response.json()
                expires_in = data.get('expires_in', 3600)
                expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
                
                return {
                    'access_token': data['access_token'],
                    'token_expires_at': expires_at.isoformat()
                }
            else:
                logger.error(f"Google token refresh failed: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error refreshing Google token: {e}")
            return None
    
    async def get_google_user_email(self, access_token: str) -> Optional[str]:
        """Get user's email from Google"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    'https://www.googleapis.com/oauth2/v2/userinfo',
                    headers={'Authorization': f'Bearer {access_token}'}
                )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('email')
            return None
        except Exception as e:
            logger.error(f"Error getting Google user email: {e}")
            return None
    
    async def refresh_microsoft_token(self, refresh_token: str) -> Optional[Dict]:
        """Refresh Microsoft access token"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f'https://login.microsoftonline.com/{config.MICROSOFT_TENANT_ID}/oauth2/v2.0/token',
                    data={
                        'refresh_token': refresh_token,
                        'client_id': config.MICROSOFT_CLIENT_ID,
                        'client_secret': config.MICROSOFT_CLIENT_SECRET,
                        'grant_type': 'refresh_token'
                    }
                )
            
            if response.status_code == 200:
                data = response.json()
                expires_in = data.get('expires_in', 3600)
                expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
                
                return {
                    'access_token': data['access_token'],
                    'token_expires_at': expires_at.isoformat()
                }
            else:
                logger.error(f"Microsoft token refresh failed: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error refreshing Microsoft token: {e}")
            return None
    
    async def get_microsoft_user_email(self, access_token: str) -> Optional[str]:
        """Get user's email from Microsoft Graph API"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    'https://graph.microsoft.com/v1.0/me',
                    headers={'Authorization': f'Bearer {access_token}'}
                )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('mail') or data.get('userPrincipalName')
            return None
        except Exception as e:
            logger.error(f"Error getting Microsoft user email: {e}")
            return None
