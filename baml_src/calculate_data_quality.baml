class DataQualityAssessment {
  overall_score float @description("Overall data quality score from 0.0 to 1.0")
  completeness_score float @description("Completeness score from 0.0 to 1.0")
  richness_score float @description("Clinical data richness score from 0.0 to 1.0")
  accuracy_score float @description("Data accuracy and consistency score from 0.0 to 1.0")
  recommendations string[] @description("List of recommendations to improve data quality")
  reasoning string @description("Detailed reasoning for the quality assessment")
}

function CalculateDataQuality(
  demographics_completeness: string,
  clinical_data_richness: int,
  medication_data_availability: int,
  total_data_points: int
) -> DataQualityAssessment {
  // client GPT4oMini
  // client GptOss20b
  client OpenaiFallback
  prompt #"
    You are a healthcare data quality analyst. Assess the quality of patient data for clinical decision-making.

    Evaluate these dimensions:
    1. COMPLETENESS: Are essential demographic and clinical fields populated?
    2. RICHNESS: Is there sufficient clinical history for meaningful analysis?
    3. ACCURACY: Are data points consistent and clinically plausible?
    4. TIMELINESS: Are recent observations available for current assessment?

    Scoring Guidelines (0.0 to 1.0):
    - 0.9-1.0: Excellent - Comprehensive data for confident clinical decisions
    - 0.7-0.89: Good - Sufficient data with minor gaps
    - 0.5-0.69: Fair - Adequate data but some important gaps
    - 0.3-0.49: Poor - Limited data, significant gaps affect decision-making
    - 0.0-0.29: Very Poor - Insufficient data for reliable clinical assessment

    Provide specific recommendations to improve data quality.

    {{ ctx.output_format }}

    {{ _.role("user") }}

    ## Data Quality Analysis

    ### Demographics Completeness Analysis
    {{ demographics_completeness }}

    ### Clinical Data Summary
    - Clinical observations available: {{ clinical_data_richness }}
    - Medications documented: {{ medication_data_availability }}
    - Total data points: {{ total_data_points }}

    {{ ctx.output_format }}
  "#
}

// Tests can be added later in BAML playground