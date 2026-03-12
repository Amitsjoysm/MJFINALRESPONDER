"""
AI Agent Service - Production-Ready Implementation
Handles all AI operations: intent classification, meeting detection, draft generation, and validation
Supports multiple LLM providers: Groq and Claude (Anthropic)
"""
import json
import logging
from typing import List, Optional, Dict, Tuple
from datetime import datetime, timezone
import httpx
from motor.motor_asyncio import AsyncIOMotorDatabase
from anthropic import AsyncAnthropic

from config import config
from models.email import Email
from models.intent import Intent
from models.knowledge_base import KnowledgeBase
from services.date_parser_service import DateParserService
from services.signature_handler import SignatureHandler

logger = logging.getLogger(__name__)


class AIAgentService:
    """
    Service for all AI operations in the email assistant
    - Intent classification using keyword matching
    - Meeting detection using LLM (Groq or Claude)
    - Draft generation using LLM (Groq or Claude) with context
    - Draft validation using LLM (Groq or Claude)
    
    Supports multiple providers with automatic fallback
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        
        # Groq configuration
        self.groq_api_key = config.GROQ_API_KEY
        
        # Claude configuration
        self.claude_api_key = config.CLAUDE_API_KEY
        self.claude_client = None
        if self.claude_api_key:
            self.claude_client = AsyncAnthropic(api_key=self.claude_api_key)
        
        # Provider configuration
        self.primary_provider = config.PRIMARY_LLM_PROVIDER
        self.fallback_provider = config.FALLBACK_LLM_PROVIDER
        
        self.tokens_used = 0
        self.date_parser = DateParserService()
        
        # Validate at least one provider is configured
        if not self.groq_api_key and not self.claude_api_key:
            logger.error("No LLM provider configured! AI features will not work.")
        else:
            providers = []
            if self.groq_api_key:
                providers.append("Groq")
            if self.claude_api_key:
                providers.append("Claude")
            logger.info(f"AI Agent Service initialized with providers: {', '.join(providers)}")
            logger.info(f"Primary provider: {self.primary_provider}, Fallback: {self.fallback_provider}")
    
    # ============================================================================
    # INTENT CLASSIFICATION
    # ============================================================================
    
    async def classify_intent(self, email: Email, user_id: str) -> Tuple[Optional[str], float, Optional[Dict]]:
        """
        Classify email intent using AI-powered semantic understanding
        
        ENHANCED ALGORITHM:
        - Uses LLM to understand what user is actually asking
        - Analyzes email context, tone, and intent
        - Matches against available intents based on meaning, not just keywords
        - Considers lead qualification criteria
        - More accurate and context-aware than keyword matching
        
        Returns:
            Tuple of (intent_id, confidence, intent_dict)
            - intent_id: The matched intent ID or None
            - confidence: 0.0-1.0 from AI analysis
            - intent_dict: Full intent document or None
        """
        try:
            # Get all active intents for user
            intents = await self.db.intents.find({
                "user_id": user_id,
                "is_active": True
            }).sort("priority", -1).to_list(100)
            
            if not intents:
                logger.warning(f"No intents found for user {user_id}")
                return None, 0.0, None
            
            # Prepare email text
            email_text = f"Subject: {email.subject}\n\nBody:\n{email.body}"
            
            # Build intent descriptions for AI
            intent_descriptions = []
            intent_map = {}
            
            for intent_doc in intents:
                # Skip default intent - use as fallback
                if intent_doc.get('is_default', False):
                    continue
                
                self._convert_datetime_fields(intent_doc)
                intent = Intent(**intent_doc)
                
                intent_info = {
                    'name': intent.name,
                    'description': intent.description,
                    'priority': intent.priority,
                    'is_lead': intent.is_lead,
                    'keywords_hint': ', '.join(intent.keywords[:10])  # Hint, not strict matching
                }
                intent_descriptions.append(intent_info)
                intent_map[intent.name] = intent_doc
            
            # If no non-default intents, use default
            if not intent_descriptions:
                default_intent = next(
                    (i for i in intents if i.get('is_default', False)),
                    None
                )
                if default_intent:
                    self._convert_datetime_fields(default_intent)
                    logger.info("Only default intent available")
                    return default_intent['id'], 0.5, default_intent
                return None, 0.0, None
            
            # Use AI to classify intent
            system_prompt = """You are an intelligent email intent classifier. Your job is to understand what the sender is actually asking for and match it to the most appropriate intent.

Analyze the email content carefully:
- What is the sender's main question or request?
- What is their underlying need or goal?
- What action or information are they seeking?
- Are they a potential customer (lead) or existing customer?

Match the email to the BEST intent based on semantic meaning, not just keywords.

Return your response in this exact JSON format:
{
  "intent_name": "The name of the best matching intent",
  "confidence": 0.95,
  "reasoning": "Brief explanation of why this intent matches"
}

If no intent matches well, return:
{
  "intent_name": "Default Response",
  "confidence": 0.5,
  "reasoning": "Email doesn't clearly match any specific intent"
}"""

            user_prompt = f"""EMAIL TO CLASSIFY:
{email_text}

AVAILABLE INTENTS:
{chr(10).join([f"- {i['name']}: {i['description']} (Priority: {i['priority']}, Lead Intent: {i['is_lead']})" for i in intent_descriptions])}

