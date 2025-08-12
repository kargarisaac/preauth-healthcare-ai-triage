"""
Clinical Analyzer Agent Configuration and Class
Dynamically loaded by DSPyAgent base class
"""
import dspy
from datetime import datetime
from preauth_system.signatures import AgentResult
from preauth_system.signatures import ClinicalAnalysis
from preauth_system.dspy_config import get_openrouter_lm, with_dspy_lm
from preauth_system.dspy_tools import DEFAULT_TOOLS


# Agent metadata - simplified
METADATA = {
    "name": "clinical-analyzer",
    "max_iters": 5,
}


class ClinicalAnalyzer:
    """Clinical Analyzer Agent with centralized LM configuration and scoped DSPy usage."""

    def __init__(self):
        self.metadata = METADATA
        self.lm = get_openrouter_lm(agent_name=self.metadata["name"])
        self.react = dspy.ReAct(
            signature=ClinicalAnalysis,
            tools=DEFAULT_TOOLS,
            max_iters=self.metadata.get("max_iters", 5),
        )

    async def analyze(self, context, previous_results):
        """Execute agent analysis."""
        start_time = datetime.now()

        try:
            # Prepare structured patient data directly
            patient_data = {
                "patient_demographics": context.get("patient_demographics", {}),
                "medical_history": context.get("medical_history", {}),
                "clinical_data": context.get("clinical_data", {}),
                "requested_treatment": context.get("requested_treatment", {}),
            }

            with with_dspy_lm(self.lm):
                result = self.react(patient_data=patient_data)

            end_time = datetime.now()

            return AgentResult(
                agent_name=self.metadata["name"],
                status="completed",
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
                processing_time_seconds=(end_time - start_time).total_seconds(),
                response=result.analysis,
                usage={
                    "model": getattr(self.lm, "model", "openrouter/openai/gpt-oss-20b"),
                    "tokens": 0,
                },
                success=True,
                error=None,
                traceback=None,
            )

        except Exception as e:
            return AgentResult(
                agent_name=self.metadata["name"],
                status="failed",
                start_time=start_time.isoformat(),
                end_time=datetime.now().isoformat(),
                processing_time_seconds=None,
                response=None,
                usage={},
                success=False,
                error=str(e),
                traceback=None,
            )
