"""Service for managing campaign contacts"""
import csv
import io
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid
import logging

from models.campaign_contact import CampaignContact, CampaignContactCreate, CampaignContactUpdate
from repositories.base_repository import GenericRepository

logger = logging.getLogger(__name__)

class CampaignContactService:
    """Service for campaign contact management"""
    
    def __init__(self, db):
        self.repository = GenericRepository(db, "campaign_contacts")
        self.db = db
    
    async def create_contact(self, user_id: str, contact_data: CampaignContactCreate) -> CampaignContact:
        """Create a new campaign contact"""
        contact = CampaignContact(
            user_id=user_id,
            **contact_data.model_dump()
        )
        
        # Check for duplicate email
        existing = await self.repository.find_one({"user_id": user_id, "email": contact.email})
        if existing:
            raise ValueError(f"Contact with email {contact.email} already exists")
        
        await self.repository.create(contact.model_dump())
        logger.info(f"Created contact {contact.id} for user {user_id}")
        return contact
    
    async def get_contact(self, user_id: str, contact_id: str) -> Optional[CampaignContact]:
        """Get a contact by ID"""
        contact_dict = await self.repository.find_by_id(contact_id)
        if not contact_dict or contact_dict.get("user_id") != user_id:
            return None
        return CampaignContact(**contact_dict)
    
    async def list_contacts(self, user_id: str, skip: int = 0, limit: int = 100, 
                          tags: Optional[List[str]] = None,
                          status: Optional[str] = None) -> List[CampaignContact]:
        """List all contacts for a user with optional filters"""
        filters = {"user_id": user_id}
        
        if tags:
            filters["tags"] = {"$in": tags}
        
        if status:
            filters["status"] = status
        
        contacts = await self.repository.find_many(filters, skip=skip, limit=limit)
        return [CampaignContact(**c) for c in contacts]
    
    async def update_contact(self, user_id: str, contact_id: str, 
                           update_data: CampaignContactUpdate) -> Optional[CampaignContact]:
        """Update a contact"""
        # Verify ownership
        existing = await self.get_contact(user_id, contact_id)
        if not existing:
            return None
        
        update_dict = update_data.model_dump(exclude_unset=True)
        update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        await self.repository.update(contact_id, update_dict)
        logger.info(f"Updated contact {contact_id}")
        
        return await self.get_contact(user_id, contact_id)
    
    async def delete_contact(self, user_id: str, contact_id: str) -> bool:
        """Delete a contact"""
        # Verify ownership
        existing = await self.get_contact(user_id, contact_id)
        if not existing:
            return False
        
        await self.repository.delete(contact_id)
        logger.info(f"Deleted contact {contact_id}")
        return True
    
    async def bulk_upload_csv(self, user_id: str, csv_content: str, 
                             field_mapping: Dict[str, str]) -> Dict[str, Any]:
        """Bulk upload contacts from CSV
        
        Args:
            user_id: User ID
            csv_content: CSV file content as string
            field_mapping: Maps CSV columns to contact fields
                          e.g., {"Email": "email", "First Name": "first_name"}
        
        Returns:
            Dictionary with success count, error count, and error details
        """
        result = {
            "success_count": 0,
            "error_count": 0,
            "errors": [],
            "contact_ids": [],
            "imported_ids": []  # Alias for frontend compatibility
        }
        
        try:
            # Parse CSV
            csv_file = io.StringIO(csv_content)
            reader = csv.DictReader(csv_file)
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    # Map CSV fields to contact fields
                    contact_data = {}
                    custom_fields = {}
                    
                    for csv_col, contact_field in field_mapping.items():
                        value = row.get(csv_col, "").strip()
                        if not value:
                            continue
                        
                        # Standard fields
                        if contact_field in ["email", "first_name", "last_name", "company", 
                                            "title", "linkedin_url", "company_domain"]:
                            contact_data[contact_field] = value
                        else:
                            # Custom fields
                            custom_fields[contact_field] = value
                    
                    if custom_fields:
                        contact_data["custom_fields"] = custom_fields
                    
                    # Validate email is present
                    if "email" not in contact_data:
                        result["errors"].append({
                            "row": row_num,
                            "error": "Email is required"
                        })
                        result["error_count"] += 1
                        continue
                    
                    # Check for duplicate
                    existing = await self.repository.find_one({
                        "user_id": user_id,
                        "email": contact_data["email"]
                    })
                    
                    if existing:
                        result["errors"].append({
                            "row": row_num,
                            "email": contact_data["email"],
                            "error": "Duplicate email"
                        })
                        result["error_count"] += 1
                        continue
                    
                    # Create contact
                    contact = CampaignContact(
                        user_id=user_id,
                        **contact_data
                    )
                    
                    await self.repository.create(contact.model_dump())
                    result["success_count"] += 1
                    result["contact_ids"].append(contact.id)
                    result["imported_ids"].append(contact.id)  # Alias for frontend
                    
                except Exception as e:
                    logger.error(f"Error processing row {row_num}: {e}")
                    result["errors"].append({
                        "row": row_num,
                        "error": str(e)
                    })
                    result["error_count"] += 1
            
            logger.info(f"Bulk upload completed: {result['success_count']} success, {result['error_count']} errors")
            return result
            
        except Exception as e:
            logger.error(f"Error in bulk upload: {e}")
            raise ValueError(f"Failed to process CSV: {str(e)}")
    
    async def get_sample_csv_template(self) -> str:
        """Generate sample CSV template for download"""
        template = "Email,First Name,Last Name,Company,Title,LinkedIn URL,Company Domain\n"
        template += "john.doe@example.com,John,Doe,Acme Inc,CEO,https://linkedin.com/in/johndoe,acme.com\n"
        template += "jane.smith@example.com,Jane,Smith,TechCorp,CTO,https://linkedin.com/in/janesmith,techcorp.com\n"
        return template
    
    async def update_engagement_stats(self, contact_id: str, 
                                     email_sent: bool = False,
                                     email_opened: bool = False,
                                     email_replied: bool = False) -> None:
        """Update contact engagement statistics"""
        update_dict = {"updated_at": datetime.now(timezone.utc).isoformat()}
        
        if email_sent:
            await self.db.campaign_contacts.update_one(
                {"id": contact_id},
                {
                    "$inc": {"emails_sent": 1},
                    "$set": {
                        "last_contacted": datetime.now(timezone.utc).isoformat(),
                        "updated_at": update_dict["updated_at"]
                    }
                }
            )
        
        if email_opened:
            await self.db.campaign_contacts.update_one(
                {"id": contact_id},
                {
                    "$inc": {"emails_opened": 1},
                    "$set": {"updated_at": update_dict["updated_at"]}
                }
            )
        
        if email_replied:
            await self.db.campaign_contacts.update_one(
                {"id": contact_id},
                {
                    "$inc": {"emails_replied": 1},
                    "$set": {"updated_at": update_dict["updated_at"]}
                }
            )
    
    async def count_contacts(self, user_id: str, filters: Optional[Dict] = None) -> int:
        """Count contacts with optional filters"""
        query = {"user_id": user_id}
        if filters:
            query.update(filters)
        return await self.repository.count(query)
