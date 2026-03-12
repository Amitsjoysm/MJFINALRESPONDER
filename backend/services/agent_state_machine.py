"""
Agent State Machine - Parlant.io-inspired state management
Provides structured, predictable state transitions for email processing and lead qualification
"""
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)


class EmailProcessingState(str, Enum):
    """Email processing states"""
    NEW = "new"
    CLASSIFYING = "classifying"
    CLASSIFIED = "classified"
    DETECTING_MEETING = "detecting_meeting"
    DRAFTING = "drafting"
    DRAFT_READY = "draft_ready"
    VALIDATING = "validating"
    VALIDATED = "validated"
    SENDING = "sending"
    SENT = "sent"
    ERROR = "error"
    ESCALATED = "escalated"


class LeadQualificationState(str, Enum):
    """Lead qualification states"""
    NEW = "new"
    AWAITING_INFO = "awaiting_info"
    QUALIFYING = "qualifying"
    QUALIFIED = "qualified"
    UNQUALIFIED = "unqualified"
    CONVERTED = "converted"
    LOST = "lost"


class DecisionReason:
    """Structured decision reasoning"""
    
    def __init__(self, reason: str, confidence: float, evidence: Dict, guideline: str):
        self.reason = reason
        self.confidence = confidence
        self.evidence = evidence
        self.guideline = guideline
        self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> Dict:
        return {
            "reason": self.reason,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "guideline": self.guideline,
            "timestamp": self.timestamp
        }


class StateTransition:
    """State transition with reasoning"""
    
    def __init__(self, from_state: str, to_state: str, reason: DecisionReason, actor: str = "system"):
        self.from_state = from_state
        self.to_state = to_state
        self.reason = reason
        self.actor = actor
        self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> Dict:
        return {
            "from_state": self.from_state,
            "to_state": self.to_state,
            "reason": self.reason.to_dict(),
            "actor": self.actor,
            "timestamp": self.timestamp
        }


