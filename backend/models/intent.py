from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
import uuid

class Intent(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    description: Optional[str] = None
    prompt: str  # Custom prompt for this intent
    keywords: List[str] = []  # Keywords to help detect this intent
    auto_send: bool = False  # Auto-send replies for this intent
    priority: int = 0  # Higher priority intents checked first
    is_default: bool = False  # Default intent for unmatched emails
    is_inbound_lead: bool = False  # Mark this intent as inbound lead
    
    # Lead Qualification & Nurturing (New Feature)
    enable_lead_qualification: bool = False  # Enable qualification for this intent
    enable_lead_nurturing: bool = False  # Enable nurturing for this intent
    
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class IntentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    prompt: str
    keywords: List[str] = []
    auto_send: bool = False
    priority: int = 0

class IntentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    prompt: Optional[str] = None
    keywords: Optional[List[str]] = None
    auto_send: Optional[bool] = None
    priority: Optional[int] = None
    is_inbound_lead: Optional[bool] = None
    enable_lead_qualification: Optional[bool] = None
    enable_lead_nurturing: Optional[bool] = None
    is_active: Optional[bool] = None

class IntentResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    prompt: str
    keywords: List[str]
    auto_send: bool
    priority: int
    is_inbound_lead: bool
    enable_lead_qualification: bool
    enable_lead_nurturing: bool
    is_active: bool
    created_at: str
