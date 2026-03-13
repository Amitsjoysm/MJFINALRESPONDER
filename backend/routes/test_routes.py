"""Test routes for development and testing"""
from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone
import uuid

from routes.auth_routes import get_current_user_from_token, get_db
from models.user import User
from models.email import Email
from workers.email_worker import process_email

router = APIRouter(prefix="/test", tags=["test"])

@router.post("/parse-dates")
async def test_date_parsing(
    text: str,
):
    """Test date parsing from text - no auth required for testing"""
    from services.date_parser_service import DateParserService
    
    parser = DateParserService()
    results = parser.parse_time_references(text)
    
    return {
        "input_text": text,
        "current_date": datetime.now(timezone.utc).isoformat(),
        "references_found": len(results),
        "references": [
            {
                "matched_text": matched_text,
                "target_date": target_date.isoformat(),
                "target_date_human": target_date.strftime("%B %d, %Y at %I:%M %p %Z"),
                "days_from_now": (target_date.date() - datetime.now(timezone.utc).date()).days,
                "context": context[:200]
            }
            for matched_text, target_date, context in results
        ]
    }

@router.post("/send-test-email")
async def send_test_email(
    subject: str,
    body: str,
    from_email: str = "test@example.com",
    user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Create and process a test email"""
    try:
        # Get user's email account
        account = await db.email_accounts.find_one({
            "user_id": user.id,
            "is_active": True
        })
        
        if not account:
            raise HTTPException(status_code=404, detail="No active email account found")
        
        # Create test email
        email = Email(
            id=str(uuid.uuid4()),
            user_id=user.id,
            email_account_id=account['id'],
            from_email=from_email,
            to_email=[account['email']],
            subject=subject,
            body=body,
            received_at=datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000 (UTC)"),
            direction="inbound",
            thread_id=f"test-{uuid.uuid4().hex[:16]}",
            message_id=f"<test-{uuid.uuid4().hex}@example.com>"
        )
        
        # Save to database
        await db.emails.insert_one(email.model_dump())
        
        # Process email asynchronously
        import asyncio
        asyncio.create_task(process_email(email.id))
        
        return {
            "message": "Test email created and queued for processing",
            "email_id": email.id,
            "subject": email.subject
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
