"""
Test configuration and shared fixtures for XML ingestion tests.

This module provides shared pytest fixtures and configuration for testing
the XML ingestion pipeline, including mock objects, test data factories,
and common test utilities.
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, patch

import pytest
import xmlschema


# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "test_data"


@pytest.fixture(scope="session", autouse=True)
def setup_test_logging():
    """Configure logging for tests to reduce noise."""
    # Reduce log level for test runs
    logging.getLogger("pipelines").setLevel(logging.WARNING)
    logging.getLogger("xmlschema").setLevel(logging.ERROR)


@pytest.fixture
def temp_xml_file():
    """
    Fixture that provides a temporary XML file that gets cleaned up.

    Returns:
        Generator that yields a function to create temp XML files
    """
    temp_files = []

    def create_temp_xml(content: str, filename: str = "test.xml") -> str:
        """Create a temporary XML file with given content."""
        temp_file = tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".xml",
            prefix=filename.replace(".xml", "_"),
            delete=False,
            encoding="utf-8",
        )
        temp_file.write(content)
        temp_file.close()
        temp_files.append(temp_file.name)
        return temp_file.name

    yield create_temp_xml

    # Cleanup
    for temp_file in temp_files:
        try:
            os.unlink(temp_file)
        except (OSError, FileNotFoundError):
            pass


@pytest.fixture
def temp_csv_file():
    """
    Fixture that provides a temporary CSV file that gets cleaned up.

    Returns:
        Generator that yields a function to create temp CSV files
    """
    temp_files = []

    def create_temp_csv(content: str, filename: str = "test.csv") -> str:
        """Create a temporary CSV file with given content."""
        temp_file = tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".csv",
            prefix=filename.replace(".csv", "_"),
            delete=False,
            encoding="utf-8",
        )
        temp_file.write(content)
        temp_file.close()
        temp_files.append(temp_file.name)
        return temp_file.name

    yield create_temp_csv

    # Cleanup
    for temp_file in temp_files:
        try:
            os.unlink(temp_file)
        except (OSError, FileNotFoundError):
            pass


@pytest.fixture
def mock_logger():
    """Fixture providing a mock logger for testing."""
    return Mock(spec=logging.Logger)


@pytest.fixture
def mock_schema_validator():
    """
    Fixture providing a mock XSD schema validator.

    Returns:
        Mock object configured to simulate schema validation
    """
    with patch("xmlschema.XMLSchema11") as mock_schema_class:
        mock_schema = Mock(spec=xmlschema.XMLSchema11)
        mock_schema.is_valid.return_value = True
        mock_schema.iter_errors.return_value = []
        mock_schema_class.return_value = mock_schema
        yield mock_schema


@pytest.fixture
def failing_schema_validator():
    """
    Fixture providing a mock schema validator that always fails.

    Returns:
        Mock object configured to simulate schema validation failures
    """
    with patch("xmlschema.XMLSchema11") as mock_schema_class:
        mock_schema = Mock(spec=xmlschema.XMLSchema11)
        mock_schema.is_valid.return_value = False

        # Create mock validation errors
        mock_error1 = Mock()
        mock_error1.path = "/Header/SenderID"
        mock_error1.reason = "Missing required element"

        mock_error2 = Mock()
        mock_error2.path = "/ServiceRequest[1]"
        mock_error2.reason = "Invalid data type"

        mock_schema.iter_errors.return_value = [mock_error1, mock_error2]
        mock_schema_class.return_value = mock_schema
        yield mock_schema


@pytest.fixture
def test_data_factory():
    """
    Fixture providing a factory for creating test data structures.

    Returns:
        TestDataFactory instance for generating various test data
    """

    class TestDataFactory:
        """Factory for creating standardized test data."""

        def create_eclaim_header(self, **overrides) -> Dict[str, Any]:
            """Create eClaimLink header data with optional overrides."""
            header = {
                "SenderID": "PROV12345",
                "ReceiverID": "PAYER67890",
                "TransactionDateTime": "27/07/2025 10:32",
                "TransactionID": "TXN-2025-000456",
            }
            header.update(overrides)
            return header

        def create_shafafiya_header(self, **overrides) -> Dict[str, Any]:
            """Create Shafafiya header data with optional overrides."""
            header = {
                "SenderID": "PROV12345",
                "ReceiverID": "PAYER67890",
                "TransactionDate": "27/07/2025 10:32",
                "RecordCount": "2",
                "DispositionFlag": "TEST",
            }
            header.update(overrides)
            return header

        def create_service_request(
            self, sequence_id: int = 1, **overrides
        ) -> Dict[str, Any]:
            """Create eClaimLink service request data with optional overrides."""
            service = {
                "ct:ActivityCode": f"8303{sequence_id}",
                "ct:DiagnosisCode": f"E11.{sequence_id}",
                "ct:ActivityDateTime": "28/07/2025 09:00",
                "ct:ActivityInstructions": f"Service {sequence_id} instructions",
                "RequestedAmount": {
                    "@currency": "AED",
                    "#text": f"{120 + sequence_id * 10}.00",
                },
            }
            service.update(overrides)
            return service

        def create_activity(
            self, activity_id: str = "1", **overrides
        ) -> Dict[str, Any]:
            """Create Shafafiya activity data with optional overrides."""
            activity = {
                "ID": activity_id,
                "Type": "3",
                "Code": f"8303{activity_id}",
                "Quantity": "1",
                "Net": f"{120 + int(activity_id) * 10}.00",
                "PaymentAmount": f"{90 + int(activity_id) * 10}.00",
            }
            activity.update(overrides)
            return activity

        def create_observation(
            self, obs_type: str = "ICD10", **overrides
        ) -> Dict[str, Any]:
            """Create observation data with optional overrides."""
            observation = {
                "Type": obs_type,
                "Code": "E11.9",
                "Value": "Type 2 diabetes mellitus without complications",
                "ValueType": "text",
            }
            observation.update(overrides)
            return observation

        def create_eclaim_xml(
            self,
            header_overrides: Dict[str, Any] = None,
            services: list = None,
            justification: str = None,
        ) -> str:
            """Create complete eClaimLink XML with customizable parts."""
            header = self.create_eclaim_header(**(header_overrides or {}))

            if services is None:
                services = [
                    self.create_service_request(1),
                    self.create_service_request(2),
                ]

            if justification is None:
                justification = "Patient requires medical attention."

            service_xml = ""
            for service in services:
                amount_attr = ""
                amount_text = ""
                if isinstance(service.get("RequestedAmount"), dict):
                    amount_attr = f'currency="{service["RequestedAmount"].get("@currency", "AED")}"'
                    amount_text = service["RequestedAmount"].get("#text", "0.00")
                else:
                    amount_text = str(service.get("RequestedAmount", "0.00"))

                service_xml += f"""
        <ServiceRequest>
            <ct:ActivityCode>{service.get("ct:ActivityCode", "83036")}</ct:ActivityCode>
            <ct:DiagnosisCode>{service.get("ct:DiagnosisCode", "E11.9")}</ct:DiagnosisCode>
            <ct:ActivityDateTime>{service.get("ct:ActivityDateTime", "28/07/2025 09:00")}</ct:ActivityDateTime>
            <ct:ActivityInstructions>{service.get("ct:ActivityInstructions", "Instructions")}</ct:ActivityInstructions>
            <RequestedAmount {amount_attr}>{amount_text}</RequestedAmount>
        </ServiceRequest>"""

            return f"""<?xml version="1.0" encoding="UTF-8"?>
<PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
    <Header>
        <SenderID>{header["SenderID"]}</SenderID>
        <ReceiverID>{header["ReceiverID"]}</ReceiverID>
        <TransactionDateTime>{header["TransactionDateTime"]}</TransactionDateTime>
        <TransactionID>{header["TransactionID"]}</TransactionID>
    </Header>
    <JustificationText>{justification}</JustificationText>
    <ServiceRequests>{service_xml}
    </ServiceRequests>
</PriorAuthorizationRequest>"""

        def create_shafafiya_xml(
            self,
            header_overrides: Dict[str, Any] = None,
            auth_overrides: Dict[str, Any] = None,
            activities: list = None,
        ) -> str:
            """Create complete Shafafiya XML with customizable parts."""
            header = self.create_shafafiya_header(**(header_overrides or {}))

            auth_defaults = {
                "Result": "Yes",
                "ID": "PA-2025-000123",
                "IDPayer": "PAYER67890",
                "Start": "25/07/2025 00:00",
                "End": "25/08/2025 23:59",
                "Limit": "1000.00",
                "Comments": "Authorization approved for treatment.",
            }
            auth_defaults.update(auth_overrides or {})

            if activities is None:
                activities = [self.create_activity("1"), self.create_activity("2")]

            activity_xml = ""
            for activity in activities:
                obs_xml = ""
                if "observations" in activity:
                    for obs in activity["observations"]:
                        obs_xml += f"""
            <Observation>
                <Type>{obs.get("Type", "ICD10")}</Type>
                <Code>{obs.get("Code", "E11.9")}</Code>
                <Value>{obs.get("Value", "Description")}</Value>
                <ValueType>{obs.get("ValueType", "text")}</ValueType>
            </Observation>"""

                activity_xml += f"""
        <Activity>
            <ID>{activity.get("ID", "1")}</ID>
            <Type>{activity.get("Type", "3")}</Type>
            <Code>{activity.get("Code", "83036")}</Code>
            <Quantity>{activity.get("Quantity", "1")}</Quantity>
            <Net>{activity.get("Net", "120.00")}</Net>
            <PaymentAmount>{activity.get("PaymentAmount", "90.00")}</PaymentAmount>{obs_xml}
        </Activity>"""

            return f"""<?xml version="1.0" encoding="UTF-8"?>
<Prior.Authorization xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <Header>
        <SenderID>{header["SenderID"]}</SenderID>
        <ReceiverID>{header["ReceiverID"]}</ReceiverID>
        <TransactionDate>{header["TransactionDate"]}</TransactionDate>
        <RecordCount>{header["RecordCount"]}</RecordCount>
        <DispositionFlag>{header["DispositionFlag"]}</DispositionFlag>
    </Header>
    <Authorization>
        <Result>{auth_defaults["Result"]}</Result>
        <ID>{auth_defaults["ID"]}</ID>
        <IDPayer>{auth_defaults["IDPayer"]}</IDPayer>
        <Start>{auth_defaults["Start"]}</Start>
        <End>{auth_defaults["End"]}</End>
        <Limit>{auth_defaults["Limit"]}</Limit>
        <Comments>{auth_defaults["Comments"]}</Comments>{activity_xml}
    </Authorization>
</Prior.Authorization>"""

    return TestDataFactory()


@pytest.fixture
def csv_test_data_factory():
    """
    Fixture providing a factory for creating CSV test data structures.

    Returns:
        CSVTestDataFactory instance for generating various CSV test data
    """

    class CSVTestDataFactory:
        """Factory for creating standardized CSV test data."""

        def create_basic_claims_csv(self, record_count: int = 3) -> str:
            """Create basic claims CSV with specified record count."""
            header = "claim_id,patient_id,provider_id,service_date,diagnosis_code,procedure_code,amount,currency,status,description\n"
            records = []

            for i in range(1, record_count + 1):
                records.append(
                    f"TXN-CSV-{i:03d},P{100000+i},PROV{i:03d},2025-07-{30-i%7:02d},E11.{i%10},8303{i%10},{100+i*25}.{i%100:02d},AED,{'pending' if i%2 else 'approved'},Test description {i}"
                )

            return header + "\n".join(records)

        def create_header_variations_csv(self) -> str:
            """Create CSV with different header variations."""
            return """ID,Member_ID,Clinic_ID,Date_of_Service,ICD_Code,CPT_Code,Billed_Amount,Status,Service_Description
