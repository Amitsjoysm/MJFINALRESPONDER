"""
Lead Nurturing Config Routes
API endpoints for managing lead nurturing configuration
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from datetime import datetime, timezone

from models.lead_nurturing_config import (
    LeadNurturingConfig,
    NurturingConfigCreate,
    NurturingConfigUpdate,
    NurturingConfigResponse
)
from models.user import User
from routes.auth_routes import get_current_user_from_token, get_db

router = APIRouter(prefix="/api/lead-nurturing-config", tags=["Lead Nurturing"])

@router.get("", response_model=List[NurturingConfigResponse])
async def list_nurturing_configs(user: User = Depends(get_current_user_from_token), db = Depends(get_db)):
    """List all nurturing configurations for current user"""
    try:
        config_collection = db['lead_nurturing_config']
        
        configs = await config_collection.find({
            "user_id": user.id,
            "is_active": True
        }).to_list(length=100)
        
        # Convert datetime to string for Pydantic validation
        for config in configs:
            if isinstance(config.get('created_at'), datetime):
                config['created_at'] = config['created_at'].isoformat()
            if isinstance(config.get('updated_at'), datetime):
                config['updated_at'] = config['updated_at'].isoformat()
        
        return configs
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{config_id}", response_model=NurturingConfigResponse)
async def get_nurturing_config(
    config_id: str,
    user: User = Depends(get_current_user_from_token), db = Depends(get_db)
):
    """Get specific nurturing configuration"""
    try:
        db
        config_collection = db['lead_nurturing_config']
        
        config = await config_collection.find_one({
            "id": config_id,
            "user_id": user.id
        })
        
        if not config:
            raise HTTPException(status_code=404, detail="Nurturing configuration not found")
        
        # Convert datetime to string
        if isinstance(config.get('created_at'), datetime):
            config['created_at'] = config['created_at'].isoformat()
        if isinstance(config.get('updated_at'), datetime):
            config['updated_at'] = config['updated_at'].isoformat()
        
        return config
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("", response_model=NurturingConfigResponse)
async def create_nurturing_config(
    config_data: NurturingConfigCreate,
    user: User = Depends(get_current_user_from_token), db = Depends(get_db)
):
    """Create new nurturing configuration"""
    try:
        db
        config_collection = db['lead_nurturing_config']
        
        # Create config document
        config = LeadNurturingConfig(
            user_id=user.id,
            **config_data.model_dump()
        )
        
        # Insert into database
        await config_collection.insert_one(config.model_dump())
        
        return config.model_dump()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{config_id}", response_model=NurturingConfigResponse)
async def update_nurturing_config(
    config_id: str,
    config_update: NurturingConfigUpdate,
    user: User = Depends(get_current_user_from_token), db = Depends(get_db)
):
    """Update nurturing configuration"""
    try:
        db
        config_collection = db['lead_nurturing_config']
        
        # Check if config exists
        existing = await config_collection.find_one({
            "id": config_id,
            "user_id": user.id
        })
        
        if not existing:
            raise HTTPException(status_code=404, detail="Nurturing configuration not found")
        
        # Prepare update data
        update_data = {
            k: v for k, v in config_update.model_dump(exclude_unset=True).items()
            if v is not None
        }
        
        if update_data:
            update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
            
            await config_collection.update_one(
                {"id": config_id, "user_id": user.id},
                {"$set": update_data}
            )
        
        # Get updated config
        updated_config = await config_collection.find_one({
            "id": config_id,
            "user_id": user.id
        })
        
        # Convert datetime to string
        if isinstance(updated_config.get('created_at'), datetime):
            updated_config['created_at'] = updated_config['created_at'].isoformat()
        if isinstance(updated_config.get('updated_at'), datetime):
            updated_config['updated_at'] = updated_config['updated_at'].isoformat()
        
        return updated_config
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{config_id}")
async def delete_nurturing_config(
    config_id: str,
    user: User = Depends(get_current_user_from_token), db = Depends(get_db)
):
    """Delete (soft delete) nurturing configuration"""
    try:
        db
        config_collection = db['lead_nurturing_config']
        
        # Soft delete by setting is_active to False
        result = await config_collection.update_one(
            {"id": config_id, "user_id": user.id},
            {"$set": {
                "is_active": False,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Nurturing configuration not found")
        
        return {"message": "Nurturing configuration deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
