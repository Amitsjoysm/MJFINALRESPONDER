"""
API routes for Inbound Lead Management
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from typing import List, Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from jose import jwt, JWTError

from models.inbound_lead import (
    InboundLead, LeadResponse, LeadDetailResponse, 
    LeadUpdate, LeadStageUpdate
)
from services.lead_agent_service import LeadAgentService
from config import config

router = APIRouter(prefix="/api/leads", tags=["leads"])

# Database connection
client = AsyncIOMotorClient(config.MONGO_URL)
db = client[config.DB_NAME]

def get_current_user_id(authorization: str = Header(...)):
    """Dependency to get current user ID from JWT token"""
    try:
        # Extract token from "Bearer <token>"
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, config.JWT_SECRET, algorithms=["HS256"])
        return payload.get("sub")  # JWT standard uses 'sub' for subject/user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")


@router.get("", response_model=List[LeadResponse])
async def list_leads(
    stage: Optional[str] = Query(None, description="Filter by stage"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by name, email, or company"),
    user_id: str = Depends(get_current_user_id)
):
    """
    List all leads for the current user with filtering
    """
    try:
        
        # Build query
        query = {"user_id": user_id}
        
        if is_active is not None:
            query["is_active"] = is_active
        
        if stage:
            query["stage"] = stage
        
        if priority:
            query["priority"] = priority
        
        if search:
            # Search in name, email, or company
            query["$or"] = [
                {"lead_name": {"$regex": search, "$options": "i"}},
                {"lead_email": {"$regex": search, "$options": "i"}},
                {"company_name": {"$regex": search, "$options": "i"}}
            ]
        
        # Get leads, sorted by updated_at descending
        leads = await db.inbound_leads.find(query).sort("updated_at", -1).to_list(1000)
        
        # Convert to response format
        response = []
        for lead_doc in leads:
            response.append(LeadResponse(
                id=lead_doc["id"],
                user_id=lead_doc["user_id"],
                lead_name=lead_doc.get("lead_name"),
                lead_email=lead_doc["lead_email"],
                company_name=lead_doc.get("company_name"),
                job_title=lead_doc.get("job_title"),
                phone=lead_doc.get("phone"),
                stage=lead_doc["stage"],
                score=lead_doc["score"],
                priority=lead_doc["priority"],
                emails_received=lead_doc["emails_received"],
                emails_sent=lead_doc["emails_sent"],
                last_contact_at=lead_doc.get("last_contact_at"),
                meeting_scheduled=lead_doc.get("meeting_scheduled", False),
                is_active=lead_doc["is_active"],
                created_at=lead_doc["created_at"],
                updated_at=lead_doc["updated_at"]
            ))
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{lead_id}", response_model=LeadDetailResponse)
async def get_lead(
    lead_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Get detailed information for a specific lead
    """
    try:
        
        lead_doc = await db.inbound_leads.find_one({
            "id": lead_id,
            "user_id": user_id
        })
        
        if not lead_doc:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        return LeadDetailResponse(
            id=lead_doc["id"],
            user_id=lead_doc["user_id"],
            lead_name=lead_doc.get("lead_name"),
            lead_email=lead_doc["lead_email"],
            company_name=lead_doc.get("company_name"),
            address=lead_doc.get("address"),
            phone=lead_doc.get("phone"),
            job_title=lead_doc.get("job_title"),
            company_size=lead_doc.get("company_size"),
            industry=lead_doc.get("industry"),
            specific_interests=lead_doc.get("specific_interests"),
            requirements=lead_doc.get("requirements"),
            stage=lead_doc["stage"],
            stage_history=lead_doc.get("stage_history", []),
            score=lead_doc["score"],
            priority=lead_doc["priority"],
            emails_received=lead_doc["emails_received"],
            emails_sent=lead_doc["emails_sent"],
            last_contact_at=lead_doc.get("last_contact_at"),
            last_reply_at=lead_doc.get("last_reply_at"),
            meeting_scheduled=lead_doc.get("meeting_scheduled", False),
            meeting_date=lead_doc.get("meeting_date"),
            activities=lead_doc.get("activities", []),
            notes=lead_doc.get("notes"),
            is_active=lead_doc["is_active"],
            qualification_checked=lead_doc.get("qualification_checked", False),
            qualification_score=lead_doc.get("qualification_score", 0),
            qualification_reasons=lead_doc.get("qualification_reasons", []),
            qualification_attempt=lead_doc.get("qualification_attempt", 0),
            nurturing_enabled=lead_doc.get("nurturing_enabled", False),
            nurturing_exchanges_count=lead_doc.get("nurturing_exchanges_count", 0),
            nurturing_questions_asked=lead_doc.get("nurturing_questions_asked", []),
            created_at=lead_doc["created_at"],
            updated_at=lead_doc["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{lead_id}", response_model=LeadDetailResponse)
async def update_lead(
    lead_id: str,
    update_data: LeadUpdate,
    user_id: str = Depends(get_current_user_id)
):
    """
    Update lead information
    """
    try:
        lead_service = LeadAgentService(db)
        
        # Verify lead exists and belongs to user
        lead_doc = await db.inbound_leads.find_one({
            "id": lead_id,
            "user_id": user_id
        })
        
        if not lead_doc:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Build update dict (only include provided fields)
        update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
        update_dict["updated_at"] = datetime.utcnow().isoformat()
        
        # Update lead
        await db.inbound_leads.update_one(
            {"id": lead_id},
            {"$set": update_dict}
        )
        
        # Add activity
        await lead_service.add_activity(
            lead_id,
            "manual_update",
            "Lead information updated manually",
            {"fields_updated": list(update_dict.keys())},
            user_id
        )
        
        # Get updated lead
        updated_doc = await db.inbound_leads.find_one({"id": lead_id})
        
        return LeadDetailResponse(
            id=updated_doc["id"],
            user_id=updated_doc["user_id"],
            lead_name=updated_doc.get("lead_name"),
            lead_email=updated_doc["lead_email"],
            company_name=updated_doc.get("company_name"),
            address=updated_doc.get("address"),
            phone=updated_doc.get("phone"),
            job_title=updated_doc.get("job_title"),
            company_size=updated_doc.get("company_size"),
            industry=updated_doc.get("industry"),
            specific_interests=updated_doc.get("specific_interests"),
            requirements=updated_doc.get("requirements"),
            stage=updated_doc["stage"],
            stage_history=updated_doc.get("stage_history", []),
            score=updated_doc["score"],
            priority=updated_doc["priority"],
            emails_received=updated_doc["emails_received"],
            emails_sent=updated_doc["emails_sent"],
            last_contact_at=updated_doc.get("last_contact_at"),
            last_reply_at=updated_doc.get("last_reply_at"),
            meeting_scheduled=updated_doc.get("meeting_scheduled", False),
            meeting_date=updated_doc.get("meeting_date"),
            activities=updated_doc.get("activities", []),
            notes=updated_doc.get("notes"),
            is_active=updated_doc["is_active"],
            qualification_checked=updated_doc.get("qualification_checked", False),
            qualification_score=updated_doc.get("qualification_score", 0),
            qualification_reasons=updated_doc.get("qualification_reasons", []),
            qualification_attempt=updated_doc.get("qualification_attempt", 0),
            nurturing_enabled=updated_doc.get("nurturing_enabled", False),
            nurturing_exchanges_count=updated_doc.get("nurturing_exchanges_count", 0),
            nurturing_questions_asked=updated_doc.get("nurturing_questions_asked", []),
            created_at=updated_doc["created_at"],
            updated_at=updated_doc["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{lead_id}/stage", response_model=LeadDetailResponse)
async def update_lead_stage(
    lead_id: str,
    stage_update: LeadStageUpdate,
    user_id: str = Depends(get_current_user_id)
):
    """
    Update lead stage (state transition)
    """
    try:
        lead_service = LeadAgentService(db)
        
        # Verify lead exists and belongs to user
        lead_doc = await db.inbound_leads.find_one({
            "id": lead_id,
            "user_id": user_id
        })
        
        if not lead_doc:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Transition stage
        updated_lead = await lead_service.transition_stage(
            lead_id,
            stage_update.stage,
            stage_update.reason,
            stage_update.performed_by or user_id
        )
        
        return LeadDetailResponse(
            id=updated_lead.id,
            user_id=updated_lead.user_id,
            lead_name=updated_lead.lead_name,
            lead_email=updated_lead.lead_email,
            company_name=updated_lead.company_name,
            address=updated_lead.address,
            phone=updated_lead.phone,
            job_title=updated_lead.job_title,
            company_size=updated_lead.company_size,
            industry=updated_lead.industry,
            specific_interests=updated_lead.specific_interests,
            requirements=updated_lead.requirements,
            stage=updated_lead.stage,
            stage_history=updated_lead.stage_history,
            score=updated_lead.score,
            priority=updated_lead.priority,
            emails_received=updated_lead.emails_received,
            emails_sent=updated_lead.emails_sent,
            last_contact_at=updated_lead.last_contact_at,
            last_reply_at=updated_lead.last_reply_at,
            meeting_scheduled=updated_lead.meeting_scheduled,
            meeting_date=updated_lead.meeting_date,
            activities=updated_lead.activities,
            notes=updated_lead.notes,
            is_active=updated_lead.is_active,
            qualification_checked=updated_lead.qualification_checked,
            qualification_score=updated_lead.qualification_score,
            qualification_reasons=updated_lead.qualification_reasons,
            qualification_attempt=updated_lead.qualification_attempt,
            nurturing_enabled=updated_lead.nurturing_enabled,
            nurturing_exchanges_count=updated_lead.nurturing_exchanges_count,
            nurturing_questions_asked=updated_lead.nurturing_questions_asked,
            created_at=updated_lead.created_at,
            updated_at=updated_lead.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{lead_id}/emails")
async def get_lead_emails(
    lead_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Get all emails associated with a lead
    """
    try:
        
        # Verify lead exists and belongs to user
        lead_doc = await db.inbound_leads.find_one({
            "id": lead_id,
            "user_id": user_id
        })
        
        if not lead_doc:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Get all emails for this lead
        email_ids = lead_doc.get("email_ids", [])
        emails = await db.emails.find({
            "id": {"$in": email_ids}
        }).sort("received_at", -1).to_list(1000)
        
        return {
            "lead_id": lead_id,
            "total_emails": len(emails),
            "emails": emails
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/summary")
async def get_lead_stats(
    user_id: str = Depends(get_current_user_id)
):
    """
    Get lead statistics summary
    """
    try:
        
        # Get all active leads
        leads = await db.inbound_leads.find({
            "user_id": user_id,
            "is_active": True
        }).to_list(10000)
        
        # Calculate stats
        total_leads = len(leads)
        by_stage = {"new": 0, "contacted": 0, "qualified": 0, "converted": 0}
        by_priority = {"low": 0, "medium": 0, "high": 0, "urgent": 0}
        total_score = 0
        meetings_scheduled = 0
        
        for lead in leads:
            stage = lead.get("stage", "new")
            if stage in by_stage:
                by_stage[stage] += 1
            
            priority = lead.get("priority", "medium")
            if priority in by_priority:
                by_priority[priority] += 1
            
            total_score += lead.get("score", 0)
            
            if lead.get("meeting_scheduled", False):
                meetings_scheduled += 1
        
        avg_score = total_score / total_leads if total_leads > 0 else 0
        
        return {
            "total_leads": total_leads,
            "by_stage": by_stage,
            "by_priority": by_priority,
            "average_score": round(avg_score, 1),
            "meetings_scheduled": meetings_scheduled,
            "conversion_rate": round((by_stage["converted"] / total_leads * 100), 1) if total_leads > 0 else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
