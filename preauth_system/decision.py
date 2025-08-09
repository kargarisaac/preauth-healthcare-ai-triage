"""
Deterministic Decision Engine for Prior Authorization
==================================================

This module implements deterministic decision mapping that combines policy evaluation
results with safety checks to produce final authorization decisions. It supports
hybrid mode integration with agent results and provides explicit rationale.

Key Features:
- Deterministic decision mapping: policy checklist + safety → APPROVE/DENY/REVIEW
- Final decision synthesis with rationale and conditions
- Integration with agent results for hybrid mode
- Cost and confidence scoring
- Audit trail for decision transparency
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

from preauth_system.state import PreAuthState, FinalDecision, AgentResult, get_all_agent_results
from preauth_system.policy.rules_engine import PolicyEvaluation, CriterionStatus


class DecisionType(Enum):
    """Final authorization decision types."""
    APPROVED = "APPROVED"
    DENIED = "DENIED" 
    REQUIRES_REVIEW = "REQUIRES_REVIEW"


class SafetyLevel(Enum):
    """Safety assessment levels."""
    LOW = "low"
    MODERATE = "moderate" 
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SafetyAssessment:
    """Safety evaluation result."""
    level: SafetyLevel
    flags: List[str]
    contraindications: List[str]
    warnings: List[str]
    rationale: str


@dataclass
class DecisionContext:
    """Context data for decision making."""
    policy_evaluation: Optional[PolicyEvaluation]
    safety_assessment: SafetyAssessment
    agent_results: Dict[str, AgentResult]
    eligibility_status: str = "eligible"
    cost_estimate: float = 0.0
    alternative_options: List[str] = None
    
    def __post_init__(self):
        if self.alternative_options is None:
            self.alternative_options = []


class DecisionEngine:
    """Main deterministic decision engine."""
    
    def __init__(self):
        """Initialize the decision engine with configuration."""
        self.decision_matrix = self._load_decision_matrix()
        self.safety_thresholds = self._load_safety_thresholds()
        self.cost_thresholds = self._load_cost_thresholds()
    
    def make_decision(
        self,
        context: DecisionContext,
        hybrid_mode: bool = True
    ) -> FinalDecision:
        """
        Make final authorization decision based on context.
        
        Args:
            context: Decision context with policy, safety, and agent results
            hybrid_mode: Whether to incorporate agent results
            
        Returns:
            FinalDecision with rationale and conditions
        """
        try:
            # Step 1: Check for immediate denial conditions
            denial_result = self._check_denial_conditions(context)
            if denial_result:
                return denial_result
            
            # Step 2: Check for immediate approval conditions
            approval_result = self._check_approval_conditions(context, hybrid_mode)
            if approval_result:
                return approval_result
            
            # Step 3: Default to review for uncertain/incomplete cases
            return self._generate_review_decision(context, hybrid_mode)
            
        except Exception as e:
            # Fail-safe: default to review with error context
            return FinalDecision(
                decision=DecisionType.REQUIRES_REVIEW.value,
                confidence=0.0,
                authorization_number=None,
                valid_days=None,
                conditions=[f"Decision engine error: {str(e)}"],
                rationale=f"System error occurred during decision processing: {str(e)}",
                agent_based=hybrid_mode
            )
    
    def _check_denial_conditions(self, context: DecisionContext) -> Optional[FinalDecision]:
        """Check for conditions that warrant immediate denial."""
        denial_reasons = []
        
        # Critical safety contraindications
        if context.safety_assessment.level == SafetyLevel.CRITICAL:
            denial_reasons.extend(context.safety_assessment.contraindications)
        
        # Policy-based denials
        if context.policy_evaluation:
            policy = context.policy_evaluation
            
            # Check for explicit denial conditions from policy
            if hasattr(policy, 'decision_matrix') and 'deny_conditions' in policy.decision_matrix:
                # This would require policy to expose decision matrix
                pass
            
            # Hard denial conditions
            required_unmet = [
                r for r in policy.criteria_results 
                if r.required and r.status == CriterionStatus.UNMET
            ]
            
            if required_unmet:
                critical_unmet = [r.description for r in required_unmet[:3]]  # Top 3
                denial_reasons.append(f"Critical required criteria unmet: {', '.join(critical_unmet)}")
        
        # Eligibility-based denial
        if context.eligibility_status == "ineligible":
            denial_reasons.append("Patient not eligible for coverage")
        
        # Agent-based critical concerns (hybrid mode)
        for agent_name, result in context.agent_results.items():
            if result.success and "CRITICAL" in result.response.upper():
                denial_reasons.append(f"{agent_name}: Critical safety concern identified")
        
        if denial_reasons:
            return FinalDecision(
                decision=DecisionType.DENIED.value,
                confidence=0.9,  # High confidence in denial
                authorization_number=None,
                valid_days=None,
                conditions=denial_reasons,
                rationale=f"Authorization denied due to: {'; '.join(denial_reasons)}",
                agent_based=len(context.agent_results) > 0
            )
        
        return None
    
    def _check_approval_conditions(
        self,
        context: DecisionContext, 
        hybrid_mode: bool
    ) -> Optional[FinalDecision]:
        """Check for conditions that warrant immediate approval."""
        
        # Must have acceptable safety level
        if context.safety_assessment.level in [SafetyLevel.HIGH, SafetyLevel.CRITICAL]:
            return None
        
        # Policy-based approval
        if context.policy_evaluation:
            policy = context.policy_evaluation
            
            # All required criteria must be met
            if not policy.required_criteria_met:
                return None
            
            # High policy score threshold (more permissive if all required criteria met)
            if policy.overall_score < 0.7:  # 70% threshold
                return None
            
            # No significant missing documentation
            if len(policy.missing_documentation) > 2:
                return None
        else:
            # No applicable policy - cannot approve without policy guidance
            return None
        
        # Agent consensus check (hybrid mode)
        if hybrid_mode and context.agent_results:
            agent_approvals = 0
            agent_concerns = 0
            
            for agent_name, result in context.agent_results.items():
                if result.success and result.response:
                    response_upper = result.response.upper()
                    if "APPROVE" in response_upper or "RECOMMEND" in response_upper:
                        agent_approvals += 1
                    elif "DENY" in response_upper or "CONCERN" in response_upper:
                        agent_concerns += 1
            
            # Require agent consensus for hybrid approval
            if len(context.agent_results) >= 2:  # At least 2 agents
                if agent_concerns > agent_approvals:
                    return None  # Agents have concerns, don't approve
        
        # Generate approval decision
        conditions = []
        
        # Add safety warnings as conditions
        if context.safety_assessment.warnings:
            conditions.extend([f"Monitor: {w}" for w in context.safety_assessment.warnings[:2]])
        
        # Add policy-based conditions
        if context.policy_evaluation:
            # Standard monitoring requirements
            if "diabetes" in context.policy_evaluation.policy_id.lower():
                conditions.extend([
                    "Quarterly endocrinology follow-up required",
                    "Annual HbA1c and complications screening required"
                ])
            elif "osteoarthritis" in context.policy_evaluation.policy_id.lower():
                conditions.extend([
                    "6-week post-procedure follow-up required",
                    "Functional assessment at 3 months required"
                ])
        
        # Determine authorization validity period
        valid_days = self._calculate_validity_period(context)
        
        # Generate authorization number
        auth_number = self._generate_authorization_number(context)
        
        return FinalDecision(
            decision=DecisionType.APPROVED.value,
            confidence=0.85,  # High confidence
            authorization_number=auth_number,
            valid_days=valid_days,
            conditions=conditions,
            rationale=self._generate_approval_rationale(context),
            agent_based=hybrid_mode and len(context.agent_results) > 0
        )
    
    def _generate_review_decision(
        self,
        context: DecisionContext,
        hybrid_mode: bool
    ) -> FinalDecision:
        """Generate review decision for uncertain/incomplete cases."""
        
        review_reasons = []
        next_steps = []
        
        # Policy-based review reasons
        if context.policy_evaluation:
            policy = context.policy_evaluation
            
            # Missing documentation
            if policy.missing_documentation:
                review_reasons.append("Missing required documentation")
                next_steps.extend(policy.missing_documentation[:3])  # Top 3
            
            # Uncertain criteria
            uncertain_criteria = [
                r for r in policy.criteria_results 
                if r.status == CriterionStatus.UNCERTAIN
            ]
            if uncertain_criteria:
                review_reasons.append(f"{len(uncertain_criteria)} criteria require clarification")
                for criterion in uncertain_criteria[:2]:  # Top 2
                    next_steps.append(f"Clarify: {criterion.description}")
            
            # Borderline policy score
            if 0.5 <= policy.overall_score < 0.8:
                review_reasons.append("Borderline policy compliance")
        
        # Safety-based review
        if context.safety_assessment.level == SafetyLevel.HIGH:
            review_reasons.append("High safety risk requires medical director review")
            next_steps.extend(context.safety_assessment.warnings[:2])
        
        # Agent-based review reasons (hybrid mode)
        if hybrid_mode and context.agent_results:
            conflicting_opinions = False
            agent_review_requests = []
            
            for agent_name, result in context.agent_results.items():
                if result.success and result.response:
                    if "REVIEW" in result.response.upper():
                        agent_review_requests.append(agent_name)
                    elif "CONFLICTING" in result.response.upper():
                        conflicting_opinions = True
            
            if agent_review_requests:
                review_reasons.append(f"Agent analysis recommends review ({len(agent_review_requests)} agents)")
            
            if conflicting_opinions:
                review_reasons.append("Conflicting clinical assessments require review")
        
        # Default review reason if none identified
        if not review_reasons:
            review_reasons.append("Case requires medical director review")
            next_steps.append("Clinical documentation review required")
        
        return FinalDecision(
            decision=DecisionType.REQUIRES_REVIEW.value,
            confidence=0.6,  # Moderate confidence in review need
            authorization_number=None,
            valid_days=None,
            conditions=next_steps,
            rationale=f"Medical director review required: {'; '.join(review_reasons)}",
            agent_based=hybrid_mode and len(context.agent_results) > 0
        )
    
    def _calculate_validity_period(self, context: DecisionContext) -> int:
        """Calculate authorization validity period in days."""
        if not context.policy_evaluation:
            return 90  # Default 3 months
        
        policy_id = context.policy_evaluation.policy_id.lower()
        
        if "diabetes" in policy_id:
            return 365  # 1 year for diabetes technology
        elif "osteoarthritis" in policy_id:
            return 90   # 3 months for procedures
        elif "parkinsons" in policy_id:
            return 180  # 6 months for DBS evaluation
        else:
            return 90   # Default
    
    def _generate_authorization_number(self, context: DecisionContext) -> str:
        """Generate unique authorization number."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        policy_prefix = "GEN"
        
        if context.policy_evaluation:
            policy_id = context.policy_evaluation.policy_id.upper()
            if "DIABETES" in policy_id:
                policy_prefix = "DIA"
            elif "OSTEOARTHRITIS" in policy_id:
                policy_prefix = "ORT"
            elif "PARKINSONS" in policy_id:
                policy_prefix = "NEU"
        
        return f"UAE{policy_prefix}{timestamp}"
    
    def _generate_approval_rationale(self, context: DecisionContext) -> str:
        """Generate detailed approval rationale."""
        rationale_parts = []
        
        if context.policy_evaluation:
            policy = context.policy_evaluation
            rationale_parts.append(
                f"Policy {policy.policy_id} criteria met "
                f"({policy.met_criteria_count}/{len(policy.criteria_results)} criteria)"
            )
            
            if policy.overall_score >= 0.9:
                rationale_parts.append("Excellent policy compliance")
            elif policy.overall_score >= 0.8:
                rationale_parts.append("Good policy compliance")
        
        if context.safety_assessment.level == SafetyLevel.LOW:
            rationale_parts.append("Low safety risk profile")
        elif context.safety_assessment.level == SafetyLevel.MODERATE:
            rationale_parts.append("Acceptable safety risk with monitoring")
        
        if context.agent_results:
            supporting_agents = sum(
                1 for result in context.agent_results.values()
                if result.success and "APPROVE" in result.response.upper()
            )
            if supporting_agents > 0:
                rationale_parts.append(f"Clinical analysis supports approval ({supporting_agents} agents)")
        
        return "Authorization approved: " + "; ".join(rationale_parts)
    
    def _load_decision_matrix(self) -> Dict[str, Any]:
        """Load decision matrix configuration."""
        return {
            "approval_thresholds": {
                "policy_score_min": 0.8,
                "safety_level_max": "moderate",
                "required_criteria_met": True
            },
            "denial_thresholds": {
                "safety_level_min": "critical",
                "required_unmet_max": 0
            }
        }
    
    def _load_safety_thresholds(self) -> Dict[str, Any]:
        """Load safety assessment thresholds."""
        return {
            "eGFR_threshold": 30,  # ml/min/1.73m2
            "age_high_risk": 75,
            "contraindication_keywords": [
                "allergy", "contraindication", "intolerance"
            ]
        }
    
    def _load_cost_thresholds(self) -> Dict[str, Any]:
        """Load cost consideration thresholds."""
        return {
            "high_cost_threshold_aed": 10000,  # ~$2,700 USD
            "cost_effectiveness_required": True
        }


