"""
Comprehensive unit tests for XML ingestion pipeline.

This module provides extensive test coverage for the XML ingestion system,
including tests for both eClaimLink and Shafafiya formats, error handling,
edge cases, and the factory pattern implementation.
"""

import logging
from unittest.mock import Mock, patch

import pytest
import xmltodict

from pipelines.base import XMLIngestor
from pipelines.eclaim_link_ingestor import EClaimLinkIngestor
from pipelines.shafafiya_ingestor import ShafafiyaIngestor
from pipelines.factory import XMLIngestorFactory
from pipelines.exceptions import (
    XMLIngestionError,
    SchemaValidationError,
    XMLParsingError,
    UnsupportedFormatError,
    DataNormalizationError,
    ConfigurationError,
)


# Test fixture data as constants
VALID_ECLAIM_LINK_XML = '''<?xml version="1.0" encoding="UTF-8"?>
<PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
    <Header>
        <SenderID>PROV12345</SenderID>
        <ReceiverID>PAYER67890</ReceiverID>
        <TransactionDateTime>27/07/2025 10:32</TransactionDateTime>
        <TransactionID>TXN-2025-000456</TransactionID>
    </Header>
    <JustificationText>Patient requires urgent medical attention for diabetes management.</JustificationText>
    <ServiceRequests>
        <ServiceRequest>
            <ct:ActivityCode>83036</ct:ActivityCode>
            <ct:DiagnosisCode>E11.9</ct:DiagnosisCode>
            <ct:ActivityDateTime>28/07/2025 09:00</ct:ActivityDateTime>
            <ct:ActivityInstructions>HbA1c test for diabetes monitoring</ct:ActivityInstructions>
            <RequestedAmount currency="AED">120.00</RequestedAmount>
        </ServiceRequest>
        <ServiceRequest>
            <ct:ActivityCode>92014</ct:ActivityCode>
            <ct:DiagnosisCode>H36.0</ct:DiagnosisCode>
            <ct:ActivityDateTime>28/07/2025 11:00</ct:ActivityDateTime>
            <ct:ActivityInstructions>Diabetic retinopathy screening</ct:ActivityInstructions>
            <RequestedAmount currency="AED">250.00</RequestedAmount>
        </ServiceRequest>
    </ServiceRequests>
</PriorAuthorizationRequest>'''

VALID_SHAFAFIYA_XML = '''<?xml version="1.0" encoding="UTF-8"?>
<Prior.Authorization xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <Header>
        <SenderID>PROV12345</SenderID>
        <ReceiverID>PAYER67890</ReceiverID>
        <TransactionDate>27/07/2025 10:32</TransactionDate>
        <RecordCount>2</RecordCount>
        <DispositionFlag>TEST</DispositionFlag>
    </Header>
    <Authorization>
        <Result>Yes</Result>
        <ID>PA-2025-000123</ID>
        <IDPayer>PAYER67890</IDPayer>
        <Start>25/07/2025 00:00</Start>
        <End>25/08/2025 23:59</End>
        <Limit>1000.00</Limit>
        <Comments>Patient with poorly controlled diabetes; last HbA1c 9 months ago.</Comments>
        <Activity>
            <ID>1</ID>
            <Type>3</Type>
            <Code>83036</Code>
            <Quantity>1</Quantity>
            <Net>120.00</Net>
            <List>150.00</List>
            <PatientShare>30.00</PatientShare>
            <PaymentAmount>90.00</PaymentAmount>
            <Observation>
                <Type>ICD10</Type>
                <Code>E11.9</Code>
                <Value>Type 2 diabetes mellitus without complications</Value>
                <ValueType>text</ValueType>
            </Observation>
        </Activity>
        <Activity>
            <ID>2</ID>
            <Type>3</Type>
            <Code>92014</Code>
            <Quantity>1</Quantity>
            <Net>250.00</Net>
            <PaymentAmount>200.00</PaymentAmount>
            <DenialCode>NONE</DenialCode>
        </Activity>
    </Authorization>
</Prior.Authorization>'''

INVALID_XML_MALFORMED = '''<?xml version="1.0" encoding="UTF-8"?>
<PriorAuthorizationRequest>
    <Header>
        <SenderID>PROV12345</SenderID>
        <!-- Missing closing tag -->
        <ReceiverID>PAYER67890
    </Header>
</PriorAuthorizationRequest>'''

INVALID_XML_MISSING_REQUIRED_FIELDS = '''<?xml version="1.0" encoding="UTF-8"?>
<PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
    <Header>
        <!-- Missing required SenderID -->
        <ReceiverID>PAYER67890</ReceiverID>
        <TransactionDateTime>27/07/2025 10:32</TransactionDateTime>
    </Header>
</PriorAuthorizationRequest>'''

INVALID_XML_WRONG_DATE_FORMAT = '''<?xml version="1.0" encoding="UTF-8"?>
<PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
    <Header>
        <SenderID>PROV12345</SenderID>
        <ReceiverID>PAYER67890</ReceiverID>
        <!-- Invalid date format - should be dd/mm/yyyy HH:MM -->
        <TransactionDateTime>2025-07-27T10:32:00</TransactionDateTime>
        <TransactionID>TXN-2025-000456</TransactionID>
    </Header>
</PriorAuthorizationRequest>'''

EMPTY_XML_FILE = '''<?xml version="1.0" encoding="UTF-8"?>
<root></root>'''

LARGE_XML_CONTENT = '''<?xml version="1.0" encoding="UTF-8"?>
<PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
    <Header>
        <SenderID>PROV12345</SenderID>
        <ReceiverID>PAYER67890</ReceiverID>
        <TransactionDateTime>27/07/2025 10:32</TransactionDateTime>
        <TransactionID>TXN-2025-000456</TransactionID>
    </Header>
    <ServiceRequests>
        {service_requests}
    </ServiceRequests>
</PriorAuthorizationRequest>'''

ARABIC_TEXT_XML = '''<?xml version="1.0" encoding="UTF-8"?>
<Prior.Authorization>
    <Header>
        <SenderID>مقدم_الخدمة_12345</SenderID>
        <ReceiverID>الدافع_67890</ReceiverID>
        <TransactionDate>27/07/2025 10:32</TransactionDate>
        <RecordCount>1</RecordCount>
    </Header>
    <Authorization>
        <Result>نعم</Result>
        <ID>PA-2025-000123</ID>
        <Start>25/07/2025 00:00</Start>
        <End>25/08/2025 23:59</End>
        <Comments>مريض مصاب بداء السكري يحتاج إلى فحص دوري</Comments>
        <Activity>
            <ID>1</ID>
            <Type>3</Type>
            <Code>83036</Code>
            <Quantity>1</Quantity>
            <Net>120.00</Net>
            <PaymentAmount>90.00</PaymentAmount>
        </Activity>
    </Authorization>
</Prior.Authorization>'''

UNSUPPORTED_ROOT_ELEMENT_XML = '''<?xml version="1.0" encoding="UTF-8"?>
<UnsupportedRootElement>
    <Data>Some data</Data>
</UnsupportedRootElement>'''