Analyze this email and determine which intent best matches what the sender is asking for. Consider the context, tone, and actual needs, not just keywords."""

            try:
                # Call LLM for intent classification
                response = await self.client.chat.completions.create(
                    model=self.primary_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3,  # Lower temperature for consistent classification
                    max_tokens=300
                )
                
                result_text = response.choices[0].message.content.strip()
                
                # Parse JSON response
                import json
                import re
                
                # Extract JSON from response (handle markdown code blocks)
                json_match = re.search(r'\{[^}]+\}', result_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    result = json.loads(result_text)
                
                intent_name = result.get('intent_name')
                confidence = float(result.get('confidence', 0.5))
                reasoning = result.get('reasoning', 'AI classification')
                
                # Find the matching intent
                if intent_name in intent_map:
                    matched_intent = intent_map[intent_name]
                    logger.info(f"✓ AI classified intent: '{intent_name}' (confidence: {confidence:.2f})")
                    logger.info(f"  Reasoning: {reasoning}")
                    return matched_intent['id'], confidence, matched_intent
                
                # If AI returned "Default Response" or no match found
                default_intent = next(
                    (i for i in intents if i.get('is_default', False)),
                    None
                )
                if default_intent:
                    self._convert_datetime_fields(default_intent)
                    logger.info(f"Using default intent (AI confidence: {confidence:.2f})")
                    logger.info(f"  Reasoning: {reasoning}")
                    return default_intent['id'], confidence, default_intent
                
            except Exception as e:
                logger.error(f"AI intent classification failed: {e}")
                logger.info("Falling back to keyword matching")
                
                # Fallback to keyword matching
                email_text_lower = f"{email.subject} {email.body}".lower()
                intent_scores = []
                
                for intent_doc in intents:
                    if intent_doc.get('is_default', False):
                        continue
                    
                    self._convert_datetime_fields(intent_doc)
                    intent = Intent(**intent_doc)
                    
                    matched_keywords = []
                    for keyword in intent.keywords:
                        if keyword.lower() in email_text_lower:
                            matched_keywords.append(keyword)
                    
                    if matched_keywords:
                        intent_scores.append({
                            'intent_doc': intent_doc,
                            'match_count': len(matched_keywords),
                            'priority': intent.priority,
                            'name': intent.name,
                            'matched_keywords': matched_keywords
                        })
                
                if intent_scores:
                    intent_scores.sort(key=lambda x: (x['match_count'], x['priority']), reverse=True)
                    best_match = intent_scores[0]
                    logger.info(f"✓ Keyword fallback: '{best_match['name']}' matched with {best_match['match_count']} keywords")
                    return best_match['intent_doc']['id'], 0.8, best_match['intent_doc']
            
            # Final fallback to default intent
            default_intent = next(
                (i for i in intents if i.get('is_default', False)),
                None
            )
            
            if default_intent:
                self._convert_datetime_fields(default_intent)
                logger.info("Using default intent (fallback)")
                return default_intent['id'], 0.5, default_intent
            
            logger.warning(f"No matching intent found for email: {email.subject}")
            return None, 0.0, None
            
        except Exception as e:
            logger.error(f"Error classifying intent: {e}", exc_info=True)
            return None, 0.0, None
    
    # ============================================================================
    # TIME REFERENCE DETECTION
    # ============================================================================
    
    async def detect_time_reference(self, email: Email) -> List[Dict]:
        """
        Detect time-based follow-up requests in email
        
        Returns:
            List of time references with target dates and context
            [
                {
                    'matched_text': 'next quarter',
                    'target_date': datetime,
                    'context': 'surrounding text',
                    'original_email_body': full email body for reference
                }
            ]
        """
        try:
            # Combine subject and body for analysis
            full_text = f"{email.subject}\n\n{email.body}"
            
            # Parse time references
            time_refs = self.date_parser.parse_time_references(full_text)
            
            if not time_refs:
                return []
            
            results = []
            for matched_text, target_date, context in time_refs:
                results.append({
                    'matched_text': matched_text,
                    'target_date': target_date,
                    'context': context,
                    'original_email_body': email.body[:500]  # First 500 chars for context
                })
            
            logger.info(f"Found {len(results)} time references in email {email.id}")
            return results
            
        except Exception as e:
            logger.error(f"Error detecting time reference: {e}")
            return []
    
    # ============================================================================
    # SIMPLE REPLY DETECTION
    # ============================================================================
    
    def is_simple_acknowledgment(self, email: Email) -> bool:
        """
        Detect if email is a simple acknowledgment that doesn't need follow-up
        
        Examples:
        - "Thanks", "Thank you", "Thanks!"
        - "Got it", "Received", "Noted"
        - "OK", "Okay", "Sure"
        - "Appreciate it", "Much appreciated"
        
        Returns:
            True if this is a simple acknowledgment (no follow-up needed)
        """
        # Combine subject and body
        full_text = f"{email.subject}\n{email.body}".lower().strip()
        
        # Remove common email signatures and footers
        lines = [line.strip() for line in full_text.split('\n') if line.strip()]
        
        # If email is very short (1-3 lines), check for simple acknowledgments
        if len(lines) <= 3:
            content = ' '.join(lines)
            
            # Simple acknowledgment patterns
            simple_patterns = [
                r'\b(thanks?|thank you|thx|ty)\b',
                r'\b(got it|received|noted|understood)\b',
                r'\b(ok|okay|sure|alright)\b',
                r'\b(appreciate it|appreciated|much appreciated)\b',
                r'\b(will do|sounds good|perfect)\b',
                r'\b(no problem|no worries)\b',
                r'^\s*👍\s*$',  # Just a thumbs up emoji
            ]
            
            import re
            for pattern in simple_patterns:
                if re.search(pattern, content):
                    # Make sure there's no time reference or request
                    request_patterns = [
                        r'\b(when|where|how|what|why|can you|could you|would you|please)\b',
                        r'\b(need|want|require|request|asking|question)\b',
                        r'\b(follow up|get back|touch base|reach out)\b',
                    ]
                    
                    has_request = any(re.search(p, content) for p in request_patterns)
                    
                    if not has_request and len(content) < 100:
                        logger.info(f"Email {email.id} detected as simple acknowledgment")
                        return True
        
        return False
    
    # ============================================================================
    # MEETING DETECTION
    # ============================================================================
    
    async def detect_meeting(
        self, 
        email: Email, 
        thread_context: List[Dict] = None
    ) -> Tuple[bool, float, Optional[Dict]]:
        """
        Detect if email contains meeting request using Groq LLM
        
        Returns:
            Tuple of (is_meeting, confidence, details)
            - is_meeting: True if meeting detected
            - confidence: 0.0-1.0 (0.8+ for explicit, 0.6-0.8 for implied)
            - details: Dict with meeting details (title, start_time, end_time, location, etc.)
        """
        try:
            current_time = config.get_datetime_string()
            current_year = datetime.now(timezone.utc).year
            
            # Build prompt with thread context
            prompt = self._build_meeting_detection_prompt(
                email, 
                thread_context, 
                current_time, 
                current_year
            )
            
            # Call LLM API (with fallback support)
            result = await self._call_llm_api(
                system_message="You are a meeting detection AI. Analyze emails and extract meeting details. Always respond with valid JSON.",
                user_message=prompt,
                temperature=0.3,
                max_tokens=500
            )
            
            # Parse response
            data = self._parse_json_response(result)
            
            is_meeting = data.get('is_meeting', False)
            confidence = data.get('confidence', 0.0)
            details = data.get('details')
            
            if is_meeting:
                logger.info(f"✓ Meeting detected with confidence {confidence}: {details.get('title', 'Untitled')}")
            
            return is_meeting, confidence, details
            
        except Exception as e:
            logger.error(f"Error detecting meeting: {e}", exc_info=True)
            return False, 0.0, None
    
    def _build_meeting_detection_prompt(
        self, 
        email: Email, 
        thread_context: List[Dict],
        current_time: str,
        current_year: int
    ) -> str:
        """Build meeting detection prompt with thread context"""
        
        # Thread context
        thread_str = ""
        if thread_context:
            thread_str = "\n\nPrevious messages in this thread:\n"
            for msg in thread_context:
                thread_str += f"From: {msg['from']} | {msg['received_at']}\n"
                thread_str += f"Subject: {msg['subject']}\n"
                thread_str += f"Body: {msg['body'][:200]}...\n\n"
        
        return f"""Current Date & Time: {current_time} (UTC)
{thread_str}

