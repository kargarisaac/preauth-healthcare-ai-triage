"""
Agent configuration modules for DSPy-based pre-authorization system.

Each agent module contains:
- METADATA: Agent configuration and capabilities
- PROMPT_TEMPLATE: Jinja2 template for prompt rendering
- get_lm(): Function returning the language model for the agent
"""

# Agent module names
AVAILABLE_AGENTS = [
    "clinical_analyzer",
    "medication_specialist", 
    "risk_assessor",
    "decision_maker",
    "compliance_auditor"
]