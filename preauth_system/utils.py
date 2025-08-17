"""
Utility functions for the Pre-Authorization system.
"""

import json
from pathlib import Path
from typing import Dict, Any, List
import xmltodict  # type: ignore
import yaml  # type: ignore
from loguru import logger
import dspy

import os
from contextlib import contextmanager
from typing import Optional

try:
    from dspy.adapters.baml_adapter import BAMLAdapter  # type: ignore
except Exception:  # pragma: no cover
    BAMLAdapter = None  # type: ignore

from preauth_system.signatures import (
    ClinicalRiskSignature,
    SpecialtyDeterminationSignature,
    DataQualitySignature
)


def get_config() -> Dict[str, Any]:
    """Load configuration exclusively from preauth_system/config.yaml."""
    cfg_path = Path(__file__).parent / "config.yaml"
    if not (yaml and cfg_path.exists()):
        return {}
    try:
        return yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


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

    # Hardened: handle namespaced root keys gracefully
    if xml_format == "eclaim":
        if "PriorAuthorizationRequest" in xml_dict:
            xml_dict = xml_dict["PriorAuthorizationRequest"]
        else:
            # Fallback: find a key that endswith PriorAuthorizationRequest
            root_key = next(
                (k for k in xml_dict.keys() if str(k).split(":")[-1] == "PriorAuthorizationRequest"),
                None,
            )
            if root_key and xml_dict.get(root_key):
                xml_dict = xml_dict[root_key]
            else:
                # If structure unexpectedly nested, take first dict child
                first_val = next((v for v in xml_dict.values() if isinstance(v, dict)), {})
                xml_dict = first_val or {}
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
        xml_dict = xml_data.get("as_dict", {}) or {}
        # Handle namespaced key variants for Patient
        patient_data = (
            xml_dict.get("Patient")
            or next(
                (
                    v
                    for k, v in xml_dict.items()
                    if isinstance(v, dict) and str(k).split(":")[-1] == "Patient"
                ),
                {},
            )
            or {}
        )

        # Extract Emirates ID safely
        patient_info["EmiratesIDNumber"] = patient_data.get("EmiratesIDNumber") or patient_data.get(
            "http://www.eclaimlink.ae/DHD/ValidationSchema:EmiratesIDNumber"
        )

        # Extract services from ServiceRequests
        sr_container = xml_dict.get("ServiceRequests") or next(
            (
                v
                for k, v in xml_dict.items()
                if isinstance(v, dict) and str(k).split(":")[-1] == "ServiceRequests"
            ),
            {},
        )
        service_requests = sr_container.get("ServiceRequest", [])
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
        # Try namespaced justification as fallback
        patient_info["justification"] = xml_dict.get("JustificationText") or xml_dict.get(
            "http://www.eclaimlink.ae/DHD/ValidationSchema:JustificationText"
        )
        # Merge basic patient fields, keeping existing keys
        for k, v in (patient_data or {}).items():
            patient_info.setdefault(k, v)

    elif xml_format == "shafafiya":
        patient_info = {
            "EmiratesIDNumber": None,
            "services": [],
            "total_cost": 0.0,
            "justification": None,
        }

    return patient_info


def prepare_pipeline_patient_data(unified_record) -> Dict[str, Any]:
    """Map UnifiedPatientRecord to the `signatures.PatientData` structure.

    Returns a dict with keys: patient_demographics, medical_history,
    clinical_data, requested_treatment.
    """
    # Patient demographics
    demographics = unified_record.current_demographics or {}

    # Medical history (high level)
    medical_history: Dict[str, Any] = {
        "conditions": unified_record.clinical_conditions or [],
        "care_episodes": unified_record.care_episodes or [],
        "questionnaires": unified_record.questionnaire_responses or [],
    }

    # Clinical data snapshot
    clinical_data: Dict[str, Any] = {
        "timeline": unified_record.clinical_timeline or [],
        "medications": unified_record.medication_regimen or [],
        "risk_assessment": unified_record.risk_assessment or {},
        "data_quality": unified_record.data_quality_assessment or {},
    }

    # Requested treatment info
    requested_treatment: Dict[str, Any] = {
        "services": unified_record.requested_services or [],
        "justification": unified_record.clinical_justification or "",
        "specialty": unified_record.specialty_context or "general",
        "total_cost": sum(s.get("amount", 0) for s in (unified_record.requested_services or [])),
    }

    return {
        "patient_demographics": demographics,
        "medical_history": medical_history,
        "clinical_data": clinical_data,
        "requested_treatment": requested_treatment,
    }