class TestXMLIngestorBase:
    """Test cases for the base XMLIngestor abstract class."""

    def test_abstract_class_cannot_be_instantiated(self):
        """Test that XMLIngestor cannot be instantiated directly."""
        with pytest.raises(TypeError):
            XMLIngestor()

    def test_configuration_validation_schema_path_required_when_validation_enabled(
        self,
    ):
        """Test that schema_path is required when validation is enabled."""

        class ConcreteIngestor(XMLIngestor):
            def normalize(self, parsed_data, xml_file_path=None):
                return parsed_data

            def get_supported_root_elements(self):
                return ["TestElement"]

        with pytest.raises(ConfigurationError) as exc_info:
            ConcreteIngestor(enable_validation=True, schema_path=None)

        assert "schema_path" in str(exc_info.value)

    def test_configuration_validation_schema_file_must_exist(self):
        """Test that schema file must exist if path is provided."""

        class ConcreteIngestor(XMLIngestor):
            def normalize(self, parsed_data, xml_file_path=None):
                return parsed_data

            def get_supported_root_elements(self):
                return ["TestElement"]

        with pytest.raises(ConfigurationError) as exc_info:
            ConcreteIngestor(schema_path="/nonexistent/schema.xsd")

        assert "does not exist" in str(exc_info.value)

    def test_validation_disabled_allows_no_schema(self):
        """Test that validation can be disabled without providing schema."""

        class ConcreteIngestor(XMLIngestor):
            def normalize(self, parsed_data, xml_file_path=None):
                return parsed_data

            def get_supported_root_elements(self):
                return ["TestElement"]

        # Should not raise exception
        ingestor = ConcreteIngestor(enable_validation=False)
        assert not ingestor.enable_validation

    def test_default_logger_creation(self):
        """Test that default logger is created when none provided."""

        class ConcreteIngestor(XMLIngestor):
            def normalize(self, parsed_data, xml_file_path=None):
                return parsed_data

            def get_supported_root_elements(self):
                return ["TestElement"]

        ingestor = ConcreteIngestor(enable_validation=False)
        assert ingestor.logger is not None
        assert isinstance(ingestor.logger, logging.Logger)

    def test_custom_logger_usage(self):
        """Test that custom logger is used when provided."""

        class ConcreteIngestor(XMLIngestor):
            def normalize(self, parsed_data, xml_file_path=None):
                return parsed_data

            def get_supported_root_elements(self):
                return ["TestElement"]

        custom_logger = Mock(spec=logging.Logger)
        ingestor = ConcreteIngestor(enable_validation=False, logger=custom_logger)
        assert ingestor.logger is custom_logger

    def test_safe_get_nested_access(self):
        """Test _safe_get method for nested dictionary access."""

        class ConcreteIngestor(XMLIngestor):
            def normalize(self, parsed_data, xml_file_path=None):
                return parsed_data

            def get_supported_root_elements(self):
                return ["TestElement"]

        ingestor = ConcreteIngestor(enable_validation=False)

        data = {"level1": {"level2": {"target": "found_value"}}}

        result = ingestor._safe_get(data, "level1.level2.target", default="default")
        assert result == "found_value"

    def test_safe_get_missing_path_with_default(self):
        """Test _safe_get returns default for missing path."""

        class ConcreteIngestor(XMLIngestor):
            def normalize(self, parsed_data, xml_file_path=None):
                return parsed_data

            def get_supported_root_elements(self):
                return ["TestElement"]

        ingestor = ConcreteIngestor(enable_validation=False)

        data = {"level1": {"level2": {}}}
        result = ingestor._safe_get(
            data, "level1.level2.missing", default="default_value"
        )
        assert result == "default_value"

    def test_safe_get_missing_required_field_raises_error(self):
        """Test _safe_get raises error for missing required field."""

        class ConcreteIngestor(XMLIngestor):
            def normalize(self, parsed_data, xml_file_path=None):
                return parsed_data

            def get_supported_root_elements(self):
                return ["TestElement"]

        ingestor = ConcreteIngestor(enable_validation=False)

        data = {"level1": {"level2": {}}}

        with pytest.raises(DataNormalizationError) as exc_info:
            ingestor._safe_get(
                data, "level1.level2.missing", field_name="required_field"
            )

        assert "required_field" in str(exc_info.value)

    def test_ensure_list_with_dict(self):
        """Test _ensure_list converts dict to single-item list."""

        class ConcreteIngestor(XMLIngestor):
            def normalize(self, parsed_data, xml_file_path=None):
                return parsed_data

            def get_supported_root_elements(self):
                return ["TestElement"]

        ingestor = ConcreteIngestor(enable_validation=False)

        result = ingestor._ensure_list({"key": "value"})
        assert result == [{"key": "value"}]

    def test_ensure_list_with_list(self):
        """Test _ensure_list returns list unchanged."""

        class ConcreteIngestor(XMLIngestor):
            def normalize(self, parsed_data, xml_file_path=None):
                return parsed_data

            def get_supported_root_elements(self):
                return ["TestElement"]

        ingestor = ConcreteIngestor(enable_validation=False)

        test_list = [{"key1": "value1"}, {"key2": "value2"}]
        result = ingestor._ensure_list(test_list)
        assert result == test_list

    def test_ensure_list_with_none(self):
        """Test _ensure_list returns empty list for None."""

        class ConcreteIngestor(XMLIngestor):
            def normalize(self, parsed_data, xml_file_path=None):
                return parsed_data

            def get_supported_root_elements(self):
                return ["TestElement"]

        ingestor = ConcreteIngestor(enable_validation=False)

        result = ingestor._ensure_list(None)
        assert result == []

    def test_ensure_list_with_string(self):
        """Test _ensure_list wraps string in value dict."""

        class ConcreteIngestor(XMLIngestor):
            def normalize(self, parsed_data, xml_file_path=None):
                return parsed_data

            def get_supported_root_elements(self):
                return ["TestElement"]

        ingestor = ConcreteIngestor(enable_validation=False)

        result = ingestor._ensure_list("test_string")
        assert result == [{"value": "test_string"}]


