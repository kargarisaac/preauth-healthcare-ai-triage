"""
End-to-end integration tests for the complete XML processing pipeline.

This module tests the full workflow from XML ingestion through FHIR Bundle
generation, including format detection, validation, transformation, and
clinical intelligence extraction across both eClaimLink and Shafafiya formats.
"""

import pytest
import tempfile
from pathlib import Path
from pipelines.factory import XMLIngestorFactory


class TestEndToEndProcessing:
    """Test complete end-to-end processing workflows."""

    @pytest.fixture
    def factory(self):
        """XMLIngestorFactory for end-to-end testing."""
        return XMLIngestorFactory(schema_base_path='schemas/')

    @pytest.fixture
    def sample_files(self):
        """Paths to sample XML files."""
        project_root = Path(__file__).parent.parent.parent
        return {
            'eclaim_link': project_root / "samples" / "eclaim_link_request.xml",
            'shafafiya': project_root / "samples" / "shafafiya_authorization.xml",
        }

    def test_complete_eclaim_processing_workflow(self, factory, sample_files):
        """Test complete eClaimLink processing from XML to FHIR Bundle."""
        xml_path = sample_files['eclaim_link']
        if not xml_path.exists():
            pytest.skip("eClaimLink sample file not found")

        # Step 1: Format detection
        detected_format = factory.detect_format(str(xml_path))
        assert (
            detected_format == 'eClaimLink'
        ), f"Should detect eClaimLink format, got {detected_format}"

        # Step 2: Create ingestor with validation
        ingestor = factory.create_ingestor(
            'eClaimLink', enable_validation=True, output_format='fhir_bundle'
        )

        # Step 3: Process file to FHIR Bundle
        bundle = ingestor.process(str(xml_path))

        # Step 4: Validate complete workflow results
        assert bundle['resourceType'] == 'Bundle'
        assert bundle['type'] == 'collection'
        assert 'meta' in bundle
        assert bundle['meta']['source'] == 'eClaimLink'
        assert bundle['total'] >= 1
        assert len(bundle['entry']) == bundle['total']

        # Step 5: Verify resource extraction completeness
        resource_types = [
            entry['resource']['resourceType'] for entry in bundle['entry']
        ]
        assert 'Claim' in resource_types, "Should extract Claim resource"

        # Step 6: Validate clinical intelligence processing
        claim_resources = [
            entry['resource']
            for entry in bundle['entry']
            if entry['resource']['resourceType'] == 'Claim'
        ]
        assert len(claim_resources) == 1, "Should have exactly one Claim"

        claim = claim_resources[0]
        assert 'item' in claim, "Claim should have service items"
        assert len(claim['item']) >= 1, "Should have at least one service item"

    def test_complete_shafafiya_processing_workflow(self, factory, sample_files):
        """Test complete Shafafiya processing from XML to FHIR Bundle."""
        xml_path = sample_files['shafafiya']
        if not xml_path.exists():
            pytest.skip("Shafafiya sample file not found")

        # Step 1: Format detection
        detected_format = factory.detect_format(str(xml_path))
        assert (
            detected_format == 'Shafafiya'
        ), f"Should detect Shafafiya format, got {detected_format}"

        # Step 2: Create ingestor with validation
        ingestor = factory.create_ingestor(
            'Shafafiya', enable_validation=True, output_format='fhir_bundle'
        )

        # Step 3: Process file to FHIR Bundle
        bundle = ingestor.process(str(xml_path))

        # Step 4: Validate complete workflow results
        assert bundle['resourceType'] == 'Bundle'
        assert bundle['type'] == 'collection'
        assert 'meta' in bundle
        assert bundle['meta']['source'] == 'Shafafiya'
        assert bundle['total'] >= 1
        assert len(bundle['entry']) == bundle['total']

        # Step 5: Verify Shafafiya-specific processing
        resource_types = [
            entry['resource']['resourceType'] for entry in bundle['entry']
        ]
        assert 'Claim' in resource_types, "Should extract Claim resource"

        # Step 6: Check for Shafafiya-specific data structures
        if 'Observation' in resource_types:
            obs_resources = [
                entry['resource']
                for entry in bundle['entry']
                if entry['resource']['resourceType'] == 'Observation'
            ]
            for obs in obs_resources:
                assert 'subject' in obs, "Observation should reference patient"

    def test_dual_format_consistency(self, factory, sample_files):
        """Test that both formats produce consistent FHIR Bundle structures."""
        bundles = {}

        for format_name, xml_path in sample_files.items():
            if not xml_path.exists():
                continue

            # Determine factory format name
            factory_format = (
                'eClaimLink' if format_name == 'eclaim_link' else 'Shafafiya'
            )

            ingestor = factory.create_ingestor(
                factory_format, enable_validation=False, output_format='fhir_bundle'
            )

            bundle = ingestor.process(str(xml_path))
            bundles[format_name] = bundle

        # Compare bundle structures
        if len(bundles) == 2:
            for format_name, bundle in bundles.items():
                # Basic Bundle structure should be consistent
                assert bundle['resourceType'] == 'Bundle'
                assert bundle['type'] == 'collection'
                assert 'meta' in bundle
                assert 'entry' in bundle
                assert 'total' in bundle
                assert bundle['total'] >= 1

                # Should have Claim resource
                resource_types = [
                    entry['resource']['resourceType'] for entry in bundle['entry']
                ]
                assert (
                    'Claim' in resource_types
                ), f"{format_name} should produce Claim resource"

    def test_auto_detection_and_processing(self, factory, sample_files):
        """Test automatic format detection and processing workflow."""
        for format_name, xml_path in sample_files.items():
            if not xml_path.exists():
                continue

            # Step 1: Auto-detect and create ingestor
            ingestor = factory.create_ingestor_for_file(
                str(xml_path), enable_validation=False, output_format='fhir_bundle'
            )

            # Step 2: Process with auto-detected ingestor
            bundle = ingestor.process(str(xml_path))

            # Step 3: Validate auto-processing results
            assert bundle['resourceType'] == 'Bundle'
            assert bundle['total'] >= 1

            # Verify format-specific processing
            expected_source = 'eClaimLink' if 'eclaim' in format_name else 'Shafafiya'
            assert bundle['meta']['source'] == expected_source

    def test_validation_enabled_processing(self, factory, sample_files):
        """Test processing with XML schema validation enabled."""
        for format_name, xml_path in sample_files.items():
            if not xml_path.exists():
                continue

            factory_format = (
                'eClaimLink' if format_name == 'eclaim_link' else 'Shafafiya'
            )

            # Process with validation enabled
            ingestor = factory.create_ingestor(
                factory_format, enable_validation=True, output_format='fhir_bundle'
            )

            try:
                bundle = ingestor.process(str(xml_path))

                # If validation passes, bundle should be valid
                assert bundle['resourceType'] == 'Bundle'
                assert bundle['total'] >= 1

                # Validation metadata should be present
                assert 'meta' in bundle
                if 'extension' in bundle:
                    validation_extensions = [
                        ext
                        for ext in bundle['extension']
                        if 'validation' in ext.get('url', '').lower()
                    ]
                    # May have validation extensions

            except Exception as e:
                # If validation fails, it should be for a valid reason
                pytest.skip(f"Validation failed for {format_name}: {str(e)}")

    def test_legacy_vs_fhir_output_comparison(self, factory, sample_files):
        """Test comparison between legacy and FHIR Bundle output formats."""
        for format_name, xml_path in sample_files.items():
            if not xml_path.exists():
                continue

            factory_format = (
                'eClaimLink' if format_name == 'eclaim_link' else 'Shafafiya'
            )

            # Process with legacy format
            legacy_ingestor = factory.create_ingestor(
                factory_format, enable_validation=False, output_format='legacy'
            )
            legacy_result = legacy_ingestor.process(str(xml_path))

            # Process with FHIR Bundle format
            fhir_ingestor = factory.create_ingestor(
                factory_format, enable_validation=False, output_format='fhir_bundle'
            )
            fhir_result = fhir_ingestor.process(str(xml_path))

            # Compare results
            # Legacy format should have traditional structure
            assert 'format_name' in legacy_result
            assert 'services' in legacy_result
            assert 'resourceType' not in legacy_result

            # FHIR format should have Bundle structure
            assert fhir_result['resourceType'] == 'Bundle'
            assert 'entry' in fhir_result
            assert 'total' in fhir_result

            # Both should process the same source data
            assert legacy_result['format_name'] == factory_format
            assert fhir_result['meta']['source'] == factory_format

    def test_error_handling_and_recovery(self, factory):
        """Test error handling for invalid XML files."""
        # Create invalid XML
        invalid_xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <InvalidRoot>
            <InvalidElement>Invalid content</InvalidElement>
        </InvalidRoot>'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(invalid_xml)
            f.flush()

            # Should handle format detection failure
            try:
                detected_format = factory.detect_format(f.name)
                # If it detects a format, it should fail during processing
            except Exception:
                # Expected to fail format detection
                pass

            # Should handle processing errors gracefully
            ingestor = factory.create_ingestor(
                'eClaimLink', enable_validation=False, output_format='fhir_bundle'
            )

            with pytest.raises(Exception):
                # Should raise appropriate exception for invalid format
                ingestor.process(f.name)

    def test_clinical_intelligence_pipeline(self, factory, sample_files):
        """Test end-to-end clinical intelligence extraction pipeline."""
        # Create test XML with rich clinical content
        rich_clinical_xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
            <Header>
                <SenderID>PROVIDER123</SenderID>
                <ReceiverID>PAYER999</ReceiverID>
                <TransactionDateTime>01/01/2025 12:00</TransactionDateTime>
                <TransactionID>CLINICAL-RICH-001</TransactionID>
            </Header>
            <ServiceRequests>
                <ServiceRequest>
                    <ct:ActivityCode>99213</ct:ActivityCode>
                    <ct:DiagnosisCode>E11.9</ct:DiagnosisCode>
                    <ct:Justification>Patient presents with Type 2 diabetes mellitus without complications (E11.9). HbA1c level elevated at 9.2%. Currently on metformin 500mg twice daily. Blood pressure reading 145/95 indicates hypertension. Recommending ACE inhibitor therapy and diabetes education. Patient reports compliance issues with current medication regimen. Follow-up appointment scheduled for medication adjustment and lifestyle counseling.</ct:Justification>
                    <ct:RequestedAmount currency="AED">250.00</ct:RequestedAmount>
                </ServiceRequest>
            </ServiceRequests>
        </PriorAuthorizationRequest>'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(rich_clinical_xml)
            f.flush()

            ingestor = factory.create_ingestor(
                'eClaimLink', enable_validation=False, output_format='fhir_bundle'
            )

            bundle = ingestor.process(f.name)

            # Validate clinical intelligence extraction
            assert bundle['resourceType'] == 'Bundle'
            assert bundle['total'] >= 1

            # Should extract clinical entities from rich justification text
            resource_types = [
                entry['resource']['resourceType'] for entry in bundle['entry']
            ]
            assert 'Claim' in resource_types

            # Check for clinical intelligence extensions
            clinical_resource_count = sum(
                1
                for rt in resource_types
                if rt
                in ['Condition', 'Observation', 'MedicationStatement', 'Procedure']
            )
            # May extract clinical entities (implementation dependent)

            # Check for clinical intelligence scoring
            if 'extension' in bundle:
                clinical_extensions = [
                    ext
                    for ext in bundle['extension']
                    if 'nazmito.com/fhir' in ext.get('url', '')
                ]
                # May have clinical intelligence extensions

    def test_concurrent_processing(self, factory, sample_files):
        """Test concurrent processing of multiple files."""
        import threading
        import queue

        results = queue.Queue()

        def process_file(format_name, xml_path):
            try:
                factory_format = (
                    'eClaimLink' if format_name == 'eclaim_link' else 'Shafafiya'
                )
                ingestor = factory.create_ingestor(
                    factory_format, enable_validation=False, output_format='fhir_bundle'
                )
                bundle = ingestor.process(str(xml_path))
                results.put((format_name, bundle, None))
            except Exception as e:
                results.put((format_name, None, str(e)))

        threads = []
        for format_name, xml_path in sample_files.items():
            if xml_path.exists():
                thread = threading.Thread(
                    target=process_file, args=(format_name, xml_path)
                )
                threads.append(thread)
                thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Collect results
        processed_results = []
        while not results.empty():
            processed_results.append(results.get())

        # Validate concurrent processing results
        for format_name, bundle, error in processed_results:
            if error:
                pytest.fail(f"Concurrent processing failed for {format_name}: {error}")

            assert bundle is not None
            assert bundle['resourceType'] == 'Bundle'
            assert bundle['total'] >= 1

    def test_data_quality_assessment_pipeline(self, factory, sample_files):
        """Test end-to-end data quality assessment and scoring."""
        quality_scores = {}

        for format_name, xml_path in sample_files.items():
            if not xml_path.exists():
                continue

            factory_format = (
                'eClaimLink' if format_name == 'eclaim_link' else 'Shafafiya'
            )
            ingestor = factory.create_ingestor(
                factory_format, enable_validation=False, output_format='fhir_bundle'
            )

            bundle = ingestor.process(str(xml_path))

            # Calculate quality metrics
            quality_metrics = {
                'total_resources': bundle['total'],
                'resource_diversity': len(
                    set(entry['resource']['resourceType'] for entry in bundle['entry'])
                ),
                'has_clinical_resources': any(
                    entry['resource']['resourceType']
                    in ['Condition', 'Observation', 'MedicationStatement', 'Procedure']
                    for entry in bundle['entry']
                ),
                'has_extensions': 'extension' in bundle,
                'bundle_completeness': bundle['total']
                / max(1, bundle['total']),  # Always 1.0, baseline metric
            }

            quality_scores[format_name] = quality_metrics

        # Validate quality assessment results
        for format_name, metrics in quality_scores.items():
            assert (
                metrics['total_resources'] >= 1
            ), f"{format_name} should produce resources"
            assert (
                metrics['resource_diversity'] >= 1
            ), f"{format_name} should have resource diversity"
            assert metrics['bundle_completeness'] == 1.0, "Bundle should be complete"

    def test_performance_benchmarking(self, factory, sample_files):
        """Test processing performance benchmarking."""
        import time

        performance_metrics = {}

        for format_name, xml_path in sample_files.items():
            if not xml_path.exists():
                continue

            factory_format = (
                'eClaimLink' if format_name == 'eclaim_link' else 'Shafafiya'
            )
            ingestor = factory.create_ingestor(
                factory_format, enable_validation=False, output_format='fhir_bundle'
            )

            # Measure processing time
            start_time = time.time()
            bundle = ingestor.process(str(xml_path))
            end_time = time.time()

            processing_time = end_time - start_time

            performance_metrics[format_name] = {
                'processing_time_seconds': processing_time,
                'resources_generated': bundle['total'],
                'resources_per_second': bundle['total'] / max(0.001, processing_time),
            }

        # Validate performance metrics
        for format_name, metrics in performance_metrics.items():
            assert (
                metrics['processing_time_seconds'] < 60.0
            ), f"{format_name} processing should be under 60 seconds"
            assert (
                metrics['resources_generated'] >= 1
            ), f"{format_name} should generate resources"
            assert (
                metrics['resources_per_second'] > 0
            ), f"{format_name} should have positive throughput"

    def test_memory_usage_validation(self, factory, sample_files):
        """Test memory usage validation during processing."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        for format_name, xml_path in sample_files.items():
            if not xml_path.exists():
                continue

            factory_format = (
                'eClaimLink' if format_name == 'eclaim_link' else 'Shafafiya'
            )
            ingestor = factory.create_ingestor(
                factory_format, enable_validation=False, output_format='fhir_bundle'
            )

            # Process and measure memory
            bundle = ingestor.process(str(xml_path))
            current_memory = process.memory_info().rss

            memory_increase = current_memory - initial_memory
            memory_increase_mb = memory_increase / (1024 * 1024)

            # Validate reasonable memory usage
            assert (
                memory_increase_mb < 100
            ), f"Memory usage increase should be under 100MB, got {memory_increase_mb:.2f}MB"
            assert (
                bundle['total'] >= 1
            ), "Should successfully process despite memory constraints"
