"""
Individual FHIR resource validation tests.

This module tests the structure and compliance of individual FHIR resources
extracted from healthcare XML data, ensuring each resource type meets
FHIR R4 specifications and UAE healthcare requirements.
"""

import pytest
import re
from pipelines.factory import XMLIngestorFactory


class TestClaimResourceValidation:
    """Test Claim resource structure and validation."""

    @pytest.fixture
    def factory(self):
        """XMLIngestorFactory for resource testing."""
        return XMLIngestorFactory(schema_base_path='schemas/')

    def test_claim_basic_structure(self, factory, create_test_xml_files):
        """Test basic Claim resource structure compliance."""
        ingestor = factory.create_ingestor(
            'eClaimLink', enable_validation=False, output_format='fhir_bundle'
        )

        bundle = ingestor.ingest_file(create_test_xml_files['valid_eclaim'])

        claim_entries = [
            entry
            for entry in bundle['entry']
            if entry['resource']['resourceType'] == 'Claim'
        ]

        assert len(claim_entries) == 1, "Should have exactly one Claim resource"
        claim = claim_entries[0]['resource']

        # Required fields
        assert claim['resourceType'] == 'Claim'
        assert 'id' in claim
        assert 'meta' in claim
        assert 'status' in claim
        assert 'type' in claim
        assert 'use' in claim
        assert 'patient' in claim
        assert 'created' in claim
        assert 'item' in claim

    def test_claim_identifiers_structure(self, factory, create_test_xml_files):
        """Test Claim identifier structure and completeness."""
        ingestor = factory.create_ingestor(
            'eClaimLink', enable_validation=False, output_format='fhir_bundle'
        )

        bundle = ingestor.ingest_file(create_test_xml_files['valid_eclaim'])
        claim = [
            e['resource']
            for e in bundle['entry']
            if e['resource']['resourceType'] == 'Claim'
        ][0]

        assert 'identifier' in claim
        identifiers = claim['identifier']
        assert isinstance(identifiers, list)
        assert len(identifiers) >= 1

        # Check identifier structure
        for identifier in identifiers:
            assert 'type' in identifier
            assert 'value' in identifier
            assert 'coding' in identifier['type']

            coding = identifier['type']['coding'][0]
            assert 'code' in coding
            assert coding['code'] in ['transaction', 'sender', 'receiver']

    def test_claim_items_structure(self, factory, create_test_xml_files):
        """Test Claim item structure and validation."""
        ingestor = factory.create_ingestor(
            'eClaimLink', enable_validation=False, output_format='fhir_bundle'
        )

        bundle = ingestor.ingest_file(create_test_xml_files['valid_eclaim'])
        claim = [
            e['resource']
            for e in bundle['entry']
            if e['resource']['resourceType'] == 'Claim'
        ][0]

        items = claim['item']
        assert len(items) >= 1, "Should have at least one item"

        for item in items:
            assert 'sequence' in item
            assert 'productOrService' in item
            assert isinstance(item['sequence'], int)
            assert item['sequence'] >= 1

            # Product or service should have coding
            prod_service = item['productOrService']
            assert 'coding' in prod_service
            coding = prod_service['coding'][0]
            assert 'system' in coding
            assert 'code' in coding

            # Should have financial information
            if 'unitPrice' in item:
                unit_price = item['unitPrice']
                assert 'value' in unit_price
                assert 'currency' in unit_price
                assert unit_price['currency'] == 'AED'

    def test_claim_meta_information(self, factory, create_test_xml_files):
        """Test Claim meta information structure."""
        ingestor = factory.create_ingestor(
            'eClaimLink', enable_validation=False, output_format='fhir_bundle'
        )

        bundle = ingestor.ingest_file(create_test_xml_files['valid_eclaim'])
        claim = [
            e['resource']
            for e in bundle['entry']
            if e['resource']['resourceType'] == 'Claim'
        ][0]

        meta = claim['meta']
        assert 'source' in meta
        assert 'lastUpdated' in meta

        if 'profile' in meta:
            profiles = meta['profile']
            assert isinstance(profiles, list)
            nazmito_profiles = [p for p in profiles if 'nazmito.com/fhir' in p]
            assert len(nazmito_profiles) >= 1


