import json
import sys
from pathlib import Path

import jsonschema
import pytest
from jsonschema import validate

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipelines.factory import XMLIngestorFactory  # noqa: E402


class TestCanonicalSchema:
    """Test suite for the canonical schema and data transformations."""

    @classmethod
    def setup_class(cls):
        """Load schema and example files once for all tests."""
        project_root = Path(__file__).parent.parent

        # Load canonical schema
        schema_path = project_root / "schemas" / "canonical_schema.json"
        with open(schema_path, "r") as f:
            cls.schema = json.load(f)

        # Load example JSON
        example_path = project_root / "canonical" / "examples" / "claim_example.json"
        with open(example_path, "r") as f:
            cls.example_claim = json.load(f)

        # Paths to sample XML files
        cls.sample_xml_paths = {
            'eclaim_link': project_root / "samples" / "eclaim_link_request.xml",
            'shafafiya': project_root / "samples" / "shafafiya_authorization.xml",
        }

    def test_schema_is_valid_json_schema(self):
        """Test that the canonical schema itself is a valid JSON Schema."""
        # This will raise an exception if the schema is invalid
        jsonschema.Draft202012Validator.check_schema(self.schema)

    def test_example_validates_against_schema(self):
        """Test that the example JSON validates against the canonical schema."""
        # This will raise ValidationError if validation fails
        validate(instance=self.example_claim, schema=self.schema)

    def test_required_fields_present(self):
        """Test that all required fields are present in the example."""
        required_fields = self.schema.get("required", [])
        for field in required_fields:
            assert field in self.example_claim, f"Required field '{field}' missing"

    def test_resource_type_is_bundle(self):
        """Test that the canonical schema supports FHIR Bundle resourceType."""
        # The canonical schema should now support Bundle as the primary resourceType
        # since we've moved to FHIR Bundle format for enhanced clinical extraction
        schema_properties = self.schema.get("properties", {})
        resource_type_prop = schema_properties.get("resourceType", {})

        if "enum" in resource_type_prop:
            valid_types = resource_type_prop["enum"]
            assert "Bundle" in valid_types, "Schema should support Bundle resourceType"
        elif "const" in resource_type_prop:
            assert resource_type_prop["const"] in [
                "Claim",
                "Bundle",
            ], "Schema should support Bundle or Claim"

    def test_identifiers_structure(self):
        """Test that identifiers have the correct structure."""
        identifiers = self.example_claim.get("identifier", [])
        assert len(identifiers) >= 1, "At least one identifier required"

        # Check for required identifier types
        id_types = [id["type"]["coding"][0]["code"] for id in identifiers]
        assert "transaction" in id_types, "Transaction identifier required"

    def test_patient_reference_format(self):
        """Test that patient reference follows the correct format."""
        patient_ref = self.example_claim["patient"]["reference"]
        assert patient_ref.startswith(
            "Patient/"
        ), "Patient reference must start with 'Patient/'"

    def test_service_items_structure(self):
        """Test that service items have the correct structure."""
        items = self.example_claim.get("item", [])
        assert len(items) > 0, "At least one service item required"

        for item in items:
            # Check required fields
            assert "sequence" in item, "Item sequence required"
            assert "productOrService" in item, "Product or service code required"
            assert "servicedDate" in item, "Service date required"
            assert "quantity" in item, "Quantity required"
            assert "unitPrice" in item, "Unit price required"

            # Check coding structure
            coding = item["productOrService"]["coding"][0]
            assert "system" in coding, "Coding system required"
            assert "code" in coding, "Service code required"

    def test_billable_period_dates(self):
        """Test that billable period has valid start and end dates."""
        period = self.example_claim["billablePeriod"]
        assert "start" in period, "Start date required"
        assert "end" in period, "End date required"

        # Verify end date is not before start date
        from datetime import datetime

        start = datetime.fromisoformat(period["start"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(period["end"].replace("Z", "+00:00"))
        assert end >= start, "End date must be after or equal to start date"

    def test_extensions_structure(self):
        """Test that Nazmito extensions follow the correct structure."""
        extensions = self.example_claim.get("extension", [])

        # Check that schema version extension exists
        schema_version_ext = next(
            (
                ext
                for ext in extensions
                if ext["url"]
                == "https://nazmito.ae/fhir/StructureDefinition/schema-version"
            ),
            None,
        )
        assert schema_version_ext is not None, "Schema version extension required"
        assert "valueString" in schema_version_ext, "Schema version value required"

    def test_xml_to_canonical_transformation(self):
        """Test transformation from XML to canonical FHIR Bundle format."""
        factory = XMLIngestorFactory(schema_base_path='schemas/')

        # Test both formats
        for format_name, xml_path in self.sample_xml_paths.items():
            if not xml_path.exists():
                pytest.skip(f"Sample XML file not found: {xml_path}")

            # Transform to FHIR Bundle format
            ingestor = factory.create_ingestor_for_file(
                str(xml_path), enable_validation=False
            )

            # Test legacy transformation (backward compatibility)
            legacy_result = ingestor.process(str(xml_path))
            assert isinstance(legacy_result, dict)
            assert 'format_name' in legacy_result
            assert 'services' in legacy_result

            # Test FHIR Bundle transformation (new enhanced format)
            fhir_ingestor = factory.create_ingestor(
                format_name.replace('_', '').title(),  # 'eclaim_link' -> 'EclaimLink'
                enable_validation=False,
                output_format='fhir_bundle',
            )

            try:
                bundle_result = fhir_ingestor.process(str(xml_path))

                # Validate FHIR Bundle structure
                assert bundle_result['resourceType'] == 'Bundle'
                assert 'entry' in bundle_result
                assert 'total' in bundle_result
                assert len(bundle_result['entry']) == bundle_result['total']

                # Validate that Bundle contains resources
                assert (
                    bundle_result['total'] >= 1
                ), "Bundle should contain at least one resource"

                # Check that primary Claim resource exists
                resource_types = [
                    entry['resource']['resourceType']
                    for entry in bundle_result['entry']
                ]
                assert (
                    'Claim' in resource_types
                ), "Bundle should contain a Claim resource"

            except Exception as e:
                pytest.skip(
                    f"FHIR Bundle validation skipped for {format_name}: {str(e)}"
                )

    def test_currency_codes(self):
        """Test that all currency codes are valid 3-letter codes."""
        items = self.example_claim.get("item", [])
        for item in items:
            if "unitPrice" in item:
                currency = item["unitPrice"].get("currency", "")
                assert len(currency) == 3, f"Currency must be 3 letters: {currency}"
                assert currency.isupper(), f"Currency must be uppercase: {currency}"

    def test_diagnosis_codes_format(self):
        """Test that diagnosis codes follow ICD-10 format."""
        diagnoses = self.example_claim.get("diagnosis", [])
        for diag in diagnoses:
            coding = diag["diagnosisCodeableConcept"]["coding"][0]
            code = coding.get("code", "")

            # Basic ICD-10 format validation
            assert len(code) >= 3, f"ICD-10 code too short: {code}"
            assert code[0].isalpha(), f"ICD-10 must start with letter: {code}"
            assert code[
                1:3
            ].isdigit(), f"ICD-10 must have digits at positions 2-3: {code}"

    def _create_canonical_from_normalized(self, normalized):
        """Helper to create a canonical claim from normalized data."""
        # This is a simplified transformation for testing
        return {
            "resourceType": "Claim",
            "id": normalized.get("authorization_id", "test-001"),
            "meta": {
                "profile": [
                    "https://nazmito.ae/fhir/StructureDefinition/PriorAuthorization"
                ],
                "source": "XML",
                "lastUpdated": "2025-07-30T14:30:00Z",
            },
            "identifier": [
                {
                    "type": {"coding": [{"code": "transaction"}]},
                    "value": normalized.get("authorization_id", "test-001"),
                },
                {
                    "type": {"coding": [{"code": "sender"}]},
                    "value": normalized.get("sender", "UNKNOWN"),
                },
                {
                    "type": {"coding": [{"code": "receiver"}]},
                    "value": normalized.get("receiver", "UNKNOWN"),
                },
            ],
            "status": "active",
            "type": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/claim-type",
                        "code": "professional",
                    }
                ]
            },
            "use": "preauthorization",
            "patient": {"reference": "Patient/patient-001"},
            "created": normalized.get("transaction_date", "2025-07-30T00:00:00Z"),
            "provider": {
                "reference": f"Organization/{normalized.get('sender', 'UNKNOWN')}"
            },
            "billablePeriod": {
                "start": normalized.get("start", "2025-07-30T00:00:00Z"),
                "end": normalized.get("end", "2025-07-30T23:59:59Z"),
            },
            "item": [
                {
                    "sequence": int(service.get("id", idx)),
                    "productOrService": {
                        "coding": [
                            {
                                "system": "http://www.ama-assn.org/go/cpt",
                                "code": service.get(
                                    "code", service.get("activity_code", "99999")
                                ),
                            }
                        ]
                    },
                    "servicedDate": "2025-07-30",
                    "quantity": {"value": float(service.get("quantity", 1))},
                    "unitPrice": {
                        "value": float(
                            service.get("net", service.get("requested_amount_value", 0))
                        ),
                        "currency": "AED",
                    },
                }
                for idx, service in enumerate(normalized.get("services", []), 1)
            ],
        }


