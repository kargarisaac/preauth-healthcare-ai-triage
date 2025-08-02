"""
Unit tests for data quality validation engine.

Tests the comprehensive data quality framework that validates all FHIR resources
against clinical and business rules for UAE healthcare standards.
"""

import pytest

from pipelines.data_quality import (
    DataQuality,
    MedicalCodeValidator,
    ClinicalLogicValidator,
    ValidationSeverity,
    QualityScore,
)


class TestMedicalCodeValidator:
    """Test medical code validation functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = MedicalCodeValidator()

    def test_valid_icd10_codes(self):
        """Test validation of valid ICD-10 codes."""
        # Test valid diabetes code
        result = self.validator.validate_icd10_code("E11.9")
        assert result["valid"] is True
        assert "diabetes" in result["description"].lower()
        assert result["code_system"] == "ICD-10"

        # Test valid back pain code
        result = self.validator.validate_icd10_code("M54.5")
        assert result["valid"] is True
        assert "back pain" in result["description"].lower()

    def test_invalid_icd10_codes(self):
        """Test validation of invalid ICD-10 codes."""
        # Test non-existent code
        result = self.validator.validate_icd10_code("X99.9")
        assert result["valid"] is False
        assert "Unknown ICD-10 code" in result["error"]
        assert "suggestion" in result

        # Test invalid format
        result = self.validator.validate_icd10_code("12345")
        assert result["valid"] is False
        assert "Invalid ICD-10 format" in result["error"]

        # Test empty code
        result = self.validator.validate_icd10_code("")
        assert result["valid"] is False
        assert "Missing ICD-10 code" in result["error"]

    def test_valid_cpt_codes(self):
        """Test validation of valid CPT codes."""
        # Test valid office visit code
        result = self.validator.validate_cpt_code("99213")
        assert result["valid"] is True
        assert "office" in result["description"].lower()
        assert result["code_system"] == "CPT"

        # Test valid lab test code
        result = self.validator.validate_cpt_code("83036")
        assert result["valid"] is True
        assert "hemoglobin" in result["description"].lower()

    def test_invalid_cpt_codes(self):
        """Test validation of invalid CPT codes."""
        # Test non-existent code
        result = self.validator.validate_cpt_code("12345")
        assert result["valid"] is False
        assert "Unknown CPT code" in result["error"]

        # Test invalid format
        result = self.validator.validate_cpt_code("123")
        assert result["valid"] is False
        assert "Invalid CPT format" in result["error"]

        # Test empty code
        result = self.validator.validate_cpt_code("")
        assert result["valid"] is False
        assert "Missing CPT code" in result["error"]

    def test_valid_loinc_codes(self):
        """Test validation of valid LOINC codes."""
        result = self.validator.validate_loinc_code("4548-4")
        assert result["valid"] is True
        assert "hemoglobin" in result["description"].lower()
        assert result["code_system"] == "LOINC"

    def test_invalid_loinc_codes(self):
        """Test validation of invalid LOINC codes."""
        # Test invalid format
        result = self.validator.validate_loinc_code("4548")
        assert result["valid"] is False
        assert "Invalid LOINC format" in result["error"]

        # Test non-existent code
        result = self.validator.validate_loinc_code("9999-9")
        assert result["valid"] is False
        assert "Unknown LOINC code" in result["error"]

    def test_valid_rxnorm_codes(self):
        """Test validation of valid RxNorm codes."""
        result = self.validator.validate_rxnorm_code("860975")
        assert result["valid"] is True
        assert "metformin" in result["description"].lower()
        assert result["code_system"] == "RxNorm"

    def test_invalid_rxnorm_codes(self):
        """Test validation of invalid RxNorm codes."""
        # Test invalid format
        result = self.validator.validate_rxnorm_code("ABC123")
        assert result["valid"] is False
        assert "Invalid RxNorm format" in result["error"]

        # Test non-existent code
        result = self.validator.validate_rxnorm_code("999999")
        assert result["valid"] is False
        assert "Unknown RxNorm code" in result["error"]

    def test_valid_snomed_codes(self):
        """Test validation of valid SNOMED codes."""
        result = self.validator.validate_snomed_code("271737000")
        assert result["valid"] is True
        assert "anemia" in result["description"].lower()
        assert result["code_system"] == "SNOMED-CT"

    def test_invalid_snomed_codes(self):
        """Test validation of invalid SNOMED codes."""
        # Test invalid format (too short)
        result = self.validator.validate_snomed_code("12345")
        assert result["valid"] is False
        assert "Invalid SNOMED format" in result["error"]

        # Test non-numeric
        result = self.validator.validate_snomed_code("ABC123456")
        assert result["valid"] is False
        assert "Invalid SNOMED format" in result["error"]


class TestClinicalLogicValidator:
    """Test clinical logic validation functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = ClinicalLogicValidator()

    def test_diabetes_care_validation_complete(self):
        """Test diabetes care validation with complete data."""
        bundle = {
            "claims": [{"diagnosis_code": "E11.9", "patient_id": "P123"}],
            "services": [
                {"activity_code": "83036", "diagnosis_code": "E11.9"}  # HbA1c test
            ],
            "raw_data": {"medication": "metformin"},
        }

        issues = self.validator.validate_diabetes_care(bundle)
        # Should have no major issues - patient has diabetes, HbA1c test, and medication
        error_issues = [i for i in issues if i.severity == ValidationSeverity.ERROR]
        assert len(error_issues) == 0

    def test_diabetes_care_validation_missing_hba1c(self):
        """Test diabetes care validation with missing HbA1c."""
        bundle = {
            "claims": [{"diagnosis_code": "E11.9", "patient_id": "P123"}],
            "services": [],  # No HbA1c test
            "raw_data": {},
        }

        issues = self.validator.validate_diabetes_care(bundle)
        # Should flag missing HbA1c monitoring
        hba1c_issues = [i for i in issues if "HbA1c" in i.message]
        assert len(hba1c_issues) > 0
        assert hba1c_issues[0].severity == ValidationSeverity.WARNING
        assert hba1c_issues[0].code == "DM001"

    def test_diabetes_care_validation_no_diabetes(self):
        """Test diabetes care validation with no diabetes diagnosis."""
        bundle = {
            "claims": [
                {
                    "diagnosis_code": "M54.5",
                    "patient_id": "P123",
                }  # Back pain, not diabetes
            ],
            "services": [],
            "raw_data": {},
        }

        issues = self.validator.validate_diabetes_care(bundle)
        # Should have no diabetes-specific issues
        assert len(issues) == 0

    def test_medication_condition_match_valid(self):
        """Test medication-condition matching with valid combination."""
        bundle = {
            "claims": [{"diagnosis_code": "E11.9", "patient_id": "P123"}],  # Diabetes
            "raw_data": {"medication_list": "insulin"},
        }

        issues = self.validator.validate_medication_condition_match(bundle)
        # Insulin for diabetes should be valid
        medication_errors = [i for i in issues if i.code == "MED001"]
        assert len(medication_errors) == 0

    def test_medication_condition_match_invalid(self):
        """Test medication-condition matching with invalid combination."""
        bundle = {
            "claims": [{"diagnosis_code": "M54.5", "patient_id": "P123"}],  # Back pain
            "raw_data": {"medication_list": "insulin"},  # Insulin without diabetes
        }

        issues = self.validator.validate_medication_condition_match(bundle)
        # Insulin without diabetes should flag error
        medication_errors = [i for i in issues if i.code == "MED001"]
        assert len(medication_errors) > 0
        assert medication_errors[0].severity == ValidationSeverity.ERROR