class AgentStateMachine:
    """
    Parlant.io-inspired state machine for predictable agent behavior
    
    Key features:
    - Explicit state transitions with reasoning
    - Decision logging and audit trail
    - Validation checkpoints at each state
    - Deterministic behavior with clear failure states
    """
    
    # Email processing state transitions
    EMAIL_TRANSITIONS = {
        EmailProcessingState.NEW: [EmailProcessingState.CLASSIFYING, EmailProcessingState.ERROR],
        EmailProcessingState.CLASSIFYING: [EmailProcessingState.CLASSIFIED, EmailProcessingState.ERROR],
        EmailProcessingState.CLASSIFIED: [EmailProcessingState.DETECTING_MEETING, EmailProcessingState.DRAFTING],
        EmailProcessingState.DETECTING_MEETING: [EmailProcessingState.DRAFTING, EmailProcessingState.ERROR],
        EmailProcessingState.DRAFTING: [EmailProcessingState.DRAFT_READY, EmailProcessingState.VALIDATING, EmailProcessingState.ERROR],
        EmailProcessingState.DRAFT_READY: [EmailProcessingState.VALIDATING, EmailProcessingState.SENDING],
        EmailProcessingState.VALIDATING: [EmailProcessingState.VALIDATED, EmailProcessingState.DRAFTING, EmailProcessingState.ESCALATED],
        EmailProcessingState.VALIDATED: [EmailProcessingState.SENDING, EmailProcessingState.SENT],
        EmailProcessingState.SENDING: [EmailProcessingState.SENT, EmailProcessingState.ERROR],
        EmailProcessingState.SENT: [],
        EmailProcessingState.ERROR: [EmailProcessingState.CLASSIFYING, EmailProcessingState.ESCALATED],
        EmailProcessingState.ESCALATED: []
    }
    
    # Lead qualification state transitions
    LEAD_TRANSITIONS = {
        LeadQualificationState.NEW: [LeadQualificationState.AWAITING_INFO, LeadQualificationState.QUALIFYING],
        LeadQualificationState.AWAITING_INFO: [LeadQualificationState.QUALIFYING, LeadQualificationState.UNQUALIFIED],
        LeadQualificationState.QUALIFYING: [LeadQualificationState.QUALIFIED, LeadQualificationState.UNQUALIFIED, LeadQualificationState.AWAITING_INFO],
        LeadQualificationState.QUALIFIED: [LeadQualificationState.CONVERTED, LeadQualificationState.LOST],
        LeadQualificationState.UNQUALIFIED: [LeadQualificationState.QUALIFYING],
        LeadQualificationState.CONVERTED: [],
        LeadQualificationState.LOST: []
    }
    
    def __init__(self, db):
        self.db = db
    
    async def transition_email_state(
        self,
        email_id: str,
        to_state: EmailProcessingState,
        reason: DecisionReason,
        actor: str = "system"
    ) -> bool:
        """
        Transition email to new state with validation and logging
        
        Returns:
            True if transition successful, False if invalid
        """
        try:
            # Get current state
            email_doc = await self.db.emails.find_one({"id": email_id})
            if not email_doc:
                logger.error(f"Email {email_id} not found")
                return False
            
            from_state = email_doc.get("status", EmailProcessingState.NEW)
            
            # Validate transition
            if not self._is_valid_email_transition(from_state, to_state):
                logger.warning(f"Invalid email state transition: {from_state} -> {to_state}")
                return False
            
            # Create transition record
            transition = StateTransition(from_state, to_state, reason, actor)
            
            # Update database
            await self.db.emails.update_one(
                {"id": email_id},
                {
                    "$set": {
                        "status": to_state,
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    },
                    "$push": {
                        "state_history": transition.to_dict()
                    }
                }
            )
            
            logger.info(f"✓ Email {email_id} transitioned: {from_state} -> {to_state} (reason: {reason.reason})")
            return True
            
        except Exception as e:
            logger.error(f"Error transitioning email state: {e}")
            return False
    
    async def transition_lead_state(
        self,
        lead_id: str,
        to_state: LeadQualificationState,
        reason: DecisionReason,
        actor: str = "system"
    ) -> bool:
        """
        Transition lead to new state with validation and logging
        
        Returns:
            True if transition successful, False if invalid
        """
        try:
            # Get current state
            lead_doc = await self.db.inbound_leads.find_one({"id": lead_id})
            if not lead_doc:
                logger.error(f"Lead {lead_id} not found")
                return False
            
            from_state = lead_doc.get("stage", LeadQualificationState.NEW)
            
            # Validate transition
            if not self._is_valid_lead_transition(from_state, to_state):
                logger.warning(f"Invalid lead state transition: {from_state} -> {to_state}")
                return False
            
            # Create transition record
            transition = StateTransition(from_state, to_state, reason, actor)
            
            # Update database
            await self.db.inbound_leads.update_one(
                {"id": lead_id},
                {
                    "$set": {
                        "stage": to_state,
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    },
                    "$push": {
                        "qualification_history": transition.to_dict()
                    }
                }
            )
            
            logger.info(f"✓ Lead {lead_id} transitioned: {from_state} -> {to_state} (reason: {reason.reason})")
            return True
            
        except Exception as e:
            logger.error(f"Error transitioning lead state: {e}")
            return False
    
    def _is_valid_email_transition(self, from_state: str, to_state: str) -> bool:
        """Validate email state transition"""
        try:
            from_enum = EmailProcessingState(from_state)
            to_enum = EmailProcessingState(to_state)
            return to_enum in self.EMAIL_TRANSITIONS.get(from_enum, [])
        except (ValueError, KeyError):
            return False
    
    def _is_valid_lead_transition(self, from_state: str, to_state: str) -> bool:
        """Validate lead state transition"""
        try:
            from_enum = LeadQualificationState(from_state)
            to_enum = LeadQualificationState(to_state)
            return to_enum in self.LEAD_TRANSITIONS.get(from_enum, [])
        except (ValueError, KeyError):
            return False
    
    async def get_state_history(self, entity_id: str, entity_type: str = "email") -> List[Dict]:
        """
        Get complete state transition history for audit trail
        
        Args:
            entity_id: Email or lead ID
            entity_type: "email" or "lead"
        
        Returns:
            List of state transitions with reasoning
        """
        try:
            if entity_type == "email":
                doc = await self.db.emails.find_one({"id": entity_id})
            else:
                doc = await self.db.inbound_leads.find_one({"id": entity_id})
            
            if not doc:
                return []
            
            history_key = "state_history" if entity_type == "email" else "qualification_history"
            return doc.get(history_key, [])
            
        except Exception as e:
            logger.error(f"Error getting state history: {e}")
            return []
