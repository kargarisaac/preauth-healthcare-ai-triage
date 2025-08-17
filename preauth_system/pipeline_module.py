"""
DSPy pipeline skeleton for the Prior Authorization MVP.

Implements a minimal `PreAuthPipeline(dspy.Module)` with a `forward(...)` stub
that returns a typed dictionary structure expected by the MVP plan.

This file intentionally provides only the scaffolding; downstream components
will fill in real logic in subsequent milestones.
"""

from __future__ import annotations

from typing import Any, Dict, TypedDict, List
import time

import dspy  # type: ignore

from preauth_system.utils import configure_dspy_default, get_module_lm, with_dspy_lm, get_config
from datetime import datetime, timezone
from preauth_system.utils import parse_xml, extract_patient_info, prepare_pipeline_patient_data
from preauth_system.etl import find_patient_by_emirates_id, create_unified_patient_record
from preauth_system.signatures import (
    ClinicalAnalysis, 
    EvidenceRetrievalSignature, 
    PolicyEvaluationSignature,
    DecisionOutcome,
    ReasonCode,
)
from preauth_system.dossier_writer import DossierWriter
from preauth_system import dspy_tools
from loguru import logger

class PipelineTimings(TypedDict, total=False):
    intake_ms: float
    summary_ms: float
    evidence_ms: float
    checklist_ms: float
    decision_ms: float
    dossier_ms: float
    total_ms: float
    # Enhanced decision phase breakdown
    decision_criteria_analysis_ms: float
    decision_rule_evaluation_ms: float
    decision_audit_generation_ms: float


class PipelineCost(TypedDict, total=False):
    total_cost_usd: float
    phases: Dict[str, float]
    tokens: Dict[str, Dict[str, int]]  # phase -> {input_tokens, output_tokens}
    phase_details: Dict[str, Dict[str, Any]]  # detailed cost breakdown per phase


class PipelineOutput(TypedDict, total=False):
    intake: Dict[str, Any]
    clinical_summary: Dict[str, Any]
    evidence: List[Dict[str, Any]]
    checklist: Dict[str, Any]
    decision: Dict[str, Any]
    dossier: Dict[str, Any]
    timings: PipelineTimings
    cost: PipelineCost
    context: Dict[str, Any]  # Include context for downstream processing
    audit_trail: Dict[str, Any]  # Comprehensive audit information


