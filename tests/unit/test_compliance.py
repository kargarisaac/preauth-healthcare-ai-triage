"""Unit tests for the compliance module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any, List

from preauth_system.compliance import (
    ComplianceValidator,
    ComplianceAssessment,
    ComplianceLevel,
    DocumentationType,
    DocumentationGap,
    PDPLAssessment,
    RegulatoryCompliance,
    validate_request_compliance
)
from preauth_system.state import PreAuthState


class TestComplianceLevel:
    """Test the ComplianceLevel enumeration."""
    
    def test_compliance_level_values(self):
        """Test compliance level enumeration values."""
        assert ComplianceLevel.COMPLIANT.value == "compliant"
        assert ComplianceLevel.MINOR_ISSUES.value == "minor_issues"
        assert ComplianceLevel.MAJOR_ISSUES.value == "major_issues"
        assert ComplianceLevel.NON_COMPLIANT.value == "non_compliant"
        
    def test_compliance_level_ordering(self):
        """Test compliance level implicit ordering for comparison."""
        levels = [ComplianceLevel.COMPLIANT, ComplianceLevel.MINOR_ISSUES, 
                 ComplianceLevel.MAJOR_ISSUES, ComplianceLevel.NON_COMPLIANT]
        
        assert len(levels) == 4
        assert ComplianceLevel.COMPLIANT in levels
        assert ComplianceLevel.NON_COMPLIANT in levels


class TestDocumentationGap:
    """Test the DocumentationGap dataclass."""
    
    def test_documentation_gap_creation(self):
        """Test creating a documentation gap."""
        gap = DocumentationGap(
            doc_type=DocumentationType.LAB_RESULTS,
            description="Recent HbA1c results required",
            requirement_level="required",
            next_steps="Upload HbA1c results from last 3 months",
            deadline_days=14
        )
        
        assert gap.doc_type == DocumentationType.LAB_RESULTS
        assert gap.requirement_level == "required"
        assert gap.deadline_days == 14
        assert "HbA1c" in gap.description
        
    def test_documentation_gap_optional_deadline(self):
        """Test documentation gap without deadline."""
        gap = DocumentationGap(
            doc_type=DocumentationType.CLINICAL_NOTES,
            description="Medical history review",
            requirement_level="recommended",
            next_steps="Provide detailed medical history"
        )
        
        assert gap.deadline_days is None
        assert gap.requirement_level == "recommended"


class TestPDPLAssessment:
    """Test the PDPLAssessment dataclass."""
    
    def test_pdpl_assessment_creation(self):
        """Test creating PDPL assessment."""
        assessment = PDPLAssessment(
            phi_elements_identified=["Emirates ID Number", "Patient demographics"],
            redaction_required=["Redact specific identifiers"],
            consent_status="valid",
            data_retention_period="7 years",
            cross_border_transfer=False
        )
        
        assert len(assessment.phi_elements_identified) == 2
        assert "Emirates ID" in assessment.phi_elements_identified[0]
        assert assessment.cross_border_transfer is False
        assert assessment.consent_status == "valid"


class TestRegulatoryCompliance:
    """Test the RegulatoryCompliance dataclass."""
    
    def test_regulatory_compliance_creation(self):
        """Test creating regulatory compliance assessment."""
        compliance = RegulatoryCompliance(
            dha_compliant=True,
            doh_compliant=True,
            licensing_valid=True,
            provider_network_status="in_network",
            regulatory_flags=[]
        )
        
        assert compliance.dha_compliant is True
        assert compliance.doh_compliant is True
        assert compliance.licensing_valid is True
        assert len(compliance.regulatory_flags) == 0
        
    def test_regulatory_compliance_with_flags(self):
        """Test regulatory compliance with warning flags."""
        compliance = RegulatoryCompliance(
            dha_compliant=False,
            doh_compliant=True,
            licensing_valid=True,
            provider_network_status="out_of_network",
            regulatory_flags=["DHA format validation required"]
        )
        
        assert compliance.dha_compliant is False
        assert len(compliance.regulatory_flags) == 1
        assert "DHA" in compliance.regulatory_flags[0]


class TestComplianceValidator:
    """Test the ComplianceValidator class."""
    
    def test_validator_initialization(self):
        """Test compliance validator initialization."""
        validator = ComplianceValidator()
        
        assert hasattr(validator, 'required_fields')
        assert hasattr(validator, 'phi_patterns')
        assert hasattr(validator, 'regulatory_requirements')
        
        # Verify initialization loads data
        assert isinstance(validator.required_fields, dict)
        assert isinstance(validator.phi_patterns, list)
        assert isinstance(validator.regulatory_requirements, dict)
        
    def test_validate_compliance_minimal_data(self):
        """Test compliance validation with minimal data."""
        validator = ComplianceValidator()
        
        # Minimal state with no patient data
        state = {
            'xml_format': 'eclaim',
            'patient_info': {},
            'patient_data': {}
        }
        
        assessment = validator.validate_compliance(state, ["95250"], ["E11.9"])
        
        assert isinstance(assessment, ComplianceAssessment)
        assert assessment.overall_level in [ComplianceLevel.MAJOR_ISSUES, ComplianceLevel.NON_COMPLIANT]
        assert len(assessment.documentation_gaps) > 0
        assert assessment.completion_score < 0.5
        
    def test_validate_compliance_complete_data(self):
        """Test compliance validation with complete data."""
        validator = ComplianceValidator()
        
        # Complete state with all required data
        state = {
            'xml_format': 'eclaim',
            'patient_info': {
                'EmiratesIDNumber': '784-1972-1234567-1',
                'services': [{'code': '95250'}],
                'justification': 'Patient with Type 2 diabetes requiring continuous glucose monitoring for optimal glycemic control due to frequent hypoglycemic episodes despite current medication regimen.'
            },
            'patient_data': {
                'demographics': {'age': 45, 'gender': 'M'},
                'labs': [
                    {
                        'name': 'HbA1c',
                        'value': 8.5,
                        'date': datetime.now().strftime('%Y-%m-%d')
                    }
                ],
                'medications': [
                    {
                        'name': 'Metformin',
                        'dose': '500mg BID',
                        'start_date': '2024-01-01'
                    }
                ],
                'claims': [
                    {
                        'claim_id': 'C123',
                        'service_date': '2025-07-01'
                    }
                ]
            }
        }
        
        assessment = validator.validate_compliance(state, ["95250"], ["E11.9"])
        
        assert isinstance(assessment, ComplianceAssessment)
        assert assessment.overall_level in [ComplianceLevel.COMPLIANT, ComplianceLevel.MINOR_ISSUES]
        assert assessment.completion_score > 0.7
        assert len(assessment.next_steps) >= 1
        
    def test_validate_compliance_error_handling(self):
        """Test compliance validation error handling."""
        validator = ComplianceValidator()
        
        # Test with invalid state that would cause errors
        with patch.object(validator, '_check_documentation_completeness') as mock_check:
            mock_check.side_effect = Exception("Test error")
            
            assessment = validator.validate_compliance({}, [], [])
            
            assert assessment.overall_level == ComplianceLevel.MAJOR_ISSUES
            assert "error" in assessment.rationale.lower()
            assert len(assessment.next_steps) > 0
            
    def test_check_documentation_completeness_missing_emirates_id(self):
        """Test documentation completeness check - missing Emirates ID."""
        validator = ComplianceValidator()
        
        state = {
            'patient_info': {},  # Missing Emirates ID
            'patient_data': {}
        }
        
        gaps = validator._check_documentation_completeness(state, ["95250"])
        
        # Should identify Emirates ID gap
        emirates_id_gap = next(
            (g for g in gaps if "emirates id" in g.description.lower()), None
        )
        assert emirates_id_gap is not None
        assert emirates_id_gap.requirement_level == "required"
        assert emirates_id_gap.deadline_days == 1
        
    def test_check_documentation_completeness_insufficient_justification(self):
        """Test documentation completeness check - insufficient justification."""
        validator = ComplianceValidator()
        
        state = {
            'patient_info': {
                'justification': 'Short text'  # Too short
            },
            'patient_data': {}
        }
        
        gaps = validator._check_documentation_completeness(state, ["95250"])
        
        # Should identify justification gap
        justification_gap = next(
            (g for g in gaps if "justification" in g.description.lower()), None
        )
        assert justification_gap is not None
        assert justification_gap.requirement_level == "required"
        
    def test_check_service_specific_documentation_diabetes(self):
        """Test service-specific documentation for diabetes technology."""
        validator = ComplianceValidator()
        
        state = {
            'patient_data': {
                'labs': []  # No recent labs
            }
        }
        
        gaps = validator._check_service_specific_documentation("95250", state)
        
        # Should require HbA1c for CGM
        hba1c_gap = next(
            (g for g in gaps if "hba1c" in g.description.lower()), None
        )
        assert hba1c_gap is not None
        assert hba1c_gap.doc_type == DocumentationType.LAB_RESULTS
        assert hba1c_gap.requirement_level == "required"
        
    def test_check_service_specific_documentation_orthopedic(self):
        """Test service-specific documentation for orthopedic procedures."""
        validator = ComplianceValidator()
        
        state = {'patient_data': {}}
        
        gaps = validator._check_service_specific_documentation("29881", state)
        
        # Should require imaging and physical therapy
        imaging_gap = next(
            (g for g in gaps if "imaging" in g.description.lower()), None
        )
        pt_gap = next(
            (g for g in gaps if "physical therapy" in g.description.lower()), None
        )
        
        assert imaging_gap is not None
        assert pt_gap is not None
        assert imaging_gap.doc_type == DocumentationType.IMAGING_REPORTS
        
    def test_check_service_specific_documentation_dbs(self):
        """Test service-specific documentation for DBS procedures."""
        validator = ComplianceValidator()
        
        state = {'patient_data': {}}
        
        gaps = validator._check_service_specific_documentation("61885", state)
        
        # Should require multiple specialized assessments
        specialist_gap = next(
            (g for g in gaps if "specialist" in g.description.lower()), None
        )
        cognitive_gap = next(
            (g for g in gaps if "cognitive" in g.description.lower()), None
        )
        
        assert specialist_gap is not None
        assert cognitive_gap is not None
        assert specialist_gap.requirement_level == "required"
        assert cognitive_gap.requirement_level == "required"
        
    def test_assess_pdpl_compliance_no_phi(self):
        """Test PDPL compliance assessment with no PHI."""
        validator = ComplianceValidator()
        
        state = {
            'patient_info': {
                'justification': 'Generic medical request for treatment'
            },
            'patient_data': {}
        }
        
        assessment = validator._assess_pdpl_compliance(state)
        
        assert isinstance(assessment, PDPLAssessment)
        assert len(assessment.phi_elements_identified) == 0
        assert len(assessment.redaction_required) == 0
        assert assessment.consent_status == "assumed_valid"
        
    def test_assess_pdpl_compliance_with_phi(self):
        """Test PDPL compliance assessment with PHI present."""
        validator = ComplianceValidator()
        
        state = {
            'patient_info': {
                'EmiratesIDNumber': '784-1972-1234567-1',
                'justification': 'Patient John Smith needs treatment'
            },
            'patient_data': {
                'demographics': {'name': 'John Smith'},
                'labs': [{'test': 'HbA1c', 'value': 8.5}]
            }
        }
        
        assessment = validator._assess_pdpl_compliance(state)
        
        assert len(assessment.phi_elements_identified) > 0
        assert "Emirates ID" in assessment.phi_elements_identified[0]
        assert assessment.data_retention_period == "7 years per UAE healthcare standards"
        
    def test_check_regulatory_compliance_eclaim(self):
        """Test regulatory compliance for eClaimLink format."""
        validator = ComplianceValidator()
        
        state = {'xml_format': 'eclaim'}
        
        compliance = validator._check_regulatory_compliance(state)
        
        assert isinstance(compliance, RegulatoryCompliance)
        assert compliance.dha_compliant is True
        assert compliance.licensing_valid is True
        assert compliance.provider_network_status == "in_network"
        
    def test_check_regulatory_compliance_shafafiya(self):
        """Test regulatory compliance for Shafafiya format."""
        validator = ComplianceValidator()
        
        state = {'xml_format': 'shafafiya'}
        
        compliance = validator._check_regulatory_compliance(state)
        
        assert compliance.doh_compliant is True
        assert len(compliance.regulatory_flags) <= 1  # May have format warnings
        
    def test_check_regulatory_compliance_unknown_format(self):
        """Test regulatory compliance for unknown format."""
        validator = ComplianceValidator()
        
        state = {'xml_format': 'unknown'}
        
        compliance = validator._check_regulatory_compliance(state)
        
        assert compliance.dha_compliant is False
        assert compliance.doh_compliant is False
        assert len(compliance.regulatory_flags) > 0
        assert any("unknown" in flag.lower() for flag in compliance.regulatory_flags)
        
    def test_calculate_completion_score_high_quality(self):
        """Test completion score calculation with high-quality data."""
        validator = ComplianceValidator()
        
        state = {
            'patient_info': {
                'EmiratesIDNumber': '784-1972-1234567-1',
                'services': [{'code': '95250'}],
                'justification': 'Detailed medical justification with sufficient clinical context and treatment history information.'
            },
            'patient_data': {
                'demographics': {'age': 45, 'gender': 'M'},
                'labs': [{'test': 'HbA1c', 'value': 8.5}],
                'medications': [{'name': 'Metformin'}],
                'claims': [{'claim_id': 'C123'}]
            }
        }
        
        gaps = []  # No gaps for high-quality data
        score = validator._calculate_completion_score(gaps, state)
        
        assert score >= 0.8
        assert score <= 1.0
        
    def test_calculate_completion_score_poor_quality(self):
        """Test completion score calculation with poor-quality data."""
        validator = ComplianceValidator()
        
        state = {
            'patient_info': {},
            'patient_data': {}
        }
        
        gaps = [
            DocumentationGap(
                doc_type=DocumentationType.LAB_RESULTS,
                description="Test gap",
                requirement_level="required",
                next_steps="Fix it"
            )
        ]
        
        score = validator._calculate_completion_score(gaps, state)
        
        assert score < 0.5
        assert score >= 0.0
        
    def test_determine_compliance_level_compliant(self):
        """Test compliance level determination - compliant case."""
        validator = ComplianceValidator()
        
        gaps = []  # No gaps
        pdpl_assessment = PDPLAssessment(
            phi_elements_identified=[],
            redaction_required=[],
            consent_status="valid",
            data_retention_period="7 years"
        )
        regulatory_compliance = RegulatoryCompliance(
            dha_compliant=True,
            doh_compliant=True,
            licensing_valid=True,
            provider_network_status="in_network",
            regulatory_flags=[]
        )
        completion_score = 0.95
        
        level = validator._determine_compliance_level(
            gaps, pdpl_assessment, regulatory_compliance, completion_score
        )
        
        assert level == ComplianceLevel.COMPLIANT
        
    def test_determine_compliance_level_non_compliant(self):
        """Test compliance level determination - non-compliant case."""
        validator = ComplianceValidator()
        
        gaps = []
        pdpl_assessment = PDPLAssessment(
            phi_elements_identified=[],
            redaction_required=[],
            consent_status="valid",
            data_retention_period="7 years"
        )
        regulatory_compliance = RegulatoryCompliance(
            dha_compliant=False,
            doh_compliant=False,
            licensing_valid=False,
            provider_network_status="unknown",
            regulatory_flags=["Critical regulatory issues"]
        )
        completion_score = 0.3
        
        level = validator._determine_compliance_level(
            gaps, pdpl_assessment, regulatory_compliance, completion_score
        )
        
        assert level == ComplianceLevel.NON_COMPLIANT
        
    def test_determine_compliance_level_major_issues(self):
        """Test compliance level determination - major issues case."""
        validator = ComplianceValidator()
        
        # Create multiple required gaps
        gaps = [
            DocumentationGap(
                doc_type=DocumentationType.LAB_RESULTS,
                description="Gap 1",
                requirement_level="required",
                next_steps="Fix 1"
            ),
            DocumentationGap(
                doc_type=DocumentationType.CLINICAL_NOTES,
                description="Gap 2",
                requirement_level="required",
                next_steps="Fix 2"
            ),
            DocumentationGap(
                doc_type=DocumentationType.IMAGING_REPORTS,
                description="Gap 3",
                requirement_level="required",
                next_steps="Fix 3"
            )
        ]
        
        pdpl_assessment = PDPLAssessment(
            phi_elements_identified=[],
            redaction_required=[],
            consent_status="valid",
            data_retention_period="7 years"
        )
        regulatory_compliance = RegulatoryCompliance(
            dha_compliant=True,
            doh_compliant=True,
            licensing_valid=True,
            provider_network_status="in_network",
            regulatory_flags=[]
        )
        completion_score = 0.4
        
        level = validator._determine_compliance_level(
            gaps, pdpl_assessment, regulatory_compliance, completion_score
        )
        
        assert level == ComplianceLevel.MAJOR_ISSUES
        
    def test_generate_next_steps_with_gaps(self):
        """Test next steps generation with documentation gaps."""
        validator = ComplianceValidator()
        
        gaps = [
            DocumentationGap(
                doc_type=DocumentationType.LAB_RESULTS,
                description="HbA1c required",
                requirement_level="required",
                next_steps="Upload recent HbA1c results"
            ),
            DocumentationGap(
                doc_type=DocumentationType.IMAGING_REPORTS,
                description="Imaging required",
                requirement_level="recommended",
                next_steps="Upload imaging studies"
            )
        ]
        
        pdpl_assessment = PDPLAssessment(
            phi_elements_identified=[],
            redaction_required=["Redact personal info"],
            consent_status="valid",
            data_retention_period="7 years"
        )
        
        regulatory_compliance = RegulatoryCompliance(
            dha_compliant=True,
            doh_compliant=True,
            licensing_valid=True,
            provider_network_status="in_network",
            regulatory_flags=[]
        )
        
        next_steps = validator._generate_next_steps(
            gaps, pdpl_assessment, regulatory_compliance
        )
        
        assert len(next_steps) >= 1
        assert any("hba1c" in step.lower() for step in next_steps)
        assert any("redact" in step.lower() for step in next_steps)
        
    def test_estimate_review_time(self):
        """Test review time estimation."""
        validator = ComplianceValidator()
        
        # Compliant case
        time_compliant = validator._estimate_review_time(ComplianceLevel.COMPLIANT, [])
        assert "0-1" in time_compliant
        
        # Minor issues
        time_minor = validator._estimate_review_time(ComplianceLevel.MINOR_ISSUES, [])
        assert "1-3" in time_minor
        
        # Major issues with deadlines
        gaps = [
            DocumentationGap(
                doc_type=DocumentationType.LAB_RESULTS,
                description="Test gap",
                requirement_level="required",
                next_steps="Fix it",
                deadline_days=14
            )
        ]
        time_major = validator._estimate_review_time(ComplianceLevel.MAJOR_ISSUES, gaps)
        assert "14" in time_major
        
    def test_generate_compliance_rationale(self):
        """Test compliance rationale generation."""
        validator = ComplianceValidator()
        
        gaps = [
            DocumentationGap(
                doc_type=DocumentationType.LAB_RESULTS,
                description="Required gap",
                requirement_level="required",
                next_steps="Fix it"
            ),
            DocumentationGap(
                doc_type=DocumentationType.CLINICAL_NOTES,
                description="Recommended gap",
                requirement_level="recommended",
                next_steps="Improve it"
            )
        ]
        
        rationale = validator._generate_compliance_rationale(
            ComplianceLevel.MINOR_ISSUES, gaps, 0.75
        )
        
        assert "75.0%" in rationale  # Completion score
        assert "1 required" in rationale
        assert "1 recommended" in rationale
        assert "minor" in rationale.lower()
        
    def test_has_recent_lab_found(self):
        """Test recent lab detection - lab found."""
        validator = ComplianceValidator()
        
        state = {
            'patient_data': {
                'labs': [
                    {
                        'name': 'Hemoglobin A1c',
                        'value': 8.5,
                        'date': datetime.now().strftime('%Y-%m-%d')
                    }
                ]
            }
        }
        
        has_lab = validator._has_recent_lab(state, "HbA1c", days=90)
        assert has_lab is True
        
    def test_has_recent_lab_not_found(self):
        """Test recent lab detection - lab not found."""
        validator = ComplianceValidator()
        
        state = {
            'patient_data': {
                'labs': [
                    {
                        'name': 'Glucose',
                        'value': 120,
                        'date': (datetime.now() - timedelta(days=120)).strftime('%Y-%m-%d')
                    }
                ]
            }
        }
        
        has_lab = validator._has_recent_lab(state, "HbA1c", days=90)
        assert has_lab is False
        
    def test_has_recent_lab_too_old(self):
        """Test recent lab detection - lab too old."""
        validator = ComplianceValidator()
        
        state = {
            'patient_data': {
                'labs': [
                    {
                        'name': 'HbA1c',
                        'value': 8.5,
                        'date': (datetime.now() - timedelta(days=120)).strftime('%Y-%m-%d')
                    }
                ]
            }
        }
        
        has_lab = validator._has_recent_lab(state, "HbA1c", days=90)
        assert has_lab is False
        
    def test_contains_phi_positive(self):
        """Test PHI detection - PHI present."""
        validator = ComplianceValidator()
        
        text_with_phi = "Patient 784-1972-1234567-1 needs treatment"
        contains_phi = validator._contains_phi(text_with_phi)
        
        assert contains_phi is True
        
    def test_contains_phi_negative(self):
        """Test PHI detection - no PHI."""
        validator = ComplianceValidator()
        
        text_without_phi = "Patient requires diabetes monitoring"
        contains_phi = validator._contains_phi(text_without_phi)
        
        assert contains_phi is False
        
    def test_contains_phi_empty_text(self):
        """Test PHI detection - empty text."""
        validator = ComplianceValidator()
        
        contains_phi = validator._contains_phi("")
        assert contains_phi is False
        
        contains_phi = validator._contains_phi(None)
        assert contains_phi is False


class TestValidateRequestCompliance:
    """Test the main validate_request_compliance function."""
    
    def test_validate_request_compliance_basic(self):
        """Test basic compliance validation."""
        state = {
            'xml_format': 'eclaim',
            'patient_info': {
                'EmiratesIDNumber': '784-1972-1234567-1',
                'services': [{'code': '95250'}],
                'justification': 'Patient needs CGM for diabetes management due to poor glycemic control.'
            },
            'patient_data': {
                'demographics': {'age': 45},
                'labs': [],
                'medications': [],
                'claims': []
            }
        }
        
        assessment = validate_request_compliance(
            state=state,
            service_codes=["95250"],
            diagnosis_codes=["E11.9"]
        )
        
        assert isinstance(assessment, ComplianceAssessment)
        assert assessment.overall_level in [
            ComplianceLevel.COMPLIANT,
            ComplianceLevel.MINOR_ISSUES,
            ComplianceLevel.MAJOR_ISSUES
        ]
        assert isinstance(assessment.completion_score, float)
        assert 0.0 <= assessment.completion_score <= 1.0
        assert isinstance(assessment.next_steps, list)
        assert len(assessment.next_steps) > 0
        
    def test_validate_request_compliance_empty_state(self):
        """Test compliance validation with empty state."""
        state = {}
        
        assessment = validate_request_compliance(
            state=state,
            service_codes=[],
            diagnosis_codes=[]
        )
        
        assert isinstance(assessment, ComplianceAssessment)
        assert assessment.overall_level in [
            ComplianceLevel.MAJOR_ISSUES,
            ComplianceLevel.NON_COMPLIANT
        ]
        assert assessment.completion_score < 0.5
        assert len(assessment.documentation_gaps) > 0
        
    def test_validate_request_compliance_multiple_services(self):
        """Test compliance validation with multiple service codes."""
        state = {
            'xml_format': 'eclaim',
            'patient_info': {
                'EmiratesIDNumber': '784-1972-1234567-1',
                'services': [{'code': '95250'}, {'code': '29881'}],
                'justification': 'Multi-service request for comprehensive diabetes and orthopedic care.'
            },
            'patient_data': {}
        }
        
        assessment = validate_request_compliance(
            state=state,
            service_codes=["95250", "29881"],
            diagnosis_codes=["E11.9", "M17.9"]
        )
        
        assert isinstance(assessment, ComplianceAssessment)
        # Should have more gaps due to multiple specialized services
        diabetes_gaps = [g for g in assessment.documentation_gaps if "hba1c" in g.description.lower()]
        ortho_gaps = [g for g in assessment.documentation_gaps if "imaging" in g.description.lower() or "physical therapy" in g.description.lower()]
        
        assert len(diabetes_gaps) > 0
        assert len(ortho_gaps) > 0


class TestComplianceAssessmentIntegration:
    """Test compliance assessment integration scenarios."""
    
    def test_diabetes_cgm_compliance_complete(self):
        """Test compliance for diabetes CGM with complete documentation."""
        state = {
            'xml_format': 'eclaim',
            'patient_info': {
                'EmiratesIDNumber': '784-1972-1234567-1',
                'services': [{'code': '95250'}],
                'justification': 'Patient with Type 2 diabetes mellitus, HbA1c 8.5%, requiring CGM for improved glucose monitoring and reduction of hypoglycemic episodes. Current therapy with metformin 1000mg BID is insufficient for optimal glycemic control.'
            },
            'patient_data': {
                'demographics': {
                    'age': 35,
                    'gender': 'M',
                    'birth_date': '1990-01-01'
                },
                'labs': [
                    {
                        'name': 'Hemoglobin A1c',
                        'value': 8.5,
                        'unit': '%',
                        'date': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                    }
                ],
                'medications': [
                    {
                        'name': 'Metformin',
                        'dose': '1000mg BID',
                        'start_date': '2024-01-01'
                    }
                ],
                'claims': [
                    {
                        'claim_id': 'C123',
                        'service_date': '2025-07-01',
                        'diagnosis_code': 'E11.9'
                    }
                ]
            }
        }
        
        assessment = validate_request_compliance(
            state=state,
            service_codes=["95250"],
            diagnosis_codes=["E11.9"]
        )
        
        assert assessment.overall_level in [ComplianceLevel.COMPLIANT, ComplianceLevel.MINOR_ISSUES]
        assert assessment.completion_score >= 0.8
        assert assessment.regulatory_compliance.dha_compliant is True
        
        # Should have minimal required gaps
        required_gaps = [g for g in assessment.documentation_gaps if g.requirement_level == "required"]
        assert len(required_gaps) <= 2  # At most minor required items
        
    def test_parkinson_dbs_compliance_incomplete(self):
        """Test compliance for Parkinson's DBS with incomplete documentation."""
        state = {
            'xml_format': 'eclaim',
            'patient_info': {
                'EmiratesIDNumber': '784-1978-7654321-2',
                'services': [{'code': '61885'}],
                'justification': 'Patient with Parkinson disease requesting DBS'
            },
            'patient_data': {
                'demographics': {
                    'age': 72,
                    'gender': 'M'
                },
                'medications': [
                    {
                        'name': 'Levodopa',
                        'dose': '100mg TID'
                    }
                ]
            }
        }
        
        assessment = validate_request_compliance(
            state=state,
            service_codes=["61885"],
            diagnosis_codes=["G20"]
        )
        
        assert assessment.overall_level in [ComplianceLevel.MAJOR_ISSUES, ComplianceLevel.NON_COMPLIANT]
        assert assessment.completion_score < 0.7
        
        # Should have multiple required gaps for specialized procedure
        required_gaps = [g for g in assessment.documentation_gaps if g.requirement_level == "required"]
        assert len(required_gaps) >= 3
        
        # Check for specific DBS requirements
        specialist_gap = next(
            (g for g in required_gaps if "specialist" in g.description.lower()), None
        )
        cognitive_gap = next(
            (g for g in required_gaps if "cognitive" in g.description.lower()), None
        )
        
        assert specialist_gap is not None
        assert cognitive_gap is not None


