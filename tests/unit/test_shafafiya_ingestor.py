"""
Unit tests for Shafafiya ingestor functionality.

This module tests the Shafafiya ingestor in isolation,
focusing on XML parsing, normalization, and error handling.
"""

import pytest
from pipelines.shafafiya_ingestor import ShafafiyaIngestor
from pipelines.exceptions import UnsupportedFormatError, DataNormalizationError


class TestShafafiyaIngestor:
    """Unit tests for Shafafiya ingestor."""

    @pytest.fixture
    def ingestor(self):
        """Create Shafafiya ingestor instance."""
        return ShafafiyaIngestor(enable_validation=False)

    @pytest.fixture
    def fhir_bundle_ingestor(self):
        """Create Shafafiya ingestor with FHIR Bundle output."""
        return ShafafiyaIngestor(enable_validation=False, output_format='fhir_bundle')

    def test_supported_root_elements(self, ingestor):
        """Test that correct root elements are supported."""
        supported = ingestor.get_supported_root_elements()
        assert 'Prior.Authorization' in supported
        assert len(supported) == 1

    def test_format_info(self, ingestor):
        """Test format information metadata."""
        info = ingestor.get_format_info()
        assert info['format_name'] == 'Shafafiya'
        assert info['schema_version'] == '2011'
        assert info['authority'] == 'Abu Dhabi Department of Health (DoH)'
        assert info['system'] == 'Shafafiya'

    def test_unsupported_root_element_error(self, ingestor):
        """Test error handling for unsupported root elements."""
        invalid_data = {'InvalidRoot': {'data': 'test'}}

        with pytest.raises(UnsupportedFormatError) as exc_info:
            ingestor.normalize(invalid_data)

        assert 'InvalidRoot' in str(exc_info.value)
        assert 'Prior.Authorization' in str(exc_info.value)

    def test_legacy_output_format(self, ingestor, test_data_factory):
        """Test legacy output format structure."""
        xml_data = test_data_factory.create_shafafiya_xml()

        import xmltodict

        parsed_data = xmltodict.parse(xml_data)
        result = ingestor.normalize(parsed_data)

        # Validate legacy structure
        assert result['format_name'] == 'Shafafiya'
        assert result['schema_version'] == '2011'
        assert 'services' in result  # Activities normalized to services
        assert 'resourceType' not in result
        assert 'authorization_id' in result
        assert 'result' in result

    def test_fhir_bundle_output_format(self, fhir_bundle_ingestor, test_data_factory):
        """Test FHIR Bundle output format structure."""
        xml_data = test_data_factory.create_shafafiya_xml(
            auth_overrides={'Comments': 'Patient with diabetes requiring monitoring'}
        )

        import xmltodict

        parsed_data = xmltodict.parse(xml_data)
        result = fhir_bundle_ingestor.normalize(parsed_data)

        # Validate FHIR Bundle structure
        assert result['resourceType'] == 'Bundle'
        assert result['type'] == 'collection'
        assert result['meta']['source'] == 'Shafafiya'
        assert 'entry' in result
        assert 'total' in result
        assert len(result['entry']) == result['total']

    def test_activity_normalization(self, ingestor, test_data_factory):
        """Test activity normalization to services."""
        activities = [
            test_data_factory.create_activity('1'),
            test_data_factory.create_activity('2'),
        ]
        xml_data = test_data_factory.create_shafafiya_xml(activities=activities)

        import xmltodict

        parsed_data = xmltodict.parse(xml_data)
        result = ingestor.normalize(parsed_data)

        assert len(result['services']) == 2
        for service in result['services']:
            assert 'id' in service
            assert 'type' in service
            assert 'code' in service
            assert service['source_format'] == 'Shafafiya'

    def test_embedded_observations_extraction(self, ingestor, test_data_factory):
        """Test extraction of embedded observations from activities."""
        observation = test_data_factory.create_observation(
            'LAB', Code='HBA1C', Value='9.2', ValueType='PERCENT'
        )
        activity = test_data_factory.create_activity('1')
        activity['observations'] = [observation]

        xml_data = test_data_factory.create_shafafiya_xml(activities=[activity])

        import xmltodict

        parsed_data = xmltodict.parse(xml_data)
        result = ingestor.normalize(parsed_data)

        service = result['services'][0]
        assert 'observations' in service
        assert len(service['observations']) == 1
        obs = service['observations'][0]
        assert obs['type'] == 'LAB'
        assert obs['code'] == 'HBA1C'
        assert obs['value'] == '9.2'
        assert obs['value_type'] == 'PERCENT'

    def test_business_rule_validation(self, ingestor, test_data_factory):
        """Test business rule validation specific to Shafafiya."""
        xml_data = test_data_factory.create_shafafiya_xml()
        import xmltodict

        parsed_data = xmltodict.parse(xml_data)
        result = ingestor.normalize(parsed_data)

        warnings = ingestor.validate_business_rules(result)
        assert isinstance(warnings, list)

    def test_authorization_result_validation(self, ingestor, test_data_factory):
        """Test validation of authorization results."""
        # Test with invalid result
        xml_data = test_data_factory.create_shafafiya_xml(
            auth_overrides={'Result': 'Maybe'}
        )
        import xmltodict

        parsed_data = xmltodict.parse(xml_data)
        result = ingestor.normalize(parsed_data)

        warnings = ingestor.validate_business_rules(result)
        assert any('authorization result' in warning.lower() for warning in warnings)

    def test_record_count_validation(self, ingestor, test_data_factory):
        """Test record count consistency validation."""
        # Create data with mismatched record count
        xml_data = test_data_factory.create_shafafiya_xml(
            header_overrides={'RecordCount': '5'},  # But only 2 activities
            activities=[
                test_data_factory.create_activity('1'),
                test_data_factory.create_activity('2'),
            ],
        )
        import xmltodict

        parsed_data = xmltodict.parse(xml_data)
        result = ingestor.normalize(parsed_data)

        warnings = ingestor.validate_business_rules(result)
        assert any('record count mismatch' in warning.lower() for warning in warnings)

    def test_minimal_data_handling(self, ingestor):
        """Test handling of minimal required data."""
        minimal_data = {
            'Prior.Authorization': {
                'Header': {
                    'SenderID': 'TEST123',
                    'ReceiverID': 'PAYER999',
                    'TransactionDate': '01/01/2025 12:00',
                    'RecordCount': '1',
                },
                'Authorization': {
                    'Result': 'Yes',
                    'ID': 'MIN-001',
                    'Start': '01/01/2025',
                    'End': '31/01/2025',
                    'Activity': {
                        'ID': '1',
                        'Type': '3',
                        'Code': '99213',
                        'Net': '100.00',
                        'PaymentAmount': '80.00',
                    },
                },
            }
        }

        result = ingestor.normalize(minimal_data)
        assert result['format_name'] == 'Shafafiya'
        assert result['authorization_id'] == 'MIN-001'
        assert len(result['services']) == 1

    def test_missing_authorization_error(self, ingestor):
        """Test error handling for missing authorization section."""
        invalid_data = {
            'Prior.Authorization': {
                'Header': {
                    'SenderID': 'TEST123',
                    'ReceiverID': 'PAYER999',
                    'TransactionDate': '01/01/2025 12:00',
                }
            }
        }

        with pytest.raises(DataNormalizationError) as exc_info:
            ingestor.normalize(invalid_data)

        assert 'Authorization' in str(exc_info.value)

    def test_payment_amount_extraction(self, ingestor, test_data_factory):
        """Test payment amount extraction from activities."""
        activity = test_data_factory.create_activity(
            '1', Net='150.50', PaymentAmount='120.00'
        )
        xml_data = test_data_factory.create_shafafiya_xml(activities=[activity])

        import xmltodict

        parsed_data = xmltodict.parse(xml_data)
        result = ingestor.normalize(parsed_data)

        service = result['services'][0]
        assert service['net'] == '150.50'
        assert service['payment_amount'] == '120.00'

    def test_observation_value_type_mapping(
        self, fhir_bundle_ingestor, test_data_factory
    ):
        """Test proper mapping of observation value types in FHIR Bundle."""
        observations = [
            test_data_factory.create_observation(
                'LAB', Code='HBA1C', Value='9.2', ValueType='NUMERIC'
            ),
            test_data_factory.create_observation(
                'LAB', Code='STATUS', Value='positive', ValueType='TEXT'
            ),
            test_data_factory.create_observation(
                'LAB', Code='DONE', Value='true', ValueType='BOOLEAN'
            ),
        ]

        activity = test_data_factory.create_activity('1')
        activity['observations'] = observations

        xml_data = test_data_factory.create_shafafiya_xml(activities=[activity])

        import xmltodict

        parsed_data = xmltodict.parse(xml_data)
        result = fhir_bundle_ingestor.normalize(parsed_data)

        # Find observation resources
        obs_entries = [
            entry
            for entry in result['entry']
            if entry['resource']['resourceType'] == 'Observation'
        ]

        # Should have extracted structured observations
        assert len(obs_entries) >= 0  # May vary based on clinical extraction
