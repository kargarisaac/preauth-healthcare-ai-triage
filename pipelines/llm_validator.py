"""
Parallel LLM execution framework for healthcare data validation.

This module provides async LLM validation capabilities with concurrent execution,
error handling, and integration with BAML generated functions for healthcare
data quality assessment.
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from loguru import logger

# Import BAML client for LLM operations
try:
    from baml_client import BamlAsyncClient

    BAML_CLIENT_AVAILABLE = True
except ImportError as e:
    logger.warning(f"BAML client not available: {e}")
    BAML_CLIENT_AVAILABLE = False
    BamlAsyncClient = None

from pipelines.llm_data_sampler import DataSample, SmartDataSampler


class ValidationTask(Enum):
    """Types of LLM validation tasks."""

    HEALTHCARE_DATA_QUALITY = "healthcare_data_quality"
    MEDICAL_CODE_VALIDATION = "medical_code_validation"
    CLINICAL_CONSISTENCY = "clinical_consistency"
    DATA_COMPLETENESS = "data_completeness"
    FORMAT_COMPLIANCE = "format_compliance"


@dataclass
class LLMValidationRequest:
    """Request for LLM validation."""

    task_id: str
    task_type: ValidationTask
    data_sample: List[Dict[str, Any]]
    context: str
    validation_prompt: str
    priority: int = 1  # 1=high, 2=medium, 3=low


@dataclass
class LLMValidationResult:
    """Result from LLM validation."""

    task_id: str
    task_type: ValidationTask
    success: bool
    validation_score: float
    issues_found: List[Dict[str, Any]]
    recommendations: List[str]
    confidence_score: float
    execution_time: float
    error_message: Optional[str] = None
    raw_llm_response: Optional[str] = None


@dataclass
class BatchValidationResult:
    """Result from batch validation execution."""

    total_tasks: int
    successful_tasks: int
    failed_tasks: int
    total_execution_time: float
    average_response_time: float
    validation_results: List[LLMValidationResult]
    aggregated_score: float
    error_summary: Dict[str, int]


class PromptTemplate:
    """Healthcare-specific prompt templates for LLM validation."""

    @staticmethod
    def healthcare_data_quality_prompt(data_sample: List[Dict], context: str) -> str:
        """Generate prompt for healthcare data quality validation."""
        return f"""
You are a healthcare data quality expert specializing in UAE healthcare systems.
Analyze the following healthcare data sample for quality, completeness, and compliance.

CONTEXT: {context}

DATA SAMPLE (showing {len(data_sample)} records):
{json.dumps(data_sample, indent=2, default=str)}

Please evaluate this healthcare data and provide:

1. OVERALL QUALITY SCORE (0.0 to 1.0):
   - Consider completeness, accuracy, consistency, and healthcare standards compliance

2. SPECIFIC ISSUES FOUND:
   - Missing required fields
   - Invalid medical codes (ICD-10, CPT)
   - Inconsistent data formats
   - Clinical logic problems
   - UAE healthcare compliance issues

3. RECOMMENDATIONS:
   - Actionable steps to improve data quality
   - Priority recommendations for immediate attention

4. CONFIDENCE LEVEL (0.0 to 1.0):
   - Your confidence in this assessment

Return your response in the following JSON format:
{{
  "overall_quality_score": 0.0,
  "issues_found": [
    {{
      "severity": "error|warning|info",
      "category": "completeness|format|clinical|compliance",
      "description": "detailed description",
      "field": "affected field name",
      "suggested_fix": "how to fix this"
    }}
  ],
  "recommendations": [
    "recommendation 1",
    "recommendation 2"
  ],
  "confidence_score": 0.0,
  "reasoning": "brief explanation of your assessment"
}}
"""

    @staticmethod
    def medical_code_validation_prompt(data_sample: List[Dict], context: str) -> str:
        """Generate prompt for medical code validation."""
        return f"""
You are a medical coding specialist with expertise in ICD-10, CPT, and UAE healthcare standards.
Validate the medical codes in this healthcare data sample.

CONTEXT: {context}

DATA SAMPLE:
{json.dumps(data_sample, indent=2, default=str)}