class PreAuthPipeline(dspy.Module):
    """End-to-end pre-authorization pipeline module (MVP skeleton)."""

    def __init__(self, *, configure_default_lm: bool = True) -> None:
        super().__init__()
        if configure_default_lm:
            # Configure a default LM from `preauth_system/config.yaml` if available
            configure_dspy_default()
        
        # Get module-specific LMs for better control
        self.clinical_lm = get_module_lm("clinical_summarizer")
        self.evidence_lm = get_module_lm("evidence_checker")  
        self.policy_lm = get_module_lm("policy_evaluator")
        self.dossier_lm = get_module_lm("dossier_writer")
        
        # Initialize LLM/agent programs inside the pipeline (centralized control)
        # These modules will use specific LMs with context managers
        self.clinical_summarizer = dspy.ChainOfThought(ClinicalAnalysis)
        # Evidence tools config
        # Signature must be in 'input -> output' format; prompt goes in instructions
        # Evidence ReAct program with typed signature
        self.evidence_checker = dspy.ReAct(EvidenceRetrievalSignature, tools=dspy_tools.DEFAULT_TOOLS)
        self.evidence_tool_map = {
            dspy_tools.get_diabetes_technology_policy.__name__: "preauth_system/policy/policies/diabetes_technology.yaml",
            dspy_tools.get_osteoarthritis_knee_intervention_policy.__name__: "preauth_system/policy/policies/osteoarthritis_knee_intervention.yaml",
            dspy_tools.get_parkinsons_dbs_policy.__name__: "preauth_system/policy/policies/parkinsons_dbs.yaml",
            dspy_tools.get_diabetes_technology_guidelines_kb.__name__: "preauth_system/rag/kb/diabetes_technology_guidelines.md",
            dspy_tools.get_osteoarthritis_management_kb.__name__: "preauth_system/rag/kb/osteoarthritis_management.md",
            dspy_tools.get_parkinsons_dbs_guidelines_kb.__name__: "preauth_system/rag/kb/parkinson_dbs_guidelines.md",
        }
        self.max_tool_calls = 2
        # Policy evaluation with ChainOfThought
        self.policy_evaluator = dspy.ChainOfThought(PolicyEvaluationSignature)
        # Professional dossier writer (Aug 20)
        self.dossier_writer = DossierWriter(language="en")

    # -----------------------------
    # Enhanced Audit and Performance Tracking
    # -----------------------------
    def _track_llm_usage(self, phase: str, lm_context: Any = None) -> Dict[str, Any]:
        """
        Track LLM token usage and cost for a specific phase.
        
        This method inspects the DSPy LM history to extract token counts
        and calculate costs based on model pricing.
        """
        usage_data = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "cost_usd": 0.0,
            "model_used": "unknown",
            "call_count": 0
        }
        
        try:
            # Attempt to get usage from DSPy LM history
            # Note: This is a simplified implementation - real usage tracking
            # would require proper DSPy integration or external tracking
            
            # For deterministic phases (like decision), cost should be 0
            if phase == "decision":
                usage_data["model_used"] = "deterministic_rules"
                usage_data["cost_usd"] = 0.0
                return usage_data
            
            # For LLM phases, we would extract from dspy.settings or LM history
            # This is a placeholder implementation
            config = get_config()
            llm_config = config.get("llm", {})
            model_name = llm_config.get("default_model", "unknown")
            usage_data["model_used"] = model_name
            
            # TODO: Implement actual token counting from DSPy LM history
            # This would require:
            # 1. Accessing dspy.settings.lm.history
            # 2. Parsing prompt/response tokens
            # 3. Calculating cost based on model pricing
            
        except Exception as e:
            logger.warning(f"Failed to track LLM usage for phase {phase}: {e}")
        
        return usage_data
    
    def _generate_comprehensive_audit_trail(self, pipeline_start_time: float, **phase_data) -> Dict[str, Any]:
        """
        Generate comprehensive audit trail for the entire pipeline execution.
        """
        return {
            "pipeline_execution": {
                "start_time": datetime.fromtimestamp(pipeline_start_time, timezone.utc).isoformat(),
                "end_time": datetime.now(timezone.utc).isoformat(),
                "total_duration_ms": (time.time() - pipeline_start_time) * 1000,
                "execution_mode": "deterministic_hybrid"
            },
            "phase_details": phase_data.get("phase_details", {}),
            "cost_breakdown": phase_data.get("cost_breakdown", {}),
            "deterministic_components": [
                "intake_processing",
                "decision_synthesis", 
                "audit_generation"
            ],
            "llm_components": [
                "clinical_summarization",
                "evidence_retrieval", 
                "policy_evaluation"
            ],
            "data_sources": phase_data.get("data_sources", []),
            "processing_flags": phase_data.get("processing_flags", {}),
            "audit_version": "v1.0",
            "compliance_notes": "PDPL-compliant processing with full audit trail"
        }

    # -----------------------------
    # Helpers for post-processing
    # -----------------------------
    def _postprocess_clinical_summary(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        obj.setdefault("executive_summary", "")
        obj.setdefault("patient_profile", {})
        obj.setdefault("timeline", [])
        obj.setdefault("appropriateness", "")
        obj.setdefault("recommendations", [])
        conf = obj.get("confidence")
        try:
            if conf is None:
                obj["confidence"] = 0.0
            else:
                c = float(conf)
                if c > 1.0:
                    c = c / 10.0 if c <= 10.0 else 1.0
                obj["confidence"] = max(0.0, min(1.0, c))
        except Exception:
            obj["confidence"] = 0.0
        return obj

    def _synthesize_decision(self, checklist: Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, float]]:
        """
        Deterministic decision synthesis from PolicyChecklistOutput.
        
        Rules:
        - APPROVE: All mandatory criteria met AND no safety blocks
        - DENY: Explicit non-coverage criterion present
        - REVIEW: Uncertain/unmet non-mandatory OR missing docs
        
        Returns:
            Tuple of (decision_object, timing_breakdown)
        """
        decision_start = time.time()
        
        # Phase 1: Extract and validate input data
        criteria_start = time.time()
        criteria = checklist.get("criteria", [])
        missing_documents = checklist.get("missing_documents", [])
        overall_compliance_score = checklist.get("overall_compliance_score", 0.0)
        policy_source = checklist.get("policy_source", "unknown")
        criteria_analysis_ms = (time.time() - criteria_start) * 1000
        
        # Phase 2: Analyze criteria status patterns  
        met_criteria = []
        unmet_criteria = []
        uncertain_criteria = []
        mandatory_unmet = []
        explicit_exclusions = []
        safety_blocks = []
        
        for criterion in criteria:
            criterion_id = criterion.get("id", "unknown")
            status = criterion.get("status", "uncertain")
            description = criterion.get("description", "")
            rationale = criterion.get("rationale", "")
            
            # Categorize criteria by status
            if status == "met":
                met_criteria.append(criterion_id)
            elif status == "unmet":
                unmet_criteria.append(criterion_id)
                
                # Detect mandatory criteria (policy-specific logic)
                if self._is_mandatory_criterion(criterion_id, description):
                    mandatory_unmet.append(criterion_id)
                    
                # Detect explicit exclusions
                if self._is_exclusion_criterion(description, rationale):
                    explicit_exclusions.append(criterion_id)
                    
                # Detect safety contraindications
                if self._is_safety_criterion(description, rationale):
                    safety_blocks.append(criterion_id)
            else:  # uncertain
                uncertain_criteria.append(criterion_id)
        
        # Phase 3: Apply deterministic decision rules
        rules_start = time.time()
        outcome = None
        reason_codes = []
        conditions = []
        rationale_parts = []
        confidence = 1.0  # Deterministic rules = 100% confidence
        
        # Rule 1: DENY for explicit exclusions or safety blocks
        if explicit_exclusions:
            outcome = DecisionOutcome.DENY
            reason_codes.append(ReasonCode.EXPLICIT_EXCLUSION.value)
            rationale_parts.append(f"Explicit exclusion criteria present: {', '.join(explicit_exclusions)}")
            
        elif safety_blocks:
            outcome = DecisionOutcome.DENY
            reason_codes.append(ReasonCode.SAFETY_CONTRAINDICATION.value)
            rationale_parts.append(f"Safety contraindications identified: {', '.join(safety_blocks)}")
            
        # Rule 2: DENY for unmet mandatory criteria
        elif mandatory_unmet:
            outcome = DecisionOutcome.DENY
            reason_codes.append(ReasonCode.MANDATORY_CRITERIA_UNMET.value)
            rationale_parts.append(f"Mandatory criteria unmet: {', '.join(mandatory_unmet)}")
            
        # Rule 3: REVIEW for missing critical documentation
        elif len(missing_documents) >= 3:  # Threshold for critical missing docs
            outcome = DecisionOutcome.REVIEW
            reason_codes.append(ReasonCode.MISSING_REQUIRED_DOCUMENTATION.value)
            rationale_parts.append(f"Critical documentation missing: {', '.join(missing_documents[:3])}")
            if len(missing_documents) > 3:
                rationale_parts.append(f"Plus {len(missing_documents) - 3} additional documents")
                
        # Rule 4: REVIEW for uncertain criteria
        elif uncertain_criteria:
            outcome = DecisionOutcome.REVIEW
            reason_codes.append(ReasonCode.POLICY_CRITERIA_UNCERTAIN.value)
            rationale_parts.append(f"Uncertain criteria require review: {', '.join(uncertain_criteria)}")
            
        # Rule 5: REVIEW for low compliance score
        elif overall_compliance_score < 0.7:  # 70% threshold
            outcome = DecisionOutcome.REVIEW
            reason_codes.append(ReasonCode.INSUFFICIENT_COMPLIANCE.value)
            rationale_parts.append(f"Overall compliance score {overall_compliance_score:.1%} below threshold")
            
        # Rule 6: APPROVE if all conditions satisfied
        else:
            outcome = DecisionOutcome.APPROVE
            rationale_parts.append(f"All criteria satisfied with {overall_compliance_score:.1%} compliance")
            
            # Add approval conditions based on policy requirements
            if policy_source != "unknown":
                conditions.append(f"Subject to {policy_source} policy terms")
            if len(met_criteria) > 0:
                conditions.append(f"Coverage validated against {len(met_criteria)} criteria")
        
        # Build comprehensive rationale
        summary_stats = (
            f"Criteria analysis: {len(met_criteria)} met, {len(unmet_criteria)} unmet, "
            f"{len(uncertain_criteria)} uncertain. Compliance: {overall_compliance_score:.1%}."
        )
        rationale_parts.insert(0, summary_stats)
        rule_evaluation_ms = (time.time() - rules_start) * 1000
        
        # Phase 4: Generate audit trail
        audit_start = time.time()
        audit_trail = self._generate_decision_audit_trail(
            checklist=checklist,
            outcome=outcome,
            reason_codes=reason_codes,
            met_criteria=met_criteria,
            unmet_criteria=unmet_criteria,
            uncertain_criteria=uncertain_criteria,
            mandatory_unmet=mandatory_unmet,
            explicit_exclusions=explicit_exclusions,
            safety_blocks=safety_blocks
        )
        audit_generation_ms = (time.time() - audit_start) * 1000
        
        # Calculate timing breakdown for this decision phase
        timing_breakdown = {
            "decision_criteria_analysis_ms": criteria_analysis_ms,
            "decision_rule_evaluation_ms": rule_evaluation_ms,
            "decision_audit_generation_ms": audit_generation_ms
        }
        
        # Log detailed decision metrics
        logger.info(f"Decision synthesis completed: {outcome.value if outcome else 'unknown'}")
        logger.info(f"Decision timing breakdown: criteria={criteria_analysis_ms:.2f}ms, "
                   f"rules={rule_evaluation_ms:.2f}ms, audit={audit_generation_ms:.2f}ms")
        logger.info(f"Decision cost: $0.00 (deterministic)")
        
        decision_result = {
            "outcome": outcome.value,
            "confidence": confidence,
            "reason_codes": reason_codes,
            "conditions": conditions,
            "rationale": " ".join(rationale_parts),
            "criteria_summary": {
                "met": met_criteria,
                "unmet": unmet_criteria,
                "uncertain": uncertain_criteria,
                "mandatory_unmet": mandatory_unmet,
                "explicit_exclusions": explicit_exclusions,
                "safety_blocks": safety_blocks
            },
            "compliance_score": overall_compliance_score,
            "policy_source": policy_source,
            "audit_trail": audit_trail,
            "decision_timestamp": datetime.now(timezone.utc).isoformat(),
            "processing_metrics": {
                "total_decision_time_ms": (time.time() - decision_start) * 1000,
                "criteria_analyzed": len(criteria),
                "rules_evaluated": 6,  # Total number of decision rules
                "deterministic_execution": True
            }
        }
        
        return decision_result, timing_breakdown
    
    def _is_mandatory_criterion(self, criterion_id: str, description: str) -> bool:
        """
        Determine if a criterion is mandatory based on ID patterns and description.
        
        Mandatory criteria typically include:
        - Diagnosis requirements
        - Safety assessments
        - Essential clinical thresholds
        """
        mandatory_patterns = [
            "diagnosis",
            "required",
            "essential",
            "mandatory",
            "safety",
            "contraindication",
            "eligibility"
        ]
        
        # Check criterion ID and description for mandatory indicators
        text_to_check = f"{criterion_id} {description}".lower()
        return any(pattern in text_to_check for pattern in mandatory_patterns)
    
    def _is_exclusion_criterion(self, description: str, rationale: str) -> bool:
        """
        Detect explicit exclusion criteria that warrant DENY decision.
        """
        exclusion_patterns = [
            "not covered",
            "excluded",
            "contraindicated",
            "inappropriate",
            "not indicated",
            "non-coverage",
            "exclusion",
            "denied"
        ]
        
        text_to_check = f"{description} {rationale}".lower()
        return any(pattern in text_to_check for pattern in exclusion_patterns)
    
    def _is_safety_criterion(self, description: str, rationale: str) -> bool:
        """
        Detect safety-related criteria that may block approval.
        """
        safety_patterns = [
            "safety",
            "adverse",
            "contraindication",
            "interaction",
            "allergy",
            "intolerance",
            "risk",
            "complication",
            "side effect"
        ]
        
        text_to_check = f"{description} {rationale}".lower()
        return any(pattern in text_to_check for pattern in safety_patterns)
    
    def _generate_decision_audit_trail(self, **kwargs) -> Dict[str, Any]:
        """
        Generate comprehensive audit trail for decision synthesis.
        """
        checklist = kwargs.get("checklist", {})
        outcome = kwargs.get("outcome")
        reason_codes = kwargs.get("reason_codes", [])
        
        return {
            "decision_method": "deterministic_rules",
            "input_criteria_count": len(checklist.get("criteria", [])),
            "input_compliance_score": checklist.get("overall_compliance_score", 0.0),
            "input_missing_docs_count": len(checklist.get("missing_documents", [])),
            "output_decision": outcome.value if outcome else "unknown",
            "output_reason_codes": reason_codes,
            "criteria_breakdown": {
                "met_count": len(kwargs.get("met_criteria", [])),
                "unmet_count": len(kwargs.get("unmet_criteria", [])),
                "uncertain_count": len(kwargs.get("uncertain_criteria", [])),
                "mandatory_unmet_count": len(kwargs.get("mandatory_unmet", [])),
                "exclusions_count": len(kwargs.get("explicit_exclusions", [])),
                "safety_blocks_count": len(kwargs.get("safety_blocks", []))
            },
            "decision_logic_applied": self._get_decision_logic_summary(**kwargs),
            "reproducible": True,
            "audit_timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _get_decision_logic_summary(self, **kwargs) -> str:
        """
        Provide human-readable summary of which decision logic path was taken.
        """
        outcome = kwargs.get("outcome")
        explicit_exclusions = kwargs.get("explicit_exclusions", [])
        safety_blocks = kwargs.get("safety_blocks", [])
        mandatory_unmet = kwargs.get("mandatory_unmet", [])
        missing_documents = kwargs.get("checklist", {}).get("missing_documents", [])
        uncertain_criteria = kwargs.get("uncertain_criteria", [])
        compliance_score = kwargs.get("checklist", {}).get("overall_compliance_score", 0.0)
        
        if outcome == DecisionOutcome.DENY:
            if explicit_exclusions:
                return "Rule 1: DENY for explicit exclusions"
            elif safety_blocks:
                return "Rule 1: DENY for safety contraindications"
            elif mandatory_unmet:
                return "Rule 2: DENY for unmet mandatory criteria"
        elif outcome == DecisionOutcome.REVIEW:
            if len(missing_documents) >= 3:
                return "Rule 3: REVIEW for missing critical documentation"
            elif uncertain_criteria:
                return "Rule 4: REVIEW for uncertain criteria"
            elif compliance_score < 0.7:
                return "Rule 5: REVIEW for low compliance score"
        elif outcome == DecisionOutcome.APPROVE:
            return "Rule 6: APPROVE - all conditions satisfied"
        
        return "Unknown decision path"

    def _postprocess_policy_checklist(self, obj: Dict[str, Any], evidence_sources: List[str]) -> Dict[str, Any]:
        """Post-process and validate PolicyChecklistOutput with schema normalization."""
        # Ensure required fields exist with defaults
        obj.setdefault("criteria", [])
        obj.setdefault("missing_documents", [])
        obj.setdefault("overall_compliance_score", 0.0)
        obj.setdefault("policy_source", "unknown")
        
        # Validate and normalize criteria
        valid_statuses = {"met", "unmet", "uncertain"}
        normalized_criteria = []
        
        for criterion in obj.get("criteria", []):
            if not isinstance(criterion, dict):
                continue
                
            normalized_criterion = {
                "id": str(criterion.get("id", "unknown")),
                "description": str(criterion.get("description", "")),
                "status": criterion.get("status", "uncertain"),
                "rationale": str(criterion.get("rationale", "")),
                "citations": criterion.get("citations", []),
                "missing_documentation": criterion.get("missing_documentation")
            }
            
            # Normalize status to valid values
            if normalized_criterion["status"] not in valid_statuses:
                normalized_criterion["status"] = "uncertain"
            
            # Ensure citations is a list
            if not isinstance(normalized_criterion["citations"], list):
                normalized_criterion["citations"] = []
            
            # Validate citations against evidence sources
            valid_citations = []
            for citation in normalized_criterion["citations"]:
                citation_str = str(citation)
                # Check if citation references any provided evidence source
                if any(source in citation_str for source in evidence_sources):
                    valid_citations.append(citation_str)
            normalized_criterion["citations"] = valid_citations
            
            normalized_criteria.append(normalized_criterion)
        
        obj["criteria"] = normalized_criteria
        
        # Normalize compliance score
        score = obj.get("overall_compliance_score", 0.0)
        try:
            score = float(score)
            if score > 1.0:
                score = score / 100.0 if score <= 100.0 else 1.0
            obj["overall_compliance_score"] = max(0.0, min(1.0, score))
        except (ValueError, TypeError):
            obj["overall_compliance_score"] = 0.0
            
        # Ensure missing_documents is a list of strings
        missing_docs = obj.get("missing_documents", [])
        if isinstance(missing_docs, list):
            obj["missing_documents"] = [str(doc) for doc in missing_docs if doc]
        else:
            obj["missing_documents"] = []
            
        return obj

    def _intake(self, xml_path: str, xml_format: str) -> tuple[Dict[str, Any], Dict[str, Any], bool]:
        """Perform intake: parse XML, extract patient info, resolve patient, build context."""
        try:
            parsed_xml = parse_xml(xml_path, xml_format)
            patient_info = extract_patient_info(parsed_xml, xml_format)
            emirates_id = patient_info.get("EmiratesIDNumber")
            patient_id = find_patient_by_emirates_id(emirates_id) if emirates_id else None
            unified_record = None
            pipeline_patient_data: Dict[str, Any] | None = None
            if patient_id:
                unified_record = create_unified_patient_record(
                    patient_id=patient_id,
                    xml_request_data=parsed_xml,
                    xml_patient_info=patient_info,
                )
                pipeline_patient_data = prepare_pipeline_patient_data(unified_record)
        except Exception:
            parsed_xml = {"file_path": xml_path, "format": xml_format, "as_dict": {}}
            patient_info = {"EmiratesIDNumber": None, "services": [], "total_cost": 0.0, "justification": None}
            emirates_id = None
            patient_id = None
            unified_record = None
            pipeline_patient_data = None

        intake: Dict[str, Any] = {
            "xml_path": xml_path,
            "xml_format": xml_format,
            "emirates_id": emirates_id,
            "patient_id": patient_id,
            "patient_info": patient_info,
        }
        context: Dict[str, Any] = {
            "patient_data": pipeline_patient_data or {},
            "unified_record_present": bool(unified_record),
        }
        return intake, context, bool(unified_record)

    def forward(self, xml_path: str, xml_format: str = "eclaim") -> PipelineOutput:  # type: ignore[override]
        """Run the MVP pipeline.

        For Aug 14 milestone, this returns a skeleton object with placeholders.
        """
        start = time.time()

        # Intake & context mapping (Aug 15)
        logger.info("Intake & context mapping")
        t0 = time.time()
        intake, context, _ = self._intake(xml_path=xml_path, xml_format=xml_format)
        intake_ms = (time.time() - t0)
        logger.info(f"Intake & context mapping took {intake_ms}s")
        # Clinical summarization (Aug 16)
        logger.info("Clinical summarization")
        t1 = time.time()
        try:
            patient_data = context.get("patient_data", {})
            with with_dspy_lm(self.clinical_lm):
                clinical_summary = self.clinical_summarizer(patient_data=patient_data)  # type: ignore
            analysis = getattr(clinical_summary, "analysis", None)
            if analysis is None:
                clinical_summary = self._postprocess_clinical_summary({})
            elif hasattr(analysis, "model_dump"):
                clinical_summary = self._postprocess_clinical_summary(analysis.model_dump())
            elif hasattr(analysis, "dict"):
                clinical_summary = self._postprocess_clinical_summary(analysis.dict())
            else:
                clinical_summary = self._postprocess_clinical_summary({})
        except Exception:
            clinical_summary = self._postprocess_clinical_summary({})
        summary_ms = (time.time() - t1)
        logger.info(f"Clinical summarization took {summary_ms}s")

        # Evidence retrieval (Aug 17)
        logger.info("Evidence retrieval")
        t2 = time.time()
        try:
            with with_dspy_lm(self.evidence_lm):
                react_out = self.evidence_checker(
                    patient_data=patient_data,
                    clinical_summary=clinical_summary,
                )  # type: ignore
            evidence_obj = getattr(react_out, "evidence", None)
            if evidence_obj and hasattr(evidence_obj, "evidence"):
                items = evidence_obj.evidence or []
                evidence = []
                for it in items[: self.max_tool_calls]:
                    src = getattr(it, "source", None)
                    snip = getattr(it, "snippet", None)
                    if src and snip:
                        evidence.append({"source": src, "snippet": snip})
        except Exception:
            evidence = []

        evidence_ms = (time.time() - t2)
        logger.info(f"Evidence retrieval took {evidence_ms}s")

        # Policy evaluation (Aug 18)
        logger.info("Policy evaluation")
        t3 = time.time()
        try:
            # Extract evidence sources for citation validation
            evidence_sources = []
            for evt in evidence:
                source = evt.get("source", "")
                if source:
                    # Map tool names to file paths using evidence_tool_map
                    mapped_source = self.evidence_tool_map.get(source, source)
                    evidence_sources.append(mapped_source)
            
            with with_dspy_lm(self.policy_lm):
                policy_pred = self.policy_evaluator(
                    patient_data=patient_data,
                    clinical_summary=clinical_summary,
                    evidence=evidence
                )  # type: ignore
            
            checklist_obj = getattr(policy_pred, "policy_checklist", None)
            if checklist_obj is None:
                checklist = {"criteria": [], "missing_documents": [], "overall_compliance_score": 0.0, "policy_source": "unknown"}
            elif hasattr(checklist_obj, "model_dump"):
                checklist = self._postprocess_policy_checklist(checklist_obj.model_dump(), evidence_sources)
            elif hasattr(checklist_obj, "dict"):
                checklist = self._postprocess_policy_checklist(checklist_obj.dict(), evidence_sources)
            else:
                # Fallback for dict-like objects
                checklist_dict = dict(checklist_obj) if hasattr(checklist_obj, "__iter__") else {}
                checklist = self._postprocess_policy_checklist(checklist_dict, evidence_sources)
        except Exception:
            # Graceful degradation with empty checklist
            checklist = {"criteria": [], "missing_documents": [], "overall_compliance_score": 0.0, "policy_source": "unknown"}
        
        checklist_ms = (time.time() - t3)
        logger.info(f"Policy evaluation took {checklist_ms}s")

        # Decision synthesis with deterministic rules (Aug 19)
        logger.info("Decision synthesis")
        t4 = time.time()
        decision, decision_timing_breakdown = self._synthesize_decision(checklist)
        decision_ms = (time.time() - t4) * 1000  # Convert to milliseconds consistently
        logger.info(f"Decision synthesis took {decision_ms:.2f}ms")

        # Professional dossier generation (Aug 20)
        logger.info("Generating professional dossier")
        t5 = time.time()
        try:
            # Prepare patient context from intake data for richer dossier
            patient_context = {
                "age": intake.get("patient_info", {}).get("age", "unknown"),
                "gender": intake.get("patient_info", {}).get("gender", "unknown"),
                "emirates_id": intake.get("patient_info", {}).get("emirates_id", "unknown"),
                "policy_number": intake.get("patient_info", {}).get("policy_number", "unknown")
            }
            
            dossier = self.dossier_writer.forward(
                clinical_summary=clinical_summary,
                checklist=checklist,
                decision=decision,
                evidence=evidence,
                patient_context=patient_context
            )
        except Exception as e:
            logger.error(f"Dossier generation failed, using fallback: {e}")
            # Fallback to basic dossier
            dossier = {
                "executive_summary": f"Authorization {decision.get('outcome', 'UNKNOWN')}: {clinical_summary.get('executive_summary', 'Clinical data processed')}",
                "sections": [
                    {
                        "title": "System Notice",
                        "content": "Professional dossier generation encountered an issue. Manual review recommended.",
                        "type": "notice"
                    }
                ],
                "citations": [],
                "language": "en",
                "metadata": {
                    "sections_count": 1,
                    "has_citations": False,
                    "complexity_score": 10,
                    "is_fallback": True
                }
            }
        
        dossier_ms = (time.time() - t5) * 1000
        logger.info(f"Dossier generation took {dossier_ms:.2f}ms")

        # Enhanced timing tracking with decision breakdown
        timings: PipelineTimings = {
            "intake_ms": intake_ms * 1000,  # Convert to milliseconds for consistency
            "summary_ms": summary_ms * 1000,
            "evidence_ms": evidence_ms * 1000,
            "checklist_ms": checklist_ms * 1000,
            "decision_ms": decision_ms,
            "dossier_ms": dossier_ms,
            "total_ms": (time.time() - start) * 1000,
            # Enhanced decision phase breakdown
            "decision_criteria_analysis_ms": decision_timing_breakdown.get("decision_criteria_analysis_ms", 0.0),
            "decision_rule_evaluation_ms": decision_timing_breakdown.get("decision_rule_evaluation_ms", 0.0),
            "decision_audit_generation_ms": decision_timing_breakdown.get("decision_audit_generation_ms", 0.0)
        }

        # Enhanced cost tracking with phase-specific usage
        cost_phases = {}
        token_usage = {}
        phase_details = {}
        
        # Track usage for each LLM phase
        for phase in ["intake", "summary", "evidence", "checklist", "decision", "dossier"]:
            usage_data = self._track_llm_usage(phase)
            cost_phases[phase] = usage_data["cost_usd"]
            token_usage[phase] = {
                "input_tokens": usage_data["input_tokens"],
                "output_tokens": usage_data["output_tokens"],
                "total_tokens": usage_data["total_tokens"]
            }
            phase_details[phase] = {
                "model_used": usage_data["model_used"],
                "call_count": usage_data["call_count"],
                "cost_usd": usage_data["cost_usd"]
            }

        cost: PipelineCost = {
            "total_cost_usd": sum(cost_phases.values()),
            "phases": cost_phases,
            "tokens": token_usage,
            "phase_details": phase_details
        }

        # Generate comprehensive audit trail
        audit_trail = self._generate_comprehensive_audit_trail(
            start,
            phase_details=phase_details,
            cost_breakdown=cost_phases,
            data_sources=[
                intake.get("xml_path", "unknown"),
                f"patient_id:{intake.get('patient_id', 'unknown')}",
                f"policy:{checklist.get('policy_source', 'unknown')}"
            ],
            processing_flags={
                "deterministic_decision": True,
                "llm_assisted_summary": bool(clinical_summary.get("executive_summary")),
                "evidence_retrieved": len(evidence) > 0,
                "policy_evaluated": bool(checklist.get("criteria"))
            }
        )

        # Log comprehensive pipeline metrics
        logger.info(f"Pipeline execution completed in {timings['total_ms']:.2f}ms")
        logger.info(f"Total cost: ${cost['total_cost_usd']:.6f}")
        logger.info(f"Decision outcome: {decision.get('outcome', 'unknown')}")
        logger.info(f"Cost breakdown: " + ", ".join([f"{k}=${v:.4f}" for k, v in cost_phases.items() if v > 0]))
        
        return {
            "intake": intake,
            "context": context,
            "clinical_summary": clinical_summary,
            "evidence": evidence,
            "checklist": checklist,
            "decision": decision,
            "dossier": dossier,
            "timings": timings,
            "cost": cost,
            "audit_trail": audit_trail
        }


def main():
    """CLI entry point for testing with Patient_007 processing and timestamped JSON output."""
    import json
    import os
    from pathlib import Path
    from datetime import datetime
    
    # Create dated run directory: output/YYYYMMDD/HHMMSS
    now = datetime.now()
    date_dir = Path("output") / now.strftime("%Y%m%d")
    time_dir = date_dir / now.strftime("%H%M%S")
    time_dir.mkdir(parents=True, exist_ok=True)
    
    # Expose run dir to route traces
    os.environ["PREAUTH_RUN_DIR"] = str(time_dir)
    
    xml_file_path = "data/dataset_2/synthetic_dataset/UAE_XML/Patient_007_eclaim.xml"
    patient_id = "Patient_007"
    
    logger.info(f"Processing {patient_id} with PreAuthPipeline")
    
    # Initialize and run pipeline
    pipeline = PreAuthPipeline()
    result = pipeline.forward(xml_path=xml_file_path, xml_format="eclaim")
    
    # Convert result to JSON-serializable format
    def serialize_result(obj):
        """Convert pipeline result to JSON-serializable format."""
        if hasattr(obj, 'dict'):
            return obj.dict()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        elif isinstance(obj, (list, tuple)):
            return [serialize_result(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: serialize_result(v) for k, v in obj.items()}
        else:
            return str(obj)
    
    serializable_result = serialize_result(result)
    
    # Save JSON output
    json_output_path = time_dir / f"{patient_id}_result.json"
    try:
        with open(json_output_path, "w", encoding="utf-8") as f:
            json.dump(serializable_result, f, indent=2, default=str)
        logger.info(f"Processing result saved to: {json_output_path}")
        print(f"✅ Processing result saved to: {json_output_path}")
    except Exception as e:
        logger.error(f"Failed to save JSON result: {e}")
        print(f"❌ Failed to save JSON result: {e}")
    
    # Display summary
    print("\n" + "=" * 60)
    print(f"PIPELINE PROCESSING SUMMARY - {patient_id}")
    print("=" * 60)
    
    # Extract key metrics
    timings = result.get("timings", {})
    cost = result.get("cost", {})
    decision = result.get("decision", {})
    
    print(f"Patient ID: {result.get('intake', {}).get('patient_id', 'Unknown')}")
    print(f"Processing Time: {timings.get('total_ms', 0):.2f}ms")
    print(f"Total Cost: ${cost.get('total_cost_usd', 0):.6f}")
    
    print(f"\nDecision: {decision.get('outcome', 'Unknown')}")
    print(f"Confidence: {decision.get('confidence', 'N/A')}")
    
    if timings:
        print(f"\nPhase Timing Breakdown:")
        for phase in ["intake_ms", "summary_ms", "evidence_ms", "checklist_ms", "decision_ms"]:
            if phase in timings:
                print(f"  - {phase.replace('_ms', '').title()}: {timings[phase]:.2f}ms")
    
    if cost.get("phases"):
        print(f"\nCost Breakdown:")
        for phase, cost_val in cost["phases"].items():
            if cost_val > 0:
                print(f"  - {phase.title()}: ${cost_val:.6f}")
    
    # Evidence and checklist summary
    evidence = result.get("evidence", [])
    checklist = result.get("checklist", {})
    
    print(f"\nEvidence Retrieved: {len(evidence)} items")
    print(f"Policy Criteria Evaluated: {len(checklist.get('criteria', []))}")
    print(f"Overall Compliance Score: {checklist.get('overall_compliance_score', 0):.1%}")
    
    print("\nOutput Files:")
    print(f"  JSON Result: {json_output_path}")
    print("=" * 60)


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    main()