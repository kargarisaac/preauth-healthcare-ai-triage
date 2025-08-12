#!/usr/bin/env python3
"""
Claude Analysis Service
Integrates Claude pre-authorization analysis system with FastAPI.

This service provides async wrapper around the Claude orchestrator,
handles patient history integration, and manages temporary file structures
required for the Claude multi-agent analysis system.
"""

import json
import shutil
import tempfile
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from loguru import logger

from api.services.patient_lookup_service import get_patient_lookup_service

# Provide an anthropic attribute for tests to patch
try:
    import anthropic  # type: ignore
except Exception:  # pragma: no cover

    class _DummyAnthropic:
        class AsyncAnthropic:  # minimal shim for tests to patch
            def __init__(self, *args, **kwargs):
                pass

    anthropic = _DummyAnthropic()  # type: ignore


class ClaudeAnalysisService:
    """
    Service for running Claude pre-authorization analysis with patient context.

    Provides async interface around Anthropic Claude for unit-test coverage.
    """

    def __init__(self):
        """Initialize Claude analysis service."""
        self.patient_lookup = get_patient_lookup_service()
        self.total_analyses_completed: int = 0

        # Check if Claude service is available
        self.claude_available = self._check_claude_availability()

        if self.claude_available:
            logger.info("Claude Analysis Service initialized successfully")
        else:
            logger.warning(
                "Claude orchestrator not available - analysis will be disabled"
            )

    def _check_claude_availability(self) -> bool:
        """Check if Anthropic API key is configured and client is importable."""
        return bool(os.environ.get("ANTHROPIC_API_KEY")) and hasattr(
            anthropic, "AsyncAnthropic"
        )

    async def analyze_patient_data(
        self,
        patient_id: str,
        patient_bundles: List[Dict[str, Any]],
        cost_limit_usd: float = 1.0,
        include_history: bool = False,
        enable_multi_agent: bool = False,
    ) -> Dict[str, Any]:
        """Analyze patient data with Claude. Returns analysis and cost tracking."""
        try:
            if not self.claude_available:
                return {
                    "success": False,
                    "patient_id": patient_id,
                    "error": "Claude analysis service is not available",
                    "timestamp": datetime.now().isoformat(),
                }

            if not patient_bundles:
                return {
                    "success": False,
                    "patient_id": patient_id,
                    "error": "No patient data provided",
                    "timestamp": datetime.now().isoformat(),
                }

            context = self.extract_clinical_context(patient_bundles)
            agent_role = "multi_agent" if enable_multi_agent else "clinical_analyzer"
            prompt = self.format_analysis_prompt(
                patient_id=patient_id,
                clinical_context=context,
                agent_role=agent_role,
            )

            api_key = os.environ.get("ANTHROPIC_API_KEY")
            client = anthropic.AsyncAnthropic(api_key=api_key)  # type: ignore

            total_input_tokens = 0
            total_output_tokens = 0
            analysis: Dict[str, Any] = {}

            if enable_multi_agent:
                roles = [
                    "clinical_analyzer",
                    "medical_reviewer",
                    "recommendation_agent",
                ]
                agent_results: List[Dict[str, Any]] = []
                for role in roles:
                    role_prompt = prompt + f"\n\nRole: {role}"
                    msg = await client.messages.create(  # type: ignore
                        model="claude-3-5-sonnet-20240620",
                        max_tokens=1000,
                        messages=[{"role": "user", "content": role_prompt}],
                    )
                    # Parse JSON payload from first content block
                    payload = {}
                    if getattr(msg, "content", None):
                        try:
                            payload = json.loads(getattr(msg.content[0], "text", "{}"))
                        except Exception:
                            payload = {"text": getattr(msg.content[0], "text", "")}
                    agent_results.append({"role": role, "result": payload})
                    total_input_tokens += (
                        getattr(getattr(msg, "usage", object()), "input_tokens", 0) or 0
                    )
                    total_output_tokens += (
                        getattr(getattr(msg, "usage", object()), "output_tokens", 0)
                        or 0
                    )

                analysis = {"agent_results": agent_results}
            else:
                msg = await client.messages.create(  # type: ignore
                    model="claude-3-5-sonnet-20240620",
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}],
                )
                payload = {}
                if getattr(msg, "content", None):
                    try:
                        payload = json.loads(getattr(msg.content[0], "text", "{}"))
                    except Exception:
                        payload = {"text": getattr(msg.content[0], "text", "")}
                analysis = payload
                total_input_tokens = (
                    getattr(getattr(msg, "usage", object()), "input_tokens", 0) or 0
                )
                total_output_tokens = (
                    getattr(getattr(msg, "usage", object()), "output_tokens", 0) or 0
                )

            # Very rough cost estimate for tests (no exact pricing dependency)
            cost_usd = ((total_input_tokens + total_output_tokens) / 1000.0) * 0.002

            result = {
                "success": True,
                "patient_id": patient_id,
                "analysis": analysis,
                "cost_usd": round(cost_usd, 6),
                "timestamp": datetime.now().isoformat(),
            }

            self.total_analyses_completed += 1
            return result

        except Exception as e:  # Surface API errors in tests
            logger.error(f"Claude analysis failed for patient {patient_id}: {e}")
            return {
                "success": False,
                "patient_id": patient_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def extract_clinical_context(self, bundles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract diagnosis/procedure codes and text context from bundles."""
        diagnosis_codes: List[str] = []
        procedure_codes: List[str] = []
        texts: List[str] = []
        for b in bundles:
            fhir = b.get("fhir_resources", {})
            for res in fhir.values():
                for d in res.get("diagnosis", []) or []:
                    code = d.get("code")
                    if code:
                        diagnosis_codes.append(code)
                for item in res.get("item", []) or []:
                    ps = item.get("productOrService", {})
                    code = ps.get("code")
                    if code:
                        procedure_codes.append(code)
            raw = b.get("raw_data", {})
            if raw:
                texts.append(str(raw))
        clinical_text = " \n".join(texts)
        return {
            "diagnosis_codes": list(dict.fromkeys(diagnosis_codes)),
            "procedure_codes": list(dict.fromkeys(procedure_codes)),
            "clinical_text": clinical_text,
            "patient_summary": "Auto-generated summary",
        }

    def format_analysis_prompt(
        self, patient_id: str, clinical_context: Dict[str, Any], agent_role: str
    ) -> str:
        """Format a simple prompt string for Claude input."""
        return (
            f"Patient ID: {patient_id}\n"
            f"Agent Role: {agent_role}\n"
            f"Diagnoses: {', '.join(clinical_context.get('diagnosis_codes', []))}\n"
            f"Procedures: {', '.join(clinical_context.get('procedure_codes', []))}\n"
            f"Context: {clinical_context.get('clinical_text', '')}"
        )

    def estimate_analysis_cost(self, bundle: Any) -> float:
        """
        Estimate cost for Claude analysis based on bundle complexity.

        Accepts a single bundle dict or a list of bundles.
        """
        base_cost = 0.15

        bundles: List[Dict[str, Any]] = bundle if isinstance(bundle, list) else [bundle]
        total_resources = 0
        total_raw_size = 0
        for b in bundles:
            fhir_resources = b.get("fhir_resources", {})
            total_resources += len(fhir_resources)
            total_raw_size += len(str(b.get("raw_data", {})))

        complexity_multiplier = 1.0 + (total_resources * 0.03)
        size_multiplier = 1.0 + min(total_raw_size / 15000, 0.3)
        estimated_cost = base_cost * complexity_multiplier * size_multiplier
        return round(min(estimated_cost, 2.0), 3)

    def get_analysis_status(self) -> Dict[str, Any]:
        """
        Get Claude analysis service status.
        """
        return {
            "claude_available": self.claude_available,
            "patient_index_size": len(self.patient_lookup.patient_index),
            "service_status": "ready" if self.claude_available else "disabled",
            "total_analyses_completed": self.total_analyses_completed,
            "timestamp": datetime.now().isoformat(),
        }


# Global service instance
_claude_analysis_service = None


def get_claude_analysis_service() -> ClaudeAnalysisService:
    """Get global Claude analysis service instance."""
    global _claude_analysis_service
    if _claude_analysis_service is None:
        _claude_analysis_service = ClaudeAnalysisService()
    return _claude_analysis_service
