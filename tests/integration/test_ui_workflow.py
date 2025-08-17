"""
End-to-End UI Workflow Tests

Tests the complete user interface workflow from file upload
through processing to results display and dossier viewing.
"""

import json
import pytest
import time
import io
from pathlib import Path
from fastapi.testclient import TestClient

from api.main import app


@pytest.mark.integration
class TestUIWorkflow:
    """End-to-end UI workflow integration tests."""
    
    @pytest.fixture
    def client(self):
        """Create FastAPI test client for UI testing."""
        return TestClient(app)
    
    @pytest.fixture
    def sample_xml_file(self):
        """Sample XML content for upload testing."""
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
    <Header>
        <SenderID>PROV12345</SenderID>
        <ReceiverID>PAYER67890</ReceiverID>
        <TransactionDateTime>31/07/2025 14:15</TransactionDateTime>
        <TransactionID>TXN-UI-TEST-001</TransactionID>
    </Header>
    <JustificationText>Patient with Type 2 diabetes requires comprehensive monitoring including HbA1c testing for glycemic control assessment. Recent symptoms include increased thirst and fatigue. Current medication includes metformin 1000mg twice daily. Last HbA1c was 8.9% three months ago indicating suboptimal control.</JustificationText>
    <ServiceRequests>
        <ServiceRequest>
            <ct:ActivityCode>83036</ct:ActivityCode>
            <ct:DiagnosisCode>E11.9</ct:DiagnosisCode>
            <ct:ActivityDateTime>01/08/2025 09:00</ct:ActivityDateTime>
            <ct:ActivityInstructions>Hemoglobin A1c test for diabetes monitoring</ct:ActivityInstructions>
            <RequestedAmount currency="AED">125.50</RequestedAmount>
        </ServiceRequest>
        <ServiceRequest>
            <ct:ActivityCode>80061</ct:ActivityCode>
            <ct:DiagnosisCode>E11.9</ct:DiagnosisCode>
            <ct:ActivityDateTime>01/08/2025 09:00</ct:ActivityDateTime>
            <ct:ActivityInstructions>Lipid panel for cardiovascular risk assessment</ct:ActivityInstructions>
            <RequestedAmount currency="AED">89.75</RequestedAmount>
        </ServiceRequest>
    </ServiceRequests>