REF001,M8765432,FAC101,31/07/2025,E11.9,83036,125.50,Pending,Hemoglobin A1c test
REF002,M7654321,FAC102,30/07/2025,I10,99213,250.00,Approved,Office consultation"""

        def create_malformed_csv(self) -> str:
            """Create CSV with malformed data for testing edge cases."""
            return """claim_id,patient_id,amount,notes
VALID001,P123456,125.50,This is a valid record
INVALID002,,INVALID_AMOUNT,Missing patient ID
INCOMPLETE003,P789012,,Missing amount
SPECIAL004,P456789,"2,500.50","Amount with comma formatting"
EMPTY_ROW_FOLLOWS,P999888,75.25,Record before empty row

,,WEIRD_AMT,This row has mostly empty values
FINAL007,P111222,999.99,Last valid record"""

        def create_numeric_variations_csv(self) -> str:
            """Create CSV with various numeric formats."""
            return """claim_id,patient_id,amount
TXN-001,P123456,"1,250.50"
TXN-002,P789012,$750.25
TXN-003,P456789,500.00 AED
TXN-004,P321654,300
TXN-005,P654987,INVALID_NUMBER"""

        def create_encoding_test_csv(self) -> str:
            """Create CSV with special characters for encoding tests."""
            return """claim_id,patient_id,description
TXN-001,P123456,Regular description
TXN-002,P789012,Description with café and naïve
TXN-003,P456789,Arabic text: مريض بحاجة إلى علاج"""

        def create_large_dataset_csv(self, record_count: int = 50) -> str:
            """Create large CSV dataset for performance testing."""
            header = "claim_id,patient_id,provider_id,service_date,diagnosis_code,procedure_code,amount,currency,status,description\n"
            records = []

            for i in range(1, record_count + 1):
                records.append(
                    f"TXN-LARGE-{i:03d},P{200000+i},PROV{(i%5)+1:03d},2025-07-{(i%28)+1:02d},"
                    f"{'E11.9' if i%3==0 else 'I10' if i%3==1 else 'Z00.00'},"
                    f"{'83036' if i%3==0 else '99213' if i%3==1 else '80061'},"
                    f"{100 + (i*17)%400}.{(i*7)%100:02d},AED,"
                    f"{'pending' if i%2 else 'approved' if i%3 else 'rejected'},"
                    f"Large dataset test record {i}"
                )

            return header + "\n".join(records)

        def create_quality_test_scenarios(self) -> dict:
            """Create different CSV scenarios for data quality testing."""
            return {
                "high_quality": """claim_id,patient_id,procedure_code,amount,service_date,diagnosis_code
TXN-001,P123456,83036,125.50,2025-07-31,E11.9
TXN-002,P789012,99213,250.00,2025-07-30,I10
TXN-003,P456789,80061,175.75,2025-07-29,Z00.00""",
                "medium_quality": """claim_id,patient_id,procedure_code,amount
TXN-001,P123456,83036,125.50
TXN-002,,99213,250.00
TXN-003,P456789,,175.75""",
                "low_quality": """claim_id,patient_id,amount
TXN-001,,INVALID
,P789012,
TXN-003,P456789,175.75""",
                "empty": "claim_id,patient_id,amount",
                "duplicates": """claim_id,patient_id,amount
TXN-001,P123456,125.50
TXN-001,P123456,125.50
TXN-002,P789012,250.00
TXN-001,P123456,125.50""",
            }

        def create_field_mapping_test_csv(self) -> str:
            """Create CSV to test all field mapping variations."""
            return """ref_no,insurance_id,facility_id,treatment_date,primary_diagnosis,service_code,total_cost,authorization_status,notes
REF-001,INS123456,FAC001,2025-07-31,E11.9,83036,125.50,pending,Diabetes monitoring
REF-002,INS789012,FAC002,2025-07-30,I10,99213,250.00,approved,Hypertension follow-up"""

    return CSVTestDataFactory()


@pytest.fixture
def create_test_csv_files(tmp_path, csv_test_data_factory):
    """
    Fixture that creates various test CSV files in a temporary directory.

    Returns:
        Dictionary mapping file types to file paths
    """
    files = {}

    # Basic valid CSV
    basic_file = tmp_path / "basic_claims.csv"
    basic_file.write_text(
        csv_test_data_factory.create_basic_claims_csv(), encoding="utf-8"
    )
    files["basic"] = str(basic_file)

    # Header variations CSV
    variations_file = tmp_path / "header_variations.csv"
    variations_file.write_text(
        csv_test_data_factory.create_header_variations_csv(), encoding="utf-8"
    )
    files["variations"] = str(variations_file)

    # Malformed CSV
    malformed_file = tmp_path / "malformed.csv"
    malformed_file.write_text(
        csv_test_data_factory.create_malformed_csv(), encoding="utf-8"
    )
    files["malformed"] = str(malformed_file)

    # Numeric variations CSV
    numeric_file = tmp_path / "numeric_variations.csv"
    numeric_file.write_text(
        csv_test_data_factory.create_numeric_variations_csv(), encoding="utf-8"
    )
    files["numeric"] = str(numeric_file)

    # Large dataset CSV
    large_file = tmp_path / "large_dataset.csv"
    large_file.write_text(
        csv_test_data_factory.create_large_dataset_csv(25), encoding="utf-8"
    )
    files["large"] = str(large_file)

    # Quality test scenarios
    quality_scenarios = csv_test_data_factory.create_quality_test_scenarios()
    for scenario_name, csv_content in quality_scenarios.items():
        scenario_file = tmp_path / f"quality_{scenario_name}.csv"
        scenario_file.write_text(csv_content, encoding="utf-8")
        files[f"quality_{scenario_name}"] = str(scenario_file)

    # Field mapping test CSV
    mapping_file = tmp_path / "field_mapping.csv"
    mapping_file.write_text(
        csv_test_data_factory.create_field_mapping_test_csv(), encoding="utf-8"
    )
    files["field_mapping"] = str(mapping_file)

    # Empty file
    empty_file = tmp_path / "empty.csv"
    empty_file.write_text("", encoding="utf-8")
    files["empty"] = str(empty_file)

    # Encoding test file
    encoding_file = tmp_path / "encoding_test.csv"
    encoding_file.write_text(
        csv_test_data_factory.create_encoding_test_csv(), encoding="utf-8"
    )
    files["encoding"] = str(encoding_file)

    return files


@pytest.fixture
def create_test_xml_files(tmp_path, test_data_factory):
    """
    Fixture that creates various test XML files in a temporary directory.

    Returns:
        Dictionary mapping file types to file paths
    """
    files = {}

    # Valid files
    eclaim_file = tmp_path / "valid_eclaim.xml"
    eclaim_file.write_text(test_data_factory.create_eclaim_xml(), encoding="utf-8")
    files["valid_eclaim"] = str(eclaim_file)

    shafafiya_file = tmp_path / "valid_shafafiya.xml"
    shafafiya_file.write_text(
        test_data_factory.create_shafafiya_xml(), encoding="utf-8"
    )
    files["valid_shafafiya"] = str(shafafiya_file)

    # Invalid files
    malformed_file = tmp_path / "malformed.xml"
    malformed_file.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<PriorAuthorizationRequest>
    <Header>
        <SenderID>PROV12345
    </Header>
</PriorAuthorizationRequest>""",
        encoding="utf-8",
    )
    files["malformed"] = str(malformed_file)

    # Missing required fields
    missing_fields_file = tmp_path / "missing_fields.xml"
    missing_fields_xml = test_data_factory.create_eclaim_xml(
        header_overrides={"SenderID": None}
    ).replace("<SenderID>None</SenderID>", "")
    missing_fields_file.write_text(missing_fields_xml, encoding="utf-8")
    files["missing_fields"] = str(missing_fields_file)

    # Unsupported root element
    unsupported_file = tmp_path / "unsupported.xml"
    unsupported_file.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<UnsupportedElement>
    <Data>Some data</Data>
