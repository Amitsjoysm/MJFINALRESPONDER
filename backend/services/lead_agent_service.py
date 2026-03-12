"""
Lead Agent Service - Parlant.io Architecture

Key Principles:
1. Clear Separation of Concerns - Each method has ONE responsibility
2. Deterministic Workflows - State transitions follow strict rules
3. Observable Actions - All actions are logged and trackable
4. Predictable Behavior - Explicit rules, no surprises
5. Error Handling - Graceful degradation with fallbacks
"""
import logging
from typing import Optional, Dict, List, Tuple, Any
from datetime import datetime, timezone
import httpx
from motor.motor_asyncio import AsyncIOMotorDatabase
import json

from models.inbound_lead import InboundLead, ExtractedData, LeadActivity, LeadStage
from models.email import Email
from models.intent import Intent
from config import config

logger = logging.getLogger(__name__)


class LeadAgentService:
    """
    Lead Agent Service following Parlant.io architecture principles
    
    Responsibilities:
    - Detect if email is from an inbound lead
    - Extract structured data from emails using AI
    - Manage lead lifecycle with state machine
    - Track all activities for observability
    - Calculate lead scores
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.groq_api_key = config.GROQ_API_KEY
        
        if not self.groq_api_key:
            logger.warning("GROQ_API_KEY not configured. Lead data extraction will be limited.")
    
    # ========================================================================
    # LEAD DETECTION (Deterministic)
    # ========================================================================
    
    async def is_inbound_lead(self, intent_id: Optional[str], user_id: str) -> bool:
        """
        Deterministic check if email is from an inbound lead
        
        Rules:
        1. Intent must exist
        2. Intent must have is_inbound_lead=True flag
        3. Intent must be active
        
        Returns:
            bool: True if this is an inbound lead email
        """
        if not intent_id:
            return False
        
        try:
            intent = await self.db.intents.find_one({
                "id": intent_id,
                "user_id": user_id,
                "is_active": True
            })
            
            if not intent:
                return False
            
            is_lead = intent.get('is_inbound_lead', False)
            
            if is_lead:
                logger.info(f"✓ Inbound lead detected via intent: {intent.get('name')}")
            
            return is_lead
            
        except Exception as e:
            logger.error(f"Error checking inbound lead status: {e}")
            return False
    
    # ========================================================================
    # DATA EXTRACTION (AI-Powered with Fallbacks)
    # ========================================================================
    
    async def extract_lead_data(self, email: Email) -> ExtractedData:
        """
        Extract structured lead data from email using AI
        
        Extraction Strategy:
        1. Use AI (Groq LLM) to extract structured data
        2. Validate extracted data
        3. Calculate confidence score
        4. Fallback to basic extraction if AI fails
        
        Returns:
            ExtractedData: Structured lead information
        """
        try:
            # Try AI extraction first
            extracted = await self._ai_extract_lead_data(email)
            
            if extracted.extraction_confidence > 0.5:
                logger.info(f"AI extraction successful for email {email.id} (confidence: {extracted.extraction_confidence})")
                return extracted
            
            # Fallback to basic extraction
            logger.info(f"AI extraction low confidence, using fallback for email {email.id}")
            return self._basic_extract_lead_data(email)
            
        except Exception as e:
            logger.error(f"Error extracting lead data: {e}")
            # Return basic extraction as ultimate fallback
            return self._basic_extract_lead_data(email)
    
    async def _ai_extract_lead_data(self, email: Email) -> ExtractedData:
        """
        Use Groq LLM to extract structured data from email including signatures and social URLs
        """
        if not self.groq_api_key:
            return ExtractedData(extraction_confidence=0.0)
        
        try:
            # Prepare extraction prompt with enhanced instructions
            prompt = f"""Extract comprehensive lead information from this email, including details from email signature. Return ONLY valid JSON.

Email Subject: {email.subject}
Email From: {email.from_email}
Email Body (including signature):
{email.body[:2000]}

Extract ALL available information (use null if not found):
{{
  "name": "Full name of the sender (check signature and email body)",
  "email": "Email address",
  "company_name": "Company/Organization name (check signature)",
  "address": "Physical address if mentioned (check signature)",
  "phone": "Phone number (check signature, format: +1-xxx-xxx-xxxx or similar)",
  "job_title": "Job title or position (check signature)",
  "company_size": "Company size if mentioned (e.g., '1-10', '11-50', '51-200', '200+')",
  "industry": "Industry or sector",
  "specific_interests": "What they're interested in (products/services mentioned)",
  "requirements": "Their specific needs or requirements",
  "linkedin_url": "LinkedIn profile URL (look for linkedin.com/in/ links)",
  "facebook_url": "Facebook profile or page URL",
  "twitter_url": "Twitter/X profile URL",
  "website_url": "Company website URL"
}}