</PriorAuthorizationRequest>'''
        return xml_content
    
    def test_complete_ui_workflow(self, client, sample_xml_file):
        """Test complete user workflow: upload → process → view results → dossier."""
        # Step 1: Health check (user loads page)
        health_response = client.get("/api/health")
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert health_data["status"] in ["healthy", "degraded"]
        assert health_data["pipeline_status"] in ["healthy", "degraded"]
        
        # Step 2: File upload and processing (user uploads XML file)
        xml_file = io.BytesIO(sample_xml_file.encode('utf-8'))
        
        upload_start = time.time()
        process_response = client.post(
            "/api/process/unified",
            files={"file": ("diabetes_monitoring.xml", xml_file, "application/xml")},
            data={
                "patient_id": "UI_TEST_001",
                "xml_format": "eclaim",
                "include_dossier": True,
                "processing_mode": "hybrid"
            }
        )
        upload_duration = time.time() - upload_start
        
        # Validate processing response
        assert process_response.status_code == 200
        process_data = process_response.json()
        assert process_data["success"] is True
        assert "analysis_id" in process_data
        assert "results" in process_data
        assert "performance" in process_data
        assert "quality_metrics" in process_data
        
        analysis_id = process_data["analysis_id"]
        
        # Validate user experience metrics
        assert upload_duration < 15, f"Upload and processing took {upload_duration:.2f}s > 15s"
        
        # Step 3: View results (user sees processing results)
        results = process_data["results"]
        
        # Validate all expected results are present for UI display
        expected_phases = ["intake", "clinical_summary", "evidence", "checklist", "decision", "dossier"]
        for phase in expected_phases:
            assert phase in results, f"Missing {phase} for UI display"
        
        # Validate decision is displayable
        decision = results["decision"]
        assert "outcome" in decision
        assert decision["outcome"] in ["APPROVE", "DENY", "REVIEW"]
        assert "rationale" in decision
        assert len(decision["rationale"]) > 10, "Decision rationale too brief for UI"
        
        # Validate clinical summary is displayable
        clinical_summary = results["clinical_summary"]
        assert "executive_summary" in clinical_summary
        assert len(clinical_summary["executive_summary"]) > 20, "Clinical summary too brief for UI"
        
        # Step 4: View performance metrics (user sees processing stats)
        performance = process_data["performance"]
        assert "timings" in performance
        assert "cost" in performance
        
        # UI should show user-friendly metrics
        timings = performance["timings"]
        total_ms = timings.get("total_ms", 0)
        assert total_ms > 0, "No timing data for UI display"
        
        cost = performance["cost"]
        total_cost = cost.get("total_cost_usd", 0)
        assert total_cost >= 0, "Invalid cost data for UI display"
        
        # Step 5: View detailed dossier (user clicks to view professional report)
        dossier_response = client.get(f"/api/dossier/{analysis_id}?format=html")
        assert dossier_response.status_code == 200
        assert "text/html" in dossier_response.headers["content-type"]
        
        html_content = dossier_response.text
        assert "<!DOCTYPE html>" in html_content
        assert "Pre-Authorization Dossier" in html_content
        assert analysis_id in html_content
        
        # Step 6: Get JSON dossier for programmatic access
        json_dossier_response = client.get(f"/api/dossier/{analysis_id}?format=json")
        assert json_dossier_response.status_code == 200
        json_dossier_data = json_dossier_response.json()
        
        assert "success" in json_dossier_data
        assert "dossier" in json_dossier_data
        
        # Validate complete workflow success
        print(f"✅ Complete UI workflow test passed:")
        print(f"   - Processing time: {upload_duration:.2f}s")
        print(f"   - Decision: {decision['outcome']}")
        print(f"   - Cost: ${total_cost:.4f}")
        print(f"   - Analysis ID: {analysis_id}")
    
    def test_dossier_viewer_functionality(self, client, sample_xml_file):
        """Test dossier viewer with different formats and content validation."""
        # Process a request to get an analysis ID
        xml_file = io.BytesIO(sample_xml_file.encode('utf-8'))
        
        process_response = client.post(
            "/api/process/unified",
            files={"file": ("dossier_test.xml", xml_file, "application/xml")},
            data={
                "patient_id": "DOSSIER_TEST",
                "xml_format": "eclaim",
                "include_dossier": True
            }
        )
        
        assert process_response.status_code == 200
        analysis_id = process_response.json()["analysis_id"]
        
        # Test HTML dossier viewer
        html_response = client.get(f"/api/dossier/{analysis_id}?format=html")
        assert html_response.status_code == 200
        
        html_content = html_response.text
        
        # Validate HTML structure for UI display
        assert "<html" in html_content
        assert "<head>" in html_content
        assert "<body>" in html_content
        assert "<title>" in html_content
        
        # Validate professional styling
        assert "css" in html_content.lower() or "style" in html_content.lower()
        assert "font-family" in html_content
        
        # Validate content sections
        assert "Pre-Authorization Dossier" in html_content
        assert "Analysis ID" in html_content
        assert "Patient ID" in html_content
        assert "Executive Summary" in html_content
        
        # Test JSON dossier for programmatic access
        json_response = client.get(f"/api/dossier/{analysis_id}?format=json")
        assert json_response.status_code == 200
        
        json_data = json_response.json()
        assert "dossier" in json_data
        
        dossier = json_data["dossier"]
        assert "content" in dossier
        assert "metadata" in dossier
        
        # Validate dossier content structure for UI rendering
        content = dossier["content"]
        assert "executive_summary" in content
        assert "sections" in content
        assert len(content["sections"]) >= 1
        
        for section in content["sections"]:
            assert "title" in section
            assert "content" in section
            assert len(section["title"]) > 0
            assert len(section["content"]) > 0
        
        # Test PDF capability
        pdf_response = client.get(f"/api/dossier/{analysis_id}?format=pdf")
        assert pdf_response.status_code == 200
        pdf_data = pdf_response.json()
        assert "PDF generation capability" in pdf_data["message"]
    
    def test_dashboard_updates_and_analytics(self, client, sample_xml_file):
        """Test dashboard real-time updates and analytics display."""
        # Get initial dashboard state
        initial_response = client.get("/api/dashboard/summary")
        assert initial_response.status_code == 200
        initial_data = initial_response.json()
        
        initial_runs = initial_data["processing_metrics"]["total_runs"]
        initial_cost = initial_data["processing_metrics"]["total_cost_usd"]
        
        # Process multiple requests to generate analytics data
        xml_file1 = io.BytesIO(sample_xml_file.encode('utf-8'))
        xml_file2 = io.BytesIO(sample_xml_file.encode('utf-8'))
        
        # First request
        response1 = client.post(
            "/api/process/unified",
            files={"file": ("analytics_test_1.xml", xml_file1, "application/xml")},
            data={"xml_format": "eclaim", "patient_id": "ANALYTICS_001"}
        )
        assert response1.status_code == 200
        
        # Second request
        response2 = client.post(
            "/api/process/unified",
            files={"file": ("analytics_test_2.xml", xml_file2, "application/xml")},
            data={"xml_format": "eclaim", "patient_id": "ANALYTICS_002"}
        )
        assert response2.status_code == 200
        
        # Get updated dashboard
        updated_response = client.get("/api/dashboard/summary")
        assert updated_response.status_code == 200
        updated_data = updated_response.json()
        
        # Validate dashboard updates
        assert "processing_metrics" in updated_data
        assert "decision_analytics" in updated_data
        assert "performance_insights" in updated_data
        assert "recent_activity" in updated_data
        
        # Validate metrics structure for UI display
        processing_metrics = updated_data["processing_metrics"]
        required_metrics = ["total_runs", "total_cost_usd", "average_cost_usd", "average_processing_time_seconds"]
        for metric in required_metrics:
            assert metric in processing_metrics
            assert isinstance(processing_metrics[metric], (int, float))
        
        # Validate decision analytics for charts
        decision_analytics = updated_data["decision_analytics"]
        assert "outcomes" in decision_analytics
        assert "outcome_percentages" in decision_analytics
        assert "approval_rate" in decision_analytics
        assert "denial_rate" in decision_analytics
        assert "review_rate" in decision_analytics
        
        # Validate performance insights for user guidance
        performance_insights = updated_data["performance_insights"]
        assert "cost_efficiency" in performance_insights
        assert "processing_speed" in performance_insights
        assert "system_reliability" in performance_insights
        
        # Validate recent activity for timeline display
        recent_activity = updated_data["recent_activity"]
        assert isinstance(recent_activity, list)
        
        if recent_activity:
            activity = recent_activity[0]
            assert "patient_id" in activity
            assert "decision" in activity
            assert "cost_usd" in activity
            assert "processing_time_seconds" in activity
    
    def test_error_states_and_user_feedback(self, client):
        """Test error handling and user feedback in UI workflows."""
        # Test invalid file upload
        invalid_file = io.BytesIO(b"This is not XML content")
        
        error_response = client.post(
            "/api/process/unified",
            files={"file": ("invalid.txt", invalid_file, "text/plain")},
            data={"xml_format": "eclaim"}
        )
        
        assert error_response.status_code == 400
        error_data = error_response.json()
        assert "detail" in error_data
        assert "file type" in error_data["detail"].lower()
        
        # Test invalid XML format
        xml_file = io.BytesIO(b"<invalid>XML content</invalid>")
        
        format_error_response = client.post(
            "/api/process/unified",
            files={"file": ("test.xml", xml_file, "application/xml")},
            data={"xml_format": "invalid_format"}
        )
        
        assert format_error_response.status_code == 400
        format_error_data = format_error_response.json()
        assert "detail" in format_error_data
        
        # Test file too large
        large_content = "<xml>" + "x" * (11 * 1024 * 1024) + "</xml>"
        large_file = io.BytesIO(large_content.encode('utf-8'))
        
        size_error_response = client.post(
            "/api/process/unified",
            files={"file": ("large.xml", large_file, "application/xml")},
            data={"xml_format": "eclaim"}
        )
        
        assert size_error_response.status_code == 413
        
        # Test nonexistent dossier
        dossier_error_response = client.get("/api/dossier/nonexistent-id")
        # Should return 200 with sample dossier (current implementation) or 404
        assert dossier_error_response.status_code in [200, 404]
        
        # Validate error responses have user-friendly messages
        assert isinstance(error_data["detail"], str)
        assert len(error_data["detail"]) > 5
    
    def test_loading_states_and_performance(self, client, sample_xml_file):
        """Test UI loading states and performance feedback."""
        xml_file = io.BytesIO(sample_xml_file.encode('utf-8'))
        
        start_time = time.time()
        
        response = client.post(
            "/api/process/unified",
            files={"file": ("performance_test.xml", xml_file, "application/xml")},
            data={
                "xml_format": "eclaim",
                "include_dossier": True,
                "processing_mode": "hybrid"
            }
        )
        
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response time is acceptable for UI
        assert response_time < 20, f"Response time {response_time:.2f}s too slow for good UX"
        
        # Validate timing data is available for progress indicators
        assert "performance" in data
        performance = data["performance"]
        assert "timings" in performance
        assert "phase_breakdown" in performance
        
        phase_breakdown = performance["phase_breakdown"]
        expected_phases = ["intake_ms", "clinical_summary_ms", "evidence_retrieval_ms", "policy_evaluation_ms", "decision_synthesis_ms"]
        
        for phase in expected_phases:
            assert phase in phase_breakdown
            assert phase_breakdown[phase] >= 0
        
        # Validate processing metadata for user feedback
        metadata = data["processing_metadata"]
        assert "start_time" in metadata
        assert "end_time" in metadata
        assert "total_duration_seconds" in metadata
        
        duration = metadata["total_duration_seconds"]
        assert duration > 0
        assert duration < 30  # Should complete in reasonable time
    
    def test_multi_format_support_ui(self, client):
        """Test UI support for multiple XML formats and display variations."""
        # Test eClaimLink format
        eclaim_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
    <Header>
        <SenderID>PROV12345</SenderID>
        <ReceiverID>PAYER67890</ReceiverID>
        <TransactionDateTime>31/07/2025 14:15</TransactionDateTime>
        <TransactionID>TXN-ECLAIM-001</TransactionID>
    </Header>
    <JustificationText>eClaimLink format test</JustificationText>
    <ServiceRequests>
        <ServiceRequest>
            <ct:ActivityCode>83036</ct:ActivityCode>
            <ct:DiagnosisCode>E11.9</ct:DiagnosisCode>
            <ct:ActivityDateTime>01/08/2025 09:00</ct:ActivityDateTime>
            <ct:ActivityInstructions>Test service</ct:ActivityInstructions>
            <RequestedAmount currency="AED">100.00</RequestedAmount>
        </ServiceRequest>
    </ServiceRequests>
</PriorAuthorizationRequest>'''
        
        # Test Shafafiya format
        shafafiya_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<Prior.Authorization xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <Header>
        <SenderID>PROV12345</SenderID>
        <ReceiverID>PAYER67890</ReceiverID>
        <TransactionDate>31/07/2025 14:15</TransactionDate>
        <RecordCount>1</RecordCount>
        <DispositionFlag>TEST</DispositionFlag>
    </Header>
    <Authorization>
        <Result>Pending</Result>
        <ID>PA-TEST-001</ID>
        <IDPayer>PAYER67890</IDPayer>
        <Start>31/07/2025 00:00</Start>
        <End>31/08/2025 23:59</End>
        <Limit>1000.00</Limit>
        <Comments>Shafafiya format test</Comments>
        <Activity>
            <ID>1</ID>
            <Type>3</Type>
            <Code>83036</Code>
            <Quantity>1</Quantity>
            <Net>100.00</Net>
            <PaymentAmount>80.00</PaymentAmount>
        </Activity>
    </Authorization>