def determine_specialty(xml_data: Dict[str, Any], patient_data: Dict[str, Any]) -> str:
    """Determine specialty using DSPy SpecialtyDetermination with fallback heuristic."""
    try:
        # Prepare requested services from XML for the LLM
        xml_dict = (xml_data or {}).get("as_dict", {}) or {}
        service_reqs = xml_dict.get("ServiceRequests", {}).get("ServiceRequest", [])
        if isinstance(service_reqs, dict):
            service_reqs = [service_reqs]

        lm = get_module_lm("specialty_determination")
        specialty_determiner = dspy.ChainOfThought(SpecialtyDeterminationSignature)
        with with_dspy_lm(lm):
            res = specialty_determiner(patient_data=patient_data or {}, requested_services=service_reqs)
        # Module returns a string or an object depending on implementation
        if isinstance(res, str):
            return res
        specialty = getattr(res, "specialty", None)
        if isinstance(specialty, str):
            return specialty
        if specialty and hasattr(specialty, "specialty"):
            return getattr(specialty, "specialty") or "general"
    except Exception as e:
        logger.warning(f"SpecialtyDetermination LLM unavailable, using fallback: {e}")

    # Fallback heuristic based on justification text keywords
    notes = ((xml_data or {}).get("as_dict", {}) or {}).get("JustificationText", "")
    text = f"{notes} {json.dumps(patient_data or {}, ensure_ascii=False)}".lower()
    if any(k in text for k in ["diabetes", "insulin", "glucose", "diabetic"]):
        return "diabetes"
    if any(k in text for k in ["cardiac", "cardiology", "heart"]):
        return "cardiac"
    if any(k in text for k in ["asthma", "lung", "respiratory", "copd"]):
        return "respiratory"
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
    """Clinical risk assessment via DSPy LLM with graceful fallback."""
    try:

        lm = get_module_lm("clinical_risk")
        assess = dspy.ChainOfThought(ClinicalRiskSignature)
        with with_dspy_lm(lm):
            result = assess(
                timeline=timeline, medications=medications, demographics=demographics
            )
        out = getattr(result, "clinical_risk", None)
        if out:
            return {
                "overall_risk": out.overall_risk,
                "risk_factors": out.risk_factors or [],
                "confidence": out.confidence,
                "reasoning": out.reasoning,
            }
    except Exception as e:
        logger.warning(f"ClinicalRisk LLM unavailable, using fallback: {e}")
    # Fallback: simple heuristic
    risk_factors: List[str] = []
    age = demographics.get("age", 0)
    if age and age > 65:
        risk_factors.append("Advanced age (>65)")
    if any(
        "critical" in (obs.get("abnormal_flag", "").lower()) for obs in timeline[:10]
    ):
        risk_factors.append("Recent critical lab results")
    overall_risk = (
        "HIGH" if len(risk_factors) >= 2 else ("MODERATE" if risk_factors else "LOW")
    )
    return {
        "overall_risk": overall_risk,
        "risk_factors": risk_factors,
        "confidence": 0.7,
        "reasoning": "Fallback heuristic",
    }