Analyze this email and determine if it contains a meeting request, invitation, or scheduling discussion.

Email Subject: {email.subject}
Email Body: {email.body}

MEETING DETECTION RULES:
1. Look for explicit meeting requests or invitations
2. Look for date/time mentions with context of scheduling  
3. Check for meeting-related keywords: meeting, call, zoom, teams, schedule, discuss, sync, catch up
4. Ignore casual mentions like "let's meet sometime" without specific details
5. Use thread context to avoid duplicates - if meeting already discussed, confidence should be lower

IMPORTANT - TIME CONFIRMATION PROTOCOL:
- If user proposes a time but hasn't explicitly confirmed: confidence should be 0.5-0.7 (ASK FOR CONFIRMATION)
- If user confirms a previously proposed time: confidence should be 0.8-1.0 (CREATE EVENT)
- Look for confirmation phrases: "works for me", "sounds good", "confirmed", "that time is perfect", "yes to [time]"
- If time is vague or missing: confidence should be 0.3-0.5 (ASK FOR TIME)

If a meeting is detected, extract:
1. Meeting date and time:
   - Convert to ISO format: YYYY-MM-DDTHH:MM:SS
   - If timezone mentioned, convert to UTC
   - If no year mentioned, assume {current_year}
   - If only date mentioned, assume 10:00 AM UTC
   - Handle relative dates: "tomorrow", "next Tuesday", etc.

2. Duration/end time:
   - If duration mentioned, calculate end time
   - Default to 1 hour if not specified
   - Format: YYYY-MM-DDTHH:MM:SS

3. Location: physical address, virtual link, or 'TBD'

4. Meeting title: extract or infer from context

5. Attendees: email addresses mentioned

Respond in JSON format:
{{
  "is_meeting": true/false,
  "confidence": 0.0-1.0,
  "details": {{
    "title": "Meeting title",
    "start_time": "2025-01-15T14:00:00",
    "end_time": "2025-01-15T15:00:00",
    "location": "Location or 'Virtual' or 'TBD'",
    "description": "Brief description",
    "attendees": ["email@example.com"],
    "timezone": "UTC"
  }}
}}