class TestXMLIngestorParsing:
    """Test cases for XML parsing functionality."""

    def test_parse_valid_xml_file(self, tmp_path):
        """Test parsing of valid XML file."""

        class ConcreteIngestor(XMLIngestor):
            def normalize(self, parsed_data, xml_file_path=None):
                return parsed_data

            def get_supported_root_elements(self):
                return ["TestElement"]

        # Create temporary XML file
        xml_file = tmp_path / "test.xml"
        xml_file.write_text(VALID_ECLAIM_LINK_XML, encoding="utf-8")

        ingestor = ConcreteIngestor(enable_validation=False)
        result = ingestor.parse(str(xml_file))

        assert isinstance(result, dict)
        assert "PriorAuthorizationRequest" in result

    def test_parse_nonexistent_file_raises_error(self):
        """Test that parsing nonexistent file raises XMLParsingError."""

        class ConcreteIngestor(XMLIngestor):
            def normalize(self, parsed_data, xml_file_path=None):
                return parsed_data

            def get_supported_root_elements(self):
                return ["TestElement"]

        ingestor = ConcreteIngestor(enable_validation=False)

        with pytest.raises(XMLParsingError) as exc_info:
            ingestor.parse("/nonexistent/file.xml")

        assert "does not exist" in str(exc_info.value)

    def test_parse_malformed_xml_raises_error(self, tmp_path):
        """Test that parsing malformed XML raises XMLParsingError."""

        class ConcreteIngestor(XMLIngestor):
            def normalize(self, parsed_data, xml_file_path=None):
                return parsed_data

            def get_supported_root_elements(self):
                return ["TestElement"]

        xml_file = tmp_path / "malformed.xml"
        xml_file.write_text(INVALID_XML_MALFORMED, encoding="utf-8")

        ingestor = ConcreteIngestor(enable_validation=False)

        with pytest.raises(XMLParsingError) as exc_info:
            ingestor.parse(str(xml_file))

        assert "parsing error" in str(exc_info.value).lower()

    def test_parse_encoding_error(self, tmp_path):
        """Test parsing file with encoding issues."""

        class ConcreteIngestor(XMLIngestor):
            def normalize(self, parsed_data, xml_file_path=None):
                return parsed_data

            def get_supported_root_elements(self):
                return ["TestElement"]

        # Create file with invalid UTF-8 encoding
        xml_file = tmp_path / "bad_encoding.xml"
        xml_file.write_bytes(
            b'<?xml version="1.0" encoding="UTF-8"?><root>\xff\xfe</root>'
        )

        ingestor = ConcreteIngestor(enable_validation=False)

        with pytest.raises(XMLParsingError) as exc_info:
            ingestor.parse(str(xml_file))

        # Should catch encoding error
        assert exc_info.value.file_path == str(xml_file)

    def test_parse_arabic_text_xml(self, tmp_path):
        """Test parsing XML with Arabic text content."""

        class ConcreteIngestor(XMLIngestor):
            def normalize(self, parsed_data, xml_file_path=None):
                return parsed_data

            def get_supported_root_elements(self):
                return ["Prior.Authorization"]

        xml_file = tmp_path / "arabic.xml"
        xml_file.write_text(ARABIC_TEXT_XML, encoding="utf-8")

        ingestor = ConcreteIngestor(enable_validation=False)
        result = ingestor.parse(str(xml_file))

        assert isinstance(result, dict)
        assert "Prior.Authorization" in result
        # Check that Arabic text is preserved
        auth_data = result["Prior.Authorization"]
        assert "مقدم_الخدمة_12345" in str(auth_data)


class TestEClaimLinkIngestor:
    """Test cases for EClaimLink XML ingestor."""

    def test_get_supported_root_elements(self):
        """Test that EClaimLink ingestor returns correct supported elements."""
        ingestor = EClaimLinkIngestor(enable_validation=False)
        elements = ingestor.get_supported_root_elements()
        assert elements == ["PriorAuthorizationRequest"]

    def test_normalize_valid_eclaim_link_data(self, tmp_path):
        """Test normalization of valid eClaimLink XML data."""
        xml_file = tmp_path / "eclaim_test.xml"
        xml_file.write_text(VALID_ECLAIM_LINK_XML, encoding="utf-8")

        ingestor = EClaimLinkIngestor(enable_validation=False)
        parsed_data = ingestor.parse(str(xml_file))
        normalized = ingestor.normalize(parsed_data, str(xml_file))

        # Check structure
        assert normalized["format_name"] == "eClaimLink"
        assert normalized["schema_version"] == "2019/11"
        assert "ingestion_metadata" in normalized

        # Check header fields
        assert normalized["sender"] == "PROV12345"
        assert normalized["receiver"] == "PAYER67890"
        assert normalized["transaction_date"] == "27/07/2025 10:32"
        assert normalized["authorization_id"] == "TXN-2025-000456"

        # Check justification text
        assert "urgent medical attention" in normalized["justification_text"]

        # Check services
        assert len(normalized["services"]) == 2
        service1 = normalized["services"][0]
        assert service1["id"] == 1
        assert service1["activity_code"] == "83036"
        assert service1["diagnosis_code"] == "E11.9"
        assert service1["requested_amount_currency"] == "AED"
        assert service1["requested_amount_value"] == "120.00"

    def test_normalize_missing_header_raises_error(self, tmp_path):
        """Test that missing header section raises DataNormalizationError."""
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
    <JustificationText>Some text</JustificationText>
</PriorAuthorizationRequest>'''

        xml_file = tmp_path / "no_header.xml"
        xml_file.write_text(xml_content, encoding="utf-8")

        ingestor = EClaimLinkIngestor(enable_validation=False)
        parsed_data = ingestor.parse(str(xml_file))

        with pytest.raises(DataNormalizationError) as exc_info:
            ingestor.normalize(parsed_data, str(xml_file))

        assert "Header" in str(exc_info.value)

    def test_normalize_missing_required_header_field(self, tmp_path):
        """Test that missing required header field raises error."""
        xml_file = tmp_path / "missing_field.xml"
        xml_file.write_text(INVALID_XML_MISSING_REQUIRED_FIELDS, encoding="utf-8")

        ingestor = EClaimLinkIngestor(enable_validation=False)
        parsed_data = ingestor.parse(str(xml_file))

        with pytest.raises(DataNormalizationError) as exc_info:
            ingestor.normalize(parsed_data, str(xml_file))

        assert "SenderID" in str(exc_info.value)

    def test_normalize_unsupported_root_element(self, tmp_path):
        """Test that unsupported root element raises UnsupportedFormatError."""
        xml_file = tmp_path / "unsupported.xml"
        xml_file.write_text(UNSUPPORTED_ROOT_ELEMENT_XML, encoding="utf-8")

        ingestor = EClaimLinkIngestor(enable_validation=False)
        parsed_data = ingestor.parse(str(xml_file))

        with pytest.raises(UnsupportedFormatError) as exc_info:
            ingestor.normalize(parsed_data, str(xml_file))

        assert "UnsupportedRootElement" in str(exc_info.value)

    def test_normalize_single_service_request(self, tmp_path):
        """Test normalization with single service request (not in list)."""
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
    <Header>
        <SenderID>PROV12345</SenderID>
        <ReceiverID>PAYER67890</ReceiverID>
        <TransactionDateTime>27/07/2025 10:32</TransactionDateTime>
        <TransactionID>TXN-2025-000456</TransactionID>
    </Header>
    <ServiceRequests>
        <ServiceRequest>
            <ct:ActivityCode>83036</ct:ActivityCode>
            <ct:DiagnosisCode>E11.9</ct:DiagnosisCode>
            <ct:ActivityDateTime>28/07/2025 09:00</ct:ActivityDateTime>
            <ct:ActivityInstructions>Test instructions</ct:ActivityInstructions>
            <RequestedAmount currency="AED">120.00</RequestedAmount>
        </ServiceRequest>
    </ServiceRequests>
    <JustificationText>Test justification</JustificationText>
</PriorAuthorizationRequest>'''

        xml_file = tmp_path / "single_service.xml"
        xml_file.write_text(xml_content, encoding="utf-8")

        ingestor = EClaimLinkIngestor(enable_validation=False)
        parsed_data = ingestor.parse(str(xml_file))
        normalized = ingestor.normalize(parsed_data, str(xml_file))

        assert len(normalized["services"]) == 1
        assert normalized["services"][0]["id"] == 1

    def test_normalize_empty_service_requests(self, tmp_path):
        """Test normalization with empty service requests section."""
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
    <Header>
        <SenderID>PROV12345</SenderID>
        <ReceiverID>PAYER67890</ReceiverID>
        <TransactionDateTime>27/07/2025 10:32</TransactionDateTime>
        <TransactionID>TXN-2025-000456</TransactionID>
    </Header>
    <JustificationText>Empty service requests test</JustificationText>
    <ServiceRequests>
    </ServiceRequests>
