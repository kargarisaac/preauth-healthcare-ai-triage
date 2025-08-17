"""
Tests for DecisionCombiner deterministic decision logic.

Validates that the decision synthesis in pipeline_module.py:
1. Returns deterministic results (same inputs → same outputs)
2. Correctly applies all decision rules (APPROVE/DENY/REVIEW)
3. Generates complete audit trails
4. Tracks timing and cost data accurately
5. Handles edge cases and error conditions
"""
import time
import pytest
from datetime import datetime, timezone
from typing import Dict, Any, List

from preauth_system.pipeline_module import PreAuthPipeline
from preauth_system.signatures import DecisionOutcome, ReasonCode


class TestDecisionCombiner:
    """Test suite for DecisionCombiner deterministic behavior."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.pipeline = PreAuthPipeline(configure_default_lm=False)
    
    def _create_test_checklist(
        self,
        criteria: List[Dict[str, Any]] = None,
        missing_documents: List[str] = None,
        compliance_score: float = 0.8,
        policy_source: str = "test_policy"
    ) -> Dict[str, Any]:
        """Create test checklist data with specified parameters."""
        default_criteria = [
            {
                "id": "test_criterion_1",
                "description": "Test diagnosis criterion",
                "status": "met",
                "rationale": "Patient has confirmed diagnosis",
                "citations": ["test_policy.yaml"],
                "missing_documentation": None
            }
        ]
        
        return {
            "criteria": criteria or default_criteria,
            "missing_documents": missing_documents or [],
            "overall_compliance_score": compliance_score,
            "policy_source": policy_source
        }

    def test_approve_decision_path(self):
        """Test APPROVE decision when all criteria are met."""
        # Create checklist with all criteria met
        checklist = self._create_test_checklist(
            criteria=[
                {
                    "id": "eligibility_criterion",
                    "description": "Patient eligibility confirmed",
                    "status": "met",
                    "rationale": "All eligibility requirements satisfied",
                    "citations": ["policy.yaml"],
                    "missing_documentation": None
                },
                {
                    "id": "clinical_criterion",
                    "description": "Clinical appropriateness established",
                    "status": "met",
                    "rationale": "Treatment clinically appropriate",
                    "citations": ["guidelines.md"],
                    "missing_documentation": None
                }
            ],
            compliance_score=0.9,
            missing_documents=[]
        )
        
        # Execute decision synthesis twice to verify determinism
        decision1, timing1 = self.pipeline._synthesize_decision(checklist)
        decision2, timing2 = self.pipeline._synthesize_decision(checklist)
        
        # Verify deterministic APPROVE outcome
        assert decision1["outcome"] == DecisionOutcome.APPROVE.value
        assert decision2["outcome"] == DecisionOutcome.APPROVE.value
        assert decision1["outcome"] == decision2["outcome"]
        
        # Verify confidence is 100% for deterministic decisions
        assert decision1["confidence"] == 1.0
        assert decision2["confidence"] == 1.0
        
        # Verify rationale includes compliance score
        assert "90.0%" in decision1["rationale"]
        assert "All criteria satisfied" in decision1["rationale"]
        
        # Verify conditions are added for approval
        assert len(decision1["conditions"]) > 0
        assert any("policy terms" in condition.lower() for condition in decision1["conditions"])
        
        # Verify criteria summary
        criteria_summary = decision1["criteria_summary"]
        assert len(criteria_summary["met"]) == 2
        assert len(criteria_summary["unmet"]) == 0
        assert len(criteria_summary["uncertain"]) == 0
        
        # Verify audit trail completeness
        audit_trail = decision1["audit_trail"]
        assert audit_trail["decision_method"] == "deterministic_rules"
        assert audit_trail["reproducible"] is True
        assert audit_trail["input_criteria_count"] == 2
        
        # Verify timing data
        assert "decision_criteria_analysis_ms" in timing1
        assert "decision_rule_evaluation_ms" in timing1
        assert "decision_audit_generation_ms" in timing1
        assert all(t >= 0 for t in timing1.values())

    def test_deny_explicit_exclusion_path(self):
        """Test DENY decision for explicit exclusion criteria."""
        checklist = self._create_test_checklist(
            criteria=[
                {
                    "id": "exclusion_criterion",
                    "description": "Treatment is contraindicated for this condition",
                    "status": "unmet",
                    "rationale": "Patient has contraindication - treatment not covered",
                    "citations": ["exclusion_policy.yaml"],
                    "missing_documentation": None
                }
            ],
            compliance_score=0.2
        )
        
        decision, timing = self.pipeline._synthesize_decision(checklist)
        
        # Verify DENY outcome
        assert decision["outcome"] == DecisionOutcome.DENY.value
        
        # Verify explicit exclusion reason code
        assert ReasonCode.EXPLICIT_EXCLUSION.value in decision["reason_codes"]
        
        # Verify rationale mentions exclusion
        assert "exclusion criteria present" in decision["rationale"].lower()
        assert "exclusion_criterion" in decision["rationale"]
        
        # Verify criteria categorization
        criteria_summary = decision["criteria_summary"]
        assert len(criteria_summary["explicit_exclusions"]) == 1
        assert "exclusion_criterion" in criteria_summary["explicit_exclusions"]
        
        # Verify audit trail shows Rule 1 applied
        audit_trail = decision["audit_trail"]
        assert "Rule 1: DENY for explicit exclusions" in audit_trail["decision_logic_applied"]

    def test_deny_safety_contraindication_path(self):
        """Test DENY decision for safety contraindications."""
        checklist = self._create_test_checklist(
            criteria=[
                {
                    "id": "safety_check",
                    "description": "Safety assessment for drug interactions",
                    "status": "unmet",
                    "rationale": "Patient has adverse reaction risk - safety contraindication",
                    "citations": ["safety_guidelines.md"],
                    "missing_documentation": None
                }
            ]
        )
        
        decision, timing = self.pipeline._synthesize_decision(checklist)
        
        # Verify DENY outcome with safety reason
        assert decision["outcome"] == DecisionOutcome.DENY.value
        assert ReasonCode.SAFETY_CONTRAINDICATION.value in decision["reason_codes"]
        
        # Verify safety blocks identified
        criteria_summary = decision["criteria_summary"]
        assert len(criteria_summary["safety_blocks"]) == 1
        assert "safety_check" in criteria_summary["safety_blocks"]
        
        # Verify audit trail
        audit_trail = decision["audit_trail"]
        assert "Rule 1: DENY for safety contraindications" in audit_trail["decision_logic_applied"]

    def test_deny_mandatory_criteria_unmet_path(self):
        """Test DENY decision for unmet mandatory criteria."""
        checklist = self._create_test_checklist(
            criteria=[
                {
                    "id": "mandatory_diagnosis",
                    "description": "Required diagnosis confirmation",
                    "status": "unmet",
                    "rationale": "Diagnosis not confirmed in medical records",
                    "citations": ["diagnostic_policy.yaml"],
                    "missing_documentation": None
                }
            ]
        )
        
        decision, timing = self.pipeline._synthesize_decision(checklist)
        
        # Verify DENY outcome
        assert decision["outcome"] == DecisionOutcome.DENY.value
        assert ReasonCode.MANDATORY_CRITERIA_UNMET.value in decision["reason_codes"]
        
        # Verify mandatory criteria identified
        criteria_summary = decision["criteria_summary"]
        assert len(criteria_summary["mandatory_unmet"]) == 1
        assert "mandatory_diagnosis" in criteria_summary["mandatory_unmet"]
        
        # Verify audit trail
        audit_trail = decision["audit_trail"]
        assert "Rule 2: DENY for unmet mandatory criteria" in audit_trail["decision_logic_applied"]

    def test_review_missing_documentation_path(self):
        """Test REVIEW decision for missing critical documentation."""
        checklist = self._create_test_checklist(
            missing_documents=[
                "Laboratory results",
                "Specialist consultation report",
                "Medical imaging studies",
                "Patient consent form"  # 4 missing docs > threshold of 3
            ],
            compliance_score=0.6
        )
        
        decision, timing = self.pipeline._synthesize_decision(checklist)
        
        # Verify REVIEW outcome
        assert decision["outcome"] == DecisionOutcome.REVIEW.value
        assert ReasonCode.MISSING_REQUIRED_DOCUMENTATION.value in decision["reason_codes"]
        
        # Verify rationale mentions missing documents
        assert "Critical documentation missing" in decision["rationale"]
        assert "Laboratory results" in decision["rationale"]
        assert "Plus 1 additional documents" in decision["rationale"]  # 4-3=1
        
        # Verify audit trail
        audit_trail = decision["audit_trail"]
        assert "Rule 3: REVIEW for missing critical documentation" in audit_trail["decision_logic_applied"]
        assert audit_trail["input_missing_docs_count"] == 4

    def test_review_uncertain_criteria_path(self):
        """Test REVIEW decision for uncertain criteria."""
        checklist = self._create_test_checklist(
            criteria=[
                {
                    "id": "uncertain_criterion",
                    "description": "Clinical benefit assessment",
                    "status": "uncertain",
                    "rationale": "Insufficient data to determine clinical benefit",
                    "citations": [],
                    "missing_documentation": "Additional clinical documentation needed"
                }
            ],
            missing_documents=[]  # No missing docs to avoid Rule 3
        )
        
        decision, timing = self.pipeline._synthesize_decision(checklist)
        
        # Verify REVIEW outcome
        assert decision["outcome"] == DecisionOutcome.REVIEW.value
        assert ReasonCode.POLICY_CRITERIA_UNCERTAIN.value in decision["reason_codes"]
        
        # Verify uncertain criteria identified
        criteria_summary = decision["criteria_summary"]
        assert len(criteria_summary["uncertain"]) == 1
        assert "uncertain_criterion" in criteria_summary["uncertain"]
        
        # Verify audit trail
        audit_trail = decision["audit_trail"]
        assert "Rule 4: REVIEW for uncertain criteria" in audit_trail["decision_logic_applied"]

    def test_review_low_compliance_score_path(self):
        """Test REVIEW decision for low compliance score."""
        checklist = self._create_test_checklist(
            criteria=[
                {
                    "id": "met_criterion",
                    "description": "Some criterion met",
                    "status": "met",
                    "rationale": "This criterion is satisfied",
                    "citations": ["policy.yaml"],
                    "missing_documentation": None
                }
            ],
            compliance_score=0.5,  # Below 70% threshold
            missing_documents=[]  # No missing docs
        )
        
        decision, timing = self.pipeline._synthesize_decision(checklist)
        
        # Verify REVIEW outcome
        assert decision["outcome"] == DecisionOutcome.REVIEW.value
        assert ReasonCode.INSUFFICIENT_COMPLIANCE.value in decision["reason_codes"]
        
        # Verify rationale mentions low compliance
        assert "compliance score 50.0% below threshold" in decision["rationale"]
        
        # Verify audit trail
        audit_trail = decision["audit_trail"]
        assert "Rule 5: REVIEW for low compliance score" in audit_trail["decision_logic_applied"]

    def test_deterministic_reproducibility(self):
        """Test that identical inputs produce identical outputs."""
        checklist = self._create_test_checklist(
            criteria=[
                {
                    "id": "test_criterion",
                    "description": "Test criterion for reproducibility",
                    "status": "met",
                    "rationale": "Test rationale",
                    "citations": ["test.yaml"],
                    "missing_documentation": None
                }
            ],
            compliance_score=0.85
        )
        
        # Run decision synthesis multiple times
        results = []
        timings = []
        
        for _ in range(5):
            decision, timing = self.pipeline._synthesize_decision(checklist)
            results.append(decision)
            timings.append(timing)
        
        # Verify all outcomes are identical
        outcomes = [r["outcome"] for r in results]
        assert len(set(outcomes)) == 1  # All outcomes the same
        
        # Verify all confidence scores identical
        confidences = [r["confidence"] for r in results]
        assert len(set(confidences)) == 1
        
        # Verify all reason codes identical
        reason_codes = [tuple(sorted(r["reason_codes"])) for r in results]
        assert len(set(reason_codes)) == 1
        
        # Verify rationale content identical (excluding timestamps)
        base_rationales = [r["rationale"].split(". Compliance:")[0] for r in results]
        assert len(set(base_rationales)) == 1
        
        # Verify criteria summaries identical
        met_counts = [len(r["criteria_summary"]["met"]) for r in results]
        assert len(set(met_counts)) == 1

    def test_decision_timing_tracking(self):
        """Test that decision timing is properly tracked and broken down."""
        checklist = self._create_test_checklist()
        
        start_time = time.time()
        decision, timing_breakdown = self.pipeline._synthesize_decision(checklist)
        end_time = time.time()
        
        # Verify timing breakdown structure
        required_timing_keys = [
            "decision_criteria_analysis_ms",
            "decision_rule_evaluation_ms", 
            "decision_audit_generation_ms"
        ]
        
        for key in required_timing_keys:
            assert key in timing_breakdown
            assert isinstance(timing_breakdown[key], (int, float))
            assert timing_breakdown[key] >= 0
        
        # Verify decision includes processing metrics
        processing_metrics = decision["processing_metrics"]
        assert "total_decision_time_ms" in processing_metrics
        assert "criteria_analyzed" in processing_metrics
        assert "rules_evaluated" in processing_metrics
        assert processing_metrics["deterministic_execution"] is True
        
        # Verify total timing is reasonable
        total_ms = processing_metrics["total_decision_time_ms"]
        actual_duration_ms = (end_time - start_time) * 1000
        assert total_ms <= actual_duration_ms + 10  # Allow 10ms tolerance

    def test_audit_trail_completeness(self):
        """Test that audit trail contains all required information."""
        checklist = self._create_test_checklist(
            criteria=[
                {
                    "id": "audit_test_criterion",
                    "description": "Test criterion for audit trail",
                    "status": "met",
                    "rationale": "Test audit rationale",
                    "citations": ["audit_test.yaml"],
                    "missing_documentation": None
                }
            ]
        )
        
        decision, timing = self.pipeline._synthesize_decision(checklist)
        audit_trail = decision["audit_trail"]
        
        # Verify required audit fields
        required_fields = [
            "decision_method",
            "input_criteria_count",
            "input_compliance_score",
            "input_missing_docs_count",
            "output_decision",
            "output_reason_codes",
            "criteria_breakdown",
            "decision_logic_applied",
            "reproducible",
            "audit_timestamp"
        ]
        
        for field in required_fields:
            assert field in audit_trail, f"Missing audit field: {field}"
        
        # Verify audit content quality
        assert audit_trail["decision_method"] == "deterministic_rules"
        assert audit_trail["reproducible"] is True
        assert audit_trail["input_criteria_count"] == 1
        assert isinstance(audit_trail["input_compliance_score"], (int, float))
        assert audit_trail["output_decision"] == DecisionOutcome.APPROVE.value
        
        # Verify criteria breakdown
        breakdown = audit_trail["criteria_breakdown"]
        assert "met_count" in breakdown
        assert "unmet_count" in breakdown
        assert "uncertain_count" in breakdown
        assert breakdown["met_count"] == 1
        
        # Verify timestamp format
        timestamp = audit_trail["audit_timestamp"]
        assert isinstance(timestamp, str)
        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))  # Should not raise

    def test_edge_case_empty_checklist(self):
        """Test decision behavior with empty checklist."""
        checklist = {
            "criteria": [],
            "missing_documents": [],
            "overall_compliance_score": 0.0,
            "policy_source": "unknown"
        }
        
        decision, timing = self.pipeline._synthesize_decision(checklist)
        
        # Should result in REVIEW for low compliance
        assert decision["outcome"] == DecisionOutcome.REVIEW.value
        assert ReasonCode.INSUFFICIENT_COMPLIANCE.value in decision["reason_codes"]
        
        # Verify criteria summary reflects empty state
        criteria_summary = decision["criteria_summary"]
        assert len(criteria_summary["met"]) == 0
        assert len(criteria_summary["unmet"]) == 0
        assert len(criteria_summary["uncertain"]) == 0

    def test_edge_case_malformed_criteria(self):
        """Test robust handling of malformed criteria data."""
        checklist = {
            "criteria": [
                {
                    "id": "valid_criterion",
                    "description": "Valid criterion",
                    "status": "met",
                    "rationale": "Valid rationale",
                    "citations": ["valid.yaml"],
                    "missing_documentation": None
                },
                {
                    # Missing id field - should get default "unknown"
                    "description": "Malformed criterion - missing id",
                    "status": "invalid_status",  # Invalid status - not in met/unmet/uncertain
                    "rationale": "Test malformed criterion handling",
                    "citations": [],
                    "missing_documentation": None
                }
            ],
            "missing_documents": [],
            "overall_compliance_score": 0.8,
            "policy_source": "test_policy"
        }
        
        decision, timing = self.pipeline._synthesize_decision(checklist)
        
        # Should handle gracefully and make a decision
        # Invalid status should be treated as uncertain, affecting decision
        assert decision["outcome"] in [DecisionOutcome.APPROVE.value, DecisionOutcome.REVIEW.value]
        assert "confidence" in decision
        assert "audit_trail" in decision
        
        # Verify criteria were processed (even malformed ones)
        criteria_summary = decision["criteria_summary"]
        assert len(criteria_summary["met"]) >= 1  # At least the valid criterion
        assert isinstance(criteria_summary["uncertain"], list)  # Should contain malformed criterion

    def test_criteria_categorization_logic(self):
        """Test the criterion categorization helper methods."""
        pipeline = self.pipeline
        
        # Test mandatory criterion detection
        assert pipeline._is_mandatory_criterion("diagnosis_required", "Essential diagnosis requirement")
        assert pipeline._is_mandatory_criterion("safety_assessment", "Mandatory safety check")
        assert not pipeline._is_mandatory_criterion("optional_test", "Optional laboratory test")
        
        # Test exclusion criterion detection
        assert pipeline._is_exclusion_criterion("Not covered under policy", "Explicitly excluded")
        assert pipeline._is_exclusion_criterion("Treatment contraindicated", "Medical contraindication")
        assert not pipeline._is_exclusion_criterion("Treatment recommended", "Clinical benefit shown")
        
        # Test safety criterion detection
        assert pipeline._is_safety_criterion("Safety assessment", "Risk of adverse events")
        assert pipeline._is_safety_criterion("Drug interaction check", "Potential contraindication")
        assert not pipeline._is_safety_criterion("Efficacy assessment", "Clinical effectiveness")

    def test_zero_cost_deterministic_execution(self):
        """Test that decision synthesis has zero LLM cost."""
        checklist = self._create_test_checklist()
        
        # Track LLM usage for decision phase
        usage_data = self.pipeline._track_llm_usage("decision")
        
        # Verify zero cost for deterministic execution
        assert usage_data["cost_usd"] == 0.0
        assert usage_data["model_used"] == "deterministic_rules"
        assert usage_data["input_tokens"] == 0
        assert usage_data["output_tokens"] == 0

    def test_decision_constants_integration(self):
        """Test that decision constants are properly integrated."""
        checklist = self._create_test_checklist()
        decision, timing = self.pipeline._synthesize_decision(checklist)
        
        # Verify outcome uses proper enum values
        assert decision["outcome"] in [e.value for e in DecisionOutcome]
        
        # Verify reason codes use proper enum values
        for reason_code in decision["reason_codes"]:
            assert reason_code in [e.value for e in ReasonCode]