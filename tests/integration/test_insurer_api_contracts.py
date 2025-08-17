"""
API Contract Testing for Insurer Workflow

Validates API contracts, response formats, and data consistency
across all insurer-specific endpoints.
"""

import pytest
import io
from fastapi.testclient import TestClient
from pydantic import ValidationError

from api.main import app


@pytest.mark.integration
class TestInsurerAPIContracts:
    """Test API contracts for insurer workflow endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create FastAPI test client."""
        return TestClient(app)
    
    def test_request_inbox_response_contract(self, client):
        """Validate request inbox API response contract."""
        response = client.get("/api/insurer/requests")
        assert response.status_code == 200
        
        data = response.json()
        
        # Validate top-level structure
        required_fields = ["success", "total_count", "requests", "filters_applied", "summary"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        assert isinstance(data["success"], bool)
        assert isinstance(data["total_count"], int)
        assert isinstance(data["requests"], list)
        
        # Validate request object structure
        if data["requests"]:
            request = data["requests"][0]
            request_required_fields = [
                "request_id", "patient_id", "status", "priority", "created_at",
                "xml_filename", "xml_format", "processing_time_seconds", "cost_usd"
            ]
            
            for field in request_required_fields:
                assert field in request, f"Missing request field: {field}"
        
        # Validate summary structure
        summary = data["summary"]
        summary_fields = ["total_requests", "status_breakdown", "priority_breakdown"]
        for field in summary_fields:
            assert field in summary, f"Missing summary field: {field}"
    
    def test_request_details_response_contract(self, client):
        """Validate request details API response contract."""
        # First create a request to get details for
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <PriorAuthorizationRequest>
            <Header><TransactionID>TEST001</TransactionID></Header>
            <JustificationText>Test request</JustificationText>
        </PriorAuthorizationRequest>"""
        
        xml_file = io.BytesIO(xml_content.encode('utf-8'))
        upload_response = client.post(
            "/api/process/unified",
            files={"file": ("test.xml", xml_file, "application/xml")},
            data={"xml_format": "eclaim"}
        )
        
        if upload_response.status_code == 200:
            request_id = upload_response.json().get("request_id")
            
            if request_id:
                response = client.get(f"/api/insurer/requests/{request_id}")
                assert response.status_code == 200
                
                data = response.json()
                required_fields = ["success", "request", "patient_history", "timeline", "metadata"]
                
                for field in required_fields:
                    assert field in data, f"Missing field: {field}"
                
                # Validate request object contains pipeline results
                request_obj = data["request"]
                pipeline_fields = ["intake_data", "clinical_summary", "checklist_data", "decision_data"]
                
                for field in pipeline_fields:
                    assert field in request_obj, f"Missing pipeline field: {field}"
    
    def test_decision_submission_contract(self, client):
        """Validate decision submission API contract."""
        # Test with invalid decision data
        response = client.post(
            "/api/insurer/requests/FAKE_REQUEST/decision",
            json={
                "decision": "invalid_decision",
                "rationale": ""
            }
        )
        
        # Should return validation error
        assert response.status_code in [400, 404, 422]
        
        # Test with valid structure but non-existent request
        response = client.post(
            "/api/insurer/requests/FAKE_REQUEST/decision",
            json={
                "decision": "approved",
                "rationale": "Valid rationale for testing",
                "conditions": ["Test condition"],
                "requires_followup": False
            }
        )
        
        assert response.status_code == 404  # Request not found
        
        error_data = response.json()
        assert "detail" in error_data
    
    def test_patient_history_response_contract(self, client):
        """Validate patient history API response contract."""
        response = client.get("/api/insurer/patients/Patient_007/history")
        
        # Should return 200 with data or 404 if patient not found
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ["success", "patient_id", "history", "timeline", "trends", "risk_assessment"]
            
            for field in required_fields:
                assert field in data, f"Missing field: {field}"
            
            # Validate history structure
            history = data["history"]
            history_fields = [
                "patient_id", "total_requests", "first_request_date", "last_request_date",
                "approved_count", "denied_count", "pending_count", "recent_requests"
            ]
            
            for field in history_fields:
                assert field in history, f"Missing history field: {field}"
            
            # Validate timeline structure
            timeline = data["timeline"]
            assert isinstance(timeline, list)
            
            if timeline:
                event = timeline[0]
                event_fields = ["date", "type", "title", "description"]
                
                for field in event_fields:
                    assert field in event, f"Missing timeline event field: {field}"
    
    def test_assignment_endpoint_contract(self, client):
        """Test request assignment endpoint contract."""
        # Test with invalid assignment data
        response = client.put(
            "/api/insurer/requests/FAKE_REQUEST/assign",
            json={
                "assigned_to": "",  # Empty assignee
                "priority": "invalid_priority"
            }
        )
        
        assert response.status_code in [400, 404, 422]
        
        # Test with valid structure but non-existent request
        response = client.put(
            "/api/insurer/requests/FAKE_REQUEST/assign",
            json={
                "assigned_to": "Dr. Test Reviewer",
                "priority": "high",
                "notes": "Test assignment"
            }
        )
        
        assert response.status_code == 404  # Request not found
    
    def test_communication_endpoint_contract(self, client):
        """Test communication marking endpoint contract."""
        response = client.post(
            "/api/insurer/requests/FAKE_REQUEST/communicate",
            params={"communication_method": "email"}
        )
        
        assert response.status_code == 404  # Request not found
        
        # Test with empty communication method
        response = client.post(
            "/api/insurer/requests/FAKE_REQUEST/communicate",
            params={"communication_method": ""}
        )
        
        assert response.status_code == 404  # Still request not found
    
    def test_dashboard_metrics_contract(self, client):
        """Test dashboard metrics endpoint contract."""
        response = client.get("/api/insurer/dashboard/metrics")
        assert response.status_code == 200
        
        data = response.json()
        required_fields = ["success", "timestamp", "workflow_metrics", "technical_metrics", "kpis", "alerts"]
        
        for field in required_fields:
            assert field in data, f"Missing dashboard metrics field: {field}"
        
        # Validate workflow metrics structure
        workflow_metrics = data["workflow_metrics"]
        workflow_fields = ["total_requests", "status_distribution", "priority_distribution"]
        
        for field in workflow_fields:
            assert field in workflow_metrics, f"Missing workflow metrics field: {field}"
        
        # Validate KPIs structure
        kpis = data["kpis"]
        kpi_fields = ["average_decision_time_hours", "sla_compliance_rate", "cost_per_request", "automation_rate"]
        
        for field in kpi_fields:
            assert field in kpis, f"Missing KPI field: {field}"
    
    def test_error_response_consistency(self, client):
        """Test that error responses follow consistent format."""
        # Test various error endpoints
        error_endpoints = [
            ("/api/insurer/requests/INVALID_ID", 404),
            ("/api/insurer/patients/INVALID_PATIENT/history", 404),
        ]
        
        for endpoint, expected_status in error_endpoints:
            response = client.get(endpoint)
            assert response.status_code == expected_status
            
            if response.status_code >= 400:
                data = response.json()
                # FastAPI error responses should have 'detail' field
                assert "detail" in data, f"Error response missing 'detail' field for {endpoint}"
    
    def test_request_filtering_parameters(self, client):
        """Test request filtering parameter validation."""
        # Test valid filters
        valid_filters = [
            "?status=pending",
            "?priority=high", 
            "?limit=10&offset=0",
            "?assigned_to=Dr.%20Test",
            "?patient_id=Patient_007"
        ]
        
        for filter_param in valid_filters:
            response = client.get(f"/api/insurer/requests{filter_param}")
            assert response.status_code == 200, f"Valid filter failed: {filter_param}"
        
        # Test invalid filters
        invalid_filters = [
            "?status=invalid_status",
            "?priority=invalid_priority",
            "?limit=-1",
            "?offset=-5"
        ]
        
        for filter_param in invalid_filters:
            response = client.get(f"/api/insurer/requests{filter_param}")
            assert response.status_code in [400, 422], f"Invalid filter should fail: {filter_param}"
    
    def test_date_format_validation(self, client):
        """Test date format validation across endpoints."""
        # Test valid ISO date formats
        valid_dates = [
            "2025-08-17T10:30:00Z",
            "2025-08-17T10:30:00+00:00",
            "2025-08-17T10:30:00"
        ]
        
        for date_str in valid_dates:
            response = client.get(f"/api/insurer/requests?date_from={date_str}")
            # Should not fail due to date format (may return 200 or other valid response)
            assert response.status_code != 422, f"Valid date format failed: {date_str}"
        
        # Test invalid date formats
        invalid_dates = [
            "2025-13-50",  # Invalid month/day
            "not-a-date",
            "2025/08/17"   # Wrong format
        ]
        
        for date_str in invalid_dates:
            response = client.get(f"/api/insurer/requests?date_from={date_str}")
            assert response.status_code == 400, f"Invalid date format should fail: {date_str}"
    
    def test_response_content_type_headers(self, client):
        """Test that responses have correct content-type headers."""
        # JSON endpoints
        json_endpoints = [
            "/api/insurer/requests",
            "/api/insurer/dashboard/metrics",
            "/api/dashboard/summary"
        ]
        
        for endpoint in json_endpoints:
            response = client.get(endpoint)
            if response.status_code == 200:
                assert "application/json" in response.headers.get("content-type", "")
        
        # HTML endpoint (dossier)
        response = client.get("/api/dossier/test-123?format=html")
        if response.status_code == 200:
            assert "text/html" in response.headers.get("content-type", "")
    
    def test_pagination_metadata(self, client):
        """Test pagination metadata in list endpoints."""
        response = client.get("/api/insurer/requests?limit=5&offset=0")
        assert response.status_code == 200
        
        data = response.json()
        
        # Should have pagination-related fields
        assert "total_count" in data
        assert "requests" in data
        assert isinstance(data["total_count"], int)
        assert isinstance(data["requests"], list)
        
        # Validate filters_applied contains pagination info
        filters_applied = data["filters_applied"]
        assert "limit" in filters_applied
        assert "offset" in filters_applied
        assert filters_applied["limit"] == 5
        assert filters_applied["offset"] == 0