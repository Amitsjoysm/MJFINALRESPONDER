from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
import uuid

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    password_hash: str
    full_name: Optional[str] = None
    quota: int = 100  # emails per day
    quota_used: int = 0
    quota_reset_date: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    # Role and permissions
    role: str = "user"  # "user", "admin", "super_admin"
    is_active: bool = True
    
    # HubSpot integration fields
    hubspot_enabled: bool = False  # Admin grants access to use HubSpot
    hubspot_connected: bool = False  # User has connected their HubSpot account
    hubspot_access_token: Optional[str] = None
    hubspot_refresh_token: Optional[str] = None
    hubspot_token_expires_at: Optional[str] = None
    hubspot_portal_id: Optional[str] = None  # HubSpot account ID
    hubspot_auto_sync: bool = False  # Auto-sync leads to HubSpot
    
    # Lead Qualification & Nurturing Global Settings (New Feature)
    global_lead_qualification_enabled: bool = False  # Global toggle for qualification
    global_lead_nurturing_enabled: bool = False  # Global toggle for nurturing
    default_qualification_criteria_id: Optional[str] = None  # Default criteria to use
    default_nurturing_config_id: Optional[str] = None  # Default nurturing config to use
    
    # Calendar & Timezone Preferences
    timezone: str = "UTC"  # User's preferred timezone (e.g., "America/New_York", "Europe/London")
    working_hours_start: str = "09:00"  # Working hours start time (24h format)
    working_hours_end: str = "17:00"  # Working hours end time (24h format)
    working_days: List[int] = [1, 2, 3, 4, 5]  # Monday=1 to Sunday=7

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    quota: int
    quota_used: int
    quota_reset_date: str
    created_at: str
    role: str
    is_active: bool
    hubspot_enabled: bool
    hubspot_connected: bool
    hubspot_portal_id: Optional[str]
    hubspot_auto_sync: bool
    global_lead_qualification_enabled: bool
    global_lead_nurturing_enabled: bool
    default_qualification_criteria_id: Optional[str]
    default_nurturing_config_id: Optional[str]

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
