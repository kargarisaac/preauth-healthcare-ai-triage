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
from preauth_system.intake import process_pa_request
from preauth_system.dossier import DossierGenerator

# LangGraph workflow imports
from preauth_system.graph import compile_preauth_graph
from preauth_system.state import (
    create_initial_state,
    PreAuthState,
    get_all_agent_results,
)
from preauth_system.summary import build_clinical_summary, ClinicalSummary
from data_ingestion.etl import find_patient_by_emirates_id
from preauth_system.utils import prime_agent_definitions_cache


class PreAuthOrchestrator:
    """Main orchestrator for pre-authorization workflow using LangGraph exclusively."""

    def __init__(self):
        """Initialize the orchestrator with LangGraph workflow."""
        self.cache = get_preauth_cache()
        self.dossier_generator = DossierGenerator()

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
        xml_file_path: Optional[str] = None,
        patient_id: Optional[str] = None,
        xml_format: str = "eclaim",
        xml_content: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process pre-authorization request using LangGraph workflow with real data.

        Args:
            xml_file_path: Path to XML file to process
            patient_id: Optional patient identifier
            xml_format: XML format type (eclaim/shafafiya)

        Returns:
            Processing result with actual decision and workflow execution details
        """
        try:
            start_time = time.time()
            logger.info(
                f"Processing PA request for patient: {patient_id} using LangGraph workflow"
            )

            # 1. INTAKE - Process XML to canonical format (real data processing)
            if xml_content is not None:
                raw_xml_content = xml_content
                # Write to a temporary file to reuse existing file-based intake
                import tempfile

                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".xml", mode="w", encoding="utf-8"
                ) as tmp:
                    tmp.write(xml_content)
                    tmp_path = tmp.name
                xml_file_path = tmp_path
            elif xml_file_path is not None:
                with open(xml_file_path, "r", encoding="utf-8") as f:
                    raw_xml_content = f.read()
            else:
                raise ValueError("Either xml_content or xml_file_path must be provided")

            canonical_request = process_pa_request(xml_file_path, xml_format)
            emirates_id = canonical_request.patient.get("EmiratesIDNumber", "Unknown")
            logger.info(f"Intake completed for Emirates ID: {emirates_id}")

            # 2. CLINICAL SUMMARY - Build using real data
            patient_in_etl = find_patient_by_emirates_id(emirates_id)

            if patient_in_etl:
                clinical_summary = build_clinical_summary(
                    patient_in_etl, mode="deterministic"
                )
                logger.info(
                    f"Clinical summary built from ETL for {emirates_id}: {len(clinical_summary.primary_diagnoses)} diagnoses"
                )
            else:
                # Create clinical summary from XML data only
                clinical_summary = self._create_summary_from_xml(
                    canonical_request, emirates_id
                )
                logger.info(
                    f"Clinical summary created from XML for {emirates_id}: {len(clinical_summary.primary_diagnoses)} diagnoses"
                )

            # 3. LANGGRAPH WORKFLOW EXECUTION
            logger.info("Executing LangGraph workflow for agent-based analysis")
            workflow_result = self._execute_langgraph_workflow(
                xml_file_path, xml_format, emirates_id
            )

            if workflow_result.get("success"):
                # Extract the final state from LangGraph execution
                final_state = workflow_result["final_state"]

                # Generate dossier using LangGraph results
                dossier_html = self._generate_dossier_from_langgraph(
                    final_state, canonical_request, clinical_summary
                )

                processing_time = time.time() - start_time

                return {
                    "success": True,
                    "patient_id": emirates_id,
                    "workflow_execution": "langgraph",
                    "decision": final_state.get("final_decision", {}),
                    "clinical_summary": {
                        "primary_diagnoses": clinical_summary.primary_diagnoses,
                        "recent_procedures": len(clinical_summary.recent_procedures),
                        "current_medications": len(
                            clinical_summary.current_medications
                        ),
                    },
                    "agent_results": workflow_result.get("agent_results", {}),
                    "cost_tracking": final_state.get("cost_tracking", {}),
                    "processing_time_seconds": round(processing_time, 2),
                    "dossier_html": dossier_html,
                    "raw_data": {
                        "xml_content": raw_xml_content,
                        "canonical_request": canonical_request.__dict__
                        if hasattr(canonical_request, "__dict__")
                        else str(canonical_request),
                        "clinical_summary": clinical_summary.__dict__
                        if hasattr(clinical_summary, "__dict__")
                        else str(clinical_summary),
                    },
                }
            else:
                # LangGraph workflow failed
                error_msg = workflow_result.get("error", "Unknown workflow error")
                logger.error(f"LangGraph workflow failed: {error_msg}")
                return {
                    "success": False,
                    "error": f"LangGraph workflow failed: {error_msg}",
                    "patient_id": emirates_id,
                    "workflow_execution": "failed",
                }

        except Exception as e:
            logger.error(f"Processing failed: {e}")
            return {"success": False, "error": str(e), "patient_id": patient_id}

    def _execute_langgraph_workflow(
        self, xml_file_path: str, xml_format: str, emirates_id: str
    ) -> Dict[str, Any]:
        """Execute the LangGraph workflow for agent-based analysis."""
        try:
            # Create initial state for LangGraph
            analysis_id = (
                f"analysis_{emirates_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            initial_state = create_initial_state(xml_file_path, xml_format, analysis_id)

            logger.info(f"Starting LangGraph workflow execution for {emirates_id}")

            # Execute the workflow
            final_state = self.langgraph_workflow.invoke(initial_state)

            # Extract agent results for response
            agent_results = get_all_agent_results(final_state)

            logger.info(f"LangGraph workflow completed successfully for {emirates_id}")
            logger.info(f"Agent results: {list(agent_results.keys())}")

            return {
                "success": True,
                "final_state": final_state,
                "agent_results": {
                    name: {
                        "status": result.get("status"),
                        "success": result.get("success"),
                        "processing_time": result.get("processing_time_seconds"),
                        "response_summary": result.get("response", "")[:500] + "..."
                        if result.get("response")
                        and len(result.get("response", "")) > 500
                        else result.get("response", ""),
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

    def _generate_dossier_from_langgraph(
        self,
        final_state: PreAuthState,
        canonical_request,
        clinical_summary: ClinicalSummary,
    ) -> str:
        """Generate HTML dossier from LangGraph workflow results."""
        try:
            # Prepare processing result for dossier generation
            processing_result_for_dossier = {
                "patient_id": final_state.get("patient_info", {}).get(
                    "EmiratesIDNumber", "Unknown"
                ),
                "decision": final_state.get("final_decision", {}),
                "clinical_summary": {
                    "primary_diagnoses": clinical_summary.primary_diagnoses,
                    "age": clinical_summary.age,
                    "gender": clinical_summary.gender,
                },
                "agent_results": final_state,
                "cost_tracking": final_state.get("cost_tracking", {}),
                "processing_time": final_state.get("cost_tracking", {}).get(
                    "total_processing_time", 0
                ),
                "workflow_execution": "langgraph",
                "analysis_id": final_state.get("analysis_id"),
            }

            # Generate dossier; when no path is provided, return html content directly
            html_content = self.dossier_generator._create_basic_html(
                processing_result_for_dossier
            )
            return html_content

        except Exception as e:
            logger.error(f"Dossier generation from LangGraph failed: {e}")
            return f"<html><body><h1>Dossier Generation Error</h1><p>{str(e)}</p></body></html>"

    def _create_summary_from_xml(self, canonical_request, emirates_id: str):
        """Create a clinical summary from XML data when ETL data is not available."""
        patient = canonical_request.patient

        # Extract basic demographics
        age = self._calculate_age_from_birthdate(patient.get("DateOfBirth", ""))
        gender = patient.get("Gender", "Unknown")

        # Extract diagnoses from services
        primary_diagnoses = []
        for service in canonical_request.services:
            if service.get("diagnosis_code"):
                diagnosis = service["diagnosis_code"].get(
                    "description", "Unknown diagnosis"
                )
                if diagnosis not in primary_diagnoses:
                    primary_diagnoses.append(diagnosis)

        # Create minimal clinical summary
        return ClinicalSummary(
            patient_id=emirates_id,
            emirates_id=emirates_id,
            age=age,
            gender=gender,
            active_conditions=[
                {"name": diag, "status": "active"} for diag in primary_diagnoses
            ],
            primary_diagnoses=primary_diagnoses,
            current_medications=[],
            prior_treatments=[],
            treatment_responses=[],
            recent_labs=[],
            recent_imaging=[],
            recent_procedures=[],
            risk_factors=[],
            summary_date=time.strftime("%Y-%m-%d"),
            data_sources=["XML"],
            completeness_score=0.3,  # Low completeness as only XML data available
        )

    def _calculate_age_from_birthdate(self, birth_date_str: str) -> int:
        """Calculate age from birth date string."""
        if not birth_date_str:
            return 45  # Default age

        try:
            birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d")
            today = datetime.now()
            return (
                today.year
                - birth_date.year
                - ((today.month, today.day) < (birth_date.month, birth_date.day))
            )
        except (ValueError, AttributeError):
            return 45  # Default age if parsing fails


def process_demo_cases(
    orchestrator: PreAuthOrchestrator, demo_case: tuple
) -> Dict[str, Any]:
    """Process demo cases with real data processing."""

    try:
        patient_id, xml_path = demo_case
        results = {}
        if Path(xml_path).exists():
            # Process XML file directly
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

    # Create output folder if it doesn't exist
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    # Process specifically Patient_007 as requested
    xml_file_path = "data/dataset_2/synthetic_dataset/UAE_XML/Patient_007_eclaim.xml"
    patient_id = "Patient_007"

    logger.info(f"Processing {patient_id} with LangGraph workflow")

    # Process the request using LangGraph workflow
    result = orchestrator.process_request(
        xml_file_path=xml_file_path, patient_id=patient_id, xml_format="eclaim"
    )

    # Generate timestamp for unique file names
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save complete processing result as JSON
    json_output_path = output_dir / f"{patient_id}_result_{timestamp}.json"
    try:
        with open(json_output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str)
        logger.info(f"Processing result saved to: {json_output_path}")
        print(f"✅ Processing result saved to: {json_output_path}")
    except Exception as e:
        logger.error(f"Failed to save JSON result: {e}")
        print(f"❌ Failed to save JSON result: {e}")

    # Save HTML dossier
    html_output_path = output_dir / f"{patient_id}_dossier_{timestamp}.html"
    try:
        dossier_html = result.get(
            "dossier_html", "<html><body>No dossier generated</body></html>"
        )
        with open(html_output_path, "w", encoding="utf-8") as f:
            f.write(dossier_html)
        logger.info(f"HTML dossier saved to: {html_output_path}")
        print(f"✅ HTML dossier saved to: {html_output_path}")
    except Exception as e:
        logger.error(f"Failed to save HTML dossier: {e}")
        print(f"❌ Failed to save HTML dossier: {e}")

    # Print processing summary
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
    print(f"  HTML Dossier: {html_output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
