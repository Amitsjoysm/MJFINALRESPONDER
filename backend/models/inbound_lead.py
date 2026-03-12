from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Literal, Dict, Any
from datetime import datetime, timezone
import uuid

# Lead Stage State Machine
LeadStage = Literal['awaiting_info', 'new', 'contacted', 'qualified', 'converted', 'unqualified', 'lost']

class LeadActivity(BaseModel):
    """Track activities on a lead"""
    timestamp: str
    activity_type: str  # email_received, email_sent, stage_changed, meeting_scheduled, manual_update
    description: str
    details: Dict[str, Any] = {}
    performed_by: str  # 'system' or 'user' or user_id

class ExtractedData(BaseModel):
    """Structured data extracted from emails"""
    name: Optional[str] = None
    email: Optional[str] = None
    company_name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    job_title: Optional[str] = None
    company_size: Optional[str] = None
    industry: Optional[str] = None
    specific_interests: Optional[str] = None
    requirements: Optional[str] = None
    linkedin_url: Optional[str] = None
    facebook_url: Optional[str] = None
    twitter_url: Optional[str] = None
    website_url: Optional[str] = None
    extraction_confidence: float = 0.0  # 0.0-1.0

class InboundLead(BaseModel):
    """Inbound Lead Model - Parlant.io Architecture"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str  # Owner of the lead (our user)
    
    # Lead Information (extracted from emails)
    lead_name: Optional[str] = None
    lead_email: str  # Primary identifier
    company_name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    job_title: Optional[str] = None
    company_size: Optional[str] = None
    industry: Optional[str] = None
    
    # Social Media & Web Presence
    linkedin_url: Optional[str] = None
    facebook_url: Optional[str] = None
    twitter_url: Optional[str] = None
    website_url: Optional[str] = None
    
    # Lead Details
    specific_interests: Optional[str] = None  # What they're interested in
    requirements: Optional[str] = None  # Their requirements/needs
    source: str = 'email'  # Source of lead
    
    # Stage Management (State Machine)
    stage: LeadStage = 'new'
    stage_changed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    stage_history: List[Dict[str, Any]] = []  # Track stage transitions
    
    # Lead Scoring
    score: int = 0  # 0-100 score based on engagement
    priority: Literal['low', 'medium', 'high', 'urgent'] = 'medium'
    
    # Email Thread Tracking
    initial_email_id: str  # First email from this lead
    thread_id: Optional[str] = None  # Email thread
    email_ids: List[str] = []  # All emails associated with this lead
    intent_id: Optional[str] = None  # Intent that triggered lead creation
    intent_name: Optional[str] = None
    
    # Engagement Metrics
    emails_received: int = 0
    emails_sent: int = 0
    last_contact_at: Optional[str] = None
    last_reply_at: Optional[str] = None
    response_time_avg: Optional[float] = None  # Average response time in hours
    
    # Lead Qualification (New Feature)
    qualification_checked: bool = False  # Has qualification been performed
    qualification_score: int = 0  # Calculated qualification score (0-100)
    qualification_reasons: List[str] = []  # Reasons for qualification/disqualification
    qualification_criteria_id: Optional[str] = None  # Criteria used for qualification
    qualification_attempt: int = 0  # Number of qualification attempts (max 3)
    
    # Lead Nurturing (New Feature)
    nurturing_enabled: bool = False  # Is nurturing active for this lead
    nurturing_exchanges_count: int = 0  # Number of nurturing exchanges completed
    nurturing_questions_asked: List[Dict[str, Any]] = []  # Questions asked with responses
    nurturing_config_id: Optional[str] = None  # Nurturing config used
    last_questions_asked: List[Dict[str, Any]] = []  # Track last questions for rephrasing
    
    # Meeting/Calendar
    meeting_scheduled: bool = False
    meeting_date: Optional[str] = None
    calendar_event_id: Optional[str] = None
    
    # Activity Timeline (Observable Actions)
    activities: List[Dict[str, Any]] = []  # All activities on this lead
    
    # Status
    is_active: bool = True
    conversion_date: Optional[str] = None
    lost_reason: Optional[str] = None
    notes: Optional[str] = None
    
    # Metadata
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class LeadCreate(BaseModel):
    """Create lead from email"""
    user_id: str
    lead_email: str
    initial_email_id: str
    intent_id: Optional[str] = None
    intent_name: Optional[str] = None
    thread_id: Optional[str] = None
    extracted_data: Optional[ExtractedData] = None

class LeadUpdate(BaseModel):
    """Update lead information"""
    lead_name: Optional[str] = None
    company_name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    job_title: Optional[str] = None
    company_size: Optional[str] = None
    industry: Optional[str] = None
    specific_interests: Optional[str] = None
    requirements: Optional[str] = None
    linkedin_url: Optional[str] = None
    facebook_url: Optional[str] = None
    twitter_url: Optional[str] = None
    website_url: Optional[str] = None
    priority: Optional[Literal['low', 'medium', 'high', 'urgent']] = None
    notes: Optional[str] = None

class LeadStageUpdate(BaseModel):
    """Update lead stage"""
    stage: LeadStage
    reason: Optional[str] = None  # Reason for stage change
    performed_by: str = 'user'  # 'system' or user_id

class LeadResponse(BaseModel):
    """Lead response for API"""
    id: str
    user_id: str
    lead_name: Optional[str]
    lead_email: str
    company_name: Optional[str]
    job_title: Optional[str]
    phone: Optional[str]
    stage: str
    score: int
    priority: str
    emails_received: int
    emails_sent: int
    last_contact_at: Optional[str]
    meeting_scheduled: bool
    is_active: bool
    created_at: str
    updated_at: str

class LeadDetailResponse(BaseModel):
    """Detailed lead response with all information"""
    id: str
    user_id: str
    lead_name: Optional[str]
    lead_email: str
    company_name: Optional[str]
    address: Optional[str]
    phone: Optional[str]
    job_title: Optional[str]
    company_size: Optional[str]
    industry: Optional[str]
    specific_interests: Optional[str]
    requirements: Optional[str]
    stage: str
    stage_history: List[Dict[str, Any]]
    score: int
    priority: str
    emails_received: int
    emails_sent: int
    last_contact_at: Optional[str]
    last_reply_at: Optional[str]
    meeting_scheduled: bool
    meeting_date: Optional[str]
    activities: List[Dict[str, Any]]
    notes: Optional[str]
    is_active: bool
    qualification_checked: bool
    qualification_score: int
    qualification_reasons: List[str]
    qualification_attempt: int
    nurturing_enabled: bool
    nurturing_exchanges_count: int
    nurturing_questions_asked: List[Dict[str, Any]]
    created_at: str
    updated_at: str
