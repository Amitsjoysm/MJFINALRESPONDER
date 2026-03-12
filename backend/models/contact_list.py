from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
import uuid

class ContactList(BaseModel):
    """Contact list for grouping contacts"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    
    # List details
    name: str
    description: Optional[str] = None
    
    # Contacts in this list
    contact_ids: List[str] = []
    
    # Stats
    total_contacts: int = 0
    
    # Metadata
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ContactListResponse(BaseModel):
    """Response model for contact list"""
    id: str
    name: str
    description: Optional[str] = None
    contact_ids: List[str]
    total_contacts: int
    created_at: str
    updated_at: str

class ContactListCreate(BaseModel):
    """Create model for contact list"""
    name: str
    description: Optional[str] = None
    contact_ids: List[str] = []

class ContactListUpdate(BaseModel):
    """Update model for contact list"""
    name: Optional[str] = None
    description: Optional[str] = None
    contact_ids: Optional[List[str]] = None

class ContactListAddContacts(BaseModel):
    """Add contacts to list"""
    contact_ids: List[str]

class ContactListRemoveContacts(BaseModel):
    """Remove contacts from list"""
    contact_ids: List[str]
