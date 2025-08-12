"""
Utility functions for the Pre-Authorization system.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import xmltodict  # type: ignore

from preauth_system.state import AgentResult, SharedContext
import yaml  # type: ignore
from baml_client import b

import datetime as _dt
import re as _re
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

# Module-level cache for agent definitions to avoid re-loading on every agent run
_AGENT_DEFINITIONS_CACHE: Optional[Dict[str, Dict[str, Any]]] = None


def get_cached_agent_definitions() -> Optional[Dict[str, Dict[str, Any]]]:
    """Return cached agent definitions if they have been loaded."""
    return _AGENT_DEFINITIONS_CACHE


def prime_agent_definitions_cache() -> Dict[str, Dict[str, Any]]:
    """
    Load agent definitions and store them in a module-level cache.
    Subsequent calls to execute agents will reuse this cache.
    """
    global _AGENT_DEFINITIONS_CACHE
    if _AGENT_DEFINITIONS_CACHE is None:
        _AGENT_DEFINITIONS_CACHE = load_agent_definitions()
    return _AGENT_DEFINITIONS_CACHE


def load_agent_definitions() -> Dict[str, Dict[str, Any]]:
    """
    Load agent definitions from markdown files.

    Returns:
        Dict mapping agent names to their parsed definitions

    Raises:
        Exception: If any required agent definition file is missing
    """
    # Return cached definitions if already loaded
    global _AGENT_DEFINITIONS_CACHE
    if _AGENT_DEFINITIONS_CACHE is not None:
        return _AGENT_DEFINITIONS_CACHE

    base_path = Path(__file__).parent
    agents_dir = base_path / "agents"

    # Create agents directory if it doesn't exist
    agents_dir.mkdir(exist_ok=True)

    # Agent names from original orchestrator
    agent_names = [
        "clinical-analyzer",
        "medication-specialist",
        "risk-assessor",
        "decision-maker",
        "compliance-auditor",
    ]

    agent_definitions = {}

    for agent_name in agent_names:
        agent_file = agents_dir / f"{agent_name}.md"

        if agent_file.exists():
            try:
                with open(agent_file, "r", encoding="utf-8") as f:
                    content = f.read()

                agent_definitions[agent_name] = _parse_agent_definition(content)
                print(f"✅ Loaded {agent_name} definition from {agent_file}")

            except Exception as e:
                print(f"❌ Failed to load {agent_name} definition: {e}")
                raise Exception(f"Failed to load {agent_name} definition: {e}")
        else:
            print(f"⚠️ No .md file found for {agent_name}")
            raise Exception(f"No agent definition markdown file found for {agent_name}")

    # Store in cache for subsequent calls
    _AGENT_DEFINITIONS_CACHE = agent_definitions
    return agent_definitions


def _parse_agent_definition(content: str) -> Dict[str, Any]:
    """
    Parse agent definition from markdown content.

    Args:
        content: Raw markdown content from agent definition file

    Returns:
        Dict containing parsed agent definition

    Raises:
        ValueError: If required frontmatter fields are missing
    """
    lines = content.split("\n")
    definition = {
        "name": "",
        "description": "",
        "instructions": "",
        "tools": [],
        "model": None,
        "reasoning_effort": None,
    }

    # Extract frontmatter if present
    if lines and lines[0].strip() == "---":
        frontmatter_end = -1
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == "---":
                frontmatter_end = i + 1
                break

        if frontmatter_end > 0:
            for line in lines[1 : frontmatter_end - 1]:
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip()

                    if key == "name":
                        definition["name"] = value
                    elif key == "description":
                        definition["description"] = value
                    elif key == "tools":
                        if value.startswith("[") and value.endswith("]"):
                            tools_str = value[1:-1]
                            definition["tools"] = [
                                t.strip() for t in tools_str.split(",") if t.strip()
                            ]
                    elif key == "model":
                        definition["model"] = value or None
                    elif key == "reasoning_effort":
                        # normalize to lower-case token expected by OpenAI Agents SDK
                        definition["reasoning_effort"] = (
                            value or ""
                        ).strip().lower() or None

            content_lines = lines[frontmatter_end:]
        else:
            content_lines = lines
    else:
        content_lines = lines

    definition["instructions"] = "\n".join(content_lines).strip()

    # Ensure required fields
    if not definition["tools"]:
        raise ValueError("Agent definition is missing 'tools' list in frontmatter.")

    return definition


def parse_xml(xml_file_path: str, xml_format: str) -> Dict[str, Any]:
    """
    Parse XML file and determine format.

    Args:
        xml_file_path: Path to the XML file to parse
        xml_format: Expected XML format ('eclaim' or 'shafafiya')

    Returns:
        Dict containing parsed XML data

    Raises:
        ValueError: If XML format is not recognized
        Exception: If xmltodict is not available or parsing fails
    """
    # Parse full XML content into dictionary when xmltodict is available
    xml_dict: Optional[Dict[str, Any]] = None
    with open(xml_file_path, "r", encoding="utf-8") as f:
        xml_content = f.read()
    try:
        xml_dict = xmltodict.parse(xml_content, process_namespaces=True)
    except Exception as ex:
        print(f"⚠️ xmltodict failed to parse XML: {ex}")
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
    """
    Extract patient info from XML.

    Args:
        xml_data: Parsed XML data dictionary
        xml_format: XML format type ('eclaim' or 'shafafiya')

    Returns:
        Dict containing extracted patient information with required fields:
        - EmiratesIDNumber, services, total_cost, justification
    """
    patient_info = {}

    if xml_format == "eclaim":
        xml_dict = xml_data.get("as_dict", {})
        patient_data = xml_dict.get("Patient", {})

        # Extract Emirates ID
        patient_info["EmiratesIDNumber"] = patient_data.get("EmiratesIDNumber")

        # Extract services from ServiceRequests
        service_requests = xml_dict.get("ServiceRequests", {}).get("ServiceRequest", [])
        if isinstance(service_requests, dict):
            service_requests = [service_requests]  # Single service case

        services = []
        total_cost = 0.0

        for service in service_requests:
            # Handle namespace-expanded keys
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
            if isinstance(amount_data, dict):
                amount = float(amount_data.get("#text", 0) or 0)
            else:
                amount = float(amount_data or 0)

            service_info = {
                "code": activity_code,
                "description": instructions,
                "diagnosis_code": diagnosis_code,
                "amount": amount,
            }
            services.append(service_info)
            total_cost += service_info["amount"]

        patient_info["services"] = services
        patient_info["total_cost"] = total_cost

        # Extract justification text
        patient_info["justification"] = xml_dict.get("JustificationText")

        # Add other patient demographics for compatibility
        patient_info.update(patient_data)

    elif xml_format == "shafafiya":
        # Add Shafafiya parsing logic when needed
        patient_info = {
            "EmiratesIDNumber": None,
            "services": [],
            "total_cost": 0.0,
            "justification": None,
        }

    return patient_info


def determine_specialty(xml_data: Dict[str, Any], patient_data: Dict[str, Any]) -> str:
    """
    Determine medical specialty from XML and patient data using LLM.

    Returns a lowercase/snake-case label consistent with prior behavior.
    """
    try:
        demographics = patient_data.get("demographics", {}) or {}
        dob_str = demographics.get("date_of_birth", "") or demographics.get("dob", "")
        age = demographics.get("age")

        # Compute age from DOB if not provided (expected format: DD/MM/YYYY)
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

        # Use passed XML dict structure directly (no parsing here)
        xml_dict = xml_data.get("as_dict", {}) or {}
        service_requests = xml_dict.get("ServiceRequests", {}).get("ServiceRequest", [])
        if isinstance(service_requests, dict):
            service_requests = [service_requests]

        # Optional notes/justification straight from XML dict
        notes = xml_dict.get("JustificationText", "")

        # Summaries from patient_data keys
        labs_list = patient_data.get("labs") or []
        medications_list = patient_data.get("medications") or []
        claims_list = patient_data.get("claims") or []
        preauth_history_list = patient_data.get("preauth_history") or []
        fhir_bundle_present = bool(patient_data.get("fhir_bundle"))

        # put all the data into a string
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

        # Call BAML function
        result = b.DetermineSpecialty(payload)
        logger.info(f"Determine Specialty result: {result}")

        # Normalize Enum value to string label
        specialty_enum = getattr(result, "specialty", None)
        label = getattr(
            specialty_enum,
            "value",
            str(specialty_enum) if specialty_enum is not None else "",
        )
        if not label:
            return "general"

        # Convert CamelCase to snake_case then lowercase
        snake = _re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", label).lower()
        return snake

    except Exception:
        # Conservative fallback if the LLM call fails
        return "general"


# Simple JSONL trace writer
class _TraceWriter:
    def __init__(self, run_id: str):
        traces_dir = Path(_CFG["tracing"]["dir"]).resolve()
        traces_dir.mkdir(parents=True, exist_ok=True)
        self.path = traces_dir / f"{run_id}.jsonl"

    def write(self, event_type: str, **payload: Any) -> None:
        record = {
            "ts": datetime.utcnow().isoformat(),
            "event": event_type,
            **payload,
        }
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


# Claude executor removed; execution handled in preauth_system/agents_openai.py


def _build_agent_prompt(
    agent_name: str,
    agent_def: Dict[str, Any],
    shared_context: SharedContext,
    previous_results: Dict[str, AgentResult],
) -> str:
    """
    Build the prompt for the agent execution.

    Args:
        agent_name: Name of the agent
        agent_def: Agent definition with instructions
        shared_context: Patient and request context
        previous_results: Results from dependent agents

    Returns:
        Complete prompt string for agent execution
    """
    agent_instructions = agent_def.get("instructions", "")

    # Get relevant previous results based on dependencies
    dependencies = _get_agent_dependencies(agent_name)
    relevant_results = {
        dep: previous_results[dep].get("response", "Not available")
        for dep in dependencies
        if dep in previous_results
    }

    # Construct final prompt
    prompt_parts = [agent_instructions.strip()]

    # Attach patient/request context
    prompt_parts.append(
        "\n\n## PATIENT DATA CONTEXT\n" + json.dumps(shared_context, indent=2)
    )

    # Attach previous agent analyses if any
    if relevant_results:
        prompt_parts.append(
            "\n\n## PREVIOUS AGENT ANALYSES\n" + json.dumps(relevant_results, indent=2)
        )

    return "\n".join(prompt_parts)


def _get_agent_dependencies(agent_name: str) -> List[str]:
    """
    Get dependencies for a specific agent.

    Args:
        agent_name: Name of the agent

    Returns:
        List of agent names this agent depends on
    """
    dependencies_map = {
        "clinical-analyzer": [],
        "medication-specialist": [],
        "risk-assessor": ["clinical-analyzer", "medication-specialist"],
        "decision-maker": [
            "clinical-analyzer",
            "medication-specialist",
            "risk-assessor",
        ],
        "compliance-auditor": ["decision-maker"],
    }

    return dependencies_map.get(agent_name, [])


def make_final_decision(
    agent_results: Dict[str, AgentResult],
    xml_data: Dict[str, Any],
    patient_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Make final decision based on agent analyses.

    Args:
        agent_results: Results from all executed agents
        xml_data: Original XML request data
        patient_data: Patient medical history

    Returns:
        Dict containing final authorization decision

    Raises:
        Exception: If decision-maker agent failed
    """
    # Get decision maker result if available
    decision_agent = agent_results.get("decision-maker")

    if decision_agent and decision_agent.get("success"):
        # Extract decision from agent response
        response = decision_agent.get("response", "")

        # Simple keyword extraction for decision
        if "approved" in response.lower() and "not" not in response.lower():
            decision = "APPROVED"
            confidence = 0.85
        elif "denied" in response.lower() or "reject" in response.lower():
            decision = "DENIED"
            confidence = 0.80
        else:
            decision = "REQUIRES_REVIEW"
            confidence = 0.60
    else:
        error_msg = (
            decision_agent.get("error", "Unknown error")
            if decision_agent
            else "Decision maker not executed"
        )
        print(f"❌ Decision maker failed: {error_msg}")
        raise Exception(f"Decision maker failed: {error_msg}")

    # Generate authorization number based on file path hash
    file_path = xml_data.get("file_path", "default")
    auth_number = f"AUTH-2025-{datetime.now().strftime('%Y%m%d')}-{abs(hash(file_path)) % 10000:04d}"

    return {
        "decision": decision,
        "confidence": confidence,
        "authorization_number": auth_number,
        "valid_days": 90,
        "conditions": ["Standard monitoring", "Follow-up required"],
        "rationale": "Based on comprehensive agent analysis including clinical review, medication assessment, and risk stratification.",
        "agent_based": decision_agent.get("success", False)
        if decision_agent
        else False,
    }


