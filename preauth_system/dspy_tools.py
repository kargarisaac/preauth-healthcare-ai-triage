"""
Simple DSPy Tools - All tool functions in one place
"""


def get_diabetes_technology_guidelines_kb() -> str:
    """Return the full text of the Diabetes Technology guidelines KB.
    Use to cite evidence or retrieve criteria related to CGM, insulin pumps, etc.
    Source: preauth_system/rag/kb/diabetes_technology_guidelines.md
    """
    with open(
        "preauth_system/rag/kb/diabetes_technology_guidelines.md", "r", encoding="utf-8"
    ) as f:
        return f.read()


def get_osteoarthritis_management_kb() -> str:
    """Return the full text of osteoarthritis management guidelines KB.
    Use to reference conservative management, imaging, and intervention criteria.
    Source: preauth_system/rag/kb/osteoarthritis_management.md
    """
    with open(
        "preauth_system/rag/kb/osteoarthritis_management.md", "r", encoding="utf-8"
    ) as f:
        return f.read()


def get_parkinsons_dbs_guidelines_kb() -> str:
    """Return the full text of Parkinson's DBS guidelines KB.
    Use to validate candidacy criteria, pre-op evaluation, and follow-up standards.
    Source: preauth_system/rag/kb/parkinson_dbs_guidelines.md
    """
    with open(
        "preauth_system/rag/kb/parkinson_dbs_guidelines.md", "r", encoding="utf-8"
    ) as f:
        return f.read()


def get_diabetes_technology_policy() -> str:
    """Return the diabetes technology policy YAML.
    Use to check payer coverage criteria and documentation requirements.
    Source: preauth_system/policy/policies/diabetes_technology.yaml
    """
    with open(
        "preauth_system/policy/policies/diabetes_technology.yaml", "r", encoding="utf-8"
    ) as f:
        return f.read()


def get_osteoarthritis_knee_intervention_policy() -> str:
    """Return the osteoarthritis knee intervention policy YAML.
    Use to verify coverage requirements for conservative therapy and procedures.
    Source: preauth_system/policy/policies/osteoarthritis_knee_intervention.yaml
    """
    with open(
        "preauth_system/policy/policies/osteoarthritis_knee_intervention.yaml",
        "r",
        encoding="utf-8",
    ) as f:
        return f.read()


def get_parkinsons_dbs_policy() -> str:
    """Return the Parkinson's DBS policy YAML.
    Use to validate coverage criteria and pre/post operative requirements.
    Source: preauth_system/policy/policies/parkinsons_dbs.yaml
    """
    with open(
        "preauth_system/policy/policies/parkinsons_dbs.yaml", "r", encoding="utf-8"
    ) as f:
        return f.read()


# Default tool set shared by all agents
DEFAULT_TOOLS = [
    get_diabetes_technology_guidelines_kb,
    get_osteoarthritis_management_kb,
    get_parkinsons_dbs_guidelines_kb,
    get_diabetes_technology_policy,
    get_osteoarthritis_knee_intervention_policy,
    get_parkinsons_dbs_policy,
]
