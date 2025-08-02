"""
Smart data sampling module for large CSV files in UAE healthcare processing.

This module provides intelligent sampling strategies for large CSV files to optimize
LLM validation while maintaining statistical representativeness and healthcare context.
"""

import json
import random
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import numpy as np
from loguru import logger


class SamplingStrategy(Enum):
    """Available sampling strategies for CSV data."""

    STRATIFIED = "stratified"  # Beginning, middle, end sections
    RANDOM = "random"  # Random sampling across dataset
    SYSTEMATIC = "systematic"  # Every nth record
    ADAPTIVE = "adaptive"  # Size-based adaptive sampling
    HEALTHCARE_AWARE = "healthcare_aware"  # Healthcare-specific sampling


@dataclass
class SampleMetadata:
    """Metadata about the sampling process and results."""

    original_size: int
    sample_size: int
    sampling_strategy: SamplingStrategy
    sample_ratio: float
    null_percentage: float
    column_coverage: float
    data_types_distribution: Dict[str, int]
    healthcare_indicators: Dict[str, Any]
    statistical_summary: Dict[str, Any]


@dataclass
class DataSample:
    """Container for sampled data with metadata."""

    sample_data: List[Dict[str, Any]]
    metadata: SampleMetadata
    context_summary: str
    quality_indicators: Dict[str, Any]