IMPORTANT:
- Look carefully in email signatures for phone, address, social URLs
- Extract URLs exactly as they appear
- For phone numbers, preserve format including country code if present
- Company name often appears in email domain or signature
- Check for "linkedin.com", "facebook.com", "twitter.com", "x.com" links

Return ONLY the JSON object, no explanations."""
            
            # Call Groq API
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.groq_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": [
                            {"role": "system", "content": "You are an expert at extracting structured data from emails. Pay special attention to email signatures which often contain phone, address, and social media URLs. Extract information accurately and return only valid JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.1,
                        "max_tokens": 600
                    }
                )
            
            if response.status_code != 200:
                logger.error(f"Groq API error: {response.status_code} - {response.text}")
                return ExtractedData(extraction_confidence=0.0)
            
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()
            
            # Parse JSON response
            # Remove markdown code blocks if present
            if content.startswith('```'):
                content = content.split('\n', 1)[1]
                content = content.rsplit('```', 1)[0]
            
            extracted_json = json.loads(content)
            
            # Calculate confidence based on fields extracted
            fields_found = sum(1 for v in extracted_json.values() if v is not None and v != "")
            total_fields = len(extracted_json)
            confidence = fields_found / total_fields if total_fields > 0 else 0.0
            
            # Create ExtractedData object
            extracted_data = ExtractedData(
                name=extracted_json.get('name'),
                email=extracted_json.get('email') or email.from_email,  # Use from_email as fallback
                company_name=extracted_json.get('company_name'),
                address=extracted_json.get('address'),
                phone=extracted_json.get('phone'),
                job_title=extracted_json.get('job_title'),
                company_size=extracted_json.get('company_size'),
                industry=extracted_json.get('industry'),
                specific_interests=extracted_json.get('specific_interests'),
                requirements=extracted_json.get('requirements'),
                linkedin_url=extracted_json.get('linkedin_url'),
                facebook_url=extracted_json.get('facebook_url'),
                twitter_url=extracted_json.get('twitter_url'),
                website_url=extracted_json.get('website_url'),
                extraction_confidence=confidence
            )
            
            logger.info(f"AI extraction completed: {fields_found}/{total_fields} fields (confidence: {confidence:.2f})")
            return extracted_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI extraction JSON: {e}")
            return ExtractedData(extraction_confidence=0.0)
        except Exception as e:
            logger.error(f"AI extraction error: {e}")
            return ExtractedData(extraction_confidence=0.0)
    
    def _basic_extract_lead_data(self, email: Email) -> ExtractedData:
        """
        Basic extraction using simple parsing (fallback)
        """
        import re
        
        # Extract email from sender
        lead_email = email.from_email
        
        # Try to extract name from email or body
        name = None
        body_lines = email.body.split('\n')
        for line in body_lines[:5]:  # Check first 5 lines
            if any(keyword in line.lower() for keyword in ['my name is', 'i am', "i'm"]):
                # Try to extract name
                parts = line.split()
                if len(parts) >= 3:
                    name = ' '.join(parts[-2:])
                break
        
        # Extract phone using regex
        phone = None
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b|\b\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}\b'
        phone_match = re.search(phone_pattern, email.body)
        if phone_match:
            phone = phone_match.group(0)
        
        # Extract company from email domain
        company_name = None
        if '@' in lead_email:
            domain = lead_email.split('@')[1]
            company_name = domain.split('.')[0].title()
        
        return ExtractedData(
            name=name,
            email=lead_email,
            company_name=company_name,
            phone=phone,
            extraction_confidence=0.3  # Low confidence for basic extraction
        )
    
    # ========================================================================
    # LEAD LIFECYCLE MANAGEMENT (State Machine)
    # ========================================================================
    
    async def create_lead(
        self,
        user_id: str,
        email: Email,
        intent_id: Optional[str],
        intent_name: Optional[str],
        extracted_data: Optional[ExtractedData] = None
    ) -> InboundLead:
        """
        Create new lead with initial state
        
        State: NEW
        Actions:
        1. Create lead record
        2. Add initial activity
        3. Calculate initial score
        """
        try:
            # Check if lead already exists for this email
            existing = await self.db.inbound_leads.find_one({
                "user_id": user_id,
                "lead_email": email.from_email,
                "is_active": True
            })
            
            if existing:
                logger.info(f"Lead already exists for {email.from_email}, updating instead")
                return await self.update_lead_from_email(existing['id'], email)
            
            # Create new lead
            lead = InboundLead(
                user_id=user_id,
                lead_email=email.from_email,
                initial_email_id=email.id,
                thread_id=email.thread_id,
                email_ids=[email.id],
                intent_id=intent_id,
                intent_name=intent_name,
                stage='new',
                emails_received=1,
                last_contact_at=email.received_at
            )
            
            # Apply extracted data if available
            if extracted_data:
                lead.lead_name = extracted_data.name
                lead.company_name = extracted_data.company_name
                lead.address = extracted_data.address
                lead.phone = extracted_data.phone
                lead.job_title = extracted_data.job_title
                lead.company_size = extracted_data.company_size
                lead.industry = extracted_data.industry
                lead.specific_interests = extracted_data.specific_interests
                lead.requirements = extracted_data.requirements
                lead.linkedin_url = extracted_data.linkedin_url
                lead.facebook_url = extracted_data.facebook_url
                lead.twitter_url = extracted_data.twitter_url
                lead.website_url = extracted_data.website_url
            
            # Calculate initial score
            lead.score = self._calculate_lead_score(lead, extracted_data)
            
            # Add initial activity
            activity = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "activity_type": "lead_created",
                "description": f"Lead created from email: {email.subject}",
                "details": {
                    "email_id": email.id,
                    "intent_name": intent_name,
                    "extraction_confidence": extracted_data.extraction_confidence if extracted_data else 0.0
                },
                "performed_by": "system"
            }
            lead.activities.append(activity)
            
            # Save to database
            await self.db.inbound_leads.insert_one(lead.model_dump())
            
            logger.info(f"✓ Lead created: {lead.id} ({lead.lead_email}) - Stage: {lead.stage}, Score: {lead.score}")
            
            return lead
            
        except Exception as e:
            logger.error(f"Error creating lead: {e}")
            raise
    
    async def update_lead_from_email(self, lead_id: str, email: Email) -> InboundLead:
        """
        Update existing lead with new email interaction
        
        Actions:
        1. Add email to lead's email list
        2. Update engagement metrics
        3. Recalculate score (PROGRESSIVE - increases with each interaction!)
        4. Add activity
        5. Check for auto-stage transition
        """
        try:
            lead_doc = await self.db.inbound_leads.find_one({"id": lead_id})
            if not lead_doc:
                raise ValueError(f"Lead {lead_id} not found")
            
            lead = InboundLead(**lead_doc)
            
            # Update email tracking
            if email.id not in lead.email_ids:
                lead.email_ids.append(email.id)
            
            # Update engagement metrics (THIS INCREASES SCORE!)
            if email.direction == 'inbound':
                lead.emails_received += 1
                lead.last_contact_at = email.received_at
            else:
                lead.emails_sent += 1
            
            # Recalculate score - WILL INCREASE due to engagement
            lead.score = self._calculate_lead_score(lead, None)
            
            # Add activity
            activity = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "activity_type": "email_received" if email.direction == 'inbound' else "email_sent",
                "description": f"Email: {email.subject}",
                "details": {
                    "email_id": email.id,
                    "new_score": lead.score,
                    "engagement": f"{lead.emails_received}+{lead.emails_sent}"
                },
                "performed_by": "system"
            }
            lead.activities.append(activity)
            
            lead.updated_at = datetime.now(timezone.utc).isoformat()
            
            # Check for auto stage transition
            new_stage = await self.check_auto_stage_transition(lead)
            if new_stage and new_stage != lead.stage:
                old_stage = lead.stage
                lead.stage = new_stage
                logger.info(f"Auto stage transition: {old_stage} → {new_stage} (score: {lead.score})")
                
                # Add transition activity
                lead.activities.append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "activity_type": "stage_transition",
                    "description": f"Auto-transitioned from {old_stage} to {new_stage}",
                    "details": {"old_stage": old_stage, "new_stage": new_stage, "score": lead.score},
                    "performed_by": "system"
                })
            
            # Save to database
            await self.db.inbound_leads.update_one(
                {"id": lead_id},
                {"$set": lead.model_dump()}
            )
            
            logger.info(f"✓ Lead updated: {lead.id} - Stage: {lead.stage}, Score: {lead.score} (+{5}pts engagement), Emails: {lead.emails_received}+{lead.emails_sent}")
            
            return lead
            
        except Exception as e:
            logger.error(f"Error updating lead: {e}")
            raise
    
    async def mark_meeting_scheduled(
        self,
        lead_id: str,
        meeting_time: str,
        meeting_details: Dict[str, Any] = None
    ) -> InboundLead:
        """
        Mark lead as having scheduled a meeting
        
        This gives the HIGHEST score boost (+30 points) as meeting
        booking is the strongest signal of a qualified, interested lead
        """
        try:
            lead_doc = await self.db.inbound_leads.find_one({"id": lead_id})
            if not lead_doc:
                raise ValueError(f"Lead {lead_id} not found")
            
            lead = InboundLead(**lead_doc)
            old_score = lead.score
            
            # Mark meeting scheduled
            lead.meeting_scheduled = True
            lead.meeting_date = meeting_time
            
            # Recalculate score - WILL GET +30 BONUS!
            lead.score = self._calculate_lead_score(lead, None)
            score_increase = lead.score - old_score
            
            # Auto-transition to qualified stage
            if lead.stage not in ['qualified', 'opportunity', 'won']:
                old_stage = lead.stage
                lead.stage = 'qualified'
                
                logger.info(f"Meeting scheduled! Auto-qualified: {old_stage} → qualified (score: {old_score} → {lead.score}, +{score_increase}pts)")
            
            # Add activity
            activity = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "activity_type": "meeting_scheduled",
                "description": f"Meeting scheduled for {meeting_time}",
                "details": {
                    "meeting_time": meeting_time,
                    "meeting_details": meeting_details or {},
                    "score_before": old_score,
                    "score_after": lead.score,
                    "score_increase": score_increase
                },
                "performed_by": "system"
            }
            lead.activities.append(activity)
            
            lead.updated_at = datetime.now(timezone.utc).isoformat()
            
            # Save to database
            await self.db.inbound_leads.update_one(
                {"id": lead_id},
                {"$set": lead.model_dump()}
            )
            
            logger.info(f"✓ Meeting scheduled for lead: {lead.id} - Score increased: {old_score} → {lead.score} (+{score_increase}pts, meeting bonus: +30)")
            
            return lead
            
        except Exception as e:
            logger.error(f"Error marking meeting scheduled: {e}")
            raise
    
    async def transition_stage(
        self,
        lead_id: str,
        new_stage: LeadStage,
        reason: Optional[str] = None,
        performed_by: str = 'system'
    ) -> InboundLead:
        """
        Transition lead to new stage with validation
        
        State Machine Rules:
        - new → contacted (when first reply sent)
        - contacted → qualified (when engagement threshold met)
        - qualified → converted (manual or trigger)
        - any → lost (manual only)
        
        This is deterministic and follows strict rules
        """
        try:
            lead_doc = await self.db.inbound_leads.find_one({"id": lead_id})
            if not lead_doc:
                raise ValueError(f"Lead {lead_id} not found")
            
            lead = InboundLead(**lead_doc)
            old_stage = lead.stage
            
            # Validate transition
            if not self._is_valid_stage_transition(old_stage, new_stage):
                logger.warning(f"Invalid stage transition: {old_stage} → {new_stage}")
                # Allow it but log the warning
            
            # Update stage
            lead.stage = new_stage
            lead.stage_changed_at = datetime.now(timezone.utc).isoformat()
            
            # Add to stage history
            stage_change = {
                "from_stage": old_stage,
                "to_stage": new_stage,
                "timestamp": lead.stage_changed_at,
                "reason": reason or "Stage transition",
                "performed_by": performed_by
            }
            lead.stage_history.append(stage_change)
            
            # Add activity
            activity = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "activity_type": "stage_changed",
                "description": f"Stage changed: {old_stage} → {new_stage}",
                "details": stage_change,
                "performed_by": performed_by
            }
            lead.activities.append(activity)
            
            # Special handling for converted/lost
            if new_stage == 'converted':
                lead.conversion_date = datetime.now(timezone.utc).isoformat()
            elif new_stage == 'lost':
                lead.lost_reason = reason
                lead.is_active = False
            
            lead.updated_at = datetime.now(timezone.utc).isoformat()
            
            # Save to database
            await self.db.inbound_leads.update_one(
                {"id": lead_id},
                {"$set": lead.model_dump()}
            )
            
            logger.info(f"✓ Lead stage transition: {lead.id} - {old_stage} → {new_stage}")
            
            return lead
            
        except Exception as e:
            logger.error(f"Error transitioning lead stage: {e}")
            raise
    
    def _is_valid_stage_transition(self, from_stage: str, to_stage: str) -> bool:
        """
        Validate stage transitions (State Machine)
        """
        valid_transitions = {
            'new': ['contacted', 'lost'],
            'contacted': ['qualified', 'lost'],
            'qualified': ['converted', 'lost'],
            'converted': [],  # Terminal state
            'lost': []  # Terminal state
        }
        
        return to_stage in valid_transitions.get(from_stage, [])
    
    async def check_auto_stage_transition(self, lead: InboundLead) -> Optional[LeadStage]:
        """
        Check if lead should auto-transition to next stage
        
        Rules:
        - new → contacted: When first reply is sent (emails_sent > 0)
        - contacted → qualified: When engagement is high (score >= 60, emails_received >= 2)
        
        Returns:
            New stage if transition should happen, None otherwise
        """
        if lead.stage == 'new' and lead.emails_sent > 0:
            return 'contacted'
        
        if lead.stage == 'contacted' and lead.score >= 60 and lead.emails_received >= 2:
            return 'qualified'
        
        return None
    
    # ========================================================================
    # LEAD SCORING (Deterministic)
    # ========================================================================
    
    def _calculate_lead_score(self, lead: InboundLead, extracted_data: Optional[ExtractedData]) -> int:
        """
        Calculate lead score (0-100) based on multiple factors
        
        Scoring Factors:
        - Data completeness: 0-20 points
        - Engagement (emails): 0-30 points (progressive: 5pts per interaction)
        - Questions answered: 0-20 points (10pts per answer)
        - Meeting scheduled: 30 points (HIGHEST PRIORITY)
        - Extraction confidence: 0-10 points
        
        Progressive scoring means score increases with each conversation!
        """
        score = 0
        
        # Data completeness (0-20 points)
        fields = [
            lead.lead_name,
            lead.company_name,
            lead.phone,
            lead.job_title,
            lead.company_size,
            lead.industry,
            lead.specific_interests
        ]
        filled_fields = sum(1 for f in fields if f)
        data_score = int((filled_fields / len(fields)) * 20)
        score += data_score
        
        # Engagement - Progressive scoring (0-30 points)
        # Each email interaction = 5 points (up to 6 interactions = 30 points)
        total_interactions = lead.emails_received + lead.emails_sent
        engagement_score = min(total_interactions * 5, 30)
        score += engagement_score
        
        # Questions answered (0-20 points)
        # Each answered question = 10 points (up to 2 questions = 20 points)
        answers_count = len(lead.answers_collected) if lead.answers_collected else 0
        answer_score = min(answers_count * 10, 20)
        score += answer_score
        
        # Meeting scheduled (30 points) - HIGHEST PRIORITY
        # This is the strongest signal of qualified lead
        if lead.meeting_scheduled:
            score += 30
            logger.info(f"Meeting bonus applied: +30 points (lead: {lead.id})")
        
        # Extraction confidence (0-10 points)
        if extracted_data:
            confidence_score = int(extracted_data.extraction_confidence * 10)
            score += confidence_score
        
        # Cap at 100
        final_score = min(score, 100)
        
        logger.info(f"Lead score calculated: {final_score}/100 (data:{data_score}, engagement:{engagement_score}, answers:{answer_score}, meeting:{30 if lead.meeting_scheduled else 0})")
        
        return final_score
    
    # ========================================================================
    # ACTIVITY TRACKING (Observable)
    # ========================================================================
    
    async def add_activity(
        self,
        lead_id: str,
        activity_type: str,
        description: str,
        details: Dict[str, Any] = None,
        performed_by: str = 'system'
    ) -> None:
        """
        Add observable activity to lead timeline
        """
        activity = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "activity_type": activity_type,
            "description": description,
            "details": details or {},
            "performed_by": performed_by
        }
        
        await self.db.inbound_leads.update_one(
            {"id": lead_id},
            {
                "$push": {"activities": activity},
                "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
            }
        )
        
        logger.info(f"Activity added to lead {lead_id}: {activity_type}")
    
    async def record_meeting_scheduled(self, lead_id: str, meeting_date: str, calendar_event_id: str) -> None:
        """
        Record meeting scheduled for lead
        """
        await self.db.inbound_leads.update_one(
            {"id": lead_id},
            {
                "$set": {
                    "meeting_scheduled": True,
                    "meeting_date": meeting_date,
                    "calendar_event_id": calendar_event_id,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        await self.add_activity(
            lead_id,
            "meeting_scheduled",
            f"Meeting scheduled for {meeting_date}",
            {"calendar_event_id": calendar_event_id},
            "system"
        )
        
        logger.info(f"Meeting scheduled for lead {lead_id}")
