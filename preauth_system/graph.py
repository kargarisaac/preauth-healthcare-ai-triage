"""
LangGraph Workflow Definition for Pre-Authorization System
=========================================================

Streamlined workflow with logical steps:
- data_preparation → phase 1 (clinical_analysis, medication_analysis in parallel)
- phase1_barrier → risk_assessment → phase 3 (decision_making, compliance_audit in parallel)
- phase3_barrier → finalize_decision

Key improvements:
- Combined intake + clinical_summary into single data_preparation node
- Uses create_unified_patient_record for efficient data processing
- Eliminated redundant data structures and legacy compatibility code
"""

from typing import Dict, Any, Literal
from datetime import datetime
import traceback

from langgraph.graph import StateGraph, START, END

from preauth_system.state import (
    PreAuthState,
    AgentResult,
    set_agent_result,
    get_all_agent_results,
)
from preauth_system.utils import (
    parse_xml,
    extract_patient_info,
    make_final_decision,
)
from data_ingestion.etl import create_unified_patient_record
from preauth_system.utils import prepare_agent_execution_context
from preauth_system.agents_openai import execute_openai_agent
from preauth_system.pricing import calculate_cost_from_usage
from data_ingestion.etl import find_patient_by_emirates_id

# Import BAML client for final decision making
try:
    from baml_client import b
    BAML_AVAILABLE = True
except ImportError:
    BAML_AVAILABLE = False
    b = None


# Helper for pricing
def _compute_cost_usd(usage: Dict[str, Any]) -> float:
    """Compute cost using API-based pricing module."""
    cost_info = calculate_cost_from_usage(usage)
    return cost_info["costs_breakdown"]["total_cost_usd"]


def data_preparation_node(state: PreAuthState) -> Dict[str, Any]:
    """
    Data preparation: Parse XML, find patient, and create unified patient record.

    This node combines intake and clinical data preparation into a single step:
    1. Parse XML request and extract patient information
    2. Find patient in FHIR data using Emirates ID
    3. Create unified patient record combining XML + FHIR data
    4. Prepare agent execution context

    UNIFIED APPROACH:
    - Uses FHIR Bundle as canonical clinical history (enriched with medical codes)
    - XML request data provides most current demographics/insurance
    - Single unified record eliminates overlapping data structures
    """
    try:
        # Step 1: Parse XML and extract patient info
        xml_data = parse_xml(state["xml_file_path"], state["xml_format"])
        patient_info = extract_patient_info(xml_data, state["xml_format"])

        # Step 2: Find patient by Emirates ID from XML request
        patient_id = find_patient_by_emirates_id(patient_info["EmiratesIDNumber"])

        if not patient_id:
            raise ValueError(
                f"Patient not found for Emirates ID: {patient_info['EmiratesIDNumber']}"
            )

        # Step 3: Create unified patient record (eliminates data duplication)
        unified_patient_record = create_unified_patient_record(
            patient_id=patient_id,
            xml_request_data=xml_data,
            xml_patient_info=patient_info,
        )

        # Step 4: Prepare streamlined agent context
        agent_execution_context = prepare_agent_execution_context(
            unified_patient_record
        )

        # Update workflow control
        wf = state["workflow_control"].copy()
        wf["current_phase"] = 1
        wf["data_architecture"] = "unified"

        return {
            "xml_data": xml_data,
            "patient_info": patient_info,
            "unified_patient_record": unified_patient_record,
            "agent_execution_context": agent_execution_context,
            "specialty": unified_patient_record.specialty_context,
            "workflow_control": wf,
        }

    except Exception as e:
        wf = state["workflow_control"].copy()
        wf["errors"] = wf["errors"] + [f"Data preparation failed: {str(e)}"]
        return {"workflow_control": wf}


def clinical_analysis_node(state: PreAuthState) -> Dict[str, Any]:
    return _execute_agent_node(state, "clinical-analyzer")


def medication_analysis_node(state: PreAuthState) -> Dict[str, Any]:
    return _execute_agent_node(state, "medication-specialist")


