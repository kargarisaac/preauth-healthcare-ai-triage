#!/usr/bin/env python3
"""
Manual test: run a single agent end-to-end with real tools and LLM (no mocks).
Usage:
  uv run python tests/manual/run_single_agent.py --agent clinical-analyzer --xml data/dataset_2/synthetic_dataset/UAE_XML/Patient_007_eclaim.xml
"""

import argparse
from preauth_system.utils import (
    parse_xml,
    extract_patient_info,
    prepare_shared_context,
    execute_claude_agent,
)
from data_ingestion.etl import find_patient_by_emirates_id, get_patient_data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--agent",
        required=True,
        help="Agent name (clinical-analyzer|medication-specialist|risk-assessor|decision-maker|compliance-auditor)",
    )
    parser.add_argument("--xml", required=True, help="Path to eClaim XML file")
    args = parser.parse_args()

    xml = parse_xml(args.xml, "eclaim")
    info = extract_patient_info(xml, "eclaim")
    emirates_id = info["EmiratesIDNumber"]
    patient_id = find_patient_by_emirates_id(emirates_id)
    pdata = get_patient_data(patient_id)
    shared = prepare_shared_context(xml, info, pdata, specialty="pediatric")

    result = execute_claude_agent(args.agent, shared, previous_results={})
    print(f"Agent: {args.agent}")
    print(f"Success: {result['success']}")
    print(f"Time (s): {result.get('processing_time_seconds')}")
    print("\n=== Response (truncated) ===\n")
    print((result.get("response") or ""))


if __name__ == "__main__":
    main()
