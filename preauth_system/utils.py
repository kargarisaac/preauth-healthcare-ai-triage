"""
Utility functions for the Pre-Authorization system.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import xmltodict  # type: ignore
import yaml  # type: ignore

import datetime as _dt
from loguru import logger


def get_config() -> Dict[str, Any]:
    """Load configuration exclusively from preauth_system/config.yaml."""
    cfg_path = Path(__file__).parent / "config.yaml"
    if not (yaml and cfg_path.exists()):
        return {}
    try:
        return yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


# Global config loaded from YAML
_CFG = get_config()


def parse_xml(xml_file_path: str, xml_format: str) -> Dict[str, Any]:
    """
    Parse XML file and determine format.
    """
    with open(xml_file_path, "r", encoding="utf-8") as f:
        xml_content = f.read()
    try:
        xml_dict = xmltodict.parse(xml_content, process_namespaces=True)
    except Exception as ex:
        raise Exception(f"xmltodict failed to parse XML: {ex}")

    if xml_format == "eclaim":
        xml_dict = xml_dict["PriorAuthorizationRequest"]
    elif xml_format == "shafafiya":
        pass
    else:
        raise ValueError(f"Unknown XML format: {xml_format}")

    return {
        "file_path": xml_file_path,
        "format": xml_format,
        "as_dict": xml_dict,
    }


def extract_patient_info(xml_data: Dict[str, Any], xml_format: str) -> Dict[str, Any]:
    """Extract patient info from XML (Emirates ID, services, total_cost, justification)."""
    patient_info: Dict[str, Any] = {}

    if xml_format == "eclaim":
        xml_dict = xml_data.get("as_dict", {})
        patient_data = xml_dict.get("Patient", {})

        # Extract Emirates ID
        patient_info["EmiratesIDNumber"] = patient_data.get("EmiratesIDNumber")

        # Extract services from ServiceRequests
        service_requests = xml_dict.get("ServiceRequests", {}).get("ServiceRequest", [])
        if isinstance(service_requests, dict):
            service_requests = [service_requests]

        services = []
        total_cost = 0.0
        for service in service_requests:
            activity_code = service.get("ct:ActivityCode", "") or service.get(
                "http://www.eclaimlink.ae/DHD/ValidationSchema:ActivityCode", ""
            )
            instructions = service.get("ct:ActivityInstructions", "") or service.get(
                "http://www.eclaimlink.ae/DHD/ValidationSchema:ActivityInstructions", ""
            )
            diagnosis_code = service.get("ct:DiagnosisCode", "") or service.get(
                "http://www.eclaimlink.ae/DHD/ValidationSchema:DiagnosisCode", ""
            )
            amount_data = service.get("RequestedAmount", {})
            amount = (
                float(amount_data.get("#text", 0) or 0)
                if isinstance(amount_data, dict)
                else float(amount_data or 0)
            )
            services.append(
                {
                    "code": activity_code,
                    "description": instructions,
                    "diagnosis_code": diagnosis_code,
                    "amount": amount,
                }
            )
            total_cost += amount

        patient_info["services"] = services
        patient_info["total_cost"] = total_cost
        patient_info["justification"] = xml_dict.get("JustificationText")
        patient_info.update(patient_data)

    elif xml_format == "shafafiya":
        patient_info = {
            "EmiratesIDNumber": None,
            "services": [],
            "total_cost": 0.0,
            "justification": None,
        }

    return patient_info


def determine_specialty(xml_data: Dict[str, Any], patient_data: Dict[str, Any]) -> str:
    """
    Determine medical specialty from XML and patient data using simple rule-based logic.
    Returns a lowercase/snake-case label (e.g., 'diabetes', 'cardiac', 'general').
    """
    try:
        demographics = patient_data.get("demographics", {}) or {}
        dob_str = demographics.get("date_of_birth", "") or demographics.get("dob", "")
        age = demographics.get("age")
        if age is None and dob_str:
            try:
                dob = _dt.datetime.strptime(dob_str, "%d/%m/%Y")
                today = _dt.datetime.now()
                age = (
                    today.year
                    - dob.year
                    - ((today.month, today.day) < (dob.month, dob.day))
                )
            except Exception:
                age = None

        xml_dict = xml_data.get("as_dict", {}) or {}
        service_requests = xml_dict.get("ServiceRequests", {}).get("ServiceRequest", [])
        if isinstance(service_requests, dict):
            service_requests = [service_requests]
        notes = xml_dict.get("JustificationText", "")

        labs_list = patient_data.get("labs") or []
        medications_list = patient_data.get("medications") or []
        claims_list = patient_data.get("claims") or []
        preauth_history_list = patient_data.get("preauth_history") or []
        fhir_bundle_present = bool(patient_data.get("fhir_bundle"))

        payload = f"""
        Patient Info: {demographics}
        Age: {age}
        Services: {service_requests}
        Notes: {notes}
        Labs: {labs_list}
        Medications: {medications_list}
        Claims: {claims_list}
        Preauth History: {preauth_history_list}
        FHIR Bundle Present: {fhir_bundle_present}
        """
        logger.info(f"Determine Specialty payload: {payload}")

        payload_lower = payload.lower()
        if any(
            word in payload_lower
            for word in ["diabetes", "insulin", "glucose", "diabetic"]
        ):
            return "diabetes"
        if any(
            word in payload_lower
            for word in ["heart", "cardiac", "cardiology", "chest pain"]
        ):
            return "cardiac"
        if any(
            word in payload_lower
            for word in ["lung", "respiratory", "asthma", "copd", "breathing"]
        ):
            return "respiratory"
        if any(
            word in payload_lower
            for word in ["cancer", "oncology", "tumor", "chemotherapy"]
        ):
            return "oncology"
        if any(
            word in payload_lower
            for word in ["bone", "orthopedic", "joint", "fracture", "surgery"]
        ):
            return "orthopedic"
        if any(
            word in payload_lower
            for word in ["kidney", "nephrology", "dialysis", "renal"]
        ):
            return "nephrology"
        if any(
            word in payload_lower for word in ["skin", "dermatology", "rash", "acne"]
        ):
            return "dermatology"
        if any(
            word in payload_lower
            for word in ["brain", "neurology", "seizure", "stroke", "neurologic"]
        ):
            return "neurology"
        if any(
            word in payload_lower
            for word in ["mental", "psychiatry", "depression", "anxiety"]
        ):
            return "mental_health"
        if age and age < 18:
            return "pediatric"
        return "general"
    except Exception:
        return "general"


def prepare_agent_execution_context(unified_record) -> Dict[str, Any]:
    """Prepare comprehensive context for agent execution from unified record."""
    recent_observations = unified_record.clinical_timeline
    total_cost = sum(
        service.get("amount", 0) for service in unified_record.requested_services
    )

    primary_providers = [
        {
            "name": provider.get("name", [{}])[0].get("given", [""])[0]
            + " "
            + provider.get("name", [{}])[0].get("family", ""),
            "qualification": provider.get("qualification", [{}])[0]
            .get("code", {})
            .get("coding", [{}])[0]
            .get("display", ""),
            "identifier": provider.get("identifier", [{}])[0].get("value", ""),
        }
        for provider in unified_record.care_team[:2]
    ]

    insurance_coverage = {
        "primary_coverage": unified_record.coverage_details[0]
        if unified_record.coverage_details
        else {},
        "coverage_summary": {
            "total_plans": len(unified_record.coverage_details),
            "active_coverage": len(
                [
                    c
                    for c in unified_record.coverage_details
                    if c.get("status") == "active"
                ]
            ),
        },
    }

    clinical_assessments = [
        {
            "questionnaire_id": resp.get("questionnaire", ""),
            "completion_date": resp.get("authored", ""),
            "key_responses": [
                item.get("answer", [{}])[0].get("valueString", "")[:200]
                for item in resp.get("item", [])[:3]
            ],
        }
        for resp in unified_record.questionnaire_responses
    ]

    return {
        "patient_profile": unified_record.current_demographics,
        "insurance_context": unified_record.current_insurance,
        "recent_observations": recent_observations,
        "current_medications": unified_record.medication_regimen,
        "relevant_conditions": unified_record.clinical_conditions,
        "historical_care_episodes": unified_record.care_episodes,
        "coverage_details": insurance_coverage,
        "care_team": primary_providers,
        "clinical_assessments": clinical_assessments,
        "services_requested": unified_record.requested_services,
        "clinical_justification": unified_record.clinical_justification,
        "total_requested_cost": total_cost,
        "risk_assessment": unified_record.risk_assessment,
        "data_quality_assessment": unified_record.data_quality_assessment,
        "specialty_focus": unified_record.specialty_context,
        "processing_mode": "hybrid",
        "analysis_timestamp": unified_record.processing_timestamp,
        "data_sources": unified_record.data_sources,
    }


def assess_clinical_risk_llm(
    timeline: List[Dict[str, Any]],
    medications: List[Dict[str, Any]],
    demographics: Dict[str, Any],
) -> Dict[str, Any]:
    """Rule-based clinical risk assessment (kept simple)."""
    risk_factors: List[str] = []
    high_risk_medications = ["warfarin", "insulin", "chemotherapy", "immunosuppressant"]

    age = demographics.get("age", 0)
    if age > 65:
        risk_factors.append("Advanced age (>65)")
    elif age and age < 18:
        risk_factors.append("Pediatric patient")

    for med in medications:
        med_name = med.get("medication_name", "").lower()
        if any(h in med_name for h in high_risk_medications):
            risk_factors.append(
                f"High-risk medication: {med.get('medication_name', '')}"
            )

    for obs in timeline[:10]:
        if "critical" in (obs.get("abnormal_flag", "").lower()):
            risk_factors.append(
                f"Critical lab result: {obs.get('test_name', '').lower()}"
            )

    if len(risk_factors) >= 3:
        overall_risk, confidence = "HIGH", 0.8
    elif len(risk_factors) >= 1:
        overall_risk, confidence = "MODERATE", 0.7
    else:
        overall_risk, confidence = "LOW", 0.75

    return {
        "overall_risk": overall_risk,
        "risk_factors": risk_factors,
        "confidence": confidence,
        "reasoning": "Rule-based assessment based on age, medications, and clinical observations",
    }


def calculate_data_quality_llm(
    demographics: Dict[str, Any],
    timeline: List[Dict[str, Any]],
    medications: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Rule-based data quality assessment."""
    demographics_completeness = check_demographics_completeness(demographics)
    completeness_score = demographics_completeness["required_completeness"]

    richness_factors: List[float] = []
    if len(timeline) > 5:
        richness_factors.append(0.4)
    elif len(timeline) > 0:
        richness_factors.append(0.2)
    if len(medications) > 0:
        richness_factors.append(0.3)
    if demographics.get("age") and demographics.get("gender"):
        richness_factors.append(0.3)

    richness_score = sum(richness_factors)
    accuracy_score = 0.9
    overall_score = (
        completeness_score * 0.4 + richness_score * 0.4 + accuracy_score * 0.2
    )

    recommendations: List[str] = []
    if completeness_score < 0.8:
        recommendations.append("Complete missing demographic information")
    if len(timeline) < 3:
        recommendations.append("Request additional clinical history")
    if len(medications) == 0:
        recommendations.append("Verify current medication status")

    return {
        "overall_score": round(overall_score, 2),
        "completeness_score": round(completeness_score, 2),
        "richness_score": round(richness_score, 2),
        "accuracy_score": accuracy_score,
        "recommendations": recommendations,
        "reasoning": "Rule-based assessment of data completeness, richness, and accuracy",
    }


def check_demographics_completeness(demographics: Dict[str, Any]) -> Dict[str, Any]:
    """Check completeness of demographic data."""
    required_fields = [
        "emirates_id",
        "first_name",
        "last_name",
        "date_of_birth",
        "gender",
    ]
    optional_fields = ["phone", "email", "address"]

    required_complete = sum(1 for field in required_fields if demographics.get(field))
    optional_complete = sum(1 for field in optional_fields if demographics.get(field))

    return {
        "required_completeness": required_complete / len(required_fields),
        "optional_completeness": optional_complete / len(optional_fields),
        "missing_required": [
            field for field in required_fields if not demographics.get(field)
        ],
        "missing_optional": [
            field for field in optional_fields if not demographics.get(field)
        ],
    }