</UnsupportedElement>""",
        encoding="utf-8",
    )
    files["unsupported"] = str(unsupported_file)

    # Empty file
    empty_file = tmp_path / "empty.xml"
    empty_file.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<root></root>""",
        encoding="utf-8",
    )
    files["empty"] = str(empty_file)

    # Large file with many services
    large_services = [test_data_factory.create_service_request(i) for i in range(1, 51)]
    large_file = tmp_path / "large.xml"
    large_file.write_text(
        test_data_factory.create_eclaim_xml(services=large_services), encoding="utf-8"
    )
    files["large"] = str(large_file)

    # Arabic text file
    arabic_file = tmp_path / "arabic.xml"
    arabic_xml = test_data_factory.create_shafafiya_xml(
        header_overrides={
            "SenderID": "مقدم_الخدمة_12345",
            "ReceiverID": "الدافع_67890",
        },
        auth_overrides={
            "Result": "نعم",
            "Comments": "مريض مصاب بداء السكري يحتاج إلى فحص دوري",
        },
    )
    arabic_file.write_text(arabic_xml, encoding="utf-8")
    files["arabic"] = str(arabic_file)

    # Rich clinical text files for FHIR testing
    rich_clinical_file = tmp_path / "rich_clinical.xml"
    rich_clinical_xml = test_data_factory.create_eclaim_xml(
        justification="35-year-old patient with Type 2 Diabetes Mellitus, poorly controlled (last HbA1c 9.2% from 6 months ago). Patient presents with symptoms of diabetic retinopathy - blurred vision and difficulty reading. Recent fasting glucose levels consistently above 250 mg/dL despite maximum metformin therapy. Requires comprehensive diabetes management including glycemic control assessment and retinal screening for complications. Patient is motivated and adherent to prescribed medications. Family history of diabetes and cardiovascular disease. Currently on metformin 1000mg twice daily. Blood pressure elevated at 150/95 mmHg. Previous eye exam done 18 months ago showed early retinopathy changes."
    )
    rich_clinical_file.write_text(rich_clinical_xml, encoding="utf-8")
    files["rich_clinical"] = str(rich_clinical_file)

    # Minimal clinical text for testing edge cases
    minimal_clinical_file = tmp_path / "minimal_clinical.xml"
    minimal_clinical_xml = test_data_factory.create_eclaim_xml(
        justification="Patient needs test."
    )
    minimal_clinical_file.write_text(minimal_clinical_xml, encoding="utf-8")
    files["minimal_clinical"] = str(minimal_clinical_file)

    # Multiple medications file
    multi_meds_file = tmp_path / "multi_medications.xml"
    multi_meds_xml = test_data_factory.create_eclaim_xml(
        justification="Patient with diabetes and hypertension. Currently on metformin 500mg twice daily, lisinopril 10mg once daily, and atorvastatin 20mg at bedtime. Patient stopped taking insulin last month due to side effects. Previously completed course of antibiotics for UTI. Blood pressure well controlled with ACE inhibitor therapy."
    )
    multi_meds_file.write_text(multi_meds_xml, encoding="utf-8")
    files["multi_medications"] = str(multi_meds_file)

    return files


@pytest.fixture
def mock_file_system():
    """Fixture for mocking file system operations."""

    class MockFileSystem:
        """Mock file system for testing file operations."""

        def __init__(self):
            self.files = {}
            self.directories = set()

        def add_file(self, path: str, content: str):
            """Add a file to the mock file system."""
            self.files[path] = content
            # Add parent directories
            parent = str(Path(path).parent)
            while parent != "/":
                self.directories.add(parent)
                parent = str(Path(parent).parent)

        def exists(self, path: str) -> bool:
            """Check if file or directory exists."""
            return path in self.files or path in self.directories

        def read_text(self, path: str) -> str:
            """Read text content of a file."""
            if path not in self.files:
                raise FileNotFoundError(f"File not found: {path}")
            return self.files[path]

        def is_file(self, path: str) -> bool:
            """Check if path is a file."""
            return path in self.files

        def is_dir(self, path: str) -> bool:
            """Check if path is a directory."""
            return path in self.directories

    return MockFileSystem()


