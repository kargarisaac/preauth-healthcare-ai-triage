"""
Unit tests for XMLProcessor Shafafiya functionality.

This module tests the XMLProcessor Shafafiya processing method,
focusing on XML parsing, field mapping, and output structure.
"""

import pytest
from pipelines.xml_processor import XMLProcessor


class TestShafafiyaProcessor:
    """Unit tests for XMLProcessor Shafafiya processing."""

    @pytest.fixture
    def processor(self):
        """Create XMLProcessor instance."""
        return XMLProcessor()

    def test_basic_shafafiya_processing(self, processor, temp_xml_file):
        """Test basic Shafafiya XML processing."""
        shafafiya_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<Prior.Authorization xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <Header>
        <SenderID>PROV12345</SenderID>
        <ReceiverID>PAYER67890</ReceiverID>
        <TransactionDate>27/07/2025 10:32</TransactionDate>
        <RecordCount>1</RecordCount>
        <DispositionFlag>TEST</DispositionFlag>
    </Header>
    <Authorization>
        <Result>Yes</Result>
        <ID>PA-2025-000123</ID>
        <IDPayer>PAYER67890</IDPayer>
        <Start>25/07/2025 00:00</Start>
        <End>25/08/2025 23:59</End>
        <Limit>1000.00</Limit>
        <Comments>Authorization approved for treatment.</Comments>
        <Activity>
            <ID>1</ID>
            <Type>3</Type>
            <Code>83036</Code>
            <Quantity>1</Quantity>
            <UnitCost>120.00</UnitCost>
            <Amount>120.00</Amount>
        </Activity>
    </Authorization>
</Prior.Authorization>'''

        xml_file = temp_xml_file(shafafiya_xml, "test_shafafiya.xml")
        result = processor.process_shafafiya(xml_file)

        # Test canonical JSON structure
        assert result['resourceType'] == 'Bundle'
        assert result['meta']['source'] == 'Shafafiya'
        assert result['authorization_id'] == 'PA-2025-000123'
        assert result['sender'] == 'PROV12345'
        assert result['receiver'] == 'PAYER67890'
        assert result['authorization_result'] == 'Yes'
        assert result['comments'] == 'Authorization approved for treatment.'

    def test_activities_extraction(self, processor, temp_xml_file):
        """Test activity extraction from Shafafiya XML."""
        shafafiya_xml = '''<?xml version="1.0" encoding="UTF-8"?>
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
        <Activity>
            <ID>1</ID>
            <Type>3</Type>
            <Code>83036</Code>
            <Description>Blood test</Description>
            <Quantity>1</Quantity>
            <UnitCost>120.00</UnitCost>
            <Amount>120.00</Amount>
        </Activity>
        <Activity>
            <ID>2</ID>
            <Type>3</Type>
            <Code>83037</Code>
            <Description>Lab analysis</Description>
            <Quantity>2</Quantity>
            <UnitCost>75.00</UnitCost>
            <Amount>150.00</Amount>
        </Activity>
    </Authorization>
