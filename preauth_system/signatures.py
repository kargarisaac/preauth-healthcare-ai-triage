"""
Shared DSPy Signature Classes for Pre-Authorization Agents
Prevents code duplication across agent files
"""
import dspy
from typing import Dict, Any, List, Optional, TypedDict, Literal
from pydantic import BaseModel
from enum import Enum

# Reuse the exact same description string across all signatures
PATIENT_DATA_DESC = (
    "Structured patient context including demographics, medical_history, "
    "clinical_data (symptoms, labs, vitals), and requested_treatment."
)


# -----------------------------
# Decision constants and enums
# -----------------------------
class DecisionOutcome(Enum):
    """Possible decision outcomes for prior authorization requests."""
    
    APPROVE = "APPROVE"
    DENY = "DENY"
    REVIEW = "REVIEW"


class ReasonCode(Enum):
    """Standardized reason codes for decision outcomes."""
    
    # Approval reasons
    POLICY_CRITERIA_MET = "POLICY_CRITERIA_MET"
    CLINICAL_APPROPRIATENESS_CONFIRMED = "CLINICAL_APPROPRIATENESS_CONFIRMED"
    
    # Denial reasons
    EXPLICIT_EXCLUSION = "EXPLICIT_EXCLUSION"
    SAFETY_CONTRAINDICATION = "SAFETY_CONTRAINDICATION"
    MANDATORY_CRITERIA_UNMET = "MANDATORY_CRITERIA_UNMET"
    POLICY_NON_COVERAGE = "POLICY_NON_COVERAGE"
    
    # Review reasons
    MISSING_REQUIRED_DOCUMENTATION = "MISSING_REQUIRED_DOCUMENTATION"
    POLICY_CRITERIA_UNCERTAIN = "POLICY_CRITERIA_UNCERTAIN"
    INSUFFICIENT_COMPLIANCE = "INSUFFICIENT_COMPLIANCE"
    INCOMPLETE_INFORMATION = "INCOMPLETE_INFORMATION"
    REQUIRES_PEER_REVIEW = "REQUIRES_PEER_REVIEW"


# Mapping of criterion patterns to reason codes for deterministic logic
CRITERION_TO_REASON_MAP = {
    "diabetes_diagnosis": {
        "unmet": ReasonCode.POLICY_NON_COVERAGE,
        "uncertain": ReasonCode.INCOMPLETE_INFORMATION
    },
    "hba1c_elevated": {
        "unmet": ReasonCode.POLICY_CRITERIA_UNCERTAIN,
        "uncertain": ReasonCode.INCOMPLETE_INFORMATION
    },
    "safety_assessment": {
        "unmet": ReasonCode.SAFETY_CONTRAINDICATION,
        "uncertain": ReasonCode.REQUIRES_PEER_REVIEW
    }
}


# -----------------------------
# Cross-module typed structures
# -----------------------------
class AgentResult(TypedDict, total=False):
    agent_name: str
    status: str
    start_time: Optional[str]
    end_time: Optional[str]
    processing_time_seconds: Optional[float]
    response: Optional[str]
    usage: Dict[str, Any]
    success: bool
    error: Optional[str]
    traceback: Optional[str]


class SharedContext(TypedDict, total=False):
    xml_request: Dict[str, Any]
    patient_demographics: Dict[str, Any]
    medical_history: Dict[str, Any]
    clinical_data: Dict[str, Any]
    specialty: str
    analysis_timestamp: str


# -----------------------------
# Pydantic output models
# -----------------------------
class ClinicalAnalysisOutput(BaseModel):
    executive_summary: Optional[str] = None
    patient_profile: Optional[Dict[str, Any]] = None
    timeline: Optional[List[str]] = None
    appropriateness: Optional[str] = None
    recommendations: Optional[List[str]] = None
    confidence: Optional[float] = None


class MedicationAnalysisOutput(BaseModel):
    summary: Optional[str] = None
    interactions: Optional[List[Dict[str, Any]]] = None
    safety: Optional[Dict[str, Any]] = None
    appropriateness: Optional[str] = None
    recommendations: Optional[List[str]] = None
    confidence: Optional[float] = None


class RiskAssessmentOutput(BaseModel):
    overall_level: Optional[str] = None
    drivers: Optional[List[str]] = None
    safety_concerns: Optional[List[str]] = None
    risk_benefit: Optional[str] = None
    mitigation: Optional[List[str]] = None
    confidence: Optional[float] = None


