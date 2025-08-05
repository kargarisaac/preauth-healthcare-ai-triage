#!/usr/bin/env python3
"""
Tests for Enhanced FastAPI Endpoints
Comprehensive tests for the new v2 endpoints with mandatory source specification.
"""

import sys
import pytest
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import status

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.main import app  # noqa: E402


class TestEnhancedEndpoints:
    """Test suite for enhanced FastAPI endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def sample_xml_content(self):
        """Sample XML content for testing."""
        return """<?xml version="1.0" encoding="UTF-8"?>
        <Prior.Authorization>
            <PatientID>11f5688b-6c4a-4c41-baad-71e6a4b82d91</PatientID>
            <Services>
                <Service>
                    <Code>99213</Code>
                    <Description>Office visit</Description>
                </Service>
            </Services>
        </Prior.Authorization>"""
    
    @pytest.fixture
    def sample_fhir_bundle(self):
        """Sample FHIR Bundle for testing."""
        return {
            "resourceType": "Bundle",
            "id": "test-bundle-123",
            "type": "collection",
            "timestamp": "2025-08-03T23:00:00Z",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient",
                        "id": "11f5688b-6c4a-4c41-baad-71e6a4b82d91",
                        "name": [{"family": "Test", "given": ["Patient"]}]
                    }
                }
            ],
            "raw_data": {"source": "test"},
            "fhir_resources": {
                "Patient/test": {
                    "resourceType": "Patient",
                    "id": "11f5688b-6c4a-4c41-baad-71e6a4b82d91"
                }
            }
        }


class TestXMLProcessingEndpoint:
    """Tests for /api/v2/process/xml endpoint."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def sample_xml_content(self):
        return """<?xml version="1.0" encoding="UTF-8"?>
        <Prior.Authorization>
            <PatientID>11f5688b-6c4a-4c41-baad-71e6a4b82d91</PatientID>
        </Prior.Authorization>"""
    
    def test_xml_processing_success_shafafiya(self, client, sample_xml_content):
        """Test successful XML processing with Shafafiya source."""
        with patch('api.services.xml_processing_service.get_xml_processing_service') as mock_service:
            # Mock the service response
            mock_instance = Mock()
            mock_instance.process_xml_file = AsyncMock(return_value={
                "success": True,
                "bundle": {"resourceType": "Bundle", "id": "test-123"},
                "source": "shafafiya",
                "patient_id": "11f5688b-6c4a-4c41-baad-71e6a4b82d91",
                "patient_folder": "data/synthetic_dataset/1",
                "metadata": {
                    "filename": "test.xml",
                    "file_size": 1024,
                    "source": "shafafiya",
                    "processing_timestamp": "2025-08-03T23:00:00Z",
                    "bundle_id": "test-123",
                    "patient_resolution": {
                        "patient_id": "11f5688b-6c4a-4c41-baad-71e6a4b82d91",
                        "patient_folder": "data/synthetic_dataset/1",
                        "id_source": "extracted"
                    }
                }
            })
            mock_service.return_value = mock_instance
            
            # Create test file
            files = {"file": ("test.xml", BytesIO(sample_xml_content.encode()), "application/xml")}
            data = {"source": "shafafiya"}
            
            response = client.post("/api/v2/process/xml", files=files, data=data)
            
            assert response.status_code == status.HTTP_200_OK
            result = response.json()
            assert result["success"] is True
            assert result["source"] == "shafafiya"
            assert result["patient_id"] == "11f5688b-6c4a-4c41-baad-71e6a4b82d91"
    
    def test_xml_processing_success_eclaim(self, client, sample_xml_content):
        """Test successful XML processing with eClaimLink source."""
        with patch('api.services.xml_processing_service.get_xml_processing_service') as mock_service:
            mock_instance = Mock()
            mock_instance.process_xml_file = AsyncMock(return_value={
                "success": True,
                "bundle": {"resourceType": "Bundle", "id": "test-456"},
                "source": "eclaim",
                "patient_id": "a9f7c2d4-1b3e-4c2a-8e7b-2d1c3a4b5e6f",
                "patient_folder": "data/synthetic_dataset/3",
                "metadata": {
                    "filename": "test.xml",
                    "file_size": 1024,
                    "source": "eclaim",
                    "processing_timestamp": "2025-08-03T23:00:00Z",
                    "bundle_id": "test-456",
                    "patient_resolution": {
                        "patient_id": "a9f7c2d4-1b3e-4c2a-8e7b-2d1c3a4b5e6f",
                        "patient_folder": "data/synthetic_dataset/3",
                        "id_source": "extracted"
                    }
                }
            })
            mock_service.return_value = mock_instance
            
            files = {"file": ("test.xml", BytesIO(sample_xml_content.encode()), "application/xml")}
            data = {"source": "eclaim"}
            
            response = client.post("/api/v2/process/xml", files=files, data=data)
            
            assert response.status_code == status.HTTP_200_OK
            result = response.json()
            assert result["success"] is True
            assert result["source"] == "eclaim"
    
    def test_xml_processing_invalid_source(self, client, sample_xml_content):
        """Test XML processing with invalid source."""
        files = {"file": ("test.xml", BytesIO(sample_xml_content.encode()), "application/xml")}
        data = {"source": "invalid"}
        
        response = client.post("/api/v2/process/xml", files=files, data=data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "must be 'eclaim' or 'shafafiya'" in response.json()["detail"]
    
    def test_xml_processing_missing_source(self, client, sample_xml_content):
        """Test XML processing without source parameter."""
        files = {"file": ("test.xml", BytesIO(sample_xml_content.encode()), "application/xml")}
        
        response = client.post("/api/v2/process/xml", files=files)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_xml_processing_with_patient_id_override(self, client, sample_xml_content):
        """Test XML processing with patient ID override."""
        with patch('api.services.xml_processing_service.get_xml_processing_service') as mock_service:
            mock_instance = Mock()
            mock_instance.process_xml_file = AsyncMock(return_value={
                "success": True,
                "bundle": {"resourceType": "Bundle", "id": "test-789"},
                "source": "shafafiya",
                "patient_id": "custom-patient-id",
                "patient_folder": None,
                "metadata": {
                    "filename": "test.xml",
                    "file_size": 1024,
                    "source": "shafafiya",
                    "processing_timestamp": "2025-08-03T23:00:00Z",
                    "bundle_id": "test-789",
                    "patient_resolution": {
                        "patient_id": "custom-patient-id",
                        "patient_folder": None,
                        "id_source": "provided"
                    }
                }
            })
            mock_service.return_value = mock_instance
            
            files = {"file": ("test.xml", BytesIO(sample_xml_content.encode()), "application/xml")}
            data = {"source": "shafafiya", "patient_id": "custom-patient-id"}
            
            response = client.post("/api/v2/process/xml", files=files, data=data)
            
            assert response.status_code == status.HTTP_200_OK
            result = response.json()
            assert result["patient_id"] == "custom-patient-id"


class TestClaudeAnalysisEndpoint:
    """Tests for /api/v2/analysis/preauth endpoint."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def sample_analysis_request(self):
        return {
            "patient_id": "11f5688b-6c4a-4c41-baad-71e6a4b82d91",
            "current_request": {
                "resourceType": "Bundle",
                "id": "test-bundle",
                "entry": []
            },
            "include_history": True,
            "cost_limit_usd": 1.0
        }
    
    def test_claude_analysis_success(self, client, sample_analysis_request):
        """Test successful Claude analysis."""
        with patch('api.services.claude_analysis_service.get_claude_analysis_service') as mock_service:
            mock_instance = Mock()
            mock_instance.analyze_preauth = AsyncMock(return_value={
                "success": True,
                "patient_id": "11f5688b-6c4a-4c41-baad-71e6a4b82d91",
                "claude_analysis": {
                    "decision": "APPROVE",
                    "confidence": 0.92,
                    "agents": {"clinical-analyzer": {"status": "success"}}
                },
                "cost_usd": 0.34,
                "processing_time_seconds": 45.2,
                "historical_files_count": 3,
                "analysis_metadata": {"start_time": "2025-08-03T23:00:00Z"},
                "agent_results": {"clinical-analyzer": {"success": True}},
                "timestamp": "2025-08-03T23:00:00Z"
            })
            mock_service.return_value = mock_instance
            
            response = client.post("/api/v2/analysis/preauth", json=sample_analysis_request)
            
            assert response.status_code == status.HTTP_200_OK
            result = response.json()
            assert result["success"] is True
            assert result["patient_id"] == "11f5688b-6c4a-4c41-baad-71e6a4b82d91"
            assert result["claude_analysis"] is not None
    
    def test_claude_analysis_failure(self, client, sample_analysis_request):
        """Test Claude analysis failure."""
        with patch('api.services.claude_analysis_service.get_claude_analysis_service') as mock_service:
            mock_instance = Mock()
            mock_instance.analyze_preauth = AsyncMock(return_value={
                "success": False,
                "patient_id": "11f5688b-6c4a-4c41-baad-71e6a4b82d91",
                "error": "Patient not found",
                "cost_usd": 0.0,
                "processing_time_seconds": 0.0,
                "historical_files_count": 0,
                "timestamp": "2025-08-03T23:00:00Z"
            })
            mock_service.return_value = mock_instance
            
            response = client.post("/api/v2/analysis/preauth", json=sample_analysis_request)
            
            assert response.status_code == status.HTTP_200_OK
            result = response.json()
            assert result["success"] is False
            assert result["error"] == "Patient not found"
    
    def test_claude_analysis_invalid_request(self, client):
        """Test Claude analysis with invalid request."""
        invalid_request = {
            "patient_id": "",  # Empty patient ID
            "current_request": {},  # Empty bundle
            "cost_limit_usd": -1.0  # Invalid cost limit
        }
        
        response = client.post("/api/v2/analysis/preauth", json=invalid_request)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestWorkflowEndpoints:
    """Tests for workflow endpoints."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def sample_xml_content(self):
        return """<?xml version="1.0" encoding="UTF-8"?>
        <Prior.Authorization>
            <PatientID>11f5688b-6c4a-4c41-baad-71e6a4b82d91</PatientID>
        </Prior.Authorization>"""
    
    def test_xml_to_analysis_workflow_success(self, client, sample_xml_content):
        """Test successful XML-to-analysis workflow."""
        with patch('api.services.workflow_orchestrator.get_workflow_orchestrator') as mock_orchestrator:
            mock_instance = Mock()
            mock_instance.xml_to_analysis_workflow = AsyncMock(return_value={
                "success": True,
                "workflow_type": "xml_to_analysis",
                "xml_processing": {
                    "success": True,
                    "bundle": {"resourceType": "Bundle", "id": "test-bundle"},
                    "source": "shafafiya",
                    "patient_id": "11f5688b-6c4a-4c41-baad-71e6a4b82d91",
                    "patient_folder": "data/synthetic_dataset/1",
                    "metadata": {}
                },
                "claude_analysis": {
                    "success": True,
                    "cost_usd": 0.34
                },
                "workflow_metadata": {
                    "start_time": "2025-08-03T23:00:00Z",
                    "end_time": "2025-08-03T23:01:00Z",
                    "total_time_seconds": 60.0,
                    "enable_analysis": True,
                    "cost_limit_usd": 1.0,
                    "include_history": True
                },
                "summary": {
                    "patient_id": "11f5688b-6c4a-4c41-baad-71e6a4b82d91",
                    "source": "shafafiya",
                    "analysis_enabled": True,
                    "analysis_cost_usd": 0.34,
                    "total_processing_time": 60.0
                }
            })
            mock_orchestrator.return_value = mock_instance
            
            files = {"file": ("test.xml", BytesIO(sample_xml_content.encode()), "application/xml")}
            data = {
                "source": "shafafiya",
                "enable_analysis": "true",
                "cost_limit_usd": "1.0",
                "include_history": "true"
            }
            
            response = client.post("/api/v2/workflow/xml-to-analysis", files=files, data=data)
            
            assert response.status_code == status.HTTP_200_OK
            result = response.json()
            assert result["success"] is True
            assert result["workflow_type"] == "xml_to_analysis"
            assert result["summary"]["analysis_enabled"] is True
    
    def test_existing_patient_analysis_success(self, client):
        """Test successful existing patient analysis."""
        with patch('api.services.workflow_orchestrator.get_workflow_orchestrator') as mock_orchestrator:
            mock_instance = Mock()
            mock_instance.analyze_existing_patient = AsyncMock(return_value={
                "success": True,
                "workflow_type": "existing_patient_analysis",
                "patient_id": "11f5688b-6c4a-4c41-baad-71e6a4b82d91",
                "claude_analysis": {
                    "success": True,
                    "cost_usd": 0.28
                },
                "workflow_metadata": {
                    "start_time": "2025-08-03T23:00:00Z",
                    "end_time": "2025-08-03T23:00:30Z",
                    "total_time_seconds": 30.0,
                    "historical_files_used": 2,
                    "current_request_source": "most_recent_processed"
                }
            })
            mock_orchestrator.return_value = mock_instance
            
            request_data = {
                "patient_id": "11f5688b-6c4a-4c41-baad-71e6a4b82d91",
                "include_history": True,
                "cost_limit_usd": 1.0
            }
            
            response = client.post("/api/v2/analysis/existing-patient", json=request_data)
            
            assert response.status_code == status.HTTP_200_OK
            result = response.json()
            assert result["success"] is True
            assert result["workflow_type"] == "existing_patient_analysis"
    
    def test_batch_process_patient_success(self, client):
        """Test successful batch patient processing."""
        with patch('api.services.workflow_orchestrator.get_workflow_orchestrator') as mock_orchestrator:
            mock_instance = Mock()
            mock_instance.batch_process_patient = AsyncMock(return_value={
                "success": True,
                "workflow_type": "batch_process_patient",
                "patient_id": "11f5688b-6c4a-4c41-baad-71e6a4b82d91",
                "source": "shafafiya",
                "processed_files": [
                    {
                        "file": "req01_shafafiya.xml",
                        "bundle": {"resourceType": "Bundle", "id": "bundle-1"},
                        "processed_at": "2025-08-03T23:00:00Z"
                    }
                ],
                "files_processed": 1,
                "claude_analysis": None,
                "workflow_metadata": {
                    "start_time": "2025-08-03T23:00:00Z",
                    "end_time": "2025-08-03T23:00:15Z",
                    "total_time_seconds": 15.0,
                    "patient_folder": "data/synthetic_dataset/1"
                }
            })
            mock_orchestrator.return_value = mock_instance
            
            request_data = {
                "patient_id": "11f5688b-6c4a-4c41-baad-71e6a4b82d91",
                "source": "shafafiya",
                "enable_analysis": False
            }
            
            response = client.post("/api/v2/batch/process-patient", json=request_data)
            
            assert response.status_code == status.HTTP_200_OK
            result = response.json()
            assert result["success"] is True
            assert result["files_processed"] == 1


class TestPatientAndStatusEndpoints:
    """Tests for patient listing and status endpoints."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_list_patients_success(self, client):
        """Test successful patient listing."""
        with patch('api.services.patient_lookup_service.get_patient_lookup_service') as mock_service:
            mock_instance = Mock()
            mock_instance.get_all_patients.return_value = {
                "11f5688b-6c4a-4c41-baad-71e6a4b82d91": "1",
                "a9f7c2d4-1b3e-4c2a-8e7b-2d1c3a4b5e6f": "3"
            }
            mock_instance.validate_patient_folder_structure.side_effect = [
                {
                    "valid": True,
                    "folder_path": "data/synthetic_dataset/1",
                    "has_profile": True,
                    "xml_files": 6,
                    "processed_json_files": 5
                },
                {
                    "valid": True,
                    "folder_path": "data/synthetic_dataset/3",
                    "has_profile": True,
                    "xml_files": 10,
                    "processed_json_files": 0
                }
            ]
            mock_service.return_value = mock_instance
            
            response = client.get("/api/v2/patients")
            
            assert response.status_code == status.HTTP_200_OK
            result = response.json()
            assert len(result) == 2
            assert result[0]["patient_id"] == "11f5688b-6c4a-4c41-baad-71e6a4b82d91"
            assert result[0]["xml_files"] == 6
    
    def test_get_patient_info_success(self, client):
        """Test successful patient info retrieval."""
        with patch('api.services.patient_lookup_service.get_patient_lookup_service') as mock_service:
            mock_instance = Mock()
            mock_instance.validate_patient_folder_structure.return_value = {
                "valid": True,
                "folder_name": "1",
                "folder_path": "data/synthetic_dataset/1",
                "has_profile": True,
                "xml_files": 6,
                "processed_json_files": 5
            }
            mock_service.return_value = mock_instance
            
            patient_id = "11f5688b-6c4a-4c41-baad-71e6a4b82d91"
            response = client.get(f"/api/v2/patients/{patient_id}")
            
            assert response.status_code == status.HTTP_200_OK
            result = response.json()
            assert result["patient_id"] == patient_id
            assert result["xml_files"] == 6
    
    def test_get_patient_info_not_found(self, client):
        """Test patient info for non-existent patient."""
        with patch('api.services.patient_lookup_service.get_patient_lookup_service') as mock_service:
            mock_instance = Mock()
            mock_instance.validate_patient_folder_structure.return_value = {
                "valid": False,
                "error": "Patient not found"
            }
            mock_service.return_value = mock_instance
            
            response = client.get("/api/v2/patients/non-existent-id")
            
            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert "not found" in response.json()["detail"]
    
    def test_system_status_success(self, client):
        """Test successful system status retrieval."""
        with patch('api.services.xml_processing_service.get_xml_processing_service') as mock_xml, \
             patch('api.services.claude_analysis_service.get_claude_analysis_service') as mock_claude, \
             patch('api.services.workflow_orchestrator.get_workflow_orchestrator') as mock_workflow:
            
            # Mock service responses
            mock_xml.return_value.get_processing_stats.return_value = {"service_status": "ready"}
            mock_claude.return_value.get_analysis_status.return_value = {
                "claude_available": True,
                "patient_index_size": 10
            }
            mock_workflow.return_value.get_workflow_status.return_value = {
                "supported_workflows": ["xml_to_analysis", "existing_patient_analysis"]
            }
            
            response = client.get("/api/v2/status")
            
            assert response.status_code == status.HTTP_200_OK
            result = response.json()
            assert result["xml_processing_available"] is True
            assert result["claude_analysis_available"] is True
            assert result["patient_index_size"] == 10
            assert "eclaim" in result["supported_sources"]
            assert "shafafiya" in result["supported_sources"]


class TestErrorHandling:
    """Tests for error handling across endpoints."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_service_unavailable_error(self, client):
        """Test handling of service unavailable errors."""
        with patch('api.services.xml_processing_service.get_xml_processing_service') as mock_service:
            mock_instance = Mock()
            mock_instance.process_xml_file = AsyncMock(side_effect=Exception("Service unavailable"))
            mock_service.return_value = mock_instance
            
            files = {"file": ("test.xml", BytesIO(b"<xml></xml>"), "application/xml")}
            data = {"source": "shafafiya"}
            
            response = client.post("/api/v2/process/xml", files=files, data=data)
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Service unavailable" in response.json()["detail"]
    
    def test_validation_error_handling(self, client):
        """Test handling of validation errors."""
        # Test with missing required fields
        response = client.post("/api/v2/analysis/preauth", json={})
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
    def test_file_upload_error_handling(self, client):
        """Test handling of file upload errors."""
        # Test with non-XML file
        files = {"file": ("test.txt", BytesIO(b"not xml"), "text/plain")}
        data = {"source": "shafafiya"}
        
        response = client.post("/api/v2/process/xml", files=files, data=data)
        
        # Should be handled by the service validation
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])