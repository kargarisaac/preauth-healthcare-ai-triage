"""
Pre-Authorization Intake Module
==============================

Handles the intake and normalization of eClaimLink/Shafafiya payloads into canonical PA requests.
Includes XML validation, field extraction, and basic code normalization.

Key Functions:
- eClaimLink → canonical PA request mapping  
- XML schema validation and field extraction
- Basic ICD-10 and CPT code normalization
- Integration with existing XML parsing utilities
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import re
from dataclasses import dataclass

from preauth_system.utils import parse_xml, extract_patient_info


@dataclass
class CanonicalPARequest:
    """
    Canonical Prior Authorization Request structure following FHIR-like patterns.
    """

    # Request Metadata
    request_id: str
    timestamp: str
    format_source: str  # 'eclaim' or 'shafafiya'

    # Patient Information
    patient: Dict[str, Any]

    # Provider Information
    provider: Dict[str, Any]

    # Service Requests
    services: List[Dict[str, Any]]

    # Clinical Context
    justification: str
    diagnoses: List[Dict[str, Any]]

    # Supporting Data
    supporting_docs: List[Dict[str, Any]]

    # Validation Status
    validation_status: str  # 'valid', 'warning', 'error'
    validation_messages: List[str]

    # Financial
    total_cost: float
    currency: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "request_id": self.request_id,
            "timestamp": self.timestamp,
            "format_source": self.format_source,
            "patient": self.patient,
            "provider": self.provider,
            "services": self.services,
            "justification": self.justification,
            "diagnoses": self.diagnoses,
            "supporting_docs": self.supporting_docs,
            "validation_status": self.validation_status,
            "validation_messages": self.validation_messages,
            "total_cost": self.total_cost,
            "currency": self.currency,
        }


class CodeNormalizer:
    """
    Basic code normalization for ICD-10 and CPT codes used in UAE healthcare.
    """

    # Basic ICD-10 mappings for common conditions
    ICD10_MAPPINGS = {
        "E10": "Type 1 diabetes mellitus",
        "E10.9": "Type 1 diabetes mellitus without complications",
        "E11": "Type 2 diabetes mellitus",
        "E11.9": "Type 2 diabetes mellitus without complications",
        "M17": "Gonarthrosis [arthrosis of knee]",
        "M17.9": "Gonarthrosis, unspecified",
        "G20": "Parkinson disease",
        "I25": "Chronic ischemic heart disease",
        "J44": "Other chronic obstructive pulmonary disease",
    }

    # Basic CPT/Activity code mappings for common procedures
    CPT_MAPPINGS = {
        "E0784": "External insulin pump, continuous glucose monitor",
        "95250": "Ambulatory continuous glucose monitoring",
        "90772": "Therapeutic injection",
        "99244": "Office consultation, comprehensive",
        "82962": "Glucose-6-phosphate dehydrogenase",
        "82270": "Blood, occult, by peroxidase activity",
        "29881": "Arthroscopy, knee, surgical",
        "20610": "Arthrocentesis, aspiration and/or injection",
        "61885": "Insertion or replacement of cranial neurostimulator",
    }

    @classmethod
    def normalize_icd10(cls, code: str) -> Dict[str, Any]:
        """
        Normalize ICD-10 diagnosis code.

        Args:
            code: Raw ICD-10 code

        Returns:
            Dict with normalized code and description
        """
        if not code:
            return {"code": "", "description": "", "system": "ICD-10", "valid": False}

        # Clean code - remove spaces and convert to uppercase
        clean_code = code.strip().upper()

        # Basic validation - ICD-10 pattern
        icd10_pattern = r"^[A-Z]\d{2}(\.\d{1,2})?$"
        is_valid = bool(re.match(icd10_pattern, clean_code))

        description = cls.ICD10_MAPPINGS.get(clean_code, "")
        if not description and is_valid:
            # Extract category description for unknown specific codes
            category = clean_code[:3]
            description = cls.ICD10_MAPPINGS.get(category, "Unknown diagnosis")

        return {
            "code": clean_code,
            "description": description,
            "system": "ICD-10",
            "valid": is_valid,
            "category": clean_code[:3] if len(clean_code) >= 3 else clean_code,
        }

    @classmethod
    def normalize_cpt(cls, code: str) -> Dict[str, Any]:
        """
        Normalize CPT/Activity code.

        Args:
            code: Raw CPT/Activity code

        Returns:
            Dict with normalized code and description
        """
        if not code:
            return {"code": "", "description": "", "system": "CPT", "valid": False}

        clean_code = code.strip()

        # Check if it's a standard 5-digit CPT code or equipment code
        cpt_pattern = r"^\d{5}$|^[A-Z]\d{4}$"
        is_valid = bool(re.match(cpt_pattern, clean_code))

        description = cls.CPT_MAPPINGS.get(clean_code, "")
        if not description:
            description = "Medical procedure/service"

        return {
            "code": clean_code,
            "description": description,
            "system": "CPT",
            "valid": is_valid,
        }


class IntakeValidator:
    """
    Validates PA requests for completeness and data quality.
    """

    REQUIRED_PATIENT_FIELDS = [
        "EmiratesIDNumber",
        "FirstName",
        "LastName",
        "DateOfBirth",
        "Gender",
    ]

    REQUIRED_SERVICE_FIELDS = ["code", "description", "diagnosis_code"]

    @classmethod
    def validate_pa_request(
        cls, pa_request: CanonicalPARequest
    ) -> Tuple[str, List[str]]:
        """
        Validate PA request for required fields and data quality.

        Args:
            pa_request: Canonical PA request to validate

        Returns:
            Tuple of (status, validation_messages)
            status: 'valid', 'warning', 'error'
        """
        messages = []
        has_errors = False
        has_warnings = False

        # Validate patient information
        patient = pa_request.patient
        for field in cls.REQUIRED_PATIENT_FIELDS:
            if not patient.get(field):
                messages.append(f"Missing required patient field: {field}")
                has_errors = True

        # Validate Emirates ID format
        emirates_id = patient.get("EmiratesIDNumber", "")
        if emirates_id and not re.match(r"^\d{3}-\d{4}-\d{7}-\d$", emirates_id):
            messages.append(f"Invalid Emirates ID format: {emirates_id}")
            has_warnings = True

        # Validate services
        if not pa_request.services:
            messages.append("No services requested")
            has_errors = True
        else:
            for i, service in enumerate(pa_request.services):
                for field in cls.REQUIRED_SERVICE_FIELDS:
                    if not service.get(field):
                        messages.append(
                            f"Missing required field '{field}' in service {i+1}"
                        )
                        has_errors = True

        # Validate justification
        if not pa_request.justification or len(pa_request.justification.strip()) < 50:
            messages.append(
                "Clinical justification is missing or too brief (<50 characters)"
            )
            has_warnings = True

        # Validate total cost
        if pa_request.total_cost <= 0:
            messages.append("Total cost must be greater than zero")
            has_warnings = True

        # Determine overall status
        if has_errors:
            status = "error"
        elif has_warnings:
            status = "warning"
        else:
            status = "valid"
            messages.append("PA request validation passed")

        return status, messages


def process_eclaim_request(xml_file_path: str) -> CanonicalPARequest:
    """
    Process eClaimLink XML request into canonical PA request.

    Args:
        xml_file_path: Path to eClaimLink XML file

    Returns:
        CanonicalPARequest object

    Raises:
        Exception: If XML parsing or processing fails
    """
    # Parse XML
    xml_data = parse_xml(xml_file_path, "eclaim")
    patient_info = extract_patient_info(xml_data, "eclaim")
    xml_dict = xml_data["as_dict"]

    # Generate request ID
    request_id = f"PA-ECLAIM-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # Extract and normalize patient information
    patient_data = xml_dict.get("Patient", {})
    patient = {
        "EmiratesIDNumber": patient_data.get("EmiratesIDNumber"),
        "FirstName": patient_data.get("FirstName"),
        "LastName": patient_data.get("LastName"),
        "DateOfBirth": patient_data.get("DateOfBirth"),
        "Gender": patient_data.get("Gender"),
        "Nationality": patient_data.get("Nationality"),
        "PhoneNumber": patient_data.get("PhoneNumber"),
        "Email": patient_data.get("Email"),
        "Weight": patient_data.get("Weight"),
        "Height": patient_data.get("Height"),
        "member_id": patient_data.get("MemberID"),
        "insurance_policy": patient_data.get("InsurancePolicy", {}),
        "medical_history": patient_data.get("MedicalHistory", {}),
    }

    # Extract provider information
    provider_data = xml_dict.get("Provider", {})
    provider = {
        "provider_id": provider_data.get("ProviderID"),
        "name": provider_data.get("ProviderName"),
        "license_number": provider_data.get("LicenseNumber"),
        "npi": provider_data.get("ProviderNPI"),
        "contact_person": provider_data.get("ContactPerson"),
        "phone": provider_data.get("PhoneNumber"),
        "email": provider_data.get("Email"),
        "specialty": provider_data.get("Specialty"),
        "address": provider_data.get("Address", {}),
    }

    # Process service requests with code normalization
    service_requests = xml_dict.get("ServiceRequests", {}).get("ServiceRequest", [])
    if isinstance(service_requests, dict):
        service_requests = [service_requests]  # Handle single service case

    services = []
    diagnoses_set = set()  # Track unique diagnoses
    total_cost = 0.0

    for service in service_requests:
        # Extract basic service info with namespace-aware handling
        raw_activity = service.get("ct:ActivityCode", "") or service.get(
            "http://www.eclaimlink.ae/DHD/ValidationSchema:ActivityCode", ""
        )
        raw_diagnosis = service.get("ct:DiagnosisCode", "") or service.get(
            "http://www.eclaimlink.ae/DHD/ValidationSchema:DiagnosisCode", ""
        )
        raw_instructions = service.get("ct:ActivityInstructions", "") or service.get(
            "http://www.eclaimlink.ae/DHD/ValidationSchema:ActivityInstructions", ""
        )

        # Normalize codes
        normalized_activity = CodeNormalizer.normalize_cpt(raw_activity)
        normalized_diagnosis = CodeNormalizer.normalize_icd10(raw_diagnosis)

        # Extract cost
        amount_data = service.get("RequestedAmount", {})
        if isinstance(amount_data, dict):
            amount = float(amount_data.get("#text", 0) or 0)
            currency = amount_data.get("@currency", "AED")
        else:
            amount = float(amount_data or 0)
            currency = "AED"

        service_info = {
            "code": normalized_activity.get("code"),
            "description": normalized_activity.get("description"),
            "activity_code": normalized_activity,
            "diagnosis_code": normalized_diagnosis,
            "instructions": raw_instructions,
            "requested_date": service.get("ct:ActivityDateTime")
            or service.get(
                "http://www.eclaimlink.ae/DHD/ValidationSchema:ActivityDateTime"
            ),
            "amount": amount,
            "currency": currency,
        }

        services.append(service_info)
        total_cost += amount

        # Collect unique diagnoses
        if raw_diagnosis:
            diagnoses_set.add(raw_diagnosis)

    # Create diagnoses list
    diagnoses = [CodeNormalizer.normalize_icd10(code) for code in diagnoses_set]

    # Extract supporting documentation
    supporting_docs = []
    doc_data = xml_dict.get("SupportingDocumentation", {}).get("Document", [])
    if isinstance(doc_data, dict):
        doc_data = [doc_data]

    for doc in doc_data:
        supporting_docs.append(
            {
                "type": doc.get("@type", ""),
                "description": doc.get("Description", ""),
                "date": doc.get("Date", ""),
            }
        )

    # Create canonical PA request
    pa_request = CanonicalPARequest(
        request_id=request_id,
        timestamp=datetime.now().isoformat(),
        format_source="eclaim",
        patient=patient,
        provider=provider,
        services=services,
        justification=xml_dict.get("JustificationText", ""),
        diagnoses=diagnoses,
        supporting_docs=supporting_docs,
        validation_status="pending",
        validation_messages=[],
        total_cost=total_cost,
        currency=currency,
    )

    # Validate the request
    status, messages = IntakeValidator.validate_pa_request(pa_request)
    pa_request.validation_status = status
    pa_request.validation_messages = messages

    return pa_request


def process_pa_request(xml_file_path: str, xml_format: str) -> CanonicalPARequest:
    """
    Process PA request from XML file into canonical format.

    Args:
        xml_file_path: Path to XML file
        xml_format: Format type ('eclaim' or 'shafafiya')

    Returns:
        CanonicalPARequest object

    Raises:
        ValueError: If XML format is not supported
        Exception: If processing fails
    """
    if xml_format != "eclaim":
        raise ValueError(
            f"Unsupported XML format: {xml_format}. Only 'eclaim' is supported."
        )
    return process_eclaim_request(xml_file_path)


# Example usage and testing
if __name__ == "__main__":
    # Test with Patient_007 (APPROVE case)
    try:
        # Use configuration manager for file paths
        from preauth_system.config_manager import get_config_manager

        config_mgr = get_config_manager()
        storage_config = config_mgr.get_storage_config()
        xml_path = str(
            storage_config.data_directory
            / "dataset_2/synthetic_dataset/UAE_XML/Patient_007_eclaim.xml"
        )
        pa_request = process_pa_request(xml_path, "eclaim")

        print(f"✅ Processed PA request: {pa_request.request_id}")
        print(
            f"   Patient: {pa_request.patient.get('FirstName')} {pa_request.patient.get('LastName')}"
        )
        print(f"   Emirates ID: {pa_request.patient.get('EmiratesIDNumber')}")
        print(f"   Services: {len(pa_request.services)}")
        print(f"   Total Cost: {pa_request.total_cost} {pa_request.currency}")
        print(f"   Validation: {pa_request.validation_status}")

        if pa_request.validation_messages:
            print("   Messages:")
            for msg in pa_request.validation_messages:
                print(f"     - {msg}")

        # Print first service as example
        if pa_request.services:
            service = pa_request.services[0]
            print(
                f"   First Service: {service['activity_code']['code']} - {service['activity_code']['description']}"
            )

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