class AuthorizationDecisionOutput(BaseModel):
    decision: Optional[str] = None
    confidence: Optional[float] = None
    rationale: Optional[str] = None
    citations: Optional[List[str]] = None
    conditions: Optional[List[str]] = None


class ComplianceAuditOutput(BaseModel):
    score: Optional[float] = None
    documentation: Optional[Dict[str, Any]] = None
    policy_adherence: Optional[Dict[str, Any]] = None
    regulatory_status: Optional[Dict[str, Any]] = None
    quality_assurance: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[str]] = None


class SpecialtyOutput(BaseModel):
    specialty: Optional[str] = None


class FinalReportOutput(BaseModel):
    executive_summary: Optional[str] = None
    clinical_context: Optional[str] = None
    decision_rationale: Optional[str] = None
    policy_analysis: Optional[str] = None
    risk_assessment: Optional[str] = None
    next_steps: Optional[str] = None
    citations: Optional[List[str]] = None
    language: Optional[str] = "en"  # en, ar for future bilingual support
    
    # Legacy support for simple content field
    content: Optional[str] = None
    
    def to_structured_dossier(self) -> Dict[str, Any]:
        """Convert to structured dossier format expected by pipeline."""
        sections = []
        
        if self.executive_summary:
            sections.append({
                "title": "Executive Summary",
                "content": self.executive_summary,
                "type": "summary"
            })
            
        if self.clinical_context:
            sections.append({
                "title": "Clinical Context",
                "content": self.clinical_context,
                "type": "clinical"
            })
            
        if self.policy_analysis:
            sections.append({
                "title": "Policy Analysis",
                "content": self.policy_analysis,
                "type": "policy"
            })
            
        if self.decision_rationale:
            sections.append({
                "title": "Decision Rationale",
                "content": self.decision_rationale,
                "type": "decision"
            })
            
        if self.risk_assessment:
            sections.append({
                "title": "Risk Assessment",
                "content": self.risk_assessment,
                "type": "risk"
            })
            
        if self.next_steps:
            sections.append({
                "title": "Next Steps",
                "content": self.next_steps,
                "type": "action"
            })
            
        return {
            "executive_summary": self.executive_summary or "No summary provided",
            "sections": sections,
            "citations": self.citations or [],
            "language": self.language,
            "metadata": {
                "sections_count": len(sections),
                "has_citations": bool(self.citations),
                "complexity_score": min(100, len(sections) * 15 + len(self.citations or []) * 5)
            }
        }


# Additional module outputs
class ClinicalRiskOutput(BaseModel):
    overall_risk: Optional[str] = None
    risk_factors: Optional[List[str]] = None
    confidence: Optional[float] = None
    reasoning: Optional[str] = None


class DataQualityOutput(BaseModel):
    overall_score: Optional[float] = None
    completeness_score: Optional[float] = None
    richness_score: Optional[float] = None
    accuracy_score: Optional[float] = None
    recommendations: Optional[List[str]] = None
    reasoning: Optional[str] = None


# -----------------------------
# Shared input signature
# -----------------------------
class PatientData(dspy.Signature):
    """Patient demographic and clinical data for analysis."""

    patient_demographics: Dict[str, Any] = dspy.InputField(
        desc="Patient age, gender, nationality, insurance info"
    )
    medical_history: Dict[str, Any] = dspy.InputField(
        desc="Past medical conditions, treatments, procedures"
    )
    clinical_data: Dict[str, Any] = dspy.InputField(
        desc="Current symptoms, lab results, vital signs"
    )
    requested_treatment: Dict[str, Any] = dspy.InputField(
        desc="Requested service, medication, or procedure details"
    )

# -----------------------------
# Evidence retrieval outputs
# -----------------------------
class EvidenceItem(BaseModel):
    source: Optional[str] = None
    snippet: Optional[str] = None


class EvidenceRetrievalOutput(BaseModel):
    evidence: Optional[List[EvidenceItem]] = None


# -----------------------------
# Policy evaluation outputs
# -----------------------------
class PolicyCriteriaItem(BaseModel):
    id: str
    description: str
    status: Literal["met", "unmet", "uncertain"]
    rationale: str
    citations: List[str]
    missing_documentation: Optional[str] = None


