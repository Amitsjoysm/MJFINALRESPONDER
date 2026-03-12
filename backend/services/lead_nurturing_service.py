"""
Lead Nurturing Service
Generates smart nurturing questions for lead qualification
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class LeadNurturingService:
    """Service for lead nurturing and question generation"""
    
    def __init__(self, db):
        self.db = db
        self.nurturing_config_collection = db['lead_nurturing_configs']  # Fixed collection name
    
    async def should_nurture_lead(
        self,
        user_id: str,
        intent_doc: Optional[Dict],
        nurturing_exchanges_count: int
    ) -> bool:
        """
        Determine if lead should be nurtured with questions
        
        Returns True if:
        - Global nurturing is enabled
        - Intent has nurturing enabled
        - Max exchanges not reached
        """
        # Get user's settings
        users_collection = self.db['users']
        user = await users_collection.find_one({"id": user_id})
        
        if not user:
            return False
        
        # Check global setting
        global_enabled = user.get('global_lead_nurturing_enabled', False)
        if not global_enabled:
            return False
        
        # Check intent-specific setting
        if intent_doc:
            intent_enabled = intent_doc.get('enable_lead_nurturing', False)
            if not intent_enabled:
                return False
        
        # Get nurturing config to check max exchanges
        config_id = user.get('default_nurturing_config_id')
        if config_id:
            config = await self.nurturing_config_collection.find_one({
                "id": config_id,
                "user_id": user_id
            })
            if config:
                max_exchanges = config.get('max_exchanges', 2)
                # Stop nurturing if max exchanges reached
                if nurturing_exchanges_count >= max_exchanges:
                    return False
        else:
            # Default: max 2 exchanges
            if nurturing_exchanges_count >= 2:
                return False
        
        return True
    
    async def generate_nurturing_questions(
        self,
        user_id: str,
        email_content: str,
        thread_context: List[Dict],
        questions_already_asked: List[Dict],
        config_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate smart nurturing questions based on context
        
        Returns list of questions to ask (max 2 per email)
        """
        try:
            # Get nurturing configuration
            if config_id:
                config = await self.nurturing_config_collection.find_one({
                    "id": config_id,
                    "user_id": user_id,
                    "is_active": True
                })
            else:
                # Get default active config for user
                config = await self.nurturing_config_collection.find_one({
                    "user_id": user_id,
                    "is_active": True,
                    "is_enabled": True
                })
            
            if not config:
                logger.warning(f"No active nurturing config found for user {user_id}")
                return []
            
            questions_config = config.get('questions', [])
            if not questions_config:
                return []
            
            questions_per_email = config.get('questions_per_email', 2)
            use_contextual = config.get('use_contextual_questions', True)
            
            # Get already asked question keys
            asked_keys = {q.get('question_key') for q in questions_already_asked}
            
            # Filter available questions
            available_questions = []
            for q in questions_config:
                question_key = q.get('question_id')
                max_asks = q.get('max_asks', 1)
                
                # Check if already asked
                ask_count = sum(1 for asked in questions_already_asked if asked.get('question_key') == question_key)
                
                if ask_count < max_asks:
                    available_questions.append(q)
            
            if not available_questions:
                logger.info(f"No more questions to ask for user {user_id}")
                return []
            
            # Select questions to ask
            selected_questions = []
            
            if use_contextual:
                # Select contextually relevant questions
                selected_questions = await self._select_contextual_questions(
                    available_questions,
                    email_content,
                    questions_per_email
                )
            else:
                # Select by priority
                sorted_questions = sorted(available_questions, key=lambda q: q.get('priority', 999))
                selected_questions = sorted_questions[:questions_per_email]
            
            # Format questions for return
            return [
                {
                    "question_key": q.get('question_id'),
                    "question_text": q.get('question_text'),
                    "is_required": q.get('is_required', False)
                }
                for q in selected_questions
            ]
            
        except Exception as e:
            logger.error(f"Error generating nurturing questions: {e}")
            return []
    
    async def _select_contextual_questions(
        self,
        questions: List[Dict],
        email_content: str,
        max_questions: int
    ) -> List[Dict]:
        """
        Select questions based on email content context
        
        Prioritizes questions whose keywords appear in the email
        """
        email_lower = email_content.lower()
        
        # Score questions by relevance
        scored_questions = []
        for q in questions:
            context_keywords = q.get('context_keywords', [])
            priority = q.get('priority', 999)
            
            # Calculate relevance score
            keyword_matches = sum(1 for keyword in context_keywords if keyword.lower() in email_lower)
            
            # Combine keyword matches with priority (lower priority number = higher importance)
            # More keyword matches = higher score, lower priority number = higher score
            relevance_score = (keyword_matches * 10) - priority
            
            scored_questions.append({
                'question': q,
                'relevance_score': relevance_score
            })
        
        # Sort by relevance score (highest first)
        scored_questions.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # Return top N questions
        return [sq['question'] for sq in scored_questions[:max_questions]]
    
    async def track_nurturing_response(
        self,
        lead_id: str,
        question_key: str,
        question_text: str,
        response: str
    ) -> bool:
        """
        Track a response to a nurturing question
        """
        try:
            leads_collection = self.db['inbound_leads']
            
            # Add response to nurturing_questions_asked array
            await leads_collection.update_one(
                {"id": lead_id},
                {
                    "$push": {
                        "nurturing_questions_asked": {
                            "question_key": question_key,
                            "question_text": question_text,
                            "response": response,
                            "answered_at": datetime.now(timezone.utc).isoformat()
                        }
                    },
                    "$inc": {
                        "nurturing_exchanges_count": 1
                    },
                    "$set": {
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error tracking nurturing response: {e}")
            return False
    
    async def extract_responses_from_email(
        self,
        email_content: str,
        questions_asked: List[Dict]
    ) -> Dict[str, str]:
        """
        Extract responses from email content for previously asked questions
        
        This is a simple implementation. For production, you might want to use
        AI to better extract responses.
        """
        responses = {}
        
        # Simple keyword-based extraction
        # In production, consider using AI/NLP for better extraction
        
        for question in questions_asked:
            question_key = question.get('question_key')
            question_text = question.get('question_text', '').lower()
            
            # Look for the question in the email
            if question_text in email_content.lower():
                # Try to extract the answer (text after the question)
                parts = email_content.lower().split(question_text)
                if len(parts) > 1:
                    # Get the next sentence as answer
                    answer_part = parts[1].split('.')[0].strip()
                    responses[question_key] = answer_part
        
        return responses
    
    async def format_questions_for_draft(
        self,
        questions: List[Dict],
        natural_integration: bool = True
    ) -> str:
        """
        Format questions to be included in the draft email
        
        If natural_integration is True, questions are formatted to be
        woven into conversation naturally.
        """
        if not questions:
            return ""
        
        if natural_integration:
            # Format for natural integration
            if len(questions) == 1:
                return f"\n\n{questions[0]['question_text']}"
            else:
                formatted = "\n\nTo better assist you, I'd like to know:"
                for i, q in enumerate(questions, 1):
                    formatted += f"\n{i}. {q['question_text']}"
                return formatted
        else:
            # More formal format
            formatted = "\n\nI have a few questions to better understand your needs:\n"
            for i, q in enumerate(questions, 1):
                required = " (required)" if q.get('is_required') else ""
                formatted += f"\n{i}. {q['question_text']}{required}"
            return formatted
