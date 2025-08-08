"""
Pre-Authorization Agent using LangGraph
======================================

Main orchestration class that wraps the LangGraph workflow for UAE healthcare 
pre-authorization analysis. Provides the same interface as the original 
orchestrator while leveraging LangGraph's enhanced capabilities.

This agent coordinates multiple specialized Claude Code agents to analyze XML 
requests, patient data, and make evidence-based authorization decisions.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import traceback

from preauth_system.state import PreAuthState, create_initial_state
from preauth_system.graph import compile_preauth_graph
from preauth_system.utils import get_agent_configuration


class PreAuthAgent:
    """
    Pre-authorization agent with LangGraph workflow execution.

    This class provides the same interface as the original PreAuthOrchestrator
    while leveraging LangGraph's enhanced workflow management, visualization,
    and debugging capabilities.

    The system operates in three sequential phases:
    - Phase 1: Clinical and medication analysis (parallel execution)
    - Phase 2: Risk assessment (depends on Phase 1)
    - Phase 3: Decision making and compliance verification (parallel execution)

    Attributes:
        workflow: Compiled LangGraph workflow
        agents: Configuration dict mapping agent names to their properties
        execution_history: Storage for workflow execution records
    """

    def __init__(self, checkpointer=None, **compile_kwargs):
        """
        Initialize the Pre-Authorization agent with LangGraph workflow.

        Args:
            checkpointer: Optional LangGraph checkpointer for state persistence
            **compile_kwargs: Additional arguments for graph compilation
        """
        # Load agent configuration
        self.agents = get_agent_configuration()

        # Compile the LangGraph workflow
        compile_args = {"checkpointer": checkpointer, **compile_kwargs}
        self.workflow = compile_preauth_graph(**compile_args)

        # Track execution history
        self.execution_history = []

        print("✅ Pre-Authorization LangGraph Agent initialized")
        print(f"📊 Configured with {len(self.agents)} specialized agents")

    def process_xml_request(
        self,
        xml_file_path: str,
        xml_format: str,
        thread_id: Optional[str] = None,
        analysis_id: Optional[str] = None,
        **invoke_kwargs,
    ) -> Dict[str, Any]:
        """
        Process XML pre-authorization request with LangGraph workflow.

        Args:
            xml_file_path: Path to XML request file
            xml_format: XML format type ('eclaim' or 'shafafiya')
            thread_id: Optional thread ID for state persistence
            analysis_id: Optional unique identifier for this analysis
            **invoke_kwargs: Additional arguments for workflow invocation

        Returns:
            Complete analysis results with agent outputs and final decision
        """
        try:
            print(f"🔄 Processing XML request: {xml_file_path}")
            start_time = datetime.now()

            # Create initial state
            initial_state = create_initial_state(
                xml_file_path=xml_file_path,
                xml_format=xml_format,
                analysis_id=analysis_id,
            )

            # Configure invocation
            config = {}
            if thread_id:
                config["configurable"] = {"thread_id": thread_id}

            # Merge any additional invoke arguments
            config.update(invoke_kwargs.get("config", {}))
            invoke_args = {**invoke_kwargs, "config": config}

            # Execute workflow
            print("🤖 Executing LangGraph workflow...")
            final_state = self.workflow.invoke(initial_state, **invoke_args)

            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            # Prepare results in original format for backwards compatibility
            results = self._format_results(final_state, execution_time)

            # Store execution record
            self.execution_history.append(
                {
                    "analysis_id": final_state["analysis_id"],
                    "xml_file_path": xml_file_path,
                    "xml_format": xml_format,
                    "thread_id": thread_id,
                    "execution_time_seconds": execution_time,
                    "success": final_state["workflow_control"]["workflow_complete"],
                    "timestamp": start_time.isoformat(),
                }
            )

            print(f"✅ Analysis completed in {execution_time:.2f}s")
            return results

        except Exception as e:
            error_msg = f"Workflow execution failed: {str(e)}"
            print(f"❌ {error_msg}")

            # Return error result in expected format
            return {
                "xml_data": None,
                "patient_info": None,
                "patient_data": None,
                "specialty": None,
                "agent_results": {},
                "final_decision": {
                    "decision": "ERROR",
                    "confidence": 0.0,
                    "authorization_number": None,
                    "valid_days": None,
                    "conditions": [],
                    "rationale": error_msg,
                    "agent_based": False,
                },
                "cost_tracking": {
                    "total_cost_usd": 0.0,
                    "token_usage_by_agent": {},
                },
                "timestamp": datetime.now().isoformat(),
                "error": error_msg,
                "traceback": traceback.format_exc(),
            }

    def stream_xml_request(
        self,
        xml_file_path: str,
        xml_format: str,
        thread_id: Optional[str] = None,
        analysis_id: Optional[str] = None,
        stream_mode: str = "values",
        **stream_kwargs,
    ):
        """
        Stream XML pre-authorization request processing with real-time updates.

        Args:
            xml_file_path: Path to XML request file
            xml_format: XML format type ('eclaim' or 'shafafiya')
            thread_id: Optional thread ID for state persistence
            analysis_id: Optional unique identifier for this analysis
            stream_mode: LangGraph streaming mode ('values', 'updates', 'debug')
            **stream_kwargs: Additional arguments for workflow streaming

        Yields:
            State updates during workflow execution
        """
        try:
            print(f"🔄 Streaming XML request: {xml_file_path}")

            # Create initial state
            initial_state = create_initial_state(
                xml_file_path=xml_file_path,
                xml_format=xml_format,
                analysis_id=analysis_id,
            )

            # Configure streaming
            config = {}
            if thread_id:
                config["configurable"] = {"thread_id": thread_id}

            config.update(stream_kwargs.get("config", {}))
            stream_args = {**stream_kwargs, "config": config}

            # Stream workflow execution
            print(f"🤖 Streaming LangGraph workflow (mode: {stream_mode})...")
            yield from self.workflow.stream(
                initial_state, stream_mode=stream_mode, **stream_args
            )

            print("✅ Streaming completed")

        except Exception as e:
            error_msg = f"Workflow streaming failed: {str(e)}"
            print(f"❌ {error_msg}")
            yield {"error": error_msg, "traceback": traceback.format_exc()}

    def get_workflow_graph(self, **graph_kwargs):
        """
        Get the workflow graph for visualization.

        Args:
            **graph_kwargs: Additional arguments for graph generation

        Returns:
            Graph representation suitable for visualization
        """
        try:
            return self.workflow.get_graph(**graph_kwargs)
        except Exception as e:
            print(f"⚠️ Graph visualization not available: {e}")
            return None

    def get_agent_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all configured agents.

        Returns:
            Dict mapping agent names to their configuration
        """
        return self.agents.copy()

    def get_execution_history(self) -> List[Dict[str, Any]]:
        """
        Get history of workflow executions.

        Returns:
            List of execution records
        """
        return self.execution_history.copy()

    def _format_results(
        self, final_state: PreAuthState, execution_time: float
    ) -> Dict[str, Any]:
        """
        Format LangGraph results to match original orchestrator output format.

        Args:
            final_state: Final workflow state from LangGraph
            execution_time: Total execution time in seconds

        Returns:
            Results dict in original orchestrator format for backwards compatibility
        """
        # Collect agent results
        agent_results = {}
        agent_fields = [
            ("clinical-analyzer", final_state.get("clinical_analysis_result")),
            ("medication-specialist", final_state.get("medication_analysis_result")),
            ("risk-assessor", final_state.get("risk_assessment_result")),
            ("decision-maker", final_state.get("decision_making_result")),
            ("compliance-auditor", final_state.get("compliance_audit_result")),
        ]

        for agent_name, result in agent_fields:
            if result is not None:
                agent_results[agent_name] = result

        # Return results in original format
        return {
            "xml_data": final_state.get("xml_data"),
            "patient_info": final_state.get("patient_info"),
            "patient_data": final_state.get("patient_data"),
            "specialty": final_state.get("specialty"),
            "agent_results": agent_results,
            "final_decision": final_state.get("final_decision"),
            "cost_tracking": final_state.get("cost_tracking", {}),
            "timestamp": final_state.get("timestamp"),
            "analysis_id": final_state.get("analysis_id"),
            "workflow_control": final_state.get("workflow_control"),
            "execution_time_seconds": execution_time,
            "langgraph_enabled": True,  # Flag to indicate LangGraph usage
        }


