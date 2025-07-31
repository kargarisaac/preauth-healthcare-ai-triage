"""
Unit tests for eClaimLink ingestor functionality.

This module tests the eClaimLink ingestor in isolation,
focusing on XML parsing, normalization, and error handling.
"""

import pytest
from pipelines.eclaim_link_ingestor import EClaimLinkIngestor
from pipelines.exceptions import UnsupportedFormatError, DataNormalizationError


class TestEClaimLinkIngestor:
    """Unit tests for eClaimLink ingestor."""

    @pytest.fixture
    def ingestor(self):
        """Create eClaimLink ingestor instance."""
        return EClaimLinkIngestor(enable_validation=False)

    @pytest.fixture
    def fhir_bundle_ingestor(self):
        """Create eClaimLink ingestor with FHIR Bundle output."""
        return EClaimLinkIngestor(enable_validation=False, output_format='fhir_bundle')

    def test_supported_root_elements(self, ingestor):
        """Test that correct root elements are supported."""
        supported = ingestor.get_supported_root_elements()
        assert 'PriorAuthorizationRequest' in supported
        assert len(supported) == 1

    def test_format_info(self, ingestor):
        """Test format information metadata."""
        info = ingestor.get_format_info()
        assert info['format_name'] == 'eClaimLink'
        assert info['schema_version'] == '2019/11'
        assert info['authority'] == 'Dubai Health Authority (DHA)'
        assert info['system'] == 'eClaimLink'

    def test_unsupported_root_element_error(self, ingestor):
        """Test error handling for unsupported root elements."""
        invalid_data = {'UnsupportedElement': {'data': 'test'}}

        with pytest.raises(UnsupportedFormatError) as exc_info:
            ingestor.normalize(invalid_data)

        assert 'UnsupportedElement' in str(exc_info.value)
        assert 'PriorAuthorizationRequest' in str(exc_info.value)

    def test_legacy_output_format(self, ingestor, test_data_factory):
        """Test legacy output format structure."""
        xml_data = test_data_factory.create_eclaim_xml()

        import xmltodict

        parsed_data = xmltodict.parse(xml_data)
        result = ingestor.normalize(parsed_data)

        # Validate legacy structure
        assert result['format_name'] == 'eClaimLink'
        assert result['schema_version'] == '2019/11'
        assert 'services' in result
        assert 'resourceType' not in result
        assert 'ingestion_metadata' in result

    def test_fhir_bundle_output_format(self, fhir_bundle_ingestor, test_data_factory):
        """Test FHIR Bundle output format structure."""
        xml_data = test_data_factory.create_eclaim_xml(
            justification="Patient with diabetes requiring HbA1c monitoring"
        )

        import xmltodict

        parsed_data = xmltodict.parse(xml_data)
        result = fhir_bundle_ingestor.normalize(parsed_data)

        # Validate FHIR Bundle structure
        assert result['resourceType'] == 'Bundle'
        assert result['type'] == 'collection'
        assert 'entry' in result
        assert 'total' in result
        assert len(result['entry']) == result['total']

    def test_business_rule_validation(self, ingestor, test_data_factory):
        """Test business rule validation."""
        # Create data with missing required fields
        xml_data = test_data_factory.create_eclaim_xml()
        import xmltodict

        parsed_data = xmltodict.parse(xml_data)
        result = ingestor.normalize(parsed_data)

        warnings = ingestor.validate_business_rules(result)
        assert isinstance(warnings, list)

    def test_service_request_normalization(self, ingestor, test_data_factory):
        """Test service request normalization."""
        services = [
            test_data_factory.create_service_request(1),
            test_data_factory.create_service_request(2),
        ]
        xml_data = test_data_factory.create_eclaim_xml(services=services)

        import xmltodict

        parsed_data = xmltodict.parse(xml_data)
        result = ingestor.normalize(parsed_data)

        assert len(result['services']) == 2
        for i, service in enumerate(result['services'], 1):
            assert service['id'] == i
            assert 'activity_code' in service
            assert 'diagnosis_code' in service
            assert service['source_format'] == 'eClaimLink'

    def test_minimal_data_handling(self, ingestor):
        """Test handling of minimal required data."""
        minimal_data = {
            'PriorAuthorizationRequest': {
                'Header': {
                    'SenderID': 'TEST123',
                    'ReceiverID': 'PAYER999',
                    'TransactionDateTime': '01/01/2025 12:00',
                    'TransactionID': 'MIN-001',
                },
                'ServiceRequests': {'ServiceRequest': {'ct:ActivityCode': '99213'}},
            }
        }

        result = ingestor.normalize(minimal_data)
        assert result['format_name'] == 'eClaimLink'
        assert len(result['services']) == 1

    def test_missing_header_error(self, ingestor):
        """Test error handling for missing header."""
        invalid_data = {'PriorAuthorizationRequest': {'ServiceRequests': {}}}

        with pytest.raises(DataNormalizationError) as exc_info:
            ingestor.normalize(invalid_data)

        assert 'Header' in str(exc_info.value)

    def test_amount_extraction(self, ingestor, test_data_factory):
        """Test amount extraction from service requests."""
        service = test_data_factory.create_service_request(
            1, RequestedAmount={'@currency': 'AED', '#text': '150.50'}
        )
        xml_data = test_data_factory.create_eclaim_xml(services=[service])

        import xmltodict

        parsed_data = xmltodict.parse(xml_data)
        result = ingestor.normalize(parsed_data)

        service_result = result['services'][0]
        assert service_result['requested_amount_currency'] == 'AED'
        assert service_result['requested_amount_value'] == '150.50'
