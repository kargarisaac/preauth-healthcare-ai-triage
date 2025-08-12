import dspy
from preauth_system.dspy_config import get_module_lm, with_dspy_lm


class ClinicalSummary(dspy.Module):
    def __init__(self):
        super().__init__()
        self.lm = get_module_lm("clinical_summary")
        self.summarize = dspy.ChainOfThought("raw_data -> clinical_summary")

    def forward(self, raw_data):
        with with_dspy_lm(self.lm):
            return self.summarize(raw_data=raw_data)