def risk_assessment_node(state: PreAuthState) -> Dict[str, Any]:
    return _execute_agent_node(state, "risk-assessor")


def decision_making_node(state: PreAuthState) -> Dict[str, Any]:
    return _execute_agent_node(state, "decision-maker")


def compliance_audit_node(state: PreAuthState) -> Dict[str, Any]:
    return _execute_agent_node(state, "compliance-auditor")


def phase1_barrier_node(_: PreAuthState) -> Dict[str, Any]:
    """Barrier node after clinical and medication analyses."""
    return {}


def phase3_barrier_node(_: PreAuthState) -> Dict[str, Any]:
    """Barrier node after decision_making and compliance_audit."""
    return {}


def _convert_agent_result_to_baml_format(agent_name: str, result: Dict[str, Any]) -> Dict[str, Any]:
    """Convert agent result to BAML AgentAnalysis format."""
    return {
        "agent_name": agent_name,
        "success": result.get("success", False),
        "response": result.get("response") if result.get("success") else None,
        "confidence": result.get("confidence"),
        "error": result.get("error") if not result.get("success") else None
    }


def _prepare_patient_context_for_baml(unified_patient_record, xml_data: Dict[str, Any]) -> tuple[str, str, str]:
    """Extract and format patient context for BAML function."""
    # Extract patient demographics
    patient_info = unified_patient_record.patient_info if hasattr(unified_patient_record, 'patient_info') else {}
    demographics = f"""
Patient ID: {patient_info.get('patient_id', 'Unknown')}
Emirates ID: {patient_info.get('emirates_id', 'Unknown')}
Name: {patient_info.get('first_name', '')} {patient_info.get('last_name', '')}
Age: {patient_info.get('age', 'Unknown')} | DOB: {patient_info.get('date_of_birth', 'Unknown')}
Gender: {patient_info.get('gender', 'Unknown')}
Nationality: {patient_info.get('nationality', 'Unknown')}
""".strip()
    
    # Extract requested services from XML
    services = xml_data.get('services', [])
    requested_services = "\n".join([
        f"- {service.get('ActivityCode', 'N/A')}: {service.get('ActivityInstructions', 'No description')} (Cost: {service.get('RequestedAmount', {}).get('#text', 'N/A')} {service.get('RequestedAmount', {}).get('@currency', 'AED')})"
        for service in services[:5]  # Limit to first 5 services
    ]) if services else "No services specified"
    
    # Extract clinical context
    clinical_notes = getattr(unified_patient_record, 'clinical_summary', 'No clinical summary available')
    recent_labs = getattr(unified_patient_record, 'recent_labs', [])
    current_meds = getattr(unified_patient_record, 'current_medications', [])
    
    clinical_context = f"""
Clinical Summary: {clinical_notes}

Recent Lab Results: {len(recent_labs)} available
Current Medications: {len(current_meds)} active medications
Specialty Context: {getattr(unified_patient_record, 'specialty_context', 'General')}
""".strip()
    
    return demographics, requested_services, clinical_context


