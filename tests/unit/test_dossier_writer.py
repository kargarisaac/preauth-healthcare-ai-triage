"""
Unit tests for DossierWriter class
"""

import pytest
from unittest.mock import Mock, patch
from preauth_system.dossier_writer import DossierWriter, generate_dossier
from preauth_system.signatures import FinalReportOutput


class TestDossierWriter:
    """Test suite for DossierWriter functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.clinical_summary = {
            "executive_summary": "Patient presents with Type 2 diabetes requiring CGM technology",
            "primary_diagnosis": {
                "code": "E11.9",
                "description": "Type 2 diabetes mellitus without complications"
            },
            "risk_factors": ["obesity", "hypertension", "family_history"]
        }
        
        self.checklist = {
            "overall_compliance_score": 0.85,
            "policy_source": "diabetes_technology.yaml",
            "criteria": [
                {
                    "criterion": "Diabetes diagnosis confirmed",
                    "status": "met",
                    "rationale": "Type 2 diabetes documented in medical history",
                    "required_evidence": ["diagnosis_code", "hba1c_results"]
                },
                {
                    "criterion": "CGM medical necessity",
                    "status": "met", 
                    "rationale": "Patient meets clinical criteria for continuous glucose monitoring",
                    "required_evidence": ["physician_prescription", "clinical_notes"]
                }
            ],
            "missing_documents": []
        }
        
        self.decision = {
            "outcome": "approved",
            "reason_code": "medically_necessary",
            "confidence_score": 0.92
        }
        
        self.evidence = [
            {
                "source": "diabetes_technology_guidelines",
                "content": "CGM is recommended for patients with frequent hypoglycemic episodes",
                "citation": "Ref 1"
            },
            {
                "source": "clinical_protocol",
                "content": "Patient demonstrates proper glucose management understanding",
                "citation": "Ref 2"
            }
        ]
        
        self.patient_context = {
            "age": "45",
            "gender": "female",
            "emirates_id": "784-1234-5678901-2",
            "policy_number": "POL-123456"
        }
    
    @patch('preauth_system.dossier_writer.with_dspy_lm')
    @patch('preauth_system.dossier_writer.get_module_lm')
    def test_dossier_writer_initialization(self, mock_get_lm, mock_with_lm):
        """Test DossierWriter initializes correctly."""
        mock_get_lm.return_value = Mock()
        
        writer = DossierWriter(language="en")
        
        assert writer.language == "en"
        mock_get_lm.assert_called_once_with("dossier_writer")
        assert hasattr(writer, 'report_generator')
    
    @patch('preauth_system.dossier_writer.with_dspy_lm')
    @patch('preauth_system.dossier_writer.get_module_lm')
    def test_dossier_generation_success(self, mock_get_lm, mock_with_lm):
        """Test successful dossier generation."""
        # Mock LLM response
        mock_lm = Mock()
        mock_get_lm.return_value = mock_lm
        
        mock_result = Mock()
        mock_final_report = FinalReportOutput(
            executive_summary="APPROVED: CGM technology authorized for diabetes management",
            clinical_context="45-year-old female with Type 2 diabetes mellitus",
            decision_rationale="Patient meets all clinical criteria for CGM technology",
            policy_analysis="85% compliance with diabetes technology policy requirements",
            risk_assessment="Low clinical risk with proper monitoring protocols",
            next_steps="Initiate CGM training and follow-up schedule",
            citations=["Ref 1: Clinical guidelines", "Ref 2: Policy documentation"]
        )
        mock_result.final_report = mock_final_report
        
        writer = DossierWriter()
        writer.report_generator = Mock(return_value=mock_result)
        
        result = writer.forward(
            clinical_summary=self.clinical_summary,
            checklist=self.checklist,
            decision=self.decision,
            evidence=self.evidence,
            patient_context=self.patient_context
        )
        
        # Verify structure
        assert "executive_summary" in result
        assert "sections" in result
        assert "citations" in result
        assert "metadata" in result
        
        # Verify content quality
        assert "APPROVED" in result["executive_summary"]
        assert len(result["sections"]) > 0
        assert result["metadata"]["sections_count"] > 0
        assert result["metadata"]["cost_estimate_usd"] <= 0.02
    
    @patch('preauth_system.dossier_writer.with_dspy_lm')
    @patch('preauth_system.dossier_writer.get_module_lm')
    def test_dossier_fallback_on_error(self, mock_get_lm, mock_with_lm):
        """Test fallback dossier generation on LLM error."""
        mock_lm = Mock()
        mock_get_lm.return_value = mock_lm
        
        writer = DossierWriter()
        writer.report_generator = Mock(side_effect=Exception("LLM error"))
        
        result = writer.forward(
            clinical_summary=self.clinical_summary,
            checklist=self.checklist,
            decision=self.decision,
            evidence=self.evidence
        )
        
        # Verify fallback structure
        assert "executive_summary" in result
        assert "sections" in result
        assert result["metadata"]["is_fallback"] is True
        assert result["metadata"]["cost_estimate_usd"] == 0.0
    
    def test_prepare_decision_context(self):
        """Test decision context preparation."""
        writer = DossierWriter()
        
        context = writer._prepare_decision_context(
            self.clinical_summary,
            self.checklist,
            self.decision,
            self.patient_context
        )
        
        # Verify key information is included
        assert "APPROVED" in context
        assert "Type 2 diabetes" in context
        assert "45 years old" in context
        assert "85.0%" in context  # compliance score
        assert "diabetes_technology.yaml" in context
    
    def test_prepare_evidence_context(self):
        """Test evidence context preparation."""
        writer = DossierWriter()
        
        context = writer._prepare_evidence_context(self.evidence, self.checklist)
        
        # Verify evidence and citations included
        assert "Ref 1" in context
        assert "Ref 2" in context
        assert "CGM is recommended" in context
        assert "Diabetes diagnosis confirmed: MET" in context
    
    def test_word_count_calculation(self):
        """Test word count calculation."""
        writer = DossierWriter()
        
        dossier = {
            "executive_summary": "This is a test summary with ten words total count",  # 11 words
            "sections": [
                {"content": "Section one has five words"},  # 5 words
                {"content": "Section two also has exactly six words"}  # 6 words
            ],
            "metadata": {}
        }
        
        word_count = writer._calculate_word_count(dossier)
        assert word_count == 22  # 11 + 5 + 6
    
    def test_cost_estimation(self):
        """Test cost estimation logic."""
        writer = DossierWriter()
        
        dossier = {
            "metadata": {
                "word_count": 500,
                "sections_count": 6
            }
        }
        
        cost = writer._estimate_cost(dossier)
        
        # Should be reasonable cost under cap
        assert 0.01 <= cost <= 0.02
    
    @patch('preauth_system.dossier_writer.DossierWriter')
    def test_convenience_function(self, mock_writer_class):
        """Test convenience function for direct usage."""
        mock_writer = Mock()
        mock_result = {"executive_summary": "Test result"}
        mock_writer.forward.return_value = mock_result
        mock_writer_class.return_value = mock_writer
        
        result = generate_dossier(
            clinical_summary=self.clinical_summary,
            checklist=self.checklist,
            decision=self.decision,
            evidence=self.evidence,
            language="en"
        )
        
        mock_writer_class.assert_called_once_with(language="en")
        mock_writer.forward.assert_called_once()
        assert result == mock_result
    
    def test_final_report_output_to_structured_dossier(self):
        """Test FinalReportOutput conversion to structured dossier."""
        report = FinalReportOutput(
            executive_summary="Test summary",
            clinical_context="Clinical info",
            decision_rationale="Decision reasoning",
            citations=["Ref 1", "Ref 2"]
        )
        
        dossier = report.to_structured_dossier()
        
        assert dossier["executive_summary"] == "Test summary"
        assert len(dossier["sections"]) == 3  # exec, clinical, decision
        assert dossier["citations"] == ["Ref 1", "Ref 2"]
        assert dossier["metadata"]["has_citations"] is True
        assert dossier["metadata"]["sections_count"] == 3