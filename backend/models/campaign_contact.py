from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import uuid

class CampaignContact(BaseModel):
    """Campaign contact with flexible custom fields"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    
    # Standard fields
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    linkedin_url: Optional[str] = None
    company_domain: Optional[str] = None
    
    # Custom flexible fields (any additional data from CSV)
    custom_fields: Dict[str, Any] = {}
    
    # Contact status
    status: str = "active"  # active, unsubscribed, bounced
    
    # Email verification
    email_verified: bool = False
    verification_status: Optional[str] = None  # valid, invalid, unknown
    
    # Engagement tracking
    emails_sent: int = 0
    emails_opened: int = 0
    emails_replied: int = 0
    last_contacted: Optional[str] = None
    
    # Tags for segmentation
    tags: list[str] = []
    
    # Metadata
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class CampaignContactResponse(BaseModel):
    """Response model for campaign contact"""
    id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    linkedin_url: Optional[str] = None
    company_domain: Optional[str] = None
    custom_fields: Dict[str, Any] = {}
    status: str
    email_verified: bool
    verification_status: Optional[str] = None
    emails_sent: int
    emails_opened: int
    emails_replied: int
    last_contacted: Optional[str] = None
    tags: list[str] = []
    created_at: str
    updated_at: str

class CampaignContactCreate(BaseModel):
    """Create model for campaign contact"""
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    linkedin_url: Optional[str] = None
    company_domain: Optional[str] = None
    custom_fields: Dict[str, Any] = {}
    tags: list[str] = []

class CampaignContactUpdate(BaseModel):
    """Update model for campaign contact"""
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    linkedin_url: Optional[str] = None
    company_domain: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    tags: Optional[list[str]] = None

class BulkContactUpload(BaseModel):
    """Model for bulk CSV upload"""
    contacts: list[Dict[str, Any]]
    field_mapping: Dict[str, str]  # Maps CSV columns to contact fields
