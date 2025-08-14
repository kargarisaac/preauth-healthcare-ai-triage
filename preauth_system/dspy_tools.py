"""
Simple DSPy Tools - All tool functions in one place
"""


def get_diabetes_technology_guidelines_kb() -> str:
    """Tool: Diabetes Technology KB
    Use when the request involves continuous glucose monitoring, insulin pumps, or diabetes devices.
    Returns full Markdown text of guideline document. Cite relevant sections.
    Source: preauth_system/rag/kb/diabetes_technology_guidelines.md
    """
    with open(
        "preauth_system/rag/kb/diabetes_technology_guidelines.md", "r", encoding="utf-8"
    ) as f:
        return f.read()


def get_osteoarthritis_management_kb() -> str:
    """Tool: Osteoarthritis Management KB
    Use for knee OA conservative therapy criteria, imaging thresholds, and intervention sequencing.
    Returns full Markdown text of guideline document.
    Source: preauth_system/rag/kb/osteoarthritis_management.md
    """
    with open(
        "preauth_system/rag/kb/osteoarthritis_management.md", "r", encoding="utf-8"
    ) as f:
        return f.read()


def get_parkinsons_dbs_guidelines_kb() -> str:
    """Tool: Parkinson's DBS Guidelines KB
    Use for DBS candidacy, pre-operative assessment, and follow-up standards.
    Returns full Markdown text of guideline document.
    Source: preauth_system/rag/kb/parkinson_dbs_guidelines.md
    """
    with open(
        "preauth_system/rag/kb/parkinson_dbs_guidelines.md", "r", encoding="utf-8"
    ) as f:
        return f.read()


def get_diabetes_technology_policy() -> str:
    """Tool: Diabetes Technology Policy YAML
    Use first for diabetes device requests (e.g., CGM, pumps). Contains payer coverage criteria and documentation requirements.
    Returns full YAML text.
    Source: preauth_system/policy/policies/diabetes_technology.yaml
    """
    with open(
        "preauth_system/policy/policies/diabetes_technology.yaml", "r", encoding="utf-8"
    ) as f:
        return f.read()


def get_osteoarthritis_knee_intervention_policy() -> str:
    """Tool: Osteoarthritis Knee Intervention Policy YAML
    Use for knee OA interventions. Check conservative therapy duration, imaging requirements, and procedural criteria.
    Returns full YAML text.
    Source: preauth_system/policy/policies/osteoarthritis_knee_intervention.yaml
    """
    with open(
        "preauth_system/policy/policies/osteoarthritis_knee_intervention.yaml",
        "r",
        encoding="utf-8",
    ) as f:
        return f.read()


def get_parkinsons_dbs_policy() -> str:
    """Tool: Parkinson's DBS Policy YAML
    Use for Parkinson's disease cases involving DBS. Contains payer coverage and documentation rules.
    Returns full YAML text.
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
