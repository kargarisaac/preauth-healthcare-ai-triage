// Healthcare FHIR-compliant models for UAE insurance validation

// Core money representation for healthcare claims
class MoneyAmount {
  value float
  currency string @description("Currency code (AED, USD, etc.)")
}

// Medical coding systems used in UAE healthcare
enum CodingSystem {
  ICD_10_AM @description("ICD-10-AM used in UAE")
  CPT @description("Current Procedural Terminology")
  SNOMED_CT @description("Systematized Nomenclature of Medicine Clinical Terms")
  LOINC @description("Logical Observation Identifiers Names and Codes")
  DHA_LOCAL @description("Dubai Health Authority local codes")
  DOH_LOCAL @description("Abu Dhabi Department of Health local codes")
  UNKNOWN
}

// Medical code with validation support
class MedicalCode {
  code string
  system CodingSystem
  display string?
  version string?
}

// UAE healthcare providers and payers
enum UAEHealthcareEntity {
  DHA @description("Dubai Health Authority")
  DOH_AD @description("Abu Dhabi Department of Health")
  MOHAP @description("Ministry of Health and Prevention")
  SEHA @description("SEHA Health System")
  DHA_INSURANCE @description("DHA Insurance companies")
  PRIVATE_INSURANCE @description("Private insurance providers")
  UNKNOWN
}

// FHIR Bundle structure for healthcare data
class HealthcareBundle {
  resourceType string @description("Always 'Bundle' for FHIR compliance")
  id string?
  meta BundleMeta?
  identifier BundleIdentifier?
  type string @description("Bundle type: document, message, transaction, etc.")
  timestamp string? @description("ISO 8601 timestamp")
  total int? @description("Number of resources in bundle")

  // Essential UAE healthcare fields
  authorization_id string?
  sender UAEHealthcareEntity?
  receiver UAEHealthcareEntity?

  // FHIR resources
  entry BundleEntry[]

  // Preserve original data
  raw_data map<string, string>? @description("Original XML/CSV data preserved")
  processing_metadata ProcessingMetadata?
}

class BundleMeta {
  lastUpdated string? @description("ISO 8601 timestamp")
  profile string[]? @description("FHIR profiles this bundle conforms to")
  source string? @description("Source system URI")
  tag Coding[]? @description("Tags applied to this bundle")
}

class BundleIdentifier {
  use string? @description("usual | official | temp | secondary")
  type CodeableConcept?
  system string? @description("Namespace for the identifier")
  value string @description("The identifier value")
  period Period?
}

class BundleEntry {
  id string?
  resource FHIRResource
  fullUrl string? @description("Absolute URL for the resource")
  search EntrySearch?
  request EntryRequest?
  response EntryResponse?
}

class Period {
  start string? @description("ISO 8601 start date")
  end string? @description("ISO 8601 end date")
}

class CodeableConcept {
  coding Coding[]?
  text string?
}

class Coding {
  system string?
  version string?
  code string?
  display string?
  userSelected bool?
}

class EntrySearch {
  mode string? @description("match | include | outcome")
  score float?
}

class EntryRequest {
  method string @description("GET | HEAD | POST | PUT | DELETE | PATCH")
  url string
  ifNoneMatch string?
  ifModifiedSince string?
  ifMatch string?
  ifNoneExist string?
}

class EntryResponse {
  status string @description("HTTP response status")
  location string?
  etag string?
  lastModified string?
  outcome OperationOutcome?
}

class OperationOutcome {
  resourceType string @description("Always 'OperationOutcome'")
  issue OutcomeIssue[]
}

class OutcomeIssue {
  severity string @description("fatal | error | warning | information")
  code string
  details CodeableConcept?
  diagnostics string?
  location string[]?
  expression string[]?
}

// FHIR Resource union type for different resource types
class FHIRResource {
  resourceType string
  id string?
  meta ResourceMeta?
  implicitRules string?
  language string?

  // Resource-specific data (varies by resourceType)
  data map<string, string> @description("Resource-specific fields as key-value pairs")
}

class ResourceMeta {
  versionId string?
  lastUpdated string?
  source string?
  profile string[]?
  security Coding[]?
  tag Coding[]?
}

// Specific FHIR resource types for healthcare
class ClaimResource {
  resourceType string @description("Always 'Claim'")
  id string?
  status string @description("active | cancelled | draft | entered-in-error")
  type CodeableConcept @description("Claim type (institutional, professional, etc.)")
  use string @description("claim | preauthorization | predetermination")

  patient Reference @description("Patient reference")
  created string @description("ISO 8601 creation date")
  insurer Reference @description("Target insurer")
  provider Reference @description("Provider responsible for claim")

  priority CodeableConcept? @description("Processing priority")
  fundsReserve CodeableConcept? @description("Funds requested to be reserved")

  // UAE specific fields
  authorization_id string?
  emirate string? @description("UAE Emirate where service provided")