@pytest.fixture
def performance_monitor():
    """Fixture for monitoring test performance metrics."""
    import time
    import tracemalloc

    class PerformanceMonitor:
        """Monitor performance metrics during tests."""

        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.memory_start = None
            self.memory_peak = None

        def start(self):
            """Start monitoring."""
            tracemalloc.start()
            self.start_time = time.time()
            self.memory_start = tracemalloc.get_traced_memory()[0]

        def stop(self):
            """Stop monitoring and capture metrics."""
            self.end_time = time.time()
            current, peak = tracemalloc.get_traced_memory()
            self.memory_peak = peak
            tracemalloc.stop()

        @property
        def elapsed_time(self) -> float:
            """Get elapsed time in seconds."""
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return 0.0

        @property
        def memory_usage_mb(self) -> float:
            """Get peak memory usage in MB."""
            if self.memory_peak:
                return self.memory_peak / 1024 / 1024
            return 0.0

        def assert_performance(
            self, max_time: float = 5.0, max_memory_mb: float = 100.0
        ):
            """Assert that performance is within acceptable limits."""
            assert (
                self.elapsed_time <= max_time
            ), f"Test took {self.elapsed_time:.2f}s, max allowed: {max_time}s"
            assert (
                self.memory_usage_mb <= max_memory_mb
            ), f"Test used {self.memory_usage_mb:.2f}MB, max allowed: {max_memory_mb}MB"

    return PerformanceMonitor()


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "performance: mark test as a performance test")
    config.addinivalue_line(
        "markers", "slow: mark test as slow (may be skipped in quick runs)"
    )
    config.addinivalue_line("markers", "edge_case: mark test as testing edge cases")
    config.addinivalue_line("markers", "fhir: mark test as FHIR-related")
    config.addinivalue_line("markers", "nlp: mark test as clinical NLP-related")
    config.addinivalue_line(
        "markers", "clinical: mark test as clinical data processing"
    )
    config.addinivalue_line("markers", "bundle: mark test as FHIR Bundle testing")


def pytest_ignore_collect(path):
    """Ignore generated tests under the output/ directory."""
    try:
        return "output/" in str(path)
    except Exception:
        return False


def pytest_collection_modifyitems(config, items):
    """Add markers to tests based on their names and content."""
    for item in items:
        # Add unit marker to most tests
        if "unit" not in item.keywords and "integration" not in item.keywords:
            item.add_marker(pytest.mark.unit)

        # Add slow marker to tests that might be slow
        if any(
            keyword in item.name.lower()
            for keyword in ["large", "concurrent", "performance", "memory"]
        ):
            item.add_marker(pytest.mark.slow)

        # Add edge_case marker to edge case tests
        if any(
            keyword in item.name.lower()
            for keyword in ["edge", "error", "invalid", "malformed"]
        ):
            item.add_marker(pytest.mark.edge_case)

        # Add FHIR marker to FHIR-related tests
        if any(
            keyword in item.name.lower()
            for keyword in [
                "fhir",
                "bundle",
                "clinical",
                "observation",
                "medication",
                "condition",
                "procedure",
            ]
        ):
            item.add_marker(pytest.mark.fhir)

        # Add NLP marker to clinical text processing tests
        if any(
            keyword in item.name.lower()
            for keyword in ["nlp", "extraction", "clinical_text", "justification"]
        ):
            item.add_marker(pytest.mark.nlp)


# Custom assertion helpers
def assert_xml_structure_matches(
    actual: Dict[str, Any], expected: Dict[str, Any], ignore_keys=None
):
    """
    Assert that XML structure matches expected structure, ignoring specified keys.

    Args:
        actual: Actual parsed XML structure
        expected: Expected XML structure
        ignore_keys: List of keys to ignore in comparison
    """
    ignore_keys = ignore_keys or ["ingestion_metadata"]

    def normalize_dict(d, ignore_keys):
        """Remove ignored keys and normalize values."""
        if isinstance(d, dict):
            return {
                k: normalize_dict(v, ignore_keys)
                for k, v in d.items()
                if k not in ignore_keys
            }
        elif isinstance(d, list):
            return [normalize_dict(item, ignore_keys) for item in d]
        else:
            return d

    normalized_actual = normalize_dict(actual, ignore_keys)
    normalized_expected = normalize_dict(expected, ignore_keys)

    assert normalized_actual == normalized_expected


def assert_error_details(
    exception, expected_file_path=None, expected_field_name=None, expected_details=None
):
    """
    Assert that exception contains expected error details.

    Args:
        exception: The caught exception
        expected_file_path: Expected file path in error
        expected_field_name: Expected field name in error
        expected_details: Expected details dict keys
    """
    if expected_file_path:
        assert exception.file_path == expected_file_path

    if expected_field_name and hasattr(exception, "field_name"):
        assert exception.field_name == expected_field_name

    if expected_details and hasattr(exception, "details"):
        for key in expected_details:
            assert key in exception.details


