"""
Integration test configuration and fixtures.

Provides test-specific configuration and shared fixtures
for integration testing scenarios.
"""

import pytest
from pathlib import Path


@pytest.fixture(scope="session")
def integration_test_config():
    """Configuration for integration tests with relaxed timing."""
    return {
        "max_pipeline_time_s": 120,  # 2 minutes for full pipeline
        "max_api_response_time_s": 180,  # 3 minutes for API responses
        "max_cost_per_request": 1.0,  # $1 maximum for testing
        "demo_xml_base_path": Path("data/dataset_2/synthetic_dataset/UAE_XML"),
        "test_patient_ids": ["patient_007", "patient_005", "patient_011"],
        "skip_if_no_demo_data": True
    }


@pytest.fixture
def demo_xml_paths(integration_test_config):
    """Provide paths to demo patient XML files for testing."""
    base_path = integration_test_config["demo_xml_base_path"]
    
    paths = {}
    for patient_id in integration_test_config["test_patient_ids"]:
        xml_path = base_path / f"Patient_{patient_id.split('_')[-1]}_eclaim.xml"
        if xml_path.exists():
            paths[patient_id] = xml_path
    
    return paths


@pytest.fixture
def skip_if_no_demo_files(demo_xml_paths, integration_test_config):
    """Skip test if no demo files are available."""
    if integration_test_config["skip_if_no_demo_data"] and not demo_xml_paths:
        pytest.skip("No demo XML files available for integration testing")


@pytest.fixture
def sample_clinical_xml():
    """Sample XML content for testing."""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
    <Header>
        <SenderID>INTEGRATION_TEST</SenderID>
        <ReceiverID>PAYER67890</ReceiverID>
        <TransactionDateTime>31/07/2025 14:15</TransactionDateTime>
        <TransactionID>TXN-INTEGRATION-001</TransactionID>
    </Header>
    <JustificationText>Integration test case: Patient with Type 2 diabetes mellitus requiring glycemic control monitoring. Current HbA1c elevated at 8.5%. Patient on metformin therapy with suboptimal response. Requires comprehensive lab workup including HbA1c and lipid panel for cardiovascular risk stratification.</JustificationText>
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
            <ct:ActivityInstructions>Comprehensive metabolic panel</ct:ActivityInstructions>
            <RequestedAmount currency="AED">89.75</RequestedAmount>
        </ServiceRequest>
    </ServiceRequests>
</PriorAuthorizationRequest>'''


def pytest_collection_modifyitems(config, items):
    """Mark integration tests and add timeout."""
    for item in items:
        # Add integration marker
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
            
        # Add timeout for integration tests
        if any(marker.name == "integration" for marker in item.iter_markers()):
            item.add_marker(pytest.mark.timeout(300))  # 5 minute timeout per test