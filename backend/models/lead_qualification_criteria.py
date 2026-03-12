from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime, timezone
import uuid

# Criteria Types
CriteriaType = Literal['rule_based', 'question_based', 'score_based']
RuleOperator = Literal['equals', 'not_equals', 'contains', 'not_contains', 'greater_than', 'less_than', 'in_list', 'not_in_list']

class QualificationRule(BaseModel):
    """Individual qualification rule"""
    field: str  # company_size, budget, industry, job_title, etc.
    operator: RuleOperator
    value: Any  # Value to compare against
    weight: float = 1.0  # Weight for scoring (0.0-1.0)

class QualificationQuestion(BaseModel):
    """Question to ask for lead qualification"""
    question_text: str
    question_key: str  # Unique identifier for tracking responses
    expected_answer_type: Literal['text', 'number', 'boolean', 'choice']  # Type of answer expected
    qualifying_answers: Optional[List[str]] = None  # List of qualifying answers (for choice type)
    disqualifying_answers: Optional[List[str]] = None  # List of disqualifying answers
    weight: float = 1.0  # Weight for scoring (0.0-1.0)
    is_required: bool = True  # Must be answered for qualification
    priority: int = 1  # Order to ask questions (lower = ask first)

class LeadQualificationCriteria(BaseModel):
    """Lead qualification criteria configuration"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str  # Owner of this criteria
    
    # Basic Info
    name: str  # Name for this criteria set
    description: Optional[str] = None
    
    # Qualification Configuration
    is_enabled: bool = True
    criteria_type: CriteriaType  # rule_based, question_based, score_based
    
    # Rule-based criteria
    rules: List[QualificationRule] = []
    
    # Question-based criteria
    questions: List[QualificationQuestion] = []
    
    # Scoring configuration
    min_qualification_score: float = 0.7  # Minimum score to qualify (0.0-1.0)
    max_exchanges: int = 2  # Maximum email exchanges for qualification
    
    # Auto-actions
    auto_disqualify_on_fail: bool = True  # Auto mark as unqualified if criteria not met
    
    # Metadata
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class QualificationCriteriaCreate(BaseModel):
    """Create new qualification criteria"""
    name: str
    description: Optional[str] = None
    criteria_type: CriteriaType
    rules: List[QualificationRule] = []
    questions: List[QualificationQuestion] = []
    min_qualification_score: float = 0.7
    max_exchanges: int = 2
    auto_disqualify_on_fail: bool = True

class QualificationCriteriaUpdate(BaseModel):
    """Update qualification criteria"""
    name: Optional[str] = None
    description: Optional[str] = None
    is_enabled: Optional[bool] = None
    criteria_type: Optional[CriteriaType] = None
    rules: Optional[List[QualificationRule]] = None
    questions: Optional[List[QualificationQuestion]] = None
    min_qualification_score: Optional[float] = None
    max_exchanges: Optional[int] = None
    auto_disqualify_on_fail: Optional[bool] = None
    is_active: Optional[bool] = None

class QualificationCriteriaResponse(BaseModel):
    """Response model for qualification criteria"""
    id: str
    user_id: str
    name: str
    description: Optional[str]
    is_enabled: bool
    criteria_type: str
    rules: List[Dict[str, Any]]
    questions: List[Dict[str, Any]]
    min_qualification_score: float
    max_exchanges: int
    auto_disqualify_on_fail: bool
    is_active: bool
    created_at: str
    updated_at: str