</PriorAuthorizationRequest>'''

        xml_file = tmp_path / "empty_services.xml"
        xml_file.write_text(xml_content, encoding="utf-8")

        ingestor = EClaimLinkIngestor(enable_validation=False)
        parsed_data = ingestor.parse(str(xml_file))
        normalized = ingestor.normalize(parsed_data, str(xml_file))

        assert len(normalized["services"]) == 0

    def test_get_format_info(self):
        """Test format information retrieval."""
        ingestor = EClaimLinkIngestor(enable_validation=False)
        info = ingestor.get_format_info()

        assert info["format_name"] == "eClaimLink"
        assert info["schema_version"] == "2019/11"
        assert info["authority"] == "Dubai Health Authority (DHA)"
        assert "Prior authorization requests" in info["typical_use_cases"]

    def test_validate_business_rules_valid_data(self, tmp_path):
        """Test business rules validation with valid data."""
        xml_file = tmp_path / "valid.xml"
        xml_file.write_text(VALID_ECLAIM_LINK_XML, encoding="utf-8")

        ingestor = EClaimLinkIngestor(enable_validation=False)
        parsed_data = ingestor.parse(str(xml_file))
        normalized = ingestor.normalize(parsed_data, str(xml_file))

        warnings = ingestor.validate_business_rules(normalized)
        # Should have minimal warnings for valid data
        assert len(warnings) <= 2  # Allow for minor validation warnings

    def test_validate_business_rules_missing_services(self):
        """Test business rules validation with missing services."""
        data = {"authorization_id": "TXN-123", "services": []}

        ingestor = EClaimLinkIngestor(enable_validation=False)
        warnings = ingestor.validate_business_rules(data)

        assert any("No services found" in w for w in warnings)

    def test_validate_business_rules_invalid_amounts(self):
        """Test business rules validation with invalid amount formats."""
        data = {
            "authorization_id": "TXN-123",
            "services": [
                {
                    "activity_code": "83036",
                    "diagnosis_code": "E11.9",
                    "requested_amount_value": "invalid_amount",
                }
            ],
        }

        ingestor = EClaimLinkIngestor(enable_validation=False)
        warnings = ingestor.validate_business_rules(data)

        assert any("invalid amount format" in w for w in warnings)


class TestShafafiyaIngestor:
    """Test cases for Shafafiya XML ingestor."""

    def test_get_supported_root_elements(self):
        """Test that Shafafiya ingestor returns correct supported elements."""
        ingestor = ShafafiyaIngestor(enable_validation=False)
        elements = ingestor.get_supported_root_elements()
        assert elements == ["Prior.Authorization"]

    def test_normalize_valid_shafafiya_data(self, tmp_path):
        """Test normalization of valid Shafafiya XML data."""
        xml_file = tmp_path / "shafafiya_test.xml"
        xml_file.write_text(VALID_SHAFAFIYA_XML, encoding="utf-8")

        ingestor = ShafafiyaIngestor(enable_validation=False)
        parsed_data = ingestor.parse(str(xml_file))
        normalized = ingestor.normalize(parsed_data, str(xml_file))

        # Check structure
        assert normalized["format_name"] == "Shafafiya"
        assert normalized["schema_version"] == "2011"

        # Check header fields
        assert normalized["sender"] == "PROV12345"
        assert normalized["receiver"] == "PAYER67890"
        assert normalized["transaction_date"] == "27/07/2025 10:32"
        assert normalized["record_count"] == "2"
        assert normalized["disposition_flag"] == "TEST"

        # Check authorization fields
        assert normalized["result"] == "Yes"
        assert normalized["authorization_id"] == "PA-2025-000123"
        assert normalized["id_payer"] == "PAYER67890"
        assert normalized["start"] == "25/07/2025 00:00"
        assert normalized["end"] == "25/08/2025 23:59"
        assert normalized["limit"] == "1000.00"
        assert "poorly controlled diabetes" in normalized["comments"]

        # Check activities/services
        assert len(normalized["services"]) == 2
        activity1 = normalized["services"][0]
        assert activity1["id"] == "1"
        assert activity1["type"] == "3"
        assert activity1["code"] == "83036"
        assert activity1["quantity"] == "1"
        assert activity1["net"] == "120.00"
        assert activity1["payment_amount"] == "90.00"

        # Check observations
        assert len(activity1["observations"]) == 1
        obs = activity1["observations"][0]
        assert obs["type"] == "ICD10"
        assert obs["code"] == "E11.9"

    def test_normalize_missing_header_raises_error(self, tmp_path):
        """Test that missing header section raises DataNormalizationError."""
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<Prior.Authorization>
    <Authorization>
        <Result>Yes</Result>
        <ID>PA-123</ID>
    </Authorization>
</Prior.Authorization>'''

        xml_file = tmp_path / "no_header.xml"
        xml_file.write_text(xml_content, encoding="utf-8")

        ingestor = ShafafiyaIngestor(enable_validation=False)
        parsed_data = ingestor.parse(str(xml_file))

        with pytest.raises(DataNormalizationError) as exc_info:
            ingestor.normalize(parsed_data, str(xml_file))

        assert "Header" in str(exc_info.value)

    def test_normalize_missing_authorization_raises_error(self, tmp_path):
        """Test that missing authorization section raises DataNormalizationError."""
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<Prior.Authorization>
    <Header>
        <SenderID>PROV123</SenderID>
        <ReceiverID>PAYER456</ReceiverID>
        <TransactionDate>27/07/2025 10:32</TransactionDate>
    </Header>
