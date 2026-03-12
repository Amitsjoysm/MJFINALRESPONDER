"""
Lead Qualification Criteria Routes
API endpoints for managing lead qualification criteria
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from datetime import datetime, timezone

from models.lead_qualification_criteria import (
    LeadQualificationCriteria,
    QualificationCriteriaCreate,
    QualificationCriteriaUpdate,
    QualificationCriteriaResponse
)
from models.user import User
from routes.auth_routes import get_current_user_from_token, get_db

router = APIRouter(prefix="/api/lead-qualification-criteria", tags=["Lead Qualification"])

@router.get("", response_model=List[QualificationCriteriaResponse])
async def list_qualification_criteria(
    user: User = Depends(get_current_user_from_token),
    db = Depends(get_db)
):
    """List all qualification criteria for current user"""
    try:
        criteria_collection = db['lead_qualification_criteria']
        
        criteria_list = await criteria_collection.find({
            "user_id": user.id,
            "is_active": True
        }).to_list(length=100)
        
        # Convert datetime to string for Pydantic validation
        for criteria in criteria_list:
            if isinstance(criteria.get('created_at'), datetime):
                criteria['created_at'] = criteria['created_at'].isoformat()
            if isinstance(criteria.get('updated_at'), datetime):
                criteria['updated_at'] = criteria['updated_at'].isoformat()
        
        return criteria_list
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{criteria_id}", response_model=QualificationCriteriaResponse)
async def get_qualification_criteria(
    criteria_id: str,
    user: User = Depends(get_current_user_from_token),
    db = Depends(get_db)
):
    """Get specific qualification criteria"""
    try:
        criteria_collection = db['lead_qualification_criteria']
        
        criteria = await criteria_collection.find_one({
            "id": criteria_id,
            "user_id": user.id
        })
        
        if not criteria:
            raise HTTPException(status_code=404, detail="Qualification criteria not found")
        
        # Convert datetime to string
        if isinstance(criteria.get('created_at'), datetime):
            criteria['created_at'] = criteria['created_at'].isoformat()
        if isinstance(criteria.get('updated_at'), datetime):
            criteria['updated_at'] = criteria['updated_at'].isoformat()
        
        return criteria
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("", response_model=QualificationCriteriaResponse)
async def create_qualification_criteria(
    criteria_data: QualificationCriteriaCreate,
    user: User = Depends(get_current_user_from_token),
    db = Depends(get_db)
):
    """Create new qualification criteria"""
    try:
        criteria_collection = db['lead_qualification_criteria']
        
        # Create criteria document
        criteria = LeadQualificationCriteria(
            user_id=user.id,
            **criteria_data.model_dump()
        )
        
        # Insert into database
        await criteria_collection.insert_one(criteria.model_dump())
        
        return criteria.model_dump()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{criteria_id}", response_model=QualificationCriteriaResponse)
async def update_qualification_criteria(
    criteria_id: str,
    criteria_update: QualificationCriteriaUpdate,
    user: User = Depends(get_current_user_from_token),
    db = Depends(get_db)
):
    """Update qualification criteria"""
    try:
        criteria_collection = db['lead_qualification_criteria']
        
        # Check if criteria exists
        existing = await criteria_collection.find_one({
            "id": criteria_id,
            "user_id": user.id
        })
        
        if not existing:
            raise HTTPException(status_code=404, detail="Qualification criteria not found")
        
        # Prepare update data
        update_data = {
            k: v for k, v in criteria_update.model_dump(exclude_unset=True).items()
            if v is not None
        }
        
        if update_data:
            update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
            
            await criteria_collection.update_one(
                {"id": criteria_id, "user_id": user.id},
                {"$set": update_data}
            )
        
        # Get updated criteria
        updated_criteria = await criteria_collection.find_one({
            "id": criteria_id,
            "user_id": user.id
        })
        
        # Convert datetime to string
        if isinstance(updated_criteria.get('created_at'), datetime):
            updated_criteria['created_at'] = updated_criteria['created_at'].isoformat()
        if isinstance(updated_criteria.get('updated_at'), datetime):
            updated_criteria['updated_at'] = updated_criteria['updated_at'].isoformat()
        
        return updated_criteria
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{criteria_id}")
async def delete_qualification_criteria(
    criteria_id: str,
    user: User = Depends(get_current_user_from_token),
    db = Depends(get_db)
):
    """Delete (soft delete) qualification criteria"""
    try:
        criteria_collection = db['lead_qualification_criteria']
        
        # Soft delete by setting is_active to False
        result = await criteria_collection.update_one(
            {"id": criteria_id, "user_id": user.id},
            {"$set": {
                "is_active": False,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Qualification criteria not found")
        
        return {"message": "Qualification criteria deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
