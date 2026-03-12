"""Service for managing campaigns and campaign execution"""
import asyncio
import random
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import logging

from models.campaign import Campaign, CampaignCreate, CampaignUpdate
from models.campaign_email import CampaignEmail
from models.campaign_follow_up import CampaignFollowUp
from repositories.base_repository import GenericRepository
from services.campaign_contact_service import CampaignContactService
from services.campaign_template_service import CampaignTemplateService
from services.campaign_analytics_service import CampaignAnalyticsService

logger = logging.getLogger(__name__)

class CampaignService:
    """Service for campaign management and execution"""
    
    def __init__(self, db):
        self.repository = GenericRepository(db, "campaigns")
        self.campaign_email_repo = GenericRepository(db, "campaign_emails")
        self.campaign_follow_up_repo = GenericRepository(db, "campaign_follow_ups")
        self.contact_service = CampaignContactService(db)
        self.template_service = CampaignTemplateService(db)
        self.analytics_service = CampaignAnalyticsService(db)
        self.db = db
    
    async def create_campaign(self, user_id: str, campaign_data: CampaignCreate) -> Campaign:
        """Create a new campaign"""
        # Validate template exists
        template = await self.template_service.get_template(user_id, campaign_data.initial_template_id)
        if not template:
            raise ValueError("Initial template not found")
        
        # Validate follow-up templates
        for template_id in campaign_data.follow_up_config.template_ids:
            follow_up_template = await self.template_service.get_template(user_id, template_id)
            if not follow_up_template:
                raise ValueError(f"Follow-up template {template_id} not found")
        
        # Validate email accounts
        for account_id in campaign_data.email_account_ids:
            account = await self.db.email_accounts.find_one({"id": account_id, "user_id": user_id})
            if not account:
                raise ValueError(f"Email account {account_id} not found")
        
        # Calculate total contacts from all sources
        total_contacts = 0
        all_contact_ids = set(campaign_data.contact_ids)
        
        # Add contacts from lists
        if campaign_data.list_ids:
            from services.contact_list_service import ContactListService
            list_service = ContactListService(self.db)
            for list_id in campaign_data.list_ids:
                contact_list = await list_service.get_list(user_id, list_id)
                if contact_list:
                    all_contact_ids.update(contact_list.contact_ids)
        
        # Add contacts from tags
        if campaign_data.contact_tags:
            tag_contacts = await self.contact_service.list_contacts(
                user_id,
                filters={"tags": {"$in": campaign_data.contact_tags}},
                limit=10000
            )
            all_contact_ids.update([c.id for c in tag_contacts])
        
        total_contacts = len(all_contact_ids)
        
        campaign = Campaign(
            user_id=user_id,
            total_contacts=total_contacts,
            emails_pending=total_contacts,
            **campaign_data.model_dump()
        )
        
        await self.repository.create(campaign.model_dump())
        logger.info(f"Created campaign {campaign.id} for user {user_id} with {total_contacts} contacts")
        return campaign
    
    async def get_campaign(self, user_id: str, campaign_id: str) -> Optional[Campaign]:
        """Get a campaign by ID"""
        campaign_dict = await self.repository.find_by_id(campaign_id)
        if not campaign_dict or campaign_dict.get("user_id") != user_id:
            return None
        return Campaign(**campaign_dict)
    
    async def list_campaigns(self, user_id: str, skip: int = 0, limit: int = 100,
                           status: Optional[str] = None) -> List[Campaign]:
        """List all campaigns for a user with optional filters"""
        filters = {"user_id": user_id}
        
        if status:
            filters["status"] = status
        
        campaigns = await self.repository.find_many(filters, skip=skip, limit=limit)
        return [Campaign(**c) for c in campaigns]
    
    async def update_campaign(self, user_id: str, campaign_id: str,
                            update_data: CampaignUpdate) -> Optional[Campaign]:
        """Update a campaign (only allowed in draft status)"""
        # Verify ownership
        existing = await self.get_campaign(user_id, campaign_id)
        if not existing:
            return None
        
        # Only allow updates for draft campaigns
        if existing.status not in ["draft", "paused"]:
            raise ValueError("Can only update campaigns in draft or paused status")
        
        update_dict = update_data.model_dump(exclude_unset=True)
        update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Recalculate total contacts if changed
        if "contact_ids" in update_dict or "contact_tags" in update_dict:
            contact_ids = update_dict.get("contact_ids", existing.contact_ids)
            contact_tags = update_dict.get("contact_tags", existing.contact_tags)
            
            total_contacts = 0
            if contact_ids:
                total_contacts = len(contact_ids)
            elif contact_tags:
                total_contacts = await self.contact_service.count_contacts(
                    user_id,
                    {"tags": {"$in": contact_tags}}
                )
            
            update_dict["total_contacts"] = total_contacts
        
        await self.repository.update(campaign_id, update_dict)
        logger.info(f"Updated campaign {campaign_id}")
        
        return await self.get_campaign(user_id, campaign_id)
    
    async def delete_campaign(self, user_id: str, campaign_id: str) -> bool:
        """Delete a campaign (only allowed in draft status)"""
        # Verify ownership
        existing = await self.get_campaign(user_id, campaign_id)
        if not existing:
            return False
        
        # Only allow deletion for draft campaigns
        if existing.status != "draft":
            raise ValueError("Can only delete campaigns in draft status")
        
        await self.repository.delete(campaign_id)
        logger.info(f"Deleted campaign {campaign_id}")
        return True
    
    async def start_campaign(self, user_id: str, campaign_id: str) -> Campaign:
        """Start a campaign"""
        campaign = await self.get_campaign(user_id, campaign_id)
        if not campaign:
            raise ValueError("Campaign not found")
        
        if campaign.status not in ["draft", "paused"]:
            raise ValueError(f"Cannot start campaign with status: {campaign.status}")
        
        # Update status
        update_dict = {
            "status": "running",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if campaign.status == "paused":
            update_dict["last_resumed_at"] = datetime.now(timezone.utc).isoformat()
        
        await self.repository.update(campaign_id, update_dict)
        logger.info(f"Started campaign {campaign_id}")
        
        # Initialize campaign emails
        await self._initialize_campaign_emails(campaign)
        
        return await self.get_campaign(user_id, campaign_id)
    
    async def pause_campaign(self, user_id: str, campaign_id: str) -> Campaign:
        """Pause a running campaign"""
        campaign = await self.get_campaign(user_id, campaign_id)
        if not campaign:
            raise ValueError("Campaign not found")
        
        if campaign.status != "running":
            raise ValueError("Can only pause running campaigns")
        
        await self.repository.update(campaign_id, {
            "status": "paused",
            "last_paused_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        })
        logger.info(f"Paused campaign {campaign_id}")
        
        return await self.get_campaign(user_id, campaign_id)
    
    async def resume_campaign(self, user_id: str, campaign_id: str) -> Campaign:
        """Resume a paused campaign"""
        campaign = await self.get_campaign(user_id, campaign_id)
        if not campaign:
            raise ValueError("Campaign not found")
        
        if campaign.status != "paused":
            raise ValueError("Can only resume paused campaigns")
        
        await self.repository.update(campaign_id, {
            "status": "running",
            "last_resumed_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        })
        logger.info(f"Resumed campaign {campaign_id}")
        
        return await self.get_campaign(user_id, campaign_id)
    
    async def stop_campaign(self, user_id: str, campaign_id: str) -> Campaign:
        """Stop a campaign (cannot be resumed)"""
        campaign = await self.get_campaign(user_id, campaign_id)
        if not campaign:
            raise ValueError("Campaign not found")
        
        if campaign.status in ["completed", "stopped"]:
            raise ValueError(f"Campaign already {campaign.status}")
        
        await self.repository.update(campaign_id, {
            "status": "stopped",
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        })
        logger.info(f"Stopped campaign {campaign_id}")
        
        # Cancel all pending campaign follow-ups
        await self._cancel_campaign_follow_ups(campaign_id, "campaign_stopped")
        
        return await self.get_campaign(user_id, campaign_id)
    
    async def _initialize_campaign_emails(self, campaign: Campaign) -> None:
        """Initialize campaign emails for all contacts"""
        # Get contacts
        contacts = []
        
        # Priority: contact_ids > list_ids > contact_tags
        if campaign.contact_ids:
            for contact_id in campaign.contact_ids:
                contact = await self.contact_service.get_contact(campaign.user_id, contact_id)
                if contact:
                    contacts.append(contact)
        elif campaign.list_ids:
            # Get contacts from lists
            for list_id in campaign.list_ids:
                contact_list = await self.db.contact_lists.find_one({"id": list_id, "user_id": campaign.user_id})
                if contact_list and contact_list.get("contact_ids"):
                    for contact_id in contact_list["contact_ids"]:
                        contact = await self.contact_service.get_contact(campaign.user_id, contact_id)
                        if contact and contact not in contacts:
                            contacts.append(contact)
        elif campaign.contact_tags:
            contacts = await self.contact_service.list_contacts(
                campaign.user_id,
                tags=campaign.contact_tags,
                limit=10000  # Large limit for now
            )
        
        # Get template
        template = await self.template_service.get_template(
            campaign.user_id, 
            campaign.initial_template_id
        )
        
        # Create campaign emails
        email_account_index = 0
        created_emails_count = 0
        
        for contact in contacts:
            # Skip if contact is not active
            if contact.status != "active":
                continue
            
            # Round-robin email account selection
            email_account_id = campaign.email_account_ids[email_account_index % len(campaign.email_account_ids)]
            email_account_index += 1
            
            # Personalize template
            personalized = await self.template_service.personalize_template(
                template,
                contact.model_dump()
            )
            
            # Create campaign email
            campaign_email = CampaignEmail(
                user_id=campaign.user_id,
                campaign_id=campaign.id,
                contact_id=contact.id,
                email_account_id=email_account_id,
                to_email=contact.email,
                subject=personalized["subject"],
                body=personalized["body"],
                email_type="initial",
                status="pending"
            )
            
            await self.campaign_email_repo.create(campaign_email.model_dump())
            created_emails_count += 1
        
        # Update campaign with actual email count
        await self.repository.update(campaign.id, {
            "total_contacts": created_emails_count,
            "emails_pending": created_emails_count,
            "updated_at": datetime.now(timezone.utc).isoformat()
        })
        
        logger.info(f"Initialized {created_emails_count} campaign emails for campaign {campaign.id}")
    
    async def _cancel_campaign_follow_ups(self, campaign_id: str, reason: str) -> None:
        """Cancel all pending follow-ups for a campaign"""
        await self.db.campaign_follow_ups.update_many(
            {
                "campaign_id": campaign_id,
                "status": {"$in": ["pending", "scheduled"]}
            },
            {
                "$set": {
                    "status": "cancelled",
                    "cancelled_reason": reason,
                    "cancelled_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
    
    async def get_campaign_analytics(self, user_id: str, campaign_id: str) -> Dict[str, Any]:
        """Get comprehensive campaign analytics"""
        campaign = await self.get_campaign(user_id, campaign_id)
        if not campaign:
            raise ValueError("Campaign not found")
        
        # Use the new analytics service
        analytics = await self.analytics_service.get_campaign_analytics(campaign_id)
        
        return analytics

