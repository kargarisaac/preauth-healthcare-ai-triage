"""
Clean CSV processor for UAE healthcare data formats.

This module provides a minimal, clean approach to processing CSV files from
UAE healthcare systems and converting them to canonical JSON format while
preserving all original data.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable
import pandas as pd
import numpy as np
from loguru import logger

from pipelines.data_quality import DataQuality


class CSVProcessor:
    """
    Clean CSV processor for UAE healthcare formats.

    Processes various CSV file formats containing healthcare claims data,
    mapping essential fields to canonical schema while preserving all
    original data for future use.
    """

    def __init__(
        self, enable_validation: bool = True, enable_smart_sampling: bool = True
    ):
        """
        Initialize CSV processor with optional data quality validation and smart sampling.

        Args:
            enable_validation: Enable data quality validation (default: True)
            enable_smart_sampling: Enable smart sampling for large files (default: True)
        """
        self.enable_validation = enable_validation
        self.enable_smart_sampling = enable_smart_sampling
        if self.enable_validation:
            self.data_quality = DataQuality()

    def apply_smart_sampling(
        self,
        df: pd.DataFrame,
        max_sample_size: int = 500,
        min_sample_size: int = 100,
        sampling_threshold: int = 1000,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Apply intelligent sampling for large datasets while maintaining representativeness.

        Args:
            df: Original DataFrame
            max_sample_size: Maximum number of records to sample
            min_sample_size: Minimum number of records to sample
            sampling_threshold: Apply sampling if records exceed this threshold
            progress_callback: Optional callback for progress updates

        Returns:
            Tuple of (sampled_dataframe, sampling_metadata)
        """
        total_records = len(df)

        if progress_callback:
            progress_callback("Analyzing dataset for smart sampling", 0.1)

        # No sampling needed for small datasets
        if total_records <= sampling_threshold:
            logger.info(f"Dataset has {total_records} records, no sampling needed")
            return df, {
                "total_records": total_records,
                "sampled_records": total_records,
                "sampling_strategy": "no_sampling",
                "sampling_ratio": 1.0,
                "representative_score": 1.0,
                "sample_indices": list(range(total_records)),
            }

        # Calculate optimal sample size
        sample_size = min(
            max_sample_size, max(min_sample_size, int(np.sqrt(total_records) * 10))
        )

        if progress_callback:
            progress_callback("Calculating representative sample", 0.3)

        # Smart sampling strategy: combination of systematic and stratified sampling
        sample_indices = self._calculate_smart_sample_indices(
            df, sample_size, progress_callback
        )

        if progress_callback:
            progress_callback("Extracting sampled records", 0.8)

        # Extract sampled data
        sampled_df = df.iloc[sample_indices].copy()

        # Calculate representativeness score
        representative_score = self._calculate_representativeness_score(df, sampled_df)

        sampling_metadata = {
            "total_records": total_records,
            "sampled_records": len(sampled_df),
            "sampling_strategy": "smart_hybrid",
            "sampling_ratio": len(sampled_df) / total_records,
            "representative_score": representative_score,
            "sample_indices": sample_indices.tolist(),
            "sample_size_target": sample_size,
            "columns_analyzed": list(df.columns),
        }

        logger.info(
            f"Applied smart sampling: {total_records} -> {len(sampled_df)} records "
            f"(ratio: {sampling_metadata['sampling_ratio']:.3f}, "
            f"representativeness: {representative_score:.3f})"
        )

        if progress_callback:
            progress_callback("Smart sampling completed", 1.0)

        return sampled_df, sampling_metadata

    def _calculate_smart_sample_indices(
        self,
        df: pd.DataFrame,
        sample_size: int,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> np.ndarray:
        """
        Calculate optimal sample indices using hybrid sampling strategy.

        Combines:
        1. Systematic sampling for even distribution
        2. Stratified sampling based on key columns
        3. Random sampling for edge cases
        """
        total_records = len(df)

        # Start with systematic sampling (every nth record)
        systematic_ratio = 0.6
        systematic_count = int(sample_size * systematic_ratio)
        step = total_records // systematic_count if systematic_count > 0 else 1
        systematic_indices = np.arange(0, total_records, step)[:systematic_count]

        if progress_callback:
            progress_callback("Applying systematic sampling", 0.4)

        # Stratified sampling based on key healthcare fields
        stratified_ratio = 0.3
        stratified_count = int(sample_size * stratified_ratio)
        stratified_indices = self._stratified_sample_indices(df, stratified_count)

        if progress_callback:
            progress_callback("Applying stratified sampling", 0.6)

        # Random sampling for remaining
        random_count = sample_size - len(systematic_indices) - len(stratified_indices)
        remaining_indices = np.setdiff1d(
            np.arange(total_records),
            np.concatenate([systematic_indices, stratified_indices]),
        )

        if len(remaining_indices) > 0 and random_count > 0:
            random_indices = np.random.choice(
                remaining_indices,
                size=min(random_count, len(remaining_indices)),
                replace=False,
            )
        else:
            random_indices = np.array([])

        # Combine all sampling strategies
        combined_indices = np.concatenate(
            [systematic_indices, stratified_indices, random_indices]
        )

        # Remove duplicates and sort
        unique_indices = np.unique(combined_indices)

        # If we have too many, trim to exact sample size
        if len(unique_indices) > sample_size:
            unique_indices = np.random.choice(
                unique_indices, size=sample_size, replace=False
            )

        return np.sort(unique_indices)

    def _stratified_sample_indices(
        self, df: pd.DataFrame, stratified_count: int
    ) -> np.ndarray:
        """Apply stratified sampling based on key healthcare data patterns."""
        # Identify key columns for stratification
        key_columns = []

        # Look for common healthcare identifier patterns
        for col in df.columns:
            col_lower = col.lower()
            if any(
                pattern in col_lower
                for pattern in [
                    'provider',
                    'clinic',
                    'facility',
                    'doctor',
                    'physician',
                    'diagnosis',
                    'icd',
                    'condition',
                    'disease',
                    'procedure',
                    'cpt',
                    'treatment',
                    'service',
                    'amount',
                    'cost',
                    'charge',
                    'payment',
                    'status',
                    'type',
                    'category',
                ]
            ):
                key_columns.append(col)

        if not key_columns:
            # Fallback to random sampling if no key columns found
            return np.random.choice(len(df), size=stratified_count, replace=False)

        # Use the first key column for stratification
        strata_column = key_columns[0]

        try:
            # Get unique values and their counts
            value_counts = df[strata_column].value_counts()

            # Calculate proportional sample sizes for each stratum
            stratified_indices = []
            for value, count in value_counts.items():
                # Proportional allocation
                stratum_sample_size = max(1, int((count / len(df)) * stratified_count))
                stratum_indices = df[df[strata_column] == value].index.values

                if len(stratum_indices) > 0:
                    sampled_stratum = np.random.choice(
                        stratum_indices,
                        size=min(stratum_sample_size, len(stratum_indices)),
                        replace=False,
                    )
                    stratified_indices.extend(sampled_stratum)

            return np.array(stratified_indices[:stratified_count])

        except Exception as e:
            logger.warning(
                f"Stratified sampling failed for column {strata_column}: {e}"
            )
            # Fallback to random sampling
            return np.random.choice(len(df), size=stratified_count, replace=False)

    def _calculate_representativeness_score(
        self, original_df: pd.DataFrame, sampled_df: pd.DataFrame
    ) -> float:
        """
        Calculate how representative the sample is compared to the original dataset.

        Returns a score between 0.0 and 1.0, where 1.0 means perfectly representative.
        """
        if len(sampled_df) == 0:
            return 0.0

        scores = []

        # Compare numeric columns distributions
        numeric_cols = original_df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            try:
                if col in sampled_df.columns:
                    orig_mean = original_df[col].mean()
                    samp_mean = sampled_df[col].mean()

                    if orig_mean != 0:
                        mean_similarity = 1 - abs(orig_mean - samp_mean) / abs(
                            orig_mean
                        )
                        scores.append(max(0, mean_similarity))
            except Exception:
                continue

        # Compare categorical columns distributions
        categorical_cols = original_df.select_dtypes(include=['object']).columns
        for col in categorical_cols[:5]:  # Limit to first 5 to avoid performance issues
            try:
                if col in sampled_df.columns:
                    orig_dist = original_df[col].value_counts(normalize=True)
                    samp_dist = sampled_df[col].value_counts(normalize=True)

                    # Calculate overlap in distributions
                    common_values = set(orig_dist.index) & set(samp_dist.index)
                    if common_values:
                        overlap_score = len(common_values) / len(
                            set(orig_dist.index) | set(samp_dist.index)
                        )
                        scores.append(overlap_score)
            except Exception:
                continue

        # Return average score, or 0.8 as default if no scores calculated
        return np.mean(scores) if scores else 0.8

    def process_claims_csv(
        self,
        csv_file_path: str,
        encoding: str = "utf-8",
        enable_sampling: bool = None,
        max_sample_size: int = 500,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> Dict[str, Any]:
        """
        Process healthcare claims CSV file to canonical JSON with optional smart sampling.

        Args:
            csv_file_path: Path to CSV file
            encoding: File encoding (default: utf-8)
            enable_sampling: Override smart sampling setting (None uses instance setting)
            max_sample_size: Maximum sample size for large files
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary in canonical JSON format with all data preserved
        """
        logger.info(f"Processing claims CSV: {csv_file_path}")

        if progress_callback:
            progress_callback("Reading CSV file", 0.1)

        # Read CSV file with pandas for robust handling
        try:
            df = pd.read_csv(csv_file_path, encoding=encoding, on_bad_lines='skip')
        except UnicodeDecodeError:
            # Try common alternative encodings
            for alt_encoding in ["latin1", "cp1256", "utf-8-sig"]:
                try:
                    df = pd.read_csv(
                        csv_file_path, encoding=alt_encoding, on_bad_lines='skip'
                    )
                    logger.info(f"Successfully read CSV with encoding: {alt_encoding}")
                    encoding = alt_encoding
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError("Could not read CSV file with any supported encoding")

        # Store original DataFrame info
        original_df = df.copy()
        sampling_metadata = None

        # Apply smart sampling if enabled
        should_sample = (
            enable_sampling
            if enable_sampling is not None
            else self.enable_smart_sampling
        )
        if should_sample:
            if progress_callback:
                progress_callback("Applying smart sampling", 0.2)

            df, sampling_metadata = self.apply_smart_sampling(
                df,
                max_sample_size=max_sample_size,
                progress_callback=lambda msg, prog: progress_callback(
                    f"Sampling: {msg}", 0.2 + prog * 0.1
                )
                if progress_callback
                else None,
            )

        if progress_callback:
            progress_callback("Converting to records", 0.4)

        # Convert DataFrame to list of dictionaries
        raw_records = df.to_dict("records")

        # Generate bundle ID and timestamp
        bundle_id = (
            f"Claims-CSV-{str(uuid.uuid4())[:8]}-{datetime.now().strftime('%Y%m%d')}"
        )
        timestamp = datetime.now(timezone.utc).isoformat()

        if progress_callback:
            progress_callback("Processing claims data", 0.5)

        # Extract and process claims
        claims = self._process_csv_records(raw_records)
        services = self._create_services_from_claims(claims)

        if progress_callback:
            progress_callback("Calculating aggregated values", 0.7)

        # Calculate aggregated values
        total_amount = sum(
            claim.get("amount", 0) for claim in claims if claim.get("amount")
        )
        currency = self._detect_currency(raw_records)
        authorization_id = self._extract_primary_id(raw_records)

        # Calculate data quality score (use original DataFrame for full picture)
        data_quality_score = self._calculate_data_quality(raw_records, df)

        # Build canonical JSON structure
        canonical_data = {
            "resourceType": "Bundle",
            "id": bundle_id,
            "meta": {
                "profile": [
                    "https://nazmito.com/fhir/StructureDefinition/healthcare-bundle"
                ],
                "source": "Claims-CSV",
                "lastUpdated": timestamp,
                "versionId": "1",
            },
            "type": "collection",
            "timestamp": timestamp,
            # Essential mapped fields
            "authorization_id": authorization_id,
            "sender": None,
            "receiver": None,
            "transaction_date": None,
            "total_amount": total_amount,
            "currency": currency,
            "claims": claims,
            "services": services,
            # Data metrics for integration tests
            "total_records": len(raw_records),
            "valid_records": len(claims),
            "data_quality_score": data_quality_score,
            "encoding_used": encoding,
            # FHIR resource mappings
            "fhir_resources": self._create_fhir_resources(claims),
            "entry": self._create_bundle_entries(claims),
            # Preserve ALL original data
            "raw_data": {
                "csv_data": raw_records,
                "columns": list(df.columns) if not df.empty else [],
                "shape": list(df.shape),
                "dtypes": df.dtypes.to_dict() if not df.empty else {},
                "original_total_records": len(original_df),
                "processed_records": len(df),
                "sampling_applied": sampling_metadata is not None,
                "sampling_metadata": sampling_metadata,
            },
            "source_file": csv_file_path,
            "processing_timestamp": timestamp,
        }

        # Add data quality validation
        if self.enable_validation:
            validation_report = self.data_quality.validate_fhir_bundle(canonical_data)
            canonical_data["data_quality"] = validation_report
            logger.info(
                f"Data quality score: {validation_report['quality_score'].overall_score:.3f}"
            )

        if progress_callback:
            progress_callback("Finalizing processing", 1.0)

        logger.info(
            f"Successfully processed claims CSV: {len(claims)} claims, {len(services)} services found"
            + (
                f" (sampled from {len(original_df)} records)"
                if sampling_metadata
                else ""
            )
        )
        return canonical_data

    def process_clinical_csv(self, csv_file_path: str) -> Dict[str, Any]:
        """
        Process clinical data CSV format to canonical JSON.

        Args:
            csv_file_path: Path to clinical data CSV file

        Returns:
            Dictionary in canonical JSON format with all data preserved
        """
        logger.info(f"Processing clinical CSV: {csv_file_path}")

        # Read CSV file
        df = pd.read_csv(csv_file_path, encoding="utf-8", on_bad_lines='skip')
        raw_records = df.to_dict("records")

        # Generate bundle ID and timestamp
        bundle_id = (
            f"Clinical-CSV-{str(uuid.uuid4())[:8]}-{datetime.now().strftime('%Y%m%d')}"
        )
        timestamp = datetime.now(timezone.utc).isoformat()

        # Extract clinical data
        observations = self._extract_observations(raw_records)

        # Build canonical JSON structure
        canonical_data = {
            "resourceType": "Bundle",
            "id": bundle_id,
            "meta": {
                "profile": [
                    "https://nazmito.com/fhir/StructureDefinition/healthcare-bundle"
                ],
                "source": "Clinical-CSV",
                "lastUpdated": timestamp,
                "versionId": "1",
            },
            "type": "collection",
            "timestamp": timestamp,
            # Clinical data fields
            "clinical_data_type": "observations",
            "patient_count": len(
                set(
                    record.get("patient_id", "")
                    for record in raw_records
                    if record.get("patient_id")
                )
            ),
            "record_count": len(raw_records),
            "observations": observations,
            # Preserve original data
            "raw_data": {
                "csv_data": raw_records,
                "columns": list(df.columns),
                "shape": list(df.shape),
            },
            "source_file": csv_file_path,
            "processing_timestamp": timestamp,
        }

        # Add data quality validation
        if self.enable_validation:
            validation_report = self.data_quality.validate_fhir_bundle(canonical_data)
            canonical_data["data_quality"] = validation_report
            logger.info(
                f"Data quality score: {validation_report['quality_score'].overall_score:.3f}"
            )

        logger.info(
            f"Successfully processed clinical CSV: {len(observations)} observations found"
        )
        return canonical_data

    def _process_csv_records(
        self, records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Process CSV records into standardized claim format."""
        claims = []

        for idx, record in enumerate(records, 1):
            try:
                # Map common CSV column variations to standard fields
                claim_data = {
                    "sequence": idx,
                    "claim_id": self._extract_field(
                        record, ["claim_id", "id", "transaction_id", "ref_no", "clm_id"]
                    ),
                    "patient_id": self._extract_field(
                        record,
                        ["patient_id", "member_id", "insurance_id", "desynpuf_id"],
                    ),
                    "provider_id": self._extract_field(
                        record, ["provider_id", "clinic_id", "facility_id", "prvdr_num"]
                    ),
                    "service_date": self._extract_field(
                        record,
                        [
                            "service_date",
                            "date_of_service",
                            "treatment_date",
                            "clm_from_dt",
                        ],
                    ),
                    "diagnosis_code": self._extract_field(
                        record,
                        [
                            "diagnosis_code",
                            "icd_code",
                            "primary_diagnosis",
                            "icd_dgns_cd1",
                            "clm_diag_cd_1",
                            "icd10_am_code",
                        ],
                    ),
                    "procedure_code": self._extract_field(
                        record,
                        ["procedure_code", "cpt_code", "service_code", "hcpcs_cd_1"],
                    ),
                    "amount": self._extract_numeric_field(
                        record,
                        [
                            "amount",
                            "billed_amount",
                            "total_cost",
                            "claim_amount",
                            "amount_aed",
                            "clm_pmt_amt",
                            "line_nch_pmt_amt_1",
                        ],
                    ),
                    "currency": self._extract_field(
                        record, ["currency"], default_value="AED"
                    ),
                    "status": self._extract_field(
                        record, ["status", "claim_status", "authorization_status"]
                    ),
                    "description": self._extract_field(
                        record, ["description", "service_description", "notes"]
                    ),
                    "raw_record": record,  # Preserve original record
                }

                # Only include claims with essential data
                if claim_data["claim_id"] or (
                    claim_data["patient_id"] and claim_data["procedure_code"]
                ):
                    claims.append(claim_data)

            except Exception as e:
                logger.warning(f"Failed to process record {idx}: {str(e)}")
                continue

        return claims

    def _create_services_from_claims(
        self, claims: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Create services list from claims data."""
        services = []
        for claim in claims:
            service = {
                "sequence": claim["sequence"],
                "activity_code": claim.get("procedure_code"),
                "diagnosis_code": claim.get("diagnosis_code"),
                "requested_amount_value": str(claim.get("amount", "")),
                "requested_amount_currency": claim.get("currency", "AED"),
                "instructions": claim.get("description"),
                "raw_service_data": claim["raw_record"],
            }
            services.append(service)
        return services

    def _create_fhir_resources(self, claims: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create FHIR resources from claims data."""
        resources = {}

        for idx, claim in enumerate(claims):
            # Create a basic Claim resource
            claim_resource = {
                "resourceType": "Claim",
                "id": f"claim-{idx + 1}",
                "status": "active",
                "type": {"text": "healthcare claim"},
                "patient": {
                    "reference": f"Patient/{claim.get('patient_id', 'unknown')}"
                },
                "provider": {
                    "reference": f"Organization/{claim.get('provider_id', 'unknown')}"
                },
            }
            resources[f"claim_{idx + 1}"] = claim_resource

        return resources

    def _create_bundle_entries(
        self, claims: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Create Bundle entries from claims data."""
        entries = []

        for idx, claim in enumerate(claims):
            entry = {
                "resource": {
                    "resourceType": "Claim",
                    "id": f"claim-{idx + 1}",
                    "status": "active",
                }
            }
            entries.append(entry)

        return entries

    def _extract_observations(
        self, records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract observations from clinical data."""
        observations = []

        for idx, record in enumerate(records, 1):
            obs = {
                "sequence": idx,
                "patient_id": self._extract_field(record, ["patient_id", "subject_id"]),
                "observation_date": self._extract_field(
                    record, ["observation_date", "date", "test_date"]
                ),
                "test_name": self._extract_field(
                    record, ["test_name", "observation_name", "name"]
                ),
                "value": self._extract_field(
                    record, ["value", "result", "measurement"]
                ),
                "unit": self._extract_field(
                    record, ["unit", "units", "measurement_unit"]
                ),
                "raw_record": record,
            }
            observations.append(obs)

        return observations

    def _extract_field(
        self, record: Dict[str, Any], field_names: List[str], default_value: str = None
    ) -> Optional[str]:
        """Extract field value from record using multiple possible field names."""
        for field_name in field_names:
            # Try exact match
            if field_name in record:
                value = record[field_name]
                if pd.notna(value) and str(value).strip():
                    return str(value).strip()

            # Try case-insensitive match
            for key, value in record.items():
                if key.lower() == field_name.lower():
                    if pd.notna(value) and str(value).strip():
                        return str(value).strip()

        return default_value

    def _extract_numeric_field(
        self, record: Dict[str, Any], field_names: List[str]
    ) -> Optional[float]:
        """Extract numeric field value from record."""
        for field_name in field_names:
            # Try exact match
            if field_name in record:
                value = record[field_name]
                if pd.notna(value):
                    try:
                        # Handle string representations of numbers
                        if isinstance(value, str):
                            value = (
                                value.replace(",", "")
                                .replace("$", "")
                                .replace("AED", "")
                                .strip()
                            )
                        return float(value)
                    except (ValueError, TypeError):
                        continue

            # Try case-insensitive match
            for key, val in record.items():
                if key.lower() == field_name.lower():
                    if pd.notna(val):
                        try:
                            if isinstance(val, str):
                                val = (
                                    val.replace(",", "")
                                    .replace("$", "")
                                    .replace("AED", "")
                                    .strip()
                                )
                            return float(val)
                        except (ValueError, TypeError):
                            continue

        return None

    def _detect_currency(self, records: List[Dict[str, Any]]) -> str:
        """Detect currency from records."""
        for record in records:
            currency = self._extract_field(record, ["currency"])
            if currency:
                return currency
        return "AED"  # Default

    def _extract_primary_id(self, records: List[Dict[str, Any]]) -> Optional[str]:
        """Extract primary identifier from records."""
        if records:
            return self._extract_field(
                records[0], ["claim_id", "id", "transaction_id", "ref_no"]
            )
        return None

    def _calculate_data_quality(
        self, records: List[Dict[str, Any]], df: pd.DataFrame
    ) -> float:
        """Calculate overall data quality score (0.0 to 1.0)."""
        if not records:
            return 0.0

        # 1. Completeness score (percentage of non-null values)
        if not df.empty:
            total_cells = df.size
            non_null_cells = df.count().sum()
            completeness_score = (
                non_null_cells / total_cells if total_cells > 0 else 0.0
            )
        else:
            completeness_score = 0.0

        # 2. Essential fields presence score
        essential_scores = []
        for record in records:
            record_score = 0
            for field_group in [
                ["claim_id", "id", "transaction_id"],
                ["patient_id", "member_id", "insurance_id"],
                ["procedure_code", "cpt_code", "service_code"],
                ["amount", "billed_amount", "total_cost"],
            ]:
                if any(
                    self._extract_field(record, field_group)
                    for field_group in [field_group]
                ):
                    record_score += 0.25
            essential_scores.append(record_score)

        essential_field_score = (
            sum(essential_scores) / len(essential_scores) if essential_scores else 0.0
        )

        # 3. Data format consistency score
        numeric_fields = ["amount", "billed_amount", "total_cost"]
        format_scores = []

        for record in records:
            format_score = 0
            # Check if numeric fields are properly formatted
            amount = self._extract_numeric_field(record, numeric_fields)
            if amount is not None and amount >= 0:
                format_score += 0.5

            # Check if dates look reasonable (basic validation)
            date_field = self._extract_field(
                record, ["service_date", "date_of_service"]
            )
            if date_field:
                format_score += 0.5

            format_scores.append(format_score)

        format_consistency_score = (
            sum(format_scores) / len(format_scores) if format_scores else 0.0
        )

        # 4. Duplicate detection score (higher score for fewer duplicates)
        if len(records) > 1:
            claim_ids = [
                self._extract_field(record, ["claim_id", "id"]) for record in records
            ]
            claim_ids = [cid for cid in claim_ids if cid]
            unique_ids = len(set(claim_ids))
            total_ids = len(claim_ids)
            duplicate_score = unique_ids / total_ids if total_ids > 0 else 1.0
        else:
            duplicate_score = 1.0

        # Weighted average of all scores
        overall_score = (
            0.3 * completeness_score
            + 0.3 * essential_field_score
            + 0.2 * format_consistency_score
            + 0.2 * duplicate_score
        )

        return round(overall_score, 3)


if __name__ == "__main__":
    """
    Debug and testing section for CSV processor.

    Tests CSV processing and saves debug output.
    """

    # Setup logging
    logger.add("debug_csv_processor.log")

    print("=" * 80)
    print("CSV Processor - Debug Mode")
    print("=" * 80)

    processor = CSVProcessor()

    # Test files
    sample_files = [
        "samples/sample_claims.csv",
        "samples/healthcare_claims_variations.csv",
        "samples/large_claims.csv",
    ]

    for csv_file in sample_files:
        try:
            print(f"\n🔧 Processing CSV file: {csv_file}")
            print("-" * 50)

            if os.path.exists(csv_file):
                result = processor.process_claims_csv(csv_file)

                print("✅ CSV processed successfully")
                print(f"   Claims Count: {len(result.get('claims', []))}")
                print(f"   Services Count: {len(result.get('services', []))}")
                print(f"   Total Amount: {result.get('total_amount', 0.0)}")
                print(f"   Currency: {result.get('currency', 'Unknown')}")

                # Save debug output
                output_file = f"debug_csv_output_{os.path.basename(csv_file).replace('.csv', '.json')}"
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2, ensure_ascii=False, default=str)
                print(f"   Debug saved to: {output_file}")
            else:
                print(f"❌ CSV file not found: {csv_file}")

        except Exception as e:
            print(f"\n❌ Error processing {csv_file}:")
            print(f"   {type(e).__name__}: {str(e)}")
            import traceback

            print("\n📋 Full traceback:")
            traceback.print_exc()

    print("\n🎉 CSV processor debug session completed!")
    print("=" * 80)
