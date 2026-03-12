"""
Enhanced Test Routes for Complete Flow Testing
Allows users to test the entire system flow interactively
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from models.user import User
import uuid

from routes.auth_routes import get_current_user_from_token, get_db
from services.ai_agent_service import AIAgentService
from services.lead_nurturing_integration_service import LeadNurturingIntegrationService
from models.email import Email

router = APIRouter(prefix="/api/test", tags=["Testing"])

class TestEmailRequest(BaseModel):
    """Request model for test email"""
    from_email: str
    subject: str
    body: str
    simulate_reply: bool = False
    reply_body: Optional[str] = None
    thread_id: Optional[str] = None

class TestFlowResponse(BaseModel):
    """Response model for complete flow test"""
    success: bool
    steps: List[Dict[str, Any]]
    summary: Dict[str, Any]
    warnings: List[str] = []
    errors: List[str] = []

@router.post("/complete-flow", response_model=TestFlowResponse)
async def test_complete_flow(
    request: TestEmailRequest,
    user: User = Depends(get_current_user_from_token),
    db = Depends(get_db)
):
    """
    Test the complete email processing flow:
    1. Email received
    2. Intent classification
    3. Lead detection & qualification
    4. Draft generation (with nurturing questions)
    5. Follow-up creation
    6. Meeting detection & calendar
    7. Reply simulation (optional)
    8. Follow-up cancellation (if reply)
    """
    
    steps = []
    warnings = []
    errors = []
    user_id = user.id
    
    try:
        # Step 1: Create test email
        email_id = f"test_{uuid.uuid4().hex[:8]}"
        thread_id = request.thread_id or f"thread_{email_id}"
        
        # Get or create mock email account
        email_account = await db.email_accounts.find_one({
            "user_id": user_id,
            "is_active": True
        })
        
        if not email_account:
            # Create mock email account for testing
            email_account_id = str(uuid.uuid4())
            mock_account = {
                "id": email_account_id,
                "user_id": user_id,
                "provider": "test",
                "email": "test@example.com",
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.email_accounts.insert_one(mock_account)
            email_account_id = mock_account['id']
        else:
            email_account_id = email_account['id']
        
        test_email = Email(
            id=email_id,
            user_id=user_id,
            email_account_id=email_account_id,
            message_id=f"<{email_id}@test.com>",
            thread_id=thread_id,
            from_email=request.from_email,
            to_email=["test@example.com"],
            subject=request.subject,
            body=request.body,
            received_at=datetime.now(timezone.utc).isoformat(),
            status="pending"
        )
        
        await db.emails.insert_one(test_email.model_dump())
        
        steps.append({
            "step": 1,
            "name": "Email Received",
            "status": "success",
            "details": {
                "from": request.from_email,
                "subject": request.subject,
                "thread_id": thread_id
            }
        })
        
        # Step 2: Intent Classification
        ai_service = AIAgentService(db)
        intent_id, confidence, intent_doc = await ai_service.classify_intent(test_email, user_id)
        
        if not intent_id:
            warnings.append("No intent matched - will use default intent")
            intent_name = "Default"
        else:
            intent_name = intent_doc.get('name', 'Unknown')
        
        steps.append({
            "step": 2,
            "name": "Intent Classification",
            "status": "success",
            "details": {
                "intent": intent_name,
                "confidence": round(confidence * 100, 1),
                "is_lead": intent_doc.get('is_inbound_lead', False) if intent_doc else False,
                "qualification_enabled": intent_doc.get('enable_lead_qualification', False) if intent_doc else False,
                "nurturing_enabled": intent_doc.get('enable_lead_nurturing', False) if intent_doc else False
            }
        })
        
        # Step 3: Lead Processing (if applicable)
        lead_stage = None
        questions = []
        lead_id = None
        
        if intent_doc and intent_doc.get('is_inbound_lead'):
            integration_service = LeadNurturingIntegrationService(db)
            
            should_create, lead_stage, questions, lead_id = await integration_service.process_lead_email(
                user_id=user_id,
                email_id=email_id,
                email_content=request.body,
                from_email=request.from_email,
                intent_doc=intent_doc,
                thread_context=[]
            )
            
            # Get lead details if created
            lead_details = {}
            if lead_id:
                lead_doc = await db.inbound_leads.find_one({"id": lead_id})
                if lead_doc:
                    lead_details = {
                        "stage": lead_doc.get('stage'),
                        "score": lead_doc.get('qualification_score', 0),
                        "attempt": lead_doc.get('qualification_attempt', 0),
                        "questions_asked": len(lead_doc.get('nurturing_questions_asked', []))
                    }
            
            steps.append({
                "step": 3,
                "name": "Lead Qualification Processing",
                "status": "success",
                "details": {
                    "is_lead": True,
                    "stage": lead_stage,
                    "should_create_inbound_lead": should_create,
                    "questions_to_ask": len(questions),
                    "lead_id": lead_id,
                    **lead_details
                }
            })
            
            if questions:
                steps[-1]["details"]["questions"] = [q.get('question_text') for q in questions]
        else:
            steps.append({
                "step": 3,
                "name": "Lead Processing",
                "status": "skipped",
                "details": {
                    "reason": "Not a lead intent"
                }
            })
        
        # Step 4: Draft Generation
        draft, tokens = await ai_service.generate_draft(
            email=test_email,
            user_id=user_id,
            intent_id=intent_id,
            thread_context=[],
            nurturing_questions=questions if questions else None
        )
        
        steps.append({
            "step": 4,
            "name": "Draft Generation",
            "status": "success",
            "details": {
                "draft": draft,
                "tokens_used": tokens,
                "length": len(draft),
                "includes_questions": len(questions) > 0 if questions else False
            }
        })
        
        # Step 5: Meeting Detection
        is_meeting, meeting_confidence, meeting_details = await ai_service.detect_meeting(
            test_email,
            thread_context=[]
        )
        
        if is_meeting:
            steps.append({
                "step": 5,
                "name": "Meeting Detection",
                "status": "success",
                "details": {
                    "detected": True,
                    "confidence": round(meeting_confidence * 100, 1),
                    "title": meeting_details.get('title', 'N/A'),
                    "start_time": meeting_details.get('start_time', 'N/A'),
                    "would_create_calendar_event": True
                }
            })
        else:
            steps.append({
                "step": 5,
                "name": "Meeting Detection",
                "status": "skipped",
                "details": {
                    "detected": False
                }
            })
        
        # Step 6: Follow-up Timeline
        follow_up_dates = [
            (datetime.now(timezone.utc) + timedelta(days=2)).strftime('%Y-%m-%d'),
            (datetime.now(timezone.utc) + timedelta(days=4)).strftime('%Y-%m-%d'),
            (datetime.now(timezone.utc) + timedelta(days=6)).strftime('%Y-%m-%d')
        ]
        
        steps.append({
            "step": 6,
            "name": "Follow-up Creation",
            "status": "info",
            "details": {
                "would_create": 3,
                "schedule": follow_up_dates,
                "note": "Follow-ups created in production"
            }
        })
        
        # Step 7: Reply Simulation (if requested)
        if request.simulate_reply and request.reply_body:
            reply_email_id = f"test_{uuid.uuid4().hex[:8]}"
            
            reply_email = Email(
                id=reply_email_id,
                user_id=user_id,
                email_account_id=email_account_id,
                message_id=f"<{reply_email_id}@test.com>",
                thread_id=thread_id,
                from_email=request.from_email,
                to_email=["test@example.com"],
                subject="Re: " + request.subject,
                body=request.reply_body,
                received_at=(datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
                status="pending"
            )
            
            await db.emails.insert_one(reply_email.model_dump())
            
            steps.append({
                "step": 7,
                "name": "Reply Received",
                "status": "success",
                "details": {
                    "from": request.from_email,
                    "thread_id": thread_id,
                    "would_cancel_followups": True
                }
            })
            
            # Process reply if it's a lead
            if lead_id and intent_doc and intent_doc.get('is_inbound_lead'):
                integration_service = LeadNurturingIntegrationService(db)
                
                should_create, new_stage, new_questions, _ = await integration_service.process_lead_email(
                    user_id=user_id,
                    email_id=reply_email_id,
                    email_content=request.reply_body,
                    from_email=request.from_email,
                    intent_doc=intent_doc,
                    thread_context=[{"role": "user", "content": request.body}]
                )
                
                # Get updated lead
                lead_doc = await db.inbound_leads.find_one({"id": lead_id})
                if lead_doc:
                    steps.append({
                        "step": 8,
                        "name": "Lead Re-qualification",
                        "status": "success",
                        "details": {
                            "previous_stage": lead_stage,
                            "new_stage": new_stage,
                            "score": lead_doc.get('qualification_score', 0),
                            "attempt": lead_doc.get('qualification_attempt', 0),
                            "additional_questions": len(new_questions) if new_questions else 0,
                            "decision": "QUALIFIED" if new_stage == "qualified" else 
                                      "DISQUALIFIED" if new_stage == "unqualified" else
                                      "NEEDS MORE INFO"
                        }
                    })
        
        # Build summary
        summary = {
            "total_steps": len(steps),
            "successful_steps": len([s for s in steps if s['status'] == 'success']),
            "intent_matched": intent_id is not None,
            "lead_detected": bool(intent_doc and intent_doc.get('is_inbound_lead')),
            "meeting_detected": is_meeting,
            "draft_generated": bool(draft),
            "tokens_used": tokens,
            "test_mode": True
        }
        
        # Clean up test data
        await db.emails.delete_many({"id": {"$in": [email_id, reply_email_id] if request.simulate_reply else [email_id]}})
        if lead_id:
            await db.inbound_leads.delete_many({"id": lead_id})
        
        return TestFlowResponse(
            success=True,
            steps=steps,
            summary=summary,
            warnings=warnings,
            errors=errors
        )
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        errors.append(str(e))
        
        return TestFlowResponse(
            success=False,
            steps=steps,
            summary={"error": str(e)},
            warnings=warnings,
            errors=errors
        )

@router.get("/system-status")
async def get_system_status(
    user: User = Depends(get_current_user_from_token),
    db = Depends(get_db)
):
    """Get system configuration status for testing"""
    
    user_id = user.id
    
    # Check configuration
    intents_count = await db.intents.count_documents({"user_id": user_id, "is_active": True})
    kb_count = await db.knowledge_base.count_documents({"user_id": user_id, "is_active": True})
    qual_criteria = await db.lead_qualification_criteria.count_documents({"user_id": user_id, "is_active": True})
    nurt_config = await db.lead_nurturing_config.count_documents({"user_id": user_id, "is_active": True})
    
    user = await db.users.find_one({"id": user_id})
    
    return {
        "ready": intents_count > 0 and kb_count > 0,
        "configuration": {
            "intents": intents_count,
            "knowledge_base": kb_count,
            "qualification_criteria": qual_criteria,
            "nurturing_config": nurt_config,
            "persona_set": bool(user.get('persona')),
            "global_qualification_enabled": user.get('global_lead_qualification_enabled', False),
            "global_nurturing_enabled": user.get('global_lead_nurturing_enabled', False)
        },
        "warnings": []
        if intents_count > 0 and kb_count > 0
        else ["Configure intents and knowledge base before testing"]
    }
