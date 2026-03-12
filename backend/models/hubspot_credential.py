from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, timezone
import uuid

class HubSpotCredential(BaseModel):
    """Stores encrypted HubSpot OAuth credentials for each user"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    expires_at: str
    scope: str
    hubspot_portal_id: Optional[str] = None
    is_enabled: bool = True
    connected_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    disconnected_at: Optional[str] = None
    last_sync_at: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class HubSpotCredentialResponse(BaseModel):
    """Response schema for HubSpot credential"""
    id: str
    user_id: str
    token_type: str
    scope: str
    hubspot_portal_id: Optional[str]
    is_enabled: bool
    connected_at: str
    last_sync_at: Optional[str]
    error_message: Optional[str]

class HubSpotConnectionStatus(BaseModel):
    """Status of HubSpot connection"""
    connected: bool
    enabled: bool = False
    connected_at: Optional[str] = None
    last_sync_at: Optional[str] = None
    error_message: Optional[str] = None