class TestComplianceEdgeCases:
    """Test edge cases and error conditions in compliance module."""
    
    def test_compliance_with_malformed_dates(self):
        """Test compliance handling with malformed date strings."""
        validator = ComplianceValidator()
        
        state = {
            'patient_data': {
                'labs': [
                    {
                        'name': 'HbA1c',
                        'value': 8.5,
                        'date': 'invalid_date_string'
                    },
                    {
                        'name': 'Glucose',
                        'value': 200,
                        'date': '2025-13-45'  # Invalid date
                    }
                ]
            }
        }
        
        # Should not crash and should conservatively assume no recent labs
        has_recent = validator._has_recent_lab(state, "HbA1c", days=90)
        assert has_recent is False
        
    def test_compliance_with_none_values(self):
        """Test compliance handling with None values in data."""
        validator = ComplianceValidator()
        
        state = {
            'patient_info': {
                'EmiratesIDNumber': None,
                'services': None,
                'justification': None
            },
            'patient_data': {
                'labs': None,
                'medications': None
            }
        }
        
        # Should not crash
        assessment = validator.validate_compliance(state, ["95250"], ["E11.9"])
        
        assert isinstance(assessment, ComplianceAssessment)
        assert assessment.overall_level in [ComplianceLevel.MAJOR_ISSUES, ComplianceLevel.NON_COMPLIANT]
        
    def test_compliance_with_empty_service_codes(self):
        """Test compliance with empty service code list."""
        state = {
            'xml_format': 'eclaim',
            'patient_info': {
                'EmiratesIDNumber': '784-1972-1234567-1',
                'justification': 'Test request'
            }
        }
        
        assessment = validate_request_compliance(
            state=state,
            service_codes=[],
            diagnosis_codes=[]
        )
        
        assert isinstance(assessment, ComplianceAssessment)
        # Should still identify gaps for missing services
        service_gap = next(
            (g for g in assessment.documentation_gaps 
             if "service" in g.description.lower() or "procedure" in g.description.lower()),
            None
        )
        assert service_gap is not None


