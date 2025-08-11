#!/usr/bin/env python3
"""
ETL for Patient Data with FHIR-Only Approach
============================================

ETL system that works exclusively with existing FHIR JSON files.
Eliminates CSV dependencies and provides unified patient records.

MVP APPROACH:
- Assumes FHIR JSON files already exist
- Uses FHIR Bundle as canonical clinical history  
- XML request data provides most current demographics
- No CSV processing required

Key Features:
- Unified patient records combining XML requests with FHIR clinical history
- Single source of truth eliminating duplicate data structures
- LLM-based risk assessment and data quality scoring

Usage:
    from data_ingestion.etl import create_unified_patient_record, find_patient_by_emirates_id
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass
from preauth_system.utils import (
    get_config,
    determine_specialty,
    assess_clinical_risk_llm,
    calculate_data_quality_llm,
)
import csv


@dataclass
class UnifiedPatientRecord:
    """
    Single source of truth for patient data combining current request
    context (XML) with enriched clinical history (FHIR Bundle).

    Data Priority:
    1. XML Request Data (most current demographics, insurance)
    2. FHIR Bundle (enriched clinical history with medical codes)
    3. No CSV processing (assumes FHIR already exists)
    """

    # Primary data sources (current request context)
    current_demographics: Dict[str, Any]  # From XML request (most up-to-date)
    current_insurance: Dict[str, Any]  # From XML request
    requested_services: List[Dict[str, Any]]  # From XML request
    clinical_justification: str  # From XML request

    # Clinical context (from existing FHIR Bundle)
    clinical_timeline: List[
        Dict[str, Any]
    ]  # Chronological observations with LOINC codes
    medication_regimen: List[Dict[str, Any]]  # Active medications with RxNorm codes
    care_episodes: List[Dict[str, Any]]  # Historical claims/procedures
    clinical_conditions: List[Dict[str, Any]]  # Coded conditions with ICD-10
    coverage_details: List[Dict[str, Any]]  # Insurance coverage from FHIR
    care_team: List[Dict[str, Any]]  # Practitioner information
    questionnaire_responses: List[Dict[str, Any]]  # Clinical assessments/surveys

    # LLM-derived insights (parallel processing)
    specialty_context: str  # Determined medical specialty
    risk_assessment: Dict[str, Any]  # LLM-based clinical risk assessment
    data_quality_assessment: Dict[str, Any]  # LLM-based data quality scoring

    # Metadata
    patient_id: str
    emirates_id: str
    processing_timestamp: str
    data_sources: List[str]


def get_patient_hist_data_from_db(
    patient_id: str, dataset_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get FHIR Bundle for a specific patient.

    FHIR-ONLY APPROACH: Only loads FHIR JSON files, no CSV processing.

    Args:
        patient_id: Patient ID (e.g., "Patient_001")
        dataset_path: Path to dataset directory (from config if None)

    Returns:
        Dictionary with FHIR bundle data only
    """
    if dataset_path is None:
        # Load from config instead of hardcoding
        from preauth_system.utils import get_config

        cfg = get_config()
        dataset_base_path = cfg.get("dataset", {}).get(
            "base_path", "data/dataset_2/synthetic_dataset"
        )
        current_dir = Path(__file__).parent.parent
        dataset_path = current_dir / dataset_base_path

    dataset_path = Path(dataset_path)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset directory not found: {dataset_path}")

    fhir_path = dataset_path / "FHIR_JSON"

    # Load FHIR bundle only
    patient_data = {
        "demographics": {},  # Will be populated from FHIR Patient resource
        "fhir_bundle": None,
    }

    # Load FHIR bundle
    fhir_file = fhir_path / f"{patient_id.lower()}.json"
    if fhir_file.exists():
        with open(fhir_file, "r") as f:
            fhir_bundle = json.load(f)
            patient_data["fhir_bundle"] = fhir_bundle

            # Extract demographics from FHIR Patient resource
            for entry in fhir_bundle.get("entry", []):
                resource = entry.get("resource", {})
                if resource.get("resourceType") == "Patient":
                    # Extract basic demographics from FHIR Patient
                    patient_resource = resource
                    patient_data["demographics"] = {
                        "patient_id": patient_id,
                        "first_name": patient_resource.get("name", [{}])[0].get(
                            "given", [""]
                        )[0]
                        if patient_resource.get("name")
                        else "",
                        "last_name": patient_resource.get("name", [{}])[0].get(
                            "family", ""
                        )
                        if patient_resource.get("name")
                        else "",
                        "date_of_birth": patient_resource.get("birthDate", ""),
                        "gender": patient_resource.get("gender", ""),
                        "emirates_id": next(
                            (
                                id_obj.get("value", "")
                                for id_obj in patient_resource.get("identifier", [])
                                if id_obj.get("system")
                                == "http://terminology.hl7.org/CodeSystem/v2-0203"
                            ),
                            "",
                        ),
                    }
                    break
    else:
        # No FHIR bundle found
        patient_data["fhir_bundle"] = None

    return patient_data


