enum RiskLevel {
  LOW
  MODERATE
  HIGH
  CRITICAL
}

class ClinicalRiskAssessment {
  overall_risk RiskLevel @description("Overall clinical risk level based on patient data")
  risk_factors string[] @description("List of identified risk factors")
  confidence float @description("Confidence score from 0.0 to 1.0")
  reasoning string @description("Detailed clinical reasoning for the risk assessment")
}

function AssessClinicalRisk(
  demographics: string,
  recent_observations: string,
  current_medications: string,
  observation_count: int,
  medication_count: int
) -> ClinicalRiskAssessment {
  client "openai/gpt-4o-mini"
  prompt #"
    You are a clinical risk assessment specialist. Analyze the provided patient data to determine clinical risk level.

    Consider these key factors:
    - Patient demographics (age, gender, chronic conditions)
    - Recent clinical observations and lab values
    - Current medication regimen and potential interactions
    - Data completeness and clinical complexity
    - Risk of complications or adverse events

    Risk Level Guidelines:
    - LOW: Stable patient, routine care, minimal risk factors
    - MODERATE: Some risk factors present, requires monitoring
    - HIGH: Multiple risk factors, complex medical history, needs careful management
    - CRITICAL: Immediate concerns, multiple high-risk factors, urgent intervention may be needed

    Provide specific risk factors identified and detailed clinical reasoning.

    {{ ctx.output_format }}

    {{ _.role("user") }}

    ## Patient Data Analysis

    ### Demographics
    {{ demographics }}

    ### Recent Clinical Observations ({{ observation_count }} total)
    {{ recent_observations }}

    ### Current Medications ({{ medication_count }} total)
    {{ current_medications }}

    {{ ctx.output_format }}
  "#
}

// Tests can be added later in BAML playground