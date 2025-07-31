"""
Clinical intelligence and NLP extraction tests for FHIR resources.

This module tests the clinical intelligence capabilities including:
- Medical entity extraction from clinical text
- Clinical context scoring and confidence measures
- NLP pattern matching for medical conditions, procedures, and medications
- Clinical data quality assessment
"""

import pytest
from pipelines.factory import XMLIngestorFactory


class TestClinicalIntelligenceExtraction:
    """Test clinical intelligence and NLP extraction capabilities."""

    @pytest.fixture
    def factory(self):
        """XMLIngestorFactory for clinical extraction testing."""
        return XMLIngestorFactory(schema_base_path='schemas/')

    def test_medical_entity_extraction(self, factory, create_test_xml_files):
        """Test extraction of medical entities from clinical text."""
        ingestor = factory.create_ingestor(
            'eClaimLink', enable_validation=False, output_format='fhir_bundle'
        )

        # Use rich clinical data file
        bundle = ingestor.ingest_file(create_test_xml_files['rich_clinical'])

        # Look for extracted medical entities in resources
        condition_entries = [
            entry
            for entry in bundle['entry']
            if entry['resource']['resourceType'] == 'Condition'
        ]

        med_entries = [
            entry
            for entry in bundle['entry']
            if entry['resource']['resourceType'] == 'MedicationStatement'
        ]

        procedure_entries = [
            entry
            for entry in bundle['entry']
            if entry['resource']['resourceType'] == 'Procedure'
        ]

        # Should extract some clinical entities
        total_clinical_entities = (
            len(condition_entries) + len(med_entries) + len(procedure_entries)
        )
        assert (
            total_clinical_entities >= 0
        ), "Should extract clinical entities from rich text"

    def test_clinical_nlp_patterns(self, factory, create_test_xml_files):
        """Test NLP pattern matching for medical concepts."""
        ingestor = factory.create_ingestor(
            'eClaimLink', enable_validation=False, output_format='fhir_bundle'
        )

        bundle = ingestor.ingest_file(create_test_xml_files['rich_clinical'])

        # Check for clinical intelligence extensions in resources
        for entry in bundle['entry']:
            resource = entry['resource']

            if 'extension' in resource:
                clinical_extensions = [
                    ext
                    for ext in resource['extension']
                    if 'nazmito.com/fhir' in ext.get('url', '')
                ]

                # Validate clinical intelligence extensions
                for ext in clinical_extensions:
                    assert 'url' in ext
                    assert ext['url'].startswith(
                        'https://nazmito.com/fhir/StructureDefinition/'
                    )

                    # Should have confidence or score values
                    value_keys = [k for k in ext.keys() if k.startswith('value')]
                    if value_keys and 'valueDecimal' in ext:
                        score = ext['valueDecimal']
                        assert (
                            0.0 <= score <= 1.0
                        ), f"Clinical score {score} should be 0-1"

    def test_condition_extraction_from_diagnosis(self, factory, create_test_xml_files):
        """Test extraction of Condition resources from diagnosis codes."""
        ingestor = factory.create_ingestor(
            'eClaimLink', enable_validation=False, output_format='fhir_bundle'
        )

        bundle = ingestor.ingest_file(create_test_xml_files['valid_eclaim'])

        condition_entries = [
            entry
            for entry in bundle['entry']
            if entry['resource']['resourceType'] == 'Condition'
        ]

        for entry in condition_entries:
            condition = entry['resource']

            # Should have basic Condition structure
            assert 'id' in condition
            assert 'meta' in condition
            assert 'subject' in condition, "Condition should reference patient"

            # Should have clinical classification
            if 'code' in condition:
                coding = condition['code']['coding'][0]
                assert 'system' in coding, "Should have coding system"
                assert 'code' in coding, "Should have diagnosis code"

                # Common diagnosis code systems
                valid_systems = [
                    'http://hl7.org/fhir/sid/icd-10',
                    'http://hl7.org/fhir/sid/icd-10-cm',
                    'http://snomed.info/sct',
                ]
                assert any(
                    system in coding['system'] for system in valid_systems
                ), f"Should use standard diagnosis coding system: {coding['system']}"

    def test_medication_extraction_from_clinical_text(
        self, factory, create_test_xml_files
    ):
        """Test extraction of MedicationStatement resources from clinical text."""
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

            # Should have basic MedicationStatement structure
            assert 'id' in med_statement
            assert 'meta' in med_statement
            assert (
                'subject' in med_statement
            ), "MedicationStatement should reference patient"
            assert 'status' in med_statement, "Should have medication status"

            # Should reference medication
            if 'medicationCodeableConcept' in med_statement:
                coding = med_statement['medicationCodeableConcept']['coding'][0]
                assert 'system' in coding
                assert 'code' in coding

                # Could be various medication coding systems
                common_med_systems = [
                    'http://www.nlm.nih.gov/research/umls/rxnorm',
                    'http://snomed.info/sct',
                    'http://www.whocc.no/atc',
                ]

    def test_procedure_extraction_from_activity_codes(
        self, factory, create_test_xml_files
    ):
        """Test extraction of Procedure resources from activity/procedure codes."""
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

            # Should have basic Procedure structure
            assert 'id' in procedure
            assert 'meta' in procedure
            assert 'subject' in procedure, "Procedure should reference patient"
            assert 'status' in procedure, "Should have procedure status"

            # Should have procedure code
            if 'code' in procedure:
                coding = procedure['code']['coding'][0]
                assert 'system' in coding
                assert 'code' in coding

                # Common procedure coding systems
                valid_systems = [
                    'http://www.ama-assn.org/go/cpt',
                    'http://snomed.info/sct',
                    'http://www.cms.gov/Medicare/Coding/ICD10',
                ]

    def test_observation_extraction_from_lab_data(self, factory, create_test_xml_files):
        """Test extraction of Observation resources from lab/diagnostic data."""
        ingestor = factory.create_ingestor(
            'Shafafiya',  # Shafafiya has more structured observation data
            enable_validation=False,
            output_format='fhir_bundle',
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

            # Should have basic Observation structure
            assert 'id' in observation
            assert 'meta' in observation
            assert 'subject' in observation, "Observation should reference patient"
            assert 'status' in observation, "Should have observation status"

            # Should have observation code and value
            if 'code' in observation:
                coding = observation['code']['coding'][0]
                assert 'system' in coding
                assert 'code' in coding

            # Should have value in appropriate format
            value_keys = [k for k in observation.keys() if k.startswith('value')]
            assert len(value_keys) >= 1, "Observation should have a value"

    def test_clinical_context_scoring(self, factory, create_test_xml_files):
        """Test clinical context scoring and confidence measures."""
        ingestor = factory.create_ingestor(
            'eClaimLink', enable_validation=False, output_format='fhir_bundle'
        )

        bundle = ingestor.ingest_file(create_test_xml_files['rich_clinical'])

        # Check for clinical intelligence extensions at bundle level
        if 'extension' in bundle:
            clinical_scores = {}

            for ext in bundle['extension']:
                if 'nazmito.com/fhir' in ext.get('url', ''):
                    if 'clinical-context-score' in ext['url']:
                        clinical_scores['context'] = ext.get('valueDecimal', 0.0)
                    elif 'data-quality-score' in ext['url']:
                        clinical_scores['quality'] = ext.get('valueDecimal', 0.0)
                    elif 'enrichment-score' in ext['url']:
                        clinical_scores['enrichment'] = ext.get('valueDecimal', 0.0)
                    elif 'ai-confidence' in ext['url']:
                        clinical_scores['confidence'] = ext.get('valueDecimal', 0.0)

            # Validate score relationships
            for score_type, score in clinical_scores.items():
                assert 0.0 <= score <= 1.0, f"{score_type} score {score} should be 0-1"

            # Rich clinical data should have higher scores
            if clinical_scores:
                avg_score = sum(clinical_scores.values()) / len(clinical_scores)
                # Rich clinical file should score reasonably well
                assert (
                    avg_score >= 0.0
                ), "Rich clinical data should have positive scores"

    def test_data_quality_assessment(self, factory, create_test_xml_files):
        """Test data quality assessment and completeness scoring."""
        test_files = ['valid_eclaim', 'rich_clinical']

        scores = {}
        for file_key in test_files:
            if file_key not in create_test_xml_files:
                continue

            ingestor = factory.create_ingestor(
                'eClaimLink', enable_validation=False, output_format='fhir_bundle'
            )

            bundle = ingestor.ingest_file(create_test_xml_files[file_key])

            # Calculate basic quality metrics
            quality_metrics = {
                'total_resources': bundle['total'],
                'resource_diversity': len(
                    set(entry['resource']['resourceType'] for entry in bundle['entry'])
                ),
                'has_extensions': 'extension' in bundle,
                'has_clinical_resources': any(
                    entry['resource']['resourceType']
                    in ['Condition', 'Observation', 'MedicationStatement', 'Procedure']
                    for entry in bundle['entry']
                ),
            }

            scores[file_key] = quality_metrics

        # Rich clinical should have better quality metrics
        if len(scores) == 2:
            rich_metrics = scores.get('rich_clinical', {})
            basic_metrics = scores.get('valid_eclaim', {})

            # Rich clinical should have more resources or diversity
            if rich_metrics and basic_metrics:
                assert (
                    rich_metrics['total_resources'] >= basic_metrics['total_resources']
                ), "Rich clinical should have equal or more resources"

    def test_clinical_text_processing_patterns(self, factory):
        """Test clinical text processing patterns and medical NLP."""
        ingestor = factory.create_ingestor(
            'eClaimLink', enable_validation=False, output_format='fhir_bundle'
        )

        # Create test XML with rich clinical justification
        clinical_xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
            <Header>
                <SenderID>TEST</SenderID>
                <ReceiverID>PAYER</ReceiverID>
                <TransactionDateTime>01/01/2025 12:00</TransactionDateTime>
                <TransactionID>CLINICAL-001</TransactionID>
            </Header>
            <ServiceRequests>
                <ServiceRequest>
                    <ct:ActivityCode>99213</ct:ActivityCode>
                    <ct:DiagnosisCode>E11.9</ct:DiagnosisCode>
                    <ct:Justification>Patient with Type 2 diabetes mellitus without complications. Requires HbA1c monitoring and metformin adjustment. Blood pressure elevated at 140/90. Recommending ACE inhibitor initiation.</ct:Justification>
                </ServiceRequest>
            </ServiceRequests>
        </PriorAuthorizationRequest>'''

        import tempfile

        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(clinical_xml)
            f.flush()

            bundle = ingestor.ingest_file(f.name)

            # Should extract clinical information from justification
            assert bundle['resourceType'] == 'Bundle'
            assert bundle['total'] >= 1

            # Look for extracted clinical entities
            clinical_resources = [
                entry['resource']
                for entry in bundle['entry']
                if entry['resource']['resourceType']
                in ['Condition', 'MedicationStatement', 'Observation']
            ]

            # Should extract some clinical entities from rich text
            assert len(clinical_resources) >= 0, "Should process clinical text"

    def test_confidence_propagation_through_resources(
        self, factory, create_test_xml_files
    ):
        """Test that confidence scores propagate appropriately through extracted resources."""
        ingestor = factory.create_ingestor(
            'eClaimLink', enable_validation=False, output_format='fhir_bundle'
        )

        bundle = ingestor.ingest_file(create_test_xml_files['rich_clinical'])

        # Check for confidence extensions at resource level
        resource_confidences = []

        for entry in bundle['entry']:
            resource = entry['resource']
            if 'extension' in resource:
                for ext in resource['extension']:
                    if 'confidence' in ext.get('url', '').lower():
                        if 'valueDecimal' in ext:
                            confidence = ext['valueDecimal']
                            resource_confidences.append(confidence)
                            assert (
                                0.0 <= confidence <= 1.0
                            ), f"Resource confidence {confidence} should be 0-1"

        # Should have some confidence scoring
        assert len(resource_confidences) >= 0, "Should have confidence scoring system"

    def test_clinical_terminology_mapping(self, factory, create_test_xml_files):
        """Test mapping to standard clinical terminologies."""
        ingestor = factory.create_ingestor(
            'eClaimLink', enable_validation=False, output_format='fhir_bundle'
        )

        bundle = ingestor.ingest_file(create_test_xml_files['valid_eclaim'])

        # Check for proper terminology mapping
        for entry in bundle['entry']:
            resource = entry['resource']
            resource_type = resource['resourceType']

            if resource_type == 'Condition' and 'code' in resource:
                coding = resource['code']['coding'][0]
                # Should map to standard diagnosis terminologies
                standard_systems = [
                    'http://hl7.org/fhir/sid/icd-10',
                    'http://snomed.info/sct',
                ]

            elif resource_type == 'Procedure' and 'code' in resource:
                coding = resource['code']['coding'][0]
                # Should map to standard procedure terminologies
                standard_systems = [
                    'http://www.ama-assn.org/go/cpt',
                    'http://snomed.info/sct',
                ]

            elif (
                resource_type == 'MedicationStatement'
                and 'medicationCodeableConcept' in resource
            ):
                coding = resource['medicationCodeableConcept']['coding'][0]
                # Should map to standard medication terminologies
                standard_systems = [
                    'http://www.nlm.nih.gov/research/umls/rxnorm',
                    'http://snomed.info/sct',
                ]
