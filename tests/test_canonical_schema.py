"""
Tests for canonical schema and XMLProcessor output structure.

This module tests the canonical JSON structure produced by XMLProcessor
for both eClaimLink and Shafafiya formats.
"""

import pytest
from pathlib import Path
from pipelines.xml_processor import XMLProcessor


class TestCanonicalSchema:
    """Test suite for canonical schema and data transformations."""

    @pytest.fixture
    def processor(self):
        """XMLProcessor instance for testing."""
        return XMLProcessor()

    @pytest.fixture
    def sample_xml_paths(self):
        """Paths to sample XML files."""
        project_root = Path(__file__).parent.parent
        return {
            'eclaim_link': project_root / "samples" / "eclaim_link_request.xml",
            'shafafiya': project_root / "samples" / "shafafiya_prior_auth_request.xml",
        }

    def test_bundle_structure_validation(self, processor, temp_xml_file):
        """Test that output has valid Bundle structure."""
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

        xml_file = temp_xml_file(eclaim_xml, "test_bundle.xml")
        result = processor.process_eclaim_link(xml_file)

        # Test Bundle structure
        assert result['resourceType'] == 'Bundle'
        assert result['type'] == 'collection'
        assert 'id' in result
        assert 'meta' in result
        assert 'timestamp' in result

        # Test meta structure
        meta = result['meta']
        assert 'source' in meta
        assert 'lastUpdated' in meta
        assert 'versionId' in meta
        assert 'profile' in meta
        assert isinstance(meta['profile'], list)

    def test_required_fields_present(self, processor, temp_xml_file):
        """Test that all required fields are present in the output."""
        # Test eClaimLink required fields
        eclaim_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
    <Header>
        <SenderID>PROV12345</SenderID>
        <ReceiverID>PAYER67890</ReceiverID>
        <TransactionDateTime>27/07/2025 10:32</TransactionDateTime>
        <TransactionID>TXN-2025-000456</TransactionID>
    </Header>
    <JustificationText>Patient justification</JustificationText>
    <ServiceRequests>
        <ServiceRequest>
            <ct:ActivityCode>83036</ct:ActivityCode>
        </ServiceRequest>
    </ServiceRequests>
</PriorAuthorizationRequest>'''

        xml_file = temp_xml_file(eclaim_xml, "test_required.xml")
        result = processor.process_eclaim_link(xml_file)

        # Required Bundle fields
        required_bundle_fields = ['resourceType', 'id', 'meta', 'type', 'timestamp']
        for field in required_bundle_fields:
            assert field in result, f"Required Bundle field '{field}' missing"

        # Required eClaimLink fields
        required_eclaim_fields = [
            'authorization_id',
            'sender',
            'receiver',
            'services',
            'raw_data',
        ]
        for field in required_eclaim_fields:
            assert field in result, f"Required eClaimLink field '{field}' missing"

    def test_xml_to_canonical_transformation(self, processor, sample_xml_paths):
        """Test transformation from XML to canonical Bundle format."""
        for format_name, xml_path in sample_xml_paths.items():
            if not xml_path.exists():
                pytest.skip(f"Sample XML file not found: {xml_path}")

            if format_name == 'eclaim_link':
                result = processor.process_eclaim_link(str(xml_path))

                # Validate eClaimLink transformation
                assert result['resourceType'] == 'Bundle'
                assert result['meta']['source'] == 'eClaimLink'
                assert 'services' in result
                assert 'justification_text' in result

            elif format_name == 'shafafiya':
                result = processor.process_shafafiya(str(xml_path))

                # Validate Shafafiya transformation
                assert result['resourceType'] == 'Bundle'
                assert result['meta']['source'] == 'Shafafiya'
                assert 'activities' in result
                assert 'authorization_result' in result

            # Common validations
            assert isinstance(result, dict)
            assert 'raw_data' in result
            assert 'processing_timestamp' in result
            assert 'source_file' in result

    def test_data_preservation(self, processor, temp_xml_file):
        """Test that all original data is preserved in raw_data."""
        complex_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
    <Header>
        <SenderID>PROV_Complex@123</SenderID>
        <ReceiverID>PAYER-999#Test</ReceiverID>
        <TransactionDateTime>27/07/2025 10:32</TransactionDateTime>
        <TransactionID>TXN-COMPLEX-DATA</TransactionID>
        <AdditionalField>Custom Value</AdditionalField>
    </Header>
    <JustificationText>Complex justification with &lt;special&gt; characters</JustificationText>
    <ServiceRequests>
        <ServiceRequest>
            <ct:ActivityCode>83036</ct:ActivityCode>
            <ct:DiagnosisCode>E11.9</ct:DiagnosisCode>
            <CustomServiceField>Custom Service Data</CustomServiceField>
            <RequestedAmount currency="AED">1234.56</RequestedAmount>
        </ServiceRequest>
    </ServiceRequests>
    <CustomRootField>Custom Root Data</CustomRootField>
</PriorAuthorizationRequest>'''

        xml_file = temp_xml_file(complex_xml, "test_preservation.xml")
        result = processor.process_eclaim_link(xml_file)

        # Verify raw data preservation
        assert 'raw_data' in result
        raw_request = result['raw_data']['PriorAuthorizationRequest']

        # Check that custom fields are preserved
        assert raw_request['Header']['AdditionalField'] == 'Custom Value'
        assert raw_request['CustomRootField'] == 'Custom Root Data'
        assert (
            raw_request['ServiceRequests']['ServiceRequest']['CustomServiceField']
            == 'Custom Service Data'
        )

    def test_services_structure(self, processor, temp_xml_file):
        """Test that services have the correct structure."""
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
            <ct:ActivityInstructions>Service instructions</ct:ActivityInstructions>
            <RequestedAmount currency="AED">120.50</RequestedAmount>
        </ServiceRequest>
    </ServiceRequests>
