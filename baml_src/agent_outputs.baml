// BAML functions for structured agent outputs in Pre-Authorization LangGraph workflow
// Provides type-safe, validated responses from Claude Code agents

// Enums for standardized values
enum DecisionType {
  APPROVED
  DENIED
  REQUIRES_REVIEW
  PENDING_INFO
}

enum RiskLevel {
  LOW
  MODERATE
  HIGH
  CRITICAL
}

enum ComplianceStatus {
  COMPLIANT
  NON_COMPLIANT
  NEEDS_REVIEW
  MISSING_INFO
}

// Clinical Analysis Output
class ClinicalFinding {
  condition string
  severity string
  status string  // "active", "resolved", "chronic"
  evidence string[]
  relevant_history string[]
}

class ClinicalAnalysisOutput {
  summary string
  key_findings ClinicalFinding[]
  disease_progression string
  current_health_status string
  clinical_necessity_score float  // 0.0 to 1.0
  supporting_evidence string[]
  concerns string[]
  recommendations string[]
}

function ExtractClinicalAnalysis(
  agent_response: string
) -> ClinicalAnalysisOutput {
  client CustomSonnet
  prompt #"
    You are parsing the output from a clinical analyzer agent. Extract structured information from the following medical analysis response.

    AGENT RESPONSE:
    {{ agent_response }}

    Parse this response and extract:
    1. A concise summary of the clinical analysis
    2. Key medical findings with conditions, severity, and status
    3. Assessment of disease progression
    4. Current health status evaluation
    5. Clinical necessity score (0.0 to 1.0, where 1.0 = absolutely necessary)
    6. Supporting evidence for medical necessity
    7. Clinical concerns identified
    8. Medical recommendations

    Ensure all extracted information is medically accurate and follows UAE healthcare standards.
    For clinical necessity score, consider:
    - Severity of condition
    - Medical urgency
    - Evidence-based need for intervention
    - Risk of delayed treatment

    Return a structured ClinicalAnalysisOutput object.
  "#
}

// Medication Analysis Output
class DrugInteraction {
  drug1 string
  drug2 string
  severity string  // "minor", "moderate", "major", "contraindicated"
  description string
  management_strategy string
}

class MedicationSafety {
  drug_name string
  contraindications string[]
  warnings string[]
  monitoring_required string[]
  dosage_concerns string[]
}

class MedicationAnalysisOutput {
  summary string
  current_medications string[]
  drug_interactions DrugInteraction[]
  safety_concerns MedicationSafety[]
  medication_necessity_score float  // 0.0 to 1.0
  therapeutic_alternatives string[]
  cost_effectiveness_notes string[]
  monitoring_recommendations string[]
}

function ExtractMedicationAnalysis(
  agent_response: string
) -> MedicationAnalysisOutput {
  client CustomSonnet
  prompt #"
    You are parsing medication specialist analysis. Extract structured information about drug interactions, safety, and necessity.

    AGENT RESPONSE:
    {{ agent_response }}

    Extract:
    1. Summary of medication analysis
    2. List of current medications being reviewed
    3. Drug interactions with severity and management
    4. Safety concerns for each medication
    5. Medication necessity score (0.0 to 1.0)
    6. Alternative therapeutic options
    7. Cost-effectiveness considerations
    8. Required monitoring protocols

    For medication necessity score, consider:
    - Evidence-based therapeutic benefit
    - Risk-benefit ratio
    - Availability of alternatives
    - Patient-specific factors

    Return structured MedicationAnalysisOutput object.
  "#
}

// Risk Assessment Output
class RiskFactor {
  factor string
  impact_level string  // "low", "moderate", "high"
  likelihood string    // "rare", "possible", "likely", "very_likely"
  mitigation_strategy string
}

class OutcomePrediction {
  scenario string
  probability float  // 0.0 to 1.0
  timeframe string
  clinical_impact string
}

class RiskAssessmentOutput {
  summary string
  overall_risk_level RiskLevel
  risk_factors RiskFactor[]
  outcome_predictions OutcomePrediction[]
  cost_benefit_analysis string
  recommended_monitoring string[]
  risk_mitigation_strategies string[]
  follow_up_requirements string[]
}

function ExtractRiskAssessment(
  agent_response: string
) -> RiskAssessmentOutput {
  client CustomSonnet
  prompt #"
    Parse risk assessor analysis to extract structured risk stratification and outcome predictions.

    AGENT RESPONSE:
    {{ agent_response }}

    Extract:
    1. Summary of risk assessment
    2. Overall risk level (LOW, MODERATE, HIGH, CRITICAL)
    3. Specific risk factors with impact and likelihood
    4. Predicted outcomes with probabilities
    5. Cost-benefit analysis summary
    6. Monitoring recommendations
    7. Risk mitigation strategies
    8. Follow-up requirements

    For overall risk level:
    - LOW: Minimal risk, standard care sufficient
    - MODERATE: Some risk factors, enhanced monitoring
    - HIGH: Significant risk, intensive management needed
    - CRITICAL: Immediate intervention required

    Return structured RiskAssessmentOutput object.
  "#
}

