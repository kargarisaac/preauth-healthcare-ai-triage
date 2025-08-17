"""
Test Fixtures and Mock Data for Insurer Workflow Testing

Provides realistic test data, mock objects, and utility functions
for comprehensive insurer workflow testing.
"""

import pytest
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path


@pytest.fixture
def mock_insurer_users():
    """Mock insurer user profiles for testing."""
    return {
        "medical_director_1": {
            "user_id": "md_001",
            "name": "Dr. Sarah Al-Zahra",
            "role": "Senior Medical Director",
            "specialties": ["Internal Medicine", "Endocrinology"],
            "authorization_limits": {"max_amount_aed": 100000},
            "active": True,
            "email": "sarah.alzahra@insurer.ae"
        },
        "medical_director_2": {
            "user_id": "md_002", 
            "name": "Dr. Ahmad Hassan",
            "role": "Medical Director",
            "specialties": ["Orthopedics", "Sports Medicine"],
            "authorization_limits": {"max_amount_aed": 75000},
            "active": True,
            "email": "ahmad.hassan@insurer.ae"
        },
        "case_manager": {
            "user_id": "cm_001",
            "name": "Fatima Al-Mansoori",
            "role": "Senior Case Manager", 
            "specialties": ["Case Management"],
            "authorization_limits": {"max_amount_aed": 25000},
            "active": True,
            "email": "fatima.almansoori@insurer.ae"
        }
    }


@pytest.fixture
def sample_requests_dataset():
    """Generate sample requests for comprehensive testing."""
    base_date = datetime.now()
    
    return [
        {
            "request_id": "REQ-TEST-001",
            "patient_id": "Patient_007",
            "condition": "Diabetes Type 1",
            "procedure": "Continuous Glucose Monitor",
            "cost_aed": 2850,
            "urgency": "routine",
            "expected_decision": "approved",
            "submission_date": base_date - timedelta(days=2),
            "xml_filename": "Patient_007_eclaim.xml",
            "provider": {
                "name": "Dubai Healthcare City",
                "id": "PROV_001",
                "type": "Hospital"
            }
        },
        {
            "request_id": "REQ-TEST-002",
            "patient_id": "Patient_005", 
            "condition": "Osteoarthritis",
            "procedure": "Total Knee Replacement",
            "cost_aed": 45000,
            "urgency": "high",
            "expected_decision": "requires_review",
            "submission_date": base_date - timedelta(days=1),
            "xml_filename": "Patient_005_eclaim.xml",
            "provider": {
                "name": "Emirates Hospital",
                "id": "PROV_002",
                "type": "Specialty Clinic"
            }
        },
        {
            "request_id": "REQ-TEST-003",
            "patient_id": "Patient_011",
            "condition": "Acute Myocardial Infarction",
            "procedure": "Emergency Cardiac Catheterization",
            "cost_aed": 75000,
            "urgency": "emergency",
            "expected_decision": "approved",
            "submission_date": base_date - timedelta(hours=6),
            "xml_filename": "Patient_011_eclaim.xml",
            "provider": {
                "name": "Sheikh Khalifa Medical City",
                "id": "PROV_003",
                "type": "Emergency Hospital"
            }
        }
    ]


@pytest.fixture
def mock_patient_histories():
    """Mock patient history data for testing."""
    return {
        "Patient_007": {
            "patient_id": "Patient_007",
            "total_requests": 5,
            "first_request_date": datetime.now() - timedelta(days=365),
            "last_request_date": datetime.now() - timedelta(days=2),
            "approved_count": 4,
            "denied_count": 1,
            "pending_count": 0,
            "conditions": ["Diabetes Type 1", "Hypertension"],
            "procedures": ["HbA1c Test", "Continuous Glucose Monitor", "Insulin Pump"],
            "medications": ["Insulin", "Metformin"],
            "high_cost_requests": 2,
            "emergency_requests": 0,
            "recent_requests": [
                {
                    "request_id": "REQ-HIST-001",
                    "created_at": (datetime.now() - timedelta(days=2)).isoformat(),
                    "status": "pending",
                    "priority": "medium",
                    "xml_filename": "Patient_007_latest.xml"
                }
            ]
        },
        "Patient_005": {
            "patient_id": "Patient_005",
            "total_requests": 3,
            "first_request_date": datetime.now() - timedelta(days=180),
            "last_request_date": datetime.now() - timedelta(days=1),
            "approved_count": 1,
            "denied_count": 1,
            "pending_count": 1,
            "conditions": ["Osteoarthritis", "Chronic Pain"],
            "procedures": ["Physical Therapy", "Knee Replacement"],
            "medications": ["NSAIDs", "Pain Management"],
            "high_cost_requests": 1,
            "emergency_requests": 0,
            "recent_requests": [
                {
                    "request_id": "REQ-HIST-002",
                    "created_at": (datetime.now() - timedelta(days=1)).isoformat(),
                    "status": "under_review",
                    "priority": "high",
                    "xml_filename": "Patient_005_knee.xml"
                }
            ]
        }
    }


