// Healthcare validation and reporting models (pruned)

// Context information accompanying data samples
class DataContext {
  source_system string? @description("eClaimLink | Shafafiya | CSV")
  emirate string? @description("UAE Emirate context")
  provider_type string? @description("hospital | clinic | pharmacy | lab")
  patient_category string? @description("national | resident | visitor")

  // Additional context for validation
  processing_date string? @description("ISO 8601 date")
  claim_type string? @description("institutional | professional | pharmacy | vision | dental")
}

// Input sample for validation
class DataSample {
  resource_type string @description("Type of healthcare resource")
  raw_data string @description("Raw data to validate (JSON, XML, or CSV excerpt)")
  context DataContext? @description("Additional context for validation")
}

// Core validation output
class ValidationResult {
  overall_quality_score float @description("Overall data quality score 0.0-1.0")
  confidence_score float @description("LLM confidence in analysis 0.0-1.0")

  validation_passed bool @description("Whether data passes basic quality checks")

  // Issue summary
  critical_issues int @description("Number of critical issues found")
  warning_issues int @description("Number of warning issues found")
  info_issues int @description("Number of informational findings")

  // Top issues for actionable feedback
  top_issues string[] @description("Top 3-5 most important issues to address")
  recommendations string[] @description("Specific actionable recommendations")

  // Processing metadata
  processing_time_ms int @description("Processing time in milliseconds")
  model_used string @description("LLM model used for validation")

  // Optional detailed reasoning for transparency
  reasoning string? @description("Brief explanation of validation approach")
}

// Severity of validation issue
enum ValidationSeverity {
  INFO
  WARNING
  ERROR
  CRITICAL
}

// Type/category of validation issue
enum ValidationType {
  COMPLIANCE @description("UAE healthcare compliance rules")
  CLINICAL @description("Medical logic and relationships")
  DATA_QUALITY @description("Data consistency and completeness")
  CODE_VALIDATION @description("Medical code verification")
}

// Individual validation issue
class ValidationIssue {
  id string
  type ValidationType
  severity ValidationSeverity
  code string @description("Issue code for categorization")
  message string @description("Human-readable description")

  field_path string? @description("JSON path to problematic field")
  expected_value string?
  actual_value string?

  resource_type string? @description("FHIR resource type affected")
  resource_id string?

  suggestions string[]? @description("Recommended fixes")

  // UAE specific context
  regulation_reference string? @description("UAE regulation reference")
  emirate_specific bool? @description("Emirate-specific rule")
}

// Overall quality scoring
class QualityScore {
  overall_score float @description("0.0 to 1.0")

  compliance_score float @description("UAE healthcare compliance")
  clinical_logic_score float @description("Medical relationships validity")
  data_completeness_score float @description("Required fields present")
  code_validity_score float @description("Medical codes are valid")

  total_issues int
  critical_issues int
  error_issues int
  warning_issues int
  info_issues int
}

// Actionable item presented to user
class ActionableItem {
  priority string @description("high | medium | low")
  category string @description("compliance | clinical | data_quality | coding")
  title string
  description string
  fix_suggestion string?
  estimated_effort string? @description("quick | moderate | extensive")

  affected_fields string[]?
  regulation_reference string?
}

// UI ready report combining scores and issues
class UIFriendlyReport {
  status string @description("pass | warning | fail")
  summary string @description("Brief human-readable summary")

  score QualityScore
  issues_by_severity map<string, ValidationIssue[]> @description("Issues grouped by severity")

  actionable_items ActionableItem[]
  next_steps string[]?
}
