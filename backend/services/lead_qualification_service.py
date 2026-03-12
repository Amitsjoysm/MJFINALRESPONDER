"""
Lead Qualification Service
Evaluates leads against qualification criteria
"""
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class LeadQualificationService:
    """Service for evaluating lead qualification"""
    
    def __init__(self, db):
        self.db = db
        self.qualification_criteria_collection = db['lead_qualification_criteria']
    
    async def evaluate_lead_qualification(
        self,
        user_id: str,
        lead_data: Dict[str, Any],
        criteria_id: Optional[str] = None
    ) -> Tuple[bool, int, List[str]]:
        """
        Evaluate if a lead meets qualification criteria
        
        Returns:
            Tuple of (is_qualified, score, reasons)
            - score is 0-100 integer
            - is_qualified = True if score >= 60
        """
        try:
            # Get qualification criteria
            if criteria_id:
                criteria = await self.qualification_criteria_collection.find_one({
                    "id": criteria_id,
                    "user_id": user_id,
                    "is_active": True
                })
            else:
                # Get default active criteria for user
                criteria = await self.qualification_criteria_collection.find_one({
                    "user_id": user_id,
                    "is_active": True,
                    "is_enabled": True
                })
            
            if not criteria:
                logger.warning(f"No active qualification criteria found for user {user_id}")
                return True, 100, ["No criteria configured - auto-qualified"]
            
            criteria_type = criteria.get('criteria_type', 'score_based')
            
            # Evaluate based on criteria type
            if criteria_type == 'rule_based':
                return await self._evaluate_rule_based(criteria, lead_data)
            elif criteria_type == 'question_based':
                return await self._evaluate_question_based(criteria, lead_data)
            else:  # score_based or default
                return await self._evaluate_score_based(criteria, lead_data)
                
        except Exception as e:
            logger.error(f"Error evaluating lead qualification: {e}")
            # Default to qualified if error occurs
            return True, 50, [f"Error in evaluation: {str(e)}"]
    
    async def _evaluate_rule_based(
        self,
        criteria: Dict,
        lead_data: Dict
    ) -> Tuple[bool, int, List[str]]:
        """Evaluate rule-based criteria - Returns score 0-100"""
        rules = criteria.get('rules', [])
        if not rules:
            return True, 100, ["No rules configured"]
        
        passed_rules = 0
        total_weight = 0
        weighted_score = 0
        reasons = []
        
        for rule in rules:
            field = rule.get('field')
            operator = rule.get('operator')
            expected_value = rule.get('value')
            weight = rule.get('weight', 1.0)
            total_weight += weight
            
            actual_value = lead_data.get(field)
            
            passed = self._check_rule(actual_value, operator, expected_value)
            
            if passed:
                passed_rules += 1
                weighted_score += weight
                reasons.append(f"✓ {field}: {actual_value} {operator} {expected_value}")
            else:
                reasons.append(f"✗ {field}: {actual_value} {operator} {expected_value}")
        
        # Calculate final score (0-100)
        score = int((weighted_score / total_weight) * 100) if total_weight > 0 else 0
        min_score = int(criteria.get('min_qualification_score', 0.7) * 100)  # Convert 0.7 to 70
        if min_score > 1:  # Already in 0-100 range
            min_score = criteria.get('min_qualification_score', 70)
        else:
            min_score = int(criteria.get('min_qualification_score', 0.7) * 100)
        
        # Use 60 as default threshold
        min_score = min_score if min_score > 0 else 60
        is_qualified = score >= min_score
        
        return is_qualified, score, reasons
    
    async def _evaluate_question_based(
        self,
        criteria: Dict,
        lead_data: Dict
    ) -> Tuple[bool, int, List[str]]:
        """Evaluate question-based criteria - Returns score 0-100"""
        questions = criteria.get('questions', [])
        if not questions:
            return True, 100, ["No questions configured"]
        
        responses = lead_data.get('nurturing_questions_asked', [])
        response_dict = {r.get('question_key'): r.get('response') for r in responses}
        
        passed_questions = 0
        total_weight = 0
        weighted_score = 0
        reasons = []
        
        for question in questions:
            question_key = question.get('question_key')
            weight = question.get('weight', 1.0)
            is_required = question.get('is_required', True)
            qualifying_answers = question.get('qualifying_answers', [])
            disqualifying_answers = question.get('disqualifying_answers', [])
            
            total_weight += weight
            
            response = response_dict.get(question_key)
            
            if not response:
                if is_required:
                    reasons.append(f"✗ {question_key}: No response (required)")
                else:
                    reasons.append(f"⚠ {question_key}: No response (optional)")
                continue
            
            # Check if response qualifies or disqualifies
            response_lower = str(response).lower()
            
            if disqualifying_answers:
                if any(ans.lower() in response_lower for ans in disqualifying_answers):
                    reasons.append(f"✗ {question_key}: Disqualifying answer - {response}")
                    continue
            
            if qualifying_answers:
                if any(ans.lower() in response_lower for ans in qualifying_answers):
                    passed_questions += 1
                    weighted_score += weight
                    reasons.append(f"✓ {question_key}: Qualifying answer - {response}")
                else:
                    reasons.append(f"⚠ {question_key}: Neutral answer - {response}")
            else:
                # If no specific qualifying answers, any response counts
                passed_questions += 1
                weighted_score += weight
                reasons.append(f"✓ {question_key}: Answered - {response}")
        
        # Calculate final score (0-100)
        score = int((weighted_score / total_weight) * 100) if total_weight > 0 else 0
        min_score = int(criteria.get('min_qualification_score', 0.7) * 100)
        if min_score > 1:
            min_score = criteria.get('min_qualification_score', 70)
        else:
            min_score = int(criteria.get('min_qualification_score', 0.7) * 100)
        
        min_score = min_score if min_score > 0 else 60
        is_qualified = score >= min_score
        
        return is_qualified, score, reasons
    
    async def _evaluate_score_based(
        self,
        criteria: Dict,
        lead_data: Dict
    ) -> Tuple[bool, int, List[str]]:
        """Evaluate using combined scoring (rules + questions) - Returns score 0-100"""
        # Evaluate both rules and questions
        rules_qualified, rules_score, rules_reasons = await self._evaluate_rule_based(criteria, lead_data)
        questions_qualified, questions_score, questions_reasons = await self._evaluate_question_based(criteria, lead_data)
        
        # Combine scores (weighted average)
        rules = criteria.get('rules', [])
        questions = criteria.get('questions', [])
        
        if rules and questions:
            # Both exist, average them
            combined_score = int((rules_score + questions_score) / 2)
        elif rules:
            # Only rules
            combined_score = rules_score
        elif questions:
            # Only questions
            combined_score = questions_score
        else:
            # Nothing configured
            combined_score = 100
        
        # Use 60 as threshold
        is_qualified = combined_score >= 60
        
        reasons = [
            f"Combined Score: {combined_score}/100 (threshold: 60)",
            "--- Rule-based Evaluation ---",
            *rules_reasons,
            "--- Question-based Evaluation ---",
            *questions_reasons
        ]
        
        return is_qualified, combined_score, reasons
    
    def _check_rule(self, actual_value: Any, operator: str, expected_value: Any) -> bool:
        """Check if a rule passes"""
        if actual_value is None:
            return False
        
        try:
            if operator == 'equals':
                return str(actual_value).lower() == str(expected_value).lower()
            elif operator == 'not_equals':
                return str(actual_value).lower() != str(expected_value).lower()
            elif operator == 'contains':
                return str(expected_value).lower() in str(actual_value).lower()
            elif operator == 'not_contains':
                return str(expected_value).lower() not in str(actual_value).lower()
            elif operator == 'greater_than':
                return float(actual_value) > float(expected_value)
            elif operator == 'less_than':
                return float(actual_value) < float(expected_value)
            elif operator == 'in_list':
                # expected_value should be a list
                return str(actual_value).lower() in [str(v).lower() for v in expected_value]
            elif operator == 'not_in_list':
                return str(actual_value).lower() not in [str(v).lower() for v in expected_value]
            else:
                logger.warning(f"Unknown operator: {operator}")
                return False
        except Exception as e:
            logger.error(f"Error checking rule: {e}")
            return False
    
    async def should_check_qualification(
        self,
        user_id: str,
        intent_doc: Optional[Dict],
        nurturing_exchanges_count: int
    ) -> bool:
        """
        Determine if qualification should be checked now
        
        Returns True if:
        - Nurturing is complete (max exchanges reached)
        - Required questions have been answered
        """
        # Get user's settings
        users_collection = self.db['users']
        user = await users_collection.find_one({"id": user_id})
        
        if not user:
            return False
        
        # Check global setting
        global_enabled = user.get('global_lead_qualification_enabled', False)
        if not global_enabled:
            return False
        
        # Check intent-specific setting
        if intent_doc:
            intent_enabled = intent_doc.get('enable_lead_qualification', False)
            if not intent_enabled:
                return False
        
        # Get criteria to check max exchanges
        criteria_id = user.get('default_qualification_criteria_id')
        if criteria_id:
            criteria = await self.qualification_criteria_collection.find_one({
                "id": criteria_id,
                "user_id": user_id
            })
            if criteria:
                max_exchanges = criteria.get('max_exchanges', 2)
                # Check qualification if max exchanges reached
                if nurturing_exchanges_count >= max_exchanges:
                    return True
        
        # Default: check after 2 exchanges
        return nurturing_exchanges_count >= 2