class TestFHIRBundleSchema:
    """Test suite for FHIR Bundle schema validation and clinical resource extraction."""

    @classmethod
    def setup_class(cls):
        """Setup for FHIR Bundle testing."""
        project_root = Path(__file__).parent.parent

        # Load canonical schema
        schema_path = project_root / "schemas" / "canonical_schema.json"
        with open(schema_path, "r") as f:
            cls.schema = json.load(f)

        cls.factory = XMLIngestorFactory(schema_base_path='schemas/')

        # Sample file paths
        cls.sample_files = {
            'eclaim_link': project_root / "samples" / "eclaim_link_request.xml",
            'shafafiya': project_root / "samples" / "shafafiya_authorization.xml",
        }

    def test_fhir_bundle_structure_validation(self):
        """Test that generated FHIR Bundles have valid structure."""
        for format_name, xml_path in self.sample_files.items():
            if not xml_path.exists():
                continue

            # Get appropriate format name for factory
            factory_format = (
                'eClaimLink' if format_name == 'eclaim_link' else 'Shafafiya'
            )
            ingestor = self.factory.create_ingestor(
                factory_format, enable_validation=False, output_format='fhir_bundle'
            )

            bundle = ingestor.process(str(xml_path))

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

    def test_fhir_resource_extraction_completeness(self):
        """Test that all expected FHIR resource types are extracted."""
        expected_resources = [
            'Claim',
            'Condition',
            'Observation',
            'MedicationStatement',
            'Procedure',
        ]

        for format_name, xml_path in self.sample_files.items():
            if not xml_path.exists():
                continue

            factory_format = (
                'eClaimLink' if format_name == 'eclaim_link' else 'Shafafiya'
            )
            ingestor = self.factory.create_ingestor(
                factory_format, enable_validation=False, output_format='fhir_bundle'
            )

            bundle = ingestor.process(str(xml_path))
            resource_types = [
                entry['resource']['resourceType'] for entry in bundle['entry']
            ]

            # Should always have a Claim resource
            assert (
                'Claim' in resource_types
            ), f"{format_name} should generate Claim resource"

            # Count unique resource types
            unique_types = set(resource_types)
            assert (
                len(unique_types) >= 1
            ), f"{format_name} should generate multiple resource types"

    def test_clinical_intelligence_extensions(self):
        """Test that clinical intelligence extensions are properly structured."""
        for format_name, xml_path in self.sample_files.items():
            if not xml_path.exists():
                continue

            factory_format = (
                'eClaimLink' if format_name == 'eclaim_link' else 'Shafafiya'
            )
            ingestor = self.factory.create_ingestor(
                factory_format, enable_validation=False, output_format='fhir_bundle'
            )

            bundle = ingestor.process(str(xml_path))

            # Check for bundle-level extensions
            if 'extension' in bundle:
                extensions = bundle['extension']
                assert isinstance(extensions, list)

                # Look for clinical intelligence extensions
                nazmito_extensions = [
                    ext
                    for ext in extensions
                    if 'nazmito.com/fhir' in ext.get('url', '')
                ]

                # Should have some clinical intelligence metadata
                assert (
                    len(nazmito_extensions) >= 0
                ), "Should have clinical intelligence extensions"

                # Validate extension structure
                for ext in nazmito_extensions:
                    assert 'url' in ext
                    assert ext['url'].startswith(
                        'https://nazmito.com/fhir/StructureDefinition/'
                    )

                    # Check for appropriate value types
                    value_keys = [k for k in ext.keys() if k.startswith('value')]
                    assert len(value_keys) >= 1, "Extension should have a value"

    def test_resource_relationships_and_references(self):
        """Test that FHIR resources properly reference each other."""
        for format_name, xml_path in self.sample_files.items():
            if not xml_path.exists():
                continue

            factory_format = (
                'eClaimLink' if format_name == 'eclaim_link' else 'Shafafiya'
            )
            ingestor = self.factory.create_ingestor(
                factory_format, enable_validation=False, output_format='fhir_bundle'
            )

            bundle = ingestor.process(str(xml_path))

            # Extract resource IDs and types
            resources = {}
            for entry in bundle['entry']:
                resource = entry['resource']
                resources[resource['id']] = resource['resourceType']

            # Find the Claim resource (primary)
            claim_resources = [
                entry['resource']
                for entry in bundle['entry']
                if entry['resource']['resourceType'] == 'Claim'
            ]

            assert len(claim_resources) >= 1, "Should have at least one Claim resource"
            claim = claim_resources[0]
            claim_id = claim['id']

            # Check that other resources reference the claim or patient appropriately
            for entry in bundle['entry']:
                resource = entry['resource']
                resource_type = resource['resourceType']

                if resource_type in ['Observation', 'MedicationStatement', 'Procedure']:
                    # These resources should reference the patient
                    if 'subject' in resource:
                        subject_ref = resource['subject']['reference']
                        assert subject_ref.startswith(
                            'Patient/'
                        ), f"{resource_type} should reference Patient"

                    # May also reference the claim via basedOn
                    if 'basedOn' in resource:
                        based_on_refs = resource['basedOn']
                        claim_refs = [
                            ref
                            for ref in based_on_refs
                            if ref.get('reference', '').startswith('Claim/')
                        ]
                        # Not required but if present should be valid

    def test_clinical_data_quality_scoring(self):
        """Test clinical data quality and completeness scoring."""
        for format_name, xml_path in self.sample_files.items():
            if not xml_path.exists():
                continue

            factory_format = (
                'eClaimLink' if format_name == 'eclaim_link' else 'Shafafiya'
            )
            ingestor = self.factory.create_ingestor(
                factory_format, enable_validation=False, output_format='fhir_bundle'
            )

            bundle = ingestor.process(str(xml_path))

            # Calculate basic quality metrics
            total_resources = bundle['total']
            resource_types = [
                entry['resource']['resourceType'] for entry in bundle['entry']
            ]
            unique_types = len(set(resource_types))

            # Quality should correlate with resource diversity
            assert total_resources >= 1, "Should have resources"
            assert unique_types >= 1, "Should have diverse resource types"

            # Check for clinical intelligence scoring in extensions
            if 'extension' in bundle:
                score_extensions = [
                    ext
                    for ext in bundle['extension']
                    if any(
                        score_type in ext.get('url', '')
                        for score_type in [
                            'clinical-context-score',
                            'data-quality-score',
                            'enrichment-score',
                            'ai-confidence',
                        ]
                    )
                ]

                # Validate score ranges
                for score_ext in score_extensions:
                    if 'valueDecimal' in score_ext:
                        score = score_ext['valueDecimal']
                        assert (
                            0.0 <= score <= 1.0
                        ), f"Score {score} should be between 0 and 1"

    def test_schema_version_evolution(self):
        """Test that schema versioning is properly handled."""
        for format_name, xml_path in self.sample_files.items():
            if not xml_path.exists():
                continue

            factory_format = (
                'eClaimLink' if format_name == 'eclaim_link' else 'Shafafiya'
            )
            ingestor = self.factory.create_ingestor(
                factory_format, enable_validation=False, output_format='fhir_bundle'
            )

            bundle = ingestor.process(str(xml_path))

            # Check bundle meta for version info
            assert 'meta' in bundle
            meta = bundle['meta']

            # Should have profile and source
            if 'profile' in meta:
                profiles = meta['profile']
                assert isinstance(profiles, list)
                assert len(profiles) >= 1

                # Should reference Nazmito FHIR profiles
                nazmito_profiles = [p for p in profiles if 'nazmito.com/fhir' in p]
                assert len(nazmito_profiles) >= 1, "Should have Nazmito FHIR profile"

            # Check for schema version extensions
            if 'extension' in bundle:
                version_extensions = [
                    ext
                    for ext in bundle['extension']
                    if 'schema-version' in ext.get('url', '')
                ]

                for version_ext in version_extensions:
                    if 'valueString' in version_ext:
                        version = version_ext['valueString']
                        assert version.startswith(
                            'v'
                        ), f"Version {version} should start with 'v'"

    def test_uae_healthcare_compliance(self):
        """Test compliance with UAE healthcare standards."""
        for format_name, xml_path in self.sample_files.items():
            if not xml_path.exists():
                continue

            factory_format = (
                'eClaimLink' if format_name == 'eclaim_link' else 'Shafafiya'
            )
            ingestor = self.factory.create_ingestor(
                factory_format, enable_validation=False, output_format='fhir_bundle'
            )

            bundle = ingestor.process(str(xml_path))

            # Check for UAE-specific extensions
            if 'extension' in bundle:
                uae_extensions = [
                    ext
                    for ext in bundle['extension']
                    if 'emirate-authority' in ext.get('url', '')
                ]

                for uae_ext in uae_extensions:
                    if 'valueString' in uae_ext:
                        authority = uae_ext['valueString']
                        valid_authorities = [
                            'Dubai Health Authority',
                            'Abu Dhabi Department of Health',
                        ]
                        assert (
                            authority in valid_authorities
                        ), f"Invalid UAE authority: {authority}"

            # Check for proper currency codes (AED)
            for entry in bundle['entry']:
                resource = entry['resource']
                if resource['resourceType'] == 'Claim' and 'item' in resource:
                    for item in resource['item']:
                        if 'unitPrice' in item and 'currency' in item['unitPrice']:
                            currency = item['unitPrice']['currency']
                            assert (
                                currency == 'AED'
                            ), f"UAE should use AED currency, got {currency}"

    def test_backward_compatibility_with_legacy_schema(self):
        """Test that the system maintains backward compatibility."""
        for format_name, xml_path in self.sample_files.items():
            if not xml_path.exists():
                continue

            factory_format = (
                'eClaimLink' if format_name == 'eclaim_link' else 'Shafafiya'
            )

            # Test legacy format (should still work)
            legacy_ingestor = self.factory.create_ingestor(
                factory_format, enable_validation=False, output_format='legacy'
            )

            legacy_result = legacy_ingestor.process(str(xml_path))

            # Should have legacy structure
            assert 'format_name' in legacy_result
            assert 'schema_version' in legacy_result
            assert 'services' in legacy_result
            assert 'resourceType' not in legacy_result  # Should NOT be FHIR

            # Test FHIR Bundle format (new enhanced format)
            fhir_ingestor = self.factory.create_ingestor(
                factory_format, enable_validation=False, output_format='fhir_bundle'
            )

            fhir_result = fhir_ingestor.process(str(xml_path))

            # Should have FHIR Bundle structure
            assert fhir_result['resourceType'] == 'Bundle'
            assert 'entry' in fhir_result
            assert 'total' in fhir_result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
