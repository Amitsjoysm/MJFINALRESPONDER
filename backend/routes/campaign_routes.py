"""API routes for campaign management"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
import logging

from models.campaign import CampaignResponse, CampaignCreate, CampaignUpdate
from services.campaign_service import CampaignService
from routes.auth_routes import get_current_user_from_token, get_db
from models.user import User
from config import config
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/campaign/campaigns", tags=["Campaigns"])

# Database connection
client = AsyncIOMotorClient(config.MONGO_URL)
db = client[config.DB_NAME]

@router.post("", response_model=CampaignResponse)
async def create_campaign(
    campaign_data: CampaignCreate,
    current_user: User = Depends(get_current_user_from_token)
):
    """Create a new campaign"""
    try:
        service = CampaignService(db)
        campaign = await service.create_campaign(current_user.id, campaign_data)
        return CampaignResponse(**campaign.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating campaign: {e}")
        raise HTTPException(status_code=500, detail="Failed to create campaign")

@router.get("", response_model=List[CampaignResponse])
async def list_campaigns(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user_from_token)
):
    """List all campaigns for the current user"""
    try:
        service = CampaignService(db)
        campaigns = await service.list_campaigns(
            current_user.id,
            skip=skip,
            limit=limit,
            status=status
        )
        return [CampaignResponse(**c.model_dump()) for c in campaigns]
    except Exception as e:
        logger.error(f"Error listing campaigns: {e}")
        raise HTTPException(status_code=500, detail="Failed to list campaigns")

@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user_from_token)
):
    """Get a specific campaign"""
    try:
        service = CampaignService(db)
        campaign = await service.get_campaign(current_user.id, campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        return CampaignResponse(**campaign.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting campaign: {e}")
        raise HTTPException(status_code=500, detail="Failed to get campaign")

@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: str,
    update_data: CampaignUpdate,
    current_user: User = Depends(get_current_user_from_token)
):
    """Update a campaign"""
    try:
        service = CampaignService(db)
        campaign = await service.update_campaign(current_user.id, campaign_id, update_data)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        return CampaignResponse(**campaign.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating campaign: {e}")
        raise HTTPException(status_code=500, detail="Failed to update campaign")

@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user_from_token)
):
    """Delete a campaign"""
    try:
        service = CampaignService(db)
        success = await service.delete_campaign(current_user.id, campaign_id)
        if not success:
            raise HTTPException(status_code=404, detail="Campaign not found")
        return {"message": "Campaign deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting campaign: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete campaign")

@router.post("/{campaign_id}/start", response_model=CampaignResponse)
async def start_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user_from_token)
):
    """Start a campaign"""
    try:
        service = CampaignService(db)
        campaign = await service.start_campaign(current_user.id, campaign_id)
        return CampaignResponse(**campaign.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting campaign: {e}")
        raise HTTPException(status_code=500, detail="Failed to start campaign")

@router.post("/{campaign_id}/pause", response_model=CampaignResponse)
async def pause_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user_from_token)
):
    """Pause a running campaign"""
    try:
        service = CampaignService(db)
        campaign = await service.pause_campaign(current_user.id, campaign_id)
        return CampaignResponse(**campaign.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error pausing campaign: {e}")
        raise HTTPException(status_code=500, detail="Failed to pause campaign")

@router.post("/{campaign_id}/resume", response_model=CampaignResponse)
async def resume_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user_from_token)
):
    """Resume a paused campaign"""
    try:
        service = CampaignService(db)
        campaign = await service.resume_campaign(current_user.id, campaign_id)
        return CampaignResponse(**campaign.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error resuming campaign: {e}")
        raise HTTPException(status_code=500, detail="Failed to resume campaign")

@router.post("/{campaign_id}/stop", response_model=CampaignResponse)
async def stop_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user_from_token)
):
    """Stop a campaign (cannot be resumed)"""
    try:
        service = CampaignService(db)
        campaign = await service.stop_campaign(current_user.id, campaign_id)
        return CampaignResponse(**campaign.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error stopping campaign: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop campaign")

@router.get("/{campaign_id}/analytics")
async def get_campaign_analytics(
    campaign_id: str,
    current_user: User = Depends(get_current_user_from_token)
):
    """Get campaign analytics"""
    try:
        service = CampaignService(db)
        analytics = await service.get_campaign_analytics(current_user.id, campaign_id)
        return analytics
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics")