def calculate_egfr(
    creatinine_mg_dl: float, age_years: int, gender: str, race: str = "other"
) -> float:
    """
    Calculate estimated Glomerular Filtration Rate (eGFR) using CKD-EPI equation.

    Args:
        creatinine_mg_dl: Serum creatinine in mg/dL
        age_years: Age in years
        gender: 'M' for male, 'F' for female
        race: 'black' or 'other' (default)

    Returns:
        eGFR value in mL/min/1.73m²
    """
    if creatinine_mg_dl <= 0:
        return 0.0

    # CKD-EPI equation constants
    if gender.upper() == "F":  # Female
        if creatinine_mg_dl <= 0.7:
            egfr = 144 * ((creatinine_mg_dl / 0.7) ** -0.329) * (0.993**age_years)
        else:
            egfr = 144 * ((creatinine_mg_dl / 0.7) ** -1.209) * (0.993**age_years)
    else:  # Male
        if creatinine_mg_dl <= 0.9:
            egfr = 141 * ((creatinine_mg_dl / 0.9) ** -0.411) * (0.993**age_years)
        else:
            egfr = 141 * ((creatinine_mg_dl / 0.9) ** -1.209) * (0.993**age_years)

    # Race factor
    if race.lower() == "black":
        egfr *= 1.159

    return round(egfr, 1)


