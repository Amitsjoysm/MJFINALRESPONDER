from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from routes.auth_routes import get_current_user_from_token, get_db
from services.email_service import EmailService
from services.auth_service import AuthService
from models.email import Email, EmailResponse, EmailSend
from models.user import User
from models.email_account import EmailAccount

router = APIRouter(prefix="/emails", tags=["emails"])

@router.get("", response_model=List[EmailResponse])
async def list_emails(
    status: Optional[str] = Query(None),
    account_id: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """List emails with filters"""
    query = {"user_id": user.id}
    
    if status:
        query["status"] = status
    if account_id:
        query["email_account_id"] = account_id
    
    emails = await db.emails.find(query).sort("received_at", -1).limit(limit).to_list(limit)
    
    return [
        EmailResponse(
            id=email['id'],
            email_account_id=email['email_account_id'],
            from_email=email['from_email'],
            to_email=email['to_email'],
            subject=email['subject'],
            body=email['body'],
            received_at=email['received_at'],
            direction=email['direction'],
            processed=email['processed'],
            intent_detected=email.get('intent_detected'),
            intent_name=email.get('intent_name'),
            intent_confidence=email.get('intent_confidence'),
            meeting_detected=email['meeting_detected'],
            meeting_confidence=email.get('meeting_confidence'),
            draft_generated=email['draft_generated'],
            draft_content=email.get('draft_content'),
            draft_validated=email.get('draft_validated', False),
            validation_issues=email.get('validation_issues', []),
            status=email['status'],
            replied=email['replied'],
            is_reply=email.get('is_reply', False),
            thread_id=email.get('thread_id'),
            action_history=email.get('action_history', []),
            error_message=email.get('error_message'),
            created_at=email['created_at']
        )
        for email in emails
    ]

@router.get("/stats")
async def get_email_stats(
    user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get email statistics"""
    total = await db.emails.count_documents({"user_id": user.id})
    sent = await db.emails.count_documents({"user_id": user.id, "replied": True})
    escalated = await db.emails.count_documents({"user_id": user.id, "status": "escalated"})
    active_accounts = await db.email_accounts.count_documents({"user_id": user.id, "is_active": True})
    total_accounts = await db.email_accounts.count_documents({"user_id": user.id})
    
    return {
        "total_emails": total,
        "sent_emails": sent,
        "escalated": escalated,
        "active_accounts": active_accounts,
        "total_accounts": total_accounts
    }

@router.get("/{email_id}", response_model=EmailResponse)
async def get_email(
    email_id: str,
    user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get email details"""
    email_doc = await db.emails.find_one({"id": email_id, "user_id": user.id})
    
    if not email_doc:
        raise HTTPException(status_code=404, detail="Email not found")
    
    return EmailResponse(
        id=email_doc['id'],
        email_account_id=email_doc['email_account_id'],
        from_email=email_doc['from_email'],
        to_email=email_doc['to_email'],
        subject=email_doc['subject'],
        body=email_doc['body'],
        received_at=email_doc['received_at'],
        direction=email_doc['direction'],
        processed=email_doc['processed'],
        intent_detected=email_doc.get('intent_detected'),
        meeting_detected=email_doc['meeting_detected'],
        draft_generated=email_doc['draft_generated'],
        draft_content=email_doc.get('draft_content'),
        status=email_doc['status'],
        replied=email_doc['replied'],
        created_at=email_doc['created_at']
    )

@router.post("/send")
async def send_email(
    email_data: EmailSend,
    user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Send email"""
    # Check quota
    auth_service = AuthService(db)
    has_quota = await auth_service.check_quota(user.id)
    
    if not has_quota:
        raise HTTPException(status_code=429, detail="Quota exceeded")
    
    # Get account
    account_doc = await db.email_accounts.find_one({
        "id": email_data.email_account_id,
        "user_id": user.id
    })
    
    if not account_doc:
        raise HTTPException(status_code=404, detail="Email account not found")
    
    account = EmailAccount(**account_doc)
    
    # Decrypt password if needed
    if account.password:
        from routes.email_account_routes import cipher
        account.password = cipher.decrypt(account.password.encode()).decode()
    
    # Send email
    email_service = EmailService(db)
    
    sent = False
    if account.account_type == 'oauth_gmail':
        result = await email_service.send_email_oauth_gmail(account, email_data)
        sent = result.get("success", False)
    else:
        sent = await email_service.send_email_smtp(account, email_data)
    
    if not sent:
        raise HTTPException(status_code=500, detail="Failed to send email")
    
    # Increment quota
    await auth_service.increment_quota(user.id)
    
    return {"success": True, "message": "Email sent successfully"}

@router.post("/{email_id}/approve-draft")
async def approve_and_send_draft(
    email_id: str,
    user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Approve and send draft"""
    email_doc = await db.emails.find_one({"id": email_id, "user_id": user.id})
    
    if not email_doc:
        raise HTTPException(status_code=404, detail="Email not found")
    
    email = Email(**email_doc)
    
    if not email.draft_content:
        raise HTTPException(status_code=400, detail="No draft available")
    
    if email.replied:
        raise HTTPException(status_code=400, detail="Email already replied")
    
    # Send draft
    email_data = EmailSend(
        email_account_id=email.email_account_id,
        to_email=[email.from_email],
        subject=f"Re: {email.subject}",
        body=email.draft_content
    )
    
    account_doc = await db.email_accounts.find_one({"id": email.email_account_id})
    if not account_doc:
        raise HTTPException(status_code=404, detail="Email account not found")
    
    account = EmailAccount(**account_doc)
    
    if account.password:
        from routes.email_account_routes import cipher
        account.password = cipher.decrypt(account.password.encode()).decode()
    
    email_service = EmailService(db)
    
    sent = False
    if account.account_type == 'oauth_gmail':
        result = await email_service.send_email_oauth_gmail(account, email_data)
        sent = result.get("success", False)
    else:
        sent = await email_service.send_email_smtp(account, email_data)
    
    if not sent:
        raise HTTPException(status_code=500, detail="Failed to send email")
    
    # Update email
    from datetime import datetime, timezone
    await db.emails.update_one(
        {"id": email_id},
        {"$set": {
            "status": "sent",
            "replied": True,
            "reply_sent_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"success": True, "message": "Draft sent successfully"}

@router.post("/{email_id}/reprocess")
async def reprocess_email(
    email_id: str,
    user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Reprocess email with AI"""
    email_doc = await db.emails.find_one({"id": email_id, "user_id": user.id})
    
    if not email_doc:
        raise HTTPException(status_code=404, detail="Email not found")
    
    # Queue for reprocessing
    from workers.email_worker import process_email
    import asyncio
    
    asyncio.create_task(process_email(email_id))
    
    return {"success": True, "message": "Email queued for reprocessing"}