def finalize_decision_node(state: PreAuthState) -> Dict[str, Any]:
    try:
        agent_results = get_all_agent_results(state)

        # Use unified patient record
        patient_data = state["unified_patient_record"]
        
        # Use BAML function for final decision if available
        if BAML_AVAILABLE and b:
            # Convert agent results to BAML format
            required_agents = ["clinical-analyzer", "medication-specialist", "risk-assessor", "decision-maker", "compliance-auditor"]
            baml_agents = {}
            
            for agent_name in required_agents:
                result = agent_results.get(agent_name, {})
                baml_agents[agent_name.replace("-", "_")] = _convert_agent_result_to_baml_format(agent_name, result)
            
            # Prepare patient context
            demographics, requested_services, clinical_context = _prepare_patient_context_for_baml(
                patient_data, state["xml_data"]
            )
            
            # Call BAML function
            baml_decision = b.FinalizePreAuthDecision(
                clinical_analysis=baml_agents["clinical_analyzer"],
                medication_analysis=baml_agents["medication_specialist"], 
                risk_assessment=baml_agents["risk_assessor"],
                decision_making=baml_agents["decision_maker"],
                compliance_audit=baml_agents["compliance_auditor"],
                patient_demographics=demographics,
                requested_services=requested_services,
                clinical_context=clinical_context
            )
            
            # Convert BAML result to expected format
            file_path = state["xml_data"].get("file_path", "default")
            auth_number = f"AUTH-2025-{datetime.now().strftime('%Y%m%d')}-{abs(hash(file_path)) % 10000:04d}"
            
            final_decision = {
                "decision": baml_decision.decision.name,  # APPROVED, DENIED, REQUIRES_REVIEW
                "confidence": baml_decision.confidence,
                "authorization_number": auth_number,
                "valid_days": 90,
                "conditions": baml_decision.conditions,
                "rationale": baml_decision.rationale,
                "agent_based": True,
                "key_factors": baml_decision.key_factors,
                "risk_assessment": baml_decision.risk_assessment,
                "policy_compliance": baml_decision.policy_compliance,
                "recommendation": baml_decision.recommendation
            }
        else:
            # Fallback to original logic if BAML not available
            final_decision = make_final_decision(
                agent_results, state["xml_data"], patient_data
            )
        cost_tracking = state["cost_tracking"].copy()
        cost_tracking["processing_end"] = datetime.now().isoformat()
        if cost_tracking["processing_start"]:
            start_time = datetime.fromisoformat(cost_tracking["processing_start"])
            cost_tracking["total_processing_time"] = (
                datetime.now() - start_time
            ).total_seconds()

        # Aggregate usage and compute costs using new pricing module
        token_usage_by_agent: Dict[str, Any] = {}
        total_cost = 0.0
        cost_optimization_notes = []

        for agent_name, res in agent_results.items():
            usage = res.get("usage") or {}

            # Use enhanced cost calculation with optimization notes
            if usage.get("pricing_source") == "api_based":
                # Already has accurate cost from agents_openai.py
                cost_usd = usage.get("cost_usd", 0.0)
                cost_breakdown = usage.get("cost_breakdown", {})
                optimization_notes = usage.get("cost_optimization_notes", [])
            else:
                # Calculate cost for usage objects without pricing info
                cost_usd = _compute_cost_usd(usage)
                cost_breakdown = {"total_cost_usd": cost_usd}
                optimization_notes = []

            total_cost += cost_usd
            cost_optimization_notes.extend(optimization_notes)

            token_usage_by_agent[agent_name] = {
                **usage,
                "cost_usd": round(cost_usd, 6),
                "cost_breakdown": cost_breakdown,
                "optimization_notes": optimization_notes,
            }

        cost_tracking["token_usage_by_agent"] = token_usage_by_agent
        cost_tracking["total_cost_usd"] = round(total_cost, 6)
        cost_tracking["cost_optimization_notes"] = list(
            set(cost_optimization_notes)
        )  # Remove duplicates

        wf = state["workflow_control"].copy()
        wf["workflow_complete"] = True
        wf["phase_3_complete"] = True
        return {
            "final_decision": final_decision,
            "cost_tracking": cost_tracking,
            "workflow_control": wf,
        }
    except Exception as e:
        wf = state["workflow_control"].copy()
        wf["errors"] = wf["errors"] + [f"Finalize failed: {str(e)}"]
        return {"workflow_control": wf}


