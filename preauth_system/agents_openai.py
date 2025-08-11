from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from preauth_system.state import AgentResult, SharedContext
from preauth_system.utils import (
    _build_agent_prompt,  # reuse existing prompt builder
    get_cached_agent_definitions,
    prime_agent_definitions_cache,
    get_config,
)
from preauth_system.pricing import calculate_cost_from_usage

# OpenAI Agents SDK
from agents import Agent as OAAgent, Runner


# Load config strictly from YAML via utils
_CFG = get_config()


@dataclass
class _TraceWriter:
    run_id: str

    def __post_init__(self) -> None:
        base_run_dir = os.environ.get("PREAUTH_RUN_DIR")
        if base_run_dir:
            traces_dir = Path(base_run_dir) / "traces"
        else:
            traces_dir = Path(
                (_CFG.get("tracing", {}) or {}).get(
                    "dir", str(Path("output") / "traces")
                )
            )
        traces_dir.mkdir(parents=True, exist_ok=True)
        self.path = traces_dir / f"{self.run_id}.jsonl"

    def write(self, event: str, **payload: Any) -> None:
        record = {
            "ts": datetime.utcnow().isoformat(),
            "event": event,
            **payload,
        }
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _build_openai_agent(
    *,
    agent_name: str,
    instructions: str,
    model: str,
    reasoning_effort: Optional[str],
    tools: List[Any],
) -> OAAgent:
    kwargs: Dict[str, Any] = {
        "name": agent_name,
        "instructions": instructions,
        "model": model,
    }
    # Only include reasoning_effort if supported by the SDK
    try:
        if (
            reasoning_effort is not None
            and "reasoning_effort" in OAAgent.__init__.__code__.co_varnames
        ):  # type: ignore
            kwargs["reasoning_effort"] = reasoning_effort
    except Exception:
        pass
    if tools:
        kwargs["tools"] = tools
    agent = OAAgent(**kwargs)
    return agent


async def _run_agent_async(
    agent: OAAgent, user_input: str, tracer: _TraceWriter
) -> Dict[str, Any]:
    tracer.write("agent_run_started", agent=agent.name)
    result = await Runner.run(agent, user_input)
    usage = getattr(result, "usage", {}) or {}
    try:
        final_output = result.final_output
    except Exception:
        final_output = getattr(result, "output", None) or ""
    tracer.write("agent_run_finished", agent=agent.name, usage=usage)
    return {"response": final_output, "usage": usage}


def _format_shared_context(
    shared_context: SharedContext, previous_results: Dict[str, AgentResult]
) -> str:
    # Leverage the same prompt builder by assembling a minimal structure
    # The builder uses shared_context and previous_results directly.
    return ""


def _resolve_agent_md(agent_name: str) -> Dict[str, Any]:
    agent_definitions = (
        get_cached_agent_definitions() or prime_agent_definitions_cache()
    )
    agent_def = agent_definitions.get(agent_name, {})
    if not agent_def:
        raise RuntimeError(f"Agent definition not found for {agent_name}")

    agents_cfg = _CFG.get("agents", {}) if isinstance(_CFG, dict) else {}
    model = agent_def.get("model") or agents_cfg.get("default_model") or "gpt-5"
    reasoning_effort = (
        agent_def.get("reasoning_effort")
        or agents_cfg.get("default_reasoning_effort")
        or None
    )
    tools = agent_def.get("tools", [])

    return {
        "instructions": agent_def.get("instructions", ""),
        "model": model,
        "reasoning_effort": reasoning_effort,
        "tools": tools,
        "name": agent_def.get("name") or agent_name,
    }


def _resolve_tools(tool_names: List[str]) -> List[Any]:
    from preauth_system.tools.agents_tools import get_openai_tools

    return get_openai_tools(tool_names)


def execute_openai_agent(
    agent_name: str,
    shared_context: SharedContext,
    previous_results: Dict[str, AgentResult],
) -> AgentResult:
    start_time = datetime.now()
    run_id = f"{agent_name}_{start_time.strftime('%Y%m%dT%H%M%S')}"
    tracer = _TraceWriter(run_id)
    try:
        agent_cfg = _resolve_agent_md(agent_name)
        prompt = _build_agent_prompt(
            agent_name, agent_cfg, shared_context, previous_results
        )

        tools = _resolve_tools(agent_cfg["tools"]) if agent_cfg.get("tools") else []
        agent = _build_openai_agent(
            agent_name=agent_cfg["name"],
            instructions=prompt,
            model=agent_cfg["model"],
            reasoning_effort=agent_cfg.get("reasoning_effort"),
            tools=tools,
        )
        tracer.write(
            "agent_started",
            agent=agent_name,
            model=agent_cfg["model"],
            tools=[getattr(t, "name", str(t)) for t in tools],
        )

        result = asyncio.run(
            _run_agent_async(agent, "Proceed with the analysis.", tracer)
        )
        raw_usage = result.get("usage", {})
        normalized_usage = {
            "model": agent_cfg["model"],
            "reasoning_effort": agent_cfg.get("reasoning_effort"),
            "input_tokens": raw_usage.get("prompt_tokens")
            or raw_usage.get("input_tokens", 0),
            "input_cached_tokens": raw_usage.get("cached_prompt_tokens", 0),
            "output_tokens": raw_usage.get("completion_tokens")
            or raw_usage.get("output_tokens", 0),
            "reasoning_tokens": raw_usage.get("reasoning_tokens", 0),
            "total_tokens": raw_usage.get("total_tokens", 0),
        }

        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        tracer.write(
            "agent_finished",
            agent=agent_name,
            processing_time_seconds=processing_time,
            usage=normalized_usage,
        )

        return AgentResult(
            agent_name=agent_name,
            status="completed",
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            processing_time_seconds=processing_time,
            response=result.get("response", ""),
            usage=normalized_usage,
            success=True,
            error=None,
            traceback=None,
        )
    except Exception as e:
        end_time = datetime.now()
        tracer.write("agent_error", agent=agent_name, error=str(e))
        return AgentResult(
            agent_name=agent_name,
            status="failed",
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            processing_time_seconds=None,
            response=None,
            usage={},
            success=False,
            error=str(e),
            traceback=None,
        )
