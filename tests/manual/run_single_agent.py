#!/usr/bin/env python3
"""
Manual test: run a single agent end-to-end with real tools and LLM (no mocks).
Usage:
  uv run python tests/manual/run_single_agent.py --agent clinical-analyzer --xml data/dataset_2/synthetic_dataset/UAE_XML/Patient_007_eclaim.xml
"""

import argparse
from preauth_system.state import AgentResult, SharedContext
from preauth_system.utils import prepare_shared_context
from preauth_system.agents_openai import execute_openai_agent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("agent", type=str)
    args = parser.parse_args()

    # minimal fake shared context
    shared: SharedContext = {
        "xml_request": {"dummy": True},
        "patient_demographics": {},
        "medical_history": {},
        "clinical_data": {},
        "specialty": "general",
        "analysis_timestamp": "",
    }

    result: AgentResult = execute_openai_agent(args.agent, shared, previous_results={})
    print(result)


if __name__ == "__main__":
    main()
