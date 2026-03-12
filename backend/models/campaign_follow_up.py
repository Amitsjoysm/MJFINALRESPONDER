from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal
from datetime import datetime, timezone
import uuid

class CampaignFollowUp(BaseModel):
    """Follow-up task for campaign emails - separate from regular follow-ups"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    campaign_id: str
    contact_id: str
    
    # Relationship
    initial_campaign_email_id: str  # The initial email sent
    thread_id: Optional[str] = None  # Email thread ID
    
    # Follow-up details
    follow_up_number: int  # 1, 2, 3, etc.
    template_id: str  # Template to use for this follow-up
    
    # Scheduling
    scheduled_date: str  # ISO datetime when to send
    days_after_initial: int  # Days after initial email
    
    # Status
    status: Literal["pending", "scheduled", "sent", "cancelled", "failed"] = "pending"
    
    # Cancellation (when contact replies)
    cancelled_reason: Optional[str] = None  # "reply_received", "campaign_stopped", etc.
    cancelled_at: Optional[str] = None
    
    # Execution
    sent_at: Optional[str] = None
    campaign_email_id: Optional[str] = None  # Link to CampaignEmail when sent
    
    # Error handling
    error_message: Optional[str] = None
    retry_count: int = 0
    
    # Metadata
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class CampaignFollowUpResponse(BaseModel):
    """Response model for campaign follow-up"""
    id: str
    campaign_id: str
    contact_id: str
    initial_campaign_email_id: str
    follow_up_number: int
    template_id: str
    scheduled_date: str
    days_after_initial: int
    status: str
    cancelled_reason: Optional[str] = None
    cancelled_at: Optional[str] = None
    sent_at: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str
    updated_at: str
