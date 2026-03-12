"""API routes for campaign contact management"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from typing import List, Optional
import logging

from models.campaign_contact import (
    CampaignContactResponse, CampaignContactCreate, CampaignContactUpdate
)
from services.campaign_contact_service import CampaignContactService
from routes.auth_routes import get_current_user_from_token, get_db
from models.user import User
from config import config
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/campaign/contacts", tags=["Campaign Contacts"])

# Database connection
client = AsyncIOMotorClient(config.MONGO_URL)
db = client[config.DB_NAME]

@router.post("", response_model=CampaignContactResponse)
async def create_contact(
    contact_data: CampaignContactCreate,
    current_user: User = Depends(get_current_user_from_token)
):
    """Create a new campaign contact"""
    try:
        service = CampaignContactService(db)
        contact = await service.create_contact(current_user.id, contact_data)
        return CampaignContactResponse(**contact.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating contact: {e}")
        raise HTTPException(status_code=500, detail="Failed to create contact")

@router.get("", response_model=List[CampaignContactResponse])
async def list_contacts(
    skip: int = 0,
    limit: int = 100,
    tags: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user_from_token)
):
    """List all contacts for the current user"""
    try:
        service = CampaignContactService(db)
        tag_list = tags.split(",") if tags else None
        contacts = await service.list_contacts(
            current_user.id,
            skip=skip,
            limit=limit,
            tags=tag_list,
            status=status
        )
        return [CampaignContactResponse(**c.model_dump()) for c in contacts]
    except Exception as e:
        logger.error(f"Error listing contacts: {e}")
        raise HTTPException(status_code=500, detail="Failed to list contacts")

@router.get("/{contact_id}", response_model=CampaignContactResponse)
async def get_contact(
    contact_id: str,
    current_user: User = Depends(get_current_user_from_token)
):
    """Get a specific contact"""
    try:
        service = CampaignContactService(db)
        contact = await service.get_contact(current_user.id, contact_id)
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        return CampaignContactResponse(**contact.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting contact: {e}")
        raise HTTPException(status_code=500, detail="Failed to get contact")

@router.put("/{contact_id}", response_model=CampaignContactResponse)
async def update_contact(
    contact_id: str,
    update_data: CampaignContactUpdate,
    current_user: User = Depends(get_current_user_from_token)
):
    """Update a contact"""
    try:
        service = CampaignContactService(db)
        contact = await service.update_contact(current_user.id, contact_id, update_data)
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        return CampaignContactResponse(**contact.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating contact: {e}")
        raise HTTPException(status_code=500, detail="Failed to update contact")

@router.delete("/{contact_id}")
async def delete_contact(
    contact_id: str,
    current_user: User = Depends(get_current_user_from_token)
):
    """Delete a contact"""
    try:
        service = CampaignContactService(db)
        success = await service.delete_contact(current_user.id, contact_id)
        if not success:
            raise HTTPException(status_code=404, detail="Contact not found")
        return {"message": "Contact deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting contact: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete contact")

@router.post("/bulk-upload")
async def bulk_upload_contacts(
    file: UploadFile = File(...),
    field_mapping: str = "",
    current_user: User = Depends(get_current_user_from_token)
):
    """Bulk upload contacts from CSV file
    
    Field mapping should be a JSON string like:
    {"Email": "email", "First Name": "first_name", "Last Name": "last_name"}
    """
    try:
        import json
        
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are allowed")
        
        # Parse field mapping
        if field_mapping:
            mapping = json.loads(field_mapping)
        else:
            # Default mapping
            mapping = {
                "Email": "email",
                "First Name": "first_name",
                "Last Name": "last_name",
                "Company": "company",
                "Title": "title",
                "LinkedIn URL": "linkedin_url",
                "Company Domain": "company_domain"
            }
        
        # Read CSV content
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        # Process upload
        service = CampaignContactService(db)
        result = await service.bulk_upload_csv(current_user.id, csv_content, mapping)
        
        return result
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid field mapping JSON")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in bulk upload: {e}")
        raise HTTPException(status_code=500, detail="Failed to process CSV file")

@router.get("/template/download")
async def download_template(
    current_user: User = Depends(get_current_user_from_token)
):
    """Download sample CSV template"""
    try:
        service = CampaignContactService(db)
        template = await service.get_sample_csv_template()
        
        return Response(
            content=template,
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=contacts_template.csv"
            }
        )
    except Exception as e:
        logger.error(f"Error generating template: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate template")