def _execute_agent_node(state: PreAuthState, agent_name: str) -> Dict[str, Any]:
    try:
        # Use streamlined agent execution context
        agent_context = state["agent_execution_context"]

        result = execute_openai_agent(
            agent_name=agent_name,
            shared_context=agent_context,
            previous_results=get_all_agent_results(state),
        )
        wf = state["workflow_control"].copy()
        wf["completed_agents"] = wf["completed_agents"] + [agent_name]
        if agent_name == "risk-assessor":
            wf["phase_2_complete"] = True
            wf["current_phase"] = 3
        if agent_name in ["clinical-analyzer", "medication-specialist"]:
            # When both complete, phase 1 can be marked done by barrier
            pass
        # Enhanced token/cost tracking with optimization suggestions
        updates = set_agent_result(agent_name, result)

        # Log cost optimization notes if available (tracer not available in this context)
        # Cost optimization notes are now stored in the result and aggregated in finalize_decision_node

        updates.update({"workflow_control": wf})
        return updates
    except Exception as e:
        failed_result = AgentResult(
            agent_name=agent_name,
            status="failed",
            start_time=None,
            end_time=datetime.now().isoformat(),
            processing_time_seconds=None,
            response=None,
            usage={},
            success=False,
            error=str(e),
            traceback=traceback.format_exc(),
        )
        wf = state["workflow_control"].copy()
        wf["failed_agents"] = wf["failed_agents"] + [agent_name]
        wf["errors"] = wf["errors"] + [f"{agent_name} failed: {str(e)}"]
        updates = set_agent_result(agent_name, failed_result)
        updates.update({"workflow_control": wf})
        return updates


def should_proceed_phase1(
    state: PreAuthState,
) -> Literal["risk_assessment", "phase1_barrier"]:
    """Proceed to risk assessment only when both clinical and medication analyses are complete."""
    completed = state["workflow_control"]["completed_agents"]
    if "clinical-analyzer" in completed and "medication-specialist" in completed:
        wf = state["workflow_control"].copy()
        wf["phase_1_complete"] = True
        return "risk_assessment"
    return "phase1_barrier"


def should_proceed_phase3(
    state: PreAuthState,
) -> Literal["finalize_decision", "phase3_barrier"]:
    """Proceed to finalize only when both decision and compliance are complete."""
    completed = state["workflow_control"]["completed_agents"]
    if "decision-maker" in completed and "compliance-auditor" in completed:
        return "finalize_decision"
    return "phase3_barrier"


def create_preauth_graph() -> StateGraph:
    workflow = StateGraph(PreAuthState)

    # Data preparation (unified intake + clinical summary)
    workflow.add_node("data_preparation", data_preparation_node)

    # Phase 1 parallel agents
    workflow.add_node("clinical_analysis", clinical_analysis_node)
    workflow.add_node("medication_analysis", medication_analysis_node)
    workflow.add_node("phase1_barrier", phase1_barrier_node)

    # Risk assessment
    workflow.add_node("risk_assessment", risk_assessment_node)

    # Phase 3 parallel agents
    workflow.add_node("decision_making", decision_making_node)
    workflow.add_node("compliance_audit", compliance_audit_node)
    workflow.add_node("phase3_barrier", phase3_barrier_node)

    # Finalization
    workflow.add_node("finalize_decision", finalize_decision_node)

    # Edges - Simplified flow
    workflow.add_edge(START, "data_preparation")

    # Start phase 1 in parallel after data preparation
    workflow.add_edge("data_preparation", "clinical_analysis")
    workflow.add_edge("data_preparation", "medication_analysis")

    # Join phase 1
    workflow.add_edge("clinical_analysis", "phase1_barrier")
    workflow.add_edge("medication_analysis", "phase1_barrier")
    workflow.add_conditional_edges(
        "phase1_barrier",
        should_proceed_phase1,
        {"risk_assessment": "risk_assessment", "phase1_barrier": "phase1_barrier"},
    )

    # After risk, start phase 3 in parallel
    workflow.add_edge("risk_assessment", "decision_making")
    workflow.add_edge("risk_assessment", "compliance_audit")

    # Join phase 3
    workflow.add_edge("decision_making", "phase3_barrier")
    workflow.add_edge("compliance_audit", "phase3_barrier")
    workflow.add_conditional_edges(
        "phase3_barrier",
        should_proceed_phase3,
        {"finalize_decision": "finalize_decision", "phase3_barrier": "phase3_barrier"},
    )

    workflow.add_edge("finalize_decision", END)
    return workflow


def compile_preauth_graph(**compile_kwargs) -> StateGraph:
    workflow = create_preauth_graph()
    return workflow.compile(**compile_kwargs)


graph = create_preauth_graph()
