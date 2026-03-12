"""Service for managing contact lists"""
from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone

from models.contact_list import ContactList, ContactListCreate, ContactListUpdate
from repositories.base_repository import GenericRepository


class ContactListService:
    """Service for contact list management"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.list_repo = GenericRepository(db, "contact_lists")
        self.contact_repo = GenericRepository(db, "campaign_contacts")
    
    async def create_list(self, user_id: str, list_data: ContactListCreate) -> ContactList:
        """Create a new contact list"""
        contact_list = ContactList(
            user_id=user_id,
            name=list_data.name,
            description=list_data.description,
            contact_ids=list_data.contact_ids,
            total_contacts=len(list_data.contact_ids)
        )
        
        await self.list_repo.create(contact_list.model_dump())
        return contact_list
    
    async def get_list(self, user_id: str, list_id: str) -> Optional[ContactList]:
        """Get a contact list by ID"""
        list_doc = await self.list_repo.find_one({"id": list_id, "user_id": user_id})
        if list_doc:
            return ContactList(**list_doc)
        return None
    
    async def list_lists(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None
    ) -> List[ContactList]:
        """List all contact lists for a user"""
        query = {"user_id": user_id}
        
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}}
            ]
        
        lists = await self.list_repo.find_many(
            query,
            skip=skip,
            limit=limit,
            sort=[("created_at", -1)]
        )
        
        return [ContactList(**lst) for lst in lists]
    
    async def update_list(
        self,
        user_id: str,
        list_id: str,
        update_data: ContactListUpdate
    ) -> Optional[ContactList]:
        """Update a contact list"""
        existing_list = await self.get_list(user_id, list_id)
        if not existing_list:
            return None
        
        update_dict = update_data.model_dump(exclude_unset=True)
        update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Update total_contacts if contact_ids changed
        if "contact_ids" in update_dict:
            update_dict["total_contacts"] = len(update_dict["contact_ids"])
        
        await self.list_repo.update({"id": list_id, "user_id": user_id}, update_dict)
        
        return await self.get_list(user_id, list_id)
    
    async def delete_list(self, user_id: str, list_id: str) -> bool:
        """Delete a contact list"""
        result = await self.list_repo.delete({"id": list_id, "user_id": user_id})
        return result
    
    async def add_contacts_to_list(
        self,
        user_id: str,
        list_id: str,
        contact_ids: List[str]
    ) -> Optional[ContactList]:
        """Add contacts to a list"""
        existing_list = await self.get_list(user_id, list_id)
        if not existing_list:
            return None
        
        # Add new contacts (avoid duplicates)
        current_ids = set(existing_list.contact_ids)
        current_ids.update(contact_ids)
        new_contact_ids = list(current_ids)
        
        update_dict = {
            "contact_ids": new_contact_ids,
            "total_contacts": len(new_contact_ids),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await self.list_repo.update({"id": list_id, "user_id": user_id}, update_dict)
        
        return await self.get_list(user_id, list_id)
    
    async def remove_contacts_from_list(
        self,
        user_id: str,
        list_id: str,
        contact_ids: List[str]
    ) -> Optional[ContactList]:
        """Remove contacts from a list"""
        existing_list = await self.get_list(user_id, list_id)
        if not existing_list:
            return None
        
        # Remove contacts
        current_ids = set(existing_list.contact_ids)
        for contact_id in contact_ids:
            current_ids.discard(contact_id)
        new_contact_ids = list(current_ids)
        
        update_dict = {
            "contact_ids": new_contact_ids,
            "total_contacts": len(new_contact_ids),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await self.list_repo.update({"id": list_id, "user_id": user_id}, update_dict)
        
        return await self.get_list(user_id, list_id)
    
    async def get_list_contacts(
        self,
        user_id: str,
        list_id: str
    ) -> List[Dict[str, Any]]:
        """Get all contacts in a list"""
        contact_list = await self.get_list(user_id, list_id)
        if not contact_list:
            return []
        
        if not contact_list.contact_ids:
            return []
        
        # Fetch contacts
        contacts = await self.contact_repo.find_many(
            {"id": {"$in": contact_list.contact_ids}, "user_id": user_id},
            limit=10000
        )
        
        return contacts