If no clear meeting detected, set is_meeting to false and confidence to 0.0."""
    
    # ============================================================================
    # DRAFT GENERATION
    # ============================================================================
    
    async def generate_draft(
        self,
        email: Email,
        user_id: str,
        intent_id: Optional[str] = None,
        thread_context: List[Dict] = None,
        validation_issues: List[str] = None,
        calendar_event = None,
        follow_up_context: Optional[Dict] = None,
        meeting_info: Optional[Dict] = None,
        nurturing_questions: List[Dict] = None
    ) -> Tuple[str, int]:
        """
        Generate email draft using Groq LLM with full context
        
        Args:
            nurturing_questions: Optional list of questions to ask for lead qualification
            follow_up_context: Optional dict with:
                - is_automated_followup: bool
                - base_date: str (target date user mentioned)
                - matched_text: str (original time reference)
                - original_context: str (context from original email)
        
        Returns:
            Tuple of (draft_text, tokens_used)
        """
        try:
            current_time = config.get_datetime_string()
            
            # Get all context (persona, KB, intent)
            context = await self._get_draft_context(user_id, email.email_account_id, intent_id)
            
            # Build comprehensive prompt
            prompt = self._build_draft_generation_prompt(
                email=email,
                context=context,
                thread_context=thread_context,
                validation_issues=validation_issues,
                calendar_event=calendar_event,
                current_time=current_time,
                follow_up_context=follow_up_context,
                meeting_info=meeting_info,
                nurturing_questions=nurturing_questions
            )
            
            system_message = self._get_draft_system_message(context, nurturing_questions)
            
            # Adjust max_tokens based on content type
            # Meeting confirmations need more tokens for event details
            # Lead qualification emails need more space to naturally integrate questions
            max_tokens = 300  # Default for concise responses
            
            # Lead qualification needs more tokens to naturally integrate questions
            if nurturing_questions and len(nurturing_questions) > 0:
                # More tokens needed to answer + ask questions naturally
                max_tokens = 600  # Increased for lead qualification with questions
                logger.info(f"Adjusted max_tokens to {max_tokens} for lead qualification with {len(nurturing_questions)} questions")
            elif calendar_event:
                max_tokens = 400  # More space for meeting details
            elif meeting_info and meeting_info.get('detected'):
                max_tokens = 350  # Medium space for meeting discussions
            
            # Call LLM API (with fallback support)
            result = await self._call_llm_api(
                system_message=system_message,
                user_message=prompt,
                temperature=0.7,
                max_tokens=max_tokens
            )
            
            draft = result.strip()
            
            # Remove any AI-generated signature to prevent double signatures
            draft = SignatureHandler.remove_ai_signature(draft)
            
            # CRITICAL PRE-CHECK: Reject obviously incomplete drafts immediately
            import re
            draft_length = len(draft)
            word_count = len(draft.split())
            
            # Remove extra whitespace for accurate checks
            draft_normalized = re.sub(r'\s+', ' ', draft).strip()
            draft_normalized_lower = draft_normalized.lower()
            
            if draft_length < 30:
                logger.error(f"✗ CRITICAL: Draft extremely short ({draft_length} chars) - likely just greeting")
                raise ValueError(f"Draft generation failed: Response too short ({draft_length} characters, minimum 30)")
            
            if word_count < 10:
                logger.error(f"✗ CRITICAL: Draft has very few words ({word_count} words) - incomplete response")
                raise ValueError(f"Draft generation failed: Too few words ({word_count} words, minimum 10)")
            
            # ENHANCED: Check for greeting-only patterns (more comprehensive)
            greeting_only_patterns = [
                r'^(hi|hello|dear|hey)\s+\w+[\s,\.!]*$',
                r'^(hi|hello|dear|hey)[\s,\.!]*$',
                r'^(hi|hello|dear|hey)\s+there[\s,\.!]*$',
            ]
            
            for pattern in greeting_only_patterns:
                if re.match(pattern, draft_normalized_lower):
                    logger.error(f"✗ CRITICAL: Draft is greeting-only: '{draft}'")
                    raise ValueError("Draft generation failed: Response is only a greeting with no content")
            
            # ENHANCED: Check if draft starts with greeting but has minimal content after
            lines = [l.strip() for l in draft.split('\n') if l.strip()]
            if len(lines) > 0:
                first_line_lower = lines[0].lower()
                greeting_starts = ['hi ', 'hello ', 'dear ', 'hey ', 'hi,', 'hello,', 'dear,', 'hey,']
                
                if any(first_line_lower.startswith(g) for g in greeting_starts):
                    # Check content after greeting
                    remaining_content = ' '.join(lines[1:]).strip()
                    if len(remaining_content) < 40 or len(remaining_content.split()) < 12:
                        logger.error(f"✗ CRITICAL: Draft has greeting but insufficient content: '{draft}'")
                        raise ValueError(f"Draft generation failed: Greeting present but insufficient content ({len(remaining_content)} chars, {len(remaining_content.split())} words after greeting)")
            
            logger.info(f"✓ Draft generated ({draft_length} chars, {word_count} words, signature removed)")
            
            return draft, self.tokens_used
            
        except Exception as e:
            logger.error(f"Error generating draft: {e}", exc_info=True)
            raise
    
    def _build_draft_generation_prompt(
        self,
        email: Email,
        context: Dict,
        thread_context: List[Dict],
        validation_issues: List[str],
        calendar_event,
        current_time: str,
        follow_up_context: Optional[Dict] = None,
        meeting_info: Optional[Dict] = None,
        nurturing_questions: List[Dict] = None
    ) -> str:
        """Build comprehensive draft generation prompt"""
        
        prompt = f"Current Date & Time: {current_time}\n\n"
        
        # Add nurturing questions if this is a lead qualification email
        if nurturing_questions and len(nurturing_questions) > 0:
            prompt += "🎯 LEAD QUALIFICATION - IMPORTANT\n"
            prompt += "="*50 + "\n"
            prompt += "This is a potential lead. You MUST naturally integrate these qualification questions into your response:\n\n"
            
            for i, q in enumerate(nurturing_questions, 1):
                question_text = q.get('question_text', '')
                is_required = q.get('is_required', False)
                required_mark = " (REQUIRED)" if is_required else ""
                prompt += f"{i}. {question_text}{required_mark}\n"
            
            prompt += "\n✨ CRITICAL INSTRUCTIONS FOR QUESTION INTEGRATION:\n"
            prompt += "- Weave these questions NATURALLY into your response\n"
            prompt += "- DO NOT make it feel like an interrogation or form\n"
            prompt += "- Introduce questions conversationally (e.g., 'To better assist you, I'd love to know...')\n"
            prompt += "- Keep your tone warm, friendly, and genuinely curious\n"
            prompt += "- Make it feel like you're having a conversation, not collecting data\n"
            prompt += "- It's okay to ask questions in a different order if it flows better\n"
            prompt += "="*50 + "\n\n"
        
        # Add follow-up context if this is an automated follow-up
        if follow_up_context and follow_up_context.get('is_automated_followup'):
            follow_up_type = follow_up_context.get('follow_up_type', 'time-based')
            
            prompt += "🔔 THIS IS AN AUTOMATED FOLLOW-UP EMAIL\n"
            prompt += "="*50 + "\n"
            
            if follow_up_type == 'standard':
                # Standard follow-up (no reply received)
                prompt += "SITUATION: You previously sent an email but haven't received a response.\n"
                prompt += f"Original Context: {follow_up_context.get('original_context', 'Follow-up')}\n"
                prompt += f"Days Since Sent: {follow_up_context.get('matched_text', 'N/A')}\n\n"
                
                prompt += "INSTRUCTIONS FOR FOLLOW-UP:\n"
                prompt += "1. Acknowledge that you're following up on your previous email\n"
                prompt += "2. Reference specific points from the original conversation\n"
                prompt += "3. Make it easy for them to respond (ask a specific question or offer help)\n"
                prompt += "4. Keep tone friendly and understanding (they might be busy)\n"
                prompt += "5. Add value - provide additional information or perspective\n"
                prompt += "6. Don't be pushy - be helpful and available\n"
                prompt += "7. Use conversation history below to make it contextual and specific\n\n"
                
                prompt += "✅ GOOD FOLLOW-UP EXAMPLE:\n"
                prompt += "\"I wanted to circle back on [specific topic from conversation]. "
                prompt += "I know things get busy, so no rush. I thought you might find [additional value] helpful. "
                prompt += "Let me know if you have any questions about [specific point]!\"\n\n"
                
                prompt += "❌ AVOID GENERIC TEMPLATES:\n"
                prompt += "- \"Just following up...\"\n"
                prompt += "- \"Did you get my previous email?\"\n"
                prompt += "- \"Checking in...\"\n"
                
            else:
                # Time-based follow-up (user asked to follow up later)
                prompt += "SITUATION: The recipient asked you to follow up at a specific time.\n"
                prompt += f"Original Request: {follow_up_context.get('matched_text', 'N/A')}\n"
                prompt += f"Target Date: {follow_up_context.get('base_date', 'N/A')}\n"
                prompt += f"Context: {follow_up_context.get('original_context', 'N/A')}\n\n"
                
                prompt += "INSTRUCTIONS FOR TIME-BASED FOLLOW-UP:\n"
                prompt += "1. Reference that they asked you to follow up at this time\n"
                prompt += "2. Remind them of the context of your previous conversation\n"
                prompt += "3. Provide any updates or new information since last contact\n"
                prompt += "4. Ask how you can help or move forward\n"
                prompt += "5. Be respectful of their time - get to the point\n"
            
            prompt += "="*50 + "\n\n"
        
        # Add persona
        if context['persona']:
            prompt += f"YOUR PERSONA:\n{context['persona']}\n\n"
        
        # Add knowledge base
        if context['knowledge_base']:
            prompt += "KNOWLEDGE BASE - Use this information to answer questions:\n"
            for kb in context['knowledge_base']:
                prompt += f"\n[{kb['category']}] {kb['title']}\n{kb['content']}\n"
            prompt += "\n"
        
        # Add intent-specific instructions
        if context['intent_prompt']:
            prompt += f"INTENT-SPECIFIC INSTRUCTIONS:\n{context['intent_prompt']}\n\n"
        
        # Add thread context
        if thread_context:
            prompt += "PREVIOUS CONVERSATION:\n" + "="*50 + "\n"
            for i, msg in enumerate(thread_context, 1):
                prompt += f"Message {i}:\n"
                prompt += f"From: {msg['from']}\n"
                prompt += f"Date: {msg['received_at']}\n"
                prompt += f"Subject: {msg['subject']}\n"
                prompt += f"Body:\n{msg['body']}\n\n"
                if msg.get('draft_sent'):
                    prompt += f"Our Previous Response:\n{msg['draft_sent']}\n\n"
                prompt += "="*50 + "\n"
        
        # Add validation feedback
        if validation_issues:
            prompt += "\n⚠️ PREVIOUS DRAFT HAD ISSUES - MUST FIX:\n"
            for issue in validation_issues:
                prompt += f"- {issue}\n"
            prompt += "\n"
        
        # Add calendar event info
        if calendar_event:
            prompt += self._format_calendar_event(calendar_event)
        # Add meeting detection info (when meeting detected but event not yet created)
        elif meeting_info and meeting_info.get('detected') and not meeting_info.get('event_created'):
            confidence = meeting_info.get('confidence', 0.0)
            details = meeting_info.get('details', {})
            
            if confidence >= 0.5:
                # Meeting detected but needs confirmation
                prompt += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 MEETING REQUEST DETECTED - TIME CONFIRMATION NEEDED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Confidence: {confidence:.1f} (Medium - needs explicit confirmation)
Suggested Time: {details.get('start_time', 'Not specified')}
Title: {details.get('title', 'Meeting')}

IMPORTANT: DO NOT create calendar event yet!
Your response should:
1. Acknowledge the meeting request warmly
2. If time was suggested: Ask "Would [time] work for you? Please confirm."
3. If time not clear: Ask "What date and time would work best for you?"
4. Let them know calendar invite will be sent once they confirm
5. Mention you'll check for any scheduling conflicts

Once user explicitly confirms the time, the system will automatically create the calendar event.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
        
        # Add current email
        if follow_up_context and follow_up_context.get('is_automated_followup'):
            prompt += f"""THIS IS A FOLLOW-UP EMAIL - NO NEW INCOMING EMAIL
