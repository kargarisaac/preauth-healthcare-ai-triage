"""
Parallel LLM execution framework for healthcare data validation using BAML.

This module provides async LLM validation capabilities with concurrent execution,
error handling, and integration with BAML generated functions for healthcare
data quality assessment.
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional
from loguru import logger

# Import BAML client and types
try:
    from baml_client import b
    from baml_client.types import (
        DataSample,
        DataContext,
        LLMValidationResult,
        ValidationType,
    )

    BAML_CLIENT_AVAILABLE = True
except ImportError as e:
    logger.warning(f"BAML client not available: {e}")
    BAML_CLIENT_AVAILABLE = False
    b = None

from pipelines.llm_data_sampler import SmartDataSampler


# All data classes are now provided by BAML - no custom classes needed


class BatchValidationResult:
    """Result from batch validation execution using BAML types."""

    def __init__(
        self,
        total_tasks: int,
        successful_tasks: int,
        failed_tasks: int,
        total_execution_time: float,
        average_response_time: float,
        validation_results: List[LLMValidationResult],
        aggregated_score: float,
        error_summary: Dict[str, int],
    ):
        self.total_tasks = total_tasks
        self.successful_tasks = successful_tasks
        self.failed_tasks = failed_tasks
        self.total_execution_time = total_execution_time
        self.average_response_time = average_response_time
        self.validation_results = validation_results
        self.aggregated_score = aggregated_score
        self.error_summary = error_summary


# All prompts are now defined in BAML files - no custom prompt templates needed


class ParallelLLMValidator:
    """
    Parallel LLM execution framework for healthcare data validation using BAML.

    Provides async LLM validation with concurrent execution, error handling,
    and result aggregation for optimal performance using BAML functions.
    """

    def __init__(self, max_concurrent_requests: int = 5, timeout_seconds: int = 30):
        """
        Initialize parallel LLM validator.

        Args:
            max_concurrent_requests: Maximum number of concurrent LLM requests
            timeout_seconds: Timeout for individual LLM requests
        """
        self.max_concurrent_requests = max_concurrent_requests
        self.timeout_seconds = timeout_seconds
        self.sampler = SmartDataSampler(max_sample_size=50)

        # Performance tracking
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_execution_time = 0.0

    async def validate_healthcare_data(
        self,
        data_sample: DataSample,
        validation_tasks: Optional[List[ValidationType]] = None,
    ) -> BatchValidationResult:
        """
        Validate healthcare data using parallel LLM execution with BAML functions.

        Args:
            data_sample: Sampled data with metadata
            validation_tasks: Specific validation tasks to run (defaults to all)

        Returns:
            Comprehensive validation results from all LLM tasks
        """
        if validation_tasks is None:
            validation_tasks = [
                ValidationType.COMPLIANCE,
                ValidationType.CODE_VALIDATION,
                ValidationType.CLINICAL,
                ValidationType.DATA_QUALITY,
            ]

        logger.info(
            f"Starting parallel LLM validation with {len(validation_tasks)} tasks using BAML"
        )
        start_time = time.time()

        # Execute BAML validation functions in parallel with semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        tasks = [
            self._execute_baml_validation_task(data_sample, task_type, semaphore)
            for task_type in validation_tasks
        ]

        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and handle exceptions
        validation_results = []
        error_summary = {}

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    f"BAML validation task {validation_tasks[i].value} failed: {result}"
                )
                error_type = type(result).__name__
                error_summary[error_type] = error_summary.get(error_type, 0) + 1

                # Create failed result using BAML types
                failed_result = LLMValidationResult(
                    validation_passed=False,
                    confidence_score=0.0,
                    issues=[],
                    quality_metrics={},
                    processing_time_ms=0,
                    model_used="error",
                )
                validation_results.append(failed_result)
            else:
                validation_results.append(result)

        # Calculate batch metrics
        total_execution_time = time.time() - start_time
        successful_tasks = len([r for r in validation_results if r.validation_passed])
        failed_tasks = len(validation_results) - successful_tasks

        avg_response_time = sum(
            r.processing_time_ms / 1000.0
            for r in validation_results
            if r.validation_passed
        ) / max(successful_tasks, 1)

        # Calculate aggregated quality score
        aggregated_score = self._calculate_aggregated_score(validation_results)

        batch_result = BatchValidationResult(
            total_tasks=len(validation_tasks),
            successful_tasks=successful_tasks,
            failed_tasks=failed_tasks,
            total_execution_time=total_execution_time,
            average_response_time=avg_response_time,
            validation_results=validation_results,
            aggregated_score=aggregated_score,
            error_summary=error_summary,
        )

        logger.info(
            f"Parallel BAML validation completed: {successful_tasks}/{len(validation_tasks)} "
            f"tasks successful in {total_execution_time:.2f}s"
        )

        return batch_result

    async def _execute_baml_validation_task(
        self,
        data_sample: DataSample,
        validation_type: ValidationType,
        semaphore: asyncio.Semaphore,
    ) -> LLMValidationResult:
        """Execute a single validation task using BAML functions with concurrency control."""
        async with semaphore:
            start_time = time.time()
            self.total_requests += 1

            try:
                # Execute appropriate BAML function based on validation type
                if validation_type == ValidationType.COMPLIANCE:
                    result = await asyncio.wait_for(
                        b.ValidateCompliance(data_sample), timeout=self.timeout_seconds
                    )
                elif validation_type == ValidationType.CODE_VALIDATION:
                    result = await asyncio.wait_for(
                        b.ValidateMedicalCodes(data_sample),
                        timeout=self.timeout_seconds,
                    )
                elif validation_type == ValidationType.CLINICAL:
                    result = await asyncio.wait_for(
                        b.AssessClinicalLogic(data_sample), timeout=self.timeout_seconds
                    )
                elif validation_type == ValidationType.DATA_QUALITY:
                    result = await asyncio.wait_for(
                        b.DetectDataAnomalies(data_sample), timeout=self.timeout_seconds
                    )
                else:
                    # Fallback to comprehensive validation
                    result = await asyncio.wait_for(
                        b.ComprehensiveValidation(data_sample),
                        timeout=self.timeout_seconds,
                    )

                # Add processing time to the result
                processing_time_ms = int((time.time() - start_time) * 1000)
                if hasattr(result, 'processing_time_ms'):
                    result.processing_time_ms = processing_time_ms

                self.successful_requests += 1
                return result

            except asyncio.TimeoutError:
                self.failed_requests += 1
                logger.warning(
                    f"BAML validation {validation_type.value} timed out after {self.timeout_seconds}s"
                )
                return self._create_error_result(
                    f"Request timed out for {validation_type.value}",
                    time.time() - start_time,
                )

            except Exception as e:
                self.failed_requests += 1
                logger.error(f"BAML validation {validation_type.value} failed: {e}")
                return self._create_error_result(
                    f"BAML validation error: {str(e)}", time.time() - start_time
                )

    def _create_error_result(
        self, error_message: str, execution_time: float
    ) -> LLMValidationResult:
        """Create error result for failed validation task using BAML types."""
        return LLMValidationResult(
            validation_passed=False,
            confidence_score=0.0,
            issues=[],
            quality_metrics={"error": error_message},
            processing_time_ms=int(execution_time * 1000),
            model_used="error",
        )

    def _calculate_aggregated_score(
        self, validation_results: List[LLMValidationResult]
    ) -> float:
        """Calculate aggregated quality score from all validation results."""
        successful_results = [r for r in validation_results if r.validation_passed]

        if not successful_results:
            return 0.0

        # Calculate weighted average based on confidence scores
        total_score = 0.0
        total_weight = 0.0

        for result in successful_results:
            # Use confidence score as the quality metric
            score = result.confidence_score
            weight = 0.25  # Equal weight for all validation types

            total_score += score * weight
            total_weight += weight

        return total_score / total_weight if total_weight > 0 else 0.0

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the validator."""
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": (self.successful_requests / max(self.total_requests, 1)),
            "total_execution_time": self.total_execution_time,
            "average_request_time": (
                self.total_execution_time / max(self.successful_requests, 1)
            ),
        }