@pytest.fixture
def sample_xml_templates():
    """XML templates for different test scenarios."""
    return {
        "diabetes_cgm": '''<?xml version="1.0" encoding="UTF-8"?>
<PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
    <Header>
        <SenderID>PROV12345</SenderID>
        <ReceiverID>INSURER001</ReceiverID>
        <TransactionDateTime>{transaction_date}</TransactionDateTime>
        <TransactionID>{transaction_id}</TransactionID>
    </Header>
    <PatientDetails>
        <ct:PatientID>{patient_id}</ct:PatientID>
        <ct:EmiratesID>{emirates_id}</ct:EmiratesID>
        <ct:FullName>{patient_name}</ct:FullName>
        <ct:DateOfBirth>{date_of_birth}</ct:DateOfBirth>
        <ct:Gender>{gender}</ct:Gender>
    </PatientDetails>
    <JustificationText>Patient with type 1 diabetes requires continuous glucose monitoring system for optimal glycemic control. HbA1c consistently >8% despite intensive management.</JustificationText>
    <ServiceRequests>
        <ServiceRequest>
            <ct:ActivityCode>95250</ct:ActivityCode>
            <ct:DiagnosisCode>E10.9</ct:DiagnosisCode>
            <ct:ActivityDateTime>{service_date}</ct:ActivityDateTime>
            <ct:ActivityInstructions>Continuous glucose monitoring device and sensor</ct:ActivityInstructions>
            <RequestedAmount currency="AED">2850.00</RequestedAmount>
        </ServiceRequest>
    </ServiceRequests>
</PriorAuthorizationRequest>''',
        
        "knee_replacement": '''<?xml version="1.0" encoding="UTF-8"?>
<PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
    <Header>
        <SenderID>PROV23456</SenderID>
        <ReceiverID>INSURER001</ReceiverID>
        <TransactionDateTime>{transaction_date}</TransactionDateTime>
        <TransactionID>{transaction_id}</TransactionID>
    </Header>
    <PatientDetails>
        <ct:PatientID>{patient_id}</ct:PatientID>
        <ct:EmiratesID>{emirates_id}</ct:EmiratesID>
        <ct:FullName>{patient_name}</ct:FullName>
        <ct:DateOfBirth>{date_of_birth}</ct:DateOfBirth>
        <ct:Gender>{gender}</ct:Gender>
    </PatientDetails>
    <JustificationText>Patient with severe osteoarthritis requiring total knee replacement. Conservative treatment has failed including physical therapy and pain management.</JustificationText>
    <ServiceRequests>
        <ServiceRequest>
            <ct:ActivityCode>27447</ct:ActivityCode>
            <ct:DiagnosisCode>M17.1</ct:DiagnosisCode>
            <ct:ActivityDateTime>{service_date}</ct:ActivityDateTime>
            <ct:ActivityInstructions>Total knee arthroplasty with prosthetic implant</ct:ActivityInstructions>
            <RequestedAmount currency="AED">45000.00</RequestedAmount>
        </ServiceRequest>
    </ServiceRequests>
</PriorAuthorizationRequest>''',
        
        "emergency_cardiac": '''<?xml version="1.0" encoding="UTF-8"?>
<PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
    <Header>
        <SenderID>PROV34567</SenderID>
        <ReceiverID>INSURER001</ReceiverID>
        <TransactionDateTime>{transaction_date}</TransactionDateTime>
        <TransactionID>{transaction_id}</TransactionID>
    </Header>
    <PatientDetails>
        <ct:PatientID>{patient_id}</ct:PatientID>
        <ct:EmiratesID>{emirates_id}</ct:EmiratesID>
        <ct:FullName>{patient_name}</ct:FullName>
        <ct:DateOfBirth>{date_of_birth}</ct:DateOfBirth>
        <ct:Gender>{gender}</ct:Gender>
    </PatientDetails>
    <JustificationText>Emergency cardiac catheterization for acute ST-elevation myocardial infarction. Patient presenting with chest pain and ECG changes.</JustificationText>
    <ServiceRequests>
        <ServiceRequest>
            <ct:ActivityCode>93458</ct:ActivityCode>
            <ct:DiagnosisCode>I21.9</ct:DiagnosisCode>
            <ct:ActivityDateTime>{service_date}</ct:ActivityDateTime>
            <ct:ActivityInstructions>Emergency cardiac catheterization with possible PCI</ct:ActivityInstructions>
            <RequestedAmount currency="AED">75000.00</RequestedAmount>
        </ServiceRequest>
    </ServiceRequests>
</PriorAuthorizationRequest>'''
    }