class PolicyChecklistOutput(BaseModel):
    criteria: List[PolicyCriteriaItem]
    missing_documents: List[str]
    overall_compliance_score: float
    policy_source: str


# -----------------------------
# Agent signatures
# -----------------------------
class ClinicalAnalysis(dspy.Signature):
    """You are a clinical analysis agent.
    Task: build a medical timeline, assess clinical appropriateness vs guidelines, and identify risk factors.
    Context: consider UAE healthcare specifics (Ramadan fasting impact, high prevalence of diabetes/CVD, climate and occupational factors).
    Output: executive summary, patient profile & risks, timeline, appropriateness, evidence‑based recommendations, confidence (1–10).
    """

    patient_data: Dict[str, Any] = dspy.InputField(desc=PATIENT_DATA_DESC)
    analysis: ClinicalAnalysisOutput = dspy.OutputField(
        desc=(
            "Return JSON matching ClinicalAnalysisOutput: executive_summary, patient_profile, "
            "timeline, appropriateness, recommendations, confidence."
        )
    )


class MedicationAnalysis(dspy.Signature):
    """You are a medication analysis agent.
    Task: evaluate interactions, safety, therapeutic appropriateness, adherence, and pharmacoeconomics.
    Context: UAE considerations (Ramadan dosing/timing, formulary restrictions, climate/storage, cultural preferences).
    Output: summary, interactions (with severity), safety assessment, appropriateness, recommendations, confidence (1–10).
    """

    patient_data: Dict[str, Any] = dspy.InputField(desc=PATIENT_DATA_DESC)
    medication_analysis: MedicationAnalysisOutput = dspy.OutputField(
        desc=(
            "Return JSON matching MedicationAnalysisOutput: summary, interactions, safety, "
            "appropriateness, recommendations, confidence."
        )
    )


class RiskAssessment(dspy.Signature):
    """You are a clinical risk assessor.
    Task: stratify risk, identify safety concerns, analyze risk‑benefit, and propose mitigation.
    Context: UAE population risk factors (heat, dust, occupation), cultural adherence, seasonal variations.
    """

    patient_data: Dict[str, Any] = dspy.InputField(desc=PATIENT_DATA_DESC)
    clinical_analysis: str = dspy.InputField(desc="Previous clinical analysis (JSON)")
    medication_analysis: str = dspy.InputField(
        desc="Previous medication analysis (JSON)"
    )
    risk_assessment: RiskAssessmentOutput = dspy.OutputField(
        desc=(
            "Return JSON matching RiskAssessmentOutput: overall_level, drivers, safety_concerns, "
            "risk_benefit, mitigation, confidence."
        )
    )


class AuthorizationDecision(dspy.Signature):
    """You are the authorization decision maker.
    Task: synthesize all analyses; determine APPROVED/DENIED/REQUIRES_REVIEW with rationale and citations.
    Context: UAE DHA/DOH regulatory standards, essential benefits, cultural/religious considerations.
    """

    patient_data: Dict[str, Any] = dspy.InputField(desc=PATIENT_DATA_DESC)
    clinical_analysis: str = dspy.InputField(desc="Clinical analysis (JSON)")
    medication_analysis: str = dspy.InputField(desc="Medication analysis (JSON)")
    risk_assessment: str = dspy.InputField(desc="Risk assessment (JSON)")
    authorization_decision: AuthorizationDecisionOutput = dspy.OutputField(
        desc=(
            "Return JSON matching AuthorizationDecisionOutput: decision, confidence, rationale, citations, conditions."
        )
    )


class ComplianceAudit(dspy.Signature):
    """You are a compliance auditor.
    Task: audit documentation completeness, policy adherence, regulatory compliance, and quality of reasoning.
    Context: UAE PDPL, DHA/DOH requirements, audit trail expectations.
    """

    patient_data: Dict[str, Any] = dspy.InputField(desc=PATIENT_DATA_DESC)
    clinical_analysis: str = dspy.InputField(desc="Clinical analysis to audit (JSON)")
    medication_analysis: str = dspy.InputField(
        desc="Medication analysis to audit (JSON)"
    )
    risk_assessment: str = dspy.InputField(desc="Risk assessment to audit (JSON)")
    authorization_decision: str = dspy.InputField(
        desc="Authorization decision to audit (JSON)"
    )
    compliance_audit: ComplianceAuditOutput = dspy.OutputField(
        desc=(
            "Return JSON matching ComplianceAuditOutput: score, documentation, policy_adherence, "
            "regulatory_status, quality_assurance, recommendations."
        )
    )