</Prior.Authorization>'''
        
        # Test eClaimLink processing
        eclaim_file = io.BytesIO(eclaim_xml.encode('utf-8'))
        eclaim_response = client.post(
            "/api/process/unified",
            files={"file": ("eclaim_test.xml", eclaim_file, "application/xml")},
            data={"xml_format": "eclaim", "patient_id": "ECLAIM_UI_TEST"}
        )
        
        assert eclaim_response.status_code == 200
        eclaim_data = eclaim_response.json()
        assert eclaim_data["success"] is True
        assert eclaim_data["processing_metadata"]["xml_format"] == "eclaim"
        
        # Test Shafafiya processing
        shafafiya_file = io.BytesIO(shafafiya_xml.encode('utf-8'))
        shafafiya_response = client.post(
            "/api/process/unified",
            files={"file": ("shafafiya_test.xml", shafafiya_file, "application/xml")},
            data={"xml_format": "shafafiya", "patient_id": "SHAFAFIYA_UI_TEST"}
        )
        
        assert shafafiya_response.status_code == 200
        shafafiya_data = shafafiya_response.json()
        assert shafafiya_data["success"] is True
        assert shafafiya_data["processing_metadata"]["xml_format"] == "shafafiya"
        
        # Validate both formats produce similar UI-displayable results
        for data in [eclaim_data, shafafiya_data]:
            assert "results" in data
            assert "quality_metrics" in data
            assert "performance" in data
            
            results = data["results"]
            assert "decision" in results
            assert "clinical_summary" in results
    
    @pytest.mark.performance
    def test_ui_performance_under_concurrent_load(self, client, sample_xml_file):
        """Test UI performance with concurrent user requests."""
        import threading
        import time
        
        results = []
        errors = []
        
        def simulate_user_session():
            try:
                session_start = time.time()
                
                # User uploads file
                xml_file = io.BytesIO(sample_xml_file.encode('utf-8'))
                process_response = client.post(
                    "/api/process/unified",
                    files={"file": ("concurrent_test.xml", xml_file, "application/xml")},
                    data={"xml_format": "eclaim", "include_dossier": True}
                )
                
                if process_response.status_code != 200:
                    errors.append(f"Process failed: {process_response.status_code}")
                    return
                
                analysis_id = process_response.json()["analysis_id"]
                
                # User views dossier
                dossier_response = client.get(f"/api/dossier/{analysis_id}?format=html")
                
                # User checks dashboard
                dashboard_response = client.get("/api/dashboard/summary")
                
                session_duration = time.time() - session_start
                
                results.append({
                    "process_status": process_response.status_code,
                    "dossier_status": dossier_response.status_code,
                    "dashboard_status": dashboard_response.status_code,
                    "session_duration": session_duration,
                    "analysis_id": analysis_id
                })
                
            except Exception as e:
                errors.append(f"Session error: {str(e)}")
        
        # Simulate 4 concurrent user sessions
        threads = []
        for i in range(4):
            thread = threading.Thread(target=simulate_user_session)
            threads.append(thread)
            thread.start()
        
        # Wait for all sessions to complete
        for thread in threads:
            thread.join(timeout=60)
        
        # Validate concurrent performance
        assert len(errors) <= 1, f"Too many errors in concurrent sessions: {errors}"
        assert len(results) >= 3, f"Expected at least 3 successful sessions, got {len(results)}"
        
        # Validate session performance
        avg_duration = sum(r["session_duration"] for r in results) / len(results)
        max_duration = max(r["session_duration"] for r in results)
        
        assert avg_duration < 25, f"Average session duration {avg_duration:.2f}s > 25s"
        assert max_duration < 45, f"Max session duration {max_duration:.2f}s > 45s"
        
        # Validate all requests succeeded
        for result in results:
            assert result["process_status"] == 200
            assert result["dossier_status"] == 200
            assert result["dashboard_status"] == 200
            assert len(result["analysis_id"]) > 10  # Valid UUID format
