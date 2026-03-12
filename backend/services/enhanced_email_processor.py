"""
Enhanced Email Processor with Intelligent Cross-Thread Conversation Management
Handles emails that reply in different threads from the same sender
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase

from models.email import Email
from services.conversation_linking_service import ConversationLinkingService
from services.ai_agent_service import AIAgentService
from services.email_service import EmailService

logger = logging.getLogger(__name__)


class EnhancedEmailProcessor:
    """
    Enhanced email processing with intelligent conversation tracking
    
    Features:
    1. Links emails across different threads from the same sender
    2. Detects when a reply comes in a new thread
    3. Provides aggregated context from all related emails
    4. Cancels follow-ups across all threads when ANY reply is received
    5. Maintains conversation continuity for better AI responses
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.conversation_service = ConversationLinkingService(db)
        self.ai_service = AIAgentService(db)
        self.email_service = EmailService(db)
    
    async def process_email_with_conversation_context(
        self,
        email: Email
    ) -> Dict[str, Any]:
        """
        Process email with full conversation context, even across different threads
        
        Args:
            email: The email to process
            
        Returns:
            Processing result with conversation metadata
        """
        logger.info(f"Processing email {email.id} with conversation intelligence")
        
        # Step 1: Link email to conversation group
        conversation_group_id = await self.conversation_service.link_email_to_conversation(
            email.id,
            email.user_id,
            email.from_email
        )
        
        # Step 2: Get all previous emails from this sender
        previous_emails = await self.conversation_service.get_conversation_history(
            email.user_id,
            email.from_email,
            limit=10
        )
        
        # Exclude current email
        previous_emails = [e for e in previous_emails if e.get('id') != email.id]
        
        # Step 3: Check if this is a continuation of a previous conversation
        is_related = False
        similarity_confidence = 0.0
        related_context = None
        
        if previous_emails:
            is_related, similarity_confidence, related_context = \
                await self.conversation_service.check_conversation_similarity(
                    email.subject,
                    email.body,
                    previous_emails
                )
            
            logger.info(
                f"Conversation similarity check: is_related={is_related}, "
                f"confidence={similarity_confidence:.2f}, "
                f"previous_emails={len(previous_emails)}"
            )
        
        # Step 4: Get conversation summary
        conversation_summary = await self.conversation_service.get_conversation_summary(
            email.user_id,
            email.from_email
        )
        
        # Step 5: Update email with conversation metadata
        await self.db.emails.update_one(
            {"id": email.id},
            {
                "$set": {
                    "conversation_group_id": conversation_group_id,
                    "is_conversation_continuation": is_related,
                    "conversation_similarity_score": similarity_confidence,
                    "total_conversation_emails": conversation_summary['total_emails'],
                    "conversation_thread_count": conversation_summary['unique_threads'],
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        # Step 6: If this is a reply (continuation), cancel ALL pending follow-ups
        if is_related and previous_emails:
            cancelled_count = await self.conversation_service.cancel_all_conversation_followups(
                email.user_id,
                email.from_email,
                reason=f"Reply received in {'different' if email.thread_id != previous_emails[0].get('thread_id') else 'same'} thread"
            )
            
            if cancelled_count > 0:
                logger.info(
                    f"✓ Cancelled {cancelled_count} pending follow-ups across "
                    f"{conversation_summary['unique_threads']} threads for {email.from_email}"
                )
                
                await self.db.emails.update_one(
                    {"id": email.id},
                    {
                        "$push": {
                            "action_history": {
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                "action": "followups_cancelled",
                                "details": {
                                    "count": cancelled_count,
                                    "reason": "Reply received in conversation",
                                    "across_threads": conversation_summary['unique_threads'],
                                    "thread_ids": conversation_summary['thread_ids']
                                },
                                "status": "success"
                            }
                        }
                    }
                )
        
        return {
            "conversation_group_id": conversation_group_id,
            "is_continuation": is_related,
            "similarity_score": similarity_confidence,
            "previous_emails_count": len(previous_emails),
            "unique_threads": conversation_summary['unique_threads'],
            "followups_cancelled": cancelled_count if is_related else 0,
            "related_context": related_context
        }
    
    async def get_context_for_draft_generation(
        self,
        email: Email
    ) -> str:
        """
        Get comprehensive context for AI draft generation
        Includes ALL related emails, even from different threads
        
        Args:
            email: The email to generate draft for
            
        Returns:
            Formatted context string with full conversation history
        """
        # Get aggregated context from all related emails
        context = await self.conversation_service.get_aggregated_context(
            email.user_id,
            email.from_email,
            current_email_id=email.id,
            max_emails=5
        )
        
        if context:
            logger.info(f"Retrieved cross-thread context for email {email.id} from {email.from_email}")
        
        return context
    
    async def generate_draft_with_full_context(
        self,
        email: Email,
        intent_doc: Optional[Dict[str, Any]] = None,
        calendar_event: Optional[Dict[str, Any]] = None,
        validation_issues: Optional[str] = None
    ) -> str:
        """
        Generate draft with full conversation context from all related threads
        
        Args:
            email: The email to respond to
            intent_doc: Matched intent document
            calendar_event: Calendar event if meeting was detected
            validation_issues: Issues from previous validation attempts
            
        Returns:
            Generated draft content
        """
        # Get comprehensive conversation context
        conversation_context = await self.get_context_for_draft_generation(email)
        
        # Get knowledge base
        kb_entries = await self.db.knowledge_base.find({
            "user_id": email.user_id,
            "is_active": True
        }).to_list(10)
        
        # Build knowledge base context
        kb_context = ""
        if kb_entries:
            kb_parts = ["=== KNOWLEDGE BASE ==="]
            for kb in kb_entries:
                kb_parts.append(f"\n**{kb['title']}** ({kb.get('category', 'General')})")
                kb_parts.append(kb['content'][:500])  # First 500 chars
            kb_parts.append("\n=== END KNOWLEDGE BASE ===\n")
            kb_context = "\n".join(kb_parts)
        
        # Combine context
        full_context = ""
        if conversation_context:
            full_context += conversation_context + "\n\n"
        if kb_context:
            full_context += kb_context + "\n\n"
        
        # Generate draft using AI service with full context
        draft = await self.ai_service.generate_draft(
            email=email,
            user_id=email.user_id,
            intent_doc=intent_doc,
            thread_context=full_context,  # Pass conversation + KB context
            calendar_event=calendar_event,
            validation_issues=validation_issues
        )
        
        # Add metadata about context usage
        if conversation_context:
            await self.db.emails.update_one(
                {"id": email.id},
                {
                    "$push": {
                        "action_history": {
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "action": "draft_generated_with_context",
                            "details": {
                                "used_conversation_history": True,
                                "context_length": len(conversation_context),
                                "note": "Draft generated with full conversation history across threads"
                            },
                            "status": "success"
                        }
                    }
                }
            )
        
        return draft
    
    async def should_create_followups(
        self,
        email: Email
    ) -> bool:
        """
        Determine if follow-ups should be created for this email
        Considers conversation history and whether this is a reply
        
        Args:
            email: The email to check
            
        Returns:
            True if follow-ups should be created, False otherwise
        """
        # Get conversation history
        previous_emails = await self.conversation_service.get_conversation_history(
            email.user_id,
            email.from_email,
            limit=5
        )
        
        # Exclude current email
        previous_emails = [e for e in previous_emails if e.get('id') != email.id]
        
        if not previous_emails:
            # First email from this sender - create follow-ups
            return True
        
        # Check if this looks like a reply to our previous email
        is_related, confidence, _ = await self.conversation_service.check_conversation_similarity(
            email.subject,
            email.body,
            previous_emails
        )
        
        if is_related:
            # This is a reply - don't create new follow-ups
            logger.info(f"Not creating follow-ups for email {email.id} - appears to be a reply (confidence: {confidence:.2f})")
            return False
        
        # New topic or question - create follow-ups
        return True
