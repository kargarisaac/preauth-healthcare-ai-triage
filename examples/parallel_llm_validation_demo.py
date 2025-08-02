"""
Parallel LLM Validation Demo

This demo showcases the complete parallel LLM execution infrastructure for
healthcare data validation, including smart sampling, parallel execution,
and hybrid scoring.
"""

import asyncio
import json
import time
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from loguru import logger

from pipelines.llm_data_sampler import SmartDataSampler, SamplingStrategy
from pipelines.llm_validator import ParallelLLMValidator
from pipelines.data_quality import DataQuality
from baml_client.types import ValidationType


async def demo_parallel_llm_validation():
    """
    Comprehensive demo of parallel LLM validation infrastructure.
    """
    print("=" * 80)
    print("Parallel LLM Validation Infrastructure Demo")
    print("=" * 80)

    # Step 1: Create realistic healthcare dataset
    print("\n🔧 Step 1: Generate Sample Healthcare Dataset")
    print("-" * 50)

    np.random.seed(42)
    n_records = 500

    # Create diverse healthcare data
    sample_data = {
        'patient_id': [f'P{i:05d}' for i in range(n_records)],
        'member_id': [f'M{i:05d}' for i in range(n_records)],
        'diagnosis_code': np.random.choice(
            [
                'E11.9',
                'E11.0',
                'M54.5',
                'J45.9',
                'I10',
                'K21.9',
                'F32.9',
                'R10.9',
                'N39.0',
                'X99.9',  # Include invalid code
            ],
            n_records,
            p=[0.15, 0.1, 0.15, 0.1, 0.15, 0.1, 0.05, 0.05, 0.1, 0.05],
        ),
        'procedure_code': np.random.choice(
            [
                '99213',
                '99214',
                '99202',
                '99203',
                '83036',
                '80053',
                '85025',
                '80061',
                '45378',
                '12345',  # Include invalid code
            ],
            n_records,
            p=[0.2, 0.15, 0.1, 0.1, 0.1, 0.1, 0.05, 0.05, 0.1, 0.05],
        ),
        'service_date': pd.date_range('2024-01-01', periods=n_records, freq='D'),
        'amount': np.random.lognormal(
            mean=5, sigma=1, size=n_records
        ),  # Realistic cost distribution
        'provider_id': [f'PROV{i%25:03d}' for i in range(n_records)],
        'claim_status': np.random.choice(
            ['approved', 'pending', 'denied'], n_records, p=[0.7, 0.2, 0.1]
        ),
        'patient_age': np.random.randint(18, 85, n_records),
        'provider_specialty': np.random.choice(
            [
                'Internal Medicine',
                'Family Medicine',
                'Cardiology',
                'Endocrinology',
                'Gastroenterology',
                'Pulmonology',
                'Psychiatry',
            ],
            n_records,
        ),
    }

    # Add some null values to simulate real data
    for col in ['diagnosis_code', 'procedure_code']:
        null_indices = np.random.choice(
            n_records, size=int(n_records * 0.05), replace=False
        )
        for idx in null_indices:
            sample_data[col][idx] = None

    df = pd.DataFrame(sample_data)

    print(f"   Generated dataset: {len(df)} records, {len(df.columns)} columns")
    print(f"   Data completeness: {(1 - df.isnull().sum().sum() / df.size) * 100:.1f}%")
    print(f"   Unique patients: {df['patient_id'].nunique()}")
    print(f"   Date range: {df['service_date'].min()} to {df['service_date'].max()}")

    # Step 2: Smart Data Sampling Demo
    print("\n🔧 Step 2: Smart Data Sampling")
    print("-" * 50)

    sampler = SmartDataSampler(max_sample_size=75)

    # Test different sampling strategies
    strategies = [
        SamplingStrategy.ADAPTIVE,
        SamplingStrategy.HEALTHCARE_AWARE,
        SamplingStrategy.STRATIFIED,
    ]

    sampling_results = {}

    for strategy in strategies:
        start_time = time.time()
        sample = sampler.create_sample(df, strategy=strategy)
        sampling_time = time.time() - start_time

        sampling_results[strategy.value] = {
            'sample_size': len(sample.sample_data),
            'sample_ratio': sample.metadata.sample_ratio,
            'sampling_time': sampling_time,
            'quality_scores': sample.quality_indicators,
            'healthcare_relevance': sample.metadata.healthcare_indicators[
                'complexity_score'
            ],
        }

        print(f"   ✅ {strategy.value.title()}: {len(sample.sample_data)} records ")
        print(f"      Quality: {sample.quality_indicators['completeness_score']:.3f}")
        print(f"      Time: {sampling_time:.3f}s")

    # Use the best sample for further testing
    best_sample = sampler.create_sample(df, strategy=SamplingStrategy.HEALTHCARE_AWARE)

    # Step 3: Parallel LLM Validation Demo
    print("\n🔧 Step 3: Parallel LLM Validation")
    print("-" * 50)

    validator = ParallelLLMValidator(max_concurrent_requests=5, timeout_seconds=15)

    # Test different validation task combinations
    task_combinations = [
        [ValidationType.DATA_QUALITY],
        [ValidationType.CODE_VALIDATION],
        [ValidationType.CLINICAL],
        [
            ValidationType.DATA_QUALITY,
            ValidationType.CODE_VALIDATION,
            ValidationType.CLINICAL,
        ],
    ]

    validation_results = {}

    for i, tasks in enumerate(task_combinations):
        start_time = time.time()

        batch_result = await validator.validate_healthcare_data(
            best_sample, validation_tasks=tasks
        )

        validation_time = time.time() - start_time

        validation_results[f'combination_{i+1}'] = {
            'task_count': len(tasks),
            'successful_tasks': batch_result.successful_tasks,
            'failed_tasks': batch_result.failed_tasks,
            'aggregated_score': batch_result.aggregated_score,
            'execution_time': validation_time,
            'parallel_efficiency': len(tasks)
            / max(validation_time, 0.1),  # Tasks per second
        }

        task_names = ', '.join([t.value for t in tasks])
        print(f"   ✅ Tasks [{task_names}]:")
        print(f"      Success: {batch_result.successful_tasks}/{len(tasks)}")
        print(f"      Score: {batch_result.aggregated_score:.3f}")
        print(f"      Time: {validation_time:.2f}s")
        print(
            f"      Efficiency: {validation_results[f'combination_{i+1}']['parallel_efficiency']:.1f} tasks/sec"
        )

    # Step 4: Enhanced Data Quality with Hybrid Scoring
    print("\n🔧 Step 4: Enhanced Data Quality with Hybrid Scoring")
    print("-" * 50)

    # Create FHIR bundle for testing
    fhir_bundle = {
        "resourceType": "Bundle",
        "id": f"demo-bundle-{int(time.time())}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "meta": {
            "source": "Demo",
            "lastUpdated": datetime.now(timezone.utc).isoformat(),
        },
        "claims": [
            {
                "sequence": i + 1,
                "claim_id": f"C{i:04d}",
                "patient_id": row['patient_id'],
                "diagnosis_code": row['diagnosis_code'],
                "procedure_code": row['procedure_code'],
                "amount": row['amount'],
            }
            for i, row in df.head(10).iterrows()
        ],
        "raw_data": {
            "csv_data": df.to_dict('records'),
            "columns": list(df.columns),
            "shape": list(df.shape),
        },
    }

    # Test both validation methods
    data_quality = DataQuality(enable_llm_validation=True, max_concurrent_llm=3)

    # Rule-based validation
    start_time = time.time()
    rule_based_result = data_quality.validate_fhir_bundle(fhir_bundle)
    rule_based_time = time.time() - start_time

    # Enhanced validation with LLM
    start_time = time.time()
    enhanced_result = await data_quality.validate_fhir_bundle_async(fhir_bundle)
    enhanced_time = time.time() - start_time

    print("   Rule-based validation:")
    print(f"      Score: {rule_based_result['quality_score'].overall_score:.3f}")
    print(f"      Issues: {len(rule_based_result['validation_issues'])}")
    print(f"      Time: {rule_based_time:.2f}s")

    print("   Enhanced (Hybrid) validation:")
    enhanced_score = enhanced_result['quality_score']
    print(f"      Rule-based: {enhanced_score.overall_score:.3f}")
    if enhanced_score.llm_validation_score:
        print(f"      LLM Score: {enhanced_score.llm_validation_score:.3f}")
    if enhanced_score.hybrid_score:
        print(f"      Hybrid Score: {enhanced_score.hybrid_score:.3f}")
    if enhanced_score.llm_confidence_score:
        print(f"      LLM Confidence: {enhanced_score.llm_confidence_score:.3f}")
    print(f"      Total Issues: {len(enhanced_result['validation_issues'])}")
    print(f"      Time: {enhanced_time:.2f}s")

    # Step 5: Performance Analysis
    print("\n🔧 Step 5: Performance Analysis")
    print("-" * 50)

    performance_metrics = validator.get_performance_metrics()

    print("   LLM Validator Performance:")
    print(f"      Total requests: {performance_metrics['total_requests']}")
    print(f"      Success rate: {performance_metrics['success_rate']:.1%}")
    print(
        f"      Avg response time: {performance_metrics.get('average_request_time', 0):.2f}s"
    )

    # Comparison analysis
    improvement = 0
    if rule_based_result['quality_score'].overall_score > 0:
        if enhanced_score.hybrid_score:
            improvement = (
                (
                    enhanced_score.hybrid_score
                    - rule_based_result['quality_score'].overall_score
                )
                / rule_based_result['quality_score'].overall_score
                * 100
            )

    print(f"   Quality Improvement: {improvement:+.1f}%")
    print(f"   LLM Processing Overhead: {enhanced_time - rule_based_time:.2f}s")

    # Step 6: Save Comprehensive Results
    print("\n🔧 Step 6: Save Results")
    print("-" * 50)

    demo_results = {
        'demo_metadata': {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'dataset_size': len(df),
            'sample_size': len(best_sample.sample_data),
            'total_demo_time': time.time(),
        },
        'dataset_summary': {
            'records': len(df),
            'columns': len(df.columns),
            'completeness': (1 - df.isnull().sum().sum() / df.size) * 100,
            'unique_patients': df['patient_id'].nunique(),
            'date_range': {
                'start': str(df['service_date'].min()),
                'end': str(df['service_date'].max()),
            },
        },
        'sampling_performance': sampling_results,
        'llm_validation_performance': validation_results,
        'quality_comparison': {
            'rule_based_score': rule_based_result['quality_score'].overall_score,
            'enhanced_score': enhanced_score.hybrid_score
            if enhanced_score.hybrid_score
            else enhanced_score.overall_score,
            'llm_score': enhanced_score.llm_validation_score,
            'improvement_percentage': improvement,
            'rule_based_time': rule_based_time,
            'enhanced_time': enhanced_time,
        },
        'performance_metrics': performance_metrics,
    }

    with open("parallel_llm_validation_demo_results.json", "w", encoding="utf-8") as f:
        json.dump(demo_results, f, indent=2, ensure_ascii=False, default=str)

    print(
        "   ✅ Comprehensive results saved to: parallel_llm_validation_demo_results.json"
    )

    return demo_results