  related ClaimRelated[]?
  payee ClaimPayee?
  referral Reference?
  facility Reference?
  careTeam ClaimCareTeam[]?
  supportingInfo ClaimSupportingInfo[]?
  diagnosis ClaimDiagnosis[]?
  procedure ClaimProcedure[]?
  insurance ClaimInsurance[]
  item ClaimItem[]?
  total MoneyAmount?
}

class Reference {
  reference string?
  type string?
  identifier Identifier?
  display string?
}

class Identifier {
  use string?
  type CodeableConcept?
  system string?
  value string
  period Period?
  assigner Reference?
}

class ClaimRelated {
  claim Reference?
  relationship CodeableConcept?
  reference Identifier?
}

class ClaimPayee {
  type CodeableConcept
  party Reference?
}

class ClaimCareTeam {
  sequence int
  provider Reference
  responsible bool?
  role CodeableConcept?
  qualification CodeableConcept?
}

class ClaimSupportingInfo {
  sequence int
  category CodeableConcept
  code CodeableConcept?
  timing_date string? @description("ISO 8601 date")
  timing_period Period?
  value_boolean bool?
  value_string string?
  value_quantity Quantity?
  value_attachment Attachment?
  value_reference Reference?
  reason Coding?
}

class Quantity {
  value float?
  comparator string? @description("< | <= | >= | >")
  unit string?
  system string?
  code string?
}

class Attachment {
  contentType string?
  language string?
  data string? @description("Base64 encoded data")
  url string?
  size int?
  hash string?
  title string?
  creation string? @description("ISO 8601 date")
}

class ClaimDiagnosis {
  sequence int
  diagnosis_codeable_concept CodeableConcept?
  diagnosis_reference Reference?
  type CodeableConcept[]?
  on_admission CodeableConcept?
  package_code CodeableConcept?
}

class ClaimProcedure {
  sequence int
  type CodeableConcept[]?
  date string? @description("ISO 8601 date")
  procedure_codeable_concept CodeableConcept?
  procedure_reference Reference?
  udi Reference[]?
}

class ClaimInsurance {
  sequence int
  focal bool
  identifier Identifier?
  coverage Reference
  business_arrangement string?
  pre_auth_ref string[]?
  claim_response Reference?
}

class ClaimItem {
  sequence int
  care_team_sequence int[]?
  diagnosis_sequence int[]?
  procedure_sequence int[]?
  information_sequence int[]?
  revenue CodeableConcept?
  category CodeableConcept?
  product_or_service CodeableConcept
  modifier CodeableConcept[]?
  program_code CodeableConcept[]?

  serviced_date string? @description("ISO 8601 date")
  serviced_period Period?
  location_codeable_concept CodeableConcept?
  location_address Address?
  location_reference Reference?

  quantity Quantity?
  unit_price MoneyAmount?
  factor float?
  net MoneyAmount?
  udi Reference[]?
  body_site CodeableConcept[]?
  sub_site CodeableConcept[]?
  encounter Reference[]?
  detail ClaimItemDetail[]?
}

class Address {
  use string? @description("home | work | temp | old | billing")
  type string? @description("postal | physical | both")
  text string?
  line string[]?
  city string?
  district string?
  state string?
  postalCode string?
  country string?
  period Period?
}

class ClaimItemDetail {
  sequence int
  revenue CodeableConcept?
  category CodeableConcept?
  product_or_service CodeableConcept
  modifier CodeableConcept[]?
  program_code CodeableConcept[]?
  quantity Quantity?
  unit_price MoneyAmount?
  factor float?
  net MoneyAmount?
  udi Reference[]?
  sub_detail ClaimItemSubDetail[]?
}

class ClaimItemSubDetail {
  sequence int
  revenue CodeableConcept?
  category CodeableConcept?
  product_or_service CodeableConcept
  modifier CodeableConcept[]?
  program_code CodeableConcept[]?
  quantity Quantity?
  unit_price MoneyAmount?
  factor float?
  net MoneyAmount?
  udi Reference[]?
}

// Observation resource for clinical data
class ObservationResource {
  resourceType string @description("Always 'Observation'")
  id string?
  status string @description("registered | preliminary | final | amended | corrected | cancelled | entered-in-error | unknown")
  category CodeableConcept[]?
  code CodeableConcept @description("Type of observation")

  subject Reference @description("Patient reference")
  encounter Reference?
  effective_date_time string? @description("ISO 8601 datetime")
  effective_period Period?

  issued string? @description("ISO 8601 datetime when result was issued")
  performer Reference[]?

  value_quantity Quantity?
  value_codeable_concept CodeableConcept?
  value_string string?
  value_boolean bool?
  value_integer int?
  value_range Range?
  value_ratio Ratio?
  value_sampled_data SampledData?
  value_time string?
  value_date_time string?
  value_period Period?