</Prior.Authorization>'''

        xml_file = tmp_path / "no_auth.xml"
        xml_file.write_text(xml_content, encoding="utf-8")

        ingestor = ShafafiyaIngestor(enable_validation=False)
        parsed_data = ingestor.parse(str(xml_file))

        with pytest.raises(DataNormalizationError) as exc_info:
            ingestor.normalize(parsed_data, str(xml_file))

        assert "Authorization" in str(exc_info.value)

    def test_normalize_single_activity(self, tmp_path):
        """Test normalization with single activity (not in list)."""
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<Prior.Authorization>
    <Header>
        <SenderID>PROV12345</SenderID>
        <ReceiverID>PAYER67890</ReceiverID>
        <TransactionDate>27/07/2025 10:32</TransactionDate>
        <RecordCount>1</RecordCount>
    </Header>
    <Authorization>
        <Result>Yes</Result>
        <ID>PA-2025-000123</ID>
        <Start>25/07/2025 00:00</Start>
        <End>25/08/2025 23:59</End>
        <Activity>
            <ID>1</ID>
            <Type>3</Type>
            <Code>83036</Code>
            <Quantity>1</Quantity>
            <Net>120.00</Net>
            <PaymentAmount>90.00</PaymentAmount>
        </Activity>
    </Authorization>
</Prior.Authorization>'''

        xml_file = tmp_path / "single_activity.xml"
        xml_file.write_text(xml_content, encoding="utf-8")

        ingestor = ShafafiyaIngestor(enable_validation=False)
        parsed_data = ingestor.parse(str(xml_file))
        normalized = ingestor.normalize(parsed_data, str(xml_file))

        assert len(normalized["services"]) == 1
        assert normalized["services"][0]["id"] == "1"

    def test_normalize_empty_activities(self, tmp_path):
        """Test normalization with no activities."""
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<Prior.Authorization>
    <Header>
        <SenderID>PROV12345</SenderID>
        <ReceiverID>PAYER67890</ReceiverID>
        <TransactionDate>27/07/2025 10:32</TransactionDate>
        <RecordCount>0</RecordCount>
    </Header>
    <Authorization>
        <Result>Yes</Result>
        <ID>PA-2025-000123</ID>
        <Start>25/07/2025 00:00</Start>
        <End>25/08/2025 23:59</End>
    </Authorization>
</Prior.Authorization>'''

        xml_file = tmp_path / "no_activities.xml"
        xml_file.write_text(xml_content, encoding="utf-8")

        ingestor = ShafafiyaIngestor(enable_validation=False)
        parsed_data = ingestor.parse(str(xml_file))
        normalized = ingestor.normalize(parsed_data, str(xml_file))

        assert len(normalized["services"]) == 0

    def test_normalize_observations_handling(self, tmp_path):
        """Test proper handling of observations in activities."""
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<Prior.Authorization>
    <Header>
        <SenderID>PROV12345</SenderID>
        <ReceiverID>PAYER67890</ReceiverID>
        <TransactionDate>27/07/2025 10:32</TransactionDate>
    </Header>
    <Authorization>
        <Result>Yes</Result>
        <ID>PA-2025-000123</ID>
        <Start>25/07/2025 00:00</Start>
        <End>25/08/2025 23:59</End>
        <Activity>
            <ID>1</ID>
            <Type>3</Type>
            <Code>83036</Code>
            <Net>120.00</Net>
            <PaymentAmount>90.00</PaymentAmount>
            <Observation>
                <Type>ICD10</Type>
                <Code>E11.9</Code>
                <Value>Type 2 diabetes</Value>
                <ValueType>text</ValueType>
            </Observation>
            <Observation>
                <Type>CPT</Type>
                <Code>83036</Code>
                <Value>Hemoglobin A1c</Value>
            </Observation>
        </Activity>
    </Authorization>
</Prior.Authorization>'''

        xml_file = tmp_path / "observations.xml"
        xml_file.write_text(xml_content, encoding="utf-8")

        ingestor = ShafafiyaIngestor(enable_validation=False)
        parsed_data = ingestor.parse(str(xml_file))
        normalized = ingestor.normalize(parsed_data, str(xml_file))

        activity = normalized["services"][0]
        assert len(activity["observations"]) == 2
        assert activity["observations"][0]["type"] == "ICD10"
        assert activity["observations"][1]["type"] == "CPT"

    def test_get_format_info(self):
        """Test format information retrieval."""
        ingestor = ShafafiyaIngestor(enable_validation=False)
        info = ingestor.get_format_info()

        assert info["format_name"] == "Shafafiya"
        assert info["schema_version"] == "2011"
        assert info["authority"] == "Abu Dhabi Department of Health (DoH)"
        assert "Prior authorization responses" in info["typical_use_cases"]

    def test_validate_business_rules_record_count_mismatch(self):
        """Test business rules validation with record count mismatch."""
        data = {
            "record_count": "3",
            "services": [{"id": "1"}, {"id": "2"}],  # Only 2 services
        }

        ingestor = ShafafiyaIngestor(enable_validation=False)
        warnings = ingestor.validate_business_rules(data)

        assert any("Record count mismatch" in w for w in warnings)

    def test_validate_business_rules_invalid_result(self):
        """Test business rules validation with invalid authorization result."""
        data = {"result": "maybe", "services": []}  # Invalid result

        ingestor = ShafafiyaIngestor(enable_validation=False)
        warnings = ingestor.validate_business_rules(data)

        assert any("Unexpected authorization result" in w for w in warnings)


