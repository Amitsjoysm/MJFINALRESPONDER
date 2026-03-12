from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
import uuid

class CampaignTemplate(BaseModel):
    """Email template with personalization tags"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    
    # Template details
    name: str
    description: Optional[str] = None
    
    # Email content
    subject: str  # Can contain {{tags}}
    body: str  # Can contain {{tags}} for personalization
    
    # Available personalization tags
    # {{email}}, {{first_name}}, {{last_name}}, {{company}}, {{title}}, 
    # {{linkedin_url}}, {{company_domain}}, {{custom_field_name}}
    available_tags: List[str] = [
        "email", "first_name", "last_name", "company", 
        "title", "linkedin_url", "company_domain"
    ]
    
    # Template type
    template_type: str = "initial"  # initial, follow_up_1, follow_up_2, etc.
    
    # Usage tracking
    times_used: int = 0
    
    # Status
    is_active: bool = True
    
    # Metadata
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class CampaignTemplateResponse(BaseModel):
    """Response model for campaign template"""
    id: str
    name: str
    description: Optional[str] = None
    subject: str
    body: str
    available_tags: List[str]
    template_type: str
    times_used: int
    is_active: bool
    created_at: str
    updated_at: str

class CampaignTemplateCreate(BaseModel):
    """Create model for campaign template"""
    name: str
    description: Optional[str] = None
    subject: str
    body: str
    template_type: str = "initial"

class CampaignTemplateUpdate(BaseModel):
    """Update model for campaign template"""
    name: Optional[str] = None
    description: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    template_type: Optional[str] = None
    is_active: Optional[bool] = None