@pytest.fixture
def fhir_test_data_factory():
    """
    Fixture providing a factory for creating FHIR test data structures.

    Returns:
        FHIRTestDataFactory instance for generating FHIR Bundle test data
    """

    class FHIRTestDataFactory:
        """Factory for creating FHIR Bundle test data."""

        def create_expected_claim_resource(self, **overrides) -> Dict[str, Any]:
            """Create expected FHIR Claim resource structure."""
            claim = {
                "resourceType": "Claim",
                "id": "TXN-ECLAIM-2025-001789",
                "meta": {
                    "profile": [
                        "https://healthcare-preauth.org/fhir/StructureDefinition/uae-claim"
                    ],
                    "source": "eClaimLink",
                },
                "identifier": [
                    {
                        "use": "official",
                        "system": "https://healthcare-preauth.org/identifiers/eclaim-transaction",
                        "value": "TXN-ECLAIM-2025-001789",
                    }
                ],
                "status": "active",
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/claim-type",
                            "code": "professional",
                        }
                    ]
                },
                "use": "preauthorization",
                "patient": {"reference": "Patient/unknown"},
                "created": "27/07/2025 14:15",
                "provider": {"reference": "Organization/unknown-provider"},
                "diagnosis": [],
                "item": [],
                "supportingInfo": [],
            }
            claim.update(overrides)
            return claim

        def create_expected_condition_resource(self, **overrides) -> Dict[str, Any]:
            """Create expected FHIR Condition resource structure."""
            condition = {
                "resourceType": "Condition",
                "id": "condition-E11.9-1",
                "meta": {
                    "profile": [
                        "https://healthcare-preauth.org/fhir/StructureDefinition/uae-condition"
                    ],
                    "source": "eClaimLink",
                },
                "identifier": [
                    {
                        "system": "https://healthcare-preauth.org/identifiers/condition",
                        "value": "condition-E11.9-1",
                    }
                ],
                "clinicalStatus": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                            "code": "active",
                        }
                    ]
                },
                "verificationStatus": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                            "code": "confirmed",
                        }
                    ]
                },
                "category": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                                "code": "encounter-diagnosis",
                            }
                        ]
                    }
                ],
                "code": {
                    "coding": [
                        {
                            "system": "http://hl7.org/fhir/sid/icd-10-am",
                            "code": "E11.9",
                            "display": "ICD-10-AM: E11.9",
                        }
                    ],
                    "text": "Condition: E11.9",
                },
                "subject": {"reference": "Patient/unknown"},
            }
            condition.update(overrides)
            return condition

        def create_expected_observation_resource(self, **overrides) -> Dict[str, Any]:
            """Create expected FHIR Observation resource structure."""
            observation = {
                "resourceType": "Observation",
                "id": "observation-hba1c-1",
                "meta": {
                    "profile": [
                        "https://healthcare-preauth.org/fhir/StructureDefinition/uae-observation"
                    ],
                    "source": "clinical-text",
                },
                "identifier": [
                    {
                        "system": "https://healthcare-preauth.org/identifiers/observation",
                        "value": "observation-hba1c-1",
                    }
                ],
                "status": "final",
                "category": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                "code": "laboratory",
                            }
                        ]
                    }
                ],
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": "4548-4",
                            "display": "Hemoglobin A1c",
                        }
                    ],
                    "text": "Hemoglobin A1c: 9.2 %",
                },
                "subject": {"reference": "Patient/unknown"},
                "valueQuantity": {
                    "value": 9.2,
                    "unit": "%",
                    "system": "http://unitsofmeasure.org",
                    "code": "%",
                },
            }
            observation.update(overrides)
            return observation

        def create_expected_medication_resource(self, **overrides) -> Dict[str, Any]:
            """Create expected FHIR MedicationStatement resource structure."""
            medication = {
                "resourceType": "MedicationStatement",
                "id": "medication-metformin-1",
                "meta": {
                    "profile": [
                        "https://healthcare-preauth.org/fhir/StructureDefinition/uae-medication-statement"
                    ],
                    "source": "clinical-text",
                },
                "identifier": [
                    {
                        "system": "https://healthcare-preauth.org/identifiers/medication-statement",
                        "value": "medication-metformin-1",
                    }
                ],
                "status": "active",
                "medicationCodeableConcept": {
                    "coding": [
                        {
                            "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                            "code": "6809",
                            "display": "Metformin",
                        }
                    ],
                    "text": "Metformin",
                },
                "subject": {"reference": "Patient/unknown"},
            }
            medication.update(overrides)
            return medication

        def create_expected_procedure_resource(self, **overrides) -> Dict[str, Any]:
            """Create expected FHIR Procedure resource structure."""
            procedure = {
                "resourceType": "Procedure",
                "id": "procedure-83036-requested",
                "meta": {
                    "profile": [
                        "https://healthcare-preauth.org/fhir/StructureDefinition/uae-procedure"
                    ],
                    "source": "eClaimLink",
                },
                "identifier": [
                    {
                        "system": "https://healthcare-preauth.org/identifiers/procedure",
                        "value": "procedure-83036-requested",
                    }
                ],
                "status": "preparation",
                "code": {
                    "coding": [
                        {
                            "system": "http://www.ama-assn.org/go/cpt",
                            "code": "83036",
                            "display": "CPT: 83036",
                        }
                    ],
                    "text": "Requested procedure: 83036",
                },
                "subject": {"reference": "Patient/unknown"},
            }
            procedure.update(overrides)
            return procedure

        def create_expected_bundle_structure(
            self, entry_count: int = 5, **overrides
        ) -> Dict[str, Any]:
            """Create expected FHIR Bundle structure."""
            bundle = {
                "resourceType": "Bundle",
                "id": "eClaimLink-Bundle-TXN-ECLAIM-2025-001789-20250731",
                "meta": {
                    "profile": [
                        "https://healthcare-preauth.org/fhir/StructureDefinition/healthcare-bundle"
                    ],
                    "source": "eClaimLink",
                    "versionId": "1",
                },
                "type": "collection",
                "total": entry_count,
                "entry": [],
                "extension": [],
            }
            bundle.update(overrides)
            return bundle

        def create_clinical_text_samples(self) -> Dict[str, str]:
            """Create various clinical text samples for testing NLP extraction."""
            return {
                "diabetes_comprehensive": "35-year-old patient with Type 2 Diabetes Mellitus, poorly controlled (last HbA1c 9.2% from 6 months ago). Patient presents with symptoms of diabetic retinopathy - blurred vision and difficulty reading. Recent fasting glucose levels consistently above 250 mg/dL despite maximum metformin therapy. Requires comprehensive diabetes management including glycemic control assessment and retinal screening for complications. Patient is motivated and adherent to prescribed medications. Family history of diabetes and cardiovascular disease.",
                "medications_rich": "Patient with diabetes and hypertension. Currently on metformin 500mg twice daily, lisinopril 10mg once daily, and atorvastatin 20mg at bedtime. Patient stopped taking insulin last month due to side effects. Previously completed course of antibiotics for UTI. Blood pressure well controlled with ACE inhibitor therapy.",
                "vital_signs": "Patient reports blood pressure readings at home averaging 150/95 mmHg. Recent weight gain of 5kg over 3 months. Temperature 37.2°C. Heart rate 88 bpm regular rhythm. Blood glucose fasting 280 mg/dL this morning.",
                "lab_values": "Recent lab results show HbA1c 8.5%, fasting glucose 245 mg/dL, creatinine 1.2 mg/dL (slightly elevated), cholesterol 220 mg/dL. Urine microalbumin positive indicating early diabetic nephropathy.",
                "historical_procedures": "Last eye exam done 18 months ago showed early retinopathy changes. Previous HbA1c test 6 months ago was 9.2%. Blood work completed 3 months ago showed elevated glucose levels. Patient had comprehensive metabolic panel done last year.",
                "minimal": "Patient needs test.",
                "empty": "",
                "arabic_mixed": "مريض مصاب بداء السكري. Patient with diabetes mellitus. HbA1c 8.2%. يحتاج إلى فحص دوري.",
            }

        def create_expected_clinical_scores(self, **overrides) -> Dict[str, float]:
            """Create expected clinical intelligence scores."""
            scores = {
                "clinical_completeness": 1.0,
                "clinical_context_score": 0.85,
                "data_quality_score": 0.95,
                "enrichment_score": 0.4,
                "ai_confidence": 0.8,
                "total_resources": 5,
                "resource_distribution": {
                    "Claim": 1,
                    "Condition": 1,
                    "Observation": 1,
                    "MedicationStatement": 1,
                    "Procedure": 1,
                },
            }
            scores.update(overrides)
            return scores

    return FHIRTestDataFactory()