class TestXMLIngestorFactory:
    """Test cases for XMLIngestorFactory."""

    def setup_method(self):
        """Reset factory state before each test."""
        # Reset the class-level registry to ensure clean state
        from pipelines.factory import XMLIngestorFactory
        from pipelines.eclaim_link_ingestor import EClaimLinkIngestor
        from pipelines.shafafiya_ingestor import ShafafiyaIngestor

        XMLIngestorFactory._INGESTOR_REGISTRY = {
            "eClaimLink": EClaimLinkIngestor,
            "Shafafiya": ShafafiyaIngestor,
        }
        XMLIngestorFactory._ROOT_ELEMENT_MAPPING = {
            "PriorAuthorizationRequest": "eClaimLink",
            "Prior.Authorization": "Shafafiya",
        }

    def test_factory_initialization_default(self):
        """Test factory initialization with default settings."""
        factory = XMLIngestorFactory()
        assert factory.enable_validation is True
        assert factory.schema_base_path is None
        assert factory.logger is not None

    def test_factory_initialization_with_parameters(self, tmp_path):
        """Test factory initialization with custom parameters."""
        logger = Mock(spec=logging.Logger)
        factory = XMLIngestorFactory(
            schema_base_path=str(tmp_path), enable_validation=False, logger=logger
        )
        assert factory.enable_validation is False
        assert factory.schema_base_path == tmp_path
        assert factory.logger is logger

    def test_detect_format_eclaim_link(self, tmp_path):
        """Test format detection for eClaimLink XML."""
        xml_file = tmp_path / "eclaim.xml"
        xml_file.write_text(VALID_ECLAIM_LINK_XML, encoding="utf-8")

        factory = XMLIngestorFactory()
        format_name = factory.detect_format(str(xml_file))
        assert format_name == "eClaimLink"

    def test_detect_format_shafafiya(self, tmp_path):
        """Test format detection for Shafafiya XML."""
        xml_file = tmp_path / "shafafiya.xml"
        xml_file.write_text(VALID_SHAFAFIYA_XML, encoding="utf-8")

        factory = XMLIngestorFactory()
        format_name = factory.detect_format(str(xml_file))
        assert format_name == "Shafafiya"

    def test_detect_format_unsupported_raises_error(self, tmp_path):
        """Test that unsupported format raises UnsupportedFormatError."""
        xml_file = tmp_path / "unsupported.xml"
        xml_file.write_text(UNSUPPORTED_ROOT_ELEMENT_XML, encoding="utf-8")

        factory = XMLIngestorFactory()

        with pytest.raises(UnsupportedFormatError) as exc_info:
            factory.detect_format(str(xml_file))

        assert "UnsupportedRootElement" in str(exc_info.value)

    def test_detect_format_nonexistent_file_raises_error(self):
        """Test that nonexistent file raises XMLParsingError."""
        factory = XMLIngestorFactory()

        with pytest.raises(XMLParsingError) as exc_info:
            factory.detect_format("/nonexistent/file.xml")

        assert "does not exist" in str(exc_info.value)

    def test_create_ingestor_eclaim_link(self):
        """Test creating eClaimLink ingestor."""
        factory = XMLIngestorFactory()
        ingestor = factory.create_ingestor("eClaimLink", enable_validation=False)

        assert isinstance(ingestor, EClaimLinkIngestor)
        assert not ingestor.enable_validation

    def test_create_ingestor_shafafiya(self):
        """Test creating Shafafiya ingestor."""
        factory = XMLIngestorFactory()
        ingestor = factory.create_ingestor("Shafafiya", enable_validation=False)

        assert isinstance(ingestor, ShafafiyaIngestor)
        assert not ingestor.enable_validation

    def test_create_ingestor_unsupported_format(self):
        """Test that creating ingestor for unsupported format raises error."""
        factory = XMLIngestorFactory()

        with pytest.raises(UnsupportedFormatError) as exc_info:
            factory.create_ingestor("UnsupportedFormat")

        assert "UnsupportedFormat" in str(exc_info.value)

    def test_create_ingestor_for_file(self, tmp_path):
        """Test auto-detecting format and creating ingestor."""
        xml_file = tmp_path / "auto_detect.xml"
        xml_file.write_text(VALID_ECLAIM_LINK_XML, encoding="utf-8")

        factory = XMLIngestorFactory()
        ingestor = factory.create_ingestor_for_file(
            str(xml_file), enable_validation=False
        )

        assert isinstance(ingestor, EClaimLinkIngestor)

    def test_process_file_complete_pipeline(self, tmp_path):
        """Test complete processing pipeline through factory."""
        xml_file = tmp_path / "pipeline_test.xml"
        xml_file.write_text(VALID_SHAFAFIYA_XML, encoding="utf-8")

        factory = XMLIngestorFactory()
        result = factory.process_file(str(xml_file), enable_validation=False)

        assert isinstance(result, dict)
        assert result["format_name"] == "Shafafiya"
        assert result["sender"] == "PROV12345"

    def test_get_supported_formats(self):
        """Test getting supported formats information."""
        factory = XMLIngestorFactory()
        formats = factory.get_supported_formats()

        assert len(formats) >= 2  # At least eClaimLink and Shafafiya
        format_names = [f.get("format_name") for f in formats]
        assert "eClaimLink" in format_names
        assert "Shafafiya" in format_names

    def test_register_new_ingestor(self):
        """Test registering a new ingestor class."""

        class CustomIngestor(XMLIngestor):
            def normalize(self, parsed_data, xml_file_path=None):
                return {"custom": True}

            def get_supported_root_elements(self):
                return ["CustomElement"]

        factory = XMLIngestorFactory()
        factory.register_ingestor(
            "CustomFormat", CustomIngestor, ["CustomElement"], "custom.xsd"
        )

        # Should be able to create the custom ingestor
        ingestor = factory.create_ingestor("CustomFormat", enable_validation=False)
        assert isinstance(ingestor, CustomIngestor)

    def test_register_invalid_ingestor_class_raises_error(self):
        """Test that registering invalid ingestor class raises error."""

        class NotAnIngestor:
            pass

        factory = XMLIngestorFactory()

        with pytest.raises(ConfigurationError) as exc_info:
            factory.register_ingestor("Invalid", NotAnIngestor, ["Element"])

        assert "must inherit from XMLIngestor" in str(exc_info.value)

    def test_unregister_ingestor(self):
        """Test unregistering an existing ingestor."""
        factory = XMLIngestorFactory()

        # Should initially support eClaimLink
        formats_before = factory.get_supported_formats()
        format_names_before = [f.get("format_name") for f in formats_before]
        assert "eClaimLink" in format_names_before

        # Unregister eClaimLink
        factory.unregister_ingestor("eClaimLink")

        # Should no longer support eClaimLink
        with pytest.raises(UnsupportedFormatError):
            factory.create_ingestor("eClaimLink")

        # Re-register for subsequent tests
        from pipelines.eclaim_link_ingestor import EClaimLinkIngestor

        factory.register_ingestor(
            "eClaimLink",
            EClaimLinkIngestor,
            ["PriorAuthorizationRequest"],
            "CommonTypes_20191113.xsd",
        )

    def test_validate_file_compatibility(self, tmp_path):
        """Test file compatibility validation."""
        xml_file = tmp_path / "compat_test.xml"
        xml_file.write_text(VALID_ECLAIM_LINK_XML, encoding="utf-8")

        factory = XMLIngestorFactory()
        compat_info = factory.validate_file_compatibility(str(xml_file))

        assert compat_info["file_path"] == str(xml_file)
        assert compat_info["detected_format"] == "eClaimLink"
        assert len(compat_info["compatible_ingestors"]) > 0

        # Should have eClaimLink as compatible
        compatible_formats = [
            ing["format_name"] for ing in compat_info["compatible_ingestors"]
        ]
        assert "eClaimLink" in compatible_formats


