"""
Pure Python asyncio orchestrator to replace LangGraph
"""

import asyncio
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger

# Core system imports
from preauth_system.utils import (
    parse_xml,
    extract_patient_info,
    prepare_agent_execution_context,
)
from preauth_system.etl import (
    create_unified_patient_record,
    find_patient_by_emirates_id,
)

# Agent imports (direct)
from preauth_system.agents.clinical_analyzer import ClinicalAnalyzer
from preauth_system.agents.medication_specialist import MedicationSpecialist
from preauth_system.agents.risk_assessor import RiskAssessor
from preauth_system.agents.decision_maker import DecisionMaker
from preauth_system.agents.compliance_auditor import ComplianceAuditor
from preauth_system.signatures import AgentResult

# LLM modules
from preauth_system.llms.specialty_determination import SpecialtyDetermination
from preauth_system.llms.final_report import FinalReport
from preauth_system.llms.clinical_summary import (
    ClinicalSummary as ClinicalSummaryModule,
)
from preauth_system.dspy_config import configure_dspy_default


class PreAuthOrchestrator:
    """Pure asyncio orchestrator for pre-authorization workflow"""

    def __init__(self):
        """Initialize orchestrator with all agents and LLM modules"""  # Warm agent definitions cache once at startup to avoid repeated loads
        # Ensure a default LM is globally configured to avoid early 'No LM is loaded' errors
        configure_dspy_default()

        # Initialize agents
        self.agents = {
            "clinical-analyzer": ClinicalAnalyzer(),
            "medication-specialist": MedicationSpecialist(),
            "risk-assessor": RiskAssessor(),
            "decision-maker": DecisionMaker(),
            "compliance-auditor": ComplianceAuditor(),
        }

        # LLM modules
        self.specialty_llm = SpecialtyDetermination()
        self.report_llm = FinalReport()
        self.clinical_summary_llm = ClinicalSummaryModule()

        logger.info("Initialized PreAuth Orchestrator with pure asyncio workflow")

    async def process_request_async(self, initial_state: Dict) -> Dict:
        """Main orchestration method - replaces LangGraph workflow"""
        start_time = datetime.now()

        try:
            logger.info("Starting asyncio workflow execution")

            # Data preparation
            context = await self._prepare_context(initial_state)
            logger.info("Data preparation completed")

            # Phase 1: Clinical + Medication (parallel)
            logger.info("Starting Phase 1: Clinical and Medication Analysis...")
            phase1_results = await self._execute_phase1(context)
            logger.info(f"Phase 1 completed with agents: {list(phase1_results.keys())}")

            # Phase 2: Risk Assessment
            logger.info("Starting Phase 2: Risk Assessment...")
            risk_result = await self._execute_phase2(context, phase1_results)
            logger.info(f"Phase 2 completed with agents: {list(risk_result.keys())}")

            # Phase 3: Decision + Compliance (parallel)
            logger.info("Starting Phase 3: Decision Making and Compliance...")
            all_previous = {**phase1_results, **risk_result}
            phase3_results = await self._execute_phase3(context, all_previous)
            logger.info(f"Phase 3 completed with agents: {list(phase3_results.keys())}")

            # Combine all results
            all_results = {**phase1_results, **risk_result, **phase3_results}

            # Generate final decision and report
            final_decision = await self._finalize_decision(context, all_results)

            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()

            logger.info(
                f"Asyncio workflow completed successfully in {processing_time:.2f}s"
            )

            return {
                "success": True,
                "workflow_complete": True,
                "workflow_execution": "asyncio",
                "processing_time": processing_time,
                "agent_results": {
                    name: {
                        "status": result.get("status"),
                        "success": result.get("success"),
                        "processing_time": result.get("processing_time_seconds"),
                        "response": result.get("response", ""),
                    }
                    for name, result in all_results.items()
                },
                "final_decision": final_decision,
                "cost_tracking": self._calculate_costs(all_results),
                "timestamp": end_time.isoformat(),
            }

        except Exception as e:
            logger.error(f"Asyncio workflow execution failed: {e}")
            import traceback

            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "workflow_execution": "asyncio_failed",
                "agent_results": {},
                "timestamp": datetime.now().isoformat(),
            }

    async def _prepare_context(self, state: Dict) -> Dict:
        """Prepare context for agents"""
        try:
            # Parse XML and extract patient info
            xml_data = parse_xml(
                state["xml_file_path"], state.get("xml_format", "eclaim")
            )
            patient_info = extract_patient_info(
                xml_data, state.get("xml_format", "eclaim")
            )

            # Find patient by Emirates ID
            patient_id = find_patient_by_emirates_id(patient_info["EmiratesIDNumber"])

            if not patient_id:
                raise ValueError(
                    f"Patient not found for Emirates ID: {patient_info['EmiratesIDNumber']}"
                )

            # Create unified patient record
            unified_patient_record = create_unified_patient_record(
                patient_id=patient_id,
                xml_request_data=xml_data,
                xml_patient_info=patient_info,
            )

            # Prepare agent context
            agent_execution_context = prepare_agent_execution_context(
                unified_patient_record
            )

            return {
                "xml_file_path": state["xml_file_path"],
                "xml_format": state.get("xml_format", "eclaim"),
                "xml_data": xml_data,
                "patient_info": patient_info,
                "unified_patient_record": unified_patient_record,
                "agent_execution_context": agent_execution_context,
                "processing_mode": state.get("processing_mode", "hybrid"),
                "patient_data": unified_patient_record,
            }
        except Exception as e:
            logger.error(f"Data preparation failed: {e}")
            raise

    async def _execute_phase1(self, context: Dict) -> Dict[str, AgentResult]:
        """Execute clinical and medication analysis in parallel"""
        tasks = [
            self.agents["clinical-analyzer"].analyze(context, {}),
            self.agents["medication-specialist"].analyze(context, {}),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            "clinical-analyzer": results[0]
            if not isinstance(results[0], Exception)
            else self._error_result("clinical-analyzer", results[0]),
            "medication-specialist": results[1]
            if not isinstance(results[1], Exception)
            else self._error_result("medication-specialist", results[1]),
        }

    async def _execute_phase2(
        self, context: Dict, previous: Dict
    ) -> Dict[str, AgentResult]:
        """Execute risk assessment"""
        try:
            result = await self.agents["risk-assessor"].analyze(context, previous)
            return {"risk-assessor": result}
        except Exception as e:
            return {"risk-assessor": self._error_result("risk-assessor", e)}

    async def _execute_phase3(
        self, context: Dict, previous: Dict
    ) -> Dict[str, AgentResult]:
        """Execute decision and compliance in parallel"""
        tasks = [
            self.agents["decision-maker"].analyze(context, previous),
            self.agents["compliance-auditor"].analyze(context, previous),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            "decision-maker": results[0]
            if not isinstance(results[0], Exception)
            else self._error_result("decision-maker", results[0]),
            "compliance-auditor": results[1]
            if not isinstance(results[1], Exception)
            else self._error_result("compliance-auditor", results[1]),
        }

    async def _finalize_decision(self, context: Dict, all_results: Dict) -> Dict:
        """Generate final decision based on agent results and produce final report."""
        try:
            # Parse decision from decision-maker agent (expects JSON per signatures)
            decision_text = all_results.get("decision-maker", {}).get("response", "{}")
            try:
                decision_obj = json.loads(decision_text)
            except Exception:
                decision_obj = {
                    "decision": "REQUIRES_REVIEW",
                    "confidence": 0.0,
                    "rationale": decision_text,
                }

            # Generate clinical summary via LLM module
            try:
                raw_summary_input = json.dumps(
                    context.get("agent_execution_context", {}),
                    default=str,
                )
                summary_pred = self.clinical_summary_llm(raw_data=raw_summary_input)
                clinical_summary_text = getattr(
                    summary_pred, "clinical_summary", None
                ) or str(summary_pred)
            except Exception:
                clinical_summary_text = None

            # Generate final report content using LLM module
            decision_data = json.dumps(
                {
                    "patient_info": context.get("patient_info", {}),
                    "xml_data": context.get("xml_data", {}),
                    "decision": decision_obj,
                    "clinical_summary": clinical_summary_text,
                },
                default=str,
            )
            agent_results = json.dumps(
                {k: v.get("response", None) for k, v in all_results.items()},
                default=str,
            )
            report = self.report_llm(
                decision_data=decision_data, agent_results=agent_results
            )

            # Assemble final decision payload
            file_path = context["xml_data"].get("file_path", "default")
            auth_number = f"AUTH-2025-{datetime.now().strftime('%Y%m%d')}-{abs(hash(file_path)) % 10000:04d}"

            return {
                "decision": decision_obj.get("decision", "REQUIRES_REVIEW"),
                "confidence": decision_obj.get("confidence", 0.0),
                "authorization_number": auth_number,
                "valid_days": 90,
                "conditions": decision_obj.get("conditions", []),
                "rationale": decision_obj.get("rationale", ""),
                "agent_based": True,
                "report": getattr(report, "final_report", None) and report.final_report,
                "clinical_summary": clinical_summary_text,
            }

        except Exception as e:
            logger.error(f"Final decision generation failed: {e}")
            return {
                "decision": "REQUIRES_REVIEW",
                "confidence": 0.0,
                "error": str(e),
                "agent_based": False,
            }

    def _error_result(self, agent_name: str, error: Exception) -> AgentResult:
        """Create error result for failed agent"""
        return AgentResult(
            agent_name=agent_name,
            status="failed",
            start_time=datetime.now().isoformat(),
            end_time=datetime.now().isoformat(),
            processing_time_seconds=0,
            response=None,
            usage={},
            success=False,
            error=str(error),
            traceback=None,
        )

    def _calculate_costs(self, results: Dict) -> Dict:
        """Calculate cost tracking info"""
        total_cost = 0.0
        token_usage_by_agent = {}

        for agent_name, result in results.items():
            usage = result.get("usage", {})
            cost = usage.get("cost_usd", 0.0)
            total_cost += cost
            token_usage_by_agent[agent_name] = usage

        return {
            "total_cost_usd": round(total_cost, 6),
            "token_usage_by_agent": token_usage_by_agent,
            "processing_end": datetime.now().isoformat(),
            "agent_count": len(results),
            "cost_optimization_notes": [],
        }

    # API-compatible method for XML content processing
    def process_request(
        self,
        xml_content: Optional[str] = None,
        xml_file_path: Optional[str] = None,
        patient_id: Optional[str] = None,
        xml_format: str = "eclaim",
    ) -> Dict[str, Any]:
        """
        Process pre-authorization request - API-compatible method that handles both content and file paths
        """
        try:
            # Handle XML content by writing to temporary file
            if xml_content and not xml_file_path:
                import tempfile

                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".xml", delete=False, encoding="utf-8"
                ) as temp_file:
                    temp_file.write(xml_content)
                    xml_file_path = temp_file.name

                try:
                    result = self.process_request_sync(
                        xml_file_path, patient_id, xml_format
                    )
                finally:
                    # Clean up temp file
                    import os

                    try:
                        os.unlink(xml_file_path)
                    except Exception:
                        pass
                return result
            elif xml_file_path:
                return self.process_request_sync(xml_file_path, patient_id, xml_format)
            else:
                raise ValueError("Either xml_content or xml_file_path must be provided")

        except Exception as e:
            logger.error(f"Processing failed: {e}")
            return {"success": False, "error": str(e), "patient_id": patient_id}

    # Legacy synchronous interface for backward compatibility
    def process_request_sync(
        self,
        xml_file_path: str,
        patient_id: Optional[str] = None,
        xml_format: str = "eclaim",
    ) -> Dict[str, Any]:
        """
        Process pre-authorization request - synchronous wrapper for async method
        """
        try:
            start_time = time.time()
            logger.info(
                f"Processing PA request for patient: {patient_id} using asyncio workflow"
            )

            # Prepare initial state
            initial_state = {
                "xml_file_path": xml_file_path,
                "xml_format": xml_format,
                "processing_mode": "hybrid",
            }

            # Execute async workflow
            workflow_result = asyncio.run(self.process_request_async(initial_state))

            if workflow_result.get("success"):
                processing_time = time.time() - start_time
                decision_obj = workflow_result.get("final_decision", {})

                # Try to get Emirates ID from result, fallback to patient_id
                emirates_id = patient_id or "Unknown"

                return {
                    "success": True,
                    "patient_id": emirates_id,
                    "workflow_execution": "asyncio",
                    "decision": decision_obj,
                    "agent_results": workflow_result.get("agent_results", {}),
                    "cost_tracking": workflow_result.get("cost_tracking", {}),
                    "processing_time_seconds": round(processing_time, 2),
                }
            else:
                error_msg = workflow_result.get("error", "Unknown workflow error")
                logger.error(f"Asyncio workflow failed: {error_msg}")
                return {
                    "success": False,
                    "error": f"Asyncio workflow failed: {error_msg}",
                    "patient_id": patient_id,
                    "workflow_execution": "asyncio_failed",
                }

        except Exception as e:
            logger.error(f"Processing failed: {e}")
            return {"success": False, "error": str(e), "patient_id": patient_id}


# Convenience function to maintain API compatibility
async def process_preauth_request(initial_state: Dict) -> Dict:
    """Process pre-authorization request - main entry point"""
    orchestrator = PreAuthOrchestrator()
    return await orchestrator.process_request_async(initial_state)


def process_demo_cases(
    orchestrator: PreAuthOrchestrator, demo_case: tuple
) -> Dict[str, Any]:
    """Process demo cases with real data processing."""
    try:
        patient_id, xml_path = demo_case
        results = {}
        if Path(xml_path).exists():
            result = orchestrator.process_request_sync(xml_path, patient_id, "eclaim")
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

    logger.info(f"Processing {patient_id} with asyncio workflow")

    result = orchestrator.process_request_sync(
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
