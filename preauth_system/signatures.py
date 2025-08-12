"""
Shared DSPy Signature Classes for Pre-Authorization Agents
Prevents code duplication across agent files
"""
import dspy
from typing import Dict, Any, List, Optional, TypedDict
from pydantic import BaseModel

# Reuse the exact same description string across all signatures
PATIENT_DATA_DESC = (
    "Structured patient context including demographics, medical_history, "
    "clinical_data (symptoms, labs, vitals), and requested_treatment."
)


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
    content: Optional[str] = None


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
    Output: overall risk level, key drivers, safety concerns/contraindications, risk‑benefit, mitigation recommendations.
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
    Output: decision, confidence (1–10), clinical rationale, policy citations, conditions/limitations (if any).
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
    Output: overall compliance score (0–100), documentation, policy_adherence, regulatory_status, QA findings, recommendations.
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
    timeline: List[Dict[str, Any]] = dspy.InputField(
        desc="Clinical timeline/observations"
    )
    medications: List[Dict[str, Any]] = dspy.InputField(desc="Medication history")
    data_quality: DataQualityOutput = dspy.OutputField(
        desc=(
            "JSON matching DataQualityOutput: overall_score, completeness_score, richness_score, "
            "accuracy_score, recommendations, reasoning."
        )
    )