class HealthcareContextBuilder:
    """Builds healthcare-specific context for LLM validation."""

    def __init__(self):
        """Initialize healthcare context builder."""
        self.healthcare_keywords = {
            'diagnosis': ['diagnosis', 'icd', 'condition', 'disease', 'disorder'],
            'procedure': ['procedure', 'cpt', 'treatment', 'service', 'operation'],
            'medication': ['medication', 'drug', 'prescription', 'rxnorm', 'medicine'],
            'patient': ['patient', 'member', 'person', 'individual', 'subscriber'],
            'provider': ['provider', 'doctor', 'physician', 'hospital', 'clinic'],
            'insurance': ['insurance', 'payer', 'coverage', 'benefit', 'plan'],
            'claim': ['claim', 'bill', 'charge', 'cost', 'amount', 'payment'],
        }

    def identify_healthcare_columns(self, columns: List[str]) -> Dict[str, List[str]]:
        """Identify healthcare-related columns by category."""
        healthcare_columns = {}

        for category, keywords in self.healthcare_keywords.items():
            matching_columns = []
            for col in columns:
                col_lower = col.lower().replace('_', ' ').replace('-', ' ')
                if any(keyword in col_lower for keyword in keywords):
                    matching_columns.append(col)
            if matching_columns:
                healthcare_columns[category] = matching_columns

        return healthcare_columns

    def extract_healthcare_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Extract healthcare-specific indicators from the dataset."""
        indicators = {
            'has_patient_ids': False,
            'has_diagnosis_codes': False,
            'has_procedure_codes': False,
            'has_monetary_amounts': False,
            'has_dates': False,
            'estimated_record_type': 'unknown',
            'complexity_score': 0,
        }

        columns_lower = [col.lower() for col in df.columns]

        # Check for patient identifiers
        patient_patterns = ['patient', 'member', 'id', 'person']
        indicators['has_patient_ids'] = any(
            any(pattern in col for pattern in patient_patterns) for col in columns_lower
        )

        # Check for diagnosis codes
        diagnosis_patterns = ['diagnosis', 'icd', 'condition', 'dx']
        indicators['has_diagnosis_codes'] = any(
            any(pattern in col for pattern in diagnosis_patterns)
            for col in columns_lower
        )

        # Check for procedure codes
        procedure_patterns = ['procedure', 'cpt', 'service', 'treatment']
        indicators['has_procedure_codes'] = any(
            any(pattern in col for pattern in procedure_patterns)
            for col in columns_lower
        )

        # Check for monetary amounts
        amount_patterns = ['amount', 'cost', 'charge', 'price', 'payment']
        indicators['has_monetary_amounts'] = any(
            any(pattern in col for pattern in amount_patterns) for col in columns_lower
        )

        # Check for dates
        date_patterns = ['date', 'time', 'created', 'updated', 'service']
        indicators['has_dates'] = any(
            any(pattern in col for pattern in date_patterns) for col in columns_lower
        )

        # Estimate record type
        if indicators['has_diagnosis_codes'] and indicators['has_procedure_codes']:
            indicators['estimated_record_type'] = 'claims_data'
        elif indicators['has_diagnosis_codes']:
            indicators['estimated_record_type'] = 'clinical_data'
        elif indicators['has_procedure_codes']:
            indicators['estimated_record_type'] = 'services_data'
        elif indicators['has_patient_ids']:
            indicators['estimated_record_type'] = 'patient_data'

        # Calculate complexity score
        complexity_factors = [
            indicators['has_patient_ids'],
            indicators['has_diagnosis_codes'],
            indicators['has_procedure_codes'],
            indicators['has_monetary_amounts'],
            indicators['has_dates'],
            len(df.columns) > 10,
            len(df) > 1000,
        ]
        indicators['complexity_score'] = sum(complexity_factors)

        return indicators


class SmartDataSampler:
    """
    Smart data sampling for large CSV files with healthcare-aware strategies.

    Provides intelligent sampling that maintains statistical representativeness
    while optimizing for LLM validation performance.
    """

    def __init__(self, max_sample_size: int = 100):
        """
        Initialize smart data sampler.

        Args:
            max_sample_size: Maximum number of records to sample for LLM validation
        """
        self.max_sample_size = max_sample_size
        self.min_sample_size = 10
        self.context_builder = HealthcareContextBuilder()

        # Adaptive thresholds based on file size
        self.size_thresholds = {
            'small': 100,  # < 100 rows: use all data
            'medium': 1000,  # 100-1000 rows: 50% sample
            'large': 10000,  # 1K-10K rows: 20% sample
            'very_large': 100000,  # 10K+ rows: max sample size
        }

    def create_sample(
        self,
        df: pd.DataFrame,
        strategy: SamplingStrategy = SamplingStrategy.ADAPTIVE,
        target_size: Optional[int] = None,
    ) -> DataSample:
        """
        Create intelligent sample from DataFrame.

        Args:
            df: Input DataFrame to sample
            strategy: Sampling strategy to use
            target_size: Specific target sample size (overrides adaptive sizing)

        Returns:
            DataSample with sampled data and comprehensive metadata
        """
        logger.info(
            f"Creating sample from DataFrame with {len(df)} rows, {len(df.columns)} columns"
        )

        # Determine optimal sample size
        sample_size = self._calculate_optimal_sample_size(df, target_size)

        # Apply sampling strategy
        if strategy == SamplingStrategy.ADAPTIVE:
            strategy = self._select_best_strategy(df)

        sampled_df = self._apply_sampling_strategy(df, strategy, sample_size)

        # Extract metadata and statistics
        metadata = self._extract_metadata(df, sampled_df, strategy)

        # Build healthcare context
        context_summary = self._build_context_summary(df, metadata)

        # Calculate quality indicators
        quality_indicators = self._calculate_quality_indicators(df, sampled_df)

        # Convert to list of dictionaries
        sample_data = sampled_df.to_dict('records')

        sample = DataSample(
            sample_data=sample_data,
            metadata=metadata,
            context_summary=context_summary,
            quality_indicators=quality_indicators,
        )

        logger.info(
            f"Created sample: {len(sample_data)} records "
            f"({metadata.sample_ratio:.1%} of original) using {strategy.value} strategy"
        )

        return sample

    def _calculate_optimal_sample_size(
        self, df: pd.DataFrame, target_size: Optional[int] = None
    ) -> int:
        """Calculate optimal sample size based on dataset characteristics."""
        if target_size:
            return min(target_size, len(df), self.max_sample_size)

        dataset_size = len(df)

        if dataset_size <= self.size_thresholds['small']:
            return dataset_size  # Use all data for small datasets
        elif dataset_size <= self.size_thresholds['medium']:
            return min(int(dataset_size * 0.5), self.max_sample_size)
        elif dataset_size <= self.size_thresholds['large']:
            return min(int(dataset_size * 0.2), self.max_sample_size)
        else:
            # For very large datasets, use statistical confidence intervals
            # 95% confidence level, 5% margin of error
            statistical_sample = min(
                int((1.96**2 * 0.25) / (0.05**2)),  # ~385 for large populations
                self.max_sample_size,
            )
            return max(statistical_sample, self.min_sample_size)

    def _select_best_strategy(self, df: pd.DataFrame) -> SamplingStrategy:
        """Select the best sampling strategy based on data characteristics."""
        dataset_size = len(df)

        # Extract healthcare indicators
        healthcare_indicators = self.context_builder.extract_healthcare_indicators(df)

        # Healthcare-aware strategy for complex healthcare data
        if healthcare_indicators['complexity_score'] >= 4:
            return SamplingStrategy.HEALTHCARE_AWARE

        # Stratified for medium to large datasets
        if dataset_size >= self.size_thresholds['medium']:
            return SamplingStrategy.STRATIFIED

        # Random for smaller datasets
        return SamplingStrategy.RANDOM

    def _apply_sampling_strategy(
        self, df: pd.DataFrame, strategy: SamplingStrategy, sample_size: int
    ) -> pd.DataFrame:
        """Apply the specified sampling strategy."""

        if sample_size >= len(df):
            return df.copy()

        if strategy == SamplingStrategy.RANDOM:
            return df.sample(n=sample_size, random_state=42)

        elif strategy == SamplingStrategy.SYSTEMATIC:
            step = len(df) // sample_size
            indices = list(range(0, len(df), step))[:sample_size]
            return df.iloc[indices]

        elif strategy == SamplingStrategy.STRATIFIED:
            return self._stratified_sample(df, sample_size)

        elif strategy == SamplingStrategy.HEALTHCARE_AWARE:
            return self._healthcare_aware_sample(df, sample_size)

        else:
            # Fallback to random
            return df.sample(n=sample_size, random_state=42)

    def _stratified_sample(self, df: pd.DataFrame, sample_size: int) -> pd.DataFrame:
        """Create stratified sample from beginning, middle, and end of dataset."""
        total_rows = len(df)

        # Allocate samples across three sections
        section_size = sample_size // 3
        remainder = sample_size % 3

        # Section sizes with remainder distribution
        sections = {
            'beginning': section_size + (1 if remainder > 0 else 0),
            'middle': section_size + (1 if remainder > 1 else 0),
            'end': section_size,
        }

        # Sample from each section
        samples = []

        # Beginning section (first 20%)
        beginning_end = max(int(total_rows * 0.2), sections['beginning'])
        if sections['beginning'] > 0:
            beginning_sample = df.head(beginning_end).sample(
                n=min(sections['beginning'], beginning_end), random_state=42
            )
            samples.append(beginning_sample)

        # Middle section (40%-60%)
        middle_start = int(total_rows * 0.4)
        middle_end = int(total_rows * 0.6)
        middle_section = df.iloc[middle_start:middle_end]
        if sections['middle'] > 0 and len(middle_section) > 0:
            middle_sample = middle_section.sample(
                n=min(sections['middle'], len(middle_section)), random_state=42
            )
            samples.append(middle_sample)

        # End section (last 20%)
        end_start = max(int(total_rows * 0.8), total_rows - sections['end'])
        if sections['end'] > 0:
            end_sample = df.tail(total_rows - end_start).sample(
                n=min(sections['end'], total_rows - end_start), random_state=42
            )
            samples.append(end_sample)

        # Combine samples
        if samples:
            return pd.concat(samples, ignore_index=True)
        else:
            return df.sample(n=sample_size, random_state=42)

    def _healthcare_aware_sample(
        self, df: pd.DataFrame, sample_size: int
    ) -> pd.DataFrame:
        """Create healthcare-aware sample prioritizing records with complete data."""
        # Identify healthcare columns
        healthcare_columns = self.context_builder.identify_healthcare_columns(
            df.columns.tolist()
        )

        # Score records based on completeness of healthcare data
        df_copy = df.copy()
        df_copy['_healthcare_score'] = 0

        for category, columns in healthcare_columns.items():
            for col in columns:
                if col in df_copy.columns:
                    # Add points for non-null values in healthcare columns
                    df_copy['_healthcare_score'] += df_copy[col].notna().astype(int)

        # Sort by healthcare score (descending) and sample
        df_scored = df_copy.sort_values('_healthcare_score', ascending=False)

        # Take top scoring records, with some randomization
        top_portion = min(
            sample_size * 2, len(df_scored)
        )  # Consider top 2x sample size
        top_records = df_scored.head(top_portion)

        # Sample from top records
        final_sample = top_records.sample(
            n=min(sample_size, len(top_records)), random_state=42
        )

        # Remove scoring column
        return final_sample.drop(columns=['_healthcare_score'])

    def _extract_metadata(
        self,
        original_df: pd.DataFrame,
        sample_df: pd.DataFrame,
        strategy: SamplingStrategy,
    ) -> SampleMetadata:
        """Extract comprehensive metadata about the sampling process."""

        # Basic statistics
        original_size = len(original_df)
        sample_size = len(sample_df)
        sample_ratio = sample_size / original_size if original_size > 0 else 0

        # Null percentage calculation
        total_cells = original_df.size
        null_cells = original_df.isnull().sum().sum()
        null_percentage = (null_cells / total_cells * 100) if total_cells > 0 else 0

        # Column coverage
        original_columns = set(original_df.columns)
        sample_columns = set(sample_df.columns)
        column_coverage = (
            len(sample_columns & original_columns) / len(original_columns) * 100
        )

        # Data types distribution
        data_types_distribution = original_df.dtypes.value_counts().to_dict()
        data_types_distribution = {
            str(k): v for k, v in data_types_distribution.items()
        }

        # Healthcare indicators
        healthcare_indicators = self.context_builder.extract_healthcare_indicators(
            original_df
        )

        # Statistical summary
        numerical_columns = original_df.select_dtypes(include=[np.number]).columns
        statistical_summary = {}

        if len(numerical_columns) > 0:
            stats = original_df[numerical_columns].describe()
            statistical_summary = {
                'numerical_columns': len(numerical_columns),
                'mean_values': stats.loc['mean'].to_dict()
                if 'mean' in stats.index
                else {},
                'std_values': stats.loc['std'].to_dict()
                if 'std' in stats.index
                else {},
                'missing_percentages': (
                    original_df[numerical_columns].isnull().sum()
                    / len(original_df)
                    * 100
                ).to_dict(),
            }

        return SampleMetadata(
            original_size=original_size,
            sample_size=sample_size,
            sampling_strategy=strategy,
            sample_ratio=sample_ratio,
            null_percentage=null_percentage,
            column_coverage=column_coverage,
            data_types_distribution=data_types_distribution,
            healthcare_indicators=healthcare_indicators,
            statistical_summary=statistical_summary,
        )

    def _build_context_summary(self, df: pd.DataFrame, metadata: SampleMetadata) -> str:
        """Build human-readable context summary for LLM."""
        healthcare_cols = self.context_builder.identify_healthcare_columns(
            df.columns.tolist()
        )

        summary_parts = [
            f"Healthcare CSV dataset with {metadata.original_size:,} records and {len(df.columns)} columns.",
            f"Sample contains {metadata.sample_size} records ({metadata.sample_ratio:.1%} of total).",
        ]

        # Add healthcare context
        if healthcare_cols:
            col_summary = []
            for category, columns in healthcare_cols.items():
                col_summary.append(f"{len(columns)} {category} columns")
            summary_parts.append(f"Healthcare data includes: {', '.join(col_summary)}.")

        # Add data quality context
        summary_parts.append(
            f"Data completeness: {100 - metadata.null_percentage:.1f}% (null values: {metadata.null_percentage:.1f}%)."
        )

        # Add estimated record type
        record_type = metadata.healthcare_indicators.get(
            'estimated_record_type', 'unknown'
        )
        if record_type != 'unknown':
            summary_parts.append(
                f"Estimated record type: {record_type.replace('_', ' ')}."
            )

        return " ".join(summary_parts)

    def _calculate_quality_indicators(
        self, original_df: pd.DataFrame, sample_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """Calculate quality indicators for the sample."""

        indicators = {
            'representativeness_score': 0.0,
            'completeness_score': 0.0,
            'diversity_score': 0.0,
            'healthcare_relevance_score': 0.0,
        }

        # Representativeness score (based on statistical similarity)
        numerical_cols = original_df.select_dtypes(include=[np.number]).columns
        if len(numerical_cols) > 0:
            try:
                original_means = original_df[numerical_cols].mean()
                sample_means = sample_df[numerical_cols].mean()
                mean_differences = abs(original_means - sample_means) / (
                    original_means + 1e-6
                )
                indicators['representativeness_score'] = max(
                    0, 1 - mean_differences.mean()
                )
            except Exception:
                indicators[
                    'representativeness_score'
                ] = 0.5  # Default if calculation fails

        # Completeness score (percentage of non-null values in sample)
        total_sample_cells = sample_df.size
        non_null_sample_cells = sample_df.count().sum()
        indicators['completeness_score'] = (
            (non_null_sample_cells / total_sample_cells)
            if total_sample_cells > 0
            else 0
        )

        # Diversity score (based on unique values in categorical columns)
        categorical_cols = sample_df.select_dtypes(include=['object']).columns
        if len(categorical_cols) > 0:
            diversity_scores = []
            for col in categorical_cols:
                unique_ratio = sample_df[col].nunique() / len(sample_df)
                diversity_scores.append(min(unique_ratio, 1.0))
            indicators['diversity_score'] = (
                np.mean(diversity_scores) if diversity_scores else 0
            )

        # Healthcare relevance score
        healthcare_indicators = self.context_builder.extract_healthcare_indicators(
            sample_df
        )
        indicators['healthcare_relevance_score'] = (
            healthcare_indicators['complexity_score'] / 7.0
        )  # Normalized to 0-1

        return indicators


if __name__ == "__main__":
    """
    Debug and testing section for smart data sampling.

    Tests sampling strategies with sample healthcare data.
    """

    # Setup logging
    logger.add("debug_data_sampler.log")

    print("=" * 80)
    print("Smart Data Sampler - Debug Mode")
    print("=" * 80)

    # Create sample healthcare DataFrame
    np.random.seed(42)
    random.seed(42)

    sample_data = {
        'patient_id': [f'P{i:04d}' for i in range(1000)],
        'member_id': [f'M{i:04d}' for i in range(1000)],
        'diagnosis_code': np.random.choice(
            ['E11.9', 'M54.5', 'I10', 'J45.9', None], 1000, p=[0.3, 0.2, 0.2, 0.2, 0.1]
        ),
        'procedure_code': np.random.choice(
            ['99213', '99214', '83036', '45378', None],
            1000,
            p=[0.25, 0.25, 0.2, 0.2, 0.1],
        ),
        'service_date': pd.date_range('2024-01-01', periods=1000, freq='D'),
        'amount': np.random.uniform(50, 500, 1000),
        'provider_id': [f'PROV{i%50:03d}' for i in range(1000)],
        'claim_status': np.random.choice(
            ['approved', 'pending', 'denied'], 1000, p=[0.7, 0.2, 0.1]
        ),
    }

    # Add some null values to simulate real data
    for col in ['diagnosis_code', 'procedure_code']:
        null_indices = np.random.choice(1000, 100, replace=False)
        for idx in null_indices:
            sample_data[col][idx] = None

    df = pd.DataFrame(sample_data)

    print("\n🔧 Step 1: Test Dataset Created")
    print("-" * 50)
    print(f"   Dataset size: {len(df)} rows, {len(df.columns)} columns")
    print(f"   Columns: {list(df.columns)}")

    # Initialize sampler
    sampler = SmartDataSampler(max_sample_size=50)

    try:
        print("\n🔧 Step 2: Test Different Sampling Strategies")
        print("-" * 50)

        strategies = [
            SamplingStrategy.ADAPTIVE,
            SamplingStrategy.STRATIFIED,
            SamplingStrategy.HEALTHCARE_AWARE,
            SamplingStrategy.RANDOM,
        ]

        results = {}

        for strategy in strategies:
            print(f"\n   Testing {strategy.value} strategy...")

            sample = sampler.create_sample(df, strategy=strategy)
            results[strategy.value] = sample

            print(f"   ✅ Sample created: {len(sample.sample_data)} records")
            print(f"      Sample ratio: {sample.metadata.sample_ratio:.1%}")
            print("      Quality scores:")
            print(
                f"        - Representativeness: {sample.quality_indicators['representativeness_score']:.3f}"
            )
            print(
                f"        - Completeness: {sample.quality_indicators['completeness_score']:.3f}"
            )
            print(
                f"        - Healthcare relevance: {sample.quality_indicators['healthcare_relevance_score']:.3f}"
            )

        print("\n🔧 Step 3: Healthcare Context Analysis")
        print("-" * 50)

        # Test healthcare context building
        context_builder = HealthcareContextBuilder()
        healthcare_cols = context_builder.identify_healthcare_columns(
            df.columns.tolist()
        )
        healthcare_indicators = context_builder.extract_healthcare_indicators(df)

        print("   Healthcare columns identified:")
        for category, columns in healthcare_cols.items():
            print(f"     - {category}: {columns}")

        print("   Healthcare indicators:")
        for key, value in healthcare_indicators.items():
            print(f"     - {key}: {value}")

        print("\n🔧 Step 4: Context Summary Example")
        print("-" * 50)

        adaptive_sample = results['adaptive']
        print("   Context summary:")
        print(f"   {adaptive_sample.context_summary}")

        # Save results for inspection
        output_data = {
            'test_metadata': {
                'original_dataset_size': len(df),
                'original_columns': list(df.columns),
                'test_timestamp': pd.Timestamp.now().isoformat(),
            },
            'sampling_results': {},
        }

        for strategy_name, sample in results.items():
            output_data['sampling_results'][strategy_name] = {
                'sample_size': len(sample.sample_data),
                'metadata': {
                    'sample_ratio': sample.metadata.sample_ratio,
                    'null_percentage': sample.metadata.null_percentage,
                    'healthcare_indicators': sample.metadata.healthcare_indicators,
                    'sampling_strategy': sample.metadata.sampling_strategy.value,
                },
                'quality_indicators': sample.quality_indicators,
                'context_summary': sample.context_summary,
                'sample_preview': sample.sample_data[:3],  # First 3 records for preview
            }

        with open("debug_data_sampler_results.json", "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
        print("\n   Detailed results saved to: debug_data_sampler_results.json")

    except Exception as e:
        print("\n❌ Error during sampling:")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback

        print("\n📋 Full traceback:")
        traceback.print_exc()
        exit(1)

    print("\n🎉 Smart data sampling debug session completed successfully!")
    print("=" * 80)
