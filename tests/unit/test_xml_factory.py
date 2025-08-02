"""
Unit tests for XMLProcessor basic functionality.

This module tests basic XMLProcessor functionality and compares
both processing methods to ensure consistent output structure.
"""

import pytest
from pipelines.xml_processor import XMLProcessor


class TestXMLProcessor:
    """Unit tests for XMLProcessor."""

    @pytest.fixture
    def processor(self):
        """Create XMLProcessor instance."""
        return XMLProcessor()

    def test_processor_initialization(self, processor):
        """Test XMLProcessor initialization."""
        assert processor is not None
        assert hasattr(processor, 'process_eclaim_link')
        assert hasattr(processor, 'process_shafafiya')

    def test_both_formats_produce_bundle_structure(self, processor, temp_xml_file):
        """Test that both formats produce consistent Bundle structure."""
        # Test eClaimLink format
        eclaim_xml = '''<?xml version="1.0" encoding="UTF-8"?>
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
        </ServiceRequest>
    </ServiceRequests>
</PriorAuthorizationRequest>'''

        eclaim_file = temp_xml_file(eclaim_xml, "test_eclaim.xml")
        eclaim_result = processor.process_eclaim_link(eclaim_file)

        # Test Shafafiya format
        shafafiya_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<Prior.Authorization xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <Header>
        <SenderID>PROV12345</SenderID>
        <ReceiverID>PAYER67890</ReceiverID>
        <TransactionDate>27/07/2025 10:32</TransactionDate>
        <RecordCount>1</RecordCount>
    </Header>
    <Authorization>
        <Result>Yes</Result>
        <ID>PA-2025-000123</ID>
        <Activity>
            <ID>1</ID>
            <Code>83036</Code>
        </Activity>
    </Authorization>
</Prior.Authorization>'''

        shafafiya_file = temp_xml_file(shafafiya_xml, "test_shafafiya.xml")
        shafafiya_result = processor.process_shafafiya(shafafiya_file)

        # Both should have Bundle structure
        assert eclaim_result['resourceType'] == 'Bundle'
        assert shafafiya_result['resourceType'] == 'Bundle'

        # Both should have consistent metadata
        assert 'meta' in eclaim_result
        assert 'meta' in shafafiya_result
        assert eclaim_result['type'] == 'collection'
        assert shafafiya_result['type'] == 'collection'

        # Both should preserve raw data
        assert 'raw_data' in eclaim_result
        assert 'raw_data' in shafafiya_result

    def test_format_specific_fields(self, processor, temp_xml_file):
        """Test that format-specific fields are correctly mapped."""
        # Test eClaimLink specific fields
        eclaim_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
    <Header>
        <SenderID>PROV12345</SenderID>
        <ReceiverID>PAYER67890</ReceiverID>
        <TransactionDateTime>27/07/2025 10:32</TransactionDateTime>
        <TransactionID>TXN-2025-000456</TransactionID>
    </Header>
    <JustificationText>Patient justification text</JustificationText>
    <ServiceRequests>
        <ServiceRequest>
            <ct:ActivityCode>83036</ct:ActivityCode>
        </ServiceRequest>
    </ServiceRequests>
</PriorAuthorizationRequest>'''

        eclaim_file = temp_xml_file(eclaim_xml, "test_eclaim_fields.xml")
        eclaim_result = processor.process_eclaim_link(eclaim_file)

        # eClaimLink should have justification_text and services
        assert 'justification_text' in eclaim_result
        assert 'services' in eclaim_result
        assert eclaim_result['justification_text'] == 'Patient justification text'

        # Test Shafafiya specific fields
        shafafiya_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<Prior.Authorization xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <Header>
        <SenderID>PROV12345</SenderID>
        <ReceiverID>PAYER67890</ReceiverID>
        <TransactionDate>27/07/2025 10:32</TransactionDate>
        <RecordCount>1</RecordCount>
    </Header>
    <Authorization>
        <Result>Yes</Result>
        <ID>PA-2025-000123</ID>
        <Comments>Authorization comments</Comments>
        <Start>01/08/2025 00:00</Start>
        <End>31/08/2025 23:59</End>
        <Activity>
            <ID>1</ID>
            <Code>83036</Code>
        </Activity>
    </Authorization>
</Prior.Authorization>'''

        shafafiya_file = temp_xml_file(shafafiya_xml, "test_shafafiya_fields.xml")
        shafafiya_result = processor.process_shafafiya(shafafiya_file)

        # Shafafiya should have authorization-specific fields and activities
        assert 'authorization_result' in shafafiya_result
        assert 'authorization_start' in shafafiya_result
        assert 'authorization_end' in shafafiya_result
        assert 'comments' in shafafiya_result
        assert 'activities' in shafafiya_result
        assert shafafiya_result['authorization_result'] == 'Yes'
        assert shafafiya_result['comments'] == 'Authorization comments'

    def test_error_handling_consistency(self, processor):
        """Test that both methods handle errors consistently."""
        # Both should raise FileNotFoundError for missing files
        with pytest.raises(FileNotFoundError):
            processor.process_eclaim_link("nonexistent_eclaim.xml")

        with pytest.raises(FileNotFoundError):
            processor.process_shafafiya("nonexistent_shafafiya.xml")

    def test_metadata_generation_consistency(self, processor, temp_xml_file):
        """Test that metadata generation is consistent across formats."""
        # Simple XML for each format
        eclaim_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
    <Header>
        <SenderID>TEST123</SenderID>
        <ReceiverID>PAYER999</ReceiverID>
        <TransactionDateTime>01/01/2025 12:00</TransactionDateTime>
        <TransactionID>TEST-001</TransactionID>
    </Header>
</PriorAuthorizationRequest>'''

        shafafiya_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<Prior.Authorization xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <Header>
        <SenderID>TEST123</SenderID>
        <ReceiverID>PAYER999</ReceiverID>
        <TransactionDate>01/01/2025 12:00</TransactionDate>
        <RecordCount>1</RecordCount>
    </Header>
    <Authorization>
        <Result>Yes</Result>
        <ID>TEST-001</ID>
    </Authorization>
</Prior.Authorization>'''

        eclaim_file = temp_xml_file(eclaim_xml, "test_meta_eclaim.xml")
        shafafiya_file = temp_xml_file(shafafiya_xml, "test_meta_shafafiya.xml")

        eclaim_result = processor.process_eclaim_link(eclaim_file)
        shafafiya_result = processor.process_shafafiya(shafafiya_file)

        # Both should have consistent metadata structure
        for result in [eclaim_result, shafafiya_result]:
            assert 'id' in result
            assert 'timestamp' in result
            assert 'processing_timestamp' in result
            assert 'source_file' in result

            meta = result['meta']
            assert 'lastUpdated' in meta
            assert 'versionId' in meta
            assert 'profile' in meta
            assert meta['profile'] == [
                'https://nazmito.com/fhir/StructureDefinition/healthcare-bundle'
            ]

        # Source should be format-specific
        assert eclaim_result['meta']['source'] == 'eClaimLink'
        assert shafafiya_result['meta']['source'] == 'Shafafiya'
