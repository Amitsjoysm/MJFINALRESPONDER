"""API routes for contact list management"""
import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional

from models.contact_list import (
    ContactListResponse, ContactListCreate, ContactListUpdate,
    ContactListAddContacts, ContactListRemoveContacts
)
from models.user import User
from services.contact_list_service import ContactListService
from routes.auth_routes import get_current_user_from_token, get_db
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/campaign/lists", tags=["Contact Lists"])


@router.post("", response_model=ContactListResponse)
async def create_contact_list(
    list_data: ContactListCreate,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Create a new contact list"""
    try:
        service = ContactListService(db)
        contact_list = await service.create_list(current_user.id, list_data)
        return ContactListResponse(**contact_list.model_dump())
    except Exception as e:
        logger.error(f"Error creating contact list: {e}")
        raise HTTPException(status_code=500, detail="Failed to create contact list")


@router.get("", response_model=List[ContactListResponse])
async def list_contact_lists(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """List all contact lists for the current user"""
    try:
        service = ContactListService(db)
        lists = await service.list_lists(
            current_user.id,
            skip=skip,
            limit=limit,
            search=search
        )
        return [ContactListResponse(**lst.model_dump()) for lst in lists]
    except Exception as e:
        logger.error(f"Error listing contact lists: {e}")
        raise HTTPException(status_code=500, detail="Failed to list contact lists")


@router.get("/{list_id}", response_model=ContactListResponse)
async def get_contact_list(
    list_id: str,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get a specific contact list"""
    try:
        service = ContactListService(db)
        contact_list = await service.get_list(current_user.id, list_id)
        if not contact_list:
            raise HTTPException(status_code=404, detail="Contact list not found")
        return ContactListResponse(**contact_list.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting contact list: {e}")
        raise HTTPException(status_code=500, detail="Failed to get contact list")


@router.put("/{list_id}", response_model=ContactListResponse)
async def update_contact_list(
    list_id: str,
    update_data: ContactListUpdate,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Update a contact list"""
    try:
        service = ContactListService(db)
        contact_list = await service.update_list(current_user.id, list_id, update_data)
        if not contact_list:
            raise HTTPException(status_code=404, detail="Contact list not found")
        return ContactListResponse(**contact_list.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating contact list: {e}")
        raise HTTPException(status_code=500, detail="Failed to update contact list")


@router.delete("/{list_id}")
async def delete_contact_list(
    list_id: str,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Delete a contact list"""
    try:
        service = ContactListService(db)
        success = await service.delete_list(current_user.id, list_id)
        if not success:
            raise HTTPException(status_code=404, detail="Contact list not found")
        return {"message": "Contact list deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting contact list: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete contact list")


@router.post("/{list_id}/add-contacts", response_model=ContactListResponse)
async def add_contacts_to_list(
    list_id: str,
    data: ContactListAddContacts,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Add contacts to a list"""
    try:
        service = ContactListService(db)
        contact_list = await service.add_contacts_to_list(
            current_user.id,
            list_id,
            data.contact_ids
        )
        if not contact_list:
            raise HTTPException(status_code=404, detail="Contact list not found")
        return ContactListResponse(**contact_list.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding contacts to list: {e}")
        raise HTTPException(status_code=500, detail="Failed to add contacts")


@router.post("/{list_id}/remove-contacts", response_model=ContactListResponse)
async def remove_contacts_from_list(
    list_id: str,
    data: ContactListRemoveContacts,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Remove contacts from a list"""
    try:
        service = ContactListService(db)
        contact_list = await service.remove_contacts_from_list(
            current_user.id,
            list_id,
            data.contact_ids
        )
        if not contact_list:
            raise HTTPException(status_code=404, detail="Contact list not found")
        return ContactListResponse(**contact_list.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing contacts from list: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove contacts")


@router.get("/{list_id}/contacts")
async def get_list_contacts(
    list_id: str,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get all contacts in a list"""
    try:
        service = ContactListService(db)
        contacts = await service.get_list_contacts(current_user.id, list_id)
        return contacts
    except Exception as e:
        logger.error(f"Error getting list contacts: {e}")
        raise HTTPException(status_code=500, detail="Failed to get list contacts")