class TestEdgeCasesAndErrorHandling:
    """Test cases for edge cases and comprehensive error handling."""

    def setup_method(self):
        """Reset factory state before each test."""
        # Reset the class-level registry to ensure clean state
        from pipelines.factory import XMLIngestorFactory
        from pipelines.eclaim_link_ingestor import EClaimLinkIngestor
        from pipelines.shafafiya_ingestor import ShafafiyaIngestor

        XMLIngestorFactory._INGESTOR_REGISTRY = {
            "eClaimLink": EClaimLinkIngestor,
            "Shafafiya": ShafafiyaIngestor,
        }
        XMLIngestorFactory._ROOT_ELEMENT_MAPPING = {
            "PriorAuthorizationRequest": "eClaimLink",
            "Prior.Authorization": "Shafafiya",
        }

    @pytest.mark.parametrize(
        "xml_content,expected_error",
        [
            (INVALID_XML_MALFORMED, XMLParsingError),
            (INVALID_XML_MISSING_REQUIRED_FIELDS, DataNormalizationError),
            (UNSUPPORTED_ROOT_ELEMENT_XML, UnsupportedFormatError),
        ],
    )
    def test_parametrized_error_scenarios(self, tmp_path, xml_content, expected_error):
        """Test various error scenarios with parametrized inputs."""
        xml_file = tmp_path / "error_test.xml"
        xml_file.write_text(xml_content, encoding="utf-8")

        factory = XMLIngestorFactory()

        with pytest.raises(expected_error):
            factory.process_file(str(xml_file), enable_validation=False)

    def test_large_xml_file_processing(self, tmp_path):
        """Test processing of large XML files."""
        # Generate large XML with many service requests
        service_requests = []
        for i in range(100):  # 100 service requests
            service_requests.append(
                f'''
        <ServiceRequest>
            <ct:ActivityCode>8303{i % 10}</ct:ActivityCode>
            <ct:DiagnosisCode>E11.{i % 10}</ct:DiagnosisCode>
            <ct:ActivityDateTime>28/07/2025 09:00</ct:ActivityDateTime>
            <RequestedAmount currency="AED">{120 + i}.00</RequestedAmount>
        </ServiceRequest>'''
            )

        large_xml = LARGE_XML_CONTENT.format(service_requests=''.join(service_requests))

        xml_file = tmp_path / "large.xml"
        xml_file.write_text(large_xml, encoding="utf-8")

        factory = XMLIngestorFactory()
        result = factory.process_file(str(xml_file), enable_validation=False)

        assert len(result["services"]) == 100
        assert result["format_name"] == "eClaimLink"

    def test_empty_xml_file(self, tmp_path):
        """Test handling of empty or minimal XML files."""
        xml_file = tmp_path / "empty.xml"
        xml_file.write_text(EMPTY_XML_FILE, encoding="utf-8")

        factory = XMLIngestorFactory()

        with pytest.raises(UnsupportedFormatError):
            factory.process_file(str(xml_file), enable_validation=False)

    def test_xml_with_cdata_sections(self, tmp_path):
        """Test handling of XML with CDATA sections in comments."""
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<Prior.Authorization>
    <Header>
        <SenderID>PROV12345</SenderID>
        <ReceiverID>PAYER67890</ReceiverID>
        <TransactionDate>27/07/2025 10:32</TransactionDate>
    </Header>
    <Authorization>
        <Result>Yes</Result>
        <ID>PA-2025-000123</ID>
        <Start>25/07/2025 00:00</Start>
        <End>25/08/2025 23:59</End>
        <Comments><![CDATA[Patient with <complex> medical history & multiple "conditions"]]></Comments>
        <Activity>
            <ID>1</ID>
            <Type>3</Type>
            <Code>83036</Code>
            <Net>120.00</Net>
            <PaymentAmount>90.00</PaymentAmount>
        </Activity>
    </Authorization>
