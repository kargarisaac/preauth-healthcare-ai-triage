#!/usr/bin/env python3
"""
Manual: force-call an MCP tool via Claude Code Python SDK and print tool events.

Examples:
  # Using our RAG tool (ensure MCP server is registered and running)
  uv run python -m tests.manual.run_mcp_tool_call \
    --tool search_healthcare_policies \
    --args '{"query":"diabetes CGM coverage criteria","top_k":2}'

  # Using another MCP server tool (replace with actual tool name and args)
  uv run python -m tests.manual.run_mcp_tool_call \
    --tool some_mcp_tool_name \
    --args '{"param":"value"}'
"""

import argparse
import asyncio
import json
from pathlib import Path

from claude_code_sdk import (
    query,
    ClaudeCodeOptions,
    AssistantMessage,
    TextBlock,
    ResultMessage,
)

# Optional richer blocks (if available in your SDK build)
try:
    from claude_code_sdk import ToolUseBlock, ToolResultBlock  # type: ignore
except Exception:  # pragma: no cover
    ToolUseBlock = None  # type: ignore
    ToolResultBlock = None  # type: ignore


def build_allowed_tools(tool: str) -> list[str]:
    """Allow both short and server-prefixed tool names."""
    # Common server prefixes look like: mcp__<server-name>__<tool>
    candidates = [tool]
    if "__" not in tool:
        candidates.append(f"mcp__langgraph-docs__{tool}")
        candidates.append(f"mcp__baml-docs__{tool}")
        candidates.append(f"mcp__kuzu-docs__{tool}")
    return candidates


async def run(tool: str, tool_args: dict, prompt_hint: str | None = None) -> int:
    # Compose a strict prompt to bias the model to call the tool
    if not prompt_hint:
        prompt = (
            f"You MUST call the tool '{tool}' exactly once with the given JSON args: "
            f"{json.dumps(tool_args)}. Do not answer without using the tool."
        )
    else:
        prompt = (
            f"{prompt_hint}\n\nNow call the tool '{tool}' with args: "
            f"{json.dumps(tool_args)} and return only the tool result."
        )

    options = ClaudeCodeOptions(
        cwd=str(Path.cwd()),
        max_turns=5,
        allowed_tools=build_allowed_tools(tool),  # include prefixed names too
        permission_mode="bypassPermissions",
    )

    saw_tool = False
    saw_result = False

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"[assistant] {block.text[:500]}")
                if ToolUseBlock and isinstance(block, ToolUseBlock):  # type: ignore
                    saw_tool = True
                    print(
                        f"[tool_used] name={getattr(block, 'name', None)} input={getattr(block, 'input', None)}"
                    )
                if ToolResultBlock and isinstance(block, ToolResultBlock):  # type: ignore
                    saw_result = True
                    print(
                        f"[tool_result] name={getattr(block, 'name', None)} output={getattr(block, 'output', None)}"
                    )
        if isinstance(message, ResultMessage):
            usage = getattr(message, "usage", None) or {}
            print(f"[usage] {usage}")

    # Heuristic: if SDK didn’t emit ToolResultBlock, we still consider success if we saw ToolUse
    if saw_tool:
        return 0
    return 1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tool", required=True, help="Exact tool name exposed via MCP")
    parser.add_argument("--args", default="{}", help="JSON string of tool arguments")
    parser.add_argument(
        "--hint",
        default=None,
        help="Optional natural language hint to guide the model",
    )
    args = parser.parse_args()

    try:
        tool_args = json.loads(args.args)
        if not isinstance(tool_args, dict):
            raise ValueError("--args must be a JSON object")
    except Exception as e:
        raise SystemExit(f"Invalid --args JSON: {e}")

    exit_code = asyncio.run(run(args.tool, tool_args, args.hint))
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