@pytest.fixture
def clinical_validation_helper():
    """
    Fixture providing helper functions for validating clinical data extraction.

    Returns:
        ClinicalValidationHelper instance with validation methods
    """

    class ClinicalValidationHelper:
        """Helper class for validating clinical data extraction."""

        def validate_fhir_bundle_structure(self, bundle: Dict[str, Any]):
            """Validate basic FHIR Bundle structure."""
            assert bundle["resourceType"] == "Bundle", "Must be a Bundle resource"
            assert "id" in bundle, "Bundle must have an ID"
            assert "type" in bundle, "Bundle must have a type"
            assert "entry" in bundle, "Bundle must have entries"
            assert "total" in bundle, "Bundle must have total count"
            assert isinstance(bundle["entry"], list), "Entries must be a list"
            assert bundle["total"] == len(
                bundle["entry"]
            ), "Total must match entry count"

        def validate_fhir_resource_structure(
            self, resource: Dict[str, Any], resource_type: str
        ):
            """Validate basic FHIR resource structure."""
            assert (
                resource["resourceType"] == resource_type
            ), f"Must be a {resource_type} resource"
            assert "id" in resource, f"{resource_type} must have an ID"
            assert "meta" in resource, f"{resource_type} must have meta"

        def validate_bundle_entry(self, entry: Dict[str, Any]):
            """Validate FHIR Bundle entry structure."""
            assert "fullUrl" in entry, "Bundle entry must have fullUrl"
            assert "resource" in entry, "Bundle entry must have resource"
            assert "search" in entry, "Bundle entry must have search info"

        def validate_clinical_extensions(self, resource: Dict[str, Any]):
            """Validate clinical intelligence extensions."""
            extensions = resource.get("extension", [])

            # Look for clinical context score
            context_scores = [
                ext
                for ext in extensions
                if ext.get("url")
                == "https://healthcare-preauth.org/fhir/StructureDefinition/clinical-context-score"
            ]
            if context_scores:
                assert (
                    "valueDecimal" in context_scores[0]
                ), "Clinical context score must have decimal value"
                assert (
                    0 <= context_scores[0]["valueDecimal"] <= 1
                ), "Score must be between 0 and 1"

        def validate_resource_relationships(self, bundle: Dict[str, Any]):
            """Validate relationships between FHIR resources."""
            resources_by_type = {}

            # Group resources by type
            for entry in bundle["entry"]:
                resource = entry["resource"]
                resource_type = resource["resourceType"]
                if resource_type not in resources_by_type:
                    resources_by_type[resource_type] = []
                resources_by_type[resource_type].append(resource)

            # Check that Claim exists (primary resource)
            assert "Claim" in resources_by_type, "Bundle must contain a Claim resource"

            # Check references are properly formed
            claim = resources_by_type["Claim"][0]
            claim_id = claim["id"]

            # Validate that other resources reference the claim appropriately
            for resource_type in ["Observation", "MedicationStatement", "Procedure"]:
                if resource_type in resources_by_type:
                    for resource in resources_by_type[resource_type]:
                        based_on = resource.get("basedOn", [])
                        if based_on:
                            assert any(
                                ref.get("reference") == f"Claim/{claim_id}"
                                for ref in based_on
                            ), f"{resource_type} should reference the Claim"

        def validate_clinical_data_quality(
            self, bundle: Dict[str, Any], min_score: float = 0.7
        ):
            """Validate clinical data quality scores."""
            extensions = bundle.get("extension", [])

            quality_scores = [
                ext
                for ext in extensions
                if ext.get("url")
                == "https://healthcare-preauth.org/fhir/StructureDefinition/data-quality-score"
            ]

            if quality_scores:
                score = quality_scores[0].get("valueDecimal", 0)
                assert (
                    score >= min_score
                ), f"Data quality score {score} below minimum {min_score}"

        def extract_clinical_observations(
            self, bundle: Dict[str, Any]
        ) -> List[Dict[str, Any]]:
            """Extract Observation resources from bundle."""
            observations = []
            for entry in bundle["entry"]:
                if entry["resource"]["resourceType"] == "Observation":
                    observations.append(entry["resource"])
            return observations

        def extract_medications(self, bundle: Dict[str, Any]) -> List[Dict[str, Any]]:
            """Extract MedicationStatement resources from bundle."""
            medications = []
            for entry in bundle["entry"]:
                if entry["resource"]["resourceType"] == "MedicationStatement":
                    medications.append(entry["resource"])
            return medications

        def extract_conditions(self, bundle: Dict[str, Any]) -> List[Dict[str, Any]]:
            """Extract Condition resources from bundle."""
            conditions = []
            for entry in bundle["entry"]:
                if entry["resource"]["resourceType"] == "Condition":
                    conditions.append(entry["resource"])
            return conditions

        def extract_procedures(self, bundle: Dict[str, Any]) -> List[Dict[str, Any]]:
            """Extract Procedure resources from bundle."""
            procedures = []
            for entry in bundle["entry"]:
                if entry["resource"]["resourceType"] == "Procedure":
                    procedures.append(entry["resource"])
            return procedures

        def count_resources_by_type(self, bundle: Dict[str, Any]) -> Dict[str, int]:
            """Count resources by type in bundle."""
            counts = {}
            for entry in bundle["entry"]:
                resource_type = entry["resource"]["resourceType"]
                counts[resource_type] = counts.get(resource_type, 0) + 1
            return counts

    return ClinicalValidationHelper()


