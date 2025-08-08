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
import xmltodict  # type: ignore

from claude_code_sdk import (
    query,
    ClaudeCodeOptions,
    AssistantMessage,
    TextBlock,
    ResultMessage,
)


from preauth_system.state import AgentResult, SharedContext


def load_agent_definitions() -> Dict[str, Dict[str, Any]]:
    """
    Load agent definitions from markdown files.

    Returns:
        Dict mapping agent names to their parsed definitions

    Raises:
        Exception: If any required agent definition file is missing
    """
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
        Dict containing extracted patient information
    """
    if xml_format == "eclaim":
        return xml_data.get("as_dict", {}).get("Patient", {})
    elif xml_format == "shafafiya":
        # Add Shafafiya parsing logic when needed
        pass

    return {}


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

        # Load agent definitions
        agent_definitions = load_agent_definitions()
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

        # Execute agent synchronously using asyncio.run
        result = asyncio.run(_execute_agent_async(prompt, options))

        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

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
    prompt: str, options: ClaudeCodeOptions
) -> Dict[str, Any]:
    """
    Execute agent asynchronously with Claude Code SDK.

    Args:
        prompt: Complete prompt for the agent
        options: Claude Code execution options

    Returns:
        Dict with response and usage data
    """
    text_responses = []
    usage_data = {}
    total_cost = 0.0

    async for message in query(prompt=prompt, options=options):
        # Extract text from AssistantMessage
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    text_responses.append(block.text)

        # Capture usage data from ResultMessage
        if isinstance(message, ResultMessage):
            if hasattr(message, "usage") and message.usage:
                usage_data = {
                    "input_tokens": message.usage.get("input_tokens", 0),
                    "output_tokens": message.usage.get("output_tokens", 0),
                    "total_tokens": message.usage.get("input_tokens", 0)
                    + message.usage.get("output_tokens", 0),
                }

            if hasattr(message, "total_cost_usd") and message.total_cost_usd:
                usage_data["total_cost_usd"] = float(message.total_cost_usd)
                total_cost += usage_data["total_cost_usd"]

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
    decision_agent = agent_results.get("decision-maker", {})

    if decision_agent.get("success"):
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
        error_msg = decision_agent.get("error", "Unknown error")
        print(f"❌ Decision maker failed: {error_msg}")
        raise Exception(f"Decision maker failed: {error_msg}")

    return {
        "decision": decision,
        "confidence": confidence,
        "authorization_number": f"AUTH-2025-{datetime.now().strftime('%Y%m%d')}-{hash(xml_data['file_path']) % 10000:04d}",
        "valid_days": 90,
        "conditions": ["Standard monitoring", "Follow-up required"],
        "rationale": "Based on comprehensive agent analysis including clinical review, medication assessment, and risk stratification.",
        "agent_based": decision_agent.get("success", False),
    }


def get_agent_configuration() -> Dict[str, Dict[str, Any]]:
    """
    Get agent configuration with phases and dependencies.

    Returns:
        Dict mapping agent names to their configuration
    """
    return {
        "clinical-analyzer": {
            "phase": 1,
            "dependencies": [],
            "description": "Medical history and disease progression analysis",
        },
        "medication-specialist": {
            "phase": 1,
            "dependencies": [],
            "description": "Drug interactions and safety assessment",
        },
        "risk-assessor": {
            "phase": 2,
            "dependencies": ["clinical-analyzer", "medication-specialist"],
            "description": "Clinical risk stratification and outcome prediction",
        },
        "decision-maker": {
            "phase": 3,
            "dependencies": [
                "clinical-analyzer",
                "medication-specialist",
                "risk-assessor",
            ],
            "description": "Evidence-based authorization recommendations",
        },
        "compliance-auditor": {
            "phase": 3,
            "dependencies": ["decision-maker"],
            "description": "UAE regulatory compliance verification",
        },
    }