@pytest.mark.performance
class TestCompliancePerformance:
    """Test performance aspects of compliance module."""
    
    def test_compliance_validation_performance(self, performance_monitor):
        """Test performance of compliance validation with complex data."""
        # Create complex state with lots of data
        state = {
            'xml_format': 'eclaim',
            'patient_info': {
                'EmiratesIDNumber': '784-1972-1234567-1',
                'services': [{'code': f'CODE{i}'} for i in range(20)],
                'justification': 'Complex multi-service request with extensive clinical justification and detailed medical history information spanning multiple specialties and treatment modalities.'
            },
            'patient_data': {
                'demographics': {'age': 65, 'gender': 'M'},
                'labs': [
                    {
                        'name': f'Test_{i}',
                        'value': i * 10,
                        'date': (datetime.now() - timedelta(days=i*5)).strftime('%Y-%m-%d')
                    }
                    for i in range(50)
                ],
                'medications': [
                    {
                        'name': f'Medication_{i}',
                        'dose': f'{100+i*50}mg',
                        'start_date': '2024-01-01'
                    }
                    for i in range(30)
                ],
                'claims': [
                    {
                        'claim_id': f'C{i}',
                        'service_date': '2025-07-01'
                    }
                    for i in range(100)
                ]
            }
        }
        
        performance_monitor.start()
        
        assessment = validate_request_compliance(
            state=state,
            service_codes=[f'CODE{i}' for i in range(20)],
            diagnosis_codes=[f'E11.{i}' for i in range(10)]
        )
        
        performance_monitor.stop()
        
        # Should complete complex compliance validation quickly
        assert isinstance(assessment, ComplianceAssessment)
        performance_monitor.assert_performance(max_time=2.0, max_memory_mb=100.0)
        
    def test_batch_compliance_validation(self, performance_monitor):
        """Test batch compliance validation performance."""
        states = []
        
        # Create multiple states for batch processing
        for i in range(10):
            states.append({
                'xml_format': 'eclaim',
                'patient_info': {
                    'EmiratesIDNumber': f'784-1972-123456{i}-1',
                    'services': [{'code': '95250'}],
                    'justification': f'Patient {i} requires diabetes management'
                },
                'patient_data': {
                    'demographics': {'age': 40 + i, 'gender': 'M'},
                    'labs': [{'name': 'HbA1c', 'value': 8.0 + i*0.1}]
                }
            })
        
        performance_monitor.start()
        
        assessments = []
        for state in states:
            assessment = validate_request_compliance(
                state=state,
                service_codes=["95250"],
                diagnosis_codes=["E11.9"]
            )
            assessments.append(assessment)
        
        performance_monitor.stop()
        
        # Should process batch efficiently
        assert len(assessments) == 10
        assert all(isinstance(a, ComplianceAssessment) for a in assessments)
        performance_monitor.assert_performance(max_time=3.0, max_memory_mb=200.0)
