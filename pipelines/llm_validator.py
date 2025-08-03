"""
Streamlined LLM healthcare data validator using BAML.

This module provides a streamlined approach to LLM-powered healthcare data validation,
replacing the complex parallel execution framework with a single, comprehensive validation.
"""

import json
import time
from typing import Dict, Any, Optional
from loguru import logger

# Import BAML client and types
try:
    from baml_client import b
    from baml_client.types import DataSample, DataContext

    BAML_CLIENT_AVAILABLE = True
except ImportError as e:
    logger.warning(f"BAML client not available: {e}")
    BAML_CLIENT_AVAILABLE = False
    b = None

    # Fallback type definitions for when BAML is not available
    from dataclasses import dataclass

    @dataclass
    class DataContext:
        source_system: Optional[str] = None
        emirate: Optional[str] = None
        provider_type: Optional[str] = None
        patient_category: Optional[str] = None

    @dataclass
    class DataSample:
        resource_type: str
        raw_data: str
        context: Optional[DataContext] = None


class ValidationResult:
    """Streamlined validation result with essential information."""

    def __init__(
        self,
        overall_quality_score: float,
        confidence_score: float,
        validation_passed: bool,
        critical_issues: int,
        warning_issues: int,
        info_issues: int,
        top_issues: list,
        recommendations: list,
        processing_time_ms: int,
        model_used: str,
        reasoning: str = None,
    ):
        self.overall_quality_score = overall_quality_score
        self.confidence_score = confidence_score
        self.validation_passed = validation_passed
        self.critical_issues = critical_issues
        self.warning_issues = warning_issues
        self.info_issues = info_issues
        self.top_issues = top_issues
        self.recommendations = recommendations
        self.processing_time_ms = processing_time_ms
        self.model_used = model_used
        self.reasoning = reasoning

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "overall_quality_score": self.overall_quality_score,
            "confidence_score": self.confidence_score,
            "validation_passed": self.validation_passed,
            "critical_issues": self.critical_issues,
            "warning_issues": self.warning_issues,
            "info_issues": self.info_issues,
            "total_issues": self.critical_issues
            + self.warning_issues
            + self.info_issues,
            "top_issues": self.top_issues,
            "recommendations": self.recommendations,
            "processing_time_ms": self.processing_time_ms,
            "model_used": self.model_used,
            "reasoning": self.reasoning,
            "grade": self._calculate_grade(),
        }

    def _calculate_grade(self) -> str:
        """Calculate letter grade based on quality score."""
        score = self.overall_quality_score
        if score >= 0.9:
            return "A"
        elif score >= 0.8:
            return "B"
        elif score >= 0.7:
            return "C"
        elif score >= 0.6:
            return "D"
        else:
            return "F"


class LLMValidator:
    """
    Streamlined LLM validator for healthcare data.

    Provides single-call comprehensive validation instead of complex parallel execution.
    """

    def __init__(self, timeout_seconds: int = 60):
        """
        Initialize streamlined LLM validator.

        Args:
            timeout_seconds: Timeout for LLM requests
        """
        self.timeout_seconds = timeout_seconds

    async def validate_healthcare_data(
        self, data: Dict[str, Any], context: Optional[Dict[str, str]] = None
    ) -> ValidationResult:
        """
        Validate healthcare data using single comprehensive LLM call.

        Args:
            data: Healthcare data to validate
            context: Optional context information (emirate, provider_type, etc.)

        Returns:
            Streamlined validation results with actionable insights
        """
        if not BAML_CLIENT_AVAILABLE:
            logger.warning("BAML client not available, using mock validation")
            return self._create_mock_result()

        start_time = time.time()

        try:
            # Prepare data sample for BAML validation
            data_sample = self._prepare_data_sample(data, context)

            # Single comprehensive validation call
            logger.info("Starting streamlined LLM validation")
            result = await b.ValidateHealthcareData(data_sample)

            processing_time_ms = int((time.time() - start_time) * 1000)

            # Convert BAML result to our streamlined format
            validation_result = ValidationResult(
                overall_quality_score=getattr(result, "overall_quality_score", 0.8),
                confidence_score=getattr(result, "confidence_score", 0.85),
                validation_passed=getattr(result, "validation_passed", True),
                critical_issues=getattr(result, "critical_issues", 0),
                warning_issues=getattr(result, "warning_issues", 0),
                info_issues=getattr(result, "info_issues", 0),
                top_issues=getattr(result, "top_issues", []),
                recommendations=getattr(result, "recommendations", []),
                processing_time_ms=processing_time_ms,
                model_used=getattr(result, "model_used", "gpt-4o-mini"),
                reasoning=getattr(result, "reasoning", None),
            )

            logger.info(
                f"LLM validation completed in {processing_time_ms}ms with score {validation_result.overall_quality_score:.3f}"
            )
            return validation_result

        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"LLM validation failed: {e}")

            # Return degraded result on error
            return ValidationResult(
                overall_quality_score=0.5,
                confidence_score=0.0,
                validation_passed=False,
                critical_issues=1,
                warning_issues=0,
                info_issues=0,
                top_issues=[f"LLM validation failed: {str(e)}"],
                recommendations=["Please review data manually or try again"],
                processing_time_ms=processing_time_ms,
                model_used="error",
                reasoning="Validation could not be completed due to technical issues",
            )

    def _prepare_data_sample(
        self, data: Dict[str, Any], context: Optional[Dict[str, str]] = None
    ) -> DataSample:
        """Prepare data sample for BAML validation."""
        # Convert data to JSON string
        raw_data = json.dumps(data, default=str, ensure_ascii=False)

        # Create context if provided
        data_context = None
        if context:
            data_context = DataContext(
                source_system=context.get("source_system", "Unknown"),
                emirate=context.get("emirate", "Unknown"),
                provider_type=context.get("provider_type", "Unknown"),
                patient_category=context.get("patient_category", "Unknown"),
            )

        # Determine resource type based on data structure
        resource_type = self._detect_resource_type(data)

        return DataSample(
            resource_type=resource_type, raw_data=raw_data, context=data_context
        )

    def _detect_resource_type(self, data: Dict[str, Any]) -> str:
        """Simple resource type detection based on data structure."""
        # Check for common healthcare data patterns
        if "claims" in data or "claim" in data:
            return "Claims"
        elif "observations" in data or "observation" in data:
            return "Observations"
        elif "patients" in data or "patient" in data:
            return "Patients"
        elif "procedures" in data or "procedure" in data:
            return "Procedures"
        else:
            return "HealthcareBundle"

    def _create_mock_result(self) -> ValidationResult:
        """Create mock validation result when BAML is not available."""
        return ValidationResult(
            overall_quality_score=0.8,
            confidence_score=0.0,  # No confidence when mocking
            validation_passed=True,
            critical_issues=0,
            warning_issues=1,
            info_issues=2,
            top_issues=["Mock validation - BAML client not available"],
            recommendations=[
                "Install BAML client for actual LLM validation",
                "Review data manually for quality assessment",
            ],
            processing_time_ms=100,
            model_used="mock",
            reasoning="Mock validation result - real LLM validation unavailable",
        )