# -----------------------------
# LLM Modules signatures
# -----------------------------
class SpecialtyDeterminationSignature(dspy.Signature):
    """Determine medical specialty from patient data and requested services."""

    patient_data = dspy.InputField(desc="Patient demographics and clinical data")
    requested_services = dspy.InputField(desc="Requested medical services")
    specialty: SpecialtyOutput = dspy.OutputField(desc="Determined medical specialty")


class FinalReportSignature(dspy.Signature):
    """Generate a comprehensive final report with rationale from decision data and agent results."""

    decision_data = dspy.InputField(desc="Context and decision data")
    agent_results = dspy.InputField(desc="All agent analysis results")
    final_report: FinalReportOutput = dspy.OutputField(
        desc="Comprehensive final report output"
    )


class ClinicalRiskSignature(dspy.Signature):
    """Assess clinical risk from recent timeline, medications, and demographics."""

    timeline: List[Dict[str, Any]] = dspy.InputField(
        desc="Recent clinical observations/events"
    )
    medications: List[Dict[str, Any]] = dspy.InputField(
        desc="Current and recent medications list"
    )
    demographics: Dict[str, Any] = dspy.InputField(
        desc="Patient demographics including age and gender"
    )
    clinical_risk: ClinicalRiskOutput = dspy.OutputField(
        desc="JSON matching ClinicalRiskOutput: overall_risk, risk_factors, confidence, reasoning."
    )


class DataQualitySignature(dspy.Signature):
    """Assess data quality (completeness, richness, accuracy) and provide recommendations."""

    demographics: Dict[str, Any] = dspy.InputField(
        desc="Patient demographics for completeness check"
    )


# -----------------------------
# Evidence Retrieval (ReAct) signature
# -----------------------------
class EvidenceRetrievalSignature(dspy.Signature):
    """You are an evidence selection assistant for prior authorization.
    Task: read full policy/KB documents using available tools based on the inputs and patient context and return at most 2 concise excerpts
    that best justify coverage criteria for the request.
    Inputs include the raw patient context and an already prepared clinical summary.
    Rules:
    - Choose tools judiciously; avoid redundant calls
    - Prefer exact payer policy YAML for the relevant request category when applicable
    - Output must be a small JSON object with up to 2 evidence items
    """

    patient_data: Dict[str, Any] = dspy.InputField(desc=PATIENT_DATA_DESC)
    clinical_summary: Dict[str, Any] = dspy.InputField(desc="Structured clinical summary (executive_summary, recommendations, etc.)")
    evidence: EvidenceRetrievalOutput = dspy.OutputField(
        desc=(
            "Return JSON matching EvidenceRetrievalOutput: evidence list with up to 2 items, each with source and snippet."
        )
    )


class PolicyEvaluationSignature(dspy.Signature):
    """You are a policy evaluation specialist for prior authorization.
    Task: evaluate policy criteria against patient case data with strict schema output.
    Context: UAE healthcare policies, DHA/DOH regulatory standards, evidence-based coverage criteria.
    Rules:
    - Evaluate each policy criterion as "met", "unmet", or "uncertain"
    - Provide detailed rationale with specific patient facts supporting your assessment
    - Always cite specific filename/section from provided evidence
    - Calculate overall compliance score as percentage of met criteria
    - Identify missing documentation needed for uncertain criteria
    Output: structured checklist with criteria evaluations, rationale, citations, and missing documents.
    """

    patient_data: Dict[str, Any] = dspy.InputField(desc=PATIENT_DATA_DESC)
    clinical_summary: Dict[str, Any] = dspy.InputField(desc="Structured clinical summary from previous analysis")
    evidence: List[Dict[str, Any]] = dspy.InputField(desc="Retrieved policy excerpts with source/snippet structure")
    policy_checklist: PolicyChecklistOutput = dspy.OutputField(
        desc=(
            "Return JSON matching PolicyChecklistOutput: criteria (list of PolicyCriteriaItem), "
            "missing_documents (list), overall_compliance_score (float 0.0-1.0), policy_source (string)."
        )
    )
