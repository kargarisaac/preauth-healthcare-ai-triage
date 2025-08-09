"""Unit tests for the summary module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any, List

from preauth_system.summary import (
    ClinicalSummary,
    ClinicalDataAggregator,
    build_clinical_summary
)
from preauth_system.intake import CanonicalPARequest


class TestClinicalSummary:
    """Test the ClinicalSummary dataclass."""
    
    def test_clinical_summary_creation(self):
        """Test creating a clinical summary."""
        summary = ClinicalSummary(
            patient_id="P123",
            emirates_id="784-1972-1234567-1",
            age=45,
            gender="M",
            active_conditions=[
                {"code": "E11.9", "description": "Type 2 diabetes"}
            ],
            primary_diagnoses=["E11.9"],
            current_medications=[
                {"name": "Metformin", "dose": "500mg", "frequency": "BID"}
            ],
            prior_treatments=[],
            treatment_responses=[],
            recent_labs=[
                {"test": "HbA1c", "value": 8.5, "date": "2025-07-01"}
            ],
            recent_imaging=[],
            recent_procedures=[],
            risk_factors=["Diabetes", "Hypertension"],
            allergies=["NKDA"],
            recent_claims=[],
            preauth_history=[],
            egfr_latest=75.0,
            kidney_function_stage="Stage 2",
            data_completeness_score=0.85,
            last_updated="2025-08-08T10:00:00Z"
        )
        
        assert summary.patient_id == "P123"
        assert summary.age == 45
        assert len(summary.active_conditions) == 1
        assert summary.egfr_latest == 75.0
        assert summary.data_completeness_score == 0.85
        
    def test_to_dict_conversion(self):
        """Test converting clinical summary to dictionary."""
        summary = ClinicalSummary(
            patient_id="P123",
            emirates_id="784-1972-1234567-1",
            age=45,
            gender="M",
            active_conditions=[{"code": "E11.9"}],
            primary_diagnoses=["E11.9"],
            current_medications=[{"name": "Metformin"}],
            prior_treatments=[],
            treatment_responses=[],
            recent_labs=[],
            recent_imaging=[],
            recent_procedures=[],
            risk_factors=["Diabetes"],
            allergies=[],
            recent_claims=[],
            preauth_history=[],
            egfr_latest=75.0,
            kidney_function_stage="Stage 2",
            data_completeness_score=0.85,
            last_updated="2025-08-08T10:00:00Z"
        )
        
        result = summary.to_dict()
        
        assert isinstance(result, dict)
        assert result["patient_id"] == "P123"
        assert result["egfr_latest"] == 75.0
        assert len(result["active_conditions"]) == 1


class TestClinicalDataAggregator:
    """Test the ClinicalDataAggregator class."""
    
    def test_aggregator_initialization(self):
        """Test aggregator initialization."""
        aggregator = ClinicalDataAggregator()
        
        assert aggregator.RECENT_PERIOD_MONTHS == 12
        assert aggregator.MAX_RECENT_LABS == 10
        assert aggregator.MAX_RECENT_CLAIMS == 5
        
    @patch('data_ingestion.etl.get_patient_data')
    def test_aggregate_patient_data_success(self, mock_get_data):
        """Test successful patient data aggregation."""
        # Mock patient data from ETL
        mock_get_data.return_value = {
            "patient_info": {
                "patient_id": "P123",
                "emirates_id": "784-1972-1234567-1",
                "age": 45,
                "gender": "M"
            },
            "conditions": [
                {
                    "code": "E11.9",
                    "description": "Type 2 diabetes",
                    "status": "active",
                    "onset_date": "2020-01-15"
                }
            ],
            "medications": [
                {
                    "name": "Metformin",
                    "dose": "500mg",
                    "frequency": "BID",
                    "start_date": "2020-02-01",
                    "status": "active"
                }
            ],
            "lab_results": [
                {
                    "test_name": "HbA1c",
                    "value": 8.5,
                    "unit": "%",
                    "date": "2025-07-01",
                    "reference_range": "<7.0"
                },
                {
                    "test_name": "Creatinine",
                    "value": 1.1,
                    "unit": "mg/dL",
                    "date": "2025-07-01"
                }
            ],
            "claims": [
                {
                    "claim_id": "C123",
                    "service_date": "2025-06-15",
                    "diagnosis_code": "E11.9",
                    "procedure_code": "99213",
                    "amount": 200.0
                }
            ]
        }
        
        aggregator = ClinicalDataAggregator()
        summary = aggregator.aggregate_patient_data("P123")
        
        assert isinstance(summary, ClinicalSummary)
        assert summary.patient_id == "P123"
        assert summary.age == 45
        assert len(summary.active_conditions) == 1
        assert len(summary.current_medications) == 1
        assert len(summary.recent_labs) == 2
        assert summary.egfr_latest is not None  # Should be calculated from creatinine
        
    @patch('data_ingestion.etl.get_patient_data')
    def test_aggregate_patient_data_missing_patient(self, mock_get_data):
        """Test aggregation when patient not found."""
        mock_get_data.return_value = None
        
        aggregator = ClinicalDataAggregator()
        
        with pytest.raises(ValueError, match="Patient P999 not found"):
            aggregator.aggregate_patient_data("P999")
            
    @patch('data_ingestion.etl.get_patient_data')
    def test_calculate_data_completeness_score(self, mock_get_data):
        """Test data completeness score calculation."""
        # Complete patient data
        mock_get_data.return_value = {
            "patient_info": {"patient_id": "P123", "age": 45, "gender": "M"},
            "conditions": [{"code": "E11.9", "status": "active"}],
            "medications": [{"name": "Metformin", "status": "active"}],
            "lab_results": [{"test_name": "HbA1c", "value": 8.5}],
            "claims": [{"claim_id": "C123"}]
        }
        
        aggregator = ClinicalDataAggregator()
        summary = aggregator.aggregate_patient_data("P123")
        
        # Should have high completeness score
        assert summary.data_completeness_score >= 0.8
        
        # Test with minimal data
        mock_get_data.return_value = {
            "patient_info": {"patient_id": "P124", "age": 45},
            "conditions": [],
            "medications": [],
            "lab_results": [],
            "claims": []
        }
        
        summary_minimal = aggregator.aggregate_patient_data("P124")
        
        # Should have lower completeness score
        assert summary_minimal.data_completeness_score < 0.5
        
    def test_filter_recent_data(self):
        """Test filtering data by recency."""
        aggregator = ClinicalDataAggregator()
        
        # Test data with various dates
        test_data = [
            {"date": "2025-07-01", "value": "recent"},
            {"date": "2024-01-01", "value": "old"},
            {"date": "2025-01-15", "value": "recent2"}
        ]
        
        recent_data = aggregator.filter_recent_data(test_data, months=6)
        
        # Should only include data from last 6 months
        assert len(recent_data) == 2
        assert all(item["value"].startswith("recent") for item in recent_data)
        
    def test_extract_risk_factors(self):
        """Test risk factor extraction from conditions and medications."""
        aggregator = ClinicalDataAggregator()
        
        conditions = [
            {"code": "E11.9", "description": "Type 2 diabetes"},
            {"code": "I10", "description": "Hypertension"}
        ]
        
        medications = [
            {"name": "Metformin", "indication": "diabetes"},
            {"name": "Lisinopril", "indication": "hypertension"}
        ]
        
        risk_factors = aggregator.extract_risk_factors(conditions, medications)
        
        assert "Diabetes" in risk_factors
        assert "Hypertension" in risk_factors
        assert len(risk_factors) >= 2
        
    @patch('preauth_system.utils.calculate_egfr')
    @patch('preauth_system.utils.get_latest_creatinine')
    def test_calculate_kidney_function(self, mock_get_creatinine, mock_calculate_egfr):
        """Test kidney function calculation."""
        mock_get_creatinine.return_value = 1.2
        mock_calculate_egfr.return_value = 65.5
        
        aggregator = ClinicalDataAggregator()
        
        lab_results = [
            {"test_name": "Creatinine", "value": 1.2, "date": "2025-07-01"},
            {"test_name": "HbA1c", "value": 8.5, "date": "2025-07-01"}
        ]
        
        egfr, stage = aggregator.calculate_kidney_function(
            lab_results, age=45, gender="M", race="other"
        )
        
        assert egfr == 65.5
        assert stage == "Stage 2"  # Based on eGFR 60-89
        
    def test_classify_kidney_stage(self):
        """Test kidney function stage classification."""
        aggregator = ClinicalDataAggregator()
        
        # Test different eGFR values
        assert aggregator.classify_kidney_stage(95) == "Stage 1"
        assert aggregator.classify_kidney_stage(75) == "Stage 2"
        assert aggregator.classify_kidney_stage(45) == "Stage 3a"
        assert aggregator.classify_kidney_stage(25) == "Stage 3b"
        assert aggregator.classify_kidney_stage(12) == "Stage 4"
        assert aggregator.classify_kidney_stage(8) == "Stage 5"


class TestBuildClinicalSummary:
    """Test the build_clinical_summary function."""
    
    @patch('preauth_system.summary.ClinicalDataAggregator')
    def test_build_clinical_summary_from_request(self, mock_aggregator_class):
        """Test building clinical summary from PA request."""
        # Mock aggregator instance
        mock_aggregator = MagicMock()
        mock_aggregator_class.return_value = mock_aggregator
        
        # Mock summary result
        mock_summary = ClinicalSummary(
            patient_id="P123",
            emirates_id="784-1972-1234567-1",
            age=45,
            gender="M",
            active_conditions=[{"code": "E11.9"}],
            primary_diagnoses=["E11.9"],
            current_medications=[{"name": "Metformin"}],
            prior_treatments=[],
            treatment_responses=[],
            recent_labs=[],
            recent_imaging=[],
            recent_procedures=[],
            risk_factors=["Diabetes"],
            allergies=[],
            recent_claims=[],
            preauth_history=[],
            egfr_latest=75.0,
            kidney_function_stage="Stage 2",
            data_completeness_score=0.85,
            last_updated="2025-08-08T10:00:00Z"
        )
        
        mock_aggregator.aggregate_patient_data.return_value = mock_summary
        
        # Create test PA request
        pa_request = CanonicalPARequest(
            request_id="TEST-001",
            timestamp="2025-08-08T10:00:00Z",
            format_source="eclaim",
            patient={"id": "P123", "name": "Test Patient"},
            provider={"id": "PROV001"},
            services=[{"code": "95250"}],
            justification="Test justification",
            diagnoses=[{"code": "E11.9"}],
            supporting_docs=[],
            validation_status="valid",
            validation_messages=[],
            total_cost=500.0,
            currency="AED"
        )
        
        result = build_clinical_summary(pa_request)
        
        assert isinstance(result, ClinicalSummary)
        assert result.patient_id == "P123"
        assert result.egfr_latest == 75.0
        
        # Verify aggregator was called with correct patient ID
        mock_aggregator.aggregate_patient_data.assert_called_once_with("P123")
        
    @patch('preauth_system.summary.ClinicalDataAggregator')
    def test_build_clinical_summary_missing_patient_id(self, mock_aggregator_class):
        """Test building clinical summary when patient ID is missing."""
        pa_request = CanonicalPARequest(
            request_id="TEST-001",
            timestamp="2025-08-08T10:00:00Z",
            format_source="eclaim",
            patient={},  # No patient ID
            provider={"id": "PROV001"},
            services=[],
            justification="Test",
            diagnoses=[],
            supporting_docs=[],
            validation_status="valid",
            validation_messages=[],
            total_cost=0.0,
            currency="AED"
        )
        
        with pytest.raises(ValueError, match="Patient ID not found"):
            build_clinical_summary(pa_request)
            
    @patch('preauth_system.summary.ClinicalDataAggregator')
    def test_build_clinical_summary_enrichment(self, mock_aggregator_class):
        """Test clinical summary enrichment with PA request data."""
        mock_aggregator = MagicMock()
        mock_aggregator_class.return_value = mock_aggregator
        
        base_summary = ClinicalSummary(
            patient_id="P123",
            emirates_id="784-1972-1234567-1",
            age=45,
            gender="M",
            active_conditions=[],
            primary_diagnoses=[],
            current_medications=[],
            prior_treatments=[],
            treatment_responses=[],
            recent_labs=[],
            recent_imaging=[],
            recent_procedures=[],
            risk_factors=[],
            allergies=[],
            recent_claims=[],
            preauth_history=[],
            egfr_latest=None,
            kidney_function_stage=None,
            data_completeness_score=0.5,
            last_updated="2025-08-08T10:00:00Z"
        )
        
        mock_aggregator.aggregate_patient_data.return_value = base_summary
        
        # PA request with additional diagnosis info
        pa_request = CanonicalPARequest(
            request_id="TEST-001",
            timestamp="2025-08-08T10:00:00Z",
            format_source="eclaim",
            patient={"id": "P123"},
            provider={"id": "PROV001"},
            services=[{"code": "95250", "description": "CGM"}],
            justification="Patient has poor glycemic control with HbA1c 8.5%",
            diagnoses=[{"code": "E11.9", "description": "Type 2 diabetes"}],
            supporting_docs=[],
            validation_status="valid",
            validation_messages=[],
            total_cost=500.0,
            currency="AED"
        )
        
        with patch('preauth_system.summary.enrich_summary_with_pa_data') as mock_enrich:
            mock_enrich.return_value = base_summary  # Return enriched summary
            
            result = build_clinical_summary(pa_request)
            
            # Verify enrichment was called
            mock_enrich.assert_called_once()


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    @patch('data_ingestion.etl.get_patient_data')
    def test_empty_patient_data(self, mock_get_data):
        """Test handling of empty patient data."""
        mock_get_data.return_value = {
            "patient_info": {"patient_id": "P123"},
            "conditions": [],
            "medications": [],
            "lab_results": [],
            "claims": []
        }
        
        aggregator = ClinicalDataAggregator()
        summary = aggregator.aggregate_patient_data("P123")
        
        assert summary.patient_id == "P123"
        assert len(summary.active_conditions) == 0
        assert summary.data_completeness_score < 0.5
        
    @patch('data_ingestion.etl.get_patient_data')
    def test_malformed_lab_results(self, mock_get_data):
        """Test handling of malformed lab results."""
        mock_get_data.return_value = {
            "patient_info": {"patient_id": "P123", "age": 45, "gender": "M"},
            "conditions": [],
            "medications": [],
            "lab_results": [
                {"test_name": "HbA1c", "value": "invalid", "date": "2025-07-01"},
                {"test_name": "Creatinine"},  # Missing value and date
                {}  # Empty result
            ],
            "claims": []
        }
        
        aggregator = ClinicalDataAggregator()
        summary = aggregator.aggregate_patient_data("P123")
        
        # Should handle malformed data gracefully
        assert isinstance(summary, ClinicalSummary)
        assert len(summary.recent_labs) >= 0  # May filter out invalid results
        
    def test_date_parsing_edge_cases(self):
        """Test edge cases in date parsing."""
        aggregator = ClinicalDataAggregator()
        
        # Test various date formats
        test_data = [
            {"date": "2025-07-01", "value": "iso_format"},
            {"date": "01/07/2025", "value": "slash_format"},
            {"date": "invalid_date", "value": "invalid"},
            {"value": "no_date"},  # Missing date
        ]
        
        # Should handle various date formats gracefully
        recent_data = aggregator.filter_recent_data(test_data, months=12)
        assert len(recent_data) >= 1  # At least valid dates should be included
        
    @patch('preauth_system.utils.calculate_egfr')
    def test_egfr_calculation_edge_cases(self, mock_calculate_egfr):
        """Test eGFR calculation edge cases."""
        # Test when calculation fails
        mock_calculate_egfr.side_effect = Exception("Calculation failed")
        
        aggregator = ClinicalDataAggregator()
        
        lab_results = [
            {"test_name": "Creatinine", "value": 1.2, "date": "2025-07-01"}
        ]
        
        egfr, stage = aggregator.calculate_kidney_function(
            lab_results, age=45, gender="M", race="other"
        )
        
        # Should handle calculation failure gracefully
        assert egfr is None
        assert stage is None


@pytest.mark.performance
class TestPerformance:
    """Test performance aspects of summary module."""
    
    @patch('data_ingestion.etl.get_patient_data')
    def test_large_dataset_aggregation_performance(self, mock_get_data, performance_monitor):
        """Test performance with large patient datasets."""
        # Mock large dataset
        mock_get_data.return_value = {
            "patient_info": {"patient_id": "P123", "age": 45, "gender": "M"},
            "conditions": [
                {"code": f"E11.{i}", "description": f"Condition {i}"}
                for i in range(50)
            ],
            "medications": [
                {"name": f"Medication_{i}", "dose": "500mg"}
                for i in range(20)
            ],
            "lab_results": [
                {"test_name": f"Test_{i}", "value": i * 10.0, "date": "2025-07-01"}
                for i in range(100)
            ],
            "claims": [
                {"claim_id": f"C{i}", "service_date": "2025-06-01", "amount": 100.0}
                for i in range(100)
            ]
        }
        
        performance_monitor.start()
        
        aggregator = ClinicalDataAggregator()
        summary = aggregator.aggregate_patient_data("P123")
        
        performance_monitor.stop()
        
        # Should process large dataset efficiently
        assert isinstance(summary, ClinicalSummary)
        assert len(summary.active_conditions) <= 50
        assert len(summary.recent_labs) <= aggregator.MAX_RECENT_LABS
        
        performance_monitor.assert_performance(max_time=3.0, max_memory_mb=100.0)
        
    def test_concurrent_summary_building(self, performance_monitor):
        """Test building summaries concurrently."""
        import concurrent.futures
        
        with patch('data_ingestion.etl.get_patient_data') as mock_get_data:
            mock_get_data.return_value = {
                "patient_info": {"patient_id": "P123", "age": 45, "gender": "M"},
                "conditions": [{"code": "E11.9"}],
                "medications": [{"name": "Metformin"}],
                "lab_results": [{"test_name": "HbA1c", "value": 8.5}],
                "claims": []
            }
            
            def build_summary(patient_id):
                aggregator = ClinicalDataAggregator()
                return aggregator.aggregate_patient_data(patient_id)
            
            performance_monitor.start()
            
            # Build summaries for multiple patients concurrently
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(build_summary, f"P{i}") for i in range(10)]
                summaries = [future.result() for future in futures]
                
            performance_monitor.stop()
            
            assert len(summaries) == 10
            assert all(isinstance(s, ClinicalSummary) for s in summaries)
            
            performance_monitor.assert_performance(max_time=5.0, max_memory_mb=200.0)
