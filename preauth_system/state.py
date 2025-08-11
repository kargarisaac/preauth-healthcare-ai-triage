"""
LangGraph State Schema for Pre-Authorization Workflow
====================================================

Defines the state structure for the UAE healthcare pre-authorization analysis
system using LangGraph StateGraph.

The PreAuthState manages the complete workflow from XML processing through 
agent execution to final authorization decisions.
"""

from typing import Dict, Any, List, Optional, Annotated
from typing_extensions import TypedDict
from datetime import datetime
from operator import add


class XMLData(TypedDict):
    """Parsed XML request data structure."""

    file_path: str
    format: str  # 'eclaim' or 'shafafiya'
    as_dict: Dict[str, Any]


class PatientInfo(TypedDict):
    """Extracted patient information from XML."""

    patient_id: Optional[str]
    EmiratesIDNumber: Optional[str]
    services: List[Dict[str, Any]]
    total_cost: float
    justification: Optional[str]


class PatientData(TypedDict):
    """Complete patient medical history from ETL."""

    demographics: Dict[str, Any]
    labs: List[Dict[str, Any]]
    medications: List[Dict[str, Any]]
    claims: List[Dict[str, Any]]
    preauth_history: List[Dict[str, Any]]


class AgentResult(TypedDict):
    """Individual agent execution result structure."""

    agent_name: str
    status: str  # 'pending', 'running', 'completed', 'failed'
    start_time: Optional[str]
    end_time: Optional[str]
    processing_time_seconds: Optional[float]
    response: Optional[str]
    usage: Dict[str, Any]
    success: bool
    error: Optional[str]
    traceback: Optional[str]


class FinalDecision(TypedDict):
    """Final authorization decision structure."""

    decision: str  # 'APPROVED', 'DENIED', 'REQUIRES_REVIEW'
    confidence: float
    authorization_number: Optional[str]
    valid_days: Optional[int]
    conditions: List[str]
    rationale: str
    agent_based: bool


class SharedContext(TypedDict):
    """Shared context data for all agents."""

    xml_request: Dict[str, Any]
    patient_demographics: Dict[str, Any]
    medical_history: Dict[str, Any]
    clinical_data: Dict[str, Any]
    specialty: str
    analysis_timestamp: str


class WorkflowControl(TypedDict):
    """Workflow execution control and tracking."""

    current_phase: int  # 1, 2, or 3
    completed_agents: Annotated[List[str], add]
    failed_agents: Annotated[List[str], add]
    phase_1_complete: bool
    phase_2_complete: bool
    phase_3_complete: bool
    workflow_complete: bool
    errors: Annotated[List[str], add]


def _merge_workflow_control(a: WorkflowControl, b: WorkflowControl) -> WorkflowControl:
    """Reducer to merge concurrent updates to workflow_control."""
    if a is None:
        return b
    if b is None:
        return a
    merged: Dict[str, Any] = dict(a)

    # Merge lists with de-duplication preserving order
    def _merge_list(l1: List[str], l2: List[str]) -> List[str]:
        seen = set(l1)
        return l1 + [x for x in l2 if x not in seen]

    merged["completed_agents"] = _merge_list(
        a.get("completed_agents", []), b.get("completed_agents", [])
    )
    merged["failed_agents"] = _merge_list(
        a.get("failed_agents", []), b.get("failed_agents", [])
    )
    merged["errors"] = a.get("errors", []) + b.get("errors", [])
    # Booleans: OR
    for key in [
        "phase_1_complete",
        "phase_2_complete",
        "phase_3_complete",
        "workflow_complete",
    ]:
        merged[key] = bool(a.get(key, False) or b.get(key, False))
    # Phase: take max (advance only)
    merged["current_phase"] = max(
        int(a.get("current_phase", 0)), int(b.get("current_phase", 0))
    )
    return merged  # type: ignore


class CostTracking(TypedDict):
    """Cost and usage tracking across agents."""

    total_cost_usd: float
    token_usage_by_agent: Dict[str, Dict[str, Any]]
    processing_start: str
    processing_end: Optional[str]
    total_processing_time: Optional[float]