Generate a follow-up message based on the conversation history above.
Reference the original request and provide a helpful check-in or update.
"""
        else:
            # Check if this is a meeting confirmation (simple yes/confirmation in thread with meeting discussion)
            is_meeting_confirmation = False
            if thread_context and len(thread_context) > 0:
                # Check if previous messages discussed meetings
                prev_discussed_meeting = any('meeting' in str(msg.get('body', '')).lower() or 
                                            'call' in str(msg.get('body', '')).lower() or
                                            'schedule' in str(msg.get('body', '')).lower()
                                            for msg in thread_context)
                # Check if current email is short confirmation
                email_body_lower = email.body.lower().strip()
                is_confirmation = any(phrase in email_body_lower for phrase in [
                    'yes', 'works for me', 'sounds good', 'perfect', 'confirmed', 
                    'that works', 'ok', 'okay', 'sure', 'great'
                ])
                is_meeting_confirmation = prev_discussed_meeting and is_confirmation and len(email.body.strip()) < 150
            
            prompt += f"""CURRENT EMAIL TO RESPOND TO:
From: {email.from_email}
To: {', '.join(email.to_email)}
Subject: {email.subject}
Body:
{email.body}
"""
            
            if is_meeting_confirmation and calendar_event:
                prompt += """
🎯 SPECIAL CASE: MEETING TIME CONFIRMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
The user has confirmed the meeting time. Calendar event has been created.

YOUR RESPONSE MUST:
1. Start with personalized greeting
2. Thank them for confirming
3. Confirm the meeting details (date, time, location/Meet link)
4. Mention calendar invite has been sent
5. Express enthusiasm about the meeting
6. Keep it warm but brief (100-150 words)

Example response structure:
"Hi [Name],

Perfect! I've confirmed our meeting for [date] at [time]. I've sent you a calendar invite with the Google Meet link.

Looking forward to our discussion!"""
                
            # Adjust word count guidance based on content
            word_count_guidance = ""
            if nurturing_questions and len(nurturing_questions) > 0:
                # Lead qualification needs more space
                word_count_guidance = "WORD COUNT: Aim for 200-300 words to naturally include qualification questions. Never exceed 400 words."
            else:
                # Standard responses are concise
                word_count_guidance = "WORD COUNT: Aim for 100-150 words. Never exceed 200 words."
            
            prompt += f"""
Generate a professional, helpful email response.

CRITICAL REQUIREMENTS:
1. ALWAYS start with a personalized greeting using the sender's name (e.g., "Hi John," or "Hello Sarah,")
   - Extract name from email address if full name not available
   - Use first name only for informal/friendly tone
2. Keep response {'CONVERSATIONAL and NATURAL' if nurturing_questions else 'SHORT and CONCISE'}: {'200-300 words for lead qualification' if nurturing_questions else '100-200 words MAXIMUM'}
   - Get straight to the point
   - {'Build rapport while asking questions naturally' if nurturing_questions else 'One main paragraph for the core message'}
   - {'Multiple paragraphs okay to integrate questions naturally' if nurturing_questions else 'Optional second paragraph only if absolutely necessary'}
3. Be natural, warm, and professional
4. Use knowledge base information for accurate responses
5. Reference conversation context when replying to threads
6. DO NOT include:
   - Subject lines
   - Email signatures (handled separately)
   - Closing phrases like "Best regards" or "Sincerely" (handled by signature)
   - Excessive explanations or details

{word_count_guidance}

