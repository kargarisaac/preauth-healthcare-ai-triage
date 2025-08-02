"""
Unit tests for XMLProcessor eClaimLink functionality.

This module tests the XMLProcessor eClaimLink processing method,
focusing on XML parsing, field mapping, and output structure.
"""

import pytest
from pipelines.xml_processor import XMLProcessor


class TestEClaimLinkProcessor:
    """Unit tests for XMLProcessor eClaimLink processing."""

    @pytest.fixture
    def processor(self):
        """Create XMLProcessor instance."""
        return XMLProcessor()

    def test_basic_eclaim_processing(self, processor, temp_xml_file):
        """Test basic eClaimLink XML processing."""
        # Create simple test XML
        eclaim_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
    <Header>
        <SenderID>PROV12345</SenderID>
        <ReceiverID>PAYER67890</ReceiverID>
        <TransactionDateTime>27/07/2025 10:32</TransactionDateTime>
        <TransactionID>TXN-2025-000456</TransactionID>
    </Header>
    <JustificationText>Patient requires medical attention.</JustificationText>
    <ServiceRequests>
        <ServiceRequest>
            <ct:ActivityCode>83036</ct:ActivityCode>
            <ct:DiagnosisCode>E11.9</ct:DiagnosisCode>
            <ct:ActivityDateTime>28/07/2025 09:00</ct:ActivityDateTime>
            <ct:ActivityInstructions>Service instructions</ct:ActivityInstructions>
            <RequestedAmount currency="AED">120.00</RequestedAmount>
        </ServiceRequest>
    </ServiceRequests>
</PriorAuthorizationRequest>'''

        xml_file = temp_xml_file(eclaim_xml, "test_eclaim.xml")
        result = processor.process_eclaim_link(xml_file)

        # Test canonical JSON structure
        assert result['resourceType'] == 'Bundle'
        assert result['meta']['source'] == 'eClaimLink'
        assert result['authorization_id'] == 'TXN-2025-000456'
        assert result['sender'] == 'PROV12345'
        assert result['receiver'] == 'PAYER67890'
        assert result['justification_text'] == 'Patient requires medical attention.'

    def test_services_extraction(self, processor, temp_xml_file):
        """Test service extraction from eClaimLink XML."""
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
            <ct:DiagnosisCode>E11.9</ct:DiagnosisCode>
            <ct:ActivityDateTime>28/07/2025 09:00</ct:ActivityDateTime>
            <ct:ActivityInstructions>Service 1 instructions</ct:ActivityInstructions>
            <RequestedAmount currency="AED">120.00</RequestedAmount>
        </ServiceRequest>
        <ServiceRequest>
            <ct:ActivityCode>83037</ct:ActivityCode>
            <ct:DiagnosisCode>E11.8</ct:DiagnosisCode>
            <ct:ActivityDateTime>29/07/2025 09:00</ct:ActivityDateTime>
            <ct:ActivityInstructions>Service 2 instructions</ct:ActivityInstructions>
            <RequestedAmount currency="AED">150.00</RequestedAmount>
        </ServiceRequest>
    </ServiceRequests>
</PriorAuthorizationRequest>'''

        xml_file = temp_xml_file(eclaim_xml, "test_eclaim_services.xml")
        result = processor.process_eclaim_link(xml_file)

        # Test services extraction
        assert len(result['services']) == 2

        service1 = result['services'][0]
        assert service1['sequence'] == 1
        assert service1['activity_code'] == '83036'
        assert service1['diagnosis_code'] == 'E11.9'
        assert service1['requested_amount_value'] == '120.00'
        assert service1['requested_amount_currency'] == 'AED'

        service2 = result['services'][1]
        assert service2['sequence'] == 2
        assert service2['activity_code'] == '83037'
        assert service2['diagnosis_code'] == 'E11.8'

    def test_raw_data_preservation(self, processor, temp_xml_file):
        """Test that raw XML data is preserved in output."""
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

        xml_file = temp_xml_file(eclaim_xml, "test_eclaim_raw.xml")
        result = processor.process_eclaim_link(xml_file)

        # Test raw data preservation
        assert 'raw_data' in result
        assert 'PriorAuthorizationRequest' in result['raw_data']
        assert (
            result['raw_data']['PriorAuthorizationRequest']['Header']['SenderID']
            == 'PROV12345'
        )

    def test_amount_extraction_variations(self, processor, temp_xml_file):
        """Test extraction of different amount formats."""
        # Test with currency attribute
        eclaim_xml_with_currency = '''<?xml version="1.0" encoding="UTF-8"?>
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
            <RequestedAmount currency="AED">120.50</RequestedAmount>
        </ServiceRequest>
    </ServiceRequests>
</PriorAuthorizationRequest>'''

        xml_file = temp_xml_file(eclaim_xml_with_currency, "test_amount.xml")
        result = processor.process_eclaim_link(xml_file)

        service = result['services'][0]
        assert service['requested_amount_value'] == '120.50'
        assert service['requested_amount_currency'] == 'AED'

    def test_minimal_xml_handling(self, processor, temp_xml_file):
        """Test handling of minimal XML structure."""
        minimal_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
    <Header>
        <SenderID>TEST123</SenderID>
        <ReceiverID>PAYER999</ReceiverID>
        <TransactionDateTime>01/01/2025 12:00</TransactionDateTime>
        <TransactionID>MIN-001</TransactionID>
    </Header>
    <ServiceRequests>
        <ServiceRequest>
            <ct:ActivityCode>99213</ct:ActivityCode>
        </ServiceRequest>
    </ServiceRequests>