  data_absent_reason CodeableConcept?
  interpretation CodeableConcept[]?
  note Annotation[]?
  body_site CodeableConcept?
  method CodeableConcept?
  specimen Reference?
  device Reference?
  reference_range ObservationReferenceRange[]?
  has_member Reference[]?
  derived_from Reference[]?
  component ObservationComponent[]?
}

class Range {
  low Quantity?
  high Quantity?
}

class Ratio {
  numerator Quantity?
  denominator Quantity?
}

class SampledData {
  origin Quantity
  period float
  factor float?
  lower_limit float?
  upper_limit float?
  dimensions int
  data string?
}

class Annotation {
  author_reference Reference?
  author_string string?
  time string? @description("ISO 8601 datetime")
  text string
}

class ObservationReferenceRange {
  low Quantity?
  high Quantity?
  type CodeableConcept?
  applies_to CodeableConcept[]?
  age Range?
  text string?
}

class ObservationComponent {
  code CodeableConcept
  value_quantity Quantity?
  value_codeable_concept CodeableConcept?
  value_string string?
  value_boolean bool?
  value_integer int?
  value_range Range?
  value_ratio Ratio?
  value_sampled_data SampledData?
  value_time string?
  value_date_time string?
  value_period Period?

  data_absent_reason CodeableConcept?
  interpretation CodeableConcept[]?
  reference_range ObservationReferenceRange[]?
}

// Service activity for procedure tracking
class ServiceActivity {
  id string
  type string @description("procedure | medication | observation | diagnostic")
  code MedicalCode
  description string?
  status string @description("planned | in-progress | completed | cancelled")

  patient_reference string
  performer_reference string?
  encounter_reference string?

  performed_date string? @description("ISO 8601 date")
  performed_period Period?

  location string?
  outcome CodeableConcept?
  notes string?

  // UAE specific
  emirate string?
  facility_license string?
  provider_license string?
}

// Processing metadata
class ProcessingMetadata {
  processed_at string @description("ISO 8601 timestamp")
  processor_version string?
  source_format string @description("xml | csv | json")
  source_system string? @description("eClaimLink | Shafafiya | CSV")

  warnings ProcessingWarning[]?
  errors ProcessingError[]?

  // Data quality metrics
  completeness_score float? @description("0.0 to 1.0")
  validity_score float? @description("0.0 to 1.0")
  consistency_score float? @description("0.0 to 1.0")

  total_records int?
  processed_records int?
  failed_records int?
}

class ProcessingWarning {
  code string
  message string
  field string?
  severity string @description("low | medium | high")
}

class ProcessingError {
  code string
  message string
  field string?
  value string?
  severity string @description("error | critical")
}

// Data quality assessment structures
enum ValidationSeverity {
  INFO
  WARNING
  ERROR
  CRITICAL
}

enum ValidationType {
  COMPLIANCE @description("UAE healthcare compliance rules")
  CLINICAL @description("Medical logic and relationships")
  DATA_QUALITY @description("Data consistency and completeness")
  CODE_VALIDATION @description("Medical code verification")
}

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

class DataQualityReport {
  bundle_id string?
  assessed_at string @description("ISO 8601 timestamp")

  quality_score QualityScore
  validation_issues ValidationIssue[]

  summary DataQualitySummary
  recommendations string[]?

  // Processing context
  total_resources int
  resources_assessed int
  assessment_duration_ms int?
}

class DataQualitySummary {
  total_records int
  valid_records int
  invalid_records int

  // Field-level analysis
  required_fields_missing int
  invalid_formats int
  inconsistent_references int

  // UAE healthcare specific
  missing_authorization_ids int
  invalid_emirates int
  unlicensed_providers int

  // Medical coding issues
  invalid_icd_codes int
  invalid_cpt_codes int
  deprecated_codes int
}

// LLM input structure
class DataSample {
  resource_type string @description("Type of healthcare resource")
  raw_data string @description("Raw data to validate (JSON, XML, or CSV excerpt)")
  context DataContext? @description("Additional context for validation")
}

class DataContext {
  source_system string? @description("eClaimLink | Shafafiya | CSV")
  emirate string? @description("UAE Emirate context")
  provider_type string? @description("hospital | clinic | pharmacy | lab")
  patient_category string? @description("national | resident | visitor")

  // Additional context for validation
  processing_date string? @description("ISO 8601 date")
  claim_type string? @description("institutional | professional | pharmacy | vision | dental")
}

// LLM validation output structures
class LLMValidationResult {
  validation_passed bool
  confidence_score float @description("0.0 to 1.0")

  issues ValidationIssue[]
  quality_metrics map<string, float> @description("Specific quality metrics")

  processing_time_ms int?
  model_used string?
}

class UIFriendlyReport {
  status string @description("pass | warning | fail")
  summary string @description("Brief human-readable summary")

  score QualityScore
  issues_by_severity map<string, ValidationIssue[]> @description("Issues grouped by severity")

  actionable_items ActionableItem[]
  next_steps string[]?
}

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
