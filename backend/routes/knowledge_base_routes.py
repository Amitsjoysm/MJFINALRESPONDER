from fastapi import APIRouter, Depends, HTTPException
from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime

from routes.auth_routes import get_current_user_from_token, get_db
from models.knowledge_base import KnowledgeBase, KnowledgeBaseCreate, KnowledgeBaseUpdate, KnowledgeBaseResponse
from models.user import User

router = APIRouter(prefix="/knowledge-base", tags=["knowledge-base"])

@router.post("", response_model=KnowledgeBaseResponse)
async def create_knowledge_base(
    kb_data: KnowledgeBaseCreate,
    user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Create knowledge base entry"""
    kb = KnowledgeBase(
        user_id=user.id,
        title=kb_data.title,
        content=kb_data.content,
        category=kb_data.category,
        tags=kb_data.tags
    )
    
    doc = kb.model_dump()
    await db.knowledge_base.insert_one(doc)
    
    return KnowledgeBaseResponse(
        id=kb.id,
        title=kb.title,
        content=kb.content,
        category=kb.category,
        tags=kb.tags,
        is_active=kb.is_active,
        created_at=kb.created_at
    )

@router.get("", response_model=List[KnowledgeBaseResponse])
async def list_knowledge_base(
    user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """List knowledge base entries"""
    kbs = await db.knowledge_base.find({"user_id": user.id}).to_list(100)
    
    return [
        KnowledgeBaseResponse(
            id=kb['id'],
            title=kb['title'],
            content=kb['content'],
            category=kb.get('category'),
            tags=kb.get('tags', []),  # Default to empty list if not present
            is_active=kb['is_active'],
            created_at=kb['created_at'].isoformat() if isinstance(kb['created_at'], datetime) else kb['created_at']
        )
        for kb in kbs
    ]

@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(
    kb_id: str,
    user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get knowledge base entry"""
    kb_doc = await db.knowledge_base.find_one({"id": kb_id, "user_id": user.id})
    
    if not kb_doc:
        raise HTTPException(status_code=404, detail="Knowledge base entry not found")
    
    return KnowledgeBaseResponse(
        id=kb_doc['id'],
        title=kb_doc['title'],
        content=kb_doc['content'],
        category=kb_doc.get('category'),
        tags=kb_doc['tags'],
        is_active=kb_doc['is_active'],
        created_at=kb_doc['created_at'].isoformat() if isinstance(kb_doc['created_at'], datetime) else kb_doc['created_at']
    )

@router.patch("/{kb_id}", response_model=KnowledgeBaseResponse)
async def update_knowledge_base(
    kb_id: str,
    update_data: KnowledgeBaseUpdate,
    user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Update knowledge base entry"""
    kb_doc = await db.knowledge_base.find_one({"id": kb_id, "user_id": user.id})
    
    if not kb_doc:
        raise HTTPException(status_code=404, detail="Knowledge base entry not found")
    
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    
    if update_dict:
        await db.knowledge_base.update_one(
            {"id": kb_id},
            {"$set": update_dict}
        )
    
    updated_doc = await db.knowledge_base.find_one({"id": kb_id})
    
    return KnowledgeBaseResponse(
        id=updated_doc['id'],
        title=updated_doc['title'],
        content=updated_doc['content'],
        category=updated_doc.get('category'),
        tags=updated_doc['tags'],
        is_active=updated_doc['is_active'],
        created_at=updated_doc['created_at'].isoformat() if isinstance(updated_doc['created_at'], datetime) else updated_doc['created_at']
    )

@router.delete("/{kb_id}")
async def delete_knowledge_base(
    kb_id: str,
    user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Delete knowledge base entry"""
    result = await db.knowledge_base.delete_one({"id": kb_id, "user_id": user.id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Knowledge base entry not found")
    
    return {"message": "Knowledge base entry deleted successfully"}
