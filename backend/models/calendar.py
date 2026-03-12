from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Literal
from datetime import datetime, timezone
import uuid

class CalendarProvider(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    provider: Literal['google', 'microsoft'] = 'google'
    email: str
    
    # OAuth
    access_token: str
    refresh_token: str
    token_expires_at: str
    
    is_active: bool = True
    last_sync: Optional[str] = None
    
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class CalendarEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    calendar_provider_id: str
    email_id: Optional[str] = None  # Linked email
    thread_id: Optional[str] = None  # Thread ID for sending reminders in same conversation
    
    # Event details
    event_id: str  # Provider's event ID
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    
    start_time: str
    end_time: str
    timezone: str = 'UTC'
    
    attendees: List[str] = []
    
    # Meeting links
    meet_link: Optional[str] = None  # Google Meet or other video conference link
    html_link: Optional[str] = None  # Link to view event in calendar
    
    # Meeting detection
    detected_from_email: bool = False
    confidence: Optional[float] = None
    
    # Conflict tracking
    has_conflicts: bool = False
    conflicts: List[dict] = []
    
    # Reminder
    reminder_sent: bool = False
    reminder_sent_at: Optional[str] = None
    
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class CalendarEventCreate(BaseModel):
    calendar_provider_id: str
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    start_time: str
    end_time: str
    timezone: str = 'UTC'
    attendees: List[str] = []

class CalendarEventResponse(BaseModel):
    id: str
    calendar_provider_id: str
    title: str
    description: Optional[str]
    location: Optional[str]
    start_time: str
    end_time: str
    attendees: List[str]
    detected_from_email: bool
    created_at: str
