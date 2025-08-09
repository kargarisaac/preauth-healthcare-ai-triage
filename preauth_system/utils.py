"""
Utility functions for the Pre-Authorization system.
"""

import sys
import json
import asyncio
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import traceback
import uuid
import os
import xmltodict  # type: ignore

from claude_code_sdk import (
    query,
    ClaudeCodeOptions,
    AssistantMessage,
    TextBlock,
    ResultMessage,
)
from claude_code_sdk import ToolUseBlock, ToolResultBlock  # type: ignore
from preauth_system.state import AgentResult, SharedContext

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
    Determine medical specialty from XML and patient data.

    Args:
        xml_data: Parsed XML request data
        patient_data: Patient's complete medical history

    Returns:
        String indicating the primary medical specialty
    """
    import datetime

    # Get patient age
    dob_str = patient_data["demographics"].get("date_of_birth", "")
    patient_age = 30  # default

    if dob_str:
        try:
            dob = datetime.datetime.strptime(dob_str, "%d/%m/%Y")
            today = datetime.datetime.now()
            patient_age = (
                today.year
                - dob.year
                - ((today.month, today.day) < (dob.month, dob.day))
            )
        except:
            pass

    # Pediatric check
    if patient_age < 18:
        return "pediatric"

    # Check service descriptions for specialty keywords
    all_text = " ".join(
        [
            s.get("description", "") + " " + s.get("code", "")
            for s in xml_data.get("services", [])
        ]
    ).lower()

    specialty_keywords = {
        "diabetes": ["diabetes", "insulin", "hba1c", "glucose", "metformin"],
        "cardiac": ["cardiac", "heart", "cardio", "catheter", "troponin"],
        "respiratory": ["respiratory", "asthma", "copd", "lung", "breathing"],
        "oncology": ["cancer", "oncology", "tumor", "chemotherapy"],
        "orthopedic": ["orthopedic", "bone", "joint", "knee", "hip"],
        "nephrology": ["kidney", "renal", "dialysis", "creatinine"],
        "dermatology": ["skin", "dermatology", "psoriasis"],
        "neurology": ["neurological", "brain", "parkinson"],
        "mental_health": ["psychiatric", "depression", "anxiety"],
    }

    for specialty, keywords in specialty_keywords.items():
        if any(keyword in all_text for keyword in keywords):
            return specialty

    return "general"


def prepare_shared_context(
    xml_data: Dict[str, Any],
    patient_info: Dict[str, Any],
    patient_data: Dict[str, Any],
    specialty: str,
) -> SharedContext:
    """
    Prepare shared context for all agents.

    Args:
        xml_data: Parsed XML request data
        patient_info: Demographics and request specifics
        patient_data: Complete medical history from ETL
        specialty: Determined medical specialty

    Returns:
        SharedContext dict containing all relevant context data
    """
    return SharedContext(
        xml_request={
            "format": xml_data["format"],
            "file_path": xml_data["file_path"],
            "services_requested": patient_info["services"],
            "total_cost": patient_info["total_cost"],
            "raw_xml": xml_data.get("as_dict"),
            "justification_text": patient_info.get("justification"),
        },
        patient_demographics=patient_data["demographics"],
        medical_history={
            "lab_records": len(patient_data["labs"]),
            "medications": len(patient_data["medications"]),
            "claims_history": len(patient_data["claims"]),
            "preauth_history": len(patient_data["preauth_history"]),
        },
        clinical_data={
            "recent_labs": patient_data["labs"][-5:] if patient_data["labs"] else [],
            "current_medications": patient_data["medications"],
            "recent_claims": patient_data["claims"][-3:]
            if patient_data["claims"]
            else [],
        },
        specialty=specialty,
        analysis_timestamp=datetime.now().isoformat(),
    )


# Simple JSONL trace writer
class _TraceWriter:
    def __init__(self, run_id: str):
        traces_dir = Path("output") / "traces"
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


def execute_claude_agent(
    agent_name: str,
    shared_context: SharedContext,
    previous_results: Dict[str, AgentResult],
) -> AgentResult:
    """
    Execute a specific Claude Code agent.

    Args:
        agent_name: Name of the agent to execute
        shared_context: Patient and request data context
        previous_results: Results from previously executed agents

    Returns:
        AgentResult with execution details and response

    Raises:
        Exception: If Claude Code SDK is not available or agent execution fails
    """
    try:
        start_time = datetime.now()
        run_id = f"{agent_name}_{start_time.strftime('%Y%m%dT%H%M%S')}_{uuid.uuid4().hex[:6]}"
        tracer = _TraceWriter(run_id)

        # Load agent definitions (cached)
        agent_definitions = (
            get_cached_agent_definitions() or prime_agent_definitions_cache()
        )
        agent_def = agent_definitions.get(agent_name, {})

        if not agent_def:
            raise Exception(f"Agent definition not found for {agent_name}")

        # Build agent prompt
        prompt = _build_agent_prompt(
            agent_name, agent_def, shared_context, previous_results
        )

        # Configure Claude Code options
        agent_tools = agent_def.get("tools", [])
        if not agent_tools:
            raise Exception(f"No tools defined for agent {agent_name}")

        options = ClaudeCodeOptions(
            cwd=str(Path.cwd()),
            max_turns=15,
            allowed_tools=agent_tools,
        )

        tracer.write(
            "agent_started",
            agent=agent_name,
            allowed_tools=agent_tools,
            run_id=run_id,
        )

        # Execute agent synchronously using asyncio.run
        result = asyncio.run(_execute_agent_async(prompt, options, tracer, agent_name))

        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        tracer.write(
            "agent_finished",
            agent=agent_name,
            run_id=run_id,
            processing_time_seconds=processing_time,
            usage=result.get("usage", {}),
        )

        return AgentResult(
            agent_name=agent_name,
            status="completed",
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            processing_time_seconds=processing_time,
            response=result["response"],
            usage=result["usage"],
            success=True,
            error=None,
            traceback=None,
        )

    except Exception as e:
        return AgentResult(
            agent_name=agent_name,
            status="failed",
            start_time=start_time.isoformat() if "start_time" in locals() else None,
            end_time=datetime.now().isoformat(),
            processing_time_seconds=None,
            response=None,
            usage={},
            success=False,
            error=str(e),
            traceback=traceback.format_exc(),
        )


async def _execute_agent_async(
    prompt: str,
    options: ClaudeCodeOptions,
    tracer: Optional[_TraceWriter] = None,
    agent_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute agent asynchronously with Claude Code SDK.

    Args:
        prompt: Complete prompt for the agent
        options: Claude Code execution options
        tracer: Optional trace writer for step/tool logging
        agent_name: Optional agent name for trace enrichment

    Returns:
        Dict with response and usage data
    """
    text_responses = []
    usage_data = {}
    pending_tool_name: Optional[str] = None

    async for message in query(prompt=prompt, options=options):
        # Assistant text blocks
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    text_responses.append(block.text)
                    if tracer:
                        tracer.write(
                            "assistant_text",
                            agent=agent_name,
                            text_preview=block.text[:500],
                        )
                        # Heuristic: if a tool was just used and the next block is text, treat it as the tool result
                        if pending_tool_name:
                            parsed = None
                            try:
                                # Try to extract JSON payload from the block text
                                idx = block.text.find("{")
                                if idx != -1:
                                    parsed = json.loads(block.text[idx:])
                            except Exception:
                                parsed = None
                            tracer.write(
                                "tool_result",
                                agent=agent_name,
                                tool=pending_tool_name,
                                output_preview=block.text[:500],
                                parsed=parsed
                                if isinstance(parsed, (dict, list))
                                else None,
                            )
                            pending_tool_name = None
                # Tool use/result blocks if available in SDK
                if ToolUseBlock and isinstance(block, ToolUseBlock):  # type: ignore
                    pending_tool_name = getattr(block, "name", None)
                    if tracer:
                        tracer.write(
                            "tool_used",
                            agent=agent_name,
                            tool=pending_tool_name,
                            input=getattr(block, "input", None),
                        )
                if ToolResultBlock and isinstance(block, ToolResultBlock):  # type: ignore
                    if tracer:
                        tracer.write(
                            "tool_result",
                            agent=agent_name,
                            tool=getattr(block, "name", None),
                            output_preview=str(getattr(block, "output", None))[:500],
                        )
                    pending_tool_name = None

        # Final result/usage
        if isinstance(message, ResultMessage):
            if hasattr(message, "usage") and message.usage:
                usage_data = {
                    "input_tokens": message.usage.get("input_tokens", 0),
                    "output_tokens": message.usage.get("output_tokens", 0),
                    "total_tokens": message.usage.get("input_tokens", 0)
                    + message.usage.get("output_tokens", 0),
                }
            if tracer:
                tracer.write("result_usage", agent=agent_name, usage=usage_data)

    meaningful_response = (
        "\n\n".join(text_responses) if text_responses else "Analysis completed"
    )

    return {"response": meaningful_response, "usage": usage_data}


def _build_agent_prompt(
    agent_name: str,
    agent_def: Dict[str, Any],
    shared_context: SharedContext,
    previous_results: Dict[str, AgentResult],
) -> str:
    """
    Build the prompt for the Claude Code agent.

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
