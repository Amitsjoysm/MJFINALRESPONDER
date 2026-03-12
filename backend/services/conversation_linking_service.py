"""
Conversation Linking Service
Intelligently links emails across different threads from the same sender
Provides context aggregation for better AI responses
"""
import logging
import hashlib
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
import httpx

from config import config

logger = logging.getLogger(__name__)


class ConversationLinkingService:
    """
    Service to intelligently link conversations across different email threads
    
    Features:
    1. Groups emails by sender email address
    2. Detects related conversations using AI semantic similarity
    3. Provides aggregated context for draft generation
    4. Manages follow-ups across all related threads
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.groq_api_key = config.GROQ_API_KEY
        self.similarity_threshold = 0.7  # 70% similarity to consider related
        
    def generate_conversation_group_id(self, user_id: str, sender_email: str) -> str:
        """
        Generate a stable conversation group ID for all emails from a sender
        
        Args:
            user_id: The recipient user ID
            sender_email: The sender's email address
            
        Returns:
            A stable hash-based group ID
        """
        # Normalize email to lowercase
        sender_email = sender_email.lower().strip()
        
        # Create stable hash
        hash_input = f"{user_id}:{sender_email}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:32]
    
    async def get_conversation_history(
        self, 
        user_id: str, 
        sender_email: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get all emails in a conversation group (from the same sender)
        
        Args:
            user_id: The recipient user ID
            sender_email: The sender's email address
            limit: Maximum number of emails to retrieve
            
        Returns:
            List of email documents sorted by date (newest first)
        """
        conversation_group_id = self.generate_conversation_group_id(user_id, sender_email)
        
        emails = await self.db.emails.find({
            "user_id": user_id,
            "from_email": sender_email.lower()
        }).sort("received_at", -1).limit(limit).to_list(limit)
        
        logger.info(f"Found {len(emails)} emails in conversation with {sender_email}")
        return emails
    
    async def check_conversation_similarity(
        self,
        new_email_subject: str,
        new_email_body: str,
        previous_emails: List[Dict[str, Any]]
    ) -> Tuple[bool, float, Optional[str]]:
        """
        Check if new email is semantically related to previous conversations
        Uses AI to detect topic similarity even with different thread IDs
        
        Args:
            new_email_subject: Subject of new email
            new_email_body: Body of new email
            previous_emails: List of previous email documents
            
        Returns:
            Tuple of (is_related, confidence_score, related_context)
        """
        if not previous_emails:
            return False, 0.0, None
        
        if not self.groq_api_key:
            logger.warning("Groq API key not configured, using basic matching")
            return self._basic_similarity_check(new_email_subject, new_email_body, previous_emails)
        
        try:
            # Build context from previous emails
            previous_context = []
            for email in previous_emails[:5]:  # Last 5 emails
                previous_context.append(
                    f"Subject: {email.get('subject', 'N/A')}\n"
                    f"Content: {email.get('body', 'N/A')[:200]}..."
                )
            
            previous_text = "\n\n".join(previous_context)
            
            # AI prompt to check similarity
            prompt = f"""You are an email conversation analyzer. Determine if the new email is related to previous conversations.

PREVIOUS EMAILS:
{previous_text}

NEW EMAIL:
Subject: {new_email_subject}
Content: {new_email_body[:500]}

Analyze if the new email:
1. Continues the same topic/conversation
2. References previous discussions
3. Is a follow-up or related inquiry
4. Shares common context (project, product, issue)

Respond with JSON ONLY:
{{
    "is_related": true/false,
    "confidence": 0.0-1.0,
    "reason": "brief explanation",
    "shared_topics": ["topic1", "topic2"]
}}"""

            # Call Groq API
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.groq_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": config.GROQ_DRAFT_MODEL,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.3,
                        "max_tokens": 500
                    }
                )
            
            if response.status_code != 200:
                logger.error(f"Groq API error: {response.status_code} - {response.text}")
                return self._basic_similarity_check(new_email_subject, new_email_body, previous_emails)
            
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()
            
            # Parse JSON response
            import json
            if content.startswith('```json'):
                content = content.split('```json')[1].split('```')[0].strip()
            elif content.startswith('```'):
                content = content.split('```')[1].split('```')[0].strip()
            
            analysis = json.loads(content)
            
            is_related = analysis.get('is_related', False)
            confidence = float(analysis.get('confidence', 0.0))
            reason = analysis.get('reason', 'Unknown')
            shared_topics = analysis.get('shared_topics', [])
            
            related_context = f"{reason}. Shared topics: {', '.join(shared_topics)}" if shared_topics else reason
            
            logger.info(f"Conversation similarity: {is_related} (confidence: {confidence:.2f}) - {reason}")
            
            return is_related, confidence, related_context
            
        except Exception as e:
            logger.error(f"Error checking conversation similarity: {e}", exc_info=True)
            return self._basic_similarity_check(new_email_subject, new_email_body, previous_emails)
    
    def _basic_similarity_check(
        self,
        new_subject: str,
        new_body: str,
        previous_emails: List[Dict[str, Any]]
    ) -> Tuple[bool, float, Optional[str]]:
        """
        Basic keyword-based similarity check (fallback)
        
        Args:
            new_subject: Subject of new email
            new_body: Body of new email
            previous_emails: List of previous emails
            
        Returns:
            Tuple of (is_related, confidence, context)
        """
        # Extract keywords from new email
        new_text = f"{new_subject} {new_body}".lower()
        new_keywords = set(word for word in new_text.split() if len(word) > 4)
        
        # Check for common keywords in previous emails
        max_overlap = 0
        for email in previous_emails[:3]:
            prev_text = f"{email.get('subject', '')} {email.get('body', '')}".lower()
            prev_keywords = set(word for word in prev_text.split() if len(word) > 4)
            
            if prev_keywords and new_keywords:
                overlap = len(new_keywords & prev_keywords) / len(new_keywords)
                max_overlap = max(max_overlap, overlap)
        
        is_related = max_overlap > 0.3  # 30% keyword overlap
        confidence = min(max_overlap, 0.6)  # Cap at 0.6 for basic matching
        
        context = f"Basic keyword matching: {max_overlap:.0%} overlap" if is_related else None
        
        return is_related, confidence, context
    
    async def get_aggregated_context(
        self,
        user_id: str,
        sender_email: str,
        current_email_id: Optional[str] = None,
        max_emails: int = 5
    ) -> str:
        """
        Get aggregated conversation context from all related emails
        
        Args:
            user_id: The recipient user ID
            sender_email: The sender's email address
            current_email_id: ID of current email to exclude
            max_emails: Maximum emails to include in context
            
        Returns:
            Formatted context string for AI draft generation
        """
        # Get conversation history
        all_emails = await self.get_conversation_history(user_id, sender_email, limit=max_emails + 1)
        
        # Exclude current email
        if current_email_id:
            all_emails = [e for e in all_emails if e.get('id') != current_email_id]
        
        all_emails = all_emails[:max_emails]
        
        if not all_emails:
            return ""
        
        # Build context string
        context_parts = [
            "=== PREVIOUS CONVERSATION HISTORY ===",
            f"All emails from: {sender_email}",
            f"Total emails in conversation: {len(all_emails)}",
            ""
        ]
        
        for i, email in enumerate(all_emails, 1):
            received_at = email.get('received_at', 'Unknown date')
            subject = email.get('subject', 'No subject')
            body = email.get('body', '')[:300]  # First 300 chars
            our_reply = email.get('draft_content', email.get('reply_sent', ''))
            
            context_parts.append(f"--- Email {i} (Received: {received_at}) ---")
            context_parts.append(f"Subject: {subject}")
            context_parts.append(f"Their message: {body}")
            
            if our_reply:
                context_parts.append(f"Our reply: {our_reply[:200]}...")
            
            context_parts.append("")
        
        context_parts.append("=== END CONVERSATION HISTORY ===")
        context_parts.append("")
        context_parts.append("IMPORTANT: Use this context to provide a coherent response that acknowledges previous discussions.")
        
        return "\n".join(context_parts)
    
    async def link_email_to_conversation(
        self,
        email_id: str,
        user_id: str,
        sender_email: str
    ) -> str:
        """
        Link an email to its conversation group
        
        Args:
            email_id: The email ID to link
            user_id: The recipient user ID
            sender_email: The sender's email address
            
        Returns:
            The conversation group ID
        """
        conversation_group_id = self.generate_conversation_group_id(user_id, sender_email)
        
        # Update email with conversation group ID
        await self.db.emails.update_one(
            {"id": email_id},
            {
                "$set": {
                    "conversation_group_id": conversation_group_id,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        logger.info(f"Linked email {email_id} to conversation group {conversation_group_id}")
        return conversation_group_id
    
    async def cancel_all_conversation_followups(
        self,
        user_id: str,
        sender_email: str,
        reason: str = "Reply received in conversation"
    ) -> int:
        """
        Cancel ALL pending follow-ups for a conversation (across all threads)
        
        Args:
            user_id: The recipient user ID
            sender_email: The sender's email address
            reason: Cancellation reason
            
        Returns:
            Number of follow-ups cancelled
        """
        # Get all emails from this sender
        emails = await self.get_conversation_history(user_id, sender_email, limit=100)
        email_ids = [e['id'] for e in emails]
        
        if not email_ids:
            return 0
        
        # Cancel all pending follow-ups for ANY email from this sender
        result = await self.db.follow_ups.update_many(
            {
                "user_id": user_id,
                "email_id": {"$in": email_ids},
                "status": "pending"
            },
            {
                "$set": {
                    "status": "cancelled",
                    "cancellation_reason": reason,
                    "cancelled_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        cancelled_count = result.modified_count
        
        if cancelled_count > 0:
            logger.info(f"Cancelled {cancelled_count} follow-ups for conversation with {sender_email}")
        
        return cancelled_count
    
    async def get_conversation_summary(
        self,
        user_id: str,
        sender_email: str
    ) -> Dict[str, Any]:
        """
        Get a summary of the entire conversation
        
        Args:
            user_id: The recipient user ID
            sender_email: The sender's email address
            
        Returns:
            Dictionary with conversation statistics
        """
        conversation_group_id = self.generate_conversation_group_id(user_id, sender_email)
        
        # Get all emails
        all_emails = await self.get_conversation_history(user_id, sender_email, limit=100)
        
        # Count threads
        unique_threads = set(e.get('thread_id') for e in all_emails if e.get('thread_id'))
        
        # Count sent vs received
        emails_received = len(all_emails)
        emails_sent = len([e for e in all_emails if e.get('status') == 'sent'])
        
        # Get date range
        if all_emails:
            first_email = all_emails[-1]
            last_email = all_emails[0]
            first_contact = first_email.get('received_at', 'Unknown')
            last_contact = last_email.get('received_at', 'Unknown')
        else:
            first_contact = None
            last_contact = None
        
        return {
            "conversation_group_id": conversation_group_id,
            "sender_email": sender_email,
            "total_emails": emails_received,
            "emails_sent": emails_sent,
            "unique_threads": len(unique_threads),
            "first_contact": first_contact,
            "last_contact": last_contact,
            "thread_ids": list(unique_threads)
        }
