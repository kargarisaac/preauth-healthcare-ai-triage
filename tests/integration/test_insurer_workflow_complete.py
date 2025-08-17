"""
Complete Insurer Workflow Integration Tests

Validates the complete end-to-end workflow from XML submission
through pipeline processing to insurer dashboard decision workflow.
"""

import json
import pytest
import tempfile
import io
import time
import asyncio
from pathlib import Path
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from typing import Dict, Any, List

from api.main import app
from api.models import RequestStatus, RequestPriority, DecisionOutcome
from api.services.request_management_service import get_request_management_service


@pytest.mark.integration
class TestInsurerWorkflowComplete:
    """Complete end-to-end insurer workflow testing."""
    
    @pytest.fixture
    def client(self):
        """Create FastAPI test client."""
        return TestClient(app)
    
    @pytest.fixture
    def request_service(self):
        """Get request management service."""
        return get_request_management_service()
    
    @pytest.fixture
    def patient_007_xml(self):
        """Load Patient_007 demo XML file."""
        xml_path = Path("data/dataset_2/synthetic_dataset/UAE_XML/Patient_007_eclaim.xml")
        if xml_path.exists():
            return xml_path.read_text(encoding='utf-8')
        
        # Fallback to sample XML
        return '''<?xml version="1.0" encoding="UTF-8"?>
<PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
    <Header>
        <SenderID>PROV12345</SenderID>
        <ReceiverID>INSURER001</ReceiverID>
        <TransactionDateTime>17/08/2025 14:30</TransactionDateTime>
        <TransactionID>TXN-PATIENT007-001</TransactionID>
    </Header>
    <PatientDetails>
        <ct:PatientID>Patient_007</ct:PatientID>
        <ct:EmiratesID>784-1987-1234567-7</ct:EmiratesID>
        <ct:FullName>Ahmad Mohammad Ali</ct:FullName>
        <ct:DateOfBirth>15/06/1987</ct:DateOfBirth>
        <ct:Gender>M</ct:Gender>
    </PatientDetails>
    <JustificationText>Patient with type 1 diabetes requires continuous glucose monitoring system for optimal glycemic control.</JustificationText>
    <ServiceRequests>
        <ServiceRequest>
            <ct:ActivityCode>95250</ct:ActivityCode>
            <ct:DiagnosisCode>E10.9</ct:DiagnosisCode>
            <ct:ActivityDateTime>20/08/2025 09:00</ct:ActivityDateTime>
            <ct:ActivityInstructions>Continuous glucose monitoring device and sensor</ct:ActivityInstructions>
            <RequestedAmount currency="AED">2850.00</RequestedAmount>
        </ServiceRequest>
    </ServiceRequests>
</PriorAuthorizationRequest>'''
    
    def test_complete_workflow_xml_to_decision(self, client, patient_007_xml, request_service):
        """Test complete workflow: XML submission → processing → dashboard → decision."""
        
        # Step 1: Submit XML for processing
        xml_file = io.BytesIO(patient_007_xml.encode('utf-8'))
        
        upload_response = client.post(
            "/api/process/unified",
            files={"file": ("Patient_007_eclaim.xml", xml_file, "application/xml")},
            data={
                "patient_id": "Patient_007",
                "xml_format": "eclaim",
                "include_dossier": True,
                "processing_mode": "hybrid"
            }
        )
        
        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        assert upload_data["success"] is True
        
        # Validate request was created and stored
        request_id = upload_data.get("request_id")
        assert request_id is not None, "Request should be automatically created and stored"
        
        # Step 2: Verify request appears in insurer inbox
        inbox_response = client.get("/api/insurer/requests")
        assert inbox_response.status_code == 200
        
        inbox_data = inbox_response.json()
        assert inbox_data["success"] is True
        assert inbox_data["total_count"] >= 1
        
        # Find our request in inbox
        our_request = None
        for request in inbox_data["requests"]:
            if request["request_id"] == request_id:
                our_request = request
                break
        
        assert our_request is not None, f"Request {request_id} not found in inbox"
        assert our_request["status"] == "pending"
        assert our_request["patient_id"] == "Patient_007"
        
        # Step 3: Get detailed request view with patient history
        details_response = client.get(f"/api/insurer/requests/{request_id}")
        assert details_response.status_code == 200
        
        details_data = details_response.json()
        assert details_data["success"] is True
        assert "request" in details_data
        assert "patient_history" in details_data
        assert "timeline" in details_data
        
        request_details = details_data["request"]
        assert request_details["request_id"] == request_id
        assert request_details["xml_filename"] == "Patient_007_eclaim.xml"
        
        # Validate pipeline results are properly stored
        assert request_details["intake_data"] is not None
        assert request_details["clinical_summary"] is not None
        assert request_details["checklist_data"] is not None
        assert request_details["decision_data"] is not None
        
        # Step 4: Assign request to medical director
        assignment_response = client.put(
            f"/api/insurer/requests/{request_id}/assign",
            json={
                "assigned_to": "Dr. Sarah Al-Zahra",
                "priority": "high",
                "notes": "Diabetes technology request - review clinical necessity"
            }
        )
        
        assert assignment_response.status_code == 200
        assignment_data = assignment_response.json()
        assert assignment_data["success"] is True
        assert assignment_data["assigned_to"] == "Dr. Sarah Al-Zahra"
        
        # Step 5: Verify assignment updated request status
        updated_details_response = client.get(f"/api/insurer/requests/{request_id}")
        updated_details = updated_details_response.json()
        updated_request = updated_details["request"]
        
        assert updated_request["status"] == "under_review"
        assert updated_request["assigned_to"] == "Dr. Sarah Al-Zahra"
        assert updated_request["priority"] == "high"
        
        # Step 6: Submit medical director decision
        decision_response = client.post(
            f"/api/insurer/requests/{request_id}/decision",
            json={
                "decision": "approved",
                "rationale": "Patient meets clinical criteria for CGM. HbA1c >8% with frequent hypoglycemic episodes documented. Conservative management has been attempted and failed.",
                "conditions": [
                    "Coverage limited to 6 months with reassessment required",
                    "Patient must complete diabetes education program",
                    "Quarterly endocrinologist follow-up required"
                ],
                "requires_followup": True,
                "followup_date": (datetime.now() + timedelta(days=180)).isoformat(),
                "notes": "Approve with conditions. Monitor utilization and clinical outcomes."
            },
            params={"decided_by": "Dr. Sarah Al-Zahra"}
        )
        
        assert decision_response.status_code == 200
        decision_data = decision_response.json()
        assert decision_data["success"] is True
        assert decision_data["decision_outcome"] == "approved"
        assert decision_data["decided_by"] == "Dr. Sarah Al-Zahra"
        
        # Step 7: Verify decision updated request status
        final_details_response = client.get(f"/api/insurer/requests/{request_id}")
        final_details = final_details_response.json()
        final_request = final_details["request"]
        
        assert final_request["status"] == "decided"
        assert final_request["final_decision"] == "approved"
        assert final_request["decision_rationale"] is not None
        assert final_request["decided_by"] == "Dr. Sarah Al-Zahra"
        assert final_request["decided_at"] is not None
        
        # Step 8: Mark decision as communicated
        communication_response = client.post(
            f"/api/insurer/requests/{request_id}/communicate",
            params={"communication_method": "automated_email"}
        )
        
        assert communication_response.status_code == 200
        communication_data = communication_response.json()
        assert communication_data["success"] is True
        assert communication_data["status"] == "communicated"
        
        # Step 9: Verify final status
        completed_details_response = client.get(f"/api/insurer/requests/{request_id}")
        completed_details = completed_details_response.json()
        completed_request = completed_details["request"]
        
        assert completed_request["status"] == "communicated"
        assert completed_request["communicated_at"] is not None
        assert completed_request["communication_method"] == "automated_email"
        
        # Step 10: Validate patient history integration
        patient_history = completed_details["patient_history"]
        if patient_history:
            assert patient_history["total_requests"] >= 1
            assert patient_history["approved_count"] >= 1
            assert "Patient_007" == patient_history["patient_id"]
        
        timeline = completed_details["timeline"]
        assert len(timeline) >= 4  # At least: submitted, assigned, decided, communicated
        
        timeline_events = {event["type"] for event in timeline}
        expected_events = {"request_submitted", "request_assigned", "decision_made", "decision_communicated"}
        assert expected_events.issubset(timeline_events)
    
    def test_request_inbox_filtering_and_pagination(self, client):
        """Test request inbox filtering, sorting, and pagination functionality."""
        
        # Test basic inbox retrieval
        response = client.get("/api/insurer/requests")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "total_count" in data
        assert "requests" in data
        assert "summary" in data
        
        # Test filtering by status
        response = client.get("/api/insurer/requests?status=pending")
        assert response.status_code == 200
        
        data = response.json()
        pending_requests = data["requests"]
        for request in pending_requests:
            assert request["status"] == "pending"
        
        # Test filtering by priority
        response = client.get("/api/insurer/requests?priority=high")
        assert response.status_code == 200
        
        # Test pagination
        response = client.get("/api/insurer/requests?limit=5&offset=0")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["requests"]) <= 5
        
        # Test date filtering
        date_from = (datetime.now() - timedelta(days=7)).isoformat()
        response = client.get(f"/api/insurer/requests?date_from={date_from}")
        assert response.status_code == 200
        
        # Test invalid status filter
        response = client.get("/api/insurer/requests?status=invalid_status")
        assert response.status_code == 400
    
    def test_patient_history_and_timeline_accuracy(self, client, patient_007_xml):
        """Test patient history aggregation and timeline accuracy."""
        
        # Submit multiple requests for same patient to build history
        request_ids = []
        for i in range(3):
            xml_file = io.BytesIO(patient_007_xml.encode('utf-8'))
            
            response = client.post(
                "/api/process/unified",
                files={"file": (f"Patient_007_request_{i}.xml", xml_file, "application/xml")},
                data={
                    "patient_id": "Patient_007",
                    "xml_format": "eclaim",
                    "include_dossier": False,  # Speed up processing
                }
            )
            
            assert response.status_code == 200
            request_ids.append(response.json().get("request_id"))
        
        # Get patient history
        response = client.get("/api/insurer/patients/Patient_007/history")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["patient_id"] == "Patient_007"
        
        history = data["history"]
        assert history["total_requests"] >= 3
        assert len(history["recent_requests"]) >= 3
        
        # Validate timeline chronological order
        timeline = data["timeline"]
        assert len(timeline) >= 3
        
        # Timeline should be sorted by date (newest first)
        dates = [datetime.fromisoformat(event["date"].replace('Z', '+00:00')) for event in timeline]
        assert dates == sorted(dates, reverse=True), "Timeline not properly sorted"
        
        # Validate trends and risk assessment
        trends = data["trends"]
        assert "requests_last_30_days" in trends
        assert isinstance(trends["requests_last_30_days"], int)
        
        risk_assessment = data["risk_assessment"]
        assert "risk_level" in risk_assessment
        assert risk_assessment["risk_level"] in ["low", "medium", "high", "critical"]
    
    def test_dashboard_metrics_and_analytics(self, client):
        """Test insurer dashboard metrics and analytics endpoints."""
        
        # Test comprehensive dashboard metrics
        response = client.get("/api/insurer/dashboard/metrics")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "workflow_metrics" in data
        assert "technical_metrics" in data
        assert "kpis" in data
        assert "alerts" in data
        
        # Validate workflow metrics
        workflow_metrics = data["workflow_metrics"]
        assert "total_requests" in workflow_metrics
        assert "status_distribution" in workflow_metrics
        assert "priority_distribution" in workflow_metrics
        
        # Validate KPIs
        kpis = data["kpis"]
        assert "average_decision_time_hours" in kpis
        assert "sla_compliance_rate" in kpis
        assert "cost_per_request" in kpis
        assert "automation_rate" in kpis
        
        # Test general dashboard summary
        response = client.get("/api/dashboard/summary")
        assert response.status_code == 200
        
        summary_data = response.json()
        assert summary_data["success"] is True
        assert "processing_metrics" in summary_data
        assert "decision_analytics" in summary_data
        assert "performance_insights" in summary_data
    
    def test_performance_and_scalability(self, client, patient_007_xml):
        """Test system performance under load and scalability characteristics."""
        
        import concurrent.futures
        import time
        
        def submit_request(request_index):
            """Submit a single request and measure performance."""
            start_time = time.time()
            
            xml_file = io.BytesIO(patient_007_xml.encode('utf-8'))
            
            response = client.post(
                "/api/process/unified",
                files={"file": (f"perf_test_{request_index}.xml", xml_file, "application/xml")},
                data={
                    "patient_id": f"Patient_PERF_{request_index}",
                    "xml_format": "eclaim",
                    "include_dossier": False  # Faster processing
                }
            )
            
            duration = time.time() - start_time
            
            return {
                "status_code": response.status_code,
                "duration": duration,
                "success": response.status_code == 200,
                "request_id": response.json().get("request_id") if response.status_code == 200 else None
            }
        
        # Test concurrent processing
        num_concurrent = 5
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [executor.submit(submit_request, i) for i in range(num_concurrent)]
            results = [future.result(timeout=60) for future in concurrent.futures.as_completed(futures)]
        
        # Validate performance
        successful_results = [r for r in results if r["success"]]
        assert len(successful_results) >= 4, f"Only {len(successful_results)}/{num_concurrent} requests succeeded"
        
        avg_duration = sum(r["duration"] for r in successful_results) / len(successful_results)
        assert avg_duration < 10.0, f"Average processing time {avg_duration:.2f}s exceeds 10s threshold"
        
        # Test inbox performance with multiple requests
        start_time = time.time()
        inbox_response = client.get("/api/insurer/requests?limit=50")
        inbox_duration = time.time() - start_time
        
        assert inbox_response.status_code == 200
        assert inbox_duration < 2.0, f"Inbox loading took {inbox_duration:.2f}s > 2s"
        
        # Test dashboard metrics performance
        start_time = time.time()
        metrics_response = client.get("/api/insurer/dashboard/metrics")
        metrics_duration = time.time() - start_time
        
        assert metrics_response.status_code == 200
        assert metrics_duration < 3.0, f"Metrics calculation took {metrics_duration:.2f}s > 3s"
    
    def test_data_consistency_and_integrity(self, client, patient_007_xml, request_service):
        """Test data consistency across all workflow components."""
        
        # Submit request and track data through entire workflow
        xml_file = io.BytesIO(patient_007_xml.encode('utf-8'))
        
        upload_response = client.post(
            "/api/process/unified",
            files={"file": ("consistency_test.xml", xml_file, "application/xml")},
            data={
                "patient_id": "Patient_007",
                "xml_format": "eclaim",
                "include_dossier": True
            }
        )
        
        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        request_id = upload_data["request_id"]
        
        # Validate pipeline results stored correctly
        request_details_response = client.get(f"/api/insurer/requests/{request_id}")
        request_details = request_details_response.json()["request"]
        
        # Check pipeline data integrity
        intake_data = request_details["intake_data"]
        assert intake_data is not None
        assert intake_data["patient_id"] == "Patient_007"
        
        clinical_summary = request_details["clinical_summary"]
        assert clinical_summary is not None
        
        decision_data = request_details["decision_data"]
        assert decision_data is not None
        assert "outcome" in decision_data
        
        # Validate cost and timing data
        assert request_details["processing_time_seconds"] is not None
        assert request_details["cost_usd"] is not None
        assert request_details["processing_time_seconds"] > 0
        assert request_details["cost_usd"] >= 0
        
        # Make decision and verify data consistency
        client.post(
            f"/api/insurer/requests/{request_id}/decision",
            json={
                "decision": "approved",
                "rationale": "Data consistency test approval"
            }
        )
        
        # Verify decision persisted correctly
        updated_response = client.get(f"/api/insurer/requests/{request_id}")
        updated_request = updated_response.json()["request"]
        
        assert updated_request["final_decision"] == "approved"
        assert updated_request["decision_rationale"] == "Data consistency test approval"
        assert updated_request["status"] == "decided"
        
        # Verify patient history updated correctly
        history_response = client.get("/api/insurer/patients/Patient_007/history")
        if history_response.status_code == 200:
            history_data = history_response.json()
            history = history_data["history"]
            
            # Find our request in recent requests
            our_request_in_history = None
            for recent_req in history["recent_requests"]:
                if recent_req["request_id"] == request_id:
                    our_request_in_history = recent_req
                    break
            
            assert our_request_in_history is not None
            assert our_request_in_history["decision"] == "approved"


def validate_request_data_structure(request_data: Dict[str, Any]) -> bool:
    """Utility function to validate request data structure."""
    required_fields = [
        "request_id", "patient_id", "status", "priority", "created_at",
        "xml_filename", "xml_format", "intake_data", "clinical_summary",
        "decision_data", "processing_time_seconds", "cost_usd"
    ]
    
    return all(field in request_data for field in required_fields)


def validate_timeline_event_structure(event: Dict[str, Any]) -> bool:
    """Utility function to validate timeline event structure."""
    required_fields = ["date", "type", "title", "description"]
    return all(field in event for field in required_fields)