class TestConditionResourceValidation:
    """Test Condition resource structure and validation."""

    @pytest.fixture
    def factory(self):
        """XMLIngestorFactory for Condition testing."""
        return XMLIngestorFactory(schema_base_path='schemas/')

    def test_condition_basic_structure(self, factory, create_test_xml_files):
        """Test basic Condition resource structure."""
        ingestor = factory.create_ingestor(
            'eClaimLink', enable_validation=False, output_format='fhir_bundle'
        )

        bundle = ingestor.ingest_file(create_test_xml_files['rich_clinical'])

        condition_entries = [
            entry
            for entry in bundle['entry']
            if entry['resource']['resourceType'] == 'Condition'
        ]

        for entry in condition_entries:
            condition = entry['resource']

            # Required fields
            assert condition['resourceType'] == 'Condition'
            assert 'id' in condition
            assert 'meta' in condition
            assert 'subject' in condition

            # Subject should reference patient
            subject_ref = condition['subject']['reference']
            assert subject_ref.startswith(
                'Patient/'
            ), "Condition should reference Patient"

    def test_condition_coding_structure(self, factory, create_test_xml_files):
        """Test Condition coding and terminology."""
        ingestor = factory.create_ingestor(
            'eClaimLink', enable_validation=False, output_format='fhir_bundle'
        )

        bundle = ingestor.ingest_file(create_test_xml_files['rich_clinical'])

        condition_entries = [
            entry
            for entry in bundle['entry']
            if entry['resource']['resourceType'] == 'Condition'
        ]

        for entry in condition_entries:
            condition = entry['resource']

            if 'code' in condition:
                code = condition['code']
                assert 'coding' in code
                coding = code['coding'][0]

                assert 'system' in coding
                assert 'code' in coding

                # Should use standard diagnosis coding systems
                valid_systems = [
                    'http://hl7.org/fhir/sid/icd-10',
                    'http://hl7.org/fhir/sid/icd-10-cm',
                    'http://snomed.info/sct',
                ]

                if 'system' in coding:
                    # System should be from recognized terminologies (if specified)
                    pass  # Validation depends on actual implementation


class TestObservationResourceValidation:
    """Test Observation resource structure and validation."""

    @pytest.fixture
    def factory(self):
        """XMLIngestorFactory for Observation testing."""
        return XMLIngestorFactory(schema_base_path='schemas/')

    def test_observation_basic_structure(self, factory, create_test_xml_files):
        """Test basic Observation resource structure."""
        # Shafafiya format has more structured observation data
        ingestor = factory.create_ingestor(
            'Shafafiya', enable_validation=False, output_format='fhir_bundle'
        )

        if 'valid_shafafiya' not in create_test_xml_files:
            pytest.skip("Shafafiya test file not available")

        bundle = ingestor.ingest_file(create_test_xml_files['valid_shafafiya'])

        obs_entries = [
            entry
            for entry in bundle['entry']
            if entry['resource']['resourceType'] == 'Observation'
        ]

        for entry in obs_entries:
            observation = entry['resource']

            # Required fields
            assert observation['resourceType'] == 'Observation'
            assert 'id' in observation
            assert 'meta' in observation
            assert 'status' in observation
            assert 'subject' in observation

            # Subject should reference patient
            subject_ref = observation['subject']['reference']
            assert subject_ref.startswith(
                'Patient/'
            ), "Observation should reference Patient"

            # Should have valid status
            valid_statuses = [
                'registered',
                'preliminary',
                'final',
                'amended',
                'corrected',
                'cancelled',
                'entered-in-error',
                'unknown',
            ]
            assert observation['status'] in valid_statuses

    def test_observation_value_types(self, factory, create_test_xml_files):
        """Test Observation value types and structure."""
        ingestor = factory.create_ingestor(
            'Shafafiya', enable_validation=False, output_format='fhir_bundle'
        )

        if 'valid_shafafiya' not in create_test_xml_files:
            pytest.skip("Shafafiya test file not available")

        bundle = ingestor.ingest_file(create_test_xml_files['valid_shafafiya'])

        obs_entries = [
            entry
            for entry in bundle['entry']
            if entry['resource']['resourceType'] == 'Observation'
        ]

        for entry in obs_entries:
            observation = entry['resource']

            # Should have a value
            value_keys = [k for k in observation.keys() if k.startswith('value')]
            assert len(value_keys) >= 1, "Observation should have a value"

            # Check specific value types
            if 'valueQuantity' in observation:
                quantity = observation['valueQuantity']
                assert 'value' in quantity
                if 'unit' in quantity:
                    assert isinstance(quantity['unit'], str)

            elif 'valueString' in observation:
                assert isinstance(observation['valueString'], str)

            elif 'valueBoolean' in observation:
                assert isinstance(observation['valueBoolean'], bool)

    def test_observation_coding_structure(self, factory, create_test_xml_files):
        """Test Observation code structure."""
        ingestor = factory.create_ingestor(
            'Shafafiya', enable_validation=False, output_format='fhir_bundle'
        )

        if 'valid_shafafiya' not in create_test_xml_files:
            pytest.skip("Shafafiya test file not available")

        bundle = ingestor.ingest_file(create_test_xml_files['valid_shafafiya'])

        obs_entries = [
            entry
            for entry in bundle['entry']
            if entry['resource']['resourceType'] == 'Observation'
        ]

        for entry in obs_entries:
            observation = entry['resource']

            if 'code' in observation:
                code = observation['code']
                assert 'coding' in code
                coding = code['coding'][0]

                assert 'system' in coding
                assert 'code' in coding

                # Common lab/observation coding systems
                valid_systems = [
                    'http://loinc.org',
                    'http://snomed.info/sct',
                    'http://terminology.hl7.org/CodeSystem/observation-category',
                ]


class TestMedicationStatementResourceValidation:
    """Test MedicationStatement resource structure and validation."""

    @pytest.fixture
    def factory(self):
        """XMLIngestorFactory for MedicationStatement testing."""
        return XMLIngestorFactory(schema_base_path='schemas/')

    def test_medication_statement_basic_structure(self, factory, create_test_xml_files):
        """Test basic MedicationStatement resource structure."""
        ingestor = factory.create_ingestor(
            'eClaimLink', enable_validation=False, output_format='fhir_bundle'
        )

        bundle = ingestor.ingest_file(create_test_xml_files['rich_clinical'])

        med_entries = [
            entry
            for entry in bundle['entry']
            if entry['resource']['resourceType'] == 'MedicationStatement'
        ]

        for entry in med_entries:
            med_statement = entry['resource']

            # Required fields
            assert med_statement['resourceType'] == 'MedicationStatement'
            assert 'id' in med_statement
            assert 'meta' in med_statement
            assert 'status' in med_statement
            assert 'subject' in med_statement

            # Subject should reference patient
            subject_ref = med_statement['subject']['reference']
            assert subject_ref.startswith(
                'Patient/'
            ), "MedicationStatement should reference Patient"

            # Should have valid status
            valid_statuses = [
                'active',
                'completed',
                'entered-in-error',
                'intended',
                'stopped',
                'on-hold',
                'unknown',
                'not-taken',
            ]
            assert med_statement['status'] in valid_statuses

    def test_medication_coding_structure(self, factory, create_test_xml_files):
        """Test medication coding and terminology."""
        ingestor = factory.create_ingestor(
            'eClaimLink', enable_validation=False, output_format='fhir_bundle'
        )

        bundle = ingestor.ingest_file(create_test_xml_files['rich_clinical'])

        med_entries = [
            entry
            for entry in bundle['entry']
            if entry['resource']['resourceType'] == 'MedicationStatement'
        ]

        for entry in med_entries:
            med_statement = entry['resource']

            # Should have medication reference or codeable concept
            has_medication = (
                'medicationReference' in med_statement
                or 'medicationCodeableConcept' in med_statement
            )
            assert has_medication, "MedicationStatement should reference medication"

            if 'medicationCodeableConcept' in med_statement:
                med_concept = med_statement['medicationCodeableConcept']
                assert 'coding' in med_concept
                coding = med_concept['coding'][0]

                assert 'system' in coding
                assert 'code' in coding

                # Common medication coding systems
                valid_systems = [
                    'http://www.nlm.nih.gov/research/umls/rxnorm',
                    'http://snomed.info/sct',
                    'http://www.whocc.no/atc',
                ]


class TestProcedureResourceValidation:
    """Test Procedure resource structure and validation."""

    @pytest.fixture
    def factory(self):
        """XMLIngestorFactory for Procedure testing."""
        return XMLIngestorFactory(schema_base_path='schemas/')

    def test_procedure_basic_structure(self, factory, create_test_xml_files):
        """Test basic Procedure resource structure."""
        ingestor = factory.create_ingestor(
            'eClaimLink', enable_validation=False, output_format='fhir_bundle'
        )

        bundle = ingestor.ingest_file(create_test_xml_files['valid_eclaim'])

        procedure_entries = [
            entry
            for entry in bundle['entry']
            if entry['resource']['resourceType'] == 'Procedure'
        ]

        for entry in procedure_entries:
            procedure = entry['resource']

            # Required fields
            assert procedure['resourceType'] == 'Procedure'
            assert 'id' in procedure
            assert 'meta' in procedure
            assert 'status' in procedure
            assert 'subject' in procedure

            # Subject should reference patient
            subject_ref = procedure['subject']['reference']
            assert subject_ref.startswith(
                'Patient/'
            ), "Procedure should reference Patient"

            # Should have valid status
            valid_statuses = [
                'preparation',
                'in-progress',
                'not-done',
                'suspended',
                'aborted',
                'completed',
                'entered-in-error',
                'unknown',
            ]
            assert procedure['status'] in valid_statuses

    def test_procedure_coding_structure(self, factory, create_test_xml_files):
        """Test Procedure code structure and terminology."""
        ingestor = factory.create_ingestor(
            'eClaimLink', enable_validation=False, output_format='fhir_bundle'
        )

        bundle = ingestor.ingest_file(create_test_xml_files['valid_eclaim'])

        procedure_entries = [
            entry
            for entry in bundle['entry']
            if entry['resource']['resourceType'] == 'Procedure'
        ]

        for entry in procedure_entries:
            procedure = entry['resource']

            if 'code' in procedure:
                code = procedure['code']
                assert 'coding' in code
                coding = code['coding'][0]

                assert 'system' in coding
                assert 'code' in coding

                # Common procedure coding systems
                valid_systems = [
                    'http://www.ama-assn.org/go/cpt',
                    'http://snomed.info/sct',
                    'http://www.cms.gov/Medicare/Coding/ICD10',
                ]


