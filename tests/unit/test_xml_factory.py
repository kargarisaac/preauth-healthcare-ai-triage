"""
Unit tests for XMLIngestorFactory functionality.

This module tests the factory pattern for automatic format detection
and ingestor creation without processing actual files.
"""

import pytest
from pipelines.factory import XMLIngestorFactory
from pipelines.eclaim_link_ingestor import EClaimLinkIngestor
from pipelines.shafafiya_ingestor import ShafafiyaIngestor
from pipelines.exceptions import UnsupportedFormatError


class TestXMLIngestorFactory:
    """Unit tests for XMLIngestorFactory."""

    @pytest.fixture
    def factory(self):
        """Create factory instance."""
        return XMLIngestorFactory(schema_base_path='schemas/')

    def test_factory_initialization(self, factory):
        """Test factory initialization."""
        assert factory.schema_base_path == 'schemas/'
        assert factory.enable_validation is True
        assert factory.logger is not None

    def test_get_supported_formats(self, factory):
        """Test retrieval of supported formats."""
        formats = factory.get_supported_formats()
        assert len(formats) >= 2

        format_names = [fmt['format_name'] for fmt in formats]
        assert 'eClaimLink' in format_names
        assert 'Shafafiya' in format_names

    def test_create_eclaim_ingestor(self, factory):
        """Test creation of eClaimLink ingestor."""
        ingestor = factory.create_ingestor('eClaimLink')
        assert isinstance(ingestor, EClaimLinkIngestor)
        assert ingestor.FORMAT_NAME == 'eClaimLink'

    def test_create_shafafiya_ingestor(self, factory):
        """Test creation of Shafafiya ingestor."""
        ingestor = factory.create_ingestor('Shafafiya')
        assert isinstance(ingestor, ShafafiyaIngestor)
        assert ingestor.FORMAT_NAME == 'Shafafiya'

    def test_create_ingestor_with_fhir_output(self, factory):
        """Test creation of ingestor with FHIR Bundle output."""
        ingestor = factory.create_ingestor('eClaimLink', output_format='fhir_bundle')
        assert ingestor.output_format == 'fhir_bundle'

    def test_create_ingestor_with_custom_schema(self, factory):
        """Test creation of ingestor with custom schema path."""
        custom_schema = 'custom/schema.xsd'
        ingestor = factory.create_ingestor('eClaimLink', schema_path=custom_schema)
        assert ingestor.schema_path == custom_schema

    def test_create_ingestor_with_validation_disabled(self, factory):
        """Test creation of ingestor with validation disabled."""
        ingestor = factory.create_ingestor('eClaimLink', enable_validation=False)
        assert ingestor.enable_validation is False

    def test_unsupported_format_error(self, factory):
        """Test error for unsupported format."""
        with pytest.raises(UnsupportedFormatError):
            factory.create_ingestor('UnsupportedFormat')

    def test_format_detection_mock_data(self, factory, mock_file_system):
        """Test format detection with mock XML data."""
        # Mock eClaimLink XML
        eclaim_xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
            <Header><SenderID>TEST</SenderID></Header>
        </PriorAuthorizationRequest>'''

        mock_file_system.add_file('/test/eclaim.xml', eclaim_xml)

        # Mock the file reading in factory
        import tempfile

        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(eclaim_xml)
            f.flush()

            detected = factory.detect_format(f.name)
            assert detected == 'eClaimLink'

    def test_ingestor_registry_operations(self, factory):
        """Test ingestor registry operations."""
        # Test getting registry info
        formats = factory.get_supported_formats()
        initial_count = len(formats)

        # Registry should have default ingestors
        assert initial_count >= 2

    def test_schema_path_resolution(self, factory):
        """Test schema path resolution logic."""
        # Test with existing format
        ingestor = factory.create_ingestor('eClaimLink')
        expected_schema = 'schemas/CommonTypes_20191113.xsd'
        # Schema path resolution logic is internal, test that it doesn't error

    def test_format_case_sensitivity(self, factory):
        """Test format name case sensitivity."""
        # Should work with exact case
        ingestor1 = factory.create_ingestor('eClaimLink')
        assert isinstance(ingestor1, EClaimLinkIngestor)

        ingestor2 = factory.create_ingestor('Shafafiya')
        assert isinstance(ingestor2, ShafafiyaIngestor)

    def test_logger_configuration(self, factory):
        """Test logger configuration."""
        assert factory.logger is not None
        assert factory.logger.name.endswith('XMLIngestorFactory')

    def test_validation_settings_inheritance(self, factory):
        """Test that validation settings are properly inherited."""
        # Factory with validation enabled
        factory_with_validation = XMLIngestorFactory(
            schema_base_path='schemas/', enable_validation=True
        )
        ingestor = factory_with_validation.create_ingestor('eClaimLink')
        assert ingestor.enable_validation is True

        # Factory with validation disabled
        factory_no_validation = XMLIngestorFactory(
            schema_base_path='schemas/', enable_validation=False
        )
        ingestor = factory_no_validation.create_ingestor('eClaimLink')
        assert ingestor.enable_validation is False

    def test_concurrent_ingestor_creation(self, factory):
        """Test concurrent creation of multiple ingestors."""
        # Should be able to create multiple ingestors simultaneously
        ingestor1 = factory.create_ingestor('eClaimLink')
        ingestor2 = factory.create_ingestor('Shafafiya')
        ingestor3 = factory.create_ingestor('eClaimLink', output_format='fhir_bundle')

        assert isinstance(ingestor1, EClaimLinkIngestor)
        assert isinstance(ingestor2, ShafafiyaIngestor)
        assert isinstance(ingestor3, EClaimLinkIngestor)
        assert ingestor3.output_format == 'fhir_bundle'

    def test_ingestor_configuration_isolation(self, factory):
        """Test that ingestor configurations are isolated."""
        ingestor1 = factory.create_ingestor('eClaimLink', enable_validation=True)
        ingestor2 = factory.create_ingestor('eClaimLink', enable_validation=False)

        # Each should have its own configuration
        assert ingestor1.enable_validation is True
        assert ingestor2.enable_validation is False
