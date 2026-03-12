from fastapi import APIRouter, Depends, HTTPException
from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase
from cryptography.fernet import Fernet
import base64
import os

from routes.auth_routes import get_current_user_from_token, get_db
from services.email_service import EmailService
from models.email_account import EmailAccount, EmailAccountCreate, EmailAccountUpdate, EmailAccountResponse
from models.user import User

router = APIRouter(prefix="/email-accounts", tags=["email-accounts"])

# Simple encryption for passwords (use proper key management in production)
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', Fernet.generate_key().decode())
cipher = Fernet(ENCRYPTION_KEY.encode() if len(ENCRYPTION_KEY) == 44 else base64.urlsafe_b64encode(ENCRYPTION_KEY.encode()[:32]))

@router.post("", response_model=EmailAccountResponse)
async def create_email_account(
    account_data: EmailAccountCreate,
    user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Create new email account"""
    # Check if account already exists
    existing = await db.email_accounts.find_one({
        "user_id": user.id,
        "email": account_data.email
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Email account already exists")
    
    # Create account based on type
    if account_data.account_type == 'app_password_gmail':
        if not account_data.app_password:
            raise HTTPException(status_code=400, detail="App password required")
        
        account = EmailAccount(
            user_id=user.id,
            email=account_data.email,
            account_type=account_data.account_type,
            imap_host='imap.gmail.com',
            imap_port=993,
            smtp_host='smtp.gmail.com',
            smtp_port=465,
            password=cipher.encrypt(account_data.app_password.encode()).decode(),
            signature=account_data.signature,
            persona=account_data.persona
        )
    elif account_data.account_type == 'custom_smtp':
        if not all([account_data.imap_host, account_data.smtp_host, account_data.password]):
            raise HTTPException(status_code=400, detail="IMAP/SMTP details required")
        
        account = EmailAccount(
            user_id=user.id,
            email=account_data.email,
            account_type=account_data.account_type,
            imap_host=account_data.imap_host,
            imap_port=account_data.imap_port or 993,
            smtp_host=account_data.smtp_host,
            smtp_port=account_data.smtp_port or 465,
            password=cipher.encrypt(account_data.password.encode()).decode(),
            signature=account_data.signature,
            persona=account_data.persona
        )
    else:
        raise HTTPException(status_code=400, detail="OAuth accounts must be created via OAuth flow")
    
    doc = account.model_dump()
    await db.email_accounts.insert_one(doc)
    
    return EmailAccountResponse(
        id=account.id,
        email=account.email,
        account_type=account.account_type,
        auto_reply_enabled=account.auto_reply_enabled,
        is_active=account.is_active,
        last_sync=account.last_sync,
        sync_status=account.sync_status,
        error_message=account.error_message,
        created_at=account.created_at,
        persona=account.persona,
        signature=account.signature
    )

@router.get("", response_model=List[EmailAccountResponse])
async def list_email_accounts(
    user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """List all email accounts for user"""
    accounts = await db.email_accounts.find({"user_id": user.id}).to_list(100)
    
    return [
        EmailAccountResponse(
            id=acc['id'],
            email=acc['email'],
            account_type=acc['account_type'],
            auto_reply_enabled=acc['auto_reply_enabled'],
            is_active=acc['is_active'],
            last_sync=acc.get('last_sync'),
            sync_status=acc['sync_status'],
            error_message=acc.get('error_message'),
            created_at=acc['created_at'],
            persona=acc.get('persona'),
            signature=acc.get('signature')
        )
        for acc in accounts
    ]

@router.get("/{account_id}", response_model=EmailAccountResponse)
async def get_email_account(
    account_id: str,
    user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get email account details"""
    account_doc = await db.email_accounts.find_one({"id": account_id, "user_id": user.id})
    
    if not account_doc:
        raise HTTPException(status_code=404, detail="Account not found")
    
    return EmailAccountResponse(
        id=account_doc['id'],
        email=account_doc['email'],
        account_type=account_doc['account_type'],
        auto_reply_enabled=account_doc['auto_reply_enabled'],
        is_active=account_doc['is_active'],
        last_sync=account_doc.get('last_sync'),
        sync_status=account_doc['sync_status'],
        error_message=account_doc.get('error_message'),
        created_at=account_doc['created_at'],
        persona=account_doc.get('persona'),
        signature=account_doc.get('signature')
    )

@router.patch("/{account_id}", response_model=EmailAccountResponse)
async def update_email_account(
    account_id: str,
    update_data: EmailAccountUpdate,
    user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Update email account settings"""
    account_doc = await db.email_accounts.find_one({"id": account_id, "user_id": user.id})
    
    if not account_doc:
        raise HTTPException(status_code=404, detail="Account not found")
    
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    
    if update_dict:
        await db.email_accounts.update_one(
            {"id": account_id},
            {"$set": update_dict}
        )
    
    updated_doc = await db.email_accounts.find_one({"id": account_id})
    
    return EmailAccountResponse(
        id=updated_doc['id'],
        email=updated_doc['email'],
        account_type=updated_doc['account_type'],
        auto_reply_enabled=updated_doc['auto_reply_enabled'],
        is_active=updated_doc['is_active'],
        last_sync=updated_doc.get('last_sync'),
        sync_status=updated_doc['sync_status'],
        error_message=updated_doc.get('error_message'),
        created_at=updated_doc['created_at'],
        persona=updated_doc.get('persona'),
        signature=updated_doc.get('signature')
    )

@router.delete("/{account_id}")
async def delete_email_account(
    account_id: str,
    user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Delete email account"""
    result = await db.email_accounts.delete_one({"id": account_id, "user_id": user.id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Account not found")
    
    return {"message": "Account deleted successfully"}

@router.post("/{account_id}/test")
async def test_email_account(
    account_id: str,
    user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Test email account connection"""
    account_doc = await db.email_accounts.find_one({"id": account_id, "user_id": user.id})
    
    if not account_doc:
        raise HTTPException(status_code=404, detail="Account not found")
    
    account = EmailAccount(**account_doc)
    
    # Decrypt password if needed
    if account.password:
        account.password = cipher.decrypt(account.password.encode()).decode()
    
    email_service = EmailService(db)
    
    try:
        if account.account_type == 'oauth_gmail':
            emails = await email_service.fetch_emails_oauth_gmail(account)
        else:
            emails = await email_service.fetch_emails_imap(account)
        
        return {
            "success": True,
            "message": f"Successfully connected. Found {len(emails)} emails."
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Connection failed: {str(e)}"
        }