class PreAuthState(TypedDict):
    """
    Complete state schema for the Pre-Authorization LangGraph workflow.

    This state is shared across all nodes and manages the entire workflow
    from XML processing through agent execution to final decision.

    Fields:
        # Input Data
        xml_file_path: Path to the XML request file
        xml_format: Format type ('eclaim' or 'shafafiya')
        xml_data: Parsed XML request data
        patient_info: Extracted patient demographics and request details
        patient_data: Complete medical history from ETL system

        # Workflow Management
        workflow_control: Execution state and phase tracking
        unified_patient_record: Complete unified patient data
        agent_execution_context: Streamlined context for agent execution

        # Agent Results (with reducers for concurrent updates)
        clinical_analysis_result: Results from clinical-analyzer agent
        medication_analysis_result: Results from medication-specialist agent
        risk_assessment_result: Results from risk-assessor agent
        decision_making_result: Results from decision-maker agent
        compliance_audit_result: Results from compliance-auditor agent

        # Output
        specialty: Determined medical specialty
        final_decision: Final authorization decision
        cost_tracking: Token usage and cost metrics

        # Metadata
        timestamp: Workflow execution timestamp
        analysis_id: Unique identifier for this analysis
    """

    # Input Data
    xml_file_path: str
    xml_format: str  # 'eclaim' or 'shafafiya'
    xml_data: Optional[XMLData]
    patient_info: Optional[PatientInfo]
    patient_data: Optional[PatientData]

    # Workflow Management
    workflow_control: Annotated[WorkflowControl, _merge_workflow_control]
    
    # NEW: Unified data architecture (preferred - eliminates duplication)
    unified_patient_record: Optional[Dict[str, Any]]  # UnifiedPatientRecord from unified_data.py
    agent_execution_context: Optional[Dict[str, Any]]  # AgentExecutionContext from unified data model

    # Agent Results (individual fields to avoid concurrent update issues)
    clinical_analysis_result: Optional[AgentResult]
    medication_analysis_result: Optional[AgentResult]
    risk_assessment_result: Optional[AgentResult]
    decision_making_result: Optional[AgentResult]
    compliance_audit_result: Optional[AgentResult]

    # Output
    specialty: Optional[str]
    final_decision: Optional[FinalDecision]
    cost_tracking: CostTracking

    # Metadata
    timestamp: str
    analysis_id: str


def create_initial_state(
    xml_file_path: str, xml_format: str, analysis_id: Optional[str] = None
) -> PreAuthState:
    """
    Create initial state for the Pre-Authorization workflow.

    Args:
        xml_file_path: Path to the XML request file
        xml_format: XML format type ('eclaim' or 'shafafiya')
        analysis_id: Optional unique identifier for this analysis

    Returns:
        PreAuthState: Initial workflow state
    """
    if not analysis_id:
        analysis_id = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    return PreAuthState(
        # Input Data
        xml_file_path=xml_file_path,
        xml_format=xml_format,
        xml_data=None,
        patient_info=None,
        patient_data=None,
        # Workflow Management
        workflow_control=WorkflowControl(
            current_phase=1,
            completed_agents=[],
            failed_agents=[],
            phase_1_complete=False,
            phase_2_complete=False,
            phase_3_complete=False,
            workflow_complete=False,
            errors=[],
        ),
        # Unified data architecture
        unified_patient_record=None,
        agent_execution_context=None,
        # Agent Results
        clinical_analysis_result=None,
        medication_analysis_result=None,
        risk_assessment_result=None,
        decision_making_result=None,
        compliance_audit_result=None,
        # Output
        specialty=None,
        final_decision=None,
        cost_tracking=CostTracking(
            total_cost_usd=0.0,
            token_usage_by_agent={},
            processing_start=datetime.now().isoformat(),
            processing_end=None,
            total_processing_time=None,
        ),
        # Metadata
        timestamp=datetime.now().isoformat(),
        analysis_id=analysis_id,
    )


def get_agent_result(state: PreAuthState, agent_name: str) -> Optional[AgentResult]:
    """
    Get agent result from state by agent name.

    Args:
        state: Current workflow state
        agent_name: Name of the agent

    Returns:
        AgentResult or None if not found
    """
    agent_field_map = {
        "clinical-analyzer": "clinical_analysis_result",
        "medication-specialist": "medication_analysis_result",
        "risk-assessor": "risk_assessment_result",
        "decision-maker": "decision_making_result",
        "compliance-auditor": "compliance_audit_result",
    }

    field_name = agent_field_map.get(agent_name)
    if field_name:
        return state.get(field_name)
    return None


def set_agent_result(agent_name: str, result: AgentResult) -> Dict[str, AgentResult]:
    """
    Create state update dict for agent result.

    Args:
        agent_name: Name of the agent
        result: Agent execution result

    Returns:
        Dict with appropriate field name for state update
    """
    agent_field_map = {
        "clinical-analyzer": "clinical_analysis_result",
        "medication-specialist": "medication_analysis_result",
        "risk-assessor": "risk_assessment_result",
        "decision-maker": "decision_making_result",
        "compliance-auditor": "compliance_audit_result",
    }

    field_name = agent_field_map.get(agent_name)
    if field_name:
        return {field_name: result}
    return {}


def get_all_agent_results(state: PreAuthState) -> Dict[str, AgentResult]:
    """
    Get all completed agent results from state.

    Args:
        state: Current workflow state

    Returns:
        Dict mapping agent names to their results
    """
    results = {}

    agent_fields = [
        ("clinical-analyzer", state.get("clinical_analysis_result")),
        ("medication-specialist", state.get("medication_analysis_result")),
        ("risk-assessor", state.get("risk_assessment_result")),
        ("decision-maker", state.get("decision_making_result")),
        ("compliance-auditor", state.get("compliance_audit_result")),
    ]

    for agent_name, result in agent_fields:
        if result is not None:
            results[agent_name] = result

    return results