def create_decision_context(
    state: PreAuthState,
    policy_evaluation: Optional[PolicyEvaluation],
    safety_assessment: SafetyAssessment
) -> DecisionContext:
    """
    Create decision context from workflow state.
    
    Args:
        state: Current workflow state
        policy_evaluation: Policy evaluation result
        safety_assessment: Safety assessment result
        
    Returns:
        DecisionContext for decision making
    """
    agent_results = get_all_agent_results(state)
    
    # Determine eligibility based on policy and safety
    eligibility_status = "eligible"
    if policy_evaluation and policy_evaluation.overall_score < 50:
        eligibility_status = "ineligible"
    elif safety_assessment and str(safety_assessment.overall_risk_level) == "HIGH":
        eligibility_status = "conditional"
    
    # Estimate cost based on services requested
    cost_estimate = _estimate_service_cost(state)
    
    # Identify alternative options if primary request has issues
    alternative_options = _identify_alternatives(policy_evaluation, safety_assessment)
    
    return DecisionContext(
        policy_evaluation=policy_evaluation,
        safety_assessment=safety_assessment,
        agent_results=agent_results,
        eligibility_status=eligibility_status,
        cost_estimate=cost_estimate,
        alternative_options=alternative_options
    )


def _estimate_service_cost(state: PreAuthState) -> float:
    """Estimate cost of requested services."""
    if not state.get('canonical_request'):
        return 0.0
    
    canonical_request = state['canonical_request']
    total_cost = 0.0
    
    # Simple cost estimation based on service types
    cost_table = {
        'imaging': 500.0,  # AED
        'procedure': 2000.0,  # AED  
        'consultation': 300.0,  # AED
        'medication': 100.0,  # AED
        'laboratory': 200.0  # AED
    }
    
    for service in canonical_request.services:
        service_type = service.get('activity_code', {}).get('code', '').lower()
        if 'mri' in service_type or 'ct' in service_type or 'scan' in service_type:
            total_cost += cost_table.get('imaging', 500.0)
        elif 'procedure' in service_type or 'surgery' in service_type:
            total_cost += cost_table.get('procedure', 2000.0)
        elif 'consult' in service_type:
            total_cost += cost_table.get('consultation', 300.0)
        elif 'lab' in service_type:
            total_cost += cost_table.get('laboratory', 200.0)
        else:
            total_cost += 100.0  # Default cost
    
    return total_cost