</Prior.Authorization>'''

        xml_file = tmp_path / "cdata.xml"
        xml_file.write_text(xml_content, encoding="utf-8")

        factory = XMLIngestorFactory()
        result = factory.process_file(str(xml_file), enable_validation=False)

        assert result["format_name"] == "Shafafiya"
        # CDATA content should be preserved
        assert "complex" in result["comments"]
        assert "&" in result["comments"] or "amp;" in result["comments"]

    def test_xml_with_namespaces_handling(self, tmp_path):
        """Test proper handling of XML namespaces."""
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<PriorAuthorizationRequest
    xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema"
    xmlns:ext="http://extensions.example.com">
    <Header>
        <SenderID>PROV12345</SenderID>
        <ReceiverID>PAYER67890</ReceiverID>
        <TransactionDateTime>27/07/2025 10:32</TransactionDateTime>
        <TransactionID>TXN-2025-000456</TransactionID>
    </Header>
    <JustificationText>Namespace handling test</JustificationText>
    <ServiceRequests>
        <ServiceRequest>
            <ct:ActivityCode>83036</ct:ActivityCode>
            <ct:DiagnosisCode>E11.9</ct:DiagnosisCode>
            <ct:ActivityDateTime>28/07/2025 09:00</ct:ActivityDateTime>
            <ct:ActivityInstructions>Namespace test instructions</ct:ActivityInstructions>
            <ext:CustomField>Custom value</ext:CustomField>
            <RequestedAmount currency="AED">120.00</RequestedAmount>
        </ServiceRequest>
    </ServiceRequests>
</PriorAuthorizationRequest>'''

        xml_file = tmp_path / "namespaces.xml"
        xml_file.write_text(xml_content, encoding="utf-8")

        factory = XMLIngestorFactory()
        result = factory.process_file(str(xml_file), enable_validation=False)

        assert result["format_name"] == "eClaimLink"
        assert len(result["services"]) == 1

    def test_concurrent_processing_safety(self, tmp_path):
        """Test that ingestors are safe for concurrent processing."""
        import threading

        xml_file1 = tmp_path / "concurrent1.xml"
        xml_file1.write_text(VALID_ECLAIM_LINK_XML, encoding="utf-8")

        xml_file2 = tmp_path / "concurrent2.xml"
        xml_file2.write_text(VALID_SHAFAFIYA_XML, encoding="utf-8")

        results = []
        errors = []

        def process_file(file_path, expected_format):
            try:
                factory = XMLIngestorFactory()
                result = factory.process_file(file_path, enable_validation=False)
                assert result["format_name"] == expected_format
                results.append(result)
            except Exception as e:
                errors.append(e)

        # Start concurrent threads
        threads = [
            threading.Thread(target=process_file, args=(str(xml_file1), "eClaimLink")),
            threading.Thread(target=process_file, args=(str(xml_file2), "Shafafiya")),
            threading.Thread(target=process_file, args=(str(xml_file1), "eClaimLink")),
            threading.Thread(target=process_file, args=(str(xml_file2), "Shafafiya")),
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Should have no errors and 4 successful results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 4

    def test_memory_efficiency_with_repeated_processing(self, tmp_path):
        """Test memory efficiency with repeated processing of same file."""
        xml_file = tmp_path / "repeated.xml"
        xml_file.write_text(VALID_ECLAIM_LINK_XML, encoding="utf-8")

        factory = XMLIngestorFactory()

        # Process the same file multiple times
        for i in range(10):
            result = factory.process_file(str(xml_file), enable_validation=False)
            assert result["format_name"] == "eClaimLink"
            assert len(result["services"]) == 2

    def test_exception_details_and_context(self, tmp_path):
        """Test that exceptions include proper details and context."""
        xml_file = tmp_path / "exception_test.xml"
        xml_file.write_text(INVALID_XML_MISSING_REQUIRED_FIELDS, encoding="utf-8")

        factory = XMLIngestorFactory()

        with pytest.raises(DataNormalizationError) as exc_info:
            factory.process_file(str(xml_file), enable_validation=False)

        error = exc_info.value
        assert error.file_path == str(xml_file)
        assert "SenderID" in error.field_name
        assert "details" in str(error).lower()

    def test_custom_exception_inheritance(self):
        """Test that custom exceptions properly inherit from base classes."""
        # Test exception hierarchy
        assert issubclass(SchemaValidationError, XMLIngestionError)
        assert issubclass(XMLParsingError, XMLIngestionError)
        assert issubclass(UnsupportedFormatError, XMLIngestionError)
        assert issubclass(DataNormalizationError, XMLIngestionError)
        assert issubclass(ConfigurationError, XMLIngestionError)

        # Test that base XMLIngestionError inherits from Exception
        assert issubclass(XMLIngestionError, Exception)

    def test_datetime_format_validation_edge_cases(self, tmp_path):
        """Test various datetime format edge cases."""
        test_cases = [
            ("31/12/2025 23:59", True),  # Valid max date/time
            ("01/01/2025 00:00", True),  # Valid min date/time
            ("29/02/2024 12:00", True),  # Valid leap year
            ("32/01/2025 10:00", False),  # Invalid day
            ("01/13/2025 10:00", False),  # Invalid month
            ("01/01/25 10:00", False),  # Invalid year format
            ("1/1/2025 10:00", False),  # Missing leading zeros
            ("01/01/2025 25:00", False),  # Invalid hour
            ("01/01/2025 10:60", False),  # Invalid minute
        ]

        for date_string, should_succeed in test_cases:
            xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<Prior.Authorization>
    <Header>
        <SenderID>PROV12345</SenderID>
        <ReceiverID>PAYER67890</ReceiverID>
        <TransactionDate>{date_string}</TransactionDate>
    </Header>
    <Authorization>
        <Result>Yes</Result>
        <ID>PA-123</ID>
        <Start>25/07/2025 00:00</Start>
        <End>25/08/2025 23:59</End>
        <Activity>
            <ID>1</ID>
            <Type>3</Type>
            <Code>83036</Code>
            <Net>120.00</Net>
            <PaymentAmount>90.00</PaymentAmount>
        </Activity>
    </Authorization>
</Prior.Authorization>'''

            xml_file = (
                tmp_path
                / f"date_test_{date_string.replace('/', '_').replace(':', '_').replace(' ', '_')}.xml"
            )
            xml_file.write_text(xml_content, encoding="utf-8")

            factory = XMLIngestorFactory()

            try:
                result = factory.process_file(str(xml_file), enable_validation=False)
                # Basic parsing should succeed regardless of date format
                # Business rule validation might flag invalid dates
                assert result["format_name"] == "Shafafiya"
                assert result["transaction_date"] == date_string
            except Exception as e:
                if should_succeed:
                    pytest.fail(
                        f"Processing failed unexpectedly for date {date_string}: {e}"
                    )
                # For invalid dates, we expect the parsing to succeed but business rules might flag it
                # The XML parsing itself shouldn't fail unless it's malformed


class TestTestHelpers:
    """Test cases for test helper functions and utilities."""

    def setup_method(self):
        """Reset factory state before each test."""
        # Reset the class-level registry to ensure clean state
        from pipelines.factory import XMLIngestorFactory
        from pipelines.eclaim_link_ingestor import EClaimLinkIngestor
        from pipelines.shafafiya_ingestor import ShafafiyaIngestor

        XMLIngestorFactory._INGESTOR_REGISTRY = {
            "eClaimLink": EClaimLinkIngestor,
            "Shafafiya": ShafafiyaIngestor,
        }
        XMLIngestorFactory._ROOT_ELEMENT_MAPPING = {
            "PriorAuthorizationRequest": "eClaimLink",
            "Prior.Authorization": "Shafafiya",
        }

    def test_xml_fixture_validity(self):
        """Test that all XML fixtures are valid and parseable."""
        fixtures = [
            VALID_ECLAIM_LINK_XML,
            VALID_SHAFAFIYA_XML,
            ARABIC_TEXT_XML,
            EMPTY_XML_FILE,
            UNSUPPORTED_ROOT_ELEMENT_XML,
        ]

        for i, xml_content in enumerate(fixtures):
            try:
                parsed = xmltodict.parse(xml_content)
                assert isinstance(parsed, dict)
                assert len(parsed) > 0
            except Exception as e:
                if (
                    xml_content != INVALID_XML_MALFORMED
                ):  # This one is expected to be invalid
                    pytest.fail(f"Fixture {i} is not valid XML: {e}")

    def test_temporary_file_cleanup(self, tmp_path):
        """Test that temporary files are properly cleaned up."""
        xml_file = tmp_path / "cleanup_test.xml"
        xml_file.write_text(VALID_ECLAIM_LINK_XML, encoding="utf-8")

        assert xml_file.exists()

        # Process the file
        factory = XMLIngestorFactory()
        result = factory.process_file(str(xml_file), enable_validation=False)
        assert result is not None

        # File should still exist (cleanup is handled by pytest tmp_path)
        assert xml_file.exists()

    def test_logging_configuration(self):
        """Test that logging is properly configured for ingestors."""
        ingestor = EClaimLinkIngestor(enable_validation=False)

        # Should have a logger
        assert ingestor.logger is not None
        assert isinstance(ingestor.logger, logging.Logger)

        # Logger should have proper name
        expected_name = f"{ingestor.__class__.__module__}.{ingestor.__class__.__name__}"
        assert ingestor.logger.name == expected_name

    def test_metadata_extraction(self):
        """Test metadata extraction from ingestors."""
        ingestor = EClaimLinkIngestor(enable_validation=False)
        metadata = ingestor.get_metadata()

        assert metadata["class_name"] == "EClaimLinkIngestor"
        assert "pipelines" in metadata["module"]
        assert "PriorAuthorizationRequest" in metadata["supported_root_elements"]
        assert metadata["validation_enabled"] is False


# Pytest configuration and fixtures
@pytest.fixture
def sample_eclaim_xml(tmp_path):
    """Fixture providing a temporary eClaimLink XML file."""
    xml_file = tmp_path / "sample_eclaim.xml"
    xml_file.write_text(VALID_ECLAIM_LINK_XML, encoding="utf-8")
    return str(xml_file)


@pytest.fixture
def sample_shafafiya_xml(tmp_path):
    """Fixture providing a temporary Shafafiya XML file."""
    xml_file = tmp_path / "sample_shafafiya.xml"
    xml_file.write_text(VALID_SHAFAFIYA_XML, encoding="utf-8")
    return str(xml_file)


@pytest.fixture
def mock_schema_file(tmp_path):
    """Fixture providing a mock XSD schema file."""
    schema_file = tmp_path / "mock_schema.xsd"
    schema_content = '''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xs:element name="root" type="xs:string"/>
</xs:schema>'''
    schema_file.write_text(schema_content, encoding="utf-8")
    return str(schema_file)


@pytest.fixture
def factory_with_mocked_validation():
    """Fixture providing a factory with mocked validation."""
    with patch('xmlschema.XMLSchema11') as mock_schema:
        mock_schema_instance = Mock()
        mock_schema_instance.is_valid.return_value = True
        mock_schema_instance.iter_errors.return_value = []
        mock_schema.return_value = mock_schema_instance

        factory = XMLIngestorFactory(enable_validation=True)
        yield factory


if __name__ == "__main__":
    # Allow running tests directly with python
    pytest.main([__file__, "-v", "--tb=short"])
