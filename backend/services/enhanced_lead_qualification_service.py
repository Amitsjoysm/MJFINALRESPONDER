"""
Enhanced Lead Qualification Service - Parlant.io-inspired
Provides structured, predictable lead qualification with explicit reasoning
"""
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone

from services.agent_state_machine import (
    AgentStateMachine,
    LeadQualificationState,
    DecisionReason
)
from services.agent_guidelines import GuidelineEngine
from services.lead_qualification_service import LeadQualificationService
from services.lead_ai_service import LeadAIService

logger = logging.getLogger(__name__)


class EnhancedLeadQualificationService:
    """
    Enhanced lead qualification with Parlant.io-like architecture
    
    Key improvements:
    - Explicit state management with state machine
    - Guideline-based decision making
    - Full audit trail of decisions
    - Predictable, deterministic behavior
    - Clear reasoning for every decision
    """
    
    def __init__(self, db):
        self.db = db
        self.state_machine = AgentStateMachine(db)
        self.guideline_engine = GuidelineEngine()
        self.qualification_service = LeadQualificationService(db)
        self.ai_service = LeadAIService()
    
    async def process_lead_with_state_tracking(
        self,
        user_id: str,
        email_id: str,
        email_content: str,
        from_email: str,
        intent_doc: Optional[Dict],
        thread_context: List[Dict]
    ) -> Tuple[bool, str, List[Dict], str, List[Dict]]:
        """
        Process lead with full state tracking and reasoning
        
        Returns:
            Tuple of (should_create_lead, lead_stage, questions_to_ask, lead_id, decision_log)
        """
        decision_log = []
        
        try:
            # Step 1: Check if lead exists
            lead = await self._find_existing_lead(user_id, from_email)
            
            if not lead:
                # NEW LEAD - Initialize
                logger.info(f"🆕 New lead detected: {from_email}")
                
                lead_id = await self._create_lead_with_state(
                    user_id,
                    from_email,
                    email_id,
                    intent_doc
                )
                
                decision_log.append({
                    "step": "lead_creation",
                    "decision": "created_new_lead",
                    "reason": "First contact from this email address",
                    "state": LeadQualificationState.NEW,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
                # Transition to AWAITING_INFO
                reason = DecisionReason(
                    reason="New lead requires information gathering",
                    confidence=1.0,
                    evidence={"first_contact": True, "from_email": from_email},
                    guideline="initial_lead_processing"
                )
                
                await self.state_machine.transition_lead_state(
                    lead_id,
                    LeadQualificationState.AWAITING_INFO,
                    reason
                )
                
                # Generate questions
                questions = await self._generate_questions_with_reasoning(
                    user_id,
                    email_content,
                    thread_context,
                    [],
                    1
                )
                
                decision_log.append({
                    "step": "question_generation",
                    "decision": f"generated_{len(questions)}_questions",
                    "reason": "Gathering information for qualification",
                    "questions": questions,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
                return False, LeadQualificationState.AWAITING_INFO, questions, lead_id, decision_log
            
            else:
                # EXISTING LEAD - Continue qualification
                lead_id = lead['id']
                current_state = lead.get('stage', LeadQualificationState.AWAITING_INFO)
                attempt = lead.get('qualification_attempt', 0)
                
                logger.info(f"🔄 Existing lead {lead_id}: state={current_state}, attempt={attempt}")
                
                decision_log.append({
                    "step": "lead_retrieval",
                    "decision": "existing_lead_found",
                    "lead_id": lead_id,
                    "current_state": current_state,
                    "attempt": attempt,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
                # Check if already in terminal state
                if current_state in [LeadQualificationState.QUALIFIED, 
                                    LeadQualificationState.UNQUALIFIED,
                                    LeadQualificationState.CONVERTED,
                                    LeadQualificationState.LOST]:
                    
                    decision_log.append({
                        "step": "state_check",
                        "decision": "terminal_state_reached",
                        "reason": f"Lead already in final state: {current_state}",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    
                    return True, current_state, [], lead_id, decision_log
                
                # Transition to QUALIFYING
                reason = DecisionReason(
                    reason="Analyzing lead responses for qualification",
                    confidence=0.9,
                    evidence={"attempt": attempt, "state": current_state},
                    guideline="lead_qualification_evaluation"
                )
                
                await self.state_machine.transition_lead_state(
                    lead_id,
                    LeadQualificationState.QUALIFYING,
                    reason
                )
                
                # Extract answers with AI
                questions_asked = lead.get('last_questions_asked', [])
                answers = await self.ai_service.extract_answers_from_email(
                    email_content,
                    questions_asked
                )
                
                decision_log.append({
                    "step": "answer_extraction",
                    "decision": f"extracted_{len(answers)}_answers",
                    "answers": answers,
                    "questions_asked": questions_asked,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
                # Store answers
                await self._store_answers(lead_id, answers, questions_asked)
                
                # Evaluate using guidelines
                context = self._build_qualification_context(lead, answers)
                action_result = await self.guideline_engine.get_best_action(context)
                
                if not action_result:
                    logger.warning(f"No guideline matched for lead {lead_id}\")\n                    action_result = {\"action\": \"mark_as_unqualified\", \"guideline\": \"default_fallback\"}\n                \n                decision_log.append({\n                    \"step\": \"guideline_matching\",\n                    \"decision\": action_result['action'],\n                    \"guideline\": action_result['guideline'],\n                    \"confidence_threshold\": action_result.get('confidence_threshold', 0.7),\n                    \"timestamp\": datetime.now(timezone.utc).isoformat()\n                })\n                \n                # Get qualification score\n                is_qualified, score, reasons = await self.qualification_service.evaluate_lead_qualification(\n                    user_id,\n                    lead,\n                    lead.get('qualification_criteria_id')\n                )\n                \n                decision_log.append({\n                    \"step\": \"scoring\",\n                    \"decision\": \"qualified\" if is_qualified else \"not_qualified\",\n                    \"score\": score,\n                    \"reasons\": reasons,\n                    \"timestamp\": datetime.now(timezone.utc).isoformat()\n                })\n                \n                # Make decision based on action and score\n                if action_result['action'] == 'mark_as_qualified' or score >= 60:\n                    # QUALIFIED\n                    reason = DecisionReason(\n                        reason=f\"Lead meets qualification criteria (score: {score})\",\n                        confidence=min(score / 100, 1.0),\n                        evidence={\"score\": score, \"reasons\": reasons, \"answers\": answers},\n                        guideline=action_result['guideline']\n                    )\n                    \n                    await self.state_machine.transition_lead_state(\n                        lead_id,\n                        LeadQualificationState.QUALIFIED,\n                        reason\n                    )\n                    \n                    await self._update_lead_score(lead_id, score, reasons)\n                    \n                    decision_log.append({\n                        \"step\": \"final_decision\",\n                        \"decision\": \"qualified\",\n                        \"reason\": reason.to_dict(),\n                        \"timestamp\": datetime.now(timezone.utc).isoformat()\n                    })\n                    \n                    return True, LeadQualificationState.QUALIFIED, [], lead_id, decision_log\n                \n                elif action_result['action'] == 'mark_as_unqualified' or score < 40:\n                    # UNQUALIFIED\n                    reason = DecisionReason(\n                        reason=f\"Lead does not meet qualification criteria (score: {score})\",\n                        confidence=min((100 - score) / 100, 1.0),\n                        evidence={\"score\": score, \"reasons\": reasons, \"answers\": answers},\n                        guideline=action_result['guideline']\n                    )\n                    \n                    await self.state_machine.transition_lead_state(\n                        lead_id,\n                        LeadQualificationState.UNQUALIFIED,\n                        reason\n                    )\n                    \n                    await self._update_lead_score(lead_id, score, reasons)\n                    \n                    decision_log.append({\n                        \"step\": \"final_decision\",\n                        \"decision\": \"unqualified\",\n                        \"reason\": reason.to_dict(),\n                        \"timestamp\": datetime.now(timezone.utc).isoformat()\n                    })\n                    \n                    return True, LeadQualificationState.UNQUALIFIED, [], lead_id, decision_log\n                \n                elif action_result['action'] == 'ask_qualification_questions':\n                    # NEEDS MORE INFO\n                    if attempt >= 3:\n                        # Max attempts - make final decision\n                        final_state = LeadQualificationState.QUALIFIED if score >= 50 else LeadQualificationState.UNQUALIFIED\n                        \n                        reason = DecisionReason(\n                            reason=f\"Max attempts reached (3), final score: {score}\",\n                            confidence=0.6,\n                            evidence={\"score\": score, \"attempts\": attempt, \"borderline\": True},\n                            guideline=\"max_attempts_fallback\"\n                        )\n                        \n                        await self.state_machine.transition_lead_state(\n                            lead_id,\n                            final_state,\n                            reason\n                        )\n                        \n                        decision_log.append({\n                            \"step\": \"final_decision\",\n                            \"decision\": final_state,\n                            \"reason\": \"max_attempts_reached\",\n                            \"timestamp\": datetime.now(timezone.utc).isoformat()\n                        })\n                        \n                        return True, final_state, [], lead_id, decision_log\n                    \n                    else:\n                        # Ask more questions\n                        reason = DecisionReason(\n                            reason=f\"Borderline score ({score}), requesting more information\",\n                            confidence=0.7,\n                            evidence={\"score\": score, \"attempt\": attempt, \"threshold_range\": \"40-60\"},\n                            guideline=action_result['guideline']\n                        )\n                        \n                        await self.state_machine.transition_lead_state(\n                            lead_id,\n                            LeadQualificationState.AWAITING_INFO,\n                            reason\n                        )\n                        \n                        new_attempt = attempt + 1\n                        questions = await self._generate_questions_with_reasoning(\n                            user_id,\n                            email_content,\n                            thread_context,\n                            questions_asked,\n                            new_attempt\n                        )\n                        \n                        await self._increment_attempt(lead_id, new_attempt, questions)\n                        \n                        decision_log.append({\n                            \"step\": \"request_more_info\",\n                            \"decision\": \"awaiting_info\",\n                            \"questions_generated\": len(questions),\n                            \"attempt\": new_attempt,\n                            \"timestamp\": datetime.now(timezone.utc).isoformat()\n                        })\n                        \n                        return False, LeadQualificationState.AWAITING_INFO, questions, lead_id, decision_log\n        \n        except Exception as e:\n            logger.error(f\"Error in enhanced lead qualification: {e}\")\n            decision_log.append({\n                \"step\": \"error\",\n                \"error\": str(e),\n                \"timestamp\": datetime.now(timezone.utc).isoformat()\n            })\n            return True, LeadQualificationState.NEW, [], None, decision_log\n    \n    def _build_qualification_context(self, lead: Dict, answers: Dict) -> Dict:\n        \"\"\"Build context for guideline matching\"\"\"\n        return {\n            \"qualification_score\": lead.get('qualification_score', 0),\n            \"qualification_attempt\": lead.get('qualification_attempt', 0),\n            \"company_size\": answers.get('company_size', 0),\n            \"budget\": answers.get('budget', 0),\n            \"timeline\": answers.get('timeline', ''),\n            \"stage\": lead.get('stage', 'new'),\n            \"answers_provided\": len(answers) > 0\n        }\n    \n    async def _find_existing_lead(self, user_id: str, from_email: str) -> Optional[Dict]:\n        \"\"\"Find existing lead by email\"\"\"\n        return await self.db.inbound_leads.find_one({\n            \"user_id\": user_id,\n            \"lead_email\": from_email,\n            \"is_active\": True\n        })\n    \n    async def _create_lead_with_state(self, user_id: str, from_email: str, email_id: str, intent_doc: Optional[Dict]) -> str:\n        \"\"\"Create new lead with initial state\"\"\"\n        from models.inbound_lead import InboundLead\n        import uuid\n        \n        lead_id = str(uuid.uuid4())\n        lead = InboundLead(\n            id=lead_id,\n            user_id=user_id,\n            lead_email=from_email,\n            stage=LeadQualificationState.NEW,\n            qualification_attempt=0,\n            source=\"email\",\n            source_email_id=email_id,\n            qualification_history=[],\n            last_questions_asked=[]\n        )\n        \n        await self.db.inbound_leads.insert_one(lead.model_dump())\n        logger.info(f\"✓ Created lead {lead_id} with state tracking\")\n        \n        return lead_id\n    \n    async def _generate_questions_with_reasoning(self, user_id: str, email_content: str, thread_context: List[Dict], previous_questions: List[Dict], attempt: int) -> List[Dict]:\n        \"\"\"Generate questions with explicit reasoning\"\"\"\n        # Use existing nurturing service logic\n        from services.lead_nurturing_service import LeadNurturingService\n        nurturing_service = LeadNurturingService(self.db)\n        \n        questions = await nurturing_service.generate_nurturing_questions(\n            user_id,\n            email_content,\n            thread_context,\n            previous_questions\n        )\n        \n        logger.info(f\"✓ Generated {len(questions)} questions for attempt {attempt}\")\n        return questions\n    \n    async def _store_answers(self, lead_id: str, answers: Dict, questions_asked: List[Dict]):\n        \"\"\"Store extracted answers\"\"\"\n        await self.db.inbound_leads.update_one(\n            {\"id\": lead_id},\n            {\n                \"$set\": {\n                    \"last_answers_extracted\": answers,\n                    \"updated_at\": datetime.now(timezone.utc).isoformat()\n                }\n            }\n        )\n    \n    async def _update_lead_score(self, lead_id: str, score: float, reasons: List[str]):\n        \"\"\"Update lead qualification score\"\"\"\n        await self.db.inbound_leads.update_one(\n            {\"id\": lead_id},\n            {\n                \"$set\": {\n                    \"qualification_score\": score,\n                    \"qualification_reasons\": reasons,\n                    \"updated_at\": datetime.now(timezone.utc).isoformat()\n                }\n            }\n        )\n    \n    async def _increment_attempt(self, lead_id: str, attempt: int, questions: List[Dict]):\n        \"\"\"Increment qualification attempt counter\"\"\"\n        await self.db.inbound_leads.update_one(\n            {\"id\": lead_id},\n            {\n                \"$set\": {\n                    \"qualification_attempt\": attempt,\n                    \"last_questions_asked\": questions,\n                    \"updated_at\": datetime.now(timezone.utc).isoformat()\n                }\n            }\n        )\n