def demo_usage_patterns():
    """
    Show common usage patterns for the LLM validation infrastructure.
    """
    print("\n" + "=" * 80)
    print("Common Usage Patterns")
    print("=" * 80)

    print(
        """
1. Basic Data Sampling:
   ```python
   from pipelines.llm_data_sampler import SmartDataSampler, SamplingStrategy

   sampler = SmartDataSampler(max_sample_size=100)
   sample = sampler.create_sample(df, strategy=SamplingStrategy.HEALTHCARE_AWARE)
   ```

2. Parallel LLM Validation:
   ```python
   from pipelines.llm_validator import ParallelLLMValidator
   from baml_client.types import ValidationType

   validator = ParallelLLMValidator(max_concurrent_requests=5)
   result = await validator.validate_healthcare_data(
       sample,
       validation_tasks=[ValidationType.DATA_QUALITY]
   )
   ```

3. Enhanced Data Quality with LLM:
   ```python
   from pipelines.data_quality import DataQuality

   data_quality = DataQuality(enable_llm_validation=True)
   enhanced_result = await data_quality.validate_fhir_bundle_async(fhir_bundle)
   ```

4. Performance-Optimized Setup:
   ```python
   # For large datasets
   sampler = SmartDataSampler(max_sample_size=200)
   validator = ParallelLLMValidator(max_concurrent_requests=10, timeout_seconds=30)
   data_quality = DataQuality(enable_llm_validation=True, max_concurrent_llm=5)
   ```
"""
    )


async def main():
    """Main demo execution."""
    logger.add("parallel_llm_validation_demo.log")

    try:
        # Run comprehensive demo
        results = await demo_parallel_llm_validation()

        # Show usage patterns
        demo_usage_patterns()

        print("\n🎉 Parallel LLM Validation Demo completed successfully!")
        print(f"   Dataset processed: {results['dataset_summary']['records']} records")
        print(
            f"   Quality improvement: {results['quality_comparison']['improvement_percentage']:+.1f}%"
        )
        print(
            f"   LLM success rate: {results['performance_metrics']['success_rate']:.1%}"
        )

    except Exception as e:
        print(f"\n❌ Demo failed: {type(e).__name__}: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
