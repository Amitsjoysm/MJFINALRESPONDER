from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid

class NurturingQuestion(BaseModel):
    """Nurturing question to ask leads"""
    question_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question_text: str
    context_keywords: List[str] = []  # Keywords to trigger this question contextually
    priority: int = 1  # Lower number = ask first
    max_asks: int = 1  # Maximum times to ask this question
    is_required: bool = False  # Must be answered

class LeadNurturingConfig(BaseModel):
    """Lead nurturing configuration"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str  # Owner of this config
    
    # Basic Info
    name: str  # Name for this nurturing config
    description: Optional[str] = None
    
    # Nurturing Configuration
    is_enabled: bool = True
    
    # Questions
    questions: List[NurturingQuestion] = []
    
    # Strategy
    questions_per_email: int = 2  # Number of questions to ask per email (1-2 recommended)
    max_exchanges: int = 2  # Maximum email exchanges before qualification
    use_contextual_questions: bool = True  # Use context-aware question selection
    
    # Behavior
    natural_integration: bool = True  # Weave questions naturally into conversation
    avoid_interrogation: bool = True  # Don't make it feel like an interrogation
    
    # Metadata
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class NurturingConfigCreate(BaseModel):
    """Create new nurturing configuration"""
    name: str
    description: Optional[str] = None
    questions: List[NurturingQuestion] = []
    questions_per_email: int = 2
    max_exchanges: int = 2
    use_contextual_questions: bool = True
    natural_integration: bool = True
    avoid_interrogation: bool = True

class NurturingConfigUpdate(BaseModel):
    """Update nurturing configuration"""
    name: Optional[str] = None
    description: Optional[str] = None
    is_enabled: Optional[bool] = None
    questions: Optional[List[NurturingQuestion]] = None
    questions_per_email: Optional[int] = None
    max_exchanges: Optional[int] = None
    use_contextual_questions: Optional[bool] = None
    natural_integration: Optional[bool] = None
    avoid_interrogation: Optional[bool] = None
    is_active: Optional[bool] = None

class NurturingConfigResponse(BaseModel):
    """Response model for nurturing configuration"""
    id: str
    user_id: str
    name: str
    description: Optional[str]
    is_enabled: bool
    questions: List[Dict[str, Any]]
    questions_per_email: int
    max_exchanges: int
    use_contextual_questions: bool
    natural_integration: bool
    avoid_interrogation: bool
    is_active: bool
    created_at: str
    updated_at: str