Focus on validating:
1. ICD-10 diagnosis codes (format: letter + 2-3 digits + optional decimal)
2. CPT procedure codes (format: 5 digits)
3. Code-condition relationships
4. UAE healthcare coding standards

Provide detailed validation results in JSON format:
{{
  "overall_quality_score": 0.0,
  "issues_found": [
    {{
      "severity": "error|warning",
      "category": "icd10|cpt|relationship",
      "description": "what's wrong",
      "field": "field name",
      "invalid_code": "the problematic code",
      "suggested_fix": "correction or suggestion"
    }}
  ],
  "recommendations": ["coding improvement suggestions"],
  "confidence_score": 0.0,
  "codes_validated": {{
    "total_icd10": 0,
    "valid_icd10": 0,
    "total_cpt": 0,
    "valid_cpt": 0
  }}
}}
"""

    @staticmethod
    def clinical_consistency_prompt(data_sample: List[Dict], context: str) -> str:
        """Generate prompt for clinical consistency validation."""
        return f"""
You are a clinical informatics expert specializing in healthcare data consistency.
Analyze this data for clinical logic and consistency issues.

CONTEXT: {context}

DATA SAMPLE:
{json.dumps(data_sample, indent=2, default=str)}

Evaluate clinical consistency:
1. Medication-diagnosis relationships
2. Procedure-diagnosis appropriateness
3. Age-appropriate treatments
4. Logical clinical pathways
5. UAE healthcare practices