def _identify_alternatives(policy_evaluation, safety_assessment) -> List[str]:
    """Identify alternative treatment options if primary request has issues."""
    alternatives = []
    
    if policy_evaluation and policy_evaluation.overall_score < 70:
        alternatives.append("Step therapy - try less expensive medication first")
        alternatives.append("Generic alternative available")
    
    if safety_assessment and safety_assessment.total_alerts > 0:
        alternatives.append("Lower dose regimen")
        alternatives.append("Alternative medication with better safety profile")
    
    return alternatives


def make_authorization_decision(
    state: PreAuthState,
    policy_evaluation: Optional[PolicyEvaluation],
    safety_assessment: SafetyAssessment,
    hybrid_mode: bool = True
) -> FinalDecision:
    """
    Main entry point for making authorization decisions.
    
    Args:
        state: Current workflow state
        policy_evaluation: Policy evaluation result
        safety_assessment: Safety assessment result
        hybrid_mode: Whether to use agent results
        
    Returns:
        FinalDecision with complete rationale
    """
    engine = DecisionEngine()
    context = create_decision_context(state, policy_evaluation, safety_assessment)
    
    return engine.make_decision(context, hybrid_mode)


if __name__ == "__main__":
    # Example usage and testing
    from preauth_system.state import create_initial_state
    
    # Create test safety assessment
    test_safety = SafetyAssessment(
        level=SafetyLevel.LOW,
        flags=[],
        contraindications=[],
        warnings=[],
        rationale="No safety concerns identified"
    )
    
    # Create test state
    test_state = create_initial_state(
        xml_file_path="/test/path.xml",
        xml_format="eclaim"
    )
    
    # Make decision
    decision = make_authorization_decision(
        state=test_state,
        policy_evaluation=None,
        safety_assessment=test_safety,
        hybrid_mode=False
    )
    
    print(f"Decision: {decision.decision}")
    print(f"Confidence: {decision.confidence}")
    print(f"Rationale: {decision.rationale}")