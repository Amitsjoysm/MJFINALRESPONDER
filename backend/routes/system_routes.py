from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
import asyncio
from datetime import datetime, timezone, timedelta

from routes.auth_routes import get_current_user_from_token, get_db
from services.queue_service import queue_service
from models.user import User

router = APIRouter(prefix="/system", tags=["system"])

@router.get("/status")
async def get_system_status(
    user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get system status"""
    # Check Redis
    redis_status = "online" if queue_service.is_available() else "offline"
    
    # Check MongoDB
    try:
        await db.command('ping')
        mongo_status = "online"
    except:
        mongo_status = "offline"
    
    # Check active accounts
    active_accounts = await db.email_accounts.count_documents({
        "user_id": user.id,
        "is_active": True
    })
    
    # Check if polling is active (simple heuristic: check recent syncs)
    from datetime import datetime, timezone, timedelta
    recent_sync_time = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    recent_syncs = await db.email_accounts.count_documents({
        "user_id": user.id,
        "last_sync": {"$gte": recent_sync_time}
    })
    
    email_polling_status = "active" if recent_syncs > 0 else "setup needed"
    
    # Check intent detection setup
    intents_count = await db.intents.count_documents({"user_id": user.id, "is_active": True})
    intent_status = "online" if intents_count > 0 else "setup needed"
    
    return {
        "email_polling": email_polling_status,
        "email_accounts": f"{active_accounts} active",
        "intent_detection": intent_status,
        "ai_processing": "online",  # Groq/Cohere
        "redis": redis_status,
        "mongodb": mongo_status
    }

@router.post("/test-email-processing")
async def test_email_processing(
    user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Test email processing with a sample email"""
    from models.email import Email
    from services.ai_agent_service import AIAgentService
    
    # Create test email
    test_email = Email(
        user_id=user.id,
        email_account_id="test",
        message_id="test-123",
        from_email="test@example.com",
        to_email=["user@example.com"],
        subject="Meeting Request for Project Discussion",
        body="Hi, I'd like to schedule a meeting with you next Monday at 2 PM to discuss the project timeline. Let me know if that works for you.",
        received_at=datetime.now(timezone.utc).isoformat()
    )
    
    ai_service = AIAgentService(db)
    
    # Test intent detection
    intent_id, intent_confidence = await ai_service.classify_intent(test_email, user.id)
    
    # Test meeting detection
    is_meeting, meeting_confidence, meeting_details = await ai_service.detect_meeting(test_email)
    
    # Test draft generation
    draft, tokens = await ai_service.generate_draft(test_email, user.id, intent_id)
    
    # Test validation
    valid, issues = await ai_service.validate_draft(draft, test_email, user.id, intent_id)
    
    return {
        "success": True,
        "intent_detection": {
            "intent_id": intent_id,
            "confidence": intent_confidence
        },
        "meeting_detection": {
            "is_meeting": is_meeting,
            "confidence": meeting_confidence,
            "details": meeting_details
        },
        "draft_generation": {
            "draft": draft,
            "tokens_used": tokens
        },
        "validation": {
            "valid": valid,
            "issues": issues
        },
        "total_tokens_used": ai_service.get_tokens_used()
    }

@router.post("/start-polling")
async def start_email_polling(
    user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Start email polling for user accounts"""
    from workers.email_worker import poll_all_accounts
    
    # Trigger immediate poll
    asyncio.create_task(poll_all_accounts())
    
    return {"success": True, "message": "Email polling started"}

@router.post("/stop-polling")
async def stop_email_polling(
    user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Stop email polling (deactivate all accounts)"""
    await db.email_accounts.update_many(
        {"user_id": user.id},
        {"$set": {"is_active": False}}
    )
    
    return {"success": True, "message": "Email polling stopped"}