// Decision Making Output
class AuthorizationRationale {
  medical_necessity string
  clinical_evidence string[]
  cost_justification string
  alternative_analysis string
  risk_benefit_summary string
}

class DecisionMakingOutput {
  summary string
  decision_recommendation DecisionType
  confidence_score float  // 0.0 to 1.0
  authorization_rationale AuthorizationRationale
  conditions_for_approval string[]
  monitoring_requirements string[]
  duration_of_authorization int?  // days
  cost_analysis string
  appeals_considerations string[]
}

function ExtractDecisionMaking(
  agent_response: string
) -> DecisionMakingOutput {
  client CustomSonnet
  prompt #"
    Parse decision maker analysis to extract authorization recommendation and rationale.

    AGENT RESPONSE:
    {{ agent_response }}

    Extract:
    1. Summary of decision analysis
    2. Authorization recommendation (APPROVED, DENIED, REQUIRES_REVIEW, PENDING_INFO)
    3. Confidence score in the decision (0.0 to 1.0)
    4. Detailed rationale including medical necessity and evidence
    5. Conditions that must be met for approval
    6. Required monitoring protocols
    7. Duration of authorization in days (if applicable)
    8. Cost analysis summary
    9. Considerations for potential appeals

    Decision mapping:
    - APPROVED: Clear medical necessity, low risk, cost-effective
    - DENIED: Insufficient medical necessity or high risk
    - REQUIRES_REVIEW: Complex case needing additional review
    - PENDING_INFO: Missing critical information for decision

    Return structured DecisionMakingOutput object.
  "#
}

// Compliance Audit Output
class ComplianceCheck {
  regulation string
  status ComplianceStatus
  requirements string[]
  gaps_identified string[]
  remediation_needed string[]
}

class DocumentationRequirement {
  document_type string
  required bool
  provided bool
  quality_assessment string
  action_needed string
}

class ComplianceAuditOutput {
  summary string
  overall_compliance_status ComplianceStatus
  uae_regulatory_checks ComplianceCheck[]
  documentation_review DocumentationRequirement[]
  policy_adherence_score float  // 0.0 to 1.0
  compliance_gaps string[]
  remediation_actions string[]
  audit_recommendations string[]
}

function ExtractComplianceAudit(
  agent_response: string
) -> ComplianceAuditOutput {
  client CustomSonnet
  prompt #"
    Parse compliance auditor analysis to extract UAE regulatory compliance assessment.

    AGENT RESPONSE:
    {{ agent_response }}

    Extract:
    1. Summary of compliance audit
    2. Overall compliance status (COMPLIANT, NON_COMPLIANT, NEEDS_REVIEW, MISSING_INFO)
    3. UAE regulatory checks with specific requirements
    4. Documentation review and requirements
    5. Policy adherence score (0.0 to 1.0)
    6. Identified compliance gaps
    7. Required remediation actions
    8. Audit recommendations

    UAE Regulatory Focus Areas:
    - Dubai Health Authority (DHA) requirements
    - Abu Dhabi Department of Health regulations
    - Insurance coverage guidelines
    - Medical necessity criteria
    - Documentation standards
    - Prior authorization protocols

    Return structured ComplianceAuditOutput object.
  "#
}

// Final Decision Integration
class FinalAuthorizationDecision {
  decision DecisionType
  confidence_score float
  authorization_number string?
  valid_duration_days int?
  conditions string[]
  monitoring_plan string[]
  cost_summary string
  appeal_rights string
  effective_date string?
  review_date string?
}

function IntegrateFinalDecision(
  clinical_analysis: ClinicalAnalysisOutput,
  medication_analysis: MedicationAnalysisOutput,
  risk_assessment: RiskAssessmentOutput,
  decision_making: DecisionMakingOutput,
  compliance_audit: ComplianceAuditOutput
) -> FinalAuthorizationDecision {
  client CustomGPT4o
  prompt #"
    You are integrating all agent analyses to make a final pre-authorization decision for UAE healthcare.

    CLINICAL ANALYSIS:
    {{ clinical_analysis }}

    MEDICATION ANALYSIS:
    {{ medication_analysis }}

    RISK ASSESSMENT:
    {{ risk_assessment }}

    DECISION MAKING:
    {{ decision_making }}

    COMPLIANCE AUDIT:
    {{ compliance_audit }}

    Based on all these analyses, determine the final authorization decision considering:

    1. Medical necessity (clinical + medication necessity scores)
    2. Risk-benefit analysis (risk level + outcome predictions)
    3. UAE regulatory compliance (compliance status + gaps)
    4. Cost-effectiveness (cost analysis from all agents)
    5. Safety considerations (drug interactions + risk factors)

    DECISION CRITERIA:
    - APPROVED: High medical necessity, acceptable risk, compliant, cost-effective
    - DENIED: Low medical necessity, high risk, non-compliant, or cost-prohibitive
    - REQUIRES_REVIEW: Borderline case, complex factors, or significant compliance gaps
    - PENDING_INFO: Missing critical information for proper assessment

    Generate authorization number format: AUTH-UAE-YYYYMMDD-XXXX
    Standard authorization duration: 90 days (adjust based on condition)

    Return comprehensive FinalAuthorizationDecision with all required elements.
  "#
}