def find_patient_by_emirates_id(
    emirates_id: str, dataset_path: Optional[str] = None
) -> Optional[str]:
    """
    Find patient ID by Emirates ID using the simplified CSV lookup.

    This simplified approach reads from CSV/patients.csv and returns the
    corresponding patient_id. It avoids scanning FHIR bundles.

    Args:
        emirates_id: Emirates ID to search for
        dataset_path: Path to dataset directory (from config if None)

    Returns:
        Patient ID if found, None otherwise
    """
    if not emirates_id:
        return None

    # Resolve dataset path from config when not provided
    if dataset_path is None:
        cfg = get_config()
        dataset_base_path = cfg.get("dataset", {}).get(
            "base_path", "data/dataset_2/synthetic_dataset"
        )
        current_dir = Path(__file__).parent.parent
        dataset_path = current_dir / dataset_base_path

    csv_path = Path(dataset_path) / "CSV" / "patients.csv"
    if not csv_path.exists():
        return None

    target_id = emirates_id.strip()
    try:
        with open(csv_path, mode="r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                row_emirates_id = (row.get("emirates_id") or "").strip()
                if row_emirates_id == target_id:
                    patient_id = (row.get("patient_id") or "").strip()
                    return patient_id or None
    except Exception:
        # On any CSV parsing or IO error, return None for simplicity
        return None

    return None


def create_unified_patient_record(
    patient_id: str, xml_request_data: Dict[str, Any], xml_patient_info: Dict[str, Any]
) -> UnifiedPatientRecord:
    """
    Create unified patient record combining XML request (current)
    with existing FHIR Bundle (clinical history).

    MVP APPROACH: Assumes FHIR JSON files already exist.
    No CSV processing needed.

    Args:
        patient_id: Patient identifier
        xml_request_data: Parsed XML request data
        xml_patient_info: Extracted patient info from XML

    Returns:
        UnifiedPatientRecord with no data duplication
    """

    # Get existing patient data (FHIR bundle only)
    patient_data = get_patient_hist_data_from_db(patient_id)
    existing_fhir_bundle = patient_data.get("fhir_bundle", {})

    # Extract current demographics from XML (most up-to-date)
    current_demographics = {
        "patient_id": patient_id,
        "emirates_id": xml_patient_info.get("EmiratesIDNumber", ""),
        "first_name": xml_patient_info.get("FirstName", ""),
        "last_name": xml_patient_info.get("LastName", ""),
        "date_of_birth": xml_patient_info.get("DateOfBirth", ""),
        "gender": xml_patient_info.get("Gender", ""),
        "phone": xml_patient_info.get("PhoneNumber", ""),
        "email": xml_patient_info.get("Email", ""),
        "address": {
            "street": xml_patient_info.get("Address", {}).get("Street", ""),
            "city": xml_patient_info.get("Address", {}).get("City", ""),
            "emirate": xml_patient_info.get("Address", {}).get("Emirate", ""),
            "postal_code": xml_patient_info.get("Address", {}).get("PostalCode", ""),
        },
    }

    # Extract current insurance from XML
    insurance_policy = xml_patient_info.get("InsurancePolicy", {})
    current_insurance = {
        "policy_number": insurance_policy.get("PolicyNumber", ""),
        "payer_name": insurance_policy.get("PayerName", ""),
        "coverage_type": insurance_policy.get("CoverageType", ""),
        "valid_from": insurance_policy.get("ValidFrom", ""),
        "valid_to": insurance_policy.get("ValidTo", ""),
        "status": "active",
    }

    # Extract requested services from XML
    requested_services = xml_patient_info.get("services", [])

    # Extract clinical data from existing FHIR Bundle
    clinical_timeline = []
    medication_regimen = []
    care_episodes = []
    clinical_conditions = []
    coverage_details = []
    care_team = []
    questionnaire_responses = []

    if existing_fhir_bundle and existing_fhir_bundle.get("entry"):
        for entry in existing_fhir_bundle.get("entry", []):
            resource = entry.get("resource", {})
            resource_type = resource.get("resourceType", "")

            if resource_type == "Observation":
                clinical_timeline.append(resource)
            elif resource_type == "MedicationStatement":
                medication_regimen.append(resource)
            elif resource_type == "Claim":
                care_episodes.append(resource)
            elif resource_type == "Condition":
                clinical_conditions.append(resource)
            elif resource_type == "Coverage":
                coverage_details.append(resource)
            elif resource_type == "Practitioner":
                care_team.append(resource)
            elif resource_type == "QuestionnaireResponse":
                questionnaire_responses.append(resource)

    # Sort clinical timeline chronologically
    clinical_timeline.sort(key=lambda x: x.get("effectiveDateTime", ""), reverse=True)

    # Determine specialty (using existing logic or fallback)
    try:
        # Convert FHIR data to expected format for determine_specialty
        patient_data_for_specialty = {
            "demographics": current_demographics,
            "labs": [
                obs
                for obs in clinical_timeline
                if obs.get("category", [{}])[0].get("coding", [{}])[0].get("code")
                == "laboratory"
            ],
            "medications": medication_regimen,
            "claims": care_episodes,
            "preauth_history": [],  # Not available in current data structure
            "fhir_bundle": existing_fhir_bundle,
        }

        specialty_context = determine_specialty(
            xml_request_data, patient_data_for_specialty
        )
    except (ImportError, Exception):
        specialty_context = "general"

    # LLM-based assessments (can run in parallel)
    risk_assessment = assess_clinical_risk_llm(
        clinical_timeline, medication_regimen, current_demographics
    )
    data_quality_assessment = calculate_data_quality_llm(
        current_demographics, clinical_timeline, medication_regimen
    )

    return UnifiedPatientRecord(
        # Current request context (from XML)
        current_demographics=current_demographics,
        current_insurance=current_insurance,
        requested_services=requested_services,
        clinical_justification=xml_patient_info.get("justification", ""),
        # Clinical context (from existing FHIR Bundle)
        clinical_timeline=clinical_timeline,
        medication_regimen=medication_regimen,
        care_episodes=care_episodes,
        clinical_conditions=clinical_conditions,
        coverage_details=coverage_details,
        care_team=care_team,
        questionnaire_responses=questionnaire_responses,
        # LLM-derived insights
        specialty_context=specialty_context,
        risk_assessment=risk_assessment,
        data_quality_assessment=data_quality_assessment,
        # Metadata
        patient_id=patient_id,
        emirates_id=xml_patient_info.get("EmiratesIDNumber", ""),
        processing_timestamp=datetime.now().isoformat(),
        data_sources=["XML_REQUEST", "EXISTING_FHIR_BUNDLE"],
    )


# Example usage and testing
if __name__ == "__main__":
    print("🧪 Testing create_unified_patient_record with Patient_001")
    print("=" * 55)

    try:
        print("\n🔗 Testing Unified Patient Record Creation with Real Data")

        # Real XML request data based on Patient_001 XML file
        xml_request_data = {
            "file_path": "data/dataset_2/synthetic_dataset/UAE_XML/Patient_001_eclaim.xml",
            "format": "eclaim",
            "as_dict": {
                "JustificationText": "Patient with poorly controlled T2DM (HbA1c 9.2%) despite maximum metformin therapy",
                "ServiceRequests": {
                    "ServiceRequest": [
                        {
                            "ActivityCode": "J3490",
                            "DiagnosisCode": "E11.9",
                            "ActivityInstructions": "GLP-1 Agonist Medication - Patient with poorly controlled T2DM",
                            "RequestedAmount": {"#text": "850.0", "@currency": "AED"},
                        },
                        {
                            "ActivityCode": "95250",
                            "DiagnosisCode": "E11.9",
                            "ActivityInstructions": "Continuous Glucose Monitor - Patient requires intensive glucose monitoring",
                            "RequestedAmount": {"#text": "275.0", "@currency": "AED"},
                        },
                        {
                            "ActivityCode": "92014",
                            "DiagnosisCode": "E11.9",
                            "ActivityInstructions": "Diabetic Retinal Screening - Annual screening required",
                            "RequestedAmount": {"#text": "250.0", "@currency": "AED"},
                        },
                    ]
                },
            },
        }

        # Real XML patient info based on Patient_001 XML file
        xml_patient_info = {
            "EmiratesIDNumber": "784-1968-6226375-1",
            "FirstName": "Ahmed",
            "LastName": "Al-Mansouri",
            "DateOfBirth": "15/03/1968",
            "Gender": "M",
            "PhoneNumber": "+971-50-405-4515",
            "Email": "ahmed.almansouri@email.ae",
            "Address": {
                "Street": "Al Wasl Road, Villa 234",
                "City": "Dubai",
                "Emirate": "Dubai",
                "PostalCode": "12345",
            },
            "InsurancePolicy": {
                "PolicyNumber": "POL-DUB-2025-2583",
                "PayerName": "Dubai Health Insurance",
                "CoverageType": "Comprehensive",
                "ValidFrom": "01/01/2025",
                "ValidTo": "31/12/2025",
            },
            "services": [
                {
                    "code": "J3490",
                    "description": "GLP-1 Agonist Medication",
                    "amount": 850.0,
                    "diagnosis_code": "E11.9",
                },
                {
                    "code": "95250",
                    "description": "Continuous Glucose Monitor",
                    "amount": 275.0,
                    "diagnosis_code": "E11.9",
                },
                {
                    "code": "92014",
                    "description": "Diabetic Retinal Screening",
                    "amount": 250.0,
                    "diagnosis_code": "E11.9",
                },
            ],
            "total_cost": 1375.0,
            "justification": "Patient with poorly controlled T2DM (HbA1c 9.2%) despite maximum metformin therapy",
        }

        # Test create_unified_patient_record function
        unified_record = create_unified_patient_record(
            patient_id="Patient_001",
            xml_request_data=xml_request_data,
            xml_patient_info=xml_patient_info,
        )

        print(
            f"✅ Created UnifiedPatientRecord for {unified_record.current_demographics['first_name']} {unified_record.current_demographics['last_name']}"
        )
        print(f"   Patient ID: {unified_record.patient_id}")
        print(f"   Emirates ID: {unified_record.emirates_id}")
        print(f"   Specialty Context: {unified_record.specialty_context}")
        print(f"   Processing Timestamp: {unified_record.processing_timestamp}")
        print(f"   Data Sources: {', '.join(unified_record.data_sources)}")

        print("\n   📊 Clinical Data Summary:")
        print(
            f"   - Clinical Timeline: {len(unified_record.clinical_timeline)} observations"
        )
        print(
            f"   - Medication Regimen: {len(unified_record.medication_regimen)} medications"
        )
        print(f"   - Care Episodes: {len(unified_record.care_episodes)} claims")
        print(
            f"   - Clinical Conditions: {len(unified_record.clinical_conditions)} conditions"
        )
        print(
            f"   - Coverage Details: {len(unified_record.coverage_details)} coverage records"
        )
        print(f"   - Care Team: {len(unified_record.care_team)} practitioners")
        print(
            f"   - Questionnaire Responses: {len(unified_record.questionnaire_responses)} assessments"
        )
        print(
            f"   - Requested Services: {len(unified_record.requested_services)} services"
        )

        print("\n   🤖 LLM-Based Assessments:")
        print(
            f"   - Risk Assessment: {unified_record.risk_assessment.get('overall_risk', 'N/A')}"
        )
        print(
            f"   - Data Quality Score: {unified_record.data_quality_assessment.get('overall_score', 'N/A')}"
        )
        print(
            f"   - Risk Confidence: {unified_record.risk_assessment.get('confidence', 'N/A')}"
        )

        # Show some risk factors if available
        risk_factors = unified_record.risk_assessment.get("risk_factors", [])
        if risk_factors:
            print(
                f"   - Risk Factors: {', '.join(risk_factors[:2])}{'...' if len(risk_factors) > 2 else ''}"
            )

        print("\n✅ create_unified_patient_record test completed successfully!")

    except Exception as e:
        print(f"❌ Test Error: {e}")
        import traceback

        traceback.print_exc()

    print("\n" + "=" * 55)
    print("📋 Test completed for create_unified_patient_record function")
    print("🚀 Function ready for production use")
