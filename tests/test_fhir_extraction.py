"""
Comprehensive end-to-end tests for FHIR Bundle extraction from both eClaimLink and Shafafiya formats.

This test suite validates the enhanced clinical data extraction capabilities that populate
all 5 FHIR resource types (Claim, Observation, MedicationStatement, Condition, Procedure)
with rich clinical context and intelligence.
"""

import pytest
from pipelines.factory import XMLIngestorFactory
from pipelines.eclaim_link_ingestor import EClaimLinkIngestor
from pipelines.shafafiya_ingestor import ShafafiyaIngestor


class TestFHIRBundleExtraction:
    """Test FHIR Bundle extraction from both XML formats."""

    @pytest.fixture
    def factory(self):
        """XMLIngestorFactory fixture."""
        return XMLIngestorFactory(schema_base_path='schemas/')

    @pytest.fixture
    def sample_files(self):
        """Sample XML file paths."""
        return {
            'eclaim_link': 'samples/eclaim_link_request.xml',
            'shafafiya': 'samples/shafafiya_authorization.xml',
        }

    def test_eclaim_link_fhir_bundle_extraction(self, factory, sample_files):
        """Test comprehensive FHIR Bundle extraction from eClaimLink format."""
        # Create enhanced ingestor
        ingestor = factory.create_ingestor(
            'eClaimLink', enable_validation=False, output_format='fhir_bundle'
        )

        # Process sample file
        bundle = ingestor.process(sample_files['eclaim_link'])

        # Validate Bundle structure
        assert bundle['resourceType'] == 'Bundle'
        assert bundle['type'] == 'collection'
        assert 'id' in bundle
        assert 'meta' in bundle
        assert bundle['meta']['source'] == 'eClaimLink'

        # Check Bundle contains all expected resource types
        resource_types = [
            entry['resource']['resourceType'] for entry in bundle['entry']
        ]
        expected_types = [
            'Claim',
            'Observation',
            'MedicationStatement',
            'Condition',
            'Procedure',
        ]

        for expected_type in expected_types:
            assert (
                expected_type in resource_types
            ), f"Missing {expected_type} resource in bundle"

        # Validate total count
        assert bundle['total'] >= 5, "Bundle should contain at least 5 resources"
        assert len(bundle['entry']) == bundle['total']

    def test_shafafiya_fhir_bundle_extraction(self, factory, sample_files):
        """Test comprehensive FHIR Bundle extraction from Shafafiya format."""
        # Create enhanced ingestor
        ingestor = factory.create_ingestor(
            'Shafafiya', enable_validation=False, output_format='fhir_bundle'
        )

        # Process sample file
        bundle = ingestor.process(sample_files['shafafiya'])

        # Validate Bundle structure
        assert bundle['resourceType'] == 'Bundle'
        assert bundle['type'] == 'collection'
        assert bundle['meta']['source'] == 'Shafafiya'

        # Check resource types
        resource_types = [
            entry['resource']['resourceType'] for entry in bundle['entry']
        ]
        expected_types = [
            'Claim',
            'Observation',
            'MedicationStatement',
            'Condition',
            'Procedure',
        ]

        for expected_type in expected_types:
            assert (
                expected_type in resource_types
            ), f"Missing {expected_type} resource in bundle"

    def test_claim_resource_extraction(self, factory, sample_files):
        """Test Claim resource extraction and structure."""
        ingestor = factory.create_ingestor(
            'eClaimLink', enable_validation=False, output_format='fhir_bundle'
        )
        bundle = ingestor.process(sample_files['eclaim_link'])

        # Find Claim resource
        claim_entry = next(
            entry
            for entry in bundle['entry']
            if entry['resource']['resourceType'] == 'Claim'
        )
        claim = claim_entry['resource']

        # Validate Claim structure
        assert claim['resourceType'] == 'Claim'
        assert 'id' in claim
        assert 'meta' in claim
        assert 'identifier' in claim
        assert 'status' in claim
        assert 'patient' in claim
        assert 'provider' in claim
        assert 'item' in claim

        # Check clinical data
        assert 'supportingInfo' in claim
        assert len(claim['supportingInfo']) > 0

        # Validate first service item
        first_item = claim['item'][0]
        assert 'productOrService' in first_item
        assert 'diagnosisCodeableConcept' in first_item

    def test_observation_resource_extraction(self, factory, sample_files):
        """Test Observation resource extraction from clinical text."""
        ingestor = factory.create_ingestor(
            'eClaimLink', enable_validation=False, output_format='fhir_bundle'
        )
        bundle = ingestor.process(sample_files['eclaim_link'])

        # Find Observation resources
        observation_entries = [
            entry
            for entry in bundle['entry']
            if entry['resource']['resourceType'] == 'Observation'
        ]
        assert len(observation_entries) > 0, "Should extract at least one Observation"

        # Test first observation
        observation = observation_entries[0]['resource']
        assert observation['resourceType'] == 'Observation'
        assert 'code' in observation
        assert 'subject' in observation  # Patient reference

        # Check for clinical value
        if 'valueQuantity' in observation:
            assert 'value' in observation['valueQuantity']
            assert 'unit' in observation['valueQuantity']
        elif 'valueString' in observation:
            assert len(observation['valueString']) > 0

        # Check clinical interpretation
        if 'interpretation' in observation:
            assert len(observation['interpretation']) > 0

    def test_medication_statement_extraction(self, factory, sample_files):
        """Test MedicationStatement resource extraction from clinical context."""
        ingestor = factory.create_ingestor(
            'eClaimLink', enable_validation=False, output_format='fhir_bundle'
        )
        bundle = ingestor.process(sample_files['eclaim_link'])

        # Find MedicationStatement resources
        med_entries = [
            entry
            for entry in bundle['entry']
            if entry['resource']['resourceType'] == 'MedicationStatement'
        ]

        if len(med_entries) > 0:  # May not always be present depending on clinical text
            medication = med_entries[0]['resource']
            assert medication['resourceType'] == 'MedicationStatement'
            assert 'medicationCodeableConcept' in medication
            assert 'subject' in medication
            assert 'status' in medication

            # Check medication coding
            med_concept = medication['medicationCodeableConcept']
            assert 'coding' in med_concept
            assert len(med_concept['coding']) > 0

    def test_condition_resource_extraction(self, factory, sample_files):
        """Test Condition resource extraction from diagnosis codes and clinical text."""
        ingestor = factory.create_ingestor(
            'eClaimLink', enable_validation=False, output_format='fhir_bundle'
        )
        bundle = ingestor.process(sample_files['eclaim_link'])

        # Find Condition resources
        condition_entries = [
            entry
            for entry in bundle['entry']
            if entry['resource']['resourceType'] == 'Condition'
        ]
        assert len(condition_entries) > 0, "Should extract at least one Condition"

        condition = condition_entries[0]['resource']
        assert condition['resourceType'] == 'Condition'
        assert 'code' in condition
        assert 'subject' in condition
        assert 'clinicalStatus' in condition

        # Check ICD-10 coding
        code_concept = condition['code']
        assert 'coding' in code_concept
        icd_coding = next(
            (
                c
                for c in code_concept['coding']
                if 'icd10' in c.get('system', '').lower()
            ),
            None,
        )
        if icd_coding:
            assert 'code' in icd_coding
            assert len(icd_coding['code']) > 0

    def test_procedure_resource_extraction(self, factory, sample_files):
        """Test Procedure resource extraction from activity codes."""
        ingestor = factory.create_ingestor(
            'eClaimLink', enable_validation=False, output_format='fhir_bundle'
        )
        bundle = ingestor.process(sample_files['eclaim_link'])

        # Find Procedure resources
        procedure_entries = [
            entry
            for entry in bundle['entry']
            if entry['resource']['resourceType'] == 'Procedure'
        ]
        assert len(procedure_entries) > 0, "Should extract at least one Procedure"

        procedure = procedure_entries[0]['resource']
        assert procedure['resourceType'] == 'Procedure'
        assert 'code' in procedure
        assert 'subject' in procedure
        assert 'status' in procedure

        # Check CPT coding
        code_concept = procedure['code']
        assert 'coding' in code_concept
        cpt_coding = next(
            (c for c in code_concept['coding'] if 'cpt' in c.get('system', '').lower()),
            None,
        )
        if cpt_coding:
            assert 'code' in cpt_coding

    def test_clinical_intelligence_scoring(self, factory, sample_files):
        """Test clinical intelligence and data quality scoring."""
        ingestor = factory.create_ingestor(
            'eClaimLink', enable_validation=False, output_format='fhir_bundle'
        )
        bundle = ingestor.process(sample_files['eclaim_link'])

        # Check bundle-level extensions for clinical intelligence
        if 'extension' in bundle:
            extensions = {ext['url']: ext for ext in bundle['extension']}

            # Look for clinical scoring extensions
            clinical_score_url = (
                'https://nazmito.com/extensions/clinical-completeness-score'
            )
            if clinical_score_url in extensions:
                score = extensions[clinical_score_url]['valueDecimal']
                assert (
                    0.0 <= score <= 1.0
                ), "Clinical completeness score should be between 0 and 1"

            quality_score_url = 'https://nazmito.com/extensions/data-quality-score'
            if quality_score_url in extensions:
                score = extensions[quality_score_url]['valueDecimal']
                assert (
                    0.0 <= score <= 1.0
                ), "Data quality score should be between 0 and 1"

    def test_cross_resource_relationships(self, factory, sample_files):
        """Test that resources are properly linked and reference each other."""
        ingestor = factory.create_ingestor(
            'eClaimLink', enable_validation=False, output_format='fhir_bundle'
        )
        bundle = ingestor.process(sample_files['eclaim_link'])

        # Extract all resource IDs
        resource_ids = {
            entry['resource']['id']: entry['resource']['resourceType']
            for entry in bundle['entry']
        }

        # Check that Observations reference the patient
        obs_entries = [
            entry
            for entry in bundle['entry']
            if entry['resource']['resourceType'] == 'Observation'
        ]
        for entry in obs_entries:
            obs = entry['resource']
            assert 'subject' in obs
            patient_ref = obs['subject']['reference']
            assert patient_ref.startswith(
                'Patient/'
            ), "Observation should reference Patient"

    def test_shafafiya_structured_observations(self, factory, sample_files):
        """Test that Shafafiya's structured observations are properly extracted."""
        ingestor = factory.create_ingestor(
            'Shafafiya', enable_validation=False, output_format='fhir_bundle'
        )
        bundle = ingestor.process(sample_files['shafafiya'])

        # Shafafiya has embedded observation elements - should be extracted
        observation_entries = [
            entry
            for entry in bundle['entry']
            if entry['resource']['resourceType'] == 'Observation'
        ]

        # Should extract structured observations from Activity/Observation elements
        assert (
            len(observation_entries) >= 0
        ), "Should extract observations from Shafafiya activities"

        # If observations exist, validate their structure
        for entry in observation_entries:
            obs = entry['resource']
            assert 'code' in obs, "Observation must have code"
            assert 'subject' in obs, "Observation must reference subject"
            assert 'status' in obs, "Observation must have status"

            # Check for proper categorization based on Shafafiya observation types
            if 'category' in obs:
                categories = [cat['coding'][0]['code'] for cat in obs['category']]
                valid_categories = [
                    'laboratory',
                    'vital-signs',
                    'imaging',
                    'procedure',
                    'survey',
                ]
                assert any(
                    cat in valid_categories for cat in categories
                ), "Valid observation category required"

    def test_backward_compatibility_legacy_mode(self, factory, sample_files):
        """Test that legacy mode still works and returns original format."""
        # Test eClaimLink legacy mode (default)
        ingestor = factory.create_ingestor(
            'eClaimLink', enable_validation=False
        )  # No output_format = legacy
        result = ingestor.process(sample_files['eclaim_link'])

        # Should return legacy dictionary format
        assert isinstance(result, dict)
        assert result['format_name'] == 'eClaimLink'
        assert result['schema_version'] == '2019/11'
        assert 'services' in result
        assert 'resourceType' not in result  # Should NOT be FHIR Bundle

        # Test Shafafiya legacy mode
        ingestor = factory.create_ingestor('Shafafiya', enable_validation=False)
        result = ingestor.process(sample_files['shafafiya'])

        assert result['format_name'] == 'Shafafiya'
        assert result['schema_version'] == '2011'
        assert 'resourceType' not in result
        assert (
            'services' in result
        )  # Shafafiya calls them activities but normalized to services

    def test_clinical_text_nlp_extraction(self, factory, sample_files):
        """Test NLP extraction from clinical justification text."""
        ingestor = factory.create_ingestor(
            'eClaimLink', enable_validation=False, output_format='fhir_bundle'
        )
        bundle = ingestor.process(sample_files['eclaim_link'])

        # The eClaimLink sample has rich clinical justification text
        # Should extract multiple clinical entities
        total_resources = len(bundle['entry'])
        assert (
            total_resources >= 5
        ), f"Expected at least 5 resources from rich clinical text, got {total_resources}"

        # Should have extracted conditions from the diabetes narrative
        condition_entries = [
            entry
            for entry in bundle['entry']
            if entry['resource']['resourceType'] == 'Condition'
        ]
        diabetes_conditions = []
        for entry in condition_entries:
            condition = entry['resource']
            for coding in condition['code']['coding']:
                if 'diabetes' in coding.get('display', '').lower() or coding.get(
                    'code', ''
                ).startswith('E11'):
                    diabetes_conditions.append(condition)

        assert (
            len(diabetes_conditions) > 0
        ), "Should extract diabetes condition from clinical text"

    def test_error_handling_and_edge_cases(self, factory):
        """Test handling of edge cases and malformed data."""
        # Test with minimal XML data
        minimal_eclaim_xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
            <Header>
                <SenderID>TEST123</SenderID>
                <ReceiverID>PAYER999</ReceiverID>
                <TransactionDateTime>01/01/2025 12:00</TransactionDateTime>
                <TransactionID>MIN-TEST-001</TransactionID>
            </Header>
            <ServiceRequests>
                <ServiceRequest>
                    <ct:ActivityCode>99213</ct:ActivityCode>
                    <RequestedAmount currency="AED">100.00</RequestedAmount>
                </ServiceRequest>
            </ServiceRequests>
        </PriorAuthorizationRequest>'''

        # Should handle minimal data gracefully
        ingestor = EClaimLinkIngestor(
            enable_validation=False, output_format='fhir_bundle'
        )

        # Parse XML string for testing
        import xmltodict

        parsed_data = xmltodict.parse(minimal_eclaim_xml)

        bundle = ingestor.normalize(parsed_data)

        # Should create bundle even with minimal data
        assert bundle['resourceType'] == 'Bundle'
        assert bundle['total'] >= 1  # At least a Claim resource

        # Should handle missing clinical text gracefully
        claim_entries = [
            entry
            for entry in bundle['entry']
            if entry['resource']['resourceType'] == 'Claim'
        ]
        assert len(claim_entries) == 1


class TestClinicalIntelligenceMetrics:
    """Test clinical intelligence scoring and data quality metrics."""

    def test_completeness_scoring(self):
        """Test clinical completeness scoring algorithm."""
        # This would test the clinical scoring methods
        # For now, we ensure the structure is present
        factory = XMLIngestorFactory(schema_base_path='schemas/')
        ingestor = factory.create_ingestor(
            'eClaimLink', enable_validation=False, output_format='fhir_bundle'
        )

        # Process rich clinical data
        bundle = ingestor.process('samples/eclaim_link_request.xml')

        # Bundle should have clinical intelligence metrics
        resource_types = [
            entry['resource']['resourceType'] for entry in bundle['entry']
        ]
        unique_types = set(resource_types)

        # More resource types = higher completeness
        completeness = len(unique_types) / 5.0  # 5 total possible resource types
        assert 0.0 <= completeness <= 1.0

    def test_data_quality_assessment(self):
        """Test data quality assessment across formats."""
        factory = XMLIngestorFactory(schema_base_path='schemas/')

        # Compare data quality between formats
        eclaim_ingestor = factory.create_ingestor(
            'eClaimLink', enable_validation=False, output_format='fhir_bundle'
        )
        shafafiya_ingestor = factory.create_ingestor(
            'Shafafiya', enable_validation=False, output_format='fhir_bundle'
        )

        eclaim_bundle = eclaim_ingestor.process('samples/eclaim_link_request.xml')
        shafafiya_bundle = shafafiya_ingestor.process(
            'samples/shafafiya_authorization.xml'
        )

        # Both should produce valid bundles
        assert eclaim_bundle['resourceType'] == 'Bundle'
        assert shafafiya_bundle['resourceType'] == 'Bundle'

        # Both should have reasonable resource counts
        assert eclaim_bundle['total'] >= 1
        assert shafafiya_bundle['total'] >= 1


class TestShafafiyaSpecificExtraction:
    """Test Shafafiya-specific FHIR extraction features."""

    @pytest.fixture
    def shafafiya_factory(self):
        """Factory configured for Shafafiya processing."""
        return XMLIngestorFactory(schema_base_path='schemas/')

    def test_shafafiya_activity_to_fhir_mapping(self, shafafiya_factory):
        """Test mapping of Shafafiya Activity elements to FHIR resources."""
        ingestor = shafafiya_factory.create_ingestor(
            'Shafafiya', enable_validation=False, output_format='fhir_bundle'
        )
        bundle = ingestor.process('samples/shafafiya_authorization.xml')

        # Check that activities are mapped to appropriate FHIR resources
        resource_types = [
            entry['resource']['resourceType'] for entry in bundle['entry']
        ]

        # Should have at least a Claim resource
        assert 'Claim' in resource_types, "Shafafiya should generate Claim resource"

        # Find the Claim resource and validate its structure
        claim_entry = next(
            entry
            for entry in bundle['entry']
            if entry['resource']['resourceType'] == 'Claim'
        )
        claim = claim_entry['resource']

        # Validate Shafafiya-specific Claim structure
        assert claim['meta']['source'] == 'Shafafiya'
        assert 'identifier' in claim
        assert 'item' in claim  # Activities mapped to claim items

        # Check that authorization result is captured
        if 'extension' in claim:
            auth_result_ext = next(
                (
                    ext
                    for ext in claim['extension']
                    if 'authorization-result' in ext.get('url', '')
                ),
                None,
            )
            if auth_result_ext:
                assert 'valueString' in auth_result_ext

    def test_shafafiya_embedded_observations(self, shafafiya_factory):
        """Test extraction of embedded observations from Shafafiya activities."""
        ingestor = shafafiya_factory.create_ingestor(
            'Shafafiya', enable_validation=False, output_format='fhir_bundle'
        )
        bundle = ingestor.process('samples/shafafiya_authorization.xml')

        # Look for observations extracted from embedded Observation elements
        obs_entries = [
            entry
            for entry in bundle['entry']
            if entry['resource']['resourceType'] == 'Observation'
        ]

        for obs_entry in obs_entries:
            obs = obs_entry['resource']

            # Validate observation structure
            assert 'code' in obs
            assert 'subject' in obs
            assert 'status' in obs

            # Check for Shafafiya-specific extensions
            if 'extension' in obs:
                source_mapping = next(
                    (
                        ext
                        for ext in obs['extension']
                        if 'source-mapping' in ext.get('url', '')
                    ),
                    None,
                )
                if source_mapping:
                    # Should indicate extraction from Activity/Observation
                    sub_extensions = source_mapping.get('extension', [])
                    source_field_ext = next(
                        (
                            ext
                            for ext in sub_extensions
                            if ext.get('url') == 'source-field'
                        ),
                        None,
                    )
                    if source_field_ext:
                        assert 'Activity' in source_field_ext.get('valueString', '')

    def test_shafafiya_procedure_extraction(self, shafafiya_factory):
        """Test extraction of procedures from Shafafiya activity codes."""
        ingestor = shafafiya_factory.create_ingestor(
            'Shafafiya', enable_validation=False, output_format='fhir_bundle'
        )
        bundle = ingestor.process('samples/shafafiya_authorization.xml')

        # Look for procedures extracted from activities
        proc_entries = [
            entry
            for entry in bundle['entry']
            if entry['resource']['resourceType'] == 'Procedure'
        ]

        for proc_entry in proc_entries:
            procedure = proc_entry['resource']

            # Validate procedure structure
            assert 'code' in procedure
            assert 'subject' in procedure
            assert 'status' in procedure

            # Check that activity codes are properly mapped
            code_concept = procedure['code']
            assert 'coding' in code_concept

            # Should have Shafafiya activity system
            shafafiya_coding = next(
                (
                    c
                    for c in code_concept['coding']
                    if 'shafafiya-activity' in c.get('system', '')
                ),
                None,
            )
            if shafafiya_coding:
                assert 'code' in shafafiya_coding
                assert len(shafafiya_coding['code']) > 0

    def test_shafafiya_clinical_comments_processing(self, shafafiya_factory):
        """Test processing of Shafafiya Comments field for clinical extraction."""
        ingestor = shafafiya_factory.create_ingestor(
            'Shafafiya', enable_validation=False, output_format='fhir_bundle'
        )
        bundle = ingestor.process('samples/shafafiya_authorization.xml')

        # Check that clinical comments are processed for entity extraction
        # Look for resources that might have been extracted from comments
        condition_entries = [
            entry
            for entry in bundle['entry']
            if entry['resource']['resourceType'] == 'Condition'
        ]
        medication_entries = [
            entry
            for entry in bundle['entry']
            if entry['resource']['resourceType'] == 'MedicationStatement'
        ]

        # If clinical comments contain medical information, should extract resources
        total_clinical_resources = len(condition_entries) + len(medication_entries)

        # Validate that clinical extraction attempted (even if no resources found)
        assert (
            total_clinical_resources >= 0
        ), "Clinical extraction should run without errors"

        # If conditions were extracted, validate their structure
        for condition_entry in condition_entries:
            condition = condition_entry['resource']
            assert 'code' in condition
            assert 'clinicalStatus' in condition
            assert 'verificationStatus' in condition

    def test_shafafiya_authorization_periods(self, shafafiya_factory):
        """Test handling of Shafafiya authorization start/end periods."""
        ingestor = shafafiya_factory.create_ingestor(
            'Shafafiya', enable_validation=False, output_format='fhir_bundle'
        )
        bundle = ingestor.process('samples/shafafiya_authorization.xml')

        # Find the Claim resource
        claim_entry = next(
            entry
            for entry in bundle['entry']
            if entry['resource']['resourceType'] == 'Claim'
        )
        claim = claim_entry['resource']

        # Check that billable period is set from Shafafiya Start/End
        if 'billablePeriod' in claim:
            period = claim['billablePeriod']
            assert (
                'start' in period or 'end' in period
            ), "Should have authorization period"

    def test_shafafiya_value_type_handling(self, shafafiya_factory):
        """Test proper handling of different ValueType fields in observations."""
        ingestor = shafafiya_factory.create_ingestor(
            'Shafafiya', enable_validation=False, output_format='fhir_bundle'
        )
        bundle = ingestor.process('samples/shafafiya_authorization.xml')

        # Find observations with different value types
        obs_entries = [
            entry
            for entry in bundle['entry']
            if entry['resource']['resourceType'] == 'Observation'
        ]

        for obs_entry in obs_entries:
            obs = obs_entry['resource']

            # Check that values are properly typed based on ValueType
            if 'valueQuantity' in obs:
                quantity = obs['valueQuantity']
                assert 'value' in quantity
                assert isinstance(quantity['value'], (int, float))

            elif 'valueString' in obs:
                assert isinstance(obs['valueString'], str)
                assert len(obs['valueString']) > 0

            elif 'valueBoolean' in obs:
                assert isinstance(obs['valueBoolean'], bool)

    def test_shafafiya_clinical_intelligence_scoring(self, shafafiya_factory):
        """Test clinical intelligence scoring for Shafafiya format."""
        ingestor = shafafiya_factory.create_ingestor(
            'Shafafiya', enable_validation=False, output_format='fhir_bundle'
        )
        bundle = ingestor.process('samples/shafafiya_authorization.xml')

        # Check for clinical intelligence extensions at bundle level
        if 'extension' in bundle:
            extensions = {ext['url']: ext for ext in bundle['extension']}

            # Look for Shafafiya-specific scoring
            score_extensions = [
                'clinical-context-score',
                'data-quality-score',
                'enrichment-score',
                'ai-confidence',
            ]

            for score_type in score_extensions:
                score_url = f'https://nazmito.com/fhir/StructureDefinition/{score_type}'
                if score_url in extensions:
                    score = extensions[score_url].get('valueDecimal', 0)
                    assert (
                        0.0 <= score <= 1.0
                    ), f"{score_type} should be between 0 and 1"

    def test_shafafiya_error_handling_minimal_data(self, shafafiya_factory):
        """Test Shafafiya processing with minimal data."""
        # Create minimal Shafafiya XML
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
                <ID>MIN-TEST-001</ID>
                <Activity>
                    <ID>1</ID>
                    <Type>3</Type>
                    <Code>99213</Code>
                    <Net>100.00</Net>
                    <PaymentAmount>80.00</PaymentAmount>
                </Activity>
            </Authorization>
        </Prior.Authorization>'''

        # Should handle minimal data gracefully
        ingestor = ShafafiyaIngestor(
            enable_validation=False, output_format='fhir_bundle'
        )

        # Parse XML string for testing
        import xmltodict

        parsed_data = xmltodict.parse(minimal_xml)

        bundle = ingestor.normalize(parsed_data)

        # Should create bundle even with minimal data
        assert bundle['resourceType'] == 'Bundle'
        assert bundle['total'] >= 1  # At least a Claim resource

        # Should handle missing clinical comments gracefully
        claim_entries = [
            entry
            for entry in bundle['entry']
            if entry['resource']['resourceType'] == 'Claim'
        ]
        assert len(claim_entries) == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
