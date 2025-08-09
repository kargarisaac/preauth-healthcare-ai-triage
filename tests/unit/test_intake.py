"""
Unit tests for the intake module (updated for current API).
"""

import pytest
from typing import Dict, Any
from unittest.mock import patch

from preauth_system.intake import (
    CanonicalPARequest,
    CodeNormalizer,
    process_pa_request,
    IntakeValidator,
)


class TestCanonicalPARequest:
    def test_canonical_request_to_dict(self):
        request = CanonicalPARequest(
            request_id="TEST-001",
            timestamp="2025-08-08T10:00:00Z",
            format_source="eclaim",
            patient={"id": "P123"},
            provider={"id": "PROV001"},
            services=[{"code": "95250", "description": "CGM"}],
            justification="Patient needs CGM for diabetes management",
            diagnoses=[{"code": "E11.9", "description": "Type 2 diabetes"}],
            supporting_docs=[],
            validation_status="valid",
            validation_messages=[],
            total_cost=500.0,
            currency="AED",
        )
        result = request.to_dict()
        assert result["request_id"] == "TEST-001"
        assert result["format_source"] == "eclaim"
        assert result["total_cost"] == 500.0


class TestCodeNormalizer:
    def test_icd10_normalization_dict(self):
        obj = CodeNormalizer.normalize_icd10("E11.9")
        assert obj["code"] == "E11.9"
        assert obj["system"] == "ICD-10"
        assert obj["valid"] is True

    def test_cpt_normalization_dict(self):
        obj = CodeNormalizer.normalize_cpt("95250")
        assert obj["code"] == "95250"
        assert obj["system"] == "CPT"
        assert isinstance(obj["description"], str)


class TestProcessPARequest:
    def test_process_pa_request_eclaim(self, tmp_path):
        xml_content = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<PriorAuthorizationRequest xmlns:ct=\"http://www.eclaimlink.ae/DHD/ValidationSchema\">
  <Header>
    <SenderID>API_TEST</SenderID>
    <TransactionID>API-001</TransactionID>
    <TransactionDateTime>08/08/2025 10:00</TransactionDateTime>
  </Header>
  <JustificationText>Test request with adequate justification text to pass validation length.</JustificationText>
  <ServiceRequests>
    <ServiceRequest>
      <ct:ActivityCode>95250</ct:ActivityCode>
      <ct:DiagnosisCode>E11.9</ct:DiagnosisCode>
      <RequestedAmount currency=\"AED\">1200.00</RequestedAmount>
    </ServiceRequest>
  </ServiceRequests>
</PriorAuthorizationRequest>"""
        xml_file = tmp_path / "test.xml"
        xml_file.write_text(xml_content, encoding="utf-8")

        with patch(
            "preauth_system.utils.extract_patient_info",
            return_value={"patient_id": "P123"},
        ):
            pa = process_pa_request(str(xml_file), "eclaim")
        assert pa.format_source == "eclaim"
        assert pa.total_cost == 1200.00
        assert len(pa.services) == 1

    def test_validate_pa_request(self, tmp_path):
        # Build minimal valid request and validate
        pa = CanonicalPARequest(
            request_id="TEST-002",
            timestamp="2025-08-08T10:00:00Z",
            format_source="eclaim",
            patient={
                "EmiratesIDNumber": "784-1972-1234567-1",
                "FirstName": "Test",
                "LastName": "User",
                "DateOfBirth": "01/01/1990",
                "Gender": "M",
            },
            provider={},
            services=[
                {"code": "95250", "description": "CGM", "diagnosis_code": "E11.9"}
            ],
            justification="Sufficient clinical justification text that passes the length requirement.",
            diagnoses=[{"code": "E11.9", "description": "Type 2 diabetes"}],
            supporting_docs=[],
            validation_status="pending",
            validation_messages=[],
            total_cost=100.0,
            currency="AED",
        )
        status, messages = IntakeValidator.validate_pa_request(pa)
        assert status in ["valid", "warning"]
        assert isinstance(messages, list)