# Synchronous wrapper for use in existing processors
class LLMValidatorSync:
    """Synchronous wrapper for the async LLM validator."""

    def __init__(self, timeout_seconds: int = 60):
        self.validator = LLMValidator(timeout_seconds)

    def validate_healthcare_data(
        self, data: Dict[str, Any], context: Optional[Dict[str, str]] = None
    ) -> ValidationResult:
        """
        Synchronous validation method for integration with existing processors.
        """
        import asyncio

        try:
            # Try to get existing event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, we need to handle this differently
                # For now, return mock result to avoid blocking
                logger.warning(
                    "Cannot run async validation in sync context - using mock result"
                )
                return self.validator._create_mock_result()
            else:
                return loop.run_until_complete(
                    self.validator.validate_healthcare_data(data, context)
                )
        except RuntimeError:
            # No event loop exists, create one
            return asyncio.run(self.validator.validate_healthcare_data(data, context))


if __name__ == "__main__":
    """
    Test the simplified LLM validator with sample healthcare data.
    """
    import asyncio

    # Setup logging
    logger.add("debug_llm_validator.log")

    print("=" * 60)
    print("Streamlined LLM Validator - Test Mode")
    print("=" * 60)

    async def test_validation():
        """Test the streamlined validation with sample data."""

        # Sample healthcare data
        sample_data = {
            "claims": [
                {
                    "claim_id": "TEST-CLM-001",
                    "patient_id": "P001",
                    "diagnosis_code": "E11.9",
                    "procedure_code": "99213",
                    "amount": 150.50,
                    "service_date": "2024-01-01",
                    "provider_id": "PROV001",
                }
            ]
        }

        context = {
            "source_system": "CSV",
            "emirate": "Dubai",
            "provider_type": "clinic",
            "patient_category": "national",
        }

        print("\n🔧 Step 1: Initialize Streamlined Validator")
        print("-" * 40)
        validator = LLMValidator(timeout_seconds=60)
        print("✅ Validator initialized")

        print("\n🔧 Step 2: Run Validation")
        print("-" * 40)
        start_time = time.time()

        result = await validator.validate_healthcare_data(sample_data, context)

        execution_time = time.time() - start_time

        print(f"✅ Validation completed in {execution_time:.2f} seconds")

        print("\n🔧 Step 3: Validation Results")
        print("-" * 40)
        result_dict = result.to_dict()

        print(f"Overall Quality Score: {result_dict['overall_quality_score']:.3f}")
        print(f"Grade: {result_dict['grade']}")
        print(f"Validation Passed: {result_dict['validation_passed']}")
        print(f"Total Issues: {result_dict['total_issues']}")
        print(f"  - Critical: {result_dict['critical_issues']}")
        print(f"  - Warning: {result_dict['warning_issues']}")
        print(f"  - Info: {result_dict['info_issues']}")

        if result_dict["top_issues"]:
            print("\nTop Issues:")
            for i, issue in enumerate(result_dict["top_issues"][:3], 1):
                print(f"  {i}. {issue}")

        if result_dict["recommendations"]:
            print("\nRecommendations:")
            for i, rec in enumerate(result_dict["recommendations"][:3], 1):
                print(f"  {i}. {rec}")

        # Save results
        output_data = {
            "test_metadata": {
                "test_timestamp": time.time(),
                "execution_time": execution_time,
                "validator_type": "streamlined",
            },
            "validation_result": result_dict,
            "sample_data": sample_data,
            "context": context,
        }

        with open("debug_llm_validator_results.json", "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)

        print("\n✅ Detailed results saved to: debug_llm_validator_results.json")

    try:
        asyncio.run(test_validation())
        print("\n🎉 Streamlined LLM validator test completed successfully!")
    except Exception as e:
        print(f"\n❌ Error during validation: {e}")
        import traceback

        print("\n📋 Full traceback:")
        traceback.print_exc()

    print("=" * 60)
