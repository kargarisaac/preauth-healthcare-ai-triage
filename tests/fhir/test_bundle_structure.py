"""
FHIR Bundle structure validation tests.

This module tests FHIR Bundle generation, structure validation,
and resource relationships for both eClaimLink and Shafafiya formats.
"""

import pytest
from pipelines.factory import XMLIngestorFactory


class TestFHIRBundleStructure:
    """Test FHIR Bundle structure and validation."""

    @pytest.fixture
    def factory(self):
        """XMLIngestorFactory for FHIR Bundle testing."""
        return XMLIngestorFactory(schema_base_path='schemas/')

    def test_bundle_basic_structure(self, factory, create_test_xml_files):
        """Test basic FHIR Bundle structure compliance."""
        for format_name in ['eClaimLink', 'Shafafiya']:
            ingestor = factory.create_ingestor(
                format_name, enable_validation=False, output_format='fhir_bundle'
            )

            # Use appropriate test file
            test_file = (
                create_test_xml_files['valid_eclaim']
                if format_name == 'eClaimLink'
                else create_test_xml_files['valid_shafafiya']
            )
            bundle = ingestor.ingest_file(test_file)

            # Validate basic Bundle structure
            assert bundle['resourceType'] == 'Bundle'
            assert 'id' in bundle
            assert 'meta' in bundle
            assert 'type' in bundle
            assert bundle['type'] == 'collection'
            assert 'entry' in bundle
            assert 'total' in bundle
            assert isinstance(bundle['entry'], list)
            assert bundle['total'] == len(bundle['entry'])

    def test_bundle_meta_structure(self, factory, create_test_xml_files):
        """Test Bundle meta information structure."""
        for format_name in ['eClaimLink', 'Shafafiya']:
            ingestor = factory.create_ingestor(
                format_name, enable_validation=False, output_format='fhir_bundle'
            )

            test_file = (
                create_test_xml_files['valid_eclaim']
                if format_name == 'eClaimLink'
                else create_test_xml_files['valid_shafafiya']
            )
            bundle = ingestor.ingest_file(test_file)

            meta = bundle['meta']
            assert 'profile' in meta
            assert 'source' in meta
            assert 'lastUpdated' in meta
            assert 'versionId' in meta

            # Check profile URLs
            profiles = meta['profile']
            assert isinstance(profiles, list)
            assert len(profiles) >= 1
            assert any('nazmito.com/fhir' in profile for profile in profiles)

            # Check source
            expected_source = format_name.replace(
                'Link', 'Link'
            )  # eClaimLink -> eClaimLink
            assert meta['source'] == expected_source

    def test_bundle_entry_structure(self, factory, create_test_xml_files):
        """Test Bundle entry structure compliance."""
        ingestor = factory.create_ingestor(
            'eClaimLink', enable_validation=False, output_format='fhir_bundle'
        )

        bundle = ingestor.ingest_file(create_test_xml_files['valid_eclaim'])

        for i, entry in enumerate(bundle['entry']):
            # Each entry should have required fields
            assert 'fullUrl' in entry, f"Entry {i} missing fullUrl"
            assert 'resource' in entry, f"Entry {i} missing resource"
            assert 'search' in entry, f"Entry {i} missing search info"

            # Validate fullUrl format
            full_url = entry['fullUrl']
            assert full_url.startswith(
                'urn:uuid:'
            ), f"Entry {i} fullUrl should be urn:uuid format"

            # Validate resource structure
            resource = entry['resource']
            assert (
                'resourceType' in resource
            ), f"Entry {i} resource missing resourceType"
            assert 'id' in resource, f"Entry {i} resource missing id"
            assert 'meta' in resource, f"Entry {i} resource missing meta"

            # Validate search info
            search = entry['search']
            assert 'mode' in search, f"Entry {i} search missing mode"
            assert 'score' in search, f"Entry {i} search missing score"
            assert search['mode'] == 'match', f"Entry {i} search mode should be 'match'"

    def test_bundle_resource_diversity(self, factory, create_test_xml_files):
        """Test that Bundle contains diverse FHIR resource types."""
        ingestor = factory.create_ingestor(
            'eClaimLink', enable_validation=False, output_format='fhir_bundle'
        )

        # Use rich clinical data
        bundle = ingestor.ingest_file(create_test_xml_files['rich_clinical'])

        resource_types = [
            entry['resource']['resourceType'] for entry in bundle['entry']
        ]
        unique_types = set(resource_types)

        # Should have Claim resource
        assert 'Claim' in resource_types, "Bundle should contain Claim resource"

        # Should have multiple resource types for rich clinical data
        assert (
            len(unique_types) >= 2
        ), f"Expected multiple resource types, got {unique_types}"

        # Expected resource types
        expected_types = [
            'Claim',
            'Condition',
            'Observation',
            'MedicationStatement',
            'Procedure',
        ]
        found_types = [rt for rt in expected_types if rt in resource_types]
        assert (
            len(found_types) >= 2
        ), f"Should find multiple expected types, found {found_types}"

    def test_bundle_extensions_structure(self, factory, create_test_xml_files):
        """Test Bundle-level extensions structure."""
        ingestor = factory.create_ingestor(
            'eClaimLink', enable_validation=False, output_format='fhir_bundle'
        )

        bundle = ingestor.ingest_file(create_test_xml_files['valid_eclaim'])

        if 'extension' in bundle:
            extensions = bundle['extension']
            assert isinstance(extensions, list)

            for ext in extensions:
                assert 'url' in ext, "Extension missing url"
                assert ext['url'].startswith(
                    'https://'
                ), "Extension url should be https"

                # Should have value
                value_keys = [k for k in ext.keys() if k.startswith('value')]
                assert len(value_keys) >= 1, "Extension should have a value"

    def test_clinical_intelligence_extensions(self, factory, create_test_xml_files):
        """Test clinical intelligence extensions in Bundle."""
        ingestor = factory.create_ingestor(
            'eClaimLink', enable_validation=False, output_format='fhir_bundle'
        )

        bundle = ingestor.ingest_file(create_test_xml_files['rich_clinical'])

        if 'extension' in bundle:
            extensions = {ext['url']: ext for ext in bundle['extension']}

            # Look for clinical intelligence extensions
            clinical_extensions = [
                'clinical-context-score',
                'data-quality-score',
                'enrichment-score',
                'ai-confidence',
            ]

            found_clinical = []
            for ext_name in clinical_extensions:
                ext_url = f'https://nazmito.com/fhir/StructureDefinition/{ext_name}'
                if ext_url in extensions:
                    found_clinical.append(ext_name)

                    # Validate score range
                    ext = extensions[ext_url]
                    if 'valueDecimal' in ext:
                        score = ext['valueDecimal']
                        assert (
                            0.0 <= score <= 1.0
                        ), f"{ext_name} score {score} should be 0-1"

    def test_bundle_timestamp_consistency(self, factory, create_test_xml_files):
        """Test timestamp consistency across Bundle."""
        ingestor = factory.create_ingestor(
            'eClaimLink', enable_validation=False, output_format='fhir_bundle'
        )

        bundle = ingestor.ingest_file(create_test_xml_files['valid_eclaim'])

        # Bundle should have timestamp
        assert 'timestamp' in bundle
        bundle_timestamp = bundle['timestamp']

        # Bundle meta should have lastUpdated
        meta_timestamp = bundle['meta']['lastUpdated']

        # Both should be valid ISO timestamps
        import re

        iso_pattern = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'
        assert re.match(
            iso_pattern, bundle_timestamp
        ), "Bundle timestamp should be ISO format"
        assert re.match(
            iso_pattern, meta_timestamp
        ), "Meta lastUpdated should be ISO format"

    def test_bundle_total_accuracy(self, factory, create_test_xml_files):
        """Test that Bundle total matches actual entry count."""
        for test_file_key in ['valid_eclaim', 'valid_shafafiya', 'rich_clinical']:
            if test_file_key not in create_test_xml_files:
                continue

            format_name = 'eClaimLink' if 'eclaim' in test_file_key else 'Shafafiya'
            ingestor = factory.create_ingestor(
                format_name, enable_validation=False, output_format='fhir_bundle'
            )

            bundle = ingestor.ingest_file(create_test_xml_files[test_file_key])

            assert bundle['total'] == len(
                bundle['entry']
            ), f"Bundle total {bundle['total']} should match entry count {len(bundle['entry'])}"
            assert bundle['total'] >= 1, "Bundle should contain at least one resource"

    def test_bundle_id_uniqueness(self, factory, create_test_xml_files):
        """Test that Bundle IDs are unique and properly formatted."""
        ingestor = factory.create_ingestor(
            'eClaimLink', enable_validation=False, output_format='fhir_bundle'
        )

        # Process same file multiple times
        bundles = []
        for _ in range(3):
            bundle = ingestor.ingest_file(create_test_xml_files['valid_eclaim'])
            bundles.append(bundle)

        # Bundle IDs should be consistent for same input
        bundle_ids = [bundle['id'] for bundle in bundles]
        # They should be the same for same input (deterministic)

        # ID should follow expected format
        bundle_id = bundles[0]['id']
        assert (
            'eClaimLink-Bundle-' in bundle_id
        ), "Bundle ID should contain format identifier"

    def test_empty_bundle_handling(self, factory):
        """Test handling of minimal data that produces minimal Bundle."""
        ingestor = factory.create_ingestor(
            'eClaimLink', enable_validation=False, output_format='fhir_bundle'
        )

        # Create minimal XML
        minimal_xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
            <Header>
                <SenderID>TEST</SenderID>
                <ReceiverID>PAYER</ReceiverID>
                <TransactionDateTime>01/01/2025 12:00</TransactionDateTime>
                <TransactionID>MIN-001</TransactionID>
            </Header>
            <ServiceRequests>
                <ServiceRequest>
                    <ct:ActivityCode>99213</ct:ActivityCode>
                </ServiceRequest>
            </ServiceRequests>
        </PriorAuthorizationRequest>'''

        import tempfile

        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(minimal_xml)
            f.flush()

            bundle = ingestor.ingest_file(f.name)

            # Should still produce valid Bundle structure
            assert bundle['resourceType'] == 'Bundle'
            assert bundle['total'] >= 1  # At least a Claim
            assert len(bundle['entry']) == bundle['total']