if __name__ == "__main__":
    """
    Debug and testing section for parallel LLM validator using BAML.

    Tests validation framework with sample healthcare data.
    """

    # Setup logging
    logger.add("debug_llm_validator.log")

    print("=" * 80)
    print("Parallel LLM Validator - Debug Mode (BAML)")
    print("=" * 80)

    async def test_baml_validation():
        """Test the parallel LLM validation framework using BAML."""

        if not BAML_CLIENT_AVAILABLE:
            print("❌ BAML client not available - cannot run tests")
            return

        # Create sample healthcare data using BAML DataSample format
        sample_claims_data = {
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

        data_sample = DataSample(
            resource_type="Claims",
            raw_data=json.dumps(sample_claims_data),
            context=DataContext(
                source_system="CSV",
                emirate="Dubai",
                provider_type="clinic",
                patient_category="national",
            ),
        )

        print("\n🔧 Step 1: Create BAML Data Sample")
        print("-" * 50)
        print(f"   Resource type: {data_sample.resource_type}")
        print(
            f"   Context: {data_sample.context.source_system} - {data_sample.context.emirate}"
        )

        print("\n🔧 Step 2: Initialize Parallel Validator")
        print("-" * 50)

        validator = ParallelLLMValidator(max_concurrent_requests=3, timeout_seconds=30)
        print(
            f"   Validator initialized with max {validator.max_concurrent_requests} concurrent requests"
        )

        print("\n🔧 Step 3: Execute Parallel BAML Validation")
        print("-" * 50)

        start_time = time.time()

        # Run all validation tasks using BAML functions
        batch_result = await validator.validate_healthcare_data(data_sample)

        execution_time = time.time() - start_time

        print(f"   ✅ BAML validation completed in {execution_time:.2f} seconds")
        print(
            f"   Successful tasks: {batch_result.successful_tasks}/{batch_result.total_tasks}"
        )
        print(f"   Failed tasks: {batch_result.failed_tasks}")
        print(f"   Average response time: {batch_result.average_response_time:.2f}s")
        print(f"   Aggregated quality score: {batch_result.aggregated_score:.3f}")

        print("\n🔧 Step 4: BAML Validation Results Summary")
        print("-" * 50)

        for i, result in enumerate(batch_result.validation_results):
            status = "✅" if result.validation_passed else "❌"
            print(f"   {status} Validation {i+1}:")
            print(f"      Passed: {result.validation_passed}")
            print(f"      Confidence: {result.confidence_score:.3f}")
            print(f"      Issues: {len(result.issues)}")
            print(f"      Processing time: {result.processing_time_ms}ms")

        print("\n🔧 Step 5: Performance Metrics")
        print("-" * 50)

        metrics = validator.get_performance_metrics()
        for key, value in metrics.items():
            print(f"   {key}: {value}")

        # Save detailed results
        results_data = {
            "test_metadata": {
                "test_timestamp": time.time(),
                "total_execution_time": execution_time,
                "baml_client_used": True,
            },
            "batch_result": {
                "total_tasks": batch_result.total_tasks,
                "successful_tasks": batch_result.successful_tasks,
                "failed_tasks": batch_result.failed_tasks,
                "aggregated_score": batch_result.aggregated_score,
                "error_summary": batch_result.error_summary,
            },
            "individual_results": [
                {
                    "validation_passed": result.validation_passed,
                    "confidence_score": result.confidence_score,
                    "issues_count": len(result.issues),
                    "processing_time_ms": result.processing_time_ms,
                    "model_used": result.model_used,
                }
                for result in batch_result.validation_results
            ],
            "performance_metrics": metrics,
        }

        with open("debug_llm_validator_baml_results.json", "w", encoding="utf-8") as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False, default=str)

        print("\n   Detailed results saved to: debug_llm_validator_baml_results.json")

    try:
        # Run async test
        asyncio.run(test_baml_validation())
        print("\n🎉 Parallel LLM validator (BAML) debug session completed successfully!")

    except Exception as e:
        print("\n❌ Error during BAML validation:")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback

        print("\n📋 Full traceback:")
        traceback.print_exc()

    print("=" * 80)
