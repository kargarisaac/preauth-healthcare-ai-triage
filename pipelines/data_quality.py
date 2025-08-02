"""
Data Quality Rules & Validation Engine for UAE Healthcare.

This module provides comprehensive data quality validation for healthcare data
processed through Nazmito's XML and CSV pipelines, ensuring all FHIR resources
meet clinical, business, and regulatory standards. Enhanced with LLM validation
for intelligent quality assessment.
"""

import json
import re
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from loguru import logger

# Import LLM validation components
try:
    from pipelines.llm_validator import ParallelLLMValidator
    from pipelines.llm_data_sampler import SmartDataSampler, SamplingStrategy
    from baml_client.types import ValidationType

    LLM_VALIDATION_AVAILABLE = True
except ImportError as e:
    logger.warning(f"LLM validation components not available: {e}")
    LLM_VALIDATION_AVAILABLE = False


class ValidationSeverity(Enum):
    """Validation issue severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """Represents a single validation issue."""

    severity: ValidationSeverity
    code: str
    message: str
    field_path: str
    suggested_fix: Optional[str] = None
    resource_type: Optional[str] = None


@dataclass
class QualityScore:
    """Data quality score breakdown with LLM enhancement."""

    overall_score: float
    code_validity: float
    completeness: float
    clinical_consistency: float
    format_compliance: float
    issues_count: Dict[str, int]  # Count by severity
    # LLM-enhanced scores
    llm_validation_score: Optional[float] = None
    llm_confidence_score: Optional[float] = None
    hybrid_score: Optional[float] = None  # Combined rule-based + LLM
    llm_available: bool = False


class MedicalCodeValidator:
    """Validates medical codes against standard terminologies."""

    def __init__(self):
        """Initialize medical code validation with lookup tables."""
        self._load_code_tables()

    def _load_code_tables(self):
        """Load medical code lookup tables."""
        # ICD-10 codes (sample for UAE healthcare)
        self.icd10_codes = {
            # Diabetes codes
            "E11.9": "Type 2 diabetes mellitus without complications",
            "E11.0": "Type 2 diabetes mellitus with hyperosmolarity",
            "E11.1": "Type 2 diabetes mellitus with ketoacidosis",
            "E11.2": "Type 2 diabetes mellitus with kidney complications",
            "E11.3": "Type 2 diabetes mellitus with ophthalmic complications",
            "E11.4": "Type 2 diabetes mellitus with neurological complications",
            "E11.5": "Type 2 diabetes mellitus with circulatory complications",
            "E11.6": "Type 2 diabetes mellitus with other specified complications",
            "E11.8": "Type 2 diabetes mellitus with unspecified complications",
            # Common conditions
            "M54.5": "Low back pain",
            "J45.9": "Asthma, unspecified",
            "I10": "Essential (primary) hypertension",
            "K21.9": "Gastro-esophageal reflux disease without esophagitis",
            "F32.9": "Major depressive disorder, single episode, unspecified",
            "R10.9": "Unspecified abdominal pain",
            "Z51.11": "Encounter for antineoplastic chemotherapy",
            "N39.0": "Urinary tract infection, site not specified",
        }

        # CPT codes (sample for UAE healthcare)
        self.cpt_codes = {
            # Office visits
            "99213": "Office or other outpatient visit for the evaluation and management of an established patient",
            "99214": "Office or other outpatient visit for the evaluation and management of an established patient",
            "99202": "Office or other outpatient visit for the evaluation and management of a new patient",
            "99203": "Office or other outpatient visit for the evaluation and management of a new patient",
            # Lab tests
            "83036": "Glycosylated hemoglobin (A1C)",
            "80053": "Comprehensive metabolic panel",
            "85025": "Blood count; complete (CBC), automated",
            "80061": "Lipid panel",
            "84443": "Thyroid stimulating hormone (TSH)",
            # Procedures
            "45378": "Colonoscopy, flexible; diagnostic",
            "76700": "Abdominal ultrasound, complete",
            "93000": "Electrocardiogram, routine ECG with at least 12 leads",
        }

        # LOINC codes (sample for lab tests)
        self.loinc_codes = {
            "4548-4": "Hemoglobin A1c/Hemoglobin.total in Blood",
            "2345-7": "Glucose [Mass/volume] in Serum or Plasma",
            "33747-0": "Anesthesia type",
            "8302-2": "Body height",
            "29463-7": "Body weight",
            "39156-5": "Body mass index (BMI) [Ratio]",
            "8480-6": "Systolic blood pressure",
            "8462-4": "Diastolic blood pressure",
        }

        # RxNorm codes (sample for medications)
        self.rxnorm_codes = {
            "860975": "Metformin 500 MG Oral Tablet",
            "198013": "Naproxen 250 MG",
            "1049502": "Insulin glargine 100 UNT/ML Injectable Solution",
            "617314": "Atorvastatin 20 MG Oral Tablet",
            "308136": "Lisinopril 10 MG Oral Tablet",
        }

        # SNOMED-CT codes (sample for clinical concepts)
        self.snomed_codes = {
            "271737000": "Anemia (disorder)",
            "44054006": "Type 2 diabetes mellitus (disorder)",
            "38341003": "Hypertensive disorder, systemic arterial (disorder)",
            "195967001": "Asthma (disorder)",
            "235595009": "Gastroesophageal reflux disease (disorder)",
        }

    def validate_icd10_code(self, code: str) -> Dict[str, Any]:
        """Validate ICD-10 diagnosis code."""
        if not code:
            return {"valid": False, "error": "Missing ICD-10 code"}

        # Check format (basic ICD-10 format validation)
        if not re.match(r'^[A-Z]\d{2}(\.\d{1,2})?$', code):
            return {
                "valid": False,
                "error": f"Invalid ICD-10 format: {code}",
                "suggestion": "ICD-10 codes should follow format like 'E11.9' or 'M54'",
            }

        # Check if code exists in our lookup table
        if code in self.icd10_codes:
            return {
                "valid": True,
                "description": self.icd10_codes[code],
                "code_system": "ICD-10",
            }

        return {
            "valid": False,
            "error": f"Unknown ICD-10 code: {code}",
            "suggestion": "Verify code against current ICD-10 codebook",
        }

    def validate_cpt_code(self, code: str) -> Dict[str, Any]:
        """Validate CPT procedure code."""
        if not code:
            return {"valid": False, "error": "Missing CPT code"}

        # Check format (CPT codes are 5 digits)
        if not re.match(r'^\d{5}$', code):
            return {
                "valid": False,
                "error": f"Invalid CPT format: {code}",
                "suggestion": "CPT codes should be 5 digits like '99213'",
            }

        # Check if code exists in our lookup table
        if code in self.cpt_codes:
            return {
                "valid": True,
                "description": self.cpt_codes[code],
                "code_system": "CPT",
            }

        return {
            "valid": False,
            "error": f"Unknown CPT code: {code}",
            "suggestion": "Verify code against current CPT codebook",
        }

    def validate_loinc_code(self, code: str) -> Dict[str, Any]:
        """Validate LOINC laboratory code."""
        if not code:
            return {"valid": False, "error": "Missing LOINC code"}

        # Check format (LOINC codes like "4548-4")
        if not re.match(r'^\d{4,5}-\d{1}$', code):
            return {
                "valid": False,
                "error": f"Invalid LOINC format: {code}",
                "suggestion": "LOINC codes should follow format like '4548-4'",
            }

        # Check if code exists in our lookup table
        if code in self.loinc_codes:
            return {
                "valid": True,
                "description": self.loinc_codes[code],
                "code_system": "LOINC",
            }

        return {
            "valid": False,
            "error": f"Unknown LOINC code: {code}",
            "suggestion": "Verify code against current LOINC database",
        }

    def validate_rxnorm_code(self, code: str) -> Dict[str, Any]:
        """Validate RxNorm medication code."""
        if not code:
            return {"valid": False, "error": "Missing RxNorm code"}

        # Check format (RxNorm codes are numeric)
        if not re.match(r'^\d+$', code):
            return {
                "valid": False,
                "error": f"Invalid RxNorm format: {code}",
                "suggestion": "RxNorm codes should be numeric like '860975'",
            }

        # Check if code exists in our lookup table
        if code in self.rxnorm_codes:
            return {
                "valid": True,
                "description": self.rxnorm_codes[code],
                "code_system": "RxNorm",
            }

        return {
            "valid": False,
            "error": f"Unknown RxNorm code: {code}",
            "suggestion": "Verify code against current RxNorm database",
        }

    def validate_snomed_code(self, code: str) -> Dict[str, Any]:
        """Validate SNOMED-CT clinical code."""
        if not code:
            return {"valid": False, "error": "Missing SNOMED code"}

        # Check format (SNOMED codes are numeric, min 6 digits)
        if not re.match(r'^\d{6,}$', code):
            return {
                "valid": False,
                "error": f"Invalid SNOMED format: {code}",
                "suggestion": "SNOMED codes should be numeric with at least 6 digits like '271737000'",
            }

        # Check if code exists in our lookup table
        if code in self.snomed_codes:
            return {
                "valid": True,
                "description": self.snomed_codes[code],
                "code_system": "SNOMED-CT",
            }

        return {
            "valid": False,
            "error": f"Unknown SNOMED code: {code}",
            "suggestion": "Verify code against current SNOMED-CT terminology",
        }


class ClinicalLogicValidator:
    """Validates clinical relationships and logic."""

    def validate_diabetes_care(
        self, fhir_bundle: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """Validate diabetes care patterns."""
        issues = []

        # Check if patient has diabetes diagnosis
        has_diabetes = self._has_diabetes_diagnosis(fhir_bundle)
        if not has_diabetes:
            return issues  # No diabetes, no specific validation needed

        # Check for HbA1c monitoring
        has_hba1c = self._has_hba1c_test(fhir_bundle)
        if not has_hba1c:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    code="DM001",
                    message="Diabetes patient missing HbA1c monitoring",
                    field_path="fhir_resources.observations",
                    suggested_fix="Add HbA1c test (CPT 83036) for diabetes monitoring",
                    resource_type="Observation",
                )
            )

        # Check medication appropriateness
        has_appropriate_medication = self._has_diabetes_medication(fhir_bundle)
        if not has_appropriate_medication:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    code="DM002",
                    message="Consider diabetes medication for patient with diabetes diagnosis",
                    field_path="fhir_resources.medications",
                    suggested_fix="Review need for diabetes medications (Metformin, Insulin)",
                    resource_type="MedicationStatement",
                )
            )

        return issues

    def validate_medication_condition_match(
        self, fhir_bundle: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """Validate that medications match diagnosed conditions."""
        issues = []

        # Get medications and conditions from bundle
        medications = self._extract_medications(fhir_bundle)
        conditions = self._extract_conditions(fhir_bundle)

        for medication in medications:
            if "insulin" in medication.lower():
                if not any("diabetes" in condition.lower() for condition in conditions):
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            code="MED001",
                            message="Insulin prescribed without diabetes diagnosis",
                            field_path="fhir_resources.medications",
                            suggested_fix="Add diabetes diagnosis code (E11.x) or review medication",
                            resource_type="MedicationStatement",
                        )
                    )

        return issues

    def _has_diabetes_diagnosis(self, fhir_bundle: Dict[str, Any]) -> bool:
        """Check if bundle contains diabetes diagnosis."""
        # Check in various places where diagnosis might be stored

        # Check claims data
        claims = fhir_bundle.get("claims", [])
        for claim in claims:
            diagnosis = claim.get("diagnosis_code") or ""
            if diagnosis and (
                diagnosis.startswith("E11") or diagnosis.startswith("E10")
            ):
                return True

        # Check services data
        services = fhir_bundle.get("services", [])
        for service in services:
            diagnosis = service.get("diagnosis_code") or ""
            if diagnosis and (
                diagnosis.startswith("E11") or diagnosis.startswith("E10")
            ):
                return True

        return False

    def _has_hba1c_test(self, fhir_bundle: Dict[str, Any]) -> bool:
        """Check if bundle contains HbA1c test."""
        # Check services for HbA1c CPT code
        services = fhir_bundle.get("services", [])
        for service in services:
            activity_code = service.get("activity_code", "")
            if activity_code == "83036":  # HbA1c CPT code
                return True

        # Check observations
        observations = fhir_bundle.get("observations", [])
        for obs in observations:
            test_name = obs.get("test_name", "").lower()
            if "hba1c" in test_name or "a1c" in test_name:
                return True

        return False

    def _has_diabetes_medication(self, fhir_bundle: Dict[str, Any]) -> bool:
        """Check if bundle contains diabetes medications."""
        medications = self._extract_medications(fhir_bundle)
        diabetes_meds = ["metformin", "insulin", "glipizide", "glyburide"]

        for medication in medications:
            if any(med in medication.lower() for med in diabetes_meds):
                return True

        return False

    def _extract_medications(self, fhir_bundle: Dict[str, Any]) -> List[str]:
        """Extract medication names from bundle."""
        medications = []

        # Check raw data for medication mentions
        raw_data = fhir_bundle.get("raw_data", {})
        if isinstance(raw_data, dict):
            try:
                raw_str = json.dumps(raw_data, default=str).lower()
                # Simple extraction - in real implementation would be more sophisticated
                if "metformin" in raw_str:
                    medications.append("metformin")
                if "insulin" in raw_str:
                    medications.append("insulin")
            except (TypeError, ValueError):
                # Fallback: search in CSV data directly
                csv_data = raw_data.get("csv_data", [])
                for record in csv_data:
                    record_str = json.dumps(record, default=str).lower()
                    if "metformin" in record_str:
                        medications.append("metformin")
                    if "insulin" in record_str:
                        medications.append("insulin")

        return medications

    def _extract_conditions(self, fhir_bundle: Dict[str, Any]) -> List[str]:
        """Extract condition descriptions from bundle."""
        conditions = []

        # Check diagnosis codes and descriptions
        claims = fhir_bundle.get("claims", [])
        for claim in claims:
            diagnosis = claim.get("diagnosis_code") or ""
            if diagnosis and (
                diagnosis.startswith("E11") or diagnosis.startswith("E10")
            ):
                conditions.append("diabetes")

        return conditions


class DataQuality:
    """
    Comprehensive data quality validation engine for UAE healthcare data.

    Validates all 6 FHIR resources against clinical and business rules,
    providing quality scores and actionable feedback for data improvement.
    Enhanced with parallel LLM validation for intelligent assessment.
    """

    def __init__(self, enable_llm_validation: bool = True, max_concurrent_llm: int = 3):
        """
        Initialize data quality engine with validators.

        Args:
            enable_llm_validation: Enable LLM-based validation (default: True)
            max_concurrent_llm: Maximum concurrent LLM requests (default: 3)
        """
        self.code_validator = MedicalCodeValidator()
        self.clinical_validator = ClinicalLogicValidator()
        self.validation_timestamp = datetime.now(timezone.utc).isoformat()

        # LLM validation setup
        self.enable_llm_validation = enable_llm_validation and LLM_VALIDATION_AVAILABLE
        if self.enable_llm_validation:
            self.llm_validator = ParallelLLMValidator(
                max_concurrent_requests=max_concurrent_llm
            )
            self.data_sampler = SmartDataSampler(max_sample_size=50)
            logger.info("LLM validation enabled for enhanced data quality assessment")
        else:
            self.llm_validator = None
            self.data_sampler = None
            if enable_llm_validation and not LLM_VALIDATION_AVAILABLE:
                logger.warning(
                    "LLM validation requested but not available - falling back to rule-based validation"
                )

    def validate_fhir_bundle(self, fhir_bundle: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate complete FHIR bundle against all quality rules.
        Synchronous version - for async with LLM validation, use validate_fhir_bundle_async.

        Args:
            fhir_bundle: FHIR Bundle dictionary from XML/CSV processor

        Returns:
            Comprehensive validation report with quality scores and issues
        """
        logger.info(
            f"Starting data quality validation for bundle: {fhir_bundle.get('id', 'unknown')}"
        )

        validation_issues = []

        # 1. Validate medical codes
        code_validation_results = self._validate_medical_codes(fhir_bundle)
        validation_issues.extend(code_validation_results["issues"])

        # 2. Validate clinical logic
        clinical_issues = self._validate_clinical_logic(fhir_bundle)
        validation_issues.extend(clinical_issues)

        # 3. Validate data completeness
        completeness_issues = self._validate_completeness(fhir_bundle)
        validation_issues.extend(completeness_issues)

        # 4. Validate format compliance
        format_issues = self._validate_format_compliance(fhir_bundle)
        validation_issues.extend(format_issues)

        # 5. Calculate quality scores (rule-based only)
        quality_score = self._calculate_quality_score(fhir_bundle, validation_issues)

        # Build comprehensive validation report
        validation_report = {
            "validation_timestamp": self.validation_timestamp,
            "bundle_id": fhir_bundle.get("id"),
            "source": fhir_bundle.get("meta", {}).get("source"),
            "quality_score": quality_score,
            "validation_issues": [
                {
                    "severity": issue.severity.value,
                    "code": issue.code,
                    "message": issue.message,
                    "field_path": issue.field_path,
                    "suggested_fix": issue.suggested_fix,
                    "resource_type": issue.resource_type,
                }
                for issue in validation_issues
            ],
            "code_validation_summary": code_validation_results["summary"],
            "clinical_validation_passed": len(
                [i for i in clinical_issues if i.severity == ValidationSeverity.ERROR]
            )
            == 0,
            "recommendations": self._generate_recommendations(validation_issues),
            "llm_validation_enabled": False,
            "validation_method": "rule_based_only",
        }

        logger.info(
            f"Data quality validation completed. Score: {quality_score.overall_score:.3f}"
        )
        return validation_report

    async def validate_fhir_bundle_async(
        self, fhir_bundle: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Async validate complete FHIR bundle with LLM enhancement.
        Combines rule-based validation with LLM intelligent assessment.

        Args:
            fhir_bundle: FHIR Bundle dictionary from XML/CSV processor

        Returns:
            Enhanced validation report with hybrid scoring and LLM insights
        """
        logger.info(
            f"Starting enhanced data quality validation for bundle: {fhir_bundle.get('id', 'unknown')}"
        )

        # Start with rule-based validation
        validation_issues = []

        # 1. Validate medical codes
        code_validation_results = self._validate_medical_codes(fhir_bundle)
        validation_issues.extend(code_validation_results["issues"])

        # 2. Validate clinical logic
        clinical_issues = self._validate_clinical_logic(fhir_bundle)
        validation_issues.extend(clinical_issues)

        # 3. Validate data completeness
        completeness_issues = self._validate_completeness(fhir_bundle)
        validation_issues.extend(completeness_issues)

        # 4. Validate format compliance
        format_issues = self._validate_format_compliance(fhir_bundle)
        validation_issues.extend(format_issues)

        # 5. Calculate rule-based quality scores
        rule_based_score = self._calculate_quality_score(fhir_bundle, validation_issues)

        # 6. LLM validation (if enabled)
        llm_validation_result = None
        if self.enable_llm_validation:
            try:
                llm_validation_result = await self._run_llm_validation(fhir_bundle)
            except Exception as e:
                logger.warning(f"LLM validation failed: {e}")

        # 7. Calculate hybrid scores
        enhanced_score = self._calculate_hybrid_score(
            rule_based_score, llm_validation_result
        )

        # 8. Merge validation issues
        all_issues = validation_issues.copy()
        if llm_validation_result:
            llm_issues = self._convert_llm_issues_to_validation_issues(
                llm_validation_result
            )
            all_issues.extend(llm_issues)

        # Build enhanced validation report
        validation_report = {
            "validation_timestamp": self.validation_timestamp,
            "bundle_id": fhir_bundle.get("id"),
            "source": fhir_bundle.get("meta", {}).get("source"),
            "quality_score": enhanced_score,
            "validation_issues": [
                {
                    "severity": issue.severity.value,
                    "code": issue.code,
                    "message": issue.message,
                    "field_path": issue.field_path,
                    "suggested_fix": issue.suggested_fix,
                    "resource_type": issue.resource_type,
                }
                for issue in all_issues
            ],
            "code_validation_summary": code_validation_results["summary"],
            "clinical_validation_passed": len(
                [i for i in clinical_issues if i.severity == ValidationSeverity.ERROR]
            )
            == 0,
            "recommendations": self._generate_enhanced_recommendations(
                all_issues, llm_validation_result
            ),
            "llm_validation_enabled": self.enable_llm_validation,
            "llm_validation_result": self._format_llm_validation_summary(
                llm_validation_result
            )
            if llm_validation_result
            else None,
            "validation_method": "hybrid_rule_based_and_llm"
            if llm_validation_result
            else "rule_based_only",
        }

        score_info = f"Rule-based: {rule_based_score.overall_score:.3f}"
        if enhanced_score.hybrid_score:
            score_info += f", Hybrid: {enhanced_score.hybrid_score:.3f}"
        if enhanced_score.llm_validation_score:
            score_info += f", LLM: {enhanced_score.llm_validation_score:.3f}"

        logger.info(f"Enhanced data quality validation completed. Scores: {score_info}")
        return validation_report

    def _validate_medical_codes(self, fhir_bundle: Dict[str, Any]) -> Dict[str, Any]:
        """Validate all medical codes in the bundle."""
        issues = []
        validation_results = {
            "icd10_validated": 0,
            "icd10_valid": 0,
            "cpt_validated": 0,
            "cpt_valid": 0,
            "loinc_validated": 0,
            "loinc_valid": 0,
        }

        # Validate ICD-10 codes in claims and services
        claims = fhir_bundle.get("claims", [])
        services = fhir_bundle.get("services", [])
        all_items = claims + services

        for item in all_items:
            # Validate diagnosis codes (ICD-10)
            diagnosis_code = item.get("diagnosis_code")
            if diagnosis_code:
                validation_results["icd10_validated"] += 1
                icd_result = self.code_validator.validate_icd10_code(diagnosis_code)
                if icd_result["valid"]:
                    validation_results["icd10_valid"] += 1
                else:
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            code="ICD001",
                            message=icd_result["error"],
                            field_path="diagnosis_code",
                            suggested_fix=icd_result.get("suggestion"),
                            resource_type="Claim",
                        )
                    )

            # Validate procedure codes (CPT)
            procedure_code = item.get("procedure_code") or item.get("activity_code")
            if procedure_code:
                validation_results["cpt_validated"] += 1
                cpt_result = self.code_validator.validate_cpt_code(procedure_code)
                if cpt_result["valid"]:
                    validation_results["cpt_valid"] += 1
                else:
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            code="CPT001",
                            message=cpt_result["error"],
                            field_path="procedure_code",
                            suggested_fix=cpt_result.get("suggestion"),
                            resource_type="ServiceRequest",
                        )
                    )

        return {"issues": issues, "summary": validation_results}

    def _validate_clinical_logic(
        self, fhir_bundle: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """Validate clinical logic and relationships."""
        issues = []

        # Validate diabetes care patterns
        diabetes_issues = self.clinical_validator.validate_diabetes_care(fhir_bundle)
        issues.extend(diabetes_issues)

        # Validate medication-condition matches
        medication_issues = self.clinical_validator.validate_medication_condition_match(
            fhir_bundle
        )
        issues.extend(medication_issues)

        return issues

    def _validate_completeness(
        self, fhir_bundle: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """Validate data completeness."""
        issues = []

        # Check required fields for FHIR Bundle
        required_fields = ["resourceType", "id", "timestamp"]
        for field in required_fields:
            if not fhir_bundle.get(field):
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        code="COMP001",
                        message=f"Missing required field: {field}",
                        field_path=field,
                        suggested_fix=f"Add {field} to FHIR Bundle",
                        resource_type="Bundle",
                    )
                )

        # Check for essential clinical data
        if not fhir_bundle.get("claims") and not fhir_bundle.get("services"):
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    code="COMP002",
                    message="Bundle contains no claims or services data",
                    field_path="claims",
                    suggested_fix="Ensure bundle contains clinical data",
                    resource_type="Bundle",
                )
            )

        return issues

    def _validate_format_compliance(
        self, fhir_bundle: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """Validate format compliance."""
        issues = []

        # Check FHIR Bundle structure
        if fhir_bundle.get("resourceType") != "Bundle":
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code="FMT001",
                    message="Invalid resourceType, must be 'Bundle'",
                    field_path="resourceType",
                    suggested_fix="Set resourceType to 'Bundle'",
                    resource_type="Bundle",
                )
            )

        # Check timestamp format
        timestamp = fhir_bundle.get("timestamp")
        if timestamp:
            try:
                datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except ValueError:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        code="FMT002",
                        message="Invalid timestamp format",
                        field_path="timestamp",
                        suggested_fix="Use ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)",
                        resource_type="Bundle",
                    )
                )

        return issues

    def _calculate_quality_score(
        self, fhir_bundle: Dict[str, Any], issues: List[ValidationIssue]
    ) -> QualityScore:
        """Calculate comprehensive quality score."""

        # Count issues by severity
        issues_count = {
            "critical": len(
                [i for i in issues if i.severity == ValidationSeverity.CRITICAL]
            ),
            "error": len([i for i in issues if i.severity == ValidationSeverity.ERROR]),
            "warning": len(
                [i for i in issues if i.severity == ValidationSeverity.WARNING]
            ),
            "info": len([i for i in issues if i.severity == ValidationSeverity.INFO]),
        }

        # 1. Code validity score (40% weight)
        total_codes_checked = 0
        valid_codes = 0

        # Count validation attempts and successes
        claims = fhir_bundle.get("claims", [])
        services = fhir_bundle.get("services", [])
        all_items = claims + services

        for item in all_items:
            if item.get("diagnosis_code"):
                total_codes_checked += 1
                result = self.code_validator.validate_icd10_code(item["diagnosis_code"])
                if result["valid"]:
                    valid_codes += 1

            procedure_code = item.get("procedure_code") or item.get("activity_code")
            if procedure_code:
                total_codes_checked += 1
                result = self.code_validator.validate_cpt_code(procedure_code)
                if result["valid"]:
                    valid_codes += 1

        code_validity = (
            valid_codes / total_codes_checked if total_codes_checked > 0 else 1.0
        )

        # 2. Completeness score (25% weight)
        required_fields = ["resourceType", "id", "timestamp"]
        present_fields = sum(1 for field in required_fields if fhir_bundle.get(field))
        completeness = present_fields / len(required_fields)

        # Bonus for having clinical data
        if fhir_bundle.get("claims") or fhir_bundle.get("services"):
            completeness = min(1.0, completeness + 0.2)

        # 3. Clinical consistency score (20% weight)
        clinical_errors = len(
            [
                i
                for i in issues
                if i.severity == ValidationSeverity.ERROR
                and i.code.startswith(("DM", "MED"))
            ]
        )
        clinical_consistency = max(0.0, 1.0 - (clinical_errors * 0.2))

        # 4. Format compliance score (15% weight)
        format_errors = len([i for i in issues if i.code.startswith("FMT")])
        format_compliance = max(0.0, 1.0 - (format_errors * 0.1))

        # Calculate weighted overall score
        overall_score = (
            0.40 * code_validity
            + 0.25 * completeness
            + 0.20 * clinical_consistency
            + 0.15 * format_compliance
        )

        # Apply penalties for critical issues
        if issues_count["critical"] > 0:
            overall_score *= 0.5
        elif issues_count["error"] > 0:
            overall_score *= 0.8

        return QualityScore(
            overall_score=round(overall_score, 3),
            code_validity=round(code_validity, 3),
            completeness=round(completeness, 3),
            clinical_consistency=round(clinical_consistency, 3),
            format_compliance=round(format_compliance, 3),
            issues_count=issues_count,
            llm_available=self.enable_llm_validation,
        )

    async def _run_llm_validation(self, fhir_bundle: Dict[str, Any]):
        """Run LLM validation on the FHIR bundle."""
        if not self.enable_llm_validation:
            return None

        # Create data sample for LLM validation
        try:
            # Convert raw data to DataFrame for sampling
            raw_data = fhir_bundle.get("raw_data", {})
            csv_data = raw_data.get("csv_data", [])

            if not csv_data:
                logger.warning("No CSV data found for LLM validation")
                return None

            import pandas as pd

            df = pd.DataFrame(csv_data)

            # Create intelligent sample
            data_sample = self.data_sampler.create_sample(
                df, strategy=SamplingStrategy.HEALTHCARE_AWARE
            )

            # Run parallel LLM validation
            batch_result = await self.llm_validator.validate_healthcare_data(
                data_sample,
                validation_tasks=[
                    ValidationType.DATA_QUALITY,
                    ValidationType.CODE_VALIDATION,
                    ValidationType.CLINICAL,
                ],
            )

            return batch_result

        except Exception as e:
            logger.error(f"Error during LLM validation: {e}")
            return None

    def _calculate_hybrid_score(
        self, rule_based_score: QualityScore, llm_result
    ) -> QualityScore:
        """Calculate hybrid score combining rule-based and LLM validation."""
        # Start with rule-based score
        hybrid_score_data = {
            "overall_score": rule_based_score.overall_score,
            "code_validity": rule_based_score.code_validity,
            "completeness": rule_based_score.completeness,
            "clinical_consistency": rule_based_score.clinical_consistency,
            "format_compliance": rule_based_score.format_compliance,
            "issues_count": rule_based_score.issues_count,
            "llm_available": rule_based_score.llm_available,
        }

        if llm_result and llm_result.successful_tasks > 0:
            # Add LLM scores
            hybrid_score_data["llm_validation_score"] = llm_result.aggregated_score

            # Calculate average confidence from successful tasks
            successful_results = [r for r in llm_result.validation_results if r.success]
            if successful_results:
                avg_confidence = sum(
                    r.confidence_score for r in successful_results
                ) / len(successful_results)
                hybrid_score_data["llm_confidence_score"] = round(avg_confidence, 3)

            # Calculate hybrid score (weighted combination)
            rule_weight = 0.6  # Rule-based validation weight
            llm_weight = 0.4  # LLM validation weight

            # Adjust weights based on LLM confidence
            if hybrid_score_data.get("llm_confidence_score", 0) > 0.8:
                llm_weight = 0.5
                rule_weight = 0.5
            elif hybrid_score_data.get("llm_confidence_score", 0) < 0.6:
                llm_weight = 0.3
                rule_weight = 0.7

            hybrid_overall_score = (
                rule_weight * rule_based_score.overall_score
                + llm_weight * llm_result.aggregated_score
            )

            hybrid_score_data["hybrid_score"] = round(hybrid_overall_score, 3)
            # Update overall score to use hybrid
            hybrid_score_data["overall_score"] = hybrid_score_data["hybrid_score"]

        return QualityScore(**hybrid_score_data)

    def _convert_llm_issues_to_validation_issues(
        self, llm_result
    ) -> List[ValidationIssue]:
        """Convert LLM validation results to ValidationIssue objects."""
        validation_issues = []

        for result in llm_result.validation_results:
            if not result.success:
                continue

            for issue in result.issues_found:
                # Map LLM severity to ValidationSeverity
                severity_map = {
                    "error": ValidationSeverity.ERROR,
                    "warning": ValidationSeverity.WARNING,
                    "info": ValidationSeverity.INFO,
                    "critical": ValidationSeverity.CRITICAL,
                }

                severity = severity_map.get(
                    issue.get("severity", "info"), ValidationSeverity.INFO
                )

                validation_issue = ValidationIssue(
                    severity=severity,
                    code=f"LLM_{result.task_type.value.upper()}_{len(validation_issues)+1:03d}",
                    message=issue.get("description", "LLM validation issue"),
                    field_path=issue.get("field", "unknown"),
                    suggested_fix=issue.get("suggested_fix"),
                    resource_type="LLM_Analysis",
                )
                validation_issues.append(validation_issue)

        return validation_issues

    def _generate_enhanced_recommendations(
        self, issues: List[ValidationIssue], llm_result
    ) -> List[str]:
        """Generate enhanced recommendations including LLM insights."""
        # Start with rule-based recommendations
        recommendations = self._generate_recommendations(issues)

        # Add LLM recommendations
        if llm_result:
            llm_recommendations = []
            for result in llm_result.validation_results:
                if result.success:
                    llm_recommendations.extend(result.recommendations)

            # Deduplicate and add LLM recommendations
            unique_llm_recs = list(set(llm_recommendations))
            recommendations.extend([f"LLM Insight: {rec}" for rec in unique_llm_recs])

        return recommendations

    def _format_llm_validation_summary(self, llm_result) -> Dict[str, Any]:
        """Format LLM validation results for the report."""
        if not llm_result:
            return None

        return {
            "total_tasks": llm_result.total_tasks,
            "successful_tasks": llm_result.successful_tasks,
            "failed_tasks": llm_result.failed_tasks,
            "aggregated_score": llm_result.aggregated_score,
            "execution_time": llm_result.total_execution_time,
            "task_results": [
                {
                    "task_type": result.task_type.value,
                    "success": result.success,
                    "score": result.validation_score,
                    "confidence": result.confidence_score,
                    "issues_count": len(result.issues_found),
                    "recommendations_count": len(result.recommendations),
                }
                for result in llm_result.validation_results
            ],
        }

    def _generate_recommendations(self, issues: List[ValidationIssue]) -> List[str]:
        """Generate actionable recommendations based on validation issues."""
        recommendations = []

        # Group issues by type
        error_count = len([i for i in issues if i.severity == ValidationSeverity.ERROR])
        warning_count = len(
            [i for i in issues if i.severity == ValidationSeverity.WARNING]
        )

        if error_count > 0:
            recommendations.append(
                f"Address {error_count} critical errors to improve data quality"
            )

        if warning_count > 0:
            recommendations.append(
                f"Review {warning_count} warnings for data enhancement opportunities"
            )

        # Specific recommendations
        code_issues = [i for i in issues if i.code.startswith(("ICD", "CPT", "LOINC"))]
        if code_issues:
            recommendations.append(
                "Verify medical codes against current terminology standards"
            )

        clinical_issues = [
            i
            for i in issues
            if i.code.startswith(("DM", "MED"))
            and i.severity in [ValidationSeverity.ERROR, ValidationSeverity.WARNING]
        ]
        if clinical_issues:
            recommendations.append(
                "Review clinical logic and medication-condition relationships"
            )

        if not recommendations:
            recommendations.append(
                "Data quality is excellent - no major issues identified"
            )

        return recommendations


if __name__ == "__main__":
    """
    Debug and testing section for enhanced data quality validation.

    Tests validation engine with sample FHIR bundle data and LLM integration.
    """
    import pandas as pd
    import numpy as np

    # Setup logging
    logger.add("debug_data_quality_enhanced.log")

    print("=" * 80)
    print("Enhanced Data Quality Validation Engine - Debug Mode")
    print("=" * 80)

    async def test_enhanced_validation():
        """Test enhanced validation with LLM integration."""

        # Initialize validation engine with LLM support
        data_quality = DataQuality(enable_llm_validation=True)

        print(f"   LLM validation enabled: {data_quality.enable_llm_validation}")

        # Create sample CSV data for testing
        np.random.seed(42)
        csv_sample_data = [
            {
                "patient_id": f"P{i:04d}",
                "diagnosis_code": np.random.choice(["E11.9", "M54.5", "I10", "X99.9"]),
                "procedure_code": np.random.choice(
                    ["99213", "99214", "83036", "12345"]
                ),
                "amount": np.random.uniform(50, 500),
                "service_date": f"2024-{i%12+1:02d}-{i%28+1:02d}",
                "provider_id": f"PROV{i%10:03d}",
            }
            for i in range(100)
        ]

        # Sample FHIR bundle for testing with CSV data
        sample_bundle = {
            "resourceType": "Bundle",
            "id": "test-bundle-enhanced-001",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "meta": {
                "source": "Enhanced-Test",
                "lastUpdated": datetime.now(timezone.utc).isoformat(),
            },
            "claims": [
                {
                    "sequence": 1,
                    "claim_id": "C001",
                    "patient_id": "P123",
                    "diagnosis_code": "E11.9",  # Valid diabetes code
                    "procedure_code": "99213",  # Valid office visit
                    "amount": 150.0,
                },
                {
                    "sequence": 2,
                    "claim_id": "C002",
                    "patient_id": "P123",
                    "diagnosis_code": "X99.9",  # Invalid code
                    "procedure_code": "12345",  # Invalid code
                    "amount": 75.0,
                },
            ],
            "services": [
                {
                    "sequence": 1,
                    "activity_code": "83036",  # Valid HbA1c test
                    "diagnosis_code": "E11.9",
                }
            ],
            "raw_data": {
                "csv_data": csv_sample_data,
                "columns": list(csv_sample_data[0].keys()) if csv_sample_data else [],
                "shape": [
                    len(csv_sample_data),
                    len(csv_sample_data[0].keys()) if csv_sample_data else 0,
                ],
            },
        }

        try:
            print("\n🔧 Step 1: Rule-Based Validation")
            print("-" * 50)

            validation_result = data_quality.validate_fhir_bundle(sample_bundle)

            print("✅ Rule-based validation completed")
            print(
                f"   Overall Quality Score: {validation_result['quality_score'].overall_score}"
            )
            print(
                f"   Code Validity: {validation_result['quality_score'].code_validity}"
            )
            print(f"   Completeness: {validation_result['quality_score'].completeness}")
            print(f"   Validation Method: {validation_result['validation_method']}")

            print("\n🔧 Step 2: Enhanced Validation with LLM")
            print("-" * 50)

            if data_quality.enable_llm_validation:
                enhanced_result = await data_quality.validate_fhir_bundle_async(
                    sample_bundle
                )

                print("✅ Enhanced validation completed")
                enhanced_score = enhanced_result['quality_score']
                print(f"   Rule-based Score: {enhanced_score.overall_score}")

                if enhanced_score.llm_validation_score:
                    print(
                        f"   LLM Validation Score: {enhanced_score.llm_validation_score}"
                    )
                if enhanced_score.hybrid_score:
                    print(f"   Hybrid Score: {enhanced_score.hybrid_score}")
                if enhanced_score.llm_confidence_score:
                    print(f"   LLM Confidence: {enhanced_score.llm_confidence_score}")

                print(f"   Validation Method: {enhanced_result['validation_method']}")

                # Show LLM validation summary
                if enhanced_result.get('llm_validation_result'):
                    llm_summary = enhanced_result['llm_validation_result']
                    print(
                        f"   LLM Tasks: {llm_summary['successful_tasks']}/{llm_summary['total_tasks']} successful"
                    )
                    print(
                        f"   LLM Execution Time: {llm_summary['execution_time']:.2f}s"
                    )

                # Save enhanced results
                with open(
                    "debug_enhanced_validation_results.json", "w", encoding="utf-8"
                ) as f:
                    json.dump(
                        enhanced_result, f, indent=2, ensure_ascii=False, default=str
                    )
                print(
                    "\n   Enhanced results saved to: debug_enhanced_validation_results.json"
                )

            else:
                print("   LLM validation not available - using rule-based only")

            print("\n🔧 Step 3: Test Individual Components")
            print("-" * 50)

            # Test data sampling
            if data_quality.data_sampler:
                df = pd.DataFrame(csv_sample_data)
                sample = data_quality.data_sampler.create_sample(df)
                print(f"   ✅ Data sampling: {len(sample.sample_data)} records sampled")
                print(
                    f"      Sample quality: {sample.quality_indicators['completeness_score']:.3f}"
                )

            # Test code validators
            code_validator = MedicalCodeValidator()
            test_codes = [
                ("ICD-10", "E11.9", code_validator.validate_icd10_code),
                ("ICD-10", "X99.9", code_validator.validate_icd10_code),
                ("CPT", "99213", code_validator.validate_cpt_code),
                ("CPT", "12345", code_validator.validate_cpt_code),
            ]

            for code_system, code, validator_func in test_codes:
                result = validator_func(code)
                status = "✅" if result["valid"] else "❌"
                print(
                    f"   {status} {code_system} {code}: {result.get('description', result.get('error'))}"
                )

            print("\n🔧 Step 4: Performance Metrics")
            print("-" * 50)

            if data_quality.llm_validator:
                metrics = data_quality.llm_validator.get_performance_metrics()
                print(f"   LLM Requests: {metrics['total_requests']}")
                print(f"   Success Rate: {metrics['success_rate']:.1%}")
                print(
                    f"   Avg Response Time: {metrics.get('average_request_time', 0):.2f}s"
                )

        except Exception as e:
            print("\n❌ Error during enhanced validation:")
            print(f"   {type(e).__name__}: {str(e)}")
            import traceback

            print("\n📋 Full traceback:")
            traceback.print_exc()

    # Run async test
    try:
        asyncio.run(test_enhanced_validation())
        print(
            "\n🎉 Enhanced data quality validation debug session completed successfully!"
        )
    except Exception as e:
        print("\n❌ Error during async testing:")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback

        print("\n📋 Full traceback:")
        traceback.print_exc()

    print("=" * 80)
