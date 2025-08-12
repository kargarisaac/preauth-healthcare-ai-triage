import dspy
from preauth_system.dspy_config import get_module_lm, with_dspy_lm
from preauth_system.signatures import ClinicalRiskSignature, DataQualitySignature


class ClinicalSummary(dspy.Module):
    def __init__(self):
        super().__init__()
        self.lm = get_module_lm("clinical_summary")
        self.summarize = dspy.ChainOfThought("raw_data -> clinical_summary")

    def forward(self, raw_data):
        with with_dspy_lm(self.lm):
            return self.summarize(raw_data=raw_data)


class ClinicalRisk(dspy.Module):
    def __init__(self):
        super().__init__()
        self.lm = get_module_lm("clinical_risk")
        self.assess = dspy.ChainOfThought(ClinicalRiskSignature)

    def forward(self, timeline, medications, demographics):
        with with_dspy_lm(self.lm):
            return self.assess(
                timeline=timeline, medications=medications, demographics=demographics
            )


class DataQuality(dspy.Module):
    def __init__(self):
        super().__init__()
        self.lm = get_module_lm("data_quality")
        self.assess = dspy.ChainOfThought(DataQualitySignature)

    def forward(self, demographics, timeline, medications):
        with with_dspy_lm(self.lm):
            return self.assess(
                demographics=demographics, timeline=timeline, medications=medications
            )
