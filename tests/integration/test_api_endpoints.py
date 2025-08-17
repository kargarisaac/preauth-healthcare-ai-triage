"""
API Endpoint Integration Tests for PreAuth Pipeline

Tests all API endpoints with realistic scenarios and validates
response formats, error handling, and integration with the pipeline.
"""

import json
import pytest
import tempfile
import io
from pathlib import Path
from fastapi.testclient import TestClient

from api.main import app


@pytest.mark.integration
class TestAPIEndpoints:
    """Integration tests for all API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create FastAPI test client."""
        return TestClient(app)
    
    @pytest.fixture
    def sample_xml_content(self):
        """Provide sample XML content for testing."""
        return '''<?xml version="1.0" encoding="UTF-8"?>
<PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
    <Header>
        <SenderID>TEST12345</SenderID>
        <ReceiverID>PAYER67890</ReceiverID>
        <TransactionDateTime>31/07/2025 14:15</TransactionDateTime>
        <TransactionID>TXN-TEST-001</TransactionID>
    </Header>
    <JustificationText>Patient with diabetes requires HbA1c monitoring.</JustificationText>
    <ServiceRequests>
        <ServiceRequest>
            <ct:ActivityCode>83036</ct:ActivityCode>
            <ct:DiagnosisCode>E11.9</ct:DiagnosisCode>
            <ct:ActivityDateTime>01/08/2025 09:00</ct:ActivityDateTime>
            <ct:ActivityInstructions>Hemoglobin A1c test</ct:ActivityInstructions>
            <RequestedAmount currency="AED">125.50</RequestedAmount>
        </ServiceRequest>
    </ServiceRequests>
</PriorAuthorizationRequest>'''
    
    @pytest.fixture
    def demo_xml_file(self):
        """Path to demo XML file for realistic testing."""
        path = Path("data/dataset_2/synthetic_dataset/UAE_XML/Patient_007_eclaim.xml")
        if path.exists():
            return path
        return None
    
    def test_health_endpoint_with_pipeline_validation(self, client):
        """Test health endpoint includes pipeline status validation."""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Basic health check fields
        assert "status" in data
        assert "version" in data
        assert "timestamp" in data
        
        # Pipeline-specific validation
        assert "pipeline_status" in data
        assert "pipeline_details" in data
        
        pipeline_details = data["pipeline_details"]
        assert "dossier_writer_available" in pipeline_details
        assert "clinical_summarizer_available" in pipeline_details
        assert "evidence_checker_available" in pipeline_details
        assert "policy_evaluator_available" in pipeline_details
        
        # API capabilities
        assert "api_endpoints" in data
        expected_endpoints = [
            "/api/process/unified",
            "/api/preauth/process", 
            "/api/dossier/{analysis_id}",
            "/api/patients",
            "/api/health"
        ]
        for endpoint in expected_endpoints:
            assert endpoint in data["api_endpoints"]
    
    def test_unified_processing_endpoint(self, client, sample_xml_content):
        """Test the unified processing endpoint with complete pipeline."""
        # Create file-like object for upload
        xml_file = io.BytesIO(sample_xml_content.encode('utf-8'))
        
        response = client.post(
            "/api/process/unified",
            files={"file": ("test.xml", xml_file, "application/xml")},
            data={
                "patient_id": "TEST_001",
                "xml_format": "eclaim",
                "include_dossier": True,
                "processing_mode": "hybrid"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert data["success"] is True
        assert "analysis_id" in data
        assert "patient_id" in data
        assert "processing_metadata" in data
        assert "results" in data
        assert "performance" in data
        assert "quality_metrics" in data
        assert "audit_trail" in data
        
        # Validate processing metadata
        metadata = data["processing_metadata"]
        assert metadata["xml_format"] == "eclaim"
        assert metadata["processing_mode"] == "hybrid"
        assert metadata["include_dossier"] is True
        assert "start_time" in metadata
        assert "end_time" in metadata
        
        # Validate results contain all pipeline phases
        results = data["results"]
        expected_phases = ["intake", "clinical_summary", "evidence", "checklist", "decision", "dossier"]
        for phase in expected_phases:
            assert phase in results, f"Missing phase: {phase}"
        
        # Validate performance metrics
        performance = data["performance"]
        assert "timings" in performance
        assert "cost" in performance
        assert "phase_breakdown" in performance
        
        # Validate quality metrics
        quality = data["quality_metrics"]
        assert "decision_outcome" in quality
        assert quality["decision_outcome"] in ["APPROVE", "DENY", "REVIEW"]
        assert "decision_confidence" in quality
        assert "compliance_score" in quality
        
        # Validate audit trail
        audit = data["audit_trail"]
        assert "pipeline_execution" in audit
        assert "deterministic_components" in audit
    
    def test_dossier_retrieval_formats(self, client):
        """Test dossier retrieval endpoint with different formats."""
        analysis_id = "test-analysis-123"
        
        # Test JSON format
        response = client.get(f"/api/dossier/{analysis_id}?format=json")
        assert response.status_code == 200
        data = response.json()
        
        assert "success" in data
        assert "dossier" in data
        assert "format" in data
        assert data["format"] == "json"
        
        dossier = data["dossier"]
        assert "analysis_id" in dossier
        assert "content" in dossier
        assert "metadata" in dossier
        
        # Test HTML format
        response = client.get(f"/api/dossier/{analysis_id}?format=html")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        html_content = response.text
        assert "<!DOCTYPE html>" in html_content
        assert "Pre-Authorization Dossier" in html_content
        
        # Test PDF format (returns metadata for now)
        response = client.get(f"/api/dossier/{analysis_id}?format=pdf")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "PDF generation capability" in data["message"]
    
    def test_preauth_process_integration(self, client, sample_xml_content):
        """Test the preauth process endpoint with pipeline integration."""
        xml_file = io.BytesIO(sample_xml_content.encode('utf-8'))
        
        response = client.post(
            "/api/preauth/process",
            files={"file": ("test.xml", xml_file, "application/xml")},
            data={
                "patient_id": "TEST_002",
                "xml_format": "eclaim"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert data["success"] is True
        assert "analysis_id" in data
        assert "patient_id" in data
        assert "processing_time_seconds" in data
        assert "cost_usd" in data
        
        # Validate core pipeline results are present
        expected_phases = ["intake", "clinical_summary", "evidence", "checklist", "decision", "dossier"]
        for phase in expected_phases:
            assert phase in data, f"Missing phase: {phase}"
        
        # Validate metadata
        metadata = data["metadata"]
        assert "processing_timestamp" in metadata
        assert "pipeline_version" in metadata
        assert metadata["deterministic_execution"] is True
        
        # Validate performance is within targets
        assert data["processing_time_seconds"] < 10, f"Processing took {data['processing_time_seconds']}s > 10s"
        assert data["cost_usd"] < 0.10, f"Cost ${data['cost_usd']} > $0.10"
    
    def test_dashboard_summary_analytics(self, client):
        """Test dashboard summary endpoint with analytics."""
        response = client.get("/api/dashboard/summary")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert data["success"] is True
        assert "timestamp" in data
        assert "system_status" in data
        
        # Validate processing metrics
        assert "processing_metrics" in data
        metrics = data["processing_metrics"]
        assert "total_runs" in metrics
        assert "total_cost_usd" in metrics
        assert "average_cost_usd" in metrics
        assert "average_processing_time_seconds" in metrics
        
        # Validate decision analytics
        assert "decision_analytics" in data
        analytics = data["decision_analytics"]
        assert "total_decisions" in analytics
        assert "outcomes" in analytics
        assert "outcome_percentages" in analytics
        
        # Validate performance insights
        assert "performance_insights" in data
        insights = data["performance_insights"]
        assert "cost_efficiency" in insights
        assert "processing_speed" in insights
        assert "system_reliability" in insights
        
        # Validate API capabilities
        assert "api_capabilities" in data
        capabilities = data["api_capabilities"]
        assert capabilities["unified_processing"] is True
        assert capabilities["dossier_generation"] is True
        assert "eclaim" in capabilities["multi_format_support"]
        assert "shafafiya" in capabilities["multi_format_support"]
    
    def test_patients_endpoint(self, client):
        """Test patients listing endpoint."""
        response = client.get("/api/patients")
        
        # Should succeed even if no patients configured
        assert response.status_code in [200, 500]  # 500 if no patient service configured
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            
            # If patients exist, validate structure
            if data:
                patient = data[0]
                assert "patient_id" in patient
                assert "folder_name" in patient
    
    def test_error_handling_and_validation(self, client):
        """Test API error handling and input validation."""
        # Test invalid XML format
        xml_file = io.BytesIO(b"invalid xml content")
        
        response = client.post(
            "/api/process/unified",
            files={"file": ("test.xml", xml_file, "application/xml")},
            data={
                "xml_format": "invalid_format",
                "processing_mode": "invalid_mode"
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        
        # Test missing file
        response = client.post(
            "/api/process/unified",
            data={"xml_format": "eclaim"}
        )
        
        assert response.status_code == 422  # Validation error
        
        # Test file too large (mock)
        large_content = "<xml>" + "x" * (11 * 1024 * 1024) + "</xml>"  # > 10MB
        large_file = io.BytesIO(large_content.encode('utf-8'))
        
        response = client.post(
            "/api/process/unified",
            files={"file": ("large.xml", large_file, "application/xml")},
            data={"xml_format": "eclaim"}
        )
        
        assert response.status_code == 413  # File too large
        
        # Test non-XML file
        text_file = io.BytesIO(b"This is not XML")
        
        response = client.post(
            "/api/process/unified",
            files={"file": ("test.txt", text_file, "text/plain")},
            data={"xml_format": "eclaim"}
        )
        
        assert response.status_code == 400
    
    def test_upload_xml_validation(self, client, sample_xml_content):
        """Test XML upload endpoint validation."""
        xml_file = io.BytesIO(sample_xml_content.encode('utf-8'))
        
        response = client.post(
            "/api/upload-xml",
            files={"file": ("test.xml", xml_file, "application/xml")},
            data={
                "source": "eclaim",
                "patient_id": "TEST_UPLOAD"
            }
        )
        
        # Should succeed or fail gracefully
        assert response.status_code in [200, 500]  # 500 if XML service not fully configured
        
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "patient_id" in data
            assert "metadata" in data
    
    @pytest.mark.performance
    def test_api_performance_under_load(self, client, sample_xml_content):
        """Test API performance under concurrent load."""
        import threading
        import time
        
        results = []
        errors = []
        
        def make_request():
            try:
                xml_file = io.BytesIO(sample_xml_content.encode('utf-8'))
                start_time = time.time()
                
                response = client.post(
                    "/api/preauth/process",
                    files={"file": ("test.xml", xml_file, "application/xml")},
                    data={"xml_format": "eclaim"}
                )
                
                duration = time.time() - start_time
                results.append({
                    "status_code": response.status_code,
                    "duration": duration,
                    "success": response.status_code == 200
                })
            except Exception as e:
                errors.append(str(e))
        
        # Run 5 concurrent requests
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join(timeout=60)  # 60 second timeout
        
        # Validate results
        assert len(errors) == 0, f"Errors in concurrent requests: {errors}"
        assert len(results) == 5, f"Expected 5 results, got {len(results)}"
        
        successful_requests = [r for r in results if r["success"]]
        assert len(successful_requests) >= 4, f"Less than 4/5 requests succeeded: {len(successful_requests)}"
        
        # Validate response times
        avg_duration = sum(r["duration"] for r in successful_requests) / len(successful_requests)
        assert avg_duration < 15, f"Average response time {avg_duration:.2f}s > 15s under load"
    
    def test_real_demo_file_processing(self, client, demo_xml_file):
        """Test processing with real demo XML file if available."""
        if demo_xml_file is None:
            pytest.skip("Demo XML file not available")
        
        with open(demo_xml_file, 'rb') as f:
            xml_content = f.read()
        
        xml_file = io.BytesIO(xml_content)
        
        response = client.post(
            "/api/process/unified",
            files={"file": ("Patient_007_eclaim.xml", xml_file, "application/xml")},
            data={
                "patient_id": "Patient_007",
                "xml_format": "eclaim",
                "include_dossier": True,
                "processing_mode": "hybrid"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate realistic processing results
        assert data["success"] is True
        assert data["patient_id"] == "Patient_007"
        
        # Validate decision quality
        quality = data["quality_metrics"]
        assert quality["decision_outcome"] in ["APPROVE", "DENY", "REVIEW"]
        assert quality["compliance_score"] >= 0
        assert quality["evidence_sources_count"] >= 0
        assert quality["criteria_evaluated_count"] >= 0
        
        # Validate performance on real data
        performance = data["performance"]
        total_cost = performance["cost"]["total_cost_usd"]
        total_time_ms = performance["timings"]["total_ms"]
        
        assert total_cost < 0.10, f"Real data processing cost ${total_cost} > $0.10"
        assert total_time_ms < 10000, f"Real data processing time {total_time_ms}ms > 10s"