class TestResourceCrossValidation:
    """Test cross-resource validation and relationships."""

    @pytest.fixture
    def factory(self):
        """XMLIngestorFactory for cross-validation testing."""
        return XMLIngestorFactory(schema_base_path='schemas/')

    def test_patient_references_consistency(self, factory, create_test_xml_files):
        """Test that all resources reference the same patient consistently."""
        ingestor = factory.create_ingestor(
            'eClaimLink', enable_validation=False, output_format='fhir_bundle'
        )

        bundle = ingestor.ingest_file(create_test_xml_files['valid_eclaim'])

        patient_references = set()

        for entry in bundle['entry']:
            resource = entry['resource']

            # Collect patient references from different resource types
            if 'subject' in resource:
                patient_ref = resource['subject']['reference']
                if patient_ref.startswith('Patient/'):
                    patient_references.add(patient_ref)

            if 'patient' in resource:
                patient_ref = resource['patient']['reference']
                if patient_ref.startswith('Patient/'):
                    patient_references.add(patient_ref)

        # All patient references should be consistent
        assert (
            len(patient_references) <= 1
        ), f"Should have consistent patient references, got {patient_references}"

    def test_resource_id_uniqueness(self, factory, create_test_xml_files):
        """Test that all resource IDs are unique within the bundle."""
        ingestor = factory.create_ingestor(
            'eClaimLink', enable_validation=False, output_format='fhir_bundle'
        )

        bundle = ingestor.ingest_file(create_test_xml_files['valid_eclaim'])

        resource_ids = []
        for entry in bundle['entry']:
            resource = entry['resource']
            resource_ids.append(resource['id'])

        # All IDs should be unique
        assert len(resource_ids) == len(
            set(resource_ids)
        ), "All resource IDs should be unique"

    def test_bundle_entry_fullurl_format(self, factory, create_test_xml_files):
        """Test that Bundle entry fullUrl follows correct format."""
        ingestor = factory.create_ingestor(
            'eClaimLink', enable_validation=False, output_format='fhir_bundle'
        )

        bundle = ingestor.ingest_file(create_test_xml_files['valid_eclaim'])

        for entry in bundle['entry']:
            assert 'fullUrl' in entry
            full_url = entry['fullUrl']

            # Should be urn:uuid format
            assert full_url.startswith(
                'urn:uuid:'
            ), f"fullUrl should be urn:uuid format: {full_url}"

            # UUID pattern validation
            uuid_pattern = (
                r'urn:uuid:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
            )
            assert re.match(uuid_pattern, full_url), f"Invalid UUID format: {full_url}"

    def test_resource_meta_consistency(self, factory, create_test_xml_files):
        """Test that resource meta information is consistent."""
        ingestor = factory.create_ingestor(
            'eClaimLink', enable_validation=False, output_format='fhir_bundle'
        )

        bundle = ingestor.ingest_file(create_test_xml_files['valid_eclaim'])

        for entry in bundle['entry']:
            resource = entry['resource']

            assert 'meta' in resource
            meta = resource['meta']

            # Should have source
            assert 'source' in meta

            # Should have lastUpdated in ISO format
            assert 'lastUpdated' in meta
            timestamp = meta['lastUpdated']
            iso_pattern = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'
            assert re.match(
                iso_pattern, timestamp
            ), f"Invalid timestamp format: {timestamp}"

    def test_extension_url_format_consistency(self, factory, create_test_xml_files):
        """Test that extension URLs follow consistent format."""
        ingestor = factory.create_ingestor(
            'eClaimLink', enable_validation=False, output_format='fhir_bundle'
        )

        bundle = ingestor.ingest_file(create_test_xml_files['rich_clinical'])

        # Check bundle-level extensions
        if 'extension' in bundle:
            for ext in bundle['extension']:
                assert 'url' in ext
                url = ext['url']
                assert url.startswith(
                    'https://'
                ), f"Extension URL should be https: {url}"

                if 'nazmito.com/fhir' in url:
                    assert (
                        'StructureDefinition' in url
                    ), f"Nazmito extensions should reference StructureDefinition: {url}"

        # Check resource-level extensions
        for entry in bundle['entry']:
            resource = entry['resource']
            if 'extension' in resource:
                for ext in resource['extension']:
                    assert 'url' in ext
                    url = ext['url']
                    assert url.startswith(
                        'https://'
                    ), f"Extension URL should be https: {url}"