@pytest.fixture
def mock_dashboard_metrics():
    """Mock dashboard metrics for testing."""
    return {
        "workflow_metrics": {
            "total_requests": 150,
            "status_distribution": {
                "pending": 25,
                "under_review": 15,
                "decided": 100,
                "communicated": 10
            },
            "priority_distribution": {
                "low": 50,
                "medium": 75,
                "high": 20,
                "urgent": 5
            },
            "recent_activity_count": 12,
            "performance_metrics": {
                "average_processing_time_seconds": 8.5,
                "total_cost_usd": 12.50,
                "approval_rate_percent": 78.5,
                "total_decided": 100,
                "pending_requests": 25
            }
        },
        "kpis": {
            "average_decision_time_hours": 18.5,
            "sla_compliance_rate": 94.2,
            "cost_per_request": 0.083,
            "automation_rate": 85.0
        },
        "alerts": {
            "overdue_requests": 3,
            "high_priority_pending": 2,
            "system_health": "healthy"
        }
    }


def create_test_xml(template_name: str, **kwargs) -> str:
    """Create test XML from template with provided parameters."""
    templates = {
        "diabetes_cgm": '''<?xml version="1.0" encoding="UTF-8"?>
<PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
    <Header>
        <SenderID>PROV12345</SenderID>
        <ReceiverID>INSURER001</ReceiverID>
        <TransactionDateTime>{transaction_date}</TransactionDateTime>
        <TransactionID>{transaction_id}</TransactionID>
    </Header>
    <PatientDetails>
        <ct:PatientID>{patient_id}</ct:PatientID>
        <ct:EmiratesID>{emirates_id}</ct:EmiratesID>
        <ct:FullName>{patient_name}</ct:FullName>
        <ct:DateOfBirth>{date_of_birth}</ct:DateOfBirth>
        <ct:Gender>{gender}</ct:Gender>
    </PatientDetails>
    <JustificationText>Patient with type 1 diabetes requires continuous glucose monitoring system for optimal glycemic control.</JustificationText>
    <ServiceRequests>
        <ServiceRequest>
            <ct:ActivityCode>95250</ct:ActivityCode>
            <ct:DiagnosisCode>E10.9</ct:DiagnosisCode>
            <ct:ActivityDateTime>{service_date}</ct:ActivityDateTime>
            <ct:ActivityInstructions>Continuous glucose monitoring device and sensor</ct:ActivityInstructions>
            <RequestedAmount currency="AED">2850.00</RequestedAmount>
        </ServiceRequest>
    </ServiceRequests>
</PriorAuthorizationRequest>'''
    }
    
    # Default values
    defaults = {
        "transaction_date": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "transaction_id": f"TXN-TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "patient_id": "Patient_TEST",
        "emirates_id": "784-1990-1234567-9",
        "patient_name": "Test Patient Name",
        "date_of_birth": "01/01/1990",
        "gender": "M",
        "service_date": (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y %H:%M")
    }
    
    # Merge defaults with provided kwargs
    params = {**defaults, **kwargs}
    
    if template_name not in templates:
        raise ValueError(f"Unknown template: {template_name}")
    
    return templates[template_name].format(**params)


def validate_request_data_structure(request_data: Dict[str, Any]) -> bool:
    """Utility function to validate request data structure."""
    required_fields = [
        "request_id", "patient_id", "status", "priority", "created_at",
        "xml_filename", "xml_format", "intake_data", "clinical_summary",
        "decision_data", "processing_time_seconds", "cost_usd"
    ]
    
    missing_fields = [field for field in required_fields if field not in request_data]
    if missing_fields:
        print(f"Missing required fields: {missing_fields}")
        return False
    
    return True


def validate_timeline_event_structure(event: Dict[str, Any]) -> bool:
    """Utility function to validate timeline event structure."""
    required_fields = ["date", "type", "title", "description"]
    missing_fields = [field for field in required_fields if field not in event]
    
    if missing_fields:
        print(f"Missing timeline event fields: {missing_fields}")
        return False
    
    return True


def validate_patient_history_structure(history: Dict[str, Any]) -> bool:
    """Utility function to validate patient history structure."""
    required_fields = [
        "patient_id", "total_requests", "first_request_date", "last_request_date",
        "approved_count", "denied_count", "pending_count", "recent_requests"
    ]
    
    missing_fields = [field for field in required_fields if field not in history]
    if missing_fields:
        print(f"Missing patient history fields: {missing_fields}")
        return False
    
    return True


def assert_performance_metrics(metrics: Dict[str, Any], thresholds: Dict[str, float]):
    """Assert performance metrics meet specified thresholds."""
    for metric, threshold in thresholds.items():
        actual_value = metrics.get(metric)
        if actual_value is None:
            raise AssertionError(f"Performance metric '{metric}' not found in results")
        
        if actual_value > threshold:
            raise AssertionError(f"Performance metric '{metric}' value {actual_value} exceeds threshold {threshold}")


def load_demo_xml_file(filename: str) -> Optional[str]:
    """Load demo XML file if it exists."""
    xml_path = Path(f"data/dataset_2/synthetic_dataset/UAE_XML/{filename}")
    if xml_path.exists():
        return xml_path.read_text(encoding='utf-8')
    return None


def create_mock_pipeline_result(patient_id: str, decision_outcome: str = "APPROVE") -> Dict[str, Any]:
    """Create mock pipeline result for testing."""
    return {
        "intake": {
            "patient_id": patient_id,
            "transaction_id": f"TXN-MOCK-{patient_id}",
            "diagnoses": [
                {"code": "E10.9", "description": "Type 1 diabetes"}
            ],
            "procedures": [
                {"code": "95250", "description": "Continuous glucose monitoring"}
            ]
        },
        "clinical_summary": {
            "summary": f"Mock clinical summary for {patient_id}",
            "primary_condition": "Type 1 diabetes",
            "severity": "moderate"
        },
        "evidence": [
            {
                "source": "clinical_guidelines",
                "content": "Mock evidence content",
                "relevance_score": 0.85
            }
        ],
        "checklist": {
            "overall_compliance_score": 0.82,
            "criteria": [
                {
                    "criterion": "Medical necessity",
                    "status": "met",
                    "rationale": "Mock rationale"
                }
            ]
        },
        "decision": {
            "outcome": decision_outcome,
            "confidence": 0.85,
            "rationale": f"Mock decision rationale for {patient_id}"
        },
        "dossier": {
            "content": f"Mock dossier content for {patient_id}",
            "sections": ["summary", "evidence", "decision"]
        },
        "timings": {
            "total_ms": 8500,
            "intake_ms": 1000,
            "summary_ms": 2000,
            "evidence_ms": 2500,
            "checklist_ms": 2000,
            "decision_ms": 1000
        },
        "cost": {
            "total_cost_usd": 0.085,
            "phases": {
                "intake": 0.01,
                "summary": 0.025,
                "evidence": 0.03,
                "checklist": 0.015,
                "decision": 0.005
            }
        },
        "audit_trail": {
            "pipeline_execution": "deterministic",
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0"
        }
    }


def generate_test_timeline_events(request_id: str, patient_id: str) -> List[Dict[str, Any]]:
    """Generate test timeline events for a request."""
    base_time = datetime.now()
    
    return [
        {
            "date": (base_time - timedelta(hours=2)).isoformat(),
            "type": "request_submitted",
            "title": f"Request {request_id} Submitted",
            "description": "Pre-authorization request submitted by provider",
            "request_id": request_id
        },
        {
            "date": (base_time - timedelta(hours=1)).isoformat(),
            "type": "request_assigned", 
            "title": "Request Assigned",
            "description": "Assigned to Dr. Test Reviewer",
            "request_id": request_id,
            "assigned_to": "Dr. Test Reviewer"
        },
        {
            "date": (base_time - timedelta(minutes=30)).isoformat(),
            "type": "decision_made",
            "title": "Decision: Approved",
            "description": "Request approved with conditions",
            "request_id": request_id,
            "decision": "approved",
            "decided_by": "Dr. Test Reviewer"
        },
        {
            "date": (base_time - timedelta(minutes=10)).isoformat(),
            "type": "decision_communicated",
            "title": "Decision Communicated",
            "description": "Decision communicated via automated email",
            "request_id": request_id
        }
    ]