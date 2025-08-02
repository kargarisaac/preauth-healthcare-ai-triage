"""
End-to-end integration tests for the XMLProcessor.

This module tests the complete XML processing workflow using
the simplified XMLProcessor class for both eClaimLink and Shafafiya formats.
"""

import pytest
import tempfile
import os
from pathlib import Path
from pipelines.xml_processor import XMLProcessor


class TestEndToEndProcessing:
    """Test complete end-to-end processing workflows."""

    @pytest.fixture
    def processor(self):
        """XMLProcessor for end-to-end testing."""
        return XMLProcessor()

    @pytest.fixture
    def sample_files(self):
        """Paths to sample XML files."""
        project_root = Path(__file__).parent.parent.parent
        return {
            'eclaim_link': project_root / "samples" / "eclaim_link_request.xml",
            'shafafiya': project_root / "samples" / "shafafiya_prior_auth_request.xml",
        }

    def test_complete_eclaim_processing_workflow(self, processor, sample_files):
        """Test complete eClaimLink processing from XML to Bundle."""
        xml_path = sample_files['eclaim_link']
        if not xml_path.exists():
            pytest.skip("eClaimLink sample file not found")

        # Process file to Bundle
        bundle = processor.process_eclaim_link(str(xml_path))

        # Validate complete workflow results
        assert bundle['resourceType'] == 'Bundle'
        assert bundle['type'] == 'collection'
        assert 'meta' in bundle
        assert bundle['meta']['source'] == 'eClaimLink'
        assert 'authorization_id' in bundle
        assert 'services' in bundle
        assert len(bundle['services']) >= 0

        # Validate raw data preservation
        assert 'raw_data' in bundle
        assert 'PriorAuthorizationRequest' in bundle['raw_data']

    def test_complete_shafafiya_processing_workflow(self, processor, sample_files):
        """Test complete Shafafiya processing from XML to Bundle."""
        xml_path = sample_files['shafafiya']
        if not xml_path.exists():
            pytest.skip("Shafafiya sample file not found")

        # Process file to Bundle
        bundle = processor.process_shafafiya(str(xml_path))

        # Validate complete workflow results
        assert bundle['resourceType'] == 'Bundle'
        assert bundle['type'] == 'collection'
        assert 'meta' in bundle
        assert bundle['meta']['source'] == 'Shafafiya'
        assert 'authorization_id' in bundle
        assert 'activities' in bundle
        assert len(bundle['activities']) >= 0

        # Validate raw data preservation
        assert 'raw_data' in bundle
        assert 'Prior.Authorization' in bundle['raw_data']

    def test_dual_format_consistency(self, processor, temp_xml_file):
        """Test that both formats produce consistent Bundle structures."""
        # Create test XMLs
        eclaim_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
    <Header>
        <SenderID>PROV12345</SenderID>
        <ReceiverID>PAYER67890</ReceiverID>
        <TransactionDateTime>27/07/2025 10:32</TransactionDateTime>
        <TransactionID>TXN-CONSISTENCY</TransactionID>
    </Header>
    <ServiceRequests>
        <ServiceRequest>
            <ct:ActivityCode>83036</ct:ActivityCode>
        </ServiceRequest>
    </ServiceRequests>
</PriorAuthorizationRequest>'''

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
        <ID>PA-CONSISTENCY</ID>
        <Activity>
            <ID>1</ID>
            <Code>83036</Code>
        </Activity>
    </Authorization>
</Prior.Authorization>'''

        eclaim_file = temp_xml_file(eclaim_xml, "test_eclaim.xml")
        shafafiya_file = temp_xml_file(shafafiya_xml, "test_shafafiya.xml")

        eclaim_bundle = processor.process_eclaim_link(eclaim_file)
        shafafiya_bundle = processor.process_shafafiya(shafafiya_file)

        # Compare bundle structures
        for bundle in [eclaim_bundle, shafafiya_bundle]:
            # Basic Bundle structure should be consistent
            assert bundle['resourceType'] == 'Bundle'
            assert bundle['type'] == 'collection'
            assert 'meta' in bundle
            assert 'id' in bundle
            assert 'timestamp' in bundle
            assert 'raw_data' in bundle

    def test_error_handling_and_recovery(self, processor):
        """Test error handling for invalid XML files."""
        # Test missing file
        with pytest.raises(FileNotFoundError):
            processor.process_eclaim_link("nonexistent_file.xml")

        with pytest.raises(FileNotFoundError):
            processor.process_shafafiya("nonexistent_file.xml")

        # Test invalid XML content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write("Invalid XML content")
            f.flush()

            try:
                with pytest.raises(Exception):  # Should raise XML parsing error
                    processor.process_eclaim_link(f.name)
            finally:
                os.unlink(f.name)

    def test_processing_performance(self, processor, temp_xml_file):
        """Test processing performance for reasonably sized files."""
        import time

        # Create a moderately complex XML
        eclaim_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
    <Header>
        <SenderID>PROV12345</SenderID>
        <ReceiverID>PAYER67890</ReceiverID>
        <TransactionDateTime>27/07/2025 10:32</TransactionDateTime>
        <TransactionID>TXN-PERF-TEST</TransactionID>
    </Header>
    <JustificationText>Performance test with longer text content to simulate real-world processing scenarios.</JustificationText>
    <ServiceRequests>'''

        # Add multiple services for performance testing
        for i in range(1, 6):  # 5 services
            eclaim_xml += f'''
        <ServiceRequest>
            <ct:ActivityCode>8303{i}</ct:ActivityCode>
            <ct:DiagnosisCode>E11.{i}</ct:DiagnosisCode>
            <ct:ActivityDateTime>28/07/2025 09:00</ct:ActivityDateTime>
            <ct:ActivityInstructions>Service {i} instructions for performance testing</ct:ActivityInstructions>
            <RequestedAmount currency="AED">{100 + i * 10}.00</RequestedAmount>
        </ServiceRequest>'''

        eclaim_xml += '''
    </ServiceRequests>
</PriorAuthorizationRequest>'''

        xml_file = temp_xml_file(eclaim_xml, "perf_test.xml")

        # Measure processing time
        start_time = time.time()
        result = processor.process_eclaim_link(xml_file)
        end_time = time.time()

        processing_time = end_time - start_time

        # Validate results
        assert result['resourceType'] == 'Bundle'
        assert len(result['services']) == 5

        # Performance should be reasonable (under 5 seconds for this small file)
        assert (
            processing_time < 5.0
        ), f"Processing took {processing_time:.2f}s, expected < 5.0s"

    def test_data_integrity_preservation(self, processor, temp_xml_file):
        """Test that all data is preserved during processing."""
        # Create XML with special characters and various data types
        complex_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
    <Header>
        <SenderID>PROV_Special@123</SenderID>
        <ReceiverID>PAYER-999#Test</ReceiverID>
        <TransactionDateTime>27/07/2025 10:32</TransactionDateTime>
        <TransactionID>TXN-INTEGRITY-&amp;-TEST</TransactionID>
    </Header>
    <JustificationText>Patient with special characters: &lt;test&gt; &amp; symbols. Unicode: ñáéíóú</JustificationText>
    <ServiceRequests>
        <ServiceRequest>
            <ct:ActivityCode>83036</ct:ActivityCode>
            <ct:DiagnosisCode>E11.9</ct:DiagnosisCode>
            <RequestedAmount currency="AED">1234.56</RequestedAmount>
        </ServiceRequest>
    </ServiceRequests>
</PriorAuthorizationRequest>'''

        xml_file = temp_xml_file(complex_xml, "integrity_test.xml")
        result = processor.process_eclaim_link(xml_file)

        # Verify essential data is preserved
        assert result['sender'] == 'PROV_Special@123'
        assert result['receiver'] == 'PAYER-999#Test'
        assert result['authorization_id'] == 'TXN-INTEGRITY-&-TEST'
        assert 'Patient with special characters' in result['justification_text']
        assert 'Unicode: ñáéíóú' in result['justification_text']

        # Verify raw data preservation
        raw_header = result['raw_data']['PriorAuthorizationRequest']['Header']
        assert raw_header['SenderID'] == 'PROV_Special@123'
        assert raw_header['TransactionID'] == 'TXN-INTEGRITY-&-TEST'

    def test_concurrent_processing(self, processor, temp_xml_file):
        """Test concurrent processing of multiple files."""
        import threading
        import queue

        results = queue.Queue()

        def process_eclaim():
            try:
                xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
    <Header>
        <SenderID>CONCURRENT1</SenderID>
        <ReceiverID>PAYER67890</ReceiverID>
        <TransactionDateTime>27/07/2025 10:32</TransactionDateTime>
        <TransactionID>TXN-CONCURRENT-1</TransactionID>
    </Header>
    <ServiceRequests>
        <ServiceRequest>
            <ct:ActivityCode>83036</ct:ActivityCode>
        </ServiceRequest>
    </ServiceRequests>
</PriorAuthorizationRequest>'''
                xml_file = temp_xml_file(xml_content, "concurrent_eclaim.xml")
                result = processor.process_eclaim_link(xml_file)
                results.put(("eclaim", result, None))
            except Exception as e:
                results.put(("eclaim", None, str(e)))

        def process_shafafiya():
            try:
                xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<Prior.Authorization xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <Header>
        <SenderID>CONCURRENT2</SenderID>
        <ReceiverID>PAYER67890</ReceiverID>
        <TransactionDate>27/07/2025 10:32</TransactionDate>
        <RecordCount>1</RecordCount>
    </Header>
    <Authorization>
        <Result>Yes</Result>
        <ID>PA-CONCURRENT-2</ID>
        <Activity>
            <ID>1</ID>
            <Code>83036</Code>
        </Activity>
    </Authorization>
</Prior.Authorization>'''
                xml_file = temp_xml_file(xml_content, "concurrent_shafafiya.xml")
                result = processor.process_shafafiya(xml_file)
                results.put(("shafafiya", result, None))
            except Exception as e:
                results.put(("shafafiya", None, str(e)))

        # Start concurrent processing
        thread1 = threading.Thread(target=process_eclaim)
        thread2 = threading.Thread(target=process_shafafiya)

        thread1.start()
        thread2.start()

        thread1.join()
        thread2.join()

        # Collect results
        processed_results = []
        while not results.empty():
            processed_results.append(results.get())

        assert len(processed_results) == 2

        # Validate concurrent processing results
        for format_name, bundle, error in processed_results:
            assert (
                error is None
            ), f"Concurrent processing failed for {format_name}: {error}"
            assert bundle is not None
            assert bundle['resourceType'] == 'Bundle'

            if format_name == "eclaim":
                assert bundle['authorization_id'] == 'TXN-CONCURRENT-1'
                assert bundle['sender'] == 'CONCURRENT1'
            else:  # shafafiya
                assert bundle['authorization_id'] == 'PA-CONCURRENT-2'
                assert bundle['sender'] == 'CONCURRENT2'

    def test_large_file_handling(self, processor, temp_xml_file):
        """Test handling of larger XML files."""
        # Create a larger XML with many services/activities
        large_eclaim_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
    <Header>
        <SenderID>PROV12345</SenderID>
        <ReceiverID>PAYER67890</ReceiverID>
        <TransactionDateTime>27/07/2025 10:32</TransactionDateTime>
        <TransactionID>TXN-LARGE-FILE</TransactionID>
    </Header>
    <JustificationText>Large file test with multiple services to validate performance and memory usage.</JustificationText>
    <ServiceRequests>'''

        # Add 20 services
        for i in range(1, 21):
            large_eclaim_xml += f'''
        <ServiceRequest>
            <ct:ActivityCode>8303{i % 10}</ct:ActivityCode>
            <ct:DiagnosisCode>E11.{i % 10}</ct:DiagnosisCode>
            <ct:ActivityDateTime>28/07/2025 09:00</ct:ActivityDateTime>
            <ct:ActivityInstructions>Service {i} for large file testing with detailed instructions</ct:ActivityInstructions>
            <RequestedAmount currency="AED">{100 + i * 5}.00</RequestedAmount>
        </ServiceRequest>'''

        large_eclaim_xml += '''
    </ServiceRequests>
</PriorAuthorizationRequest>'''

        xml_file = temp_xml_file(large_eclaim_xml, "large_test.xml")
        result = processor.process_eclaim_link(xml_file)

        # Validate processing of large file
        assert result['resourceType'] == 'Bundle'
        assert len(result['services']) == 20
        assert result['authorization_id'] == 'TXN-LARGE-FILE'

        # Verify all services are processed correctly
        for i, service in enumerate(result['services'], 1):
            assert service['sequence'] == i
            assert service['activity_code'] == f'8303{i % 10}'
            assert service['requested_amount_value'] == f'{100 + i * 5}.00'
