from fastapi import APIRouter, Depends, HTTPException
from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime

from routes.auth_routes import get_current_user_from_token, get_db
from models.intent import Intent, IntentCreate, IntentUpdate, IntentResponse
from models.user import User

router = APIRouter(prefix="/intents", tags=["intents"])

@router.post("", response_model=IntentResponse)
async def create_intent(
    intent_data: IntentCreate,
    user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Create new intent"""
    intent = Intent(
        user_id=user.id,
        name=intent_data.name,
        description=intent_data.description,
        prompt=intent_data.prompt,
        keywords=intent_data.keywords,
        auto_send=intent_data.auto_send,
        priority=intent_data.priority
    )
    
    doc = intent.model_dump()
    await db.intents.insert_one(doc)
    
    return IntentResponse(
        id=intent.id,
        name=intent.name,
        description=intent.description,
        prompt=intent.prompt,
        keywords=intent.keywords,
        auto_send=intent.auto_send,
        priority=intent.priority,
        is_inbound_lead=intent.is_inbound_lead,
        enable_lead_qualification=intent.enable_lead_qualification,
        enable_lead_nurturing=intent.enable_lead_nurturing,
        is_active=intent.is_active,
        created_at=intent.created_at
    )

@router.get("", response_model=List[IntentResponse])
async def list_intents(
    user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """List all intents"""
    intents = await db.intents.find({"user_id": user.id}).sort("priority", -1).to_list(100)
    
    return [
        IntentResponse(
            id=intent['id'],
            name=intent['name'],
            description=intent.get('description'),
            prompt=intent['prompt'],
            keywords=intent['keywords'],
            auto_send=intent['auto_send'],
            priority=intent['priority'],
            is_inbound_lead=intent.get('is_inbound_lead', False),
            enable_lead_qualification=intent.get('enable_lead_qualification', False),
            enable_lead_nurturing=intent.get('enable_lead_nurturing', False),
            is_active=intent['is_active'],
            created_at=intent['created_at'].isoformat() if isinstance(intent['created_at'], datetime) else intent['created_at']
        )
        for intent in intents
    ]

@router.get("/{intent_id}", response_model=IntentResponse)
async def get_intent(
    intent_id: str,
    user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get intent details"""
    intent_doc = await db.intents.find_one({"id": intent_id, "user_id": user.id})
    
    if not intent_doc:
        raise HTTPException(status_code=404, detail="Intent not found")
    
    return IntentResponse(
        id=intent_doc['id'],
        name=intent_doc['name'],
        description=intent_doc.get('description'),
        prompt=intent_doc['prompt'],
        keywords=intent_doc['keywords'],
        auto_send=intent_doc['auto_send'],
        priority=intent_doc['priority'],
        is_inbound_lead=intent_doc.get('is_inbound_lead', False),
        enable_lead_qualification=intent_doc.get('enable_lead_qualification', False),
        enable_lead_nurturing=intent_doc.get('enable_lead_nurturing', False),
        is_active=intent_doc['is_active'],
        created_at=intent_doc['created_at'].isoformat() if isinstance(intent_doc['created_at'], datetime) else intent_doc['created_at']
    )

@router.patch("/{intent_id}", response_model=IntentResponse)
async def update_intent(
    intent_id: str,
    update_data: IntentUpdate,
    user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Update intent"""
    intent_doc = await db.intents.find_one({"id": intent_id, "user_id": user.id})
    
    if not intent_doc:
        raise HTTPException(status_code=404, detail="Intent not found")
    
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    
    if update_dict:
        await db.intents.update_one(
            {"id": intent_id},
            {"$set": update_dict}
        )
    
    updated_doc = await db.intents.find_one({"id": intent_id})
    
    return IntentResponse(
        id=updated_doc['id'],
        name=updated_doc['name'],
        description=updated_doc.get('description'),
        prompt=updated_doc['prompt'],
        keywords=updated_doc['keywords'],
        auto_send=updated_doc['auto_send'],
        priority=updated_doc['priority'],
        is_inbound_lead=updated_doc.get('is_inbound_lead', False),
        enable_lead_qualification=updated_doc.get('enable_lead_qualification', False),
        enable_lead_nurturing=updated_doc.get('enable_lead_nurturing', False),
        is_active=updated_doc['is_active'],
        created_at=updated_doc['created_at'].isoformat() if isinstance(updated_doc['created_at'], datetime) else updated_doc['created_at']
    )

@router.delete("/{intent_id}")
async def delete_intent(
    intent_id: str,
    user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Delete intent"""
    result = await db.intents.delete_one({"id": intent_id, "user_id": user.id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Intent not found")
    
    return {"message": "Intent deleted successfully"}
