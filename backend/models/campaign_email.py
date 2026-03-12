from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal, List
from datetime import datetime, timezone
import uuid

class CampaignEmail(BaseModel):
    """Individual email sent as part of a campaign"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    campaign_id: str
    contact_id: str
    
    # Email details
    email_account_id: str  # Which account was used to send
    to_email: str
    subject: str
    body: str
    
    # Relationship
    email_id: Optional[str] = None  # Link to main Email model if sent
    thread_id: Optional[str] = None  # Email thread ID
    
    # Email type
    email_type: Literal["initial", "follow_up_1", "follow_up_2", "follow_up_3"] = "initial"
    follow_up_number: Optional[int] = None  # Which follow-up (1, 2, 3, etc.)
    parent_campaign_email_id: Optional[str] = None  # Link to initial email for follow-ups
    
    # Status
    status: Literal["pending", "scheduled", "sending", "sent", "failed", "cancelled"] = "pending"
    
    # Scheduling
    scheduled_at: Optional[str] = None
    sent_at: Optional[str] = None
    
    # Tracking
    opened: bool = False
    opened_at: Optional[str] = None
    open_count: int = 0  # Number of times opened
    
    clicked: bool = False  # New: Track if any link was clicked
    clicked_at: Optional[str] = None
    click_count: int = 0  # Number of clicks
    links_clicked: List[str] = []  # Which links were clicked
    
    replied: bool = False
    replied_at: Optional[str] = None
    reply_content: Optional[str] = None  # Store reply for analysis
    reply_sentiment: Optional[Literal["positive", "neutral", "negative"]] = None
    
    # Lead qualification from reply
    is_lead: bool = False
    lead_score: Optional[int] = None  # 0-100
    is_opportunity: bool = False  # Expressed interest
    is_converted: bool = False  # Meeting booked / deal closed
    
    bounced: bool = False
    bounce_reason: Optional[str] = None
    bounce_type: Optional[Literal["hard", "soft"]] = None
    
    # Error handling
    error_message: Optional[str] = None
    retry_count: int = 0
    
    # Metadata
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class CampaignEmailResponse(BaseModel):
    """Response model for campaign email"""
    id: str
    campaign_id: str
    contact_id: str
    email_account_id: str
    to_email: str
    subject: str
    email_type: str
    follow_up_number: Optional[int] = None
    status: str
    scheduled_at: Optional[str] = None
    sent_at: Optional[str] = None
    opened: bool
    opened_at: Optional[str] = None
    replied: bool
    replied_at: Optional[str] = None
    bounced: bool
    bounce_reason: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str
    updated_at: str