@pytest.fixture
def sample_xml_paths():
    """
    Fixture providing paths to actual sample XML files.

    Returns:
        Dictionary with paths to sample XML files
    """
    base_path = Path(__file__).parent.parent / "samples"
    return {
        "eclaim_link": str(base_path / "eclaim_link_request.xml"),
        "shafafiya": str(base_path / "shafafiya_prior_auth_request.xml"),
    }


@pytest.fixture
def schema_paths():
    """
    Fixture providing paths to XSD schema files.

    Returns:
        Dictionary with paths to schema files
    """
    base_path = Path(__file__).parent.parent / "schemas"
    return {
        "common_types": str(base_path / "CommonTypes_20191113.xsd"),
        "prior_authorization": str(base_path / "PriorAuthorization.xsd"),
    }


def assert_fhir_bundle_structure(
    bundle: Dict[str, Any], expected_resource_count: int = None
):
    """
    Assert that a dictionary represents a valid FHIR Bundle structure.

    Args:
        bundle: Dictionary to validate as FHIR Bundle
        expected_resource_count: Expected number of resources in bundle
    """
    assert bundle.get("resourceType") == "Bundle", "Must be a Bundle resource"
    assert "id" in bundle, "Bundle must have an ID"
    assert "type" in bundle, "Bundle must have a type"
    assert "entry" in bundle, "Bundle must have entries"
    assert "total" in bundle, "Bundle must have total count"
    assert isinstance(bundle["entry"], list), "Entries must be a list"

    if expected_resource_count is not None:
        assert (
            len(bundle["entry"]) == expected_resource_count
        ), f"Expected {expected_resource_count} resources, got {len(bundle['entry'])}"

    assert bundle["total"] == len(bundle["entry"]), "Total must match entry count"

    # Validate each entry
    for i, entry in enumerate(bundle["entry"]):
        assert "fullUrl" in entry, f"Entry {i} must have fullUrl"
        assert "resource" in entry, f"Entry {i} must have resource"
        assert (
            "resourceType" in entry["resource"]
        ), f"Entry {i} resource must have resourceType"
        assert "id" in entry["resource"], f"Entry {i} resource must have id"


def assert_fhir_resource_quality(
    resource: Dict[str, Any], resource_type: str, min_confidence: float = 0.5
):
    """
    Assert that a FHIR resource meets quality standards.

    Args:
        resource: FHIR resource to validate
        resource_type: Expected resource type
        min_confidence: Minimum confidence score for clinical extractions
    """
    assert (
        resource.get("resourceType") == resource_type
    ), f"Expected {resource_type}, got {resource.get('resourceType')}"
    assert "id" in resource, f"{resource_type} must have an ID"
    assert "meta" in resource, f"{resource_type} must have meta"

    # Check for clinical context extensions if present
    extensions = resource.get("extension", [])
    for ext in extensions:
        if (
            ext.get("url")
            == "https://healthcare-preauth.org/fhir/StructureDefinition/clinical-context-score"
        ):
            confidence = ext.get("valueDecimal", 0)
            assert (
                confidence >= min_confidence
            ), f"Clinical confidence {confidence} below minimum {min_confidence}"


def assert_clinical_nlp_extraction(
    bundle: Dict[str, Any], clinical_text: str, expected_extractions: Dict[str, int]
):
    """
    Assert that clinical NLP extraction produced expected results.

    Args:
        bundle: FHIR Bundle with extracted resources
        clinical_text: Original clinical text
        expected_extractions: Expected counts by resource type
    """
    resource_counts = {}

    for entry in bundle["entry"]:
        resource_type = entry["resource"]["resourceType"]
        resource_counts[resource_type] = resource_counts.get(resource_type, 0) + 1

    for resource_type, expected_count in expected_extractions.items():
        actual_count = resource_counts.get(resource_type, 0)
        assert (
            actual_count >= expected_count
        ), f"Expected at least {expected_count} {resource_type} resources, got {actual_count}"

    # If clinical text is rich, expect more extractions
    if len(clinical_text) > 200:
        total_extracted = (
            sum(resource_counts.values()) - 1
        )  # Subtract the primary Claim
        assert (
            total_extracted >= 2
        ), f"Rich clinical text should produce multiple extractions, got {total_extracted}"