</PriorAuthorizationRequest>'''

        xml_file = temp_xml_file(eclaim_xml, "test_services.xml")
        result = processor.process_eclaim_link(xml_file)

        services = result.get("services", [])
        assert len(services) > 0, "At least one service required"

        for service in services:
            # Check required service fields
            assert "sequence" in service, "Service sequence required"
            assert "activity_code" in service, "Activity code required"
            assert isinstance(service["sequence"], int), "Sequence must be integer"

            # Check optional but expected fields
            if "requested_amount_value" in service:
                assert service["requested_amount_value"] is not None
            if "requested_amount_currency" in service:
                assert isinstance(service["requested_amount_currency"], str)

    def test_activities_structure_shafafiya(self, processor, temp_xml_file):
        """Test that Shafafiya activities have correct structure."""
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
            <Type>3</Type>
            <Code>83036</Code>
            <Description>Blood test</Description>
            <Quantity>1</Quantity>
            <UnitCost>120.00</UnitCost>
            <Amount>120.00</Amount>
        </Activity>
    </Authorization>
</Prior.Authorization>'''

        xml_file = temp_xml_file(shafafiya_xml, "test_activities.xml")
        result = processor.process_shafafiya(xml_file)

        activities = result.get("activities", [])
        assert len(activities) > 0, "At least one activity required"

        for activity in activities:
            # Check required activity fields
            assert "id" in activity, "Activity ID required"
            assert "code" in activity, "Activity code required"

            # Check that raw activity data is preserved
            assert (
                "raw_activity_data" in activity
            ), "Raw activity data must be preserved"

    def test_metadata_consistency(self, processor, temp_xml_file):
        """Test that metadata is consistently generated."""
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
    <Header>
        <SenderID>META_TEST</SenderID>
        <ReceiverID>PAYER999</ReceiverID>
        <TransactionDateTime>01/01/2025 12:00</TransactionDateTime>
        <TransactionID>META-001</TransactionID>
    </Header>
</PriorAuthorizationRequest>'''

        xml_file = temp_xml_file(xml_content, "test_metadata.xml")
        result = processor.process_eclaim_link(xml_file)

        # Test timestamp generation
        assert 'timestamp' in result
        assert 'processing_timestamp' in result

        # Test Bundle ID generation
        assert result['id'].startswith('eClaimLink-')

        # Test meta structure
        meta = result['meta']
        assert meta['source'] == 'eClaimLink'
        assert 'lastUpdated' in meta
        assert meta['versionId'] == '1'
        assert meta['profile'] == [
            'https://nazmito.com/fhir/StructureDefinition/healthcare-bundle'
        ]

    def test_format_specific_fields(self, processor, temp_xml_file):
        """Test that format-specific fields are correctly mapped."""
        # Test eClaimLink specific field mapping
        eclaim_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
    <Header>
        <SenderID>PROV12345</SenderID>
        <ReceiverID>PAYER67890</ReceiverID>
        <TransactionDateTime>27/07/2025 10:32</TransactionDateTime>
        <TransactionID>TXN-FORMAT-TEST</TransactionID>
    </Header>
    <JustificationText>eClaimLink specific justification</JustificationText>
</PriorAuthorizationRequest>'''

        eclaim_file = temp_xml_file(eclaim_xml, "test_eclaim_fields.xml")
        eclaim_result = processor.process_eclaim_link(eclaim_file)

        # eClaimLink should have these specific fields
        assert 'justification_text' in eclaim_result
        assert 'services' in eclaim_result
        assert (
            eclaim_result['justification_text'] == 'eClaimLink specific justification'
        )

        # Test Shafafiya specific field mapping
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
        <ID>PA-FORMAT-TEST</ID>
        <Comments>Shafafiya specific comments</Comments>
        <Start>01/08/2025 00:00</Start>
        <End>31/08/2025 23:59</End>
    </Authorization>
