"""
Interactive Multi-Turn Test Session API
Allows users to simulate complete email conversations with full visibility
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

router = APIRouter(prefix="/api/test-session", tags=["Test Session"])

class SendMessageRequest(BaseModel):
    """Request to send a message in test session"""
    session_id: Optional[str] = None  # Omit for new session
    from_email: str
    subject: str
    body: str
    is_reply: bool = False  # Is this a reply to previous message

class TestSessionResponse(BaseModel):
    """Response for test session"""
    session_id: str
    conversation_history: List[Dict[str, Any]]
    follow_ups: List[Dict[str, Any]]
    lead_info: Optional[Dict[str, Any]]
    calendar_events: List[Dict[str, Any]]
    agent_actions: List[Dict[str, Any]]
    summary: Dict[str, Any]

@router.post("/send-message", response_model=TestSessionResponse)
async def send_test_message(
    request: SendMessageRequest,
    user: User = Depends(get_current_user_from_token),
    db = Depends(get_db)
):
    """
    Send a message in test session and get complete response with all agent actions
    
    This simulates the complete production flow:
    1. Email received
    2. Intent classification
    3. Lead processing (if applicable)
    4. Draft generation
    5. Validation
    6. Follow-up creation/cancellation
    7. Calendar event creation (if meeting)
    """
    
    user_id = user.id
    
    try:
        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())
        
        # Get session data
        test_sessions = db['test_sessions']
        session_data = await test_sessions.find_one({"session_id": session_id, "user_id": user_id})
        
        if not session_data:
            # Create new session
            thread_id = f"test_thread_{uuid.uuid4().hex[:8]}"
            session_data = {
                "session_id": session_id,
                "user_id": user_id,
                "thread_id": thread_id,
                "from_email": request.from_email,
                "conversation": [],
                "follow_ups": [],
                "lead_id": None,
                "calendar_events": [],
                "agent_actions": [],
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await test_sessions.insert_one(session_data)
        
        thread_id = session_data['thread_id']
        
        # Create test email
        email_id = f"test_{uuid.uuid4().hex[:8]}"
        
        # Get or create mock email account
        email_account = await db.email_accounts.find_one({
            "user_id": user_id,
            "is_active": True
        })
        
        if not email_account:
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
            subject=request.subject if not request.is_reply else f"Re: {request.subject}",
            body=request.body,
            received_at=datetime.now(timezone.utc).isoformat(),
            status="pending"
        )
        
        await db.emails.insert_one(test_email.model_dump())
        
        # Add to conversation history
        conversation_entry = {
            "email_id": email_id,
            "direction": "inbound",
            "from": request.from_email,
            "to": "test@example.com",
            "subject": test_email.subject,
            "body": request.body,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # STEP 1: Intent Classification
        ai_service = AIAgentService(db)
        intent_id, confidence, intent_doc = await ai_service.classify_intent(test_email, user_id)
        
        intent_action = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": "intent_classified",
            "details": {
                "intent": intent_doc.get('name') if intent_doc else "No match",
                "confidence": round(confidence * 100, 1),
                "is_lead": intent_doc.get('is_inbound_lead', False) if intent_doc else False
            }
        }
        
        # STEP 2: Lead Processing (if applicable)
        lead_id = session_data.get('lead_id')
        questions_to_ask = []
        lead_action = None
        
        if intent_doc and intent_doc.get('is_inbound_lead'):
            integration_service = LeadNurturingIntegrationService(db)
            
            # Build thread context for lead processing (role/content format)
            lead_thread_context = []
            for msg in session_data.get('conversation', []):
                lead_thread_context.append({
                    "role": "user" if msg['direction'] == "inbound" else "assistant",
                    "content": msg['body']
                })
            
            should_create, lead_stage, questions, returned_lead_id = await integration_service.process_lead_email(
                user_id=user_id,
                email_id=email_id,
                email_content=request.body,
                from_email=request.from_email,
                intent_doc=intent_doc,
                thread_context=lead_thread_context
            )
            
            # Update lead_id in session
            if returned_lead_id:
                lead_id = returned_lead_id
            
            questions_to_ask = questions or []
            
            # Get lead details
            if lead_id:
                lead_doc = await db.inbound_leads.find_one({"id": lead_id})
                if lead_doc:
                    lead_action = {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "action": "lead_processed",
                        "details": {
                            "lead_id": lead_id,
                            "stage": lead_doc.get('stage'),
                            "score": lead_doc.get('qualification_score', 0),
                            "attempt": lead_doc.get('qualification_attempt', 0),
                            "questions_to_ask": questions_to_ask,  # Return actual questions list
                            "should_create_inbound": should_create
                        }
                    }
        
        # STEP 3: Cancel follow-ups if this is a reply
        cancelled_followups = []
        if request.is_reply and session_data.get('follow_ups'):
            for followup_id in session_data['follow_ups']:
                # Mark as cancelled
                cancelled_followups.append({
                    "followup_id": followup_id,
                    "status": "cancelled",
                    "reason": "Reply received in thread",
                    "cancelled_at": datetime.now(timezone.utc).isoformat()
                })
            
            if cancelled_followups:
                cancellation_action = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "action": "followups_cancelled",
                    "details": {
                        "count": len(cancelled_followups),
                        "reason": "Reply received in thread",
                        "followup_ids": [f['followup_id'] for f in cancelled_followups]
                    }
                }
                session_data.setdefault('agent_actions', []).append(cancellation_action)
        
        # STEP 4: Meeting Detection
        is_meeting, meeting_confidence, meeting_details = await ai_service.detect_meeting(
            test_email,
            thread_context=[]
        )
        
        meeting_action = None
        calendar_event = None
        
        if is_meeting and meeting_confidence > 0.5:
            # Simulate calendar event creation
            event_id = str(uuid.uuid4())
            
            calendar_event = {
                "event_id": event_id,
                "title": meeting_details.get('title', 'Meeting'),
                "start_time": meeting_details.get('start_time'),
                "duration": meeting_details.get('duration', 60),
                "attendees": [request.from_email, "test@example.com"],
                "meet_link": f"https://meet.google.com/test-{uuid.uuid4().hex[:8]}",
                "reminder_time": "1 hour before",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            meeting_action = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action": "meeting_detected",
                "details": {
                    "detected": True,
                    "confidence": round(meeting_confidence * 100, 1),
                    **meeting_details,
                    "calendar_event_id": event_id
                }
            }
        
        # STEP 5: Draft Generation
        # Build thread context for draft generation (from/subject/body format)
        draft_thread_context = []
        for msg in session_data.get('conversation', []):
            draft_thread_context.append({
                "from": msg.get('from'),
                "to": msg.get('to'),
                "subject": msg.get('subject'),
                "body": msg.get('body'),
                "received_at": msg.get('timestamp'),
                "draft_sent": msg.get('draft_sent') if msg['direction'] == 'outbound' else None
            })
        
        draft, tokens = await ai_service.generate_draft(
            email=test_email,
            user_id=user_id,
            intent_id=intent_id,
            thread_context=draft_thread_context,
            nurturing_questions=questions_to_ask if questions_to_ask else None,
            calendar_event=calendar_event if calendar_event else None,
            meeting_info={
                "detected": is_meeting,
                "confidence": meeting_confidence,
                "details": meeting_details
            } if is_meeting else None
        )
        
        draft_action = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": "draft_generated",
            "details": {
                "draft": draft,
                "tokens_used": tokens,
                "length": len(draft),
                "includes_questions": len(questions_to_ask) > 0,
                "includes_calendar": calendar_event is not None
            }
        }
        
        # STEP 6: Draft Validation
        is_valid, validation_issues, validation_tokens = await ai_service.validate_draft(
            draft=draft,
            original_email=test_email,
            thread_context=draft_thread_context
        )
        
        validation_action = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": "draft_validated",
            "details": {
                "valid": is_valid,
                "issues": validation_issues if validation_issues else []
            }
        }
        
        # STEP 7: Create new follow-ups
        # Only create follow-ups if:
        # 1. Draft is valid
        # 2. Lead is still awaiting info (not qualified/unqualified)
        # 3. OR no lead processing (non-lead emails)
        new_followups = []
        
        # Check lead stage if lead exists
        lead_stage = None
        if lead_id:
            lead_doc = await db.inbound_leads.find_one({"id": lead_id})
            if lead_doc:
                lead_stage = lead_doc.get('stage')
        
        should_create_followups = is_valid and (
            not lead_id or  # No lead (non-lead email)
            lead_stage == 'awaiting_info'  # Lead needs more info
        )
        
        if should_create_followups:
            for days in [2, 4, 6]:
                followup_id = str(uuid.uuid4())
                scheduled_date = (datetime.now(timezone.utc) + timedelta(days=days))
                
                new_followups.append({
                    "followup_id": followup_id,
                    "scheduled_at": scheduled_date.isoformat(),
                    "scheduled_date": scheduled_date.strftime('%Y-%m-%d'),
                    "days_from_now": days,
                    "status": "pending",
                    "thread_id": thread_id
                })
            
            followup_action = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action": "followups_created",
                "details": {
                    "count": len(new_followups),
                    "schedule": [f['scheduled_date'] for f in new_followups],
                    "followup_ids": [f['followup_id'] for f in new_followups]
                }
            }
        
        # Add response to conversation
        response_entry = {
            "email_id": f"response_{email_id}",
            "direction": "outbound",
            "from": "test@example.com",
            "to": request.from_email,
            "subject": f"Re: {request.subject}",
            "body": draft,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Update session
        updated_conversation = session_data.get('conversation', []) + [conversation_entry, response_entry]
        updated_actions = session_data.get('agent_actions', [])
        
        # Add all actions
        updated_actions.append(intent_action)
        if lead_action:
            updated_actions.append(lead_action)
        if cancelled_followups:
            updated_actions.append(cancellation_action)
        if meeting_action:
            updated_actions.append(meeting_action)
        updated_actions.append(draft_action)
        updated_actions.append(validation_action)
        if is_valid and new_followups:
            updated_actions.append(followup_action)
        
        # Build updated follow-ups list (cancelled + new)
        all_followups = cancelled_followups + new_followups
        
        # Add calendar event if created
        updated_calendar = session_data.get('calendar_events', [])
        if calendar_event:
            updated_calendar.append(calendar_event)
        
        # Update session in DB
        await test_sessions.update_one(
            {"session_id": session_id},
            {"$set": {
                "conversation": updated_conversation,
                "follow_ups": [f['followup_id'] for f in new_followups],  # Only track active ones
                "lead_id": lead_id,
                "calendar_events": updated_calendar,
                "agent_actions": updated_actions,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Get lead info
        lead_info = None
        if lead_id:
            lead_doc = await db.inbound_leads.find_one({"id": lead_id})
            if lead_doc:
                lead_info = {
                    "lead_id": lead_id,
                    "stage": lead_doc.get('stage'),
                    "score": lead_doc.get('qualification_score', 0),
                    "attempt": lead_doc.get('qualification_attempt', 0),
                    "nurturing_exchanges": lead_doc.get('nurturing_exchanges_count', 0),
                    "questions_asked": len(lead_doc.get('nurturing_questions_asked', [])),
                    "qualification_checked": lead_doc.get('qualification_checked', False),
                    "qualification_reasons": lead_doc.get('qualification_reasons', [])
                }
        
        # Build summary
        summary = {
            "total_messages": len(updated_conversation),
            "active_followups": len(new_followups),
            "cancelled_followups": len(cancelled_followups),
            "calendar_events": len(updated_calendar),
            "lead_stage": lead_info['stage'] if lead_info else None,
            "lead_score": lead_info['score'] if lead_info else None
        }
        
        return TestSessionResponse(
            session_id=session_id,
            conversation_history=updated_conversation,
            follow_ups=all_followups,
            lead_info=lead_info,
            calendar_events=updated_calendar,
            agent_actions=updated_actions,
            summary=summary
        )
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"Test session error: {str(e)}")

@router.delete("/session/{session_id}")
async def delete_test_session(
    session_id: str,
    user: User = Depends(get_current_user_from_token),
    db = Depends(get_db)
):
    """Delete test session and cleanup all test data"""
    
    user_id = user.id
    
    try:
        # Get session
        test_sessions = db['test_sessions']
        session = await test_sessions.find_one({"session_id": session_id, "user_id": user_id})
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Delete test emails
        email_ids = [msg['email_id'] for msg in session.get('conversation', []) if msg.get('email_id')]
        if email_ids:
            await db.emails.delete_many({"id": {"$in": email_ids}})
        
        # Delete test lead
        if session.get('lead_id'):
            await db.inbound_leads.delete_many({"id": session['lead_id']})
        
        # Delete session
        await test_sessions.delete_one({"session_id": session_id})
        
        return {"message": "Test session deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/session/{session_id}", response_model=TestSessionResponse)
async def get_test_session(
    session_id: str,
    user: User = Depends(get_current_user_from_token),
    db = Depends(get_db)
):
    """Get existing test session"""
    
    user_id = user.id
    
    try:
        test_sessions = db['test_sessions']
        session = await test_sessions.find_one({"session_id": session_id, "user_id": user_id})
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get lead info
        lead_info = None
        if session.get('lead_id'):
            lead_doc = await db.inbound_leads.find_one({"id": session['lead_id']})
            if lead_doc:
                lead_info = {
                    "lead_id": session['lead_id'],
                    "stage": lead_doc.get('stage'),
                    "score": lead_doc.get('qualification_score', 0),
                    "attempt": lead_doc.get('qualification_attempt', 0),
                    "nurturing_exchanges": lead_doc.get('nurturing_exchanges_count', 0),
                    "questions_asked": len(lead_doc.get('nurturing_questions_asked', [])),
                    "qualification_checked": lead_doc.get('qualification_checked', False)
                }
        
        # Build follow-ups from actions
        follow_ups = []
        for action in session.get('agent_actions', []):
            if action['action'] == 'followups_created':
                followup_ids = action['details'].get('followup_ids', [])
                schedule = action['details'].get('schedule', [])
                for i, fid in enumerate(followup_ids):
                    follow_ups.append({
                        "followup_id": fid,
                        "scheduled_date": schedule[i] if i < len(schedule) else "N/A",
                        "status": "pending"
                    })
            elif action['action'] == 'followups_cancelled':
                for fid in action['details'].get('followup_ids', []):
                    # Find and update
                    for fu in follow_ups:
                        if fu['followup_id'] == fid:
                            fu['status'] = 'cancelled'
        
        summary = {
            "total_messages": len(session.get('conversation', [])),
            "active_followups": len([f for f in follow_ups if f['status'] == 'pending']),
            "cancelled_followups": len([f for f in follow_ups if f['status'] == 'cancelled']),
            "calendar_events": len(session.get('calendar_events', [])),
            "lead_stage": lead_info['stage'] if lead_info else None,
            "lead_score": lead_info['score'] if lead_info else None
        }
        
        return TestSessionResponse(
            session_id=session_id,
            conversation_history=session.get('conversation', []),
            follow_ups=follow_ups,
            lead_info=lead_info,
            calendar_events=session.get('calendar_events', []),
            agent_actions=session.get('agent_actions', []),
            summary=summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
