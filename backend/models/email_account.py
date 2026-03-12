from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, Literal
from datetime import datetime, timezone
import uuid

class EmailAccount(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    email: EmailStr
    account_type: Literal['oauth_gmail', 'oauth_outlook', 'app_password_gmail', 'custom_smtp']
    
    # OAuth fields
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[str] = None
    
    # IMAP/SMTP fields
    imap_host: Optional[str] = None
    imap_port: Optional[int] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    password: Optional[str] = None  # encrypted
    
    # Settings
    auto_reply_enabled: bool = False
    signature: Optional[str] = None
    persona: Optional[str] = None
    
    # Follow-up settings
    follow_up_enabled: bool = True
    follow_up_days: int = 2  # Days to wait before first follow-up
    follow_up_count: int = 3  # Maximum number of follow-ups
    
    # Status
    is_active: bool = True
    last_sync: Optional[str] = None
    sync_status: str = 'pending'  # pending, syncing, success, error
    error_message: Optional[str] = None
    
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class EmailAccountCreate(BaseModel):
    email: EmailStr
    account_type: Literal['oauth_gmail', 'oauth_outlook', 'app_password_gmail', 'custom_smtp']
    
    # For app_password_gmail
    app_password: Optional[str] = None
    
    # For custom_smtp
    imap_host: Optional[str] = None
    imap_port: Optional[int] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    password: Optional[str] = None
    
    # Settings
    signature: Optional[str] = None
    persona: Optional[str] = None

class EmailAccountUpdate(BaseModel):
    auto_reply_enabled: Optional[bool] = None
    signature: Optional[str] = None
    persona: Optional[str] = None
    is_active: Optional[bool] = None
    follow_up_enabled: Optional[bool] = None
    follow_up_days: Optional[int] = None
    follow_up_count: Optional[int] = None

class EmailAccountResponse(BaseModel):
    id: str
    email: str
    account_type: str
    auto_reply_enabled: bool
    is_active: bool
    last_sync: Optional[str]
    sync_status: str
    error_message: Optional[str]
    created_at: str
    persona: Optional[str] = None
    signature: Optional[str] = None
    follow_up_enabled: bool = True
    follow_up_days: int = 2
    follow_up_count: int = 3
