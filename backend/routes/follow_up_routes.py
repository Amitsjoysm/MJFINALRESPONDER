from fastapi import APIRouter, Depends, HTTPException
from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone, timedelta

from routes.auth_routes import get_current_user_from_token, get_db
from models.follow_up import FollowUp, FollowUpCreate, FollowUpResponse
from models.user import User

router = APIRouter(prefix="/follow-ups", tags=["follow-ups"])

@router.post("", response_model=FollowUpResponse)
async def create_follow_up(
    follow_up_data: FollowUpCreate,
    user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Create follow-up"""
    # Get email
    email_doc = await db.emails.find_one({"id": follow_up_data.email_id, "user_id": user.id})
    if not email_doc:
        raise HTTPException(status_code=404, detail="Email not found")
    
    follow_up = FollowUp(
        user_id=user.id,
        email_id=follow_up_data.email_id,
        email_account_id=email_doc['email_account_id'],
        scheduled_at=follow_up_data.scheduled_at,
        subject=follow_up_data.subject,
        body=follow_up_data.body
    )
    
    doc = follow_up.model_dump()
    await db.follow_ups.insert_one(doc)
    
    return FollowUpResponse(
        id=follow_up.id,
        email_id=follow_up.email_id,
        scheduled_at=follow_up.scheduled_at,
        sent_at=follow_up.sent_at,
        subject=follow_up.subject,
        status=follow_up.status,
        response_detected=follow_up.response_detected,
        created_at=follow_up.created_at
    )

@router.get("", response_model=List[dict])
async def list_follow_ups(
    user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """List follow-ups with email details"""
    follow_ups = await db.follow_ups.find({"user_id": user.id}).sort("scheduled_at", 1).to_list(100)
    
    result = []
    for f in follow_ups:
        # Get the original email
        email = await db.emails.find_one({"id": f['email_id']})
        
        result.append({
            "id": f['id'],
            "email_id": f['email_id'],
            "scheduled_at": f['scheduled_at'],
            "sent_at": f.get('sent_at'),
            "subject": f['subject'],
            "body": f.get('body', ''),
            "status": f['status'],
            "response_detected": f['response_detected'],
            "created_at": f['created_at'],
            "thread_id": f.get('thread_id'),
            "cancelled_reason": f.get('cancelled_reason'),
            # Email details
            "original_email": {
                "subject": email.get('subject', '') if email else '',
                "from_email": email.get('from_email', '') if email else '',
                "received_at": email.get('received_at', '') if email else '',
                "body": email.get('body', '')[:200] + '...' if email and len(email.get('body', '')) > 200 else (email.get('body', '') if email else '')
            } if email else None
        })
    
    return result

@router.get("/{follow_up_id}", response_model=dict)
async def get_follow_up(
    follow_up_id: str,
    user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get detailed follow-up information"""
    follow_up = await db.follow_ups.find_one({"id": follow_up_id, "user_id": user.id})
    
    if not follow_up:
        raise HTTPException(status_code=404, detail="Follow-up not found")
    
    # Get the original email
    email = await db.emails.find_one({"id": follow_up['email_id']})
    
    # Get email account
    email_account = None
    if follow_up.get('email_account_id'):
        account = await db.emails_accounts.find_one({"id": follow_up['email_account_id']})
        if account:
            email_account = {
                "email": account.get('email', ''),
                "account_type": account.get('account_type', '')
            }
    
    return {
        "id": follow_up['id'],
        "email_id": follow_up['email_id'],
        "scheduled_at": follow_up['scheduled_at'],
        "sent_at": follow_up.get('sent_at'),
        "subject": follow_up['subject'],
        "body": follow_up.get('body', ''),
        "status": follow_up['status'],
        "response_detected": follow_up['response_detected'],
        "response_detected_at": follow_up.get('response_detected_at'),
        "created_at": follow_up['created_at'],
        "updated_at": follow_up.get('updated_at'),
        "thread_id": follow_up.get('thread_id'),
        "cancelled_reason": follow_up.get('cancelled_reason'),
        # Email details
        "original_email": {
            "id": email.get('id', '') if email else '',
            "subject": email.get('subject', '') if email else '',
            "from_email": email.get('from_email', '') if email else '',
            "to_email": email.get('to_email', []) if email else [],
            "received_at": email.get('received_at', '') if email else '',
            "body": email.get('body', '') if email else '',
            "thread_id": email.get('thread_id', '') if email else '',
            "intent_name": email.get('intent_name', '') if email else '',
            "replied": email.get('replied', False) if email else False
        } if email else None,
        "email_account": email_account
    }

@router.delete("/{follow_up_id}")
async def delete_follow_up(
    follow_up_id: str,
    user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Cancel follow-up"""
    result = await db.follow_ups.update_one(
        {"id": follow_up_id, "user_id": user.id},
        {"$set": {"status": "cancelled"}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Follow-up not found")
    
    return {"message": "Follow-up cancelled successfully"}
