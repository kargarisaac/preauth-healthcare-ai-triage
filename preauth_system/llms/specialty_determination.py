"""
Specialty Determination LLM Module
"""

import dspy
from preauth_system.dspy_config import get_module_lm, with_dspy_lm
from preauth_system.signatures import SpecialtyDeterminationSignature


class SpecialtyDetermination(dspy.Module):
    """LLM module for determining medical specialty"""

    def __init__(self):
        super().__init__()
        self.lm = get_module_lm("specialty_determination")
        self.specialty_determiner = dspy.ChainOfThought(SpecialtyDeterminationSignature)

    def forward(self, patient_data: str, requested_services: str) -> str:
        """Determine medical specialty based on patient data and services"""
        with with_dspy_lm(self.lm):
            result = self.specialty_determiner(
                patient_data=patient_data, requested_services=requested_services
            )
        return result.specialty.specialty
