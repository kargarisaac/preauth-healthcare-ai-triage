"""
LangGraph Workflow Definition for Pre-Authorization System
=========================================================

Defines the LangGraph workflow with nodes and edges for the UAE healthcare 
pre-authorization analysis system. Implements the 3-phase agent execution 
model with proper dependency management and parallel processing.

WORKFLOW PHASES:
- Phase 1: Clinical & Medication Analysis (Parallel)
- Phase 2: Risk Assessment (Sequential)  
- Phase 3: Decision Making & Compliance (Parallel)
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
    determine_specialty,
    prepare_shared_context,
    execute_claude_agent,
    make_final_decision,
)
from preauth_system.intake import process_pa_request
from preauth_system.summary import build_clinical_summary
from preauth_system.safety import run_basic_safety_checks

from data_ingestion.etl import get_patient_data, find_patient_by_emirates_id


def prepare_context_node(state: PreAuthState) -> Dict[str, Any]:
    """
    Initialize shared context and prepare patient data.

    Phase: Initialization
    Dependencies: None
    Parallel: No

    Args:
        state: Current workflow state

    Returns:
        State updates with parsed XML, patient data, and shared context
    """
    try:
        print(f"🔄 Preparing context for analysis: {state['xml_file_path']}")

        # Step 1: Parse XML
        xml_data = parse_xml(state["xml_file_path"], state["xml_format"])
        print(f"✅ Parsed XML format: {xml_data['format']}")

        # Step 2: Extract patient info
        patient_info = extract_patient_info(xml_data, state["xml_format"])
        patient_id = find_patient_by_emirates_id(patient_info["EmiratesIDNumber"])
        print(f"✅ Found patient: {patient_id}")

        # Step 3: Get patient data from ETL
        patient_data = get_patient_data(patient_id)
        print(
            f"✅ Retrieved patient data: {len(patient_data['labs'])} labs, {len(patient_data['claims'])} claims"
        )

        # Step 4: Determine specialty
        specialty = determine_specialty(xml_data, patient_data)
        print(f"✅ Medical specialty: {specialty}")

        # Step 5: Prepare shared context
        shared_context = prepare_shared_context(
            xml_data, patient_info, patient_data, specialty
        )

        # Update workflow control
        workflow_control = state["workflow_control"].copy()
        workflow_control["current_phase"] = 1

        return {
            "xml_data": xml_data,
            "patient_info": patient_info,
            "patient_data": patient_data,
            "specialty": specialty,
            "shared_context": shared_context,
            "workflow_control": workflow_control,
        }

    except Exception as e:
        print(f"❌ Context preparation failed: {e}")
        workflow_control = state["workflow_control"].copy()
        workflow_control["errors"] = workflow_control["errors"] + [
            f"Context preparation failed: {str(e)}"
        ]

        return {"workflow_control": workflow_control}


def clinical_analysis_node(state: PreAuthState) -> Dict[str, Any]:
    """
    Execute clinical analysis using Claude Code agent with healthcare tools.

    Phase: 1 (Parallel with medication analysis)
    Dependencies: prepare_context

    Args:
        state: Current workflow state
    """
    return _execute_agent_node(state, "clinical-analyzer")


def medication_analysis_node(state: PreAuthState) -> Dict[str, Any]:
    """
    Execute medication analysis using Claude Code agent with healthcare tools.

    Phase: 1 (Parallel with clinical analysis)
    Dependencies: prepare_context

    Args:
        state: Current workflow state

    Returns:
        State updates with medication analysis results
    """
    return _execute_agent_node(state, "medication-specialist")


def risk_assessment_node(state: PreAuthState) -> Dict[str, Any]:
    """
    Execute risk assessment using Claude Code agent with healthcare tools.

    Phase: 2 (Sequential after Phase 1)
    Dependencies: clinical_analysis, medication_analysis

    Args:
        state: Current workflow state

    Returns:
        State updates with risk assessment results
    """
    return _execute_agent_node(state, "risk-assessor")


def decision_making_node(state: PreAuthState) -> Dict[str, Any]:
    """
    Execute decision making using Claude Code agent with healthcare tools.

    Phase: 3 (Parallel with compliance audit)
    Dependencies: clinical_analysis, medication_analysis, risk_assessment

    Args:
        state: Current workflow state

    Returns:
        State updates with decision making results
    """
    return _execute_agent_node(state, "decision-maker")


def compliance_audit_node(state: PreAuthState) -> Dict[str, Any]:
    """
    Execute compliance audit using Claude Code agent with healthcare tools.

    Phase: 3 (Parallel with decision making)
    Dependencies: decision_making (for compliance verification)

    Args:
        state: Current workflow state

    Returns:
        State updates with compliance audit results
    """
    return _execute_agent_node(state, "compliance-auditor")


def finalize_decision_node(state: PreAuthState) -> Dict[str, Any]:
    """
    Process final decision and complete workflow.

    Phase: Final
    Dependencies: All previous agents

    Args:
        state: Current workflow state

    Returns:
        State updates with final decision and cost tracking
    """
    try:
        print("🏆 Finalizing authorization decision...")

        # Get all agent results
        agent_results = get_all_agent_results(state)

        # Make final decision
        final_decision = make_final_decision(
            agent_results, state["xml_data"], state["patient_data"]
        )
        print(f"✅ Final decision: {final_decision['decision']}")

        # Update cost tracking
        cost_tracking = state["cost_tracking"].copy()
        cost_tracking["processing_end"] = datetime.now().isoformat()

        if cost_tracking["processing_start"]:
            start_time = datetime.fromisoformat(cost_tracking["processing_start"])
            end_time = datetime.now()
            cost_tracking["total_processing_time"] = (
                end_time - start_time
            ).total_seconds()

        # Mark workflow complete
        workflow_control = state["workflow_control"].copy()
        workflow_control["workflow_complete"] = True
        workflow_control["phase_3_complete"] = True

        return {
            "final_decision": final_decision,
            "cost_tracking": cost_tracking,
            "workflow_control": workflow_control,
        }

    except Exception as e:
        print(f"❌ Decision finalization failed: {e}")
        workflow_control = state["workflow_control"].copy()
        workflow_control["errors"] = workflow_control["errors"] + [
            f"Decision finalization failed: {str(e)}"
        ]

        return {"workflow_control": workflow_control}


def _execute_agent_node(state: PreAuthState, agent_name: str) -> Dict[str, Any]:
    """
    Common function to execute any agent with error handling.

    Args:
        state: Current workflow state
        agent_name: Name of the agent to execute

    Returns:
        State updates with agent results
    """
    try:
        print(f"🤖 Starting {agent_name} analysis...")
        start_time = datetime.now()

        # Execute agent
        result = execute_claude_agent(
            agent_name=agent_name,
            shared_context=state["shared_context"],
            previous_results=get_all_agent_results(state),
        )

        # Update workflow control
        workflow_control = state["workflow_control"].copy()
        workflow_control["completed_agents"] = workflow_control["completed_agents"] + [
            agent_name
        ]

        # Check phase completion
        if agent_name in ["clinical-analyzer", "medication-specialist"]:
            if (
                len(
                    [
                        a
                        for a in workflow_control["completed_agents"]
                        if a in ["clinical-analyzer", "medication-specialist"]
                    ]
                )
                == 2
            ):
                workflow_control["phase_1_complete"] = True
                workflow_control["current_phase"] = 2
        elif agent_name == "risk-assessor":
            workflow_control["phase_2_complete"] = True
            workflow_control["current_phase"] = 3
        elif agent_name in ["decision-maker", "compliance-auditor"]:
            if (
                len(
                    [
                        a
                        for a in workflow_control["completed_agents"]
                        if a in ["decision-maker", "compliance-auditor"]
                    ]
                )
                == 2
            ):
                workflow_control["phase_3_complete"] = True

        # Update cost tracking
        cost_tracking = state["cost_tracking"].copy()
        if result.get("usage", {}).get("total_cost_usd"):
            cost_tracking["total_cost_usd"] += result["usage"]["total_cost_usd"]
            cost_tracking["token_usage_by_agent"][agent_name] = result["usage"]

        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        print(f"✅ {agent_name} completed in {processing_time:.2f}s")

        # Prepare state updates
        updates = set_agent_result(agent_name, result)
        updates.update(
            {"workflow_control": workflow_control, "cost_tracking": cost_tracking}
        )

        return updates

    except Exception as e:
        print(f"❌ {agent_name} failed: {e}")

        # Create failed result
        failed_result = AgentResult(
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

        # Update workflow control
        workflow_control = state["workflow_control"].copy()
        workflow_control["failed_agents"] = workflow_control["failed_agents"] + [
            agent_name
        ]
        workflow_control["errors"] = workflow_control["errors"] + [
            f"{agent_name} failed: {str(e)}"
        ]

        updates = set_agent_result(agent_name, failed_result)
        updates.update({"workflow_control": workflow_control})

        return updates


def should_start_phase_1(state: PreAuthState) -> Literal["clinical_analysis", "error"]:
    """
    Conditional edge to start Phase 1 or handle errors.

    Args:
        state: Current workflow state

    Returns:
        Next node name or error handling
    """
    if state["shared_context"] is None:
        return "error"
    return "clinical_analysis"


def should_start_phase_2(state: PreAuthState) -> Literal["risk_assessment", "wait"]:
    """
    Conditional edge to start Phase 2 when Phase 1 is complete.

    Args:
        state: Current workflow state

    Returns:
        Next node name based on Phase 1 completion
    """
    if state["workflow_control"]["phase_1_complete"]:
        return "risk_assessment"
    return "wait"


def should_start_phase_3(state: PreAuthState) -> Literal["decision_making", "wait"]:
    """
    Conditional edge to start Phase 3 when Phase 2 is complete.

    Args:
        state: Current workflow state

    Returns:
        Next node name based on Phase 2 completion
    """
    if state["workflow_control"]["phase_2_complete"]:
        return "decision_making"
    return "wait"


def should_finalize(state: PreAuthState) -> Literal["finalize_decision", "wait"]:
    """
    Conditional edge to finalize when Phase 3 is complete.

    Args:
        state: Current workflow state

    Returns:
        Next node name based on Phase 3 completion
    """
    # Check if both decision-making and compliance-auditor are complete
    completed = state["workflow_control"]["completed_agents"]
    decision_complete = "decision-maker" in completed
    compliance_complete = "compliance-auditor" in completed

    if decision_complete and compliance_complete:
        return "finalize_decision"
    return "wait"


def create_preauth_graph() -> StateGraph:
    """
    Create and configure the Pre-Authorization LangGraph workflow.

    Returns:
        StateGraph: Configured workflow graph
    """
    # Create graph
    workflow = StateGraph(PreAuthState)

    # Add nodes
    workflow.add_node("prepare_context", prepare_context_node)
    workflow.add_node("clinical_analysis", clinical_analysis_node)
    workflow.add_node("medication_analysis", medication_analysis_node)
    workflow.add_node("risk_assessment", risk_assessment_node)
    workflow.add_node("decision_making", decision_making_node)
    workflow.add_node("compliance_audit", compliance_audit_node)
    workflow.add_node("finalize_decision", finalize_decision_node)

    # Define edges
    # Entry point
    workflow.add_edge(START, "prepare_context")

    # Phase 1: Conditional start after context preparation
    workflow.add_conditional_edges(
        "prepare_context",
        should_start_phase_1,
        {"clinical_analysis": "clinical_analysis", "error": END},
    )

    # Phase 1: Parallel execution - both go to medication analysis check
    workflow.add_edge("clinical_analysis", "medication_analysis")

    # Phase 2: Start risk assessment when Phase 1 complete
    workflow.add_conditional_edges(
        "medication_analysis",
        should_start_phase_2,
        {
            "risk_assessment": "risk_assessment",
            "wait": END,  # Should not happen in normal flow
        },
    )

    # Phase 3: Start decision making when Phase 2 complete
    workflow.add_conditional_edges(
        "risk_assessment",
        should_start_phase_3,
        {
            "decision_making": "decision_making",
            "wait": END,  # Should not happen in normal flow
        },
    )

    # Phase 3: Parallel execution - decision making triggers compliance audit
    workflow.add_edge("decision_making", "compliance_audit")

    # Finalization: Complete when Phase 3 done
    workflow.add_conditional_edges(
        "compliance_audit",
        should_finalize,
        {
            "finalize_decision": "finalize_decision",
            "wait": END,  # Should not happen in normal flow
        },
    )

    # End workflow
    workflow.add_edge("finalize_decision", END)

    return workflow


def compile_preauth_graph(**compile_kwargs) -> StateGraph:
    """
    Compile the Pre-Authorization workflow graph.

    Args:
        **compile_kwargs: Additional compilation arguments

    Returns:
        Compiled StateGraph ready for execution
    """
    workflow = create_preauth_graph()
    return workflow.compile(**compile_kwargs)


graph = create_preauth_graph()

if __name__ == "__main__":
    # Test graph creation and visualization
    try:
        graph = create_preauth_graph()
        compiled_graph = compile_preauth_graph()

        print("✅ Pre-Authorization LangGraph created successfully")
        print(f"📊 Graph has {len(graph.nodes)} nodes and {len(graph.edges)} edges")

        # Try to create a simple visualization
        try:
            # This will work if graphviz is installed
            graph_image = compiled_graph.get_graph().draw_ascii()
            print("\n📈 Graph Structure:")
            print(graph_image)
        except Exception as viz_error:
            print(f"⚠️ Graph visualization not available: {viz_error}")

    except Exception as e:
        print(f"❌ Failed to create graph: {e}")
        traceback.print_exc()
