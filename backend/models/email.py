from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Literal, Dict, Any
from datetime import datetime, timezone
import uuid

class ActionHistory(BaseModel):
    """Track each action taken on an email"""
    timestamp: str
    action: str  # classifying, drafting, validating, sending, sent, escalated, error
    details: Dict[str, Any] = {}
    status: str  # success, failed, in_progress

class Email(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    email_account_id: str
    
    # Email fields
    message_id: str  # Provider's message ID
    thread_id: Optional[str] = None
    in_reply_to: Optional[str] = None  # Message ID this is replying to
    references: Optional[List[str]] = None  # Thread references
    from_email: str
    to_email: List[str]
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    subject: str
    body: str
    html_body: Optional[str] = None
    
    # Metadata
    received_at: str
    direction: Literal['inbound', 'outbound'] = 'inbound'
    is_reply: bool = False  # Is this a reply to our sent email?
    
    # Campaign tracking
    campaign_id: Optional[str] = None  # Link to campaign if part of campaign
    campaign_email_id: Optional[str] = None  # Link to CampaignEmail
    
    # AI Processing
    processed: bool = False
    intent_detected: Optional[str] = None
    intent_name: Optional[str] = None  # Human-readable intent name
    intent_confidence: Optional[float] = None
    meeting_detected: bool = False
    meeting_confidence: Optional[float] = None
    
    # Draft & Response
    draft_generated: bool = False
    draft_content: Optional[str] = None
    draft_validated: bool = False
    validation_issues: Optional[List[str]] = None
    draft_retry_count: int = 0  # Track regeneration attempts
    
    # Status tracking
    status: Literal['pending', 'classifying', 'drafting', 'validating', 'sending', 'sent', 'escalated', 'error', 'draft_ready'] = 'pending'
    replied: bool = False
    reply_sent_at: Optional[str] = None
    error_message: Optional[str] = None
    
    # Action history
    action_history: List[Dict[str, Any]] = []
    
    # Follow-up
    requires_follow_up: bool = False
    follow_up_scheduled: bool = False
    
    # Token tracking
    tokens_used: int = 0
    
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class EmailResponse(BaseModel):
    id: str
    email_account_id: str
    from_email: str
    to_email: List[str]
    subject: str
    body: str
    received_at: str
    direction: str
    processed: bool
    intent_detected: Optional[str]
    intent_name: Optional[str]
    intent_confidence: Optional[float]
    meeting_detected: bool
    meeting_confidence: Optional[float]
    draft_generated: bool
    draft_content: Optional[str]
    draft_validated: bool
    validation_issues: Optional[List[str]]
    status: str
    replied: bool
    is_reply: bool
    thread_id: Optional[str]
    action_history: List[Dict[str, Any]]
    error_message: Optional[str]
    created_at: str

class EmailSend(BaseModel):
    email_account_id: str
    to_email: List[str]
    subject: str
    body: str
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