class TestDataQuality:
    """Test comprehensive data quality validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.data_quality = DataQuality()
        self.sample_bundle = {
            "resourceType": "Bundle",
            "id": "test-bundle-001",
            "timestamp": "2025-07-31T10:30:00Z",
            "meta": {"source": "Test", "lastUpdated": "2025-07-31T10:30:00Z"},
            "claims": [
                {
                    "sequence": 1,
                    "claim_id": "C001",
                    "patient_id": "P123",
                    "diagnosis_code": "E11.9",  # Valid diabetes code
                    "procedure_code": "99213",  # Valid office visit
                    "amount": 150.0,
                }
            ],
            "services": [
                {
                    "sequence": 1,
                    "activity_code": "83036",  # Valid HbA1c test
                    "diagnosis_code": "E11.9",
                }
            ],
        }

    def test_validate_high_quality_bundle(self):
        """Test validation of a high-quality FHIR bundle."""
        result = self.data_quality.validate_fhir_bundle(self.sample_bundle)

        # Check overall structure
        assert "validation_timestamp" in result
        assert "bundle_id" in result
        assert "quality_score" in result
        assert "validation_issues" in result

        # Check quality score
        quality_score = result["quality_score"]
        assert isinstance(quality_score, QualityScore)
        assert quality_score.overall_score >= 0.8  # Should be high quality
        assert quality_score.code_validity >= 0.8
        assert quality_score.completeness >= 0.8

        # Check for minimal issues
        critical_issues = [
            i for i in result["validation_issues"] if i["severity"] == "critical"
        ]
        error_issues = [
            i for i in result["validation_issues"] if i["severity"] == "error"
        ]
        assert len(critical_issues) == 0
        assert len(error_issues) == 0

    def test_validate_low_quality_bundle(self):
        """Test validation of a low-quality FHIR bundle."""
        low_quality_bundle = {
            "resourceType": "Bundle",
            "id": "test-bundle-002",
            # Missing timestamp
            "claims": [
                {
                    "sequence": 1,
                    "diagnosis_code": "X99.9",  # Invalid code
                    "procedure_code": "12345",  # Invalid code
                    "amount": 150.0,
                }
            ],
        }

        result = self.data_quality.validate_fhir_bundle(low_quality_bundle)

        # Check quality score is low
        quality_score = result["quality_score"]
        assert quality_score.overall_score < 0.5  # Should be low quality
        assert quality_score.code_validity < 0.5  # Invalid codes

        # Check for validation issues
        error_issues = [
            i for i in result["validation_issues"] if i["severity"] == "error"
        ]
        assert len(error_issues) > 0

        # Check for specific code validation errors
        icd_errors = [i for i in error_issues if i["code"] == "ICD001"]
        cpt_errors = [i for i in error_issues if i["code"] == "CPT001"]
        assert len(icd_errors) > 0
        assert len(cpt_errors) > 0

    def test_validate_empty_bundle(self):
        """Test validation of an empty/minimal bundle."""
        empty_bundle = {"resourceType": "Bundle"}

        result = self.data_quality.validate_fhir_bundle(empty_bundle)

        # Should have completeness issues
        quality_score = result["quality_score"]
        assert quality_score.completeness < 0.5

        # Should flag missing required fields
        completeness_errors = [
            i for i in result["validation_issues"] if i["code"] == "COMP001"
        ]
        assert len(completeness_errors) > 0

    def test_validate_bundle_with_clinical_issues(self):
        """Test validation of bundle with clinical logic issues."""
        clinical_issue_bundle = {
            "resourceType": "Bundle",
            "id": "test-bundle-003",
            "timestamp": "2025-07-31T10:30:00Z",
            "claims": [
                {"diagnosis_code": "M54.5", "procedure_code": "99213"}  # Back pain
            ],
            "raw_data": {"medication_list": "insulin"},  # Insulin without diabetes
        }

        result = self.data_quality.validate_fhir_bundle(clinical_issue_bundle)

        # Should flag medication-condition mismatch
        medication_errors = [
            i for i in result["validation_issues"] if i["code"] == "MED001"
        ]
        assert len(medication_errors) > 0

        # Clinical consistency score should be reduced
        quality_score = result["quality_score"]
        assert quality_score.clinical_consistency < 1.0

    def test_quality_score_calculation(self):
        """Test quality score calculation components."""
        result = self.data_quality.validate_fhir_bundle(self.sample_bundle)
        quality_score = result["quality_score"]

        # Check all components are present and valid
        assert 0.0 <= quality_score.overall_score <= 1.0
        assert 0.0 <= quality_score.code_validity <= 1.0
        assert 0.0 <= quality_score.completeness <= 1.0
        assert 0.0 <= quality_score.clinical_consistency <= 1.0
        assert 0.0 <= quality_score.format_compliance <= 1.0

        # Check issues count
        assert isinstance(quality_score.issues_count, dict)
        assert "critical" in quality_score.issues_count
        assert "error" in quality_score.issues_count
        assert "warning" in quality_score.issues_count
        assert "info" in quality_score.issues_count

    def test_recommendations_generation(self):
        """Test generation of actionable recommendations."""
        result = self.data_quality.validate_fhir_bundle(self.sample_bundle)

        # Should have recommendations
        assert "recommendations" in result
        assert isinstance(result["recommendations"], list)
        assert len(result["recommendations"]) > 0

        # High quality data should get positive recommendation
        recommendations_text = " ".join(result["recommendations"])
        assert (
            "excellent" in recommendations_text.lower()
            or "no major issues" in recommendations_text.lower()
        )

    def test_validation_issue_structure(self):
        """Test validation issue data structure."""
        low_quality_bundle = {
            "resourceType": "Bundle",
            "claims": [{"diagnosis_code": "X99.9"}],  # Invalid code
        }

        result = self.data_quality.validate_fhir_bundle(low_quality_bundle)

        # Check validation issues have proper structure
        for issue in result["validation_issues"]:
            assert "severity" in issue
            assert "code" in issue
            assert "message" in issue
            assert "field_path" in issue
            assert issue["severity"] in ["info", "warning", "error", "critical"]
            assert isinstance(issue["code"], str)
            assert isinstance(issue["message"], str)


class TestDataQualityIntegration:
    """Test data quality integration scenarios."""

    def test_diabetes_patient_complete_workflow(self):
        """Test complete workflow for diabetes patient with good data quality."""
        diabetes_bundle = {
            "resourceType": "Bundle",
            "id": "diabetes-patient-001",
            "timestamp": "2025-07-31T10:30:00Z",
            "meta": {"source": "eClaimLink"},
            "claims": [
                {
                    "sequence": 1,
                    "diagnosis_code": "E11.9",  # Type 2 diabetes
                    "procedure_code": "99213",  # Office visit
                    "patient_id": "P123",
                }
            ],
            "services": [
                {
                    "sequence": 1,
                    "activity_code": "83036",  # HbA1c test
                    "diagnosis_code": "E11.9",
                }
            ],
            "raw_data": {"medications": "metformin 500mg"},
        }

        data_quality = DataQuality()
        result = data_quality.validate_fhir_bundle(diabetes_bundle)

        # Should have high quality score for complete diabetes care
        assert result["quality_score"].overall_score >= 0.8
        assert result["clinical_validation_passed"] is True

        # Should have minimal warnings
        warning_count = result["quality_score"].issues_count["warning"]
        error_count = result["quality_score"].issues_count["error"]
        assert error_count == 0
        assert warning_count <= 1  # May have info warnings

    def test_multi_condition_validation(self):
        """Test validation of patient with multiple conditions."""
        multi_condition_bundle = {
            "resourceType": "Bundle",
            "id": "multi-condition-001",
            "timestamp": "2025-07-31T10:30:00Z",
            "claims": [
                {
                    "sequence": 1,
                    "diagnosis_code": "E11.9",  # Diabetes
                    "procedure_code": "99213",
                },
                {
                    "sequence": 2,
                    "diagnosis_code": "I10",  # Hypertension
                    "procedure_code": "99214",
                },
            ],
            "services": [
                {"activity_code": "83036", "diagnosis_code": "E11.9"},  # HbA1c
                {"activity_code": "80053", "diagnosis_code": "I10"},  # Metabolic panel
            ],
        }

        data_quality = DataQuality()
        result = data_quality.validate_fhir_bundle(multi_condition_bundle)

        # Should validate all conditions properly
        assert result["quality_score"].code_validity >= 0.8

        # Check code validation summary
        summary = result["code_validation_summary"]
        assert summary["icd10_validated"] >= 2  # Two diagnosis codes
        assert summary["cpt_validated"] >= 2  # Two procedure codes


if __name__ == "__main__":
    """Run tests when executed directly."""
    pytest.main([__file__, "-v"])