</Prior.Authorization>'''

        shafafiya_file = temp_xml_file(shafafiya_xml, "test_shafafiya_fields.xml")
        shafafiya_result = processor.process_shafafiya(shafafiya_file)

        # Shafafiya should have these specific fields
        assert 'authorization_result' in shafafiya_result
        assert 'authorization_start' in shafafiya_result
        assert 'authorization_end' in shafafiya_result
        assert 'comments' in shafafiya_result
        assert 'activities' in shafafiya_result
        assert shafafiya_result['authorization_result'] == 'Yes'
        assert shafafiya_result['comments'] == 'Shafafiya specific comments'

    def test_edge_cases_handling(self, processor, temp_xml_file):
        """Test handling of edge cases and minimal data."""
        # Test minimal eClaimLink XML
        minimal_eclaim = '''<?xml version="1.0" encoding="UTF-8"?>
<PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
    <Header>
        <SenderID>MIN</SenderID>
        <ReceiverID>PAYER</ReceiverID>
        <TransactionDateTime>01/01/2025</TransactionDateTime>
        <TransactionID>MIN-001</TransactionID>
    </Header>
</PriorAuthorizationRequest>'''

        minimal_file = temp_xml_file(minimal_eclaim, "test_minimal.xml")
        result = processor.process_eclaim_link(minimal_file)

        # Should still produce valid Bundle structure
        assert result['resourceType'] == 'Bundle'
        assert result['authorization_id'] == 'MIN-001'
        assert result['sender'] == 'MIN'
        assert 'services' in result  # Should be empty list
        assert isinstance(result['services'], list)


class TestOutputFormatConsistency:
    """Test consistency of output format across different scenarios."""

    @pytest.fixture
    def processor(self):
        return XMLProcessor()

    def test_consistent_bundle_structure(self, processor, temp_xml_file):
        """Test that Bundle structure is consistent across formats."""
        formats_and_xmls = {
            'eClaimLink': '''<?xml version="1.0" encoding="UTF-8"?>
<PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
    <Header>
        <SenderID>CONSISTENCY_TEST</SenderID>
        <ReceiverID>PAYER999</ReceiverID>
        <TransactionDateTime>01/01/2025 12:00</TransactionDateTime>
        <TransactionID>CONSIST-ECLAIM</TransactionID>
    </Header>
</PriorAuthorizationRequest>''',
            'Shafafiya': '''<?xml version="1.0" encoding="UTF-8"?>
<Prior.Authorization xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <Header>
        <SenderID>CONSISTENCY_TEST</SenderID>
        <ReceiverID>PAYER999</ReceiverID>
        <TransactionDate>01/01/2025 12:00</TransactionDate>
        <RecordCount>1</RecordCount>
    </Header>
    <Authorization>
        <Result>Yes</Result>
        <ID>CONSIST-SHAF</ID>
    </Authorization>
</Prior.Authorization>''',
        }

        results = {}
        for format_name, xml_content in formats_and_xmls.items():
            xml_file = temp_xml_file(xml_content, f"test_{format_name.lower()}.xml")

            if format_name == 'eClaimLink':
                result = processor.process_eclaim_link(xml_file)
            else:
                result = processor.process_shafafiya(xml_file)

            results[format_name] = result

        # Test that all results have consistent Bundle structure
        for format_name, result in results.items():
            assert result['resourceType'] == 'Bundle'
            assert result['type'] == 'collection'
            assert 'id' in result
            assert 'meta' in result
            assert 'timestamp' in result
            assert 'raw_data' in result
            assert 'processing_timestamp' in result
            assert 'source_file' in result

            # Meta should have consistent structure
            meta = result['meta']
            assert 'source' in meta
            assert 'lastUpdated' in meta
            assert 'versionId' in meta
            assert 'profile' in meta
            assert meta['source'] == format_name


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