</PriorAuthorizationRequest>'''

        xml_file = temp_xml_file(minimal_xml, "test_minimal.xml")
        result = processor.process_eclaim_link(xml_file)

        assert result['resourceType'] == 'Bundle'
        assert result['authorization_id'] == 'MIN-001'
        assert result['sender'] == 'TEST123'
        assert len(result['services']) == 1
        assert result['services'][0]['activity_code'] == '99213'

    def test_missing_file_error(self, processor):
        """Test error handling for missing XML file."""
        with pytest.raises(FileNotFoundError):
            processor.process_eclaim_link("nonexistent_file.xml")

    def test_bundle_metadata(self, processor, temp_xml_file):
        """Test Bundle metadata generation."""
        eclaim_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
    <Header>
        <SenderID>PROV12345</SenderID>
        <ReceiverID>PAYER67890</ReceiverID>
        <TransactionDateTime>27/07/2025 10:32</TransactionDateTime>
        <TransactionID>TXN-2025-000456</TransactionID>
    </Header>
</PriorAuthorizationRequest>'''

        xml_file = temp_xml_file(eclaim_xml, "test_metadata.xml")
        result = processor.process_eclaim_link(xml_file)

        # Test Bundle structure
        assert result['resourceType'] == 'Bundle'
        assert 'id' in result
        assert result['id'].startswith('eClaimLink-')
        assert result['type'] == 'collection'

        # Test meta information
        meta = result['meta']
        assert meta['source'] == 'eClaimLink'
        assert 'lastUpdated' in meta
        assert 'versionId' in meta
        assert meta['profile'] == [
            'https://nazmito.com/fhir/StructureDefinition/healthcare-bundle'
        ]

    def test_single_service_vs_multiple_services(self, processor, temp_xml_file):
        """Test handling of single service vs multiple services."""
        # Test single service (not in list)
        single_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
    <Header>
        <SenderID>PROV12345</SenderID>
        <ReceiverID>PAYER67890</ReceiverID>
        <TransactionDateTime>27/07/2025 10:32</TransactionDateTime>
        <TransactionID>TXN-SINGLE</TransactionID>
    </Header>
    <ServiceRequests>
        <ServiceRequest>
            <ct:ActivityCode>83036</ct:ActivityCode>
            <RequestedAmount>100.00</RequestedAmount>
        </ServiceRequest>
    </ServiceRequests>
</PriorAuthorizationRequest>'''

        xml_file = temp_xml_file(single_xml, "test_single.xml")
        result = processor.process_eclaim_link(xml_file)

        assert len(result['services']) == 1
        assert result['services'][0]['sequence'] == 1
        assert result['services'][0]['requested_amount_value'] == '100.00'
