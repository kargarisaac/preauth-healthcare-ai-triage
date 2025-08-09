#!/usr/bin/env python3
"""
Manual test: exercise the healthcare policy tools and show how to start the MCP server.
Usage:
  uv run python tests/manual/run_mcp_tools.py

To run the MCP stdio server for agent use:
  uv run python preauth_system/tools/mcp_server.py
"""

import json
from preauth_system.tools.tools import (
    search_healthcare_policies,
    get_policy_information,
    validate_evidence_citation,
)


def main():
    print("🔧 RAG Tool Functions (direct Python calls):\n")

    print("1) Policy info (diabetes_tech):")
    res = get_policy_information("diabetes_tech")
    print(json.dumps(json.loads(res), indent=2)[:800] + "\n...")

    print("\n2) Search policies (diabetes CGM):")
    res = search_healthcare_policies(
        "diabetes CGM coverage criteria", top_k=3, policy_filter="diabetes_tech"
    )
    print(json.dumps(json.loads(res), indent=2)[:800] + "\n...")

    # If the previous search returned evidence, try validating the first snippet
    parsed = json.loads(res)
    evidence = parsed.get("data", {}).get("evidence", [])
    if evidence:
        first_id = evidence[0].get("snippet_id")
        print(f"\n3) Validate citation for snippet: {first_id}")
        res = validate_evidence_citation(first_id)
        print(json.dumps(json.loads(res), indent=2)[:800] + "\n...")

    print("\nTo start the MCP server for agent usage:")
    print("  uv run python preauth_system/tools/mcp_server.py")


if __name__ == "__main__":
    main()