def get_latest_creatinine(patient_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Get the most recent creatinine lab result from patient data.

    Args:
        patient_data: Patient data from ETL system

    Returns:
        Dict with latest creatinine info or None if not found
    """
    labs = patient_data.get("labs", [])
    creatinine_labs = [
        lab for lab in labs if "creatinine" in lab.get("test_name", "").lower()
    ]

    if not creatinine_labs:
        return None

    # Sort by test_date and get the most recent
    creatinine_labs.sort(key=lambda x: x.get("test_date", ""), reverse=True)
    latest = creatinine_labs[0]

    return {
        "value": float(latest.get("result_value", 0)),
        "unit": latest.get("unit", "mg/dL"),
        "date": latest.get("test_date"),
        "reference_range": latest.get("reference_range", ""),
        "abnormal_flag": latest.get("abnormal_flag", "N"),
    }


# Unified data model functions moved from data_ingestion/unified_data.py


def prepare_agent_execution_context(unified_record) -> Dict[str, Any]:
    """
    Prepare comprehensive context for agent execution using all available
    UnifiedPatientRecord data including new FHIR resources.

    Replaces the previous SharedContext which had overlapping data
    from multiple sources. This provides clean, non-duplicated context.

    Args:
        unified_record: UnifiedPatientRecord instance

    Returns:
        AgentExecutionContext dict with no data duplication
    """

    # Get recent clinical observations (last 5)
    recent_observations = unified_record.clinical_timeline

    # Calculate total requested cost
    total_cost = sum(
        service.get("amount", 0) for service in unified_record.requested_services
    )

    # Extract care team information
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
        for provider in unified_record.care_team[:2]  # Top 2 providers
    ]

    # Extract coverage information
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

    # Extract questionnaire responses for clinical insights
    clinical_assessments = [
        {
            "questionnaire_id": resp.get("questionnaire", ""),
            "completion_date": resp.get("authored", ""),
            "key_responses": [
                item.get("answer", [{}])[0].get("valueString", "")[
                    :200
                ]  # First 200 chars
                for item in resp.get("item", [])[:3]  # Top 3 responses
            ],
        }
        for resp in unified_record.questionnaire_responses
    ]

    return {
        # Patient profile (current from XML)
        "patient_profile": unified_record.current_demographics,
        "insurance_context": unified_record.current_insurance,
        # Clinical context (from FHIR Bundle)
        "recent_observations": recent_observations,
        "current_medications": unified_record.medication_regimen,
        "relevant_conditions": unified_record.clinical_conditions,
        "historical_care_episodes": unified_record.care_episodes,
        "coverage_details": insurance_coverage,
        "care_team": primary_providers,
        "clinical_assessments": clinical_assessments,
        # Request context (from XML)
        "services_requested": unified_record.requested_services,
        "clinical_justification": unified_record.clinical_justification,
        "total_requested_cost": total_cost,
        # LLM-derived insights (pre-computed for efficiency)
        "risk_assessment": unified_record.risk_assessment,
        "data_quality_assessment": unified_record.data_quality_assessment,
        # Processing context
        "specialty_focus": unified_record.specialty_context,
        "processing_mode": "hybrid",  # Can be configured
        "analysis_timestamp": unified_record.processing_timestamp,
        "data_sources": unified_record.data_sources,
    }


def assess_clinical_risk_llm(
    timeline: List[Dict[str, Any]],
    medications: List[Dict[str, Any]],
    demographics: Dict[str, Any],
) -> Dict[str, Any]:
    """
    LLM-based clinical risk assessment using BAML.
    """

    try:
        # Call BAML clinical risk assessment function
        risk_result = b.AssessClinicalRisk(
            demographics=str(demographics),
            recent_observations=str(timeline[:10]),  # Last 10 observations
            current_medications=str(medications),
            observation_count=len(timeline),
            medication_count=len(medications),
        )

        # Convert enum to string if needed
        overall_risk = (
            getattr(risk_result.overall_risk, "value", str(risk_result.overall_risk))
            if hasattr(risk_result, "overall_risk")
            else "MODERATE"
        )

        return {
            "overall_risk": overall_risk,
            "risk_factors": risk_result.risk_factors
            if hasattr(risk_result, "risk_factors")
            else [],
            "confidence": risk_result.confidence
            if hasattr(risk_result, "confidence")
            else 0.7,
            "reasoning": risk_result.reasoning
            if hasattr(risk_result, "reasoning")
            else "LLM-based assessment completed",
        }

    except Exception as e:
        # Fallback if LLM call fails
        return {
            "overall_risk": "UNKNOWN",
            "risk_factors": [f"Assessment failed: {str(e)}"],
            "confidence": 0.0,
            "reasoning": f"LLM assessment failed: {str(e)}",
        }


def calculate_data_quality_llm(
    demographics: Dict[str, Any],
    timeline: List[Dict[str, Any]],
    medications: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    LLM-based data quality assessment using BAML.
    """
    try:
        # Get demographics completeness analysis
        demographics_completeness = check_demographics_completeness(demographics)

        # Call BAML data quality assessment function
        quality_result = b.CalculateDataQuality(
            demographics_completeness=str(demographics_completeness),
            clinical_data_richness=len(timeline),
            medication_data_availability=len(medications),
            total_data_points=len(timeline)
            + len(medications)
            + len([d for d in demographics.values() if d]),
        )

        return {
            "overall_score": quality_result.overall_score
            if hasattr(quality_result, "overall_score")
            else 0.85,
            "completeness_score": quality_result.completeness_score
            if hasattr(quality_result, "completeness_score")
            else 0.9,
            "richness_score": quality_result.richness_score
            if hasattr(quality_result, "richness_score")
            else 0.8,
            "accuracy_score": quality_result.accuracy_score
            if hasattr(quality_result, "accuracy_score")
            else 0.85,
            "recommendations": quality_result.recommendations
            if hasattr(quality_result, "recommendations")
            else [],
            "reasoning": quality_result.reasoning
            if hasattr(quality_result, "reasoning")
            else "LLM-based assessment completed",
        }

    except Exception as e:
        # Fallback if LLM call fails
        return {
            "overall_score": 0.0,
            "completeness_score": 0.0,
            "richness_score": 0.0,
            "accuracy_score": 0.0,
            "recommendations": [f"Assessment failed: {str(e)}"],
            "reasoning": f"LLM assessment failed: {str(e)}",
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