</Prior.Authorization>'''

        xml_file = temp_xml_file(shafafiya_xml, "test_shafafiya_activities.xml")
        result = processor.process_shafafiya(xml_file)

        # Test activities extraction
        assert len(result['activities']) == 2

        activity1 = result['activities'][0]
        assert activity1['id'] == '1'
        assert activity1['type'] == '3'
        assert activity1['code'] == '83036'
        assert activity1['description'] == 'Blood test'
        assert activity1['quantity'] == '1'
        assert activity1['unit_cost'] == '120.00'
        assert activity1['amount'] == '120.00'

        activity2 = result['activities'][1]
        assert activity2['id'] == '2'
        assert activity2['code'] == '83037'
        assert activity2['description'] == 'Lab analysis'

    def test_raw_data_preservation(self, processor, temp_xml_file):
        """Test that raw XML data is preserved in output."""
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

        xml_file = temp_xml_file(shafafiya_xml, "test_shafafiya_raw.xml")
        result = processor.process_shafafiya(xml_file)

        # Test raw data preservation
        assert 'raw_data' in result
        assert 'Prior.Authorization' in result['raw_data']
        assert (
            result['raw_data']['Prior.Authorization']['Header']['SenderID']
            == 'PROV12345'
        )

    def test_minimal_xml_handling(self, processor, temp_xml_file):
        """Test handling of minimal XML structure."""
        minimal_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<Prior.Authorization xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <Header>
        <SenderID>TEST123</SenderID>
        <ReceiverID>PAYER999</ReceiverID>
        <TransactionDate>01/01/2025 12:00</TransactionDate>
        <RecordCount>1</RecordCount>
    </Header>
    <Authorization>
        <Result>Yes</Result>
        <ID>MIN-001</ID>
        <Activity>
            <ID>1</ID>
            <Type>3</Type>
            <Code>99213</Code>
        </Activity>
    </Authorization>
</Prior.Authorization>'''

        xml_file = temp_xml_file(minimal_xml, "test_minimal.xml")
        result = processor.process_shafafiya(xml_file)

        assert result['resourceType'] == 'Bundle'
        assert result['authorization_id'] == 'MIN-001'
        assert result['sender'] == 'TEST123'
        assert result['authorization_result'] == 'Yes'
        assert len(result['activities']) == 1
        assert result['activities'][0]['code'] == '99213'

    def test_missing_file_error(self, processor):
        """Test error handling for missing XML file."""
        with pytest.raises(FileNotFoundError):
            processor.process_shafafiya("nonexistent_file.xml")

    def test_bundle_metadata(self, processor, temp_xml_file):
        """Test Bundle metadata generation."""
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
        <ID>PA-2025-000456</ID>
    </Authorization>
</Prior.Authorization>'''

        xml_file = temp_xml_file(shafafiya_xml, "test_metadata.xml")
        result = processor.process_shafafiya(xml_file)

        # Test Bundle structure
        assert result['resourceType'] == 'Bundle'
        assert 'id' in result
        assert result['id'].startswith('Shafafiya-')
        assert result['type'] == 'collection'

        # Test meta information
        meta = result['meta']
        assert meta['source'] == 'Shafafiya'
        assert 'lastUpdated' in meta
        assert 'versionId' in meta
        assert meta['profile'] == [
            'https://nazmito.com/fhir/StructureDefinition/healthcare-bundle'
        ]

    def test_single_activity_vs_multiple_activities(self, processor, temp_xml_file):
        """Test handling of single activity vs multiple activities."""
        # Test single activity (not in list)
        single_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<Prior.Authorization xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <Header>
        <SenderID>PROV12345</SenderID>
        <ReceiverID>PAYER67890</ReceiverID>
        <TransactionDate>27/07/2025 10:32</TransactionDate>
        <RecordCount>1</RecordCount>
    </Header>
    <Authorization>
        <Result>Yes</Result>
        <ID>PA-SINGLE</ID>
        <Activity>
            <ID>1</ID>
            <Code>83036</Code>
            <Amount>100.00</Amount>
        </Activity>
    </Authorization>
</Prior.Authorization>'''

        xml_file = temp_xml_file(single_xml, "test_single.xml")
        result = processor.process_shafafiya(xml_file)

        assert len(result['activities']) == 1
        assert result['activities'][0]['id'] == '1'
        assert result['activities'][0]['amount'] == '100.00'

    def test_authorization_dates(self, processor, temp_xml_file):
        """Test extraction of authorization start and end dates."""
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
        <ID>PA-DATES</ID>
        <Start>01/08/2025 00:00</Start>
        <End>31/08/2025 23:59</End>
        <Activity>
            <ID>1</ID>
            <Code>83036</Code>
        </Activity>
    </Authorization>
</Prior.Authorization>'''

        xml_file = temp_xml_file(shafafiya_xml, "test_dates.xml")
        result = processor.process_shafafiya(xml_file)

        assert result['authorization_start'] == '01/08/2025 00:00'
        assert result['authorization_end'] == '31/08/2025 23:59'
