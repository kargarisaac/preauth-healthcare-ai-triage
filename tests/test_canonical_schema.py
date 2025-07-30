import json
import sys
from pathlib import Path

import jsonschema
import pytest
from jsonschema import validate

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_pipelines.eclaim_link import normalize_prior_authorization  # noqa: E402


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

        # Path to sample XML
        cls.sample_xml_path = project_root / "samples" / "prior_auth_request.xml"

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

    def test_resource_type_is_claim(self):
        """Test that resourceType is set to 'Claim'."""
        assert self.example_claim["resourceType"] == "Claim"

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
        """Test transformation from XML to canonical format."""
        if not self.sample_xml_path.exists():
            pytest.skip("Sample XML file not found")

        # Transform the XML
        normalized = normalize_prior_authorization(str(self.sample_xml_path))

        # Create a minimal canonical structure from normalized data
        canonical = self._create_canonical_from_normalized(normalized)

        # Validate the transformed data against schema
        validate(instance=canonical, schema=self.schema)

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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