def calculate_data_quality_llm(
    demographics: Dict[str, Any],
    timeline: List[Dict[str, Any]],
    medications: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Data quality assessment via DSPy LLM with graceful fallback."""
    try:
        lm = get_module_lm("data_quality")
        assess = dspy.ChainOfThought(DataQualitySignature)
        with with_dspy_lm(lm):
            result = assess(
            demographics=demographics, timeline=timeline, medications=medications
        )
        out = getattr(result, "data_quality", None)
        if out:
            return {
                "overall_score": out.overall_score,
                "completeness_score": out.completeness_score,
                "richness_score": out.richness_score,
                "accuracy_score": out.accuracy_score,
                "recommendations": out.recommendations or [],
                "reasoning": out.reasoning,
            }
    except Exception as e:
        logger.warning(f"DataQuality LLM unavailable, using fallback: {e}")
    # Fallback: simple heuristic
    completeness = check_demographics_completeness(demographics).get(
        "required_completeness", 0.5
    )
    richness = (0.4 if len(timeline) > 5 else (0.2 if len(timeline) > 0 else 0.0)) + (
        0.3 if medications else 0.0
    )
    accuracy = 0.9
    overall = completeness * 0.4 + richness * 0.4 + accuracy * 0.2
    recs: List[str] = []
    if completeness < 0.8:
        recs.append("Complete missing demographic information")
    if len(timeline) < 3:
        recs.append("Request additional clinical history")
    if not medications:
        recs.append("Verify current medication status")
    return {
        "overall_score": round(overall, 2),
        "completeness_score": round(completeness, 2),
        "richness_score": round(richness, 2),
        "accuracy_score": accuracy,
        "recommendations": recs,
        "reasoning": "Fallback heuristic",
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


def _resolve_model_name(
    agent_name: Optional[str] = None, module_name: Optional[str] = None
) -> str:
    cfg = get_config() or {}
    llm_cfg = cfg.get("llm") or {}
    # New preferred default
    default_model = (
        llm_cfg.get("default_model")
        or llm_cfg.get("model")
        or "openrouter/openai/gpt-oss-20b"
    )
    # Agent override
    if agent_name:
        agent_entry = (llm_cfg.get("agents") or {}).get(agent_name) or {}
        if agent_entry.get("model"):
            return agent_entry["model"]
    # Module override
    if module_name:
        module_entry = (llm_cfg.get("modules") or {}).get(module_name) or {}
        if module_entry.get("model"):
            return module_entry["model"]
    return default_model


def get_openrouter_lm(
    model: str | None = None,
    cache: bool = True,
    *,
    agent_name: Optional[str] = None,
    module_name: Optional[str] = None,
) -> dspy.LM:
    """Get OpenRouter LM instance based on central config or override.
    Resolution order: explicit model arg > per-agent > per-module > default.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY environment variable required")

    model_name = model or _resolve_model_name(
        agent_name=agent_name, module_name=module_name
    )

    return dspy.LM(
        model=model_name,
        api_key=api_key,
        cache=cache,
    )


def configure_dspy_default():
    """Configure DSPy with a default LM read from config.yaml.
    Use sparingly; prefer per-call scoping with with_dspy_lm().
    """
    try:
        lm = get_openrouter_lm()
        if BAMLAdapter is not None:
            dspy.configure(lm=lm, adapter=BAMLAdapter())
        else:
            dspy.configure(lm=lm)
    except Exception:
        # Last resort - no global config
        pass


@contextmanager
def with_dspy_lm(lm: dspy.LM):
    """Context manager to scope dspy.configure to a specific LM without global side effects."""
    try:
        if BAMLAdapter is not None:
            dspy.configure(lm=lm, adapter=BAMLAdapter())
        else:
            dspy.configure(lm=lm)
        yield
    finally:
        pass


# Convenience helpers


def get_agent_lm(agent_name: str, cache: bool = True) -> dspy.LM:
    return get_openrouter_lm(cache=cache, agent_name=agent_name)


def get_module_lm(module_name: str, cache: bool = True) -> dspy.LM:
    return get_openrouter_lm(cache=cache, module_name=module_name)
