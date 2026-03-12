"""
Agent Guidelines - Parlant.io-inspired condition-action rules
Provides declarative guidelines for decision making
"""
import logging
from typing import Dict, List, Optional, Callable
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class Guideline:
    """
    A single guideline with condition and action
    
    Guidelines are declarative rules that determine agent behavior:
    - Condition: When does this guideline apply?
    - Action: What should the agent do?
    - Priority: Which guideline wins if multiple match?
    - Tools: What tools are authorized for this action?
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        condition: Callable,
        action: str,
        priority: int = 1,
        tools: List[str] = None,
        confidence_threshold: float = 0.7
    ):
        self.name = name
        self.description = description
        self.condition = condition
        self.action = action
        self.priority = priority
        self.tools = tools or []
        self.confidence_threshold = confidence_threshold
        self.created_at = datetime.now(timezone.utc).isoformat()
    
    async def matches(self, context: Dict) -> bool:
        """
        Check if this guideline's condition matches the current context
        
        Args:
            context: Current conversation state and metadata
        
        Returns:
            True if condition matches
        """
        try:
            return await self.condition(context)
        except Exception as e:
            logger.error(f"Error evaluating guideline {self.name}: {e}")
            return False
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "action": self.action,
            "priority": self.priority,
            "tools": self.tools,
            "confidence_threshold": self.confidence_threshold
        }


class GuidelineEngine:
    """
    Engine for matching and applying guidelines
    
    Key features:
    - Dynamic guideline matching based on context
    - Priority-based selection when multiple guidelines match
    - Tool authorization through guideline matching
    - Audit trail of which guidelines were applied
    """
    
    def __init__(self):
        self.guidelines: List[Guideline] = []
        self._initialize_default_guidelines()
    
    def _initialize_default_guidelines(self):
        """
        Initialize default guidelines for email automation
        
        These can be customized per user/organization
        """
        
        # Intent Classification Guidelines
        self.add_guideline(Guideline(
            name="classify_meeting_request",
            description="Classify emails with meeting-related keywords",
            condition=lambda ctx: any(kw in ctx.get("email_text", "").lower() 
                                     for kw in ["meeting", "schedule", "call", "zoom", "meet"]),
            action="classify_as_meeting_request",
            priority=10,
            tools=["calendar_tool", "meeting_detection"],
            confidence_threshold=0.8
        ))
        
        self.add_guideline(Guideline(
            name="classify_pricing_inquiry",
            description="Classify emails asking about pricing or cost",
            condition=lambda ctx: any(kw in ctx.get("email_text", "").lower() 
                                     for kw in ["price", "pricing", "cost", "quote", "budget"]),
            action="classify_as_pricing_inquiry",
            priority=9,
            tools=["lead_qualification", "draft_generator"],
            confidence_threshold=0.9
        ))
        
        self.add_guideline(Guideline(
            name="classify_demo_request",
            description="Classify emails requesting product demo",
            condition=lambda ctx: any(kw in ctx.get("email_text", "").lower() 
                                     for kw in ["demo", "trial", "test", "preview", "show me"]),
            action="classify_as_demo_request",
            priority=9,
            tools=["lead_qualification", "calendar_tool", "draft_generator"],
            confidence_threshold=0.9
        ))
        
        # Lead Qualification Guidelines
        self.add_guideline(Guideline(
            name="qualify_high_value_lead",
            description="Qualify leads with high budget and company size",
            condition=lambda ctx: (
                ctx.get("qualification_score", 0) >= 60 and
                ctx.get("company_size", 0) >= 50
            ),
            action="mark_as_qualified",
            priority=10,
            tools=["crm_integration", "notification"],
            confidence_threshold=0.8
        ))
        
        self.add_guideline(Guideline(
            name="request_more_info",
            description="Request additional information for borderline leads",
            condition=lambda ctx: (
                40 <= ctx.get("qualification_score", 0) < 60 and
                ctx.get("qualification_attempt", 0) < 3
            ),
            action="ask_qualification_questions",
            priority=8,
            tools=["draft_generator"],
            confidence_threshold=0.7
        ))
        
        self.add_guideline(Guideline(
            name="disqualify_low_score",
            description="Disqualify leads with low scores after multiple attempts",
            condition=lambda ctx: (
                ctx.get("qualification_score", 0) < 40 or
                (ctx.get("qualification_score", 0) < 50 and ctx.get("qualification_attempt", 0) >= 3)
            ),
            action="mark_as_unqualified",
            priority=8,
            tools=[],
            confidence_threshold=0.8
        ))
        
        # Auto-send Guidelines
        self.add_guideline(Guideline(
            name="auto_send_validated_draft",
            description="Auto-send drafts that pass validation when intent allows",
            condition=lambda ctx: (
                ctx.get("draft_validated", False) and
                ctx.get("intent_auto_send", False) and
                ctx.get("validation_confidence", 0) >= 0.8
            ),
            action="send_email_automatically",
            priority=10,
            tools=["email_sender", "follow_up_scheduler"],
            confidence_threshold=0.9
        ))
        
        self.add_guideline(Guideline(
            name="escalate_failed_validation",
            description="Escalate drafts that fail validation after retries",
            condition=lambda ctx: (
                not ctx.get("draft_validated", False) and
                ctx.get("retry_count", 0) >= 2
            ),
            action="escalate_to_human",
            priority=10,
            tools=["notification"],
            confidence_threshold=1.0
        ))
    
    def add_guideline(self, guideline: Guideline):
        """Add a guideline to the engine"""
        self.guidelines.append(guideline)
        self.guidelines.sort(key=lambda g: g.priority, reverse=True)
    
    async def match_guidelines(self, context: Dict) -> List[Guideline]:
        """
        Find all guidelines that match the current context
        
        Args:
            context: Current conversation state and metadata
        
        Returns:
            List of matching guidelines, sorted by priority
        """
        matching = []
        
        for guideline in self.guidelines:
            if await guideline.matches(context):
                matching.append(guideline)
                logger.info(f"✓ Guideline matched: {guideline.name} (priority: {guideline.priority})")
        
        return matching
    
    async def get_best_action(self, context: Dict) -> Optional[Dict]:
        """
        Get the best action to take based on matching guidelines
        
        Returns:
            Dict with action details, authorized tools, and guideline info
        """
        matching = await self.match_guidelines(context)
        
        if not matching:
            logger.warning("No guidelines matched for current context")
            return None
        
        # Best guideline is first (highest priority)
        best = matching[0]
        
        return {
            "action": best.action,
            "guideline": best.name,
            "priority": best.priority,
            "tools": best.tools,
            "confidence_threshold": best.confidence_threshold,
            "description": best.description,
            "alternatives": [g.name for g in matching[1:]]  # Other matching guidelines
        }
    
    def is_tool_authorized(self, tool_name: str, guideline_name: str) -> bool:
        """
        Check if a tool is authorized by the current guideline
        
        This provides deterministic tool invocation:
        Tools only execute when authorized by a matched guideline
        
        Args:
            tool_name: Name of the tool to check
            guideline_name: Name of the matched guideline
        
        Returns:
            True if tool is authorized
        """
        guideline = next((g for g in self.guidelines if g.name == guideline_name), None)
        
        if not guideline:
            logger.warning(f"Guideline {guideline_name} not found")
            return False
        
        authorized = tool_name in guideline.tools
        
        if not authorized:
            logger.warning(f"Tool {tool_name} not authorized by guideline {guideline_name}")
        
        return authorized
