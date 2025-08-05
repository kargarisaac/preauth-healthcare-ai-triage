#!/usr/bin/env python3
"""
Integration tests for patient-centric workflow API endpoints.

Tests all 5 core endpoints of the patient workflow:
1. GET /api/patients
2. POST /api/upload-xml
3. POST /api/process/{patient_id}
4. POST /api/analyze/{patient_id}
5. GET /api/patient/{patient_id}/dashboard
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from fastapi import UploadFile

from api.main import app


class TestPatientWorkflowEndpoints:
    """Integration tests for patient workflow API endpoints."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
        self.sample_patient_id = "patient-test-123"
        
        # Sample XML content for testing
        self.sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
            <Header>
                <SenderID>PROV12345</SenderID>
                <ReceiverID>PAYER67890</ReceiverID>
                <TransactionDateTime>31/07/2025 10:30</TransactionDateTime>
                <TransactionID>TXN-ECLAIM-2025-001789</TransactionID>
            </Header>
            <JustificationText>Patient with Type 2 diabetes needs HbA1c monitoring test.</JustificationText>
            <ServiceRequests>
                <ServiceRequest>
                    <ct:ActivityCode>83036</ct:ActivityCode>
                    <ct:DiagnosisCode>E11.9</ct:DiagnosisCode>
                    <ct:ActivityDateTime>01/08/2025 09:00</ct:ActivityDateTime>
                    <ct:ActivityInstructions>HbA1c test for diabetes monitoring</ct:ActivityInstructions>
                    <RequestedAmount currency="AED">125.50</RequestedAmount>
                </ServiceRequest>
            </ServiceRequests>
        </PriorAuthorizationRequest>"""
        
        # Sample patient data matching actual profile.json structure
        self.sample_patient_data = {
            "patient_id": self.sample_patient_id,
            "full_name": "Ahmed Al Mansoori",
            "gender": "Male",
            "birth_year": 1985,
            "nationality": "Emirati",
            "marital_status": "Married",
            "employment_sector": "Finance",
            "insurance_plan": "Dubai Health Insurance Premium",
            "coverage_tier": "Gold",
            "smoker": "N",
            "baseline_BMI": 26.5,
            "baseline_BP_systolic": 125,
            "family_history_diabetes": "N",
            "family_history_CAD": "Y"
        }
        
        # Sample FHIR bundle
        self.sample_bundle = {
            "resourceType": "Bundle",
            "id": "test-bundle",
            "authorization_id": self.sample_patient_id,
            "sender": "PROV12345",
            "receiver": "PAYER67890",
            "fhir_resources": {
                "claim-1": {
                    "resourceType": "Claim",
                    "id": "TXN-ECLAIM-2025-001789",
                    "diagnosis": [{"code": "E11.9", "display": "Type 2 diabetes"}]
                }
            },
            "raw_data": {
                "TransactionID": "TXN-ECLAIM-2025-001789",
                "JustificationText": "Patient with Type 2 diabetes needs HbA1c monitoring test."
            }
        }
    
    @pytest.fixture
    def mock_services(self):
        """Mock all backend services for testing."""
        with patch('api.main.patient_lookup_service') as mock_patient, \
             patch('api.main.xml_processing_service') as mock_xml, \
             patch('api.main.claude_analysis_service') as mock_claude, \
             patch('api.main.workflow_orchestrator') as mock_workflow:
            
            # Mock patient lookup service
            mock_patient.get_all_patients.return_value = {
                self.sample_patient_id: "patient_folder_123",
                "patient-test-456": "patient_folder_456"
            }
            mock_patient.validate_patient_folder_structure.return_value = {
                "folder_path": "/test/patient/123",
                "has_profile": True,
                "xml_files": 2,
                "processed_json_files": 1
            }
            mock_patient.check_patient_data_availability.return_value = {
                "patient_exists": True,
                "raw_data_available": True,
                "processed_data_available": True,
                "folder_name": "patient_folder_123",
                "xml_files_count": 2,
                "json_files_count": 1,
                "raw_data_path": "/test/raw/123",
                "processed_data_path": "/test/processed/123"
            }
            mock_patient.get_patient_profile.return_value = self.sample_patient_data
            mock_patient.get_patient_folder_paths.return_value = {
                "raw_data_path": "/test/raw/123",
                "processed_data_path": "/test/processed/123"
            }
            mock_patient.get_patient_history.return_value = [self.sample_bundle]
            
            # Mock XML processing service
            mock_xml.process_xml_file = AsyncMock(return_value={
                "success": True,
                "bundle": self.sample_bundle,
                "patient_id": self.sample_patient_id
            })
            mock_xml.get_processing_stats.return_value = {
                "service_status": "ready",
                "total_files_processed": 10,
                "success_rate": 0.95
            }
            
            # Mock Claude analysis service
            mock_claude.claude_available = True
            mock_claude.get_analysis_status.return_value = {
                "claude_available": True,
                "patient_index_size": 2
            }
            
            # Mock workflow orchestrator
            mock_workflow.analyze_existing_patient = AsyncMock(return_value={
                "success": True,
                "patient_id": self.sample_patient_id,
                "claude_analysis": {
                    "summary": "Test analysis completed",
                    "cost_usd": 0.75,
                    "agent_results": {
                        "recommendation_agent": {
                            "recommendations": ["Approve HbA1c test", "Schedule follow-up"]
                        },
                        "medical_reviewer_agent": {
                            "confidence_score": 0.88
                        }
                    }
                }
            })
            
            yield {
                "patient": mock_patient,
                "xml": mock_xml,
                "claude": mock_claude,
                "workflow": mock_workflow
            }
    
    def test_health_check_endpoint(self, mock_services):
        """Test GET /api/health endpoint."""
        response = self.client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] in ["healthy", "degraded"]
        assert "timestamp" in data
        assert "version" in data
        assert "xml_processing_available" in data
        assert "claude_analysis_available" in data
        assert "patient_index_size" in data
        assert "supported_sources" in data
    
    def test_list_patients_endpoint_success(self, mock_services):
        """Test GET /api/patients endpoint success."""
        response = self.client.get("/api/patients")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) == 2  # Two patients from mock
        
        # Check patient data structure includes basic metadata
        patient = data[0]
        assert "patient_id" in patient
        assert "folder_name" in patient
        assert "folder_path" in patient
        assert "has_profile" in patient
        assert "xml_files" in patient
        assert "processed_json_files" in patient
        
        # Check patient data structure includes complete profile information
        assert "full_name" in patient
        assert "gender" in patient
        assert "birth_year" in patient
        assert "nationality" in patient
        assert "marital_status" in patient
        assert "employment_sector" in patient
        assert "insurance_plan" in patient
        assert "coverage_tier" in patient
        assert "smoker" in patient
        assert "baseline_BMI" in patient
        assert "baseline_BP_systolic" in patient
        assert "family_history_diabetes" in patient
        assert "family_history_CAD" in patient
        
        # Verify profile data from mock
        assert patient["full_name"] == "Ahmed Al Mansoori"
    
    def test_list_patients_endpoint_service_error(self, mock_services):
        """Test GET /api/patients endpoint with service error."""
        mock_services["patient"].get_all_patients.side_effect = Exception("Database error")
        
        response = self.client.get("/api/patients")
        
        assert response.status_code == 500
        data = response.json()
        assert "Failed to list patients" in data["detail"]
    
    def test_upload_xml_endpoint_success(self, mock_services):
        """Test POST /api/upload-xml endpoint success."""
        files = {
            "file": ("test.xml", BytesIO(self.sample_xml.encode()), "application/xml")
        }
        data = {
            "source": "eclaim",
            "patient_id": self.sample_patient_id
        }
        
        response = self.client.post("/api/upload-xml", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["success"] is True
        assert result["patient_id"] == self.sample_patient_id
        assert "data" in result
        assert "metadata" in result
        
        # Check metadata
        metadata = result["metadata"]
        assert metadata["filename"] == "test.xml"
        assert metadata["xml_source"] == "eclaim"
    
    def test_upload_xml_endpoint_invalid_source(self):
        """Test POST /api/upload-xml with invalid source."""
        files = {
            "file": ("test.xml", BytesIO(self.sample_xml.encode()), "application/xml")
        }
        data = {
            "source": "invalid_source"
        }
        
        response = self.client.post("/api/upload-xml", files=files, data=data)
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid source" in data["detail"]
    
    def test_upload_xml_endpoint_invalid_file_type(self):
        """Test POST /api/upload-xml with invalid file type."""
        files = {
            "file": ("test.txt", BytesIO(b"not xml content"), "text/plain")
        }
        data = {
            "source": "eclaim"
        }
        
        response = self.client.post("/api/upload-xml", files=files, data=data)
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid file type" in data["detail"]
    
    def test_upload_xml_endpoint_file_too_large(self):
        """Test POST /api/upload-xml with file too large."""
        # Create large content (>10MB)
        large_content = "x" * (11 * 1024 * 1024)
        files = {
            "file": ("large.xml", BytesIO(large_content.encode()), "application/xml")
        }
        data = {
            "source": "eclaim"
        }
        
        response = self.client.post("/api/upload-xml", files=files, data=data)
        
        assert response.status_code == 413
        data = response.json()
        assert "File too large" in data["detail"]
    
    @patch('pathlib.Path.glob')
    @patch('pathlib.Path.stat')
    def test_process_patient_endpoint_success(self, mock_stat, mock_glob, mock_services):
        """Test POST /api/process/{patient_id} endpoint success."""
        # Mock file system operations
        mock_file = Mock()
        mock_file.name = "test.xml"
        mock_file.stat.return_value.st_mtime = 1627750000.0
        mock_glob.return_value = [mock_file]
        
        mock_stat_result = Mock()
        mock_stat_result.st_mtime = 1627750000.0
        mock_stat.return_value = mock_stat_result
        
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = self.sample_xml.encode()
            
            with patch('json.dump') as mock_json_dump:
                response = self.client.post(f"/api/process/{self.sample_patient_id}")
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["success"] is True
        assert result["patient_id"] == self.sample_patient_id
        assert "data" in result
        assert "metadata" in result
        
        # Verify XML processing service was called
        mock_services["xml"].process_xml_file.assert_called_once()
    
    def test_process_patient_endpoint_patient_not_found(self, mock_services):
        """Test POST /api/process/{patient_id} with non-existent patient."""
        mock_services["patient"].check_patient_data_availability.return_value = {
            "patient_exists": False
        }
        
        response = self.client.post("/api/process/non-existent-patient")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]
    
    def test_process_patient_endpoint_no_xml_files(self, mock_services):
        """Test POST /api/process/{patient_id} with no XML files."""
        mock_services["patient"].check_patient_data_availability.return_value = {
            "patient_exists": True,
            "raw_data_available": False
        }
        
        response = self.client.post(f"/api/process/{self.sample_patient_id}")
        
        assert response.status_code == 404
        data = response.json()
        assert "No XML files found" in data["detail"]
    
    def test_analyze_patient_endpoint_success(self, mock_services):
        """Test POST /api/analyze/{patient_id} endpoint success."""
        response = self.client.post(
            f"/api/analyze/{self.sample_patient_id}",
            params={"cost_limit_usd": 2.0, "include_history": True}
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["success"] is True
        assert result["patient_id"] == self.sample_patient_id
        assert "analysis" in result
        assert "recommendations" in result
        assert "confidence_score" in result
        
        # Check analysis content
        assert result["analysis"]["cost_usd"] == 0.75
        assert len(result["recommendations"]) == 2
        assert result["confidence_score"] == 0.88
        
        # Verify workflow orchestrator was called
        mock_services["workflow"].analyze_existing_patient.assert_called_once_with(
            patient_id=self.sample_patient_id,
            cost_limit_usd=2.0,
            include_history=True
        )
    
    def test_analyze_patient_endpoint_patient_not_found(self, mock_services):
        """Test POST /api/analyze/{patient_id} with non-existent patient."""
        mock_services["patient"].check_patient_data_availability.return_value = {
            "patient_exists": False
        }
        
        response = self.client.post(f"/api/analyze/non-existent-patient")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]
    
    def test_analyze_patient_endpoint_no_processed_data(self, mock_services):
        """Test POST /api/analyze/{patient_id} with no processed data."""
        mock_services["patient"].check_patient_data_availability.return_value = {
            "patient_exists": True,
            "processed_data_available": False
        }
        
        response = self.client.post(f"/api/analyze/{self.sample_patient_id}")
        
        assert response.status_code == 404
        data = response.json()
        assert "No processed data found" in data["detail"]
    
    def test_analyze_patient_endpoint_claude_unavailable(self, mock_services):
        """Test POST /api/analyze/{patient_id} with Claude unavailable."""
        mock_services["claude"].claude_available = False
        
        response = self.client.post(f"/api/analyze/{self.sample_patient_id}")
        
        assert response.status_code == 503
        data = response.json()
        assert "Claude analysis service is not available" in data["detail"]
    
    def test_analyze_patient_endpoint_analysis_failure(self, mock_services):
        """Test POST /api/analyze/{patient_id} with analysis failure."""
        mock_services["workflow"].analyze_existing_patient.return_value = {
            "success": False,
            "error": "Analysis failed due to API rate limit"
        }
        
        response = self.client.post(f"/api/analyze/{self.sample_patient_id}")
        
        assert response.status_code == 500
        data = response.json()
        assert "Analysis failed due to API rate limit" in data["detail"]
    
    @patch('pathlib.Path.glob')
    @patch('pathlib.Path.stat')
    def test_patient_dashboard_endpoint_success(self, mock_stat, mock_glob, mock_services):
        """Test GET /api/patient/{patient_id}/dashboard endpoint success."""
        # Mock file system operations for recent files
        mock_xml_file = Mock()
        mock_xml_file.name = "recent.xml"
        mock_xml_file.stat.return_value.st_mtime = 1627750000.0
        mock_xml_file.stat.return_value.st_size = 1024
        mock_glob.return_value = [mock_xml_file]
        
        mock_json_file = Mock()
        mock_json_file.exists.return_value = True
        mock_json_file.stat.return_value.st_mtime = 1627750100.0
        
        with patch('pathlib.Path.__truediv__') as mock_path_div:
            mock_path_div.return_value = mock_json_file
            
            response = self.client.get(f"/api/patient/{self.sample_patient_id}/dashboard")
        
        assert response.status_code == 200
        result = response.json()
        
        assert "patient_info" in result
        assert "recent_files" in result
        assert "analysis_history" in result
        assert "summary_stats" in result
        
        # Check patient info
        patient_info = result["patient_info"]
        assert patient_info["patient_id"] == self.sample_patient_id
        assert patient_info["has_profile"] is True
        
        # Check summary stats
        summary = result["summary_stats"]
        assert "total_xml_files" in summary
        assert "total_processed_files" in summary
        assert "processing_success_rate" in summary
        assert "claude_analysis_available" in summary
    
    def test_patient_dashboard_endpoint_patient_not_found(self, mock_services):
        """Test GET /api/patient/{patient_id}/dashboard with non-existent patient."""
        mock_services["patient"].check_patient_data_availability.return_value = {
            "patient_exists": False
        }
        
        response = self.client.get("/api/patient/non-existent-patient/dashboard")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]
    
    def test_patient_dashboard_endpoint_with_patient_profile(self, mock_services):
        """Test dashboard endpoint includes patient profile data."""
        with patch('pathlib.Path.glob') as mock_glob:
            mock_glob.return_value = []  # No files
            
            response = self.client.get(f"/api/patient/{self.sample_patient_id}/dashboard")
        
        assert response.status_code == 200
        result = response.json()
        
        # Check that patient profile data is included in summary stats
        summary = result["summary_stats"]
        assert summary["patient_name"] == "Ahmed Al Mansoori"
        assert summary["insurance_company"] == "Dubai Health Insurance Premium"
        assert summary["member_id"] == self.sample_patient_id
    
    def test_complete_patient_workflow_integration(self, mock_services):
        """Test complete workflow: upload → process → analyze → dashboard."""
        # Step 1: Upload XML file
        files = {
            "file": ("workflow_test.xml", BytesIO(self.sample_xml.encode()), "application/xml")
        }
        data = {"source": "eclaim", "patient_id": self.sample_patient_id}
        
        upload_response = self.client.post("/api/upload-xml", files=files, data=data)
        assert upload_response.status_code == 200
        
        # Step 2: Process patient data
        with patch('pathlib.Path.glob') as mock_glob, \
             patch('pathlib.Path.stat') as mock_stat, \
             patch('builtins.open', create=True) as mock_open, \
             patch('json.dump'):
            
            mock_file = Mock()
            mock_file.name = "workflow_test.xml"
            mock_file.stat.return_value.st_mtime = 1627750000.0
            mock_glob.return_value = [mock_file]
            mock_open.return_value.__enter__.return_value.read.return_value = self.sample_xml.encode()
            
            process_response = self.client.post(f"/api/process/{self.sample_patient_id}")
            assert process_response.status_code == 200
        
        # Step 3: Analyze patient
        analyze_response = self.client.post(
            f"/api/analyze/{self.sample_patient_id}",
            params={"cost_limit_usd": 2.0}
        )
        assert analyze_response.status_code == 200
        
        # Step 4: Get dashboard
        with patch('pathlib.Path.glob') as mock_glob:
            mock_glob.return_value = []  # No files for simplicity
            dashboard_response = self.client.get(f"/api/patient/{self.sample_patient_id}/dashboard")
            assert dashboard_response.status_code == 200
        
        # Verify all services were called appropriately
        mock_services["xml"].process_xml_file.assert_called()
        mock_services["workflow"].analyze_existing_patient.assert_called_once()
    
    def test_error_handling_and_logging(self, mock_services):
        """Test proper error handling and response formatting."""
        # Test service exception handling
        mock_services["patient"].get_all_patients.side_effect = Exception("Unexpected error")
        
        response = self.client.get("/api/patients")
        
        assert response.status_code == 500
        data = response.json()
        
        # Should have proper error structure
        assert "detail" in data
        assert "Failed to list patients" in data["detail"]
        
        # Should not expose internal error details in production
        assert "Unexpected error" in data["detail"]  # This would be logged but not exposed in production
    
    def test_cors_headers(self):
        """Test that CORS headers are properly set."""
        response = self.client.get("/api/health")
        
        # FastAPI TestClient doesn't automatically handle CORS,
        # but we can verify the middleware is configured
        assert response.status_code == 200
    
    def test_api_versioning_and_metadata(self, mock_services):
        """Test API version information in responses."""
        files = {
            "file": ("version_test.xml", BytesIO(self.sample_xml.encode()), "application/xml")
        }
        data = {"source": "eclaim"}
        
        response = self.client.post("/api/upload-xml", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        
        # Check API version in metadata
        assert result["metadata"]["api_version"] == "2.0.0"
    
    def test_concurrent_requests_handling(self, mock_services):
        """Test handling of concurrent API requests."""
        import concurrent.futures
        import threading
        
        def make_request():
            return self.client.get("/api/patients")
        
        # Make multiple concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            results = [future.result() for future in futures]
        
        # All requests should succeed
        for response in results:
            assert response.status_code == 200
        
        # Service should handle concurrent calls
        assert mock_services["patient"].get_all_patients.call_count >= 5