def create_agent(checkpointer=None, **compile_kwargs) -> PreAuthAgent:
    """
    Create a Pre-Authorization agent instance.

    Args:
        checkpointer: Optional LangGraph checkpointer for state persistence
        **compile_kwargs: Additional arguments for graph compilation

    Returns:
        PreAuthAgent: Configured agent instance
    """
    return PreAuthAgent(checkpointer=checkpointer, **compile_kwargs)


# Test the agent
if __name__ == "__main__":
    from data_ingestion.etl import DATASET_PATH

    xml_file = str(DATASET_PATH / "UAE_XML" / "patient_001_eclaim.xml")
    xml_format = "eclaim"

    try:
        # Create agent
        agent = PreAuthAgent()

        # Test workflow graph
        print("\n📊 Testing workflow graph...")
        graph = agent.get_workflow_graph()
        if graph:
            print("✅ Workflow graph created successfully")

            # Try to display ASCII representation
            try:
                ascii_graph = graph.draw_ascii()
                print("\n📈 Workflow Structure:")
                print(ascii_graph)
            except Exception as viz_error:
                print(f"⚠️ ASCII visualization not available: {viz_error}")

        # Test agent info
        print("\n🤖 Agent Configuration:")
        for agent_name, config in agent.get_agent_info().items():
            phase = config["phase"]
            deps = config.get("dependencies", [])
            desc = config["description"]
            print(f"  Phase {phase}: {agent_name} - {desc}")
            if deps:
                print(f"    Dependencies: {', '.join(deps)}")

        # Test actual execution (commented out to avoid running full workflow in test)
        # print(f"\n🔄 Testing workflow execution...")
        # results = agent.process_xml_request(xml_file, xml_format)
        # print(f"✅ Test execution completed")
        # print(f"Final decision: {results['final_decision']['decision']}")

    except Exception as e:
        print(f"❌ Agent test failed: {e}")
        traceback.print_exc()
