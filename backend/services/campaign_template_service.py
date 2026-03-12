"""Service for managing campaign templates"""
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import logging

from models.campaign_template import CampaignTemplate, CampaignTemplateCreate, CampaignTemplateUpdate
from repositories.base_repository import GenericRepository

logger = logging.getLogger(__name__)

class CampaignTemplateService:
    """Service for campaign template management"""
    
    def __init__(self, db):
        self.repository = GenericRepository(db, "campaign_templates")
        self.db = db
    
    async def create_template(self, user_id: str, template_data: CampaignTemplateCreate) -> CampaignTemplate:
        """Create a new campaign template"""
        template = CampaignTemplate(
            user_id=user_id,
            **template_data.model_dump()
        )
        
        # Extract tags from template
        available_tags = self._extract_tags(template.subject + " " + template.body)
        template.available_tags.extend([tag for tag in available_tags if tag not in template.available_tags])
        
        await self.repository.create(template.model_dump())
        logger.info(f"Created template {template.id} for user {user_id}")
        return template
    
    async def get_template(self, user_id: str, template_id: str) -> Optional[CampaignTemplate]:
        """Get a template by ID"""
        template_dict = await self.repository.find_by_id(template_id)
        if not template_dict or template_dict.get("user_id") != user_id:
            return None
        return CampaignTemplate(**template_dict)
    
    async def list_templates(self, user_id: str, skip: int = 0, limit: int = 100,
                           template_type: Optional[str] = None,
                           is_active: Optional[bool] = None) -> List[CampaignTemplate]:
        """List all templates for a user with optional filters"""
        filters = {"user_id": user_id}
        
        if template_type:
            filters["template_type"] = template_type
        
        if is_active is not None:
            filters["is_active"] = is_active
        
        templates = await self.repository.find_many(filters, skip=skip, limit=limit)
        return [CampaignTemplate(**t) for t in templates]
    
    async def update_template(self, user_id: str, template_id: str,
                            update_data: CampaignTemplateUpdate) -> Optional[CampaignTemplate]:
        """Update a template"""
        # Verify ownership
        existing = await self.get_template(user_id, template_id)
        if not existing:
            return None
        
        update_dict = update_data.model_dump(exclude_unset=True)
        update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Re-extract tags if subject or body changed
        if "subject" in update_dict or "body" in update_dict:
            new_subject = update_dict.get("subject", existing.subject)
            new_body = update_dict.get("body", existing.body)
            available_tags = self._extract_tags(new_subject + " " + new_body)
            update_dict["available_tags"] = list(set(existing.available_tags + available_tags))
        
        await self.repository.update(template_id, update_dict)
        logger.info(f"Updated template {template_id}")
        
        return await self.get_template(user_id, template_id)
    
    async def delete_template(self, user_id: str, template_id: str) -> bool:
        """Delete a template"""
        # Verify ownership
        existing = await self.get_template(user_id, template_id)
        if not existing:
            return False
        
        # Check if template is used in any active campaigns
        active_campaigns = await self.db.campaigns.count_documents({
            "user_id": user_id,
            "status": {"$in": ["scheduled", "running"]},
            "$or": [
                {"initial_template_id": template_id},
                {"follow_up_config.template_ids": template_id}
            ]
        })
        
        if active_campaigns > 0:
            raise ValueError("Cannot delete template that is used in active campaigns")
        
        await self.repository.delete(template_id)
        logger.info(f"Deleted template {template_id}")
        return True
    
    def _extract_tags(self, text: str) -> List[str]:
        """Extract personalization tags from template text
        
        Tags are in format: {{tag_name}}
        """
        pattern = r'\{\{([^}]+)\}\}'
        tags = re.findall(pattern, text)
        return [tag.strip() for tag in tags]
    
    async def personalize_template(self, template: CampaignTemplate, 
                                  contact_data: Dict[str, Any]) -> Dict[str, str]:
        """Personalize template with contact data
        
        Args:
            template: Template to personalize
            contact_data: Contact data including custom_fields
        
        Returns:
            Dictionary with personalized subject and body
        """
        subject = template.subject
        body = template.body
        
        # Standard fields
        replacements = {
            "email": contact_data.get("email", ""),
            "first_name": contact_data.get("first_name", ""),
            "last_name": contact_data.get("last_name", ""),
            "company": contact_data.get("company", ""),
            "title": contact_data.get("title", ""),
            "linkedin_url": contact_data.get("linkedin_url", ""),
            "company_domain": contact_data.get("company_domain", "")
        }
        
        # Add custom fields
        custom_fields = contact_data.get("custom_fields", {})
        replacements.update(custom_fields)
        
        # Replace tags
        for tag, value in replacements.items():
            subject = subject.replace(f"{{{{{tag}}}}}", str(value))
            body = body.replace(f"{{{{{tag}}}}}", str(value))
        
        return {
            "subject": subject,
            "body": body
        }
    
    async def increment_usage(self, template_id: str) -> None:
        """Increment template usage count"""
        await self.db.campaign_templates.update_one(
            {"id": template_id},
            {
                "$inc": {"times_used": 1},
                "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
            }
        )
    
    async def count_templates(self, user_id: str, filters: Optional[Dict] = None) -> int:
        """Count templates with optional filters"""
        query = {"user_id": user_id}
        if filters:
            query.update(filters)
        return await self.repository.count(query)
