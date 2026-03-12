"""HubSpot CRM service for syncing leads"""
import httpx
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import logging
from utils.encryption import get_encryption_service

logger = logging.getLogger(__name__)

class HubSpotService:
    """Service for interacting with HubSpot CRM APIs"""
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://api.hubapi.com"
    
    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers for HubSpot API requests"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    async def create_contact(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a contact in HubSpot CRM"""
        logger.info(f"Creating HubSpot contact for: {lead_data.get('email')}")
        
        contact_properties = {
            "firstname": lead_data.get("name", "").split()[0] if lead_data.get("name") else "",
            "lastname": " ".join(lead_data.get("name", "").split()[1:]) if lead_data.get("name") and len(lead_data.get("name", "").split()) > 1 else "",
            "email": lead_data.get("email"),
        }
        
        # Add optional fields
        if lead_data.get("phone"):
            contact_properties["phone"] = lead_data.get("phone")
        if lead_data.get("company"):
            contact_properties["company"] = lead_data.get("company")
        if lead_data.get("job_title"):
            contact_properties["jobtitle"] = lead_data.get("job_title")
        if lead_data.get("website"):
            contact_properties["website"] = lead_data.get("website")
        if lead_data.get("lead_source"):
            contact_properties["hs_lead_status"] = lead_data.get("lead_source")
        
        contact_data = {
            "properties": contact_properties
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/crm/v3/objects/contacts",
                    json=contact_data,
                    headers=self._get_headers()
                )
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    logger.info(f"Successfully created contact in HubSpot: {result.get('id')}")
                    return result
                elif response.status_code == 409:
                    # Contact already exists with this email
                    logger.info(f"Contact already exists, attempting to update...")
                    return await self.update_contact_by_email(lead_data)
                else:
                    error_detail = response.json() if response.text else {"message": "Unknown error"}
                    logger.error(f"Failed to create contact: {error_detail}")
                    raise Exception(f"Failed to create contact: {error_detail.get('message', 'Unknown error')}")
                    
            except httpx.HTTPError as e:
                logger.error(f"HTTP error creating contact: {e}")
                raise Exception(f"Failed to connect to HubSpot: {str(e)}")
    
    async def update_contact_by_email(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update contact using email as unique identifier"""
        logger.info(f"Updating HubSpot contact by email: {lead_data.get('email')}")
        
        # First, search for the contact by email
        email = lead_data.get("email")
        search_url = f"{self.base_url}/crm/v3/objects/contacts/search"
        
        search_data = {
            "filterGroups": [{
                "filters": [{
                    "propertyName": "email",
                    "operator": "EQ",
                    "value": email
                }]
            }]
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Search for contact
                search_response = await client.post(
                    search_url,
                    json=search_data,
                    headers=self._get_headers()
                )
                
                if search_response.status_code != 200:
                    raise Exception("Failed to search for contact")
                
                search_results = search_response.json()
                if not search_results.get("results"):
                    raise Exception("Contact not found")
                
                contact_id = search_results["results"][0]["id"]
                
                # Update the contact
                contact_properties = {
                    "firstname": lead_data.get("name", "").split()[0] if lead_data.get("name") else "",
                    "lastname": " ".join(lead_data.get("name", "").split()[1:]) if lead_data.get("name") and len(lead_data.get("name", "").split()) > 1 else "",
                }
                
                if lead_data.get("phone"):
                    contact_properties["phone"] = lead_data.get("phone")
                if lead_data.get("company"):
                    contact_properties["company"] = lead_data.get("company")
                if lead_data.get("job_title"):
                    contact_properties["jobtitle"] = lead_data.get("job_title")
                if lead_data.get("website"):
                    contact_properties["website"] = lead_data.get("website")
                
                update_data = {"properties": contact_properties}
                
                update_response = await client.patch(
                    f"{self.base_url}/crm/v3/objects/contacts/{contact_id}",
                    json=update_data,
                    headers=self._get_headers()
                )
                
                if update_response.status_code == 200:
                    result = update_response.json()
                    logger.info(f"Successfully updated contact in HubSpot: {contact_id}")
                    return result
                else:
                    raise Exception(f"Failed to update contact: {update_response.text}")
                    
            except Exception as e:
                logger.error(f"Error updating contact: {e}")
                raise
    
    async def get_contacts(self, limit: int = 100, after: Optional[str] = None) -> Dict[str, Any]:
        """Fetch contacts from HubSpot"""
        logger.info(f"Fetching contacts from HubSpot (limit: {limit})")
        
        params = {"limit": limit}
        if after:
            params["after"] = after
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/crm/v3/objects/contacts",
                    params=params,
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Successfully fetched {len(result.get('results', []))} contacts")
                    return result
                else:
                    raise Exception(f"Failed to fetch contacts: {response.text}")
                    
            except httpx.HTTPError as e:
                logger.error(f"HTTP error fetching contacts: {e}")
                raise Exception(f"Failed to connect to HubSpot: {str(e)}")
    
    async def sync_lead_to_hubspot(self, lead: Dict[str, Any]) -> Dict[str, str]:
        """Sync a single lead to HubSpot"""
        try:
            result = await self.create_contact(lead)
            return {
                "status": "success",
                "hubspot_contact_id": result.get("id"),
                "message": "Lead successfully synced to HubSpot"
            }
        except Exception as e:
            logger.error(f"Failed to sync lead: {e}")
            return {
                "status": "failed",
                "message": str(e)
            }
    
    async def sync_multiple_leads(self, leads: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Sync multiple leads to HubSpot"""
        logger.info(f"Syncing {len(leads)} leads to HubSpot")
        
        results = {
            "total": len(leads),
            "successful": 0,
            "failed": 0,
            "details": []
        }
        
        for lead in leads:
            sync_result = await self.sync_lead_to_hubspot(lead)
            
            if sync_result["status"] == "success":
                results["successful"] += 1
            else:
                results["failed"] += 1
            
            results["details"].append({
                "lead_email": lead.get("email"),
                "status": sync_result["status"],
                "message": sync_result.get("message"),
                "hubspot_id": sync_result.get("hubspot_contact_id")
            })
        
        logger.info(f"Sync completed: {results['successful']} successful, {results['failed']} failed")
        return results
