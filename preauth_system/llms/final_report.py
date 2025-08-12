"""
Final Report Generation LLM Module
"""

import dspy
from preauth_system.dspy_config import get_module_lm, with_dspy_lm
from preauth_system.signatures import FinalReportSignature


class FinalReportResult:
    """Result container for final report"""

    def __init__(self, final_report: str):
        self.final_report = final_report


class FinalReport(dspy.Module):
    """LLM module for generating final reports"""

    def __init__(self):
        super().__init__()
        self.lm = get_module_lm("final_report")
        self.report_generator = dspy.ChainOfThought(FinalReportSignature)

    def forward(self, decision_data: str, agent_results: str) -> FinalReportResult:
        """Generate final report based on decision data and agent results"""
        with with_dspy_lm(self.lm):
            result = self.report_generator(
                decision_data=decision_data, agent_results=agent_results
            )
        # FinalReportSignature outputs a pydantic model with `content`
        return FinalReportResult(final_report=result.final_report.content or "")
