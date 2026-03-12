"""API routes for campaign template management"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
import logging

from models.campaign_template import (
    CampaignTemplateResponse, CampaignTemplateCreate, CampaignTemplateUpdate
)
from services.campaign_template_service import CampaignTemplateService
from routes.auth_routes import get_current_user_from_token, get_db
from models.user import User
from config import config
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/campaign/templates", tags=["Campaign Templates"])

# Database connection
client = AsyncIOMotorClient(config.MONGO_URL)
db = client[config.DB_NAME]

@router.post("", response_model=CampaignTemplateResponse)
async def create_template(
    template_data: CampaignTemplateCreate,
    current_user: User = Depends(get_current_user_from_token)
):
    """Create a new campaign template"""
    try:
        service = CampaignTemplateService(db)
        template = await service.create_template(current_user.id, template_data)
        return CampaignTemplateResponse(**template.model_dump())
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        raise HTTPException(status_code=500, detail="Failed to create template")

@router.get("", response_model=List[CampaignTemplateResponse])
async def list_templates(
    skip: int = 0,
    limit: int = 100,
    template_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user_from_token)
):
    """List all templates for the current user"""
    try:
        service = CampaignTemplateService(db)
        templates = await service.list_templates(
            current_user.id,
            skip=skip,
            limit=limit,
            template_type=template_type,
            is_active=is_active
        )
        return [CampaignTemplateResponse(**t.model_dump()) for t in templates]
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to list templates")

@router.get("/{template_id}", response_model=CampaignTemplateResponse)
async def get_template(
    template_id: str,
    current_user: User = Depends(get_current_user_from_token)
):
    """Get a specific template"""
    try:
        service = CampaignTemplateService(db)
        template = await service.get_template(current_user.id, template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        return CampaignTemplateResponse(**template.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template: {e}")
        raise HTTPException(status_code=500, detail="Failed to get template")

@router.put("/{template_id}", response_model=CampaignTemplateResponse)
async def update_template(
    template_id: str,
    update_data: CampaignTemplateUpdate,
    current_user: User = Depends(get_current_user_from_token)
):
    """Update a template"""
    try:
        service = CampaignTemplateService(db)
        template = await service.update_template(current_user.id, template_id, update_data)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        return CampaignTemplateResponse(**template.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating template: {e}")
        raise HTTPException(status_code=500, detail="Failed to update template")

@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    current_user: User = Depends(get_current_user_from_token)
):
    """Delete a template"""
    try:
        service = CampaignTemplateService(db)
        success = await service.delete_template(current_user.id, template_id)
        if not success:
            raise HTTPException(status_code=404, detail="Template not found")
        return {"message": "Template deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting template: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete template")