Return validation results:
{{
  "overall_quality_score": 0.0,
  "issues_found": [
    {{
      "severity": "error|warning|info",
      "category": "medication|procedure|age|pathway",
      "description": "clinical inconsistency found",
      "field": "affected field",
      "clinical_concern": "why this is concerning",
      "suggested_fix": "clinical recommendation"
    }}
  ],
  "recommendations": ["clinical data improvement suggestions"],
  "confidence_score": 0.0,
  "clinical_patterns": {{
    "diabetes_care_complete": false,
    "medication_appropriateness": 0.0,
    "procedure_justification": 0.0
  }}
}}
"""


class ParallelLLMValidator:
    """
    Parallel LLM execution framework for healthcare data validation.

    Provides async LLM validation with concurrent execution, error handling,
    and result aggregation for optimal performance.
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
        self.baml_client = BamlAsyncClient({}) if BAML_CLIENT_AVAILABLE else None
        self.sampler = SmartDataSampler(max_sample_size=50)

        # Performance tracking
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_execution_time = 0.0

    async def validate_healthcare_data(
        self,
        data_sample: DataSample,
        validation_tasks: Optional[List[ValidationTask]] = None,
    ) -> BatchValidationResult:
        """
        Validate healthcare data using parallel LLM execution.

        Args:
            data_sample: Sampled data with metadata
            validation_tasks: Specific validation tasks to run (defaults to all)

        Returns:
            Comprehensive validation results from all LLM tasks
        """
        if validation_tasks is None:
            validation_tasks = [
                ValidationTask.HEALTHCARE_DATA_QUALITY,
                ValidationTask.MEDICAL_CODE_VALIDATION,
                ValidationTask.CLINICAL_CONSISTENCY,
            ]

        logger.info(
            f"Starting parallel LLM validation with {len(validation_tasks)} tasks"
        )
        start_time = time.time()

        # Create validation requests
        requests = self._create_validation_requests(data_sample, validation_tasks)

        # Execute requests in parallel with semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        tasks = [
            self._execute_validation_task(request, semaphore) for request in requests
        ]

        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and handle exceptions
        validation_results = []
        error_summary = {}

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Validation task {i} failed: {result}")
                error_type = type(result).__name__
                error_summary[error_type] = error_summary.get(error_type, 0) + 1

                # Create failed result
                failed_result = LLMValidationResult(
                    task_id=requests[i].task_id,
                    task_type=requests[i].task_type,
                    success=False,
                    validation_score=0.0,
                    issues_found=[],
                    recommendations=[],
                    confidence_score=0.0,
                    execution_time=0.0,
                    error_message=str(result),
                )
                validation_results.append(failed_result)
            else:
                validation_results.append(result)

        # Calculate batch metrics
        total_execution_time = time.time() - start_time
        successful_tasks = len([r for r in validation_results if r.success])
        failed_tasks = len(validation_results) - successful_tasks

        avg_response_time = sum(
            r.execution_time for r in validation_results if r.success
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
            f"Parallel validation completed: {successful_tasks}/{len(validation_tasks)} "
            f"tasks successful in {total_execution_time:.2f}s"
        )

        return batch_result

    def _create_validation_requests(
        self, data_sample: DataSample, validation_tasks: List[ValidationTask]
    ) -> List[LLMValidationRequest]:
        """Create LLM validation requests from data sample and tasks."""
        requests = []

        for i, task_type in enumerate(validation_tasks):
            task_id = f"{task_type.value}_{i}_{int(time.time())}"

            # Select appropriate prompt template
            if task_type == ValidationTask.HEALTHCARE_DATA_QUALITY:
                prompt = PromptTemplate.healthcare_data_quality_prompt(
                    data_sample.sample_data, data_sample.context_summary
                )
            elif task_type == ValidationTask.MEDICAL_CODE_VALIDATION:
                prompt = PromptTemplate.medical_code_validation_prompt(
                    data_sample.sample_data, data_sample.context_summary
                )
            elif task_type == ValidationTask.CLINICAL_CONSISTENCY:
                prompt = PromptTemplate.clinical_consistency_prompt(
                    data_sample.sample_data, data_sample.context_summary
                )
            else:
                # Fallback to general quality prompt
                prompt = PromptTemplate.healthcare_data_quality_prompt(
                    data_sample.sample_data, data_sample.context_summary
                )

            request = LLMValidationRequest(
                task_id=task_id,
                task_type=task_type,
                data_sample=data_sample.sample_data,
                context=data_sample.context_summary,
                validation_prompt=prompt,
                priority=1,
            )
            requests.append(request)

        return requests

    async def _execute_validation_task(
        self, request: LLMValidationRequest, semaphore: asyncio.Semaphore
    ) -> LLMValidationResult:
        """Execute a single validation task with concurrency control."""
        async with semaphore:
            start_time = time.time()
            self.total_requests += 1

            try:
                # Execute LLM request with timeout
                llm_response = await asyncio.wait_for(
                    self._call_llm_for_validation(request), timeout=self.timeout_seconds
                )

                # Parse LLM response
                validation_result = self._parse_llm_response(
                    request, llm_response, start_time
                )
                self.successful_requests += 1

                return validation_result

            except asyncio.TimeoutError:
                self.failed_requests += 1
                logger.warning(
                    f"LLM request {request.task_id} timed out after {self.timeout_seconds}s"
                )
                return self._create_error_result(
                    request, "Request timed out", time.time() - start_time
                )

            except Exception as e:
                self.failed_requests += 1
                logger.error(f"LLM request {request.task_id} failed: {e}")
                return self._create_error_result(
                    request, str(e), time.time() - start_time
                )

    async def _call_llm_for_validation(self, request: LLMValidationRequest) -> str:
        """
        Call LLM for validation using BAML client.

        Note: This is a simplified example. In a real implementation,
        you would create appropriate BAML functions for healthcare validation.
        """
        try:
            # For now, using the existing ExtractResume function as a placeholder
            # In production, you would have dedicated healthcare validation functions

            # Simulate LLM call with structured prompt
            # This would be replaced with actual BAML healthcare validation functions
            mock_response = await self._simulate_llm_response(request)
            return mock_response

        except Exception as e:
            logger.error(f"BAML client error: {e}")
            raise

    async def _simulate_llm_response(self, request: LLMValidationRequest) -> str:
        """
        Simulate LLM response for testing purposes.

        In production, this would be replaced with actual BAML function calls.
        """
        # Simulate processing delay
        await asyncio.sleep(0.5)

        # Generate mock response based on task type
        if request.task_type == ValidationTask.HEALTHCARE_DATA_QUALITY:
            return json.dumps(
                {
                    "overall_quality_score": 0.85,
                    "issues_found": [
                        {
                            "severity": "warning",
                            "category": "completeness",
                            "description": "Some diagnosis codes are missing",
                            "field": "diagnosis_code",
                            "suggested_fix": "Ensure all medical encounters have diagnosis codes",
                        }
                    ],
                    "recommendations": [
                        "Implement data validation rules for diagnosis codes",
                        "Train staff on proper medical coding",
                    ],
                    "confidence_score": 0.9,
                    "reasoning": "Data shows good overall structure with minor completeness issues",
                }
            )

        elif request.task_type == ValidationTask.MEDICAL_CODE_VALIDATION:
            return json.dumps(
                {
                    "overall_quality_score": 0.78,
                    "issues_found": [
                        {
                            "severity": "error",
                            "category": "icd10",
                            "description": "Invalid ICD-10 format detected",
                            "field": "diagnosis_code",
                            "invalid_code": "X99.9",
                            "suggested_fix": "Verify against current ICD-10 codebook",
                        }
                    ],
                    "recommendations": [
                        "Update medical coding validation rules",
                        "Provide coding training for staff",
                    ],
                    "confidence_score": 0.95,
                    "codes_validated": {
                        "total_icd10": 45,
                        "valid_icd10": 42,
                        "total_cpt": 38,
                        "valid_cpt": 36,
                    },
                }
            )

        else:  # Clinical consistency
            return json.dumps(
                {
                    "overall_quality_score": 0.82,
                    "issues_found": [
                        {
                            "severity": "info",
                            "category": "medication",
                            "description": "Insulin prescribed - ensure diabetes monitoring",
                            "field": "medication",
                            "clinical_concern": "Diabetes care coordination",
                            "suggested_fix": "Schedule HbA1c follow-up",
                        }
                    ],
                    "recommendations": [
                        "Implement diabetes care protocols",
                        "Ensure medication-diagnosis alignment",
                    ],
                    "confidence_score": 0.88,
                    "clinical_patterns": {
                        "diabetes_care_complete": True,
                        "medication_appropriateness": 0.9,
                        "procedure_justification": 0.85,
                    },
                }
            )

    def _parse_llm_response(
        self, request: LLMValidationRequest, llm_response: str, start_time: float
    ) -> LLMValidationResult:
        """Parse LLM response into structured validation result."""
        execution_time = time.time() - start_time

        try:
            # Parse JSON response
            response_data = json.loads(llm_response)

            return LLMValidationResult(
                task_id=request.task_id,
                task_type=request.task_type,
                success=True,
                validation_score=response_data.get("overall_quality_score", 0.0),
                issues_found=response_data.get("issues_found", []),
                recommendations=response_data.get("recommendations", []),
                confidence_score=response_data.get("confidence_score", 0.0),
                execution_time=execution_time,
                raw_llm_response=llm_response,
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response for {request.task_id}: {e}")
            return self._create_error_result(
                request, f"Failed to parse LLM response: {e}", execution_time
            )
        except Exception as e:
            logger.error(f"Error processing LLM response for {request.task_id}: {e}")
            return self._create_error_result(
                request, f"Error processing response: {e}", execution_time
            )

    def _create_error_result(
        self, request: LLMValidationRequest, error_message: str, execution_time: float
    ) -> LLMValidationResult:
        """Create error result for failed validation task."""
        return LLMValidationResult(
            task_id=request.task_id,
            task_type=request.task_type,
            success=False,
            validation_score=0.0,
            issues_found=[
                {
                    "severity": "error",
                    "category": "system",
                    "description": f"Validation failed: {error_message}",
                    "field": "system",
                    "suggested_fix": "Check LLM service availability and retry",
                }
            ],
            recommendations=["Retry validation when LLM service is available"],
            confidence_score=0.0,
            execution_time=execution_time,
            error_message=error_message,
        )

    def _calculate_aggregated_score(
        self, validation_results: List[LLMValidationResult]
    ) -> float:
        """Calculate aggregated quality score from all validation results."""
        successful_results = [r for r in validation_results if r.success]

        if not successful_results:
            return 0.0

        # Weight different validation types
        weights = {
            ValidationTask.HEALTHCARE_DATA_QUALITY: 0.4,
            ValidationTask.MEDICAL_CODE_VALIDATION: 0.3,
            ValidationTask.CLINICAL_CONSISTENCY: 0.3,
        }

        weighted_score = 0.0
        total_weight = 0.0

        for result in successful_results:
            weight = weights.get(result.task_type, 0.1)
            weighted_score += result.validation_score * weight
            total_weight += weight

        return weighted_score / total_weight if total_weight > 0 else 0.0

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
    Debug and testing section for parallel LLM validator.

    Tests validation framework with sample healthcare data.
    """

    # Setup logging
    logger.add("debug_llm_validator.log")

    print("=" * 80)
    print("Parallel LLM Validator - Debug Mode")
    print("=" * 80)

    async def test_parallel_validation():
        """Test the parallel LLM validation framework."""

        # Create sample healthcare data
        import pandas as pd
        import numpy as np

        np.random.seed(42)

        sample_data = {
            "patient_id": [f"P{i:04d}" for i in range(50)],
            "diagnosis_code": np.random.choice(["E11.9", "M54.5", "I10", "X99.9"], 50),
            "procedure_code": np.random.choice(
                ["99213", "99214", "83036", "12345"], 50
            ),
            "amount": np.random.uniform(50, 500, 50),
            "service_date": pd.date_range("2024-01-01", periods=50),
            "provider_id": [f"PROV{i%10:03d}" for i in range(50)],
        }

        df = pd.DataFrame(sample_data)

        print("\n🔧 Step 1: Create Data Sample")
        print("-" * 50)
        print(f"   Created dataset with {len(df)} rows")

        # Create smart sample
        sampler = SmartDataSampler(max_sample_size=20)
        data_sample = sampler.create_sample(df)

        print(f"   Sample size: {len(data_sample.sample_data)} records")
        print(f"   Context: {data_sample.context_summary[:100]}...")

        print("\n🔧 Step 2: Initialize Parallel Validator")
        print("-" * 50)

        validator = ParallelLLMValidator(max_concurrent_requests=3, timeout_seconds=10)
        print(
            f"   Validator initialized with max {validator.max_concurrent_requests} concurrent requests"
        )

        print("\n🔧 Step 3: Execute Parallel Validation")
        print("-" * 50)

        start_time = time.time()

        # Run all validation tasks
        batch_result = await validator.validate_healthcare_data(data_sample)

        execution_time = time.time() - start_time

        print(f"   ✅ Validation completed in {execution_time:.2f} seconds")
        print(
            f"   Successful tasks: {batch_result.successful_tasks}/{batch_result.total_tasks}"
        )
        print(f"   Failed tasks: {batch_result.failed_tasks}")
        print(f"   Average response time: {batch_result.average_response_time:.2f}s")
        print(f"   Aggregated quality score: {batch_result.aggregated_score:.3f}")

        print("\n🔧 Step 4: Validation Results Summary")
        print("-" * 50)

        for result in batch_result.validation_results:
            status = "✅" if result.success else "❌"
            print(f"   {status} {result.task_type.value}:")
            print(f"      Score: {result.validation_score:.3f}")
            print(f"      Issues: {len(result.issues_found)}")
            print(f"      Recommendations: {len(result.recommendations)}")
            print(f"      Execution time: {result.execution_time:.2f}s")

            if result.error_message:
                print(f"      Error: {result.error_message}")

        print("\n🔧 Step 5: Performance Metrics")
        print("-" * 50)

        metrics = validator.get_performance_metrics()
        for key, value in metrics.items():
            print(f"   {key}: {value}")

        # Save detailed results
        results_data = {
            "test_metadata": {
                "test_timestamp": time.time(),
                "sample_size": len(data_sample.sample_data),
                "total_execution_time": execution_time,
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
                    "task_type": result.task_type.value,
                    "success": result.success,
                    "validation_score": result.validation_score,
                    "issues_count": len(result.issues_found),
                    "recommendations_count": len(result.recommendations),
                    "confidence_score": result.confidence_score,
                    "execution_time": result.execution_time,
                    "error_message": result.error_message,
                }
                for result in batch_result.validation_results
            ],
            "performance_metrics": metrics,
        }

        with open("debug_llm_validator_results.json", "w", encoding="utf-8") as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False, default=str)

        print("\n   Detailed results saved to: debug_llm_validator_results.json")

    try:
        # Run async test
        asyncio.run(test_parallel_validation())
        print("\n🎉 Parallel LLM validator debug session completed successfully!")

    except Exception as e:
        print("\n❌ Error during validation:")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback

        print("\n📋 Full traceback:")
        traceback.print_exc()

    print("=" * 80)