Focus on helpful, {'conversational' if nurturing_questions else 'concise'}, contextual response with proper personalized greeting."""
        
        return prompt
    
    def _format_calendar_event(self, calendar_event) -> str:
        """Format calendar event details for prompt"""
        
        # Handle both dict and Pydantic model
        if hasattr(calendar_event, 'model_dump'):
            event = calendar_event.model_dump()
        else:
            event = calendar_event
        
        calendar_str = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 CALENDAR EVENT CREATED - MUST MENTION IN RESPONSE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Title: {event.get('title')}
Date & Time: {event.get('start_time')} to {event.get('end_time')} ({event.get('timezone', 'UTC')})
Location: {event.get('location') or 'Virtual Meeting'}
"""
        
        if event.get('meet_link'):
            calendar_str += f"Google Meet Link: {event.get('meet_link')}\n"
        if event.get('html_link'):
            calendar_str += f"View in Calendar: {event.get('html_link')}\n"
        if event.get('attendees'):
            calendar_str += f"Attendees: {', '.join(event.get('attendees', []))}\n"
        
        calendar_str += """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

IMPORTANT: You MUST include in your response:
1. Confirm the meeting has been scheduled
2. Provide the date, time, and timezone
3. Include the Google Meet link if available
4. Include the calendar link
5. Make it sound natural and professional

"""
        
        return calendar_str
    
    def _get_draft_system_message(self, context: Dict, nurturing_questions: List[Dict] = None) -> str:
        """Get system message for draft generation"""
        
        # Adjust conciseness requirement based on whether we have lead qualification
        has_questions = nurturing_questions and len(nurturing_questions) > 0
        conciseness_guidance = "Be CONVERSATIONAL and THOROUGH: 200-300 words ideal for lead qualification" if has_questions else "Be CONCISE: Keep responses under 200 words (100-150 words ideal)"
        paragraph_guidance = "Use 2-3 paragraphs to naturally integrate questions" if has_questions else "Use 1-2 short paragraphs maximum"
        
        base_message = f"""You are an AI email assistant that generates professional, helpful email responses.

🚨 CRITICAL REQUIREMENTS - MUST FOLLOW:
1. NEVER respond with ONLY a greeting (e.g., "Hi John," or "Hello," alone)
2. ALWAYS provide substantive content - minimum 50 characters, 20 words
3. ALWAYS address the specific questions or concerns in the email
4. ALWAYS provide helpful, actionable information
5. Your response MUST be complete and helpful, not just a greeting

CORE PRINCIPLES:
1. Be professional but natural and conversational
2. Use the provided knowledge base for accurate information
3. Follow the persona and intent-specific instructions
4. {conciseness_guidance}
5. Never make up information - use only what's in the knowledge base
6. If you don't know something, say so professionally
7. ALWAYS write a complete, helpful response (not just greetings)

FORMATTING:
- Only output the email body (no subject line, no "Subject:" prefix)
- {paragraph_guidance}
- DO NOT add any sign-off, closing, signature, or "Best regards" type phrases
- DO NOT include sender name or contact information at the end
- End with the main content only - signature will be added automatically
- Use the persona's tone and style

❌ INVALID EXAMPLES (DO NOT GENERATE):
- "Hi John,"
- "Hello Sarah,"
- "Dear Customer,"
- "Thanks for reaching out."
- Any response under 50 characters

✅ VALID EXAMPLES (MUST GENERATE):
- Complete responses that address the inquiry with specific information
- Responses that answer questions with details
- Responses that provide value and next steps"""
        
        if context.get('persona'):
            base_message += f"\n\nYOUR STYLE: {context['persona'][:200]}"
        
        return base_message
    
    async def _get_draft_context(
        self,
        user_id: str,
        email_account_id: str,
        intent_id: Optional[str]
    ) -> Dict:
        """Get all context needed for draft generation"""
        
        context = {
            'persona': None,
            'knowledge_base': [],
            'intent_prompt': None,
            'intent_name': None
        }
        
        # Get persona from USER (primary) or email account (fallback)
        try:
            user = await self.db.users.find_one({"id": user_id})
            if user and user.get('persona'):
                context['persona'] = user['persona']
                logger.info(f"✓ Loaded user persona ({len(user['persona'])} chars)")
            else:
                # Fallback to email account persona
                account = await self.db.email_accounts.find_one({"id": email_account_id})
                if account and account.get('persona'):
                    context['persona'] = account['persona']
                    logger.info(f"✓ Loaded email account persona ({len(account['persona'])} chars)")
        except Exception as e:
            logger.warning(f"Could not load persona: {e}")
        
        # Get knowledge base (ALL active entries)
        try:
            kb_entries = await self.db.knowledge_base.find({
                "user_id": user_id,
                "is_active": True
            }).to_list(100)  # Increased from 50 to 100
            context['knowledge_base'] = kb_entries
            logger.info(f"✓ Loaded {len(kb_entries)} knowledge base entries")
        except Exception as e:
            logger.warning(f"Could not load knowledge base: {e}")
        
        # Get intent-specific prompt
        if intent_id:
            try:
                intent = await self.db.intents.find_one({"id": intent_id})
                if intent:
                    if intent.get('prompt'):
                        context['intent_prompt'] = intent['prompt']
                    context['intent_name'] = intent.get('name', 'Unknown')
                    logger.info(f"✓ Loaded intent: {context['intent_name']}")
                    logger.info(f"✓ Intent prompt: {len(context['intent_prompt'])} chars" if context['intent_prompt'] else "⚠ No intent prompt")
            except Exception as e:
                logger.warning(f"Could not load intent: {e}")
        
        # Log what context we have
        logger.info(f"Draft context summary: Persona={'Yes' if context['persona'] else 'No'}, KB={len(context['knowledge_base'])}, Intent={'Yes' if context['intent_prompt'] else 'No'}")
        
        return context
    
    # ============================================================================
    # DRAFT VALIDATION
    # ============================================================================
    
    async def validate_draft(
        self,
        draft: str,
        original_email: Email,
        thread_context: List[Dict] = None
    ) -> Tuple[bool, List[str], int]:
        """
        Validate email draft using multiple layers of validation
        
        STRICT VALIDATION - Prevents incomplete or greeting-only responses
        
        Returns:
            Tuple of (is_valid, issues, tokens_used)
            - is_valid: True if draft passes ALL validation layers
            - issues: List of issues found (empty if valid)
            - tokens_used: Total tokens consumed
        """
        try:
            issues = []
            
            # ============================================================
            # LAYER 1: BASIC LENGTH VALIDATION (CRITICAL)
            # ============================================================
            if not draft or not draft.strip():
                return False, ["Draft is empty"], 0
            
            draft_stripped = draft.strip()
            draft_length = len(draft_stripped)
            
            # Absolute minimum: 50 characters
            if draft_length < 50:
                logger.warning(f"✗ VALIDATION FAILED: Draft too short ({draft_length} chars, minimum 50)")
                return False, [f"Draft is too short: {draft_length} characters (minimum 50 required)"], 0
            
            # ============================================================
            # LAYER 2: GREETING-ONLY DETECTION (CRITICAL) - ENHANCED
            # ============================================================
            import re
            draft_lower = draft_stripped.lower()
            
            # Remove all whitespace/newlines for pure content check
            draft_no_whitespace = re.sub(r'\s+', ' ', draft_stripped).strip()
            draft_no_whitespace_lower = draft_no_whitespace.lower()
            
            # Pattern 1: Just "Hi {Name}," or "Hello {Name}," (exact match)
            greeting_exact_patterns = [
                r'^hi\s+\w+[\s,\.!]*$',
                r'^hello\s+\w+[\s,\.!]*$',
                r'^dear\s+\w+[\s,\.!]*$',
                r'^hey\s+\w+[\s,\.!]*$',
                r'^hi\s+there[\s,\.!]*$',
                r'^hello\s+there[\s,\.!]*$',
            ]
            
            for pattern in greeting_exact_patterns:
                if re.match(pattern, draft_no_whitespace_lower):
                    logger.warning(f"✗ VALIDATION FAILED: Greeting-only response detected (exact match)")
                    return False, ["Draft contains only a greeting with no actual content"], 0
            
            # Pattern 2: Greeting at start + minimal content (STRICTER)
            # Split by lines and check all variations
            lines = [line.strip() for line in draft_stripped.split('\n') if line.strip()]
            
            if len(lines) > 0:
                first_line_lower = lines[0].lower()
                
                # Check if first line is a greeting
                greeting_starts = ['hi ', 'hello ', 'dear ', 'hey ', 'hi,', 'hello,', 'dear,', 'hey,']
                is_greeting_start = any(first_line_lower.startswith(g) for g in greeting_starts)
                
                if is_greeting_start:
                    # Calculate actual content (excluding greeting line)
                    remaining_lines = lines[1:] if len(lines) > 1 else []
                    remaining_content = ' '.join(remaining_lines).strip()
                    
                    # STRICT: If remaining content is less than 50 characters, reject
                    if len(remaining_content) < 50:
                        logger.warning(f"✗ VALIDATION FAILED: Greeting with insufficient content ({len(remaining_content)} chars after greeting)")
                        return False, [f"Draft has greeting but insufficient actual content ({len(remaining_content)} characters after greeting, minimum 50 required)"], 0
                    
                    # EXTRA CHECK: Ensure remaining content has substance (not just filler)
                    remaining_word_count = len(remaining_content.split())
                    if remaining_word_count < 15:
                        logger.warning(f"✗ VALIDATION FAILED: Greeting with too few words after greeting ({remaining_word_count} words)")
                        return False, [f"Draft has greeting but too few words after greeting ({remaining_word_count} words, minimum 15 required)"], 0
            
            # ============================================================
            # LAYER 3: WORD COUNT VALIDATION
            # ============================================================
            word_count = len(draft_stripped.split())
            
            # Minimum 20 words for any response
            if word_count < 20:
                logger.warning(f"✗ VALIDATION FAILED: Too few words ({word_count}, minimum 20)")
                return False, [f"Draft has only {word_count} words (minimum 20 required)"], 0
            
            # ============================================================
            # LAYER 4: SENTENCE COUNT VALIDATION
            # ============================================================
            # Must have at least 2 sentences (indicated by . ! ? or newlines)
            sentence_endings = draft_stripped.count('.') + draft_stripped.count('!') + draft_stripped.count('?')
            
            if sentence_endings < 2:
                logger.warning(f"✗ VALIDATION FAILED: Too few sentences ({sentence_endings})")
                return False, [f"Draft needs at least 2 complete sentences (found {sentence_endings})"], 0
            
            # ============================================================
            # LAYER 5: AI-POWERED VALIDATION
            # ============================================================
            # Build validation prompt
            prompt = self._build_validation_prompt(draft, original_email, thread_context)
            
            system_message = """You are a STRICT email validation AI. Your job is to prevent low-quality or incomplete drafts from being sent.

VALIDATION CRITERIA (ALL must pass):
1. ✅ Professional tone and language
2. ✅ Directly addresses the sender's questions/concerns
3. ✅ Provides helpful, actionable information
4. ✅ No grammatical errors or typos
5. ✅ Appropriate length (minimum 50 characters, 20+ words)
6. ✅ Does not repeat information already in thread
7. ✅ Does not make promises that can't be kept
8. ✅ Shows understanding of the specific situation
9. ✅ Has actual content (NOT just a greeting)
10. ✅ Answers questions if any were asked

CRITICAL REJECTION RULES:
❌ REJECT if draft is just "Hi {Name}," or similar greeting
❌ REJECT if draft is under 50 characters
❌ REJECT if draft doesn't address the email content
❌ REJECT if draft is generic template text
❌ REJECT if draft doesn't answer questions asked
❌ REJECT if draft is incomplete or cut off

BE STRICT. When in doubt, REJECT the draft.

Respond with JSON:
{
  "is_valid": true/false,
  "issues": ["specific issues found"],
  "score": 0-100
}

Score < 70 = REJECT (is_valid: false)"""
            
            # Call LLM API (with fallback support)
            result = await self._call_llm_api(
                system_message=system_message,
                user_message=prompt,
                temperature=0.2,  # Lower temperature for more consistent validation
                max_tokens=500
            )
            
            # Parse response
            data = self._parse_json_response(result)
            
            is_valid = data.get('is_valid', False)
            ai_issues = data.get('issues', [])
            score = data.get('score', 0)
            
            # Enforce score threshold
            if score < 70:
                is_valid = False
                if "Low quality score" not in str(ai_issues):
                    ai_issues.append(f"Quality score too low: {score}/100 (minimum 70)")
            
            # Combine issues from all layers
            all_issues = issues + ai_issues
            
            if is_valid and not all_issues:
                logger.info(f"✓ Draft validation PASSED (score: {score}/100, {draft_length} chars, {word_count} words)")
            else:
                logger.warning(f"✗ Draft validation FAILED (score: {score}/100): {', '.join(all_issues)}")
            
            return is_valid, all_issues, self.tokens_used
            
        except Exception as e:
            logger.error(f"Error validating draft: {e}", exc_info=True)
            # On error, REJECT to be safe
            return False, [f"Validation error: {str(e)}"], self.tokens_used
    
    def _build_validation_prompt(
        self,
        draft: str,
        original_email: Email,
        thread_context: List[Dict]
    ) -> str:
        """Build validation prompt with strict criteria"""
        
        prompt = f"""ORIGINAL EMAIL:
From: {original_email.from_email}
Subject: {original_email.subject}
Body:
{original_email.body}

"""
        
        # Add thread context
        if thread_context:
            prompt += "PREVIOUS CONVERSATION:\n"
            for msg in thread_context:
                prompt += f"- {msg['from']}: {msg['body'][:150]}...\n"
                if msg.get('draft_sent'):
                    prompt += f"  Our response: {msg['draft_sent'][:150]}...\n"
            prompt += "\n"
        
        prompt += f"""DRAFT TO VALIDATE:
{draft}

VALIDATION CHECKLIST:
1. ✅ Is the draft MORE than just a greeting? (Must answer: YES)
2. ✅ Does it address the sender's specific questions/concerns? (Must answer: YES)
3. ✅ Does it provide helpful, actionable information? (Must answer: YES)
4. ✅ Is it at least 50 characters and 20 words? (Must answer: YES)
5. ✅ Is it professional and well-written? (Must answer: YES)
6. ✅ Does it avoid repeating what was already said? (Must answer: YES)
7. ✅ Is it specific to this situation, not generic? (Must answer: YES)

EXAMPLES OF INVALID DRAFTS (MUST REJECT):
❌ "Hi John,"
❌ "Hello Sarah, "
❌ "Dear Customer,"
❌ "Hi there, thanks for reaching out."
❌ Any draft under 50 characters
❌ Any draft that doesn't answer the questions asked

If ANY checklist item fails, mark as invalid.

Respond with JSON indicating validation result."""
        
        return prompt
    
    # ============================================================================
    # GROQ API INTEGRATION
    # ============================================================================
    
    async def _call_groq_api(
        self,
        system_message: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 800
    ) -> str:
        """
        Call Groq API with error handling
        
        Returns:
            Response text from the API
        """
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY not configured")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    'https://api.groq.com/openai/v1/chat/completions',
                    headers={
                        'Authorization': f'Bearer {self.groq_api_key}',
                        'Content-Type': 'application/json'
                    },
                    json={
                        'model': config.GROQ_DRAFT_MODEL,
                        'messages': [
                            {'role': 'system', 'content': system_message},
                            {'role': 'user', 'content': user_message}
                        ],
                        'temperature': temperature,
                        'max_tokens': max_tokens
                    }
                )
                
                if response.status_code != 200:
                    error_detail = response.text
                    logger.error(f"Groq API error {response.status_code}: {error_detail}")
                    raise Exception(f"Groq API error: {response.status_code}")
                
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # Track token usage
                usage = result.get('usage', {})
                tokens = usage.get('total_tokens', 0)
                self.tokens_used += tokens
                
                return content
                
        except httpx.TimeoutException:
            logger.error("Groq API timeout")
            raise Exception("Groq API timeout")
        except Exception as e:
            logger.error(f"Groq API call failed: {e}", exc_info=True)
            raise
    
    # ============================================================================
    # CLAUDE API INTEGRATION
    # ============================================================================
    
    async def _call_claude_api(
        self,
        system_message: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 800
    ) -> str:
        """
        Call Claude (Anthropic) API with error handling
        
        Returns:
            Response text from the API
        """
        if not self.claude_client:
            raise ValueError("Claude API not configured")
        
        try:
            response = await self.claude_client.messages.create(
                model=config.CLAUDE_DRAFT_MODEL,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_message,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )
            
            # Extract content from response
            content = response.content[0].text
            
            # Track token usage
            if hasattr(response, 'usage'):
                tokens = response.usage.input_tokens + response.usage.output_tokens
                self.tokens_used += tokens
            
            return content
            
        except Exception as e:
            logger.error(f"Claude API call failed: {e}", exc_info=True)
            raise
    
    # ============================================================================
    # UNIFIED LLM API CALL WITH FALLBACK
    # ============================================================================
    
    async def _call_llm_api(
        self,
        system_message: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 800,
        provider: Optional[str] = None
    ) -> str:
        """
        Unified LLM API call with automatic fallback
        
        Args:
            system_message: System instructions
            user_message: User prompt
            temperature: Temperature setting
            max_tokens: Maximum tokens to generate
            provider: Specific provider to use ('groq' or 'claude'), or None for auto-selection
            
        Returns:
            Response text from the API
        """
        # Determine which provider to try first
        if provider:
            primary = provider
            fallback = self.fallback_provider if provider != self.fallback_provider else None
        else:
            primary = self.primary_provider
            fallback = self.fallback_provider
        
        # Try primary provider
        try:
            if primary == 'groq' and self.groq_api_key:
                logger.debug(f"Using Groq API (primary)")
                return await self._call_groq_api(system_message, user_message, temperature, max_tokens)
            elif primary == 'claude' and self.claude_client:
                logger.debug(f"Using Claude API (primary)")
                return await self._call_claude_api(system_message, user_message, temperature, max_tokens)
            else:
                raise ValueError(f"Primary provider '{primary}' not configured")
        except Exception as e:
            logger.warning(f"Primary provider '{primary}' failed: {e}")
            
            # Try fallback provider if available
            if fallback and fallback != primary:
                try:
                    logger.info(f"Attempting fallback to '{fallback}' provider")
                    if fallback == 'groq' and self.groq_api_key:
                        return await self._call_groq_api(system_message, user_message, temperature, max_tokens)
                    elif fallback == 'claude' and self.claude_client:
                        return await self._call_claude_api(system_message, user_message, temperature, max_tokens)
                except Exception as fallback_error:
                    logger.error(f"Fallback provider '{fallback}' also failed: {fallback_error}")
                    raise Exception(f"Both primary and fallback LLM providers failed")
            
            # No fallback available or already failed
            raise
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    def _parse_json_response(self, content: str) -> Dict:
        """Parse JSON response, handling markdown code blocks"""
        try:
            # Remove markdown code blocks if present
            json_content = content.strip()
            if json_content.startswith('```json'):
                json_content = json_content[7:]
            if json_content.startswith('```'):
                json_content = json_content[3:]
            if json_content.endswith('```'):
                json_content = json_content[:-3]
            json_content = json_content.strip()
            
            return json.loads(json_content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {content}")
            raise ValueError(f"Invalid JSON response: {str(e)}")
    
    def _convert_datetime_fields(self, doc: Dict):
        """Convert datetime fields to ISO strings for Pydantic compatibility"""
        if isinstance(doc.get('created_at'), datetime):
            doc['created_at'] = doc['created_at'].isoformat()
        if isinstance(doc.get('updated_at'), datetime):
            doc['updated_at'] = doc['updated_at'].isoformat()
