from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
import uuid

class KnowledgeBase(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    content: str
    category: Optional[str] = None
    tags: List[str] = []
    
    # Embedding for RAG (would be computed)
    embedding: Optional[List[float]] = None
    
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class KnowledgeBaseCreate(BaseModel):
    title: str
    content: str
    category: Optional[str] = None
    tags: List[str] = []

class KnowledgeBaseUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None

class KnowledgeBaseResponse(BaseModel):
    id: str
    title: str
    content: str
    category: Optional[str]
    tags: List[str]
    is_active: bool
    created_at: str
