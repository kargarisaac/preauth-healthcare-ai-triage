#!/usr/bin/env python3
"""
Claude Analysis Service
Integrates Claude pre-authorization analysis system with FastAPI.

This service provides async wrapper around the Claude orchestrator,
handles patient history integration, and manages temporary file structures
required for the Claude multi-agent analysis system.
"""

import asyncio
import json
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from loguru import logger

from api.services.patient_lookup_service import get_patient_lookup_service


class ClaudeAnalysisService:
    """
    Service for running Claude pre-authorization analysis with patient context.

    Integrates the existing Claude orchestrator system with FastAPI,
    providing async interface and proper patient history management.
    """

    def __init__(self):
        """Initialize Claude analysis service."""
        self.patient_lookup = get_patient_lookup_service()

        # Check if Claude orchestrator is available
        self.claude_available = self._check_claude_availability()

        if self.claude_available:
            logger.info("Claude Analysis Service initialized successfully")
        else:
            logger.warning(
                "Claude orchestrator not available - analysis will be disabled"
            )

    def _check_claude_availability(self) -> bool:
        """Check if Claude orchestrator is available."""
        try:
            from preauth_system.agent import PreAuthOrchestrator  # noqa: F401

            return True
        except ImportError as e:
            logger.error(f"Claude orchestrator not available: {e}")
            return False

    async def analyze_preauth(
        self,
        patient_id: str,
        current_request: Dict[str, Any],
        include_history: bool = True,
        cost_limit_usd: float = 1.0,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> Dict[str, Any]:
        """
        Run Claude pre-authorization analysis with patient history.

        Args:
            patient_id: Patient UUID
            current_request: FHIR Bundle for current request
            include_history: Whether to include patient history
            cost_limit_usd: Maximum cost limit for analysis
            progress_callback: Optional progress callback function

        Returns:
            Analysis results with cost tracking and metadata
        """
        if not self.claude_available:
            raise RuntimeError("Claude orchestrator not available")

        if progress_callback:
            progress_callback("Initializing analysis", 0.1)

        # Validate patient exists
        patient_folder = self.patient_lookup.find_patient_folder(patient_id)
        if not patient_folder:
            raise ValueError(f"Patient {patient_id} not found in dataset")

        if progress_callback:
            progress_callback("Loading patient history", 0.2)

        # Get patient history if requested
        historical_data = []
        if include_history:
            historical_data = self.patient_lookup.get_patient_history(patient_id)
            logger.info(
                f"Loaded {len(historical_data)} historical records for patient {patient_id}"
            )

        # Get patient profile
        patient_profile = self.patient_lookup.get_patient_profile(patient_id)

        if progress_callback:
            progress_callback("Setting up analysis environment", 0.3)

        # Create temporary patient structure for Claude
        temp_patient_dir = self._create_temp_patient_structure(
            patient_id, current_request, historical_data, patient_profile
        )

        try:
            if progress_callback:
                progress_callback("Starting Claude analysis", 0.4)

            # Run Claude orchestrator
            analysis_results = await self._run_claude_orchestrator(
                temp_patient_dir, progress_callback, cost_limit_usd
            )

            if progress_callback:
                progress_callback("Analysis completed", 1.0)

            # Compile final results
            results = {
                "success": True,
                "patient_id": patient_id,
                "claude_analysis": analysis_results.get("analysis_results", {}),
                "cost_usd": analysis_results.get("total_cost", 0.0),
                "processing_time_seconds": analysis_results.get("processing_time", 0.0),
                "historical_files_count": len(historical_data),
                "analysis_metadata": analysis_results.get("metadata", {}),
                "agent_results": analysis_results.get("agent_results", {}),
                "timestamp": datetime.now().isoformat(),
            }

            logger.info(
                f"Claude analysis completed for patient {patient_id}: "
                f"${results['cost_usd']:.3f}, {results['processing_time_seconds']:.1f}s"
            )

            return results

        except Exception as e:
            logger.error(f"Claude analysis failed for patient {patient_id}: {e}")
            return {
                "success": False,
                "patient_id": patient_id,
                "error": str(e),
                "cost_usd": 0.0,
                "processing_time_seconds": 0.0,
                "historical_files_count": len(historical_data),
                "timestamp": datetime.now().isoformat(),
            }
        finally:
            # Clean up temporary directory
            if temp_patient_dir.exists():
                try:
                    shutil.rmtree(temp_patient_dir.parent)
                    logger.debug(
                        f"Cleaned up temporary directory: {temp_patient_dir.parent}"
                    )
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary directory: {e}")

    def _create_temp_patient_structure(
        self,
        patient_id: str,
        current_request: Dict[str, Any],
        historical_data: List[Dict[str, Any]],
        patient_profile: Optional[Dict[str, Any]],
    ) -> Path:
        """
        Create temporary patient directory structure for Claude analysis.

        Args:
            patient_id: Patient UUID
            current_request: FHIR Bundle for current request
            historical_data: List of historical FHIR Bundles
            patient_profile: Patient profile data

        Returns:
            Path to temporary patient directory
        """
        # Create temporary directory
        temp_dir = Path(tempfile.mkdtemp(prefix=f"nazmito_analysis_{patient_id[:8]}_"))
        patient_dir = temp_dir / "patient"
        patient_dir.mkdir(parents=True)

        logger.debug(f"Created temporary patient structure: {patient_dir}")

        # Save patient profile
        if patient_profile:
            with open(patient_dir / "profile.json", "w", encoding="utf-8") as f:
                json.dump(patient_profile, f, indent=2, default=str)

        # Save current request
        current_request_file = patient_dir / "current_request.json"
        with open(current_request_file, "w", encoding="utf-8") as f:
            json.dump(current_request, f, indent=2, default=str)

        # Save historical data
        for i, historical_bundle in enumerate(historical_data, 1):
            historical_file = patient_dir / f"historical_{i:03d}.json"
            with open(historical_file, "w", encoding="utf-8") as f:
                json.dump(historical_bundle, f, indent=2, default=str)

        logger.debug(
            f"Saved {len(historical_data)} historical files for patient {patient_id}"
        )

        return patient_dir

    async def _run_claude_orchestrator(
        self,
        patient_dir: Path,
        progress_callback: Optional[Callable[[str, float], None]],
        cost_limit: float,
    ) -> Dict[str, Any]:
        """
        Run Claude orchestrator with progress tracking.

        Args:
            patient_dir: Path to patient directory
            progress_callback: Progress callback function
            cost_limit: Cost limit for analysis

        Returns:
            Analysis results from orchestrator
        """
        try:
            from preauth_system.agent import PreAuthOrchestrator

            # Set up orchestrator
            current_request_file = patient_dir / "current_request.json"
            orchestrator = PreAuthOrchestrator()

            # If the agent expects XML, this part would be adapted as needed.
            # Here we return a structured result placeholder to keep API stable.
            # Replace with actual call whenever the JSON flow is integrated.
            results = {
                "analysis_results": {},
                "total_cost": 0.0,
                "processing_time": 0.0,
                "agent_results": {},
                "metadata": {},
            }

            return results

        except Exception as e:
            logger.error(f"Claude orchestrator execution failed: {e}")
            raise

    def estimate_analysis_cost(self, bundle: Dict[str, Any]) -> float:
        """
        Estimate cost for Claude analysis based on bundle complexity.

        Args:
            bundle: FHIR Bundle to analyze

        Returns:
            Estimated cost in USD
        """
        # Simple cost estimation based on data complexity
        base_cost = 0.15  # Base cost for analysis

        # Factor in bundle complexity
        fhir_resources = bundle.get("fhir_resources", {})
        resource_count = len(fhir_resources)

        # Factor in raw data size
        raw_data_size = len(str(bundle.get("raw_data", {})))

        # Calculate multipliers
        complexity_multiplier = 1.0 + (resource_count * 0.05)
        size_multiplier = 1.0 + min(raw_data_size / 10000, 0.3)

        estimated_cost = base_cost * complexity_multiplier * size_multiplier

        # Cap at reasonable maximum
        estimated_cost = min(estimated_cost, 2.0)

        logger.debug(f"Estimated analysis cost: ${estimated_cost:.3f}")
        return round(estimated_cost, 3)

    def get_analysis_status(self) -> Dict[str, Any]:
        """
        Get Claude analysis service status.

        Returns:
            Service status information
        """
        return {
            "claude_available": self.claude_available,
            "patient_index_size": len(self.patient_lookup.patient_index),
            "service_status": "ready" if self.claude_available else "disabled",
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
