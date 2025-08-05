#!/usr/bin/env python3
"""
End-to-end integration tests for complete patient workflow.

Tests the full patient journey from selection through analysis:
1. Patient selection from dropdown
2. XML file upload with patient context
3. XML processing and FHIR bundle generation
4. Claude analysis with multi-agent workflow
5. Dashboard view with results
"""

import json
import tempfile
import time
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, patch, AsyncMock
from io import BytesIO

import pytest
from fastapi.testclient import TestClient

from api.main import app


class TestPatientWorkflowE2E:
    """End-to-end tests for complete patient workflow."""
    
    def setup_method(self):
        """Set up test fixtures for E2E testing."""
        self.client = TestClient(app)
        self.test_patient_id = "patient-e2e-test-001"
        
        # Sample XML for testing
        self.sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
            <Header>
                <SenderID>PROV12345</SenderID>
                <ReceiverID>PAYER67890</ReceiverID>
                <TransactionDateTime>04/08/2025 14:30</TransactionDateTime>
                <TransactionID>TXN-E2E-TEST-001</TransactionID>
            </Header>
            <JustificationText>35-year-old patient with Type 2 Diabetes Mellitus presenting for routine HbA1c monitoring. Last HbA1c was 8.5% three months ago, indicating suboptimal glycemic control. Patient is currently on metformin 1000mg twice daily and has been compliant with medication. Recent symptoms include increased thirst and frequent urination. Blood pressure is well controlled at 120/80 mmHg. Patient has family history of diabetes and cardiovascular disease. Requesting HbA1c test to assess current diabetes management and consider treatment adjustments.</JustificationText>
            <ServiceRequests>
                <ServiceRequest>
                    <ct:ActivityCode>83036</ct:ActivityCode>
                    <ct:DiagnosisCode>E11.9</ct:DiagnosisCode>
                    <ct:ActivityDateTime>05/08/2025 09:00</ct:ActivityDateTime>
                    <ct:ActivityInstructions>Hemoglobin A1c test for diabetes monitoring and treatment adjustment assessment</ct:ActivityInstructions>
                    <RequestedAmount currency="AED">125.50</RequestedAmount>
                </ServiceRequest>
                <ServiceRequest>
                    <ct:ActivityCode>80061</ct:ActivityCode>
                    <ct:DiagnosisCode>E11.9</ct:DiagnosisCode>
                    <ct:ActivityDateTime>05/08/2025 09:00</ct:ActivityDateTime>
                    <ct:ActivityInstructions>Lipid panel to assess cardiovascular risk in diabetic patient</ct:ActivityInstructions>
                    <RequestedAmount currency="AED">85.00</RequestedAmount>
                </ServiceRequest>
            </ServiceRequests>
        </PriorAuthorizationRequest>"""
        
        # Expected processed bundle structure
        self.expected_bundle = {
            "resourceType": "Bundle",
            "id": "eClaimLink-Bundle-TXN-E2E-TEST-001",
            "authorization_id": "TXN-E2E-TEST-001",
            "sender": "PROV12345",
            "receiver": "PAYER67890",
            "fhir_resources": {
                "claim-1": {
                    "resourceType": "Claim",
                    "id": "TXN-E2E-TEST-001",
                    "diagnosis": [{"code": "E11.9"}],
                    "item": [
                        {"productOrService": {"code": "83036"}},
                        {"productOrService": {"code": "80061"}}
                    ]
                }
            },
            "raw_data": {
                "TransactionID": "TXN-E2E-TEST-001",
                "JustificationText": "35-year-old patient with Type 2 Diabetes Mellitus..."
            }
        }
        
        # Expected analysis result
        self.expected_analysis = {
            "summary": "Comprehensive diabetes management analysis",
            "cost_usd": 1.25,
            "agent_results": {
                "clinical_analyzer": {
                    "findings": [
                        "Type 2 diabetes with suboptimal control",
                        "HbA1c monitoring required",
                        "Cardiovascular risk assessment indicated"
                    ],
                    "clinical_context_score": 0.92
                },
                "medical_reviewer": {
                    "medical_necessity": "HIGH",
                    "approval_recommendation": "APPROVE",
                    "confidence_score": 0.89,
                    "reasoning": "Well-documented diabetes case with clear need for monitoring"
                },
                "recommendation_agent": {
                    "recommendations": [
                        "Approve HbA1c test - medically necessary for diabetes monitoring",
                        "Approve lipid panel - appropriate for cardiovascular risk assessment",
                        "Schedule endocrinologist follow-up in 3 months",
                        "Consider medication adjustment based on results"
                    ],
                    "priority": "HIGH"
                }
            }
        }
    
    @pytest.fixture
    def mock_comprehensive_services(self):
        """Comprehensive mocking for full workflow testing."""
        with patch('api.main.patient_lookup_service') as mock_patient, \
             patch('api.main.xml_processing_service') as mock_xml, \
             patch('api.main.claude_analysis_service') as mock_claude, \
             patch('api.main.workflow_orchestrator') as mock_workflow:
            
            # Mock patient lookup service
            mock_patient.get_all_patients.return_value = {
                self.test_patient_id: "Ahmed_Al_Mansoori_E2E",
                "patient-e2e-test-002": "Fatima_Al_Zahra_E2E"
            }
            
            mock_patient.validate_patient_folder_structure.return_value = {
                "folder_path": f"/test/patient/{self.test_patient_id}",
                "has_profile": True,
                "xml_files": 1,
                "processed_json_files": 0
            }
            
            mock_patient.check_patient_data_availability.return_value = {
                "patient_exists": True,
                "raw_data_available": True,
                "processed_data_available": True,
                "folder_name": "Ahmed_Al_Mansoori_E2E",
                "xml_files_count": 1,
                "json_files_count": 1,
                "raw_data_path": f"/test/raw/{self.test_patient_id}",
                "processed_data_path": f"/test/processed/{self.test_patient_id}"
            }
            
            mock_patient.get_patient_profile.return_value = {
                "patient_id": self.test_patient_id,
                "full_name": "Ahmed Al Mansoori",
                "date_of_birth": "1988-03-15",
                "insurance_details": {
                    "company": "Dubai Health Insurance",
                    "member_id": "DH789012",
                    "policy_number": "POL345678"
                }
            }
            
            mock_patient.get_patient_folder_paths.return_value = {
                "raw_data_path": f"/test/raw/{self.test_patient_id}",
                "processed_data_path": f"/test/processed/{self.test_patient_id}"
            }
            
            mock_patient.get_patient_history.return_value = [self.expected_bundle]
            
            # Mock XML processing service
            mock_xml.process_xml_file = AsyncMock(return_value={
                "success": True,
                "bundle": self.expected_bundle,
                "patient_id": "TXN-E2E-TEST-001"
            })
            
            mock_xml.get_processing_stats.return_value = {
                "service_status": "ready",
                "total_files_processed": 1,
                "success_rate": 1.0
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
                "patient_id": "TXN-E2E-TEST-001",
                "claude_analysis": self.expected_analysis
            })
            
            # Mock file system operations
            with patch('pathlib.Path.glob') as mock_glob, \
                 patch('pathlib.Path.stat') as mock_stat, \
                 patch('pathlib.Path.mkdir'), \
                 patch('builtins.open', create=True) as mock_open, \
                 patch('json.dump'):
                
                mock_file = Mock()
                mock_file.name = "e2e_test.xml"
                mock_file.stat.return_value.st_mtime = time.time()
                mock_file.stat.return_value.st_size = len(self.sample_xml)
                mock_glob.return_value = [mock_file]
                
                mock_open.return_value.__enter__.return_value.read.return_value = self.sample_xml.encode()
                
                yield {
                    "patient": mock_patient,
                    "xml": mock_xml,
                    "claude": mock_claude,
                    "workflow": mock_workflow,
                    "glob": mock_glob,
                    "stat": mock_stat,
                    "open": mock_open
                }
    
    def test_complete_patient_workflow_success(self, mock_comprehensive_services):
        """Test complete successful patient workflow from start to finish."""
        # Step 1: Get patient list (simulating dropdown population)
        patients_response = self.client.get("/api/patients")
        assert patients_response.status_code == 200
        
        patients = patients_response.json()
        assert len(patients) == 2
        
        # Find our test patient
        test_patient = next(
            (p for p in patients if p["patient_id"] == self.test_patient_id),
            None
        )
        assert test_patient is not None
        assert test_patient["has_profile"] is True
        
        # Step 2: Upload XML file with patient context
        files = {
            "file": ("diabetes_monitoring_e2e.xml", BytesIO(self.sample_xml.encode()), "application/xml")
        }
        data = {
            "source": "eclaim",
            "patient_id": self.test_patient_id
        }
        
        upload_response = self.client.post("/api/upload-xml", files=files, data=data)
        assert upload_response.status_code == 200
        
        upload_result = upload_response.json()
        assert upload_result["success"] is True
        assert upload_result["patient_id"] == "TXN-E2E-TEST-001"
        assert "data" in upload_result
        
        # Verify processed bundle structure
        bundle = upload_result["data"]
        assert bundle["resourceType"] == "Bundle"
        assert bundle["authorization_id"] == "TXN-E2E-TEST-001"
        assert "fhir_resources" in bundle
        
        # Step 3: Process patient data (using extracted patient ID)
        extracted_patient_id = upload_result["patient_id"]
        
        # Update mock to reflect that we now have raw data
        mock_comprehensive_services["patient"].check_patient_data_availability.return_value.update({
            "raw_data_available": True,
            "xml_files_count": 1
        })
        
        process_response = self.client.post(f"/api/process/{extracted_patient_id}")
        assert process_response.status_code == 200
        
        process_result = process_response.json()
        assert process_result["success"] is True
        assert process_result["patient_id"] == extracted_patient_id
        
        # Step 4: Run Claude analysis
        # Update mock to reflect processed data availability
        mock_comprehensive_services["patient"].check_patient_data_availability.return_value.update({
            "processed_data_available": True,
            "json_files_count": 1
        })
        
        analysis_response = self.client.post(
            f"/api/analyze/{extracted_patient_id}",
            params={"cost_limit_usd": 3.0, "include_history": True}
        )
        assert analysis_response.status_code == 200
        
        analysis_result = analysis_response.json()
        assert analysis_result["success"] is True
        assert analysis_result["patient_id"] == extracted_patient_id
        assert "analysis" in analysis_result
        
        # Verify analysis quality
        analysis = analysis_result["analysis"]
        assert analysis["cost_usd"] == 1.25
        assert "agent_results" in analysis
        assert "clinical_analyzer" in analysis["agent_results"]
        assert "medical_reviewer" in analysis["agent_results"]
        assert "recommendation_agent" in analysis["agent_results"]
        
        # Step 5: View patient dashboard
        dashboard_response = self.client.get(f"/api/patient/{extracted_patient_id}/dashboard")
        assert dashboard_response.status_code == 200
        
        dashboard_data = dashboard_response.json()
        assert "patient_info" in dashboard_data
        assert "recent_files" in dashboard_data
        assert "summary_stats" in dashboard_data
        
        # Verify dashboard reflects completed workflow
        patient_info = dashboard_data["patient_info"]
        assert patient_info["patient_id"] == extracted_patient_id
        assert patient_info["has_profile"] is True
        
        summary_stats = dashboard_data["summary_stats"]
        assert summary_stats["claude_analysis_available"] is True
        assert summary_stats["total_xml_files"] >= 1
        assert summary_stats["total_processed_files"] >= 1
        
        # Verify all services were called in correct sequence
        mock_comprehensive_services["xml"].process_xml_file.assert_called()
        mock_comprehensive_services["workflow"].analyze_existing_patient.assert_called_once()
    
    def test_workflow_with_processing_error(self, mock_comprehensive_services):
        """Test workflow handling when XML processing fails."""
        # Mock XML processing failure
        mock_comprehensive_services["xml"].process_xml_file.return_value = {
            "success": False,
            "error": "Invalid XML structure at line 15"
        }
        
        # Step 1: Upload file
        files = {
            "file": ("invalid.xml", BytesIO(b"<invalid>xml</invalid>"), "application/xml")
        }
        data = {"source": "eclaim", "patient_id": self.test_patient_id}
        
        upload_response = self.client.post("/api/upload-xml", files=files, data=data)
        assert upload_response.status_code == 200
        
        upload_result = upload_response.json()
        assert upload_result["success"] is False
        assert "Invalid XML structure" in upload_result["error"]
        
        # Step 2: Analysis should fail due to no processed data
        mock_comprehensive_services["patient"].check_patient_data_availability.return_value.update({
            "processed_data_available": False,
            "json_files_count": 0
        })
        
        analysis_response = self.client.post(f"/api/analyze/{self.test_patient_id}")
        assert analysis_response.status_code == 404
        assert "No processed data found" in analysis_response.json()["detail"]
    
    def test_workflow_with_claude_unavailable(self, mock_comprehensive_services):
        """Test workflow when Claude analysis is unavailable."""
        # Mock Claude unavailable
        mock_comprehensive_services["claude"].claude_available = False
        
        # Steps 1-3: Upload and process successfully
        files = {
            "file": ("test.xml", BytesIO(self.sample_xml.encode()), "application/xml")
        }
        data = {"source": "eclaim", "patient_id": self.test_patient_id}
        
        upload_response = self.client.post("/api/upload-xml", files=files, data=data)
        assert upload_response.status_code == 200
        
        process_response = self.client.post(f"/api/process/{self.test_patient_id}")
        assert process_response.status_code == 200
        
        # Step 4: Analysis should fail due to Claude unavailability
        analysis_response = self.client.post(f"/api/analyze/{self.test_patient_id}")
        assert analysis_response.status_code == 503
        assert "Claude analysis service is not available" in analysis_response.json()["detail"]
        
        # Step 5: Dashboard should still work but show Claude as unavailable
        dashboard_response = self.client.get(f"/api/patient/{self.test_patient_id}/dashboard")
        assert dashboard_response.status_code == 200
        
        dashboard_data = dashboard_response.json()
        summary_stats = dashboard_data["summary_stats"]
        assert summary_stats["claude_analysis_available"] is False
    
    def test_workflow_with_cost_limit_exceeded(self, mock_comprehensive_services):
        """Test workflow when analysis cost limit is exceeded."""
        # Mock high-cost analysis
        mock_comprehensive_services["workflow"].analyze_existing_patient.return_value = {
            "success": False,
            "error": "Analysis cost ($5.50) exceeds limit ($2.00)",
            "estimated_cost": 5.50
        }
        
        # Complete upload and processing
        files = {
            "file": ("complex.xml", BytesIO(self.sample_xml.encode()), "application/xml")
        }
        data = {"source": "eclaim", "patient_id": self.test_patient_id}
        
        upload_response = self.client.post("/api/upload-xml", files=files, data=data)
        assert upload_response.status_code == 200
        
        process_response = self.client.post(f"/api/process/{self.test_patient_id}")
        assert process_response.status_code == 200
        
        # Analysis with low cost limit
        analysis_response = self.client.post(
            f"/api/analyze/{self.test_patient_id}",
            params={"cost_limit_usd": 2.0}
        )
        assert analysis_response.status_code == 500
        
        analysis_result = analysis_response.json()
        assert "cost" in analysis_result["detail"].lower()
        assert "exceeds limit" in analysis_result["detail"]
    
    def test_workflow_performance_tracking(self, mock_comprehensive_services):
        """Test that workflow tracks performance metrics correctly."""
        start_time = time.time()
        
        # Complete workflow
        files = {
            "file": ("perf_test.xml", BytesIO(self.sample_xml.encode()), "application/xml")
        }
        data = {"source": "eclaim", "patient_id": self.test_patient_id}
        
        # Track upload time
        upload_response = self.client.post("/api/upload-xml", files=files, data=data)
        assert upload_response.status_code == 200
        
        upload_result = upload_response.json()
        assert "metadata" in upload_result
        assert "processing_time_seconds" in upload_result["metadata"]
        assert upload_result["metadata"]["processing_time_seconds"] >= 0
        
        # Track processing time
        process_response = self.client.post(f"/api/process/{self.test_patient_id}")
        assert process_response.status_code == 200
        
        process_result = process_response.json()
        assert "metadata" in process_result
        assert "processing_time_seconds" in process_result["metadata"]
        
        # Track analysis time
        analysis_response = self.client.post(
            f"/api/analyze/{self.test_patient_id}",
            params={"cost_limit_usd": 3.0}
        )
        assert analysis_response.status_code == 200
        
        total_time = time.time() - start_time
        assert total_time < 5.0  # Ensure reasonable performance
    
    def test_workflow_data_consistency(self, mock_comprehensive_services):
        """Test data consistency throughout the workflow."""
        # Upload with specific patient ID
        files = {
            "file": ("consistency_test.xml", BytesIO(self.sample_xml.encode()), "application/xml")
        }
        data = {"source": "eclaim", "patient_id": self.test_patient_id}
        
        upload_response = self.client.post("/api/upload-xml", files=files, data=data)
        upload_result = upload_response.json()
        extracted_patient_id = upload_result["patient_id"]
        
        # Verify patient ID consistency in processing
        process_response = self.client.post(f"/api/process/{extracted_patient_id}")
        process_result = process_response.json()
        assert process_result["patient_id"] == extracted_patient_id
        
        # Verify patient ID consistency in analysis
        analysis_response = self.client.post(f"/api/analyze/{extracted_patient_id}")
        analysis_result = analysis_response.json()
        assert analysis_result["patient_id"] == extracted_patient_id
        
        # Verify patient ID consistency in dashboard
        dashboard_response = self.client.get(f"/api/patient/{extracted_patient_id}/dashboard")
        dashboard_result = dashboard_response.json()
        assert dashboard_result["patient_info"]["patient_id"] == extracted_patient_id
        
        # Verify data references are consistent
        upload_bundle = upload_result["data"]
        process_bundle = process_result["data"]
        
        assert upload_bundle["authorization_id"] == process_bundle["authorization_id"]
        assert upload_bundle["sender"] == process_bundle["sender"]
        assert upload_bundle["receiver"] == process_bundle["receiver"]
    
    def test_workflow_concurrent_patients(self, mock_comprehensive_services):
        """Test workflow handles concurrent processing of different patients."""
        import concurrent.futures
        
        def process_patient(patient_id: str, xml_content: str) -> Dict[str, Any]:
            """Process a single patient workflow."""
            # Upload
            files = {
                "file": (f"patient_{patient_id}.xml", BytesIO(xml_content.encode()), "application/xml")
            }
            data = {"source": "eclaim", "patient_id": patient_id}
            
            upload_response = self.client.post("/api/upload-xml", files=files, data=data)
            if upload_response.status_code != 200:
                return {"success": False, "step": "upload", "error": upload_response.json()}
            
            # Process
            upload_result = upload_response.json()
            extracted_id = upload_result["patient_id"]
            
            process_response = self.client.post(f"/api/process/{extracted_id}")
            if process_response.status_code != 200:
                return {"success": False, "step": "process", "error": process_response.json()}
            
            # Analyze
            analysis_response = self.client.post(f"/api/analyze/{extracted_id}")
            if analysis_response.status_code != 200:
                return {"success": False, "step": "analyze", "error": analysis_response.json()}
            
            return {"success": True, "patient_id": extracted_id}
        
        # Process multiple patients concurrently
        patient_ids = ["patient-concurrent-001", "patient-concurrent-002", "patient-concurrent-003"]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(process_patient, pid, self.sample_xml)
                for pid in patient_ids
            ]
            
            results = [future.result() for future in futures]
        
        # All should succeed
        for result in results:
            assert result["success"] is True, f"Failed at step {result.get('step')}: {result.get('error')}"
        
        # Verify different patient IDs were extracted
        extracted_ids = [result["patient_id"] for result in results]
        assert len(set(extracted_ids)) == len(extracted_ids), "Patient IDs should be unique"
    
    def test_workflow_error_recovery(self, mock_comprehensive_services):
        """Test workflow error recovery and retry capabilities."""
        # First attempt fails
        mock_comprehensive_services["xml"].process_xml_file.side_effect = [
            {"success": False, "error": "Temporary network error"},
            {"success": True, "bundle": self.expected_bundle, "patient_id": "TXN-E2E-TEST-001"}
        ]
        
        files = {
            "file": ("retry_test.xml", BytesIO(self.sample_xml.encode()), "application/xml")
        }
        data = {"source": "eclaim", "patient_id": self.test_patient_id}
        
        # First attempt should fail
        first_response = self.client.post("/api/upload-xml", files=files, data=data)
        assert first_response.status_code == 200
        first_result = first_response.json()
        assert first_result["success"] is False
        
        # Second attempt should succeed
        second_response = self.client.post("/api/upload-xml", files=files, data=data)
        assert second_response.status_code == 200
        second_result = second_response.json()
        assert second_result["success"] is True
        
        # Verify service was called twice
        assert mock_comprehensive_services["xml"].process_xml_file.call_count == 2
    
    def test_health_check_during_workflow(self, mock_comprehensive_services):
        """Test system health check reflects workflow activity."""
        # Check initial health
        health_response = self.client.get("/api/health")
        assert health_response.status_code == 200
        
        initial_health = health_response.json()
        assert initial_health["status"] in ["healthy", "degraded"]
        
        # Run workflow
        files = {
            "file": ("health_test.xml", BytesIO(self.sample_xml.encode()), "application/xml")
        }
        data = {"source": "eclaim", "patient_id": self.test_patient_id}
        
        upload_response = self.client.post("/api/upload-xml", files=files, data=data)
        assert upload_response.status_code == 200
        
        # Check health after workflow activity
        final_health_response = self.client.get("/api/health")
        assert final_health_response.status_code == 200
        
        final_health = final_health_response.json()
        assert final_health["xml_processing_available"] is True
        assert final_health["claude_analysis_available"] is True
        assert final_health["patient_index_size"] >= 0
        assert "eclaim" in final_health.get("supported_sources", [])
        assert "shafafiya" in final_health.get("supported_sources", [])


@pytest.mark.integration
@pytest.mark.slow
class TestPatientWorkflowRealScenarios:
    """Integration tests with more realistic scenarios."""
    
    def setup_method(self):
        """Set up realistic test scenarios."""
        self.client = TestClient(app)
    
    def test_large_xml_file_workflow(self):
        """Test workflow with large XML files (realistic hospital data)."""
        # Create large XML with multiple service requests
        large_xml = self._create_large_xml_file(service_count=50)
        
        with patch('api.main.patient_lookup_service'), \
             patch('api.main.xml_processing_service') as mock_xml, \
             patch('api.main.claude_analysis_service'), \
             patch('api.main.workflow_orchestrator'):
            
            mock_xml.process_xml_file = AsyncMock(return_value={
                "success": True,
                "bundle": {"resourceType": "Bundle", "id": "large-bundle"},
                "patient_id": "large-patient-001"
            })
            
            files = {
                "file": ("large_hospital_data.xml", BytesIO(large_xml.encode()), "application/xml")
            }
            data = {"source": "eclaim"}
            
            response = self.client.post("/api/upload-xml", files=files, data=data)
            
            assert response.status_code == 200
            result = response.json()
            assert result["success"] is True
            
            # Verify processing time is reasonable even for large files
            processing_time = result["metadata"]["processing_time_seconds"]
            assert processing_time < 30  # Should process within 30 seconds
    
    def _create_large_xml_file(self, service_count: int = 50) -> str:
        """Create large XML file for testing."""
        services = ""
        for i in range(service_count):
            services += f"""
            <ServiceRequest>
                <ct:ActivityCode>8303{i % 10}</ct:ActivityCode>
                <ct:DiagnosisCode>E11.{i % 10}</ct:DiagnosisCode>
                <ct:ActivityDateTime>05/08/2025 09:00</ct:ActivityDateTime>
                <ct:ActivityInstructions>Service {i} for comprehensive care</ct:ActivityInstructions>
                <RequestedAmount currency="AED">{100 + i * 5}.00</RequestedAmount>
            </ServiceRequest>"""
        
        return f"""<?xml version="1.0" encoding="UTF-8"?>
        <PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
            <Header>
                <SenderID>LARGE_HOSPITAL_001</SenderID>
                <ReceiverID>MAJOR_PAYER_001</ReceiverID>
                <TransactionDateTime>04/08/2025 14:30</TransactionDateTime>
                <TransactionID>TXN-LARGE-001</TransactionID>
            </Header>
            <JustificationText>Comprehensive care plan for complex patient case requiring multiple diagnostic and therapeutic interventions. Patient presents with multiple comorbidities requiring coordinated care approach.</JustificationText>
            <ServiceRequests>{services}
            </ServiceRequests>
        </PriorAuthorizationRequest>"""


@pytest.mark.performance
class TestPatientWorkflowPerformance:
    """Performance tests for patient workflow."""
    
    def setup_method(self):
        """Set up performance testing."""
        self.client = TestClient(app)
    
    def test_workflow_response_times(self):
        """Test that workflow steps complete within acceptable time limits."""
        with patch('api.main.patient_lookup_service'), \
             patch('api.main.xml_processing_service') as mock_xml, \
             patch('api.main.claude_analysis_service'), \
             patch('api.main.workflow_orchestrator') as mock_workflow:
            
            # Mock quick responses
            mock_xml.process_xml_file = AsyncMock(return_value={
                "success": True,
                "bundle": {"resourceType": "Bundle"},
                "patient_id": "perf-test-001"
            })
            
            mock_workflow.analyze_existing_patient = AsyncMock(return_value={
                "success": True,
                "patient_id": "perf-test-001",
                "claude_analysis": {"summary": "Quick analysis", "cost_usd": 0.25}
            })
            
            # Test upload response time
            start_time = time.time()
            
            files = {"file": ("perf.xml", BytesIO(b"<xml>test</xml>"), "application/xml")}
            data = {"source": "eclaim"}
            
            response = self.client.post("/api/upload-xml", files=files, data=data)
            upload_time = time.time() - start_time
            
            assert response.status_code == 200
            assert upload_time < 5.0  # Should complete within 5 seconds
            
            # Test analysis response time
            start_time = time.time()
            
            with patch('api.main.patient_lookup_service') as mock_patient:
                mock_patient.check_patient_data_availability.return_value = {
                    "patient_exists": True,
                    "processed_data_available": True
                }
                
                analysis_response = self.client.post("/api/analyze/perf-test-001")
                analysis_time = time.time() - start_time
            
            assert analysis_response.status_code == 200
            assert analysis_time < 10.0  # Should complete within 10 seconds
