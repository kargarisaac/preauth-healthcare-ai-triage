"""
Pre-Authorization Orchestrator - LangGraph Integration
Uses LangGraph workflow exclusively with real data processing
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger

# Core system imports
from preauth_system.performance import get_preauth_cache

# LangGraph workflow imports
from preauth_system.graph import compile_preauth_graph
from preauth_system.state import (
    create_initial_state,
    get_all_agent_results,
)
from preauth_system.utils import prime_agent_definitions_cache


class PreAuthOrchestrator:
    """Main orchestrator for pre-authorization workflow using LangGraph exclusively."""

    def __init__(self):
        """Initialize the orchestrator with LangGraph workflow."""
        self.cache = get_preauth_cache()

        # Warm agent definitions cache once at startup to avoid repeated loads
        try:
            prime_agent_definitions_cache()
        except Exception as e:
            logger.warning(f"Agent definitions cache warm-up failed: {e}")

        # Initialize LangGraph workflow
        try:
            self.langgraph_workflow = compile_preauth_graph()
            logger.info("Initialized LangGraph workflow successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LangGraph workflow: {e}")
            raise Exception(f"LangGraph workflow initialization failed: {e}")

        logger.info("Initialized PreAuth Orchestrator with LangGraph workflow")

    def process_request(
        self,
        xml_file_path: str,
        patient_id: Optional[str] = None,
        xml_format: str = "eclaim",
    ) -> Dict[str, Any]:
        """
        Process pre-authorization request using LangGraph workflow.
        Input parsing and clinical summary are handled by graph nodes.
        """
        try:
            start_time = time.time()
            logger.info(
                f"Processing PA request for patient: {patient_id} using LangGraph workflow"
            )

            # Execute LangGraph workflow end-to-end (intake, clinical summary, agents, finalize)
            workflow_result = self._execute_langgraph_workflow(
                xml_file_path, xml_format, patient_id or "unknown"
            )

            if workflow_result.get("success"):
                final_state = workflow_result["final_state"]

                processing_time = time.time() - start_time
                decision_obj = final_state.get("final_decision") or {}

                # Emirates ID from graph state
                emirates_id = (final_state.get("patient_info") or {}).get(
                    "EmiratesIDNumber", patient_id or "Unknown"
                )

                return {
                    "success": True,
                    "patient_id": emirates_id,
                    "workflow_execution": "langgraph",
                    "decision": decision_obj,
                    "agent_results": workflow_result.get("agent_results", {}),
                    "cost_tracking": final_state.get("cost_tracking", {}),
                    "processing_time_seconds": round(processing_time, 2),
                }
            else:
                error_msg = workflow_result.get("error", "Unknown workflow error")
                logger.error(f"LangGraph workflow failed: {error_msg}")
                return {
                    "success": False,
                    "error": f"LangGraph workflow failed: {error_msg}",
                    "patient_id": patient_id,
                    "workflow_execution": "failed",
                }

        except Exception as e:
            logger.error(f"Processing failed: {e}")
            return {"success": False, "error": str(e), "patient_id": patient_id}

    def _execute_langgraph_workflow(
        self, xml_file_path: str, xml_format: str, request_id: str
    ) -> Dict[str, Any]:
        """Execute the LangGraph workflow for agent-based analysis."""
        try:
            analysis_id = (
                f"analysis_{request_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            initial_state = create_initial_state(xml_file_path, xml_format, analysis_id)

            logger.info(f"Starting LangGraph workflow execution for {request_id}")
            final_state = self.langgraph_workflow.invoke(initial_state)
            agent_results = get_all_agent_results(final_state)

            logger.info(f"LangGraph workflow completed successfully for {request_id}")
            logger.info(f"Agent results: {list(agent_results.keys())}")

            return {
                "success": True,
                "final_state": final_state,
                "agent_results": {
                    name: {
                        "status": result.get("status"),
                        "success": result.get("success"),
                        "processing_time": result.get("processing_time_seconds"),
                        "response": result.get("response", ""),
                    }
                    for name, result in agent_results.items()
                },
                "workflow_complete": final_state.get("workflow_control", {}).get(
                    "workflow_complete", False
                ),
            }

        except Exception as e:
            logger.error(f"LangGraph workflow execution failed: {e}")
            import traceback

            traceback.print_exc()
            return {"success": False, "error": str(e), "workflow_complete": False}


def process_demo_cases(
    orchestrator: PreAuthOrchestrator, demo_case: tuple
) -> Dict[str, Any]:
    """Process demo cases with real data processing."""

    try:
        patient_id, xml_path = demo_case
        results = {}
        if Path(xml_path).exists():
            result = orchestrator.process_request(xml_path, patient_id, "eclaim")
            results[patient_id] = result

            if result.get("success"):
                decision = result.get("decision", {})
                decision_type = decision.get("decision", "UNKNOWN")
                logger.info(f"✅ {patient_id}: {decision_type}")
            else:
                logger.error(f"❌ {patient_id}: {result.get('error')}")
        else:
            results[patient_id] = {
                "success": False,
                "error": f"File not found: {xml_path}",
            }
            logger.error(f"❌ {patient_id}: File not found")

    except Exception as e:
        results[patient_id] = {"success": False, "error": str(e)}
        logger.error(f"❌ {patient_id}: Processing failed - {e}")

    return result


def main():
    """CLI entry point for testing with Patient_007 processing and file output."""
    orchestrator = PreAuthOrchestrator()

    # Create dated run directory: output/YYYYMMDD/HHMMSS
    now = datetime.now()
    date_dir = Path("output") / now.strftime("%Y%m%d")
    time_dir = date_dir / now.strftime("%H%M%S")
    time_dir.mkdir(parents=True, exist_ok=True)

    # Expose run dir to route traces
    os.environ["PREAUTH_RUN_DIR"] = str(time_dir)

    xml_file_path = "data/dataset_2/synthetic_dataset/UAE_XML/Patient_007_eclaim.xml"
    patient_id = "Patient_007"

    logger.info(f"Processing {patient_id} with LangGraph workflow")

    result = orchestrator.process_request(
        xml_file_path=xml_file_path, patient_id=patient_id, xml_format="eclaim"
    )

    json_output_path = time_dir / f"{patient_id}_result.json"
    try:
        with open(json_output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str)
        logger.info(f"Processing result saved to: {json_output_path}")
        print(f"✅ Processing result saved to: {json_output_path}")
    except Exception as e:
        logger.error(f"Failed to save JSON result: {e}")
        print(f"❌ Failed to save JSON result: {e}")

    print("\n" + "=" * 60)
    print(f"PROCESSING SUMMARY - {patient_id}")
    print("=" * 60)
    status = "SUCCESS" if result.get("success") else "FAILED"
    print(f"Status: {status}")

    if result.get("success"):
        print(f"Patient ID: {result.get('patient_id')}")
        print(f"Workflow: {result.get('workflow_execution')}")
        print(f"Processing Time: {result.get('processing_time_seconds')}s")

        decision = result.get("decision", {})
        print(f"Decision: {decision.get('decision', 'Unknown')}")
        print(f"Confidence: {decision.get('confidence', 'N/A')}")

        if result.get("agent_results"):
            print("\nAgent Execution Results:")
            for agent_name, agent_result in result.get("agent_results", {}).items():
                print(
                    f"  - {agent_name}: {agent_result.get('status')} ({agent_result.get('processing_time', 'N/A')}s)"
                )

        cost_tracking = result.get("cost_tracking", {})
        if cost_tracking.get("total_cost_usd"):
            print(f"\nTotal Cost: ${cost_tracking.get('total_cost_usd', 0):.4f}")

    else:
        print(f"Error: {result.get('error')}")

    print("\nOutput Files:")
    print(f"  JSON Result: {json_output_path}")
    print("=" * 60)


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    main()
