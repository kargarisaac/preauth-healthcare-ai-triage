import os
import dspy
from contextlib import contextmanager
from preauth_system.utils import get_config
from typing import Optional

try:
    from dspy.adapters.baml_adapter import BAMLAdapter  # type: ignore
except Exception:  # pragma: no cover
    BAMLAdapter = None  # type: ignore


def _resolve_model_name(
    agent_name: Optional[str] = None, module_name: Optional[str] = None
) -> str:
    cfg = get_config() or {}
    llm_cfg = cfg.get("llm") or {}
    # New preferred default
    default_model = (
        llm_cfg.get("default_model")
        or llm_cfg.get("model")
        or "openrouter/openai/gpt-oss-20b"
    )
    # Agent override
    if agent_name:
        agent_entry = (llm_cfg.get("agents") or {}).get(agent_name) or {}
        if agent_entry.get("model"):
            return agent_entry["model"]
    # Module override
    if module_name:
        module_entry = (llm_cfg.get("modules") or {}).get(module_name) or {}
        if module_entry.get("model"):
            return module_entry["model"]
    return default_model


def get_openrouter_lm(
    model: str | None = None,
    cache: bool = True,
    *,
    agent_name: Optional[str] = None,
    module_name: Optional[str] = None,
) -> dspy.LM:
    """Get OpenRouter LM instance based on central config or override.
    Resolution order: explicit model arg > per-agent > per-module > default.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY environment variable required")

    model_name = model or _resolve_model_name(
        agent_name=agent_name, module_name=module_name
    )

    return dspy.LM(
        model=model_name,
        api_key=api_key,
        cache=cache,
    )


def configure_dspy_default():
    """Configure DSPy with a default LM read from config.yaml.
    Use sparingly; prefer per-call scoping with with_dspy_lm().
    """
    try:
        lm = get_openrouter_lm()
        if BAMLAdapter is not None:
            dspy.configure(lm=lm, adapter=BAMLAdapter())
        else:
            dspy.configure(lm=lm)
    except Exception:
        # Last resort - no global config
        pass


@contextmanager
def with_dspy_lm(lm: dspy.LM):
    """Context manager to scope dspy.configure to a specific LM without global side effects."""
    try:
        if BAMLAdapter is not None:
            dspy.configure(lm=lm, adapter=BAMLAdapter())
        else:
            dspy.configure(lm=lm)
        yield
    finally:
        pass


# Convenience helpers


def get_agent_lm(agent_name: str, cache: bool = True) -> dspy.LM:
    return get_openrouter_lm(cache=cache, agent_name=agent_name)


def get_module_lm(module_name: str, cache: bool = True) -> dspy.LM:
    return get_openrouter_lm(cache=cache, module_name=module_name)
