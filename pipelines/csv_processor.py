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
from typing import Dict, Any, List, Optional
import pandas as pd
from loguru import logger

from pipelines.data_quality import DataQuality


class CSVProcessor:
    """
    Clean CSV processor for UAE healthcare formats.

    Processes various CSV file formats containing healthcare claims data,
    mapping essential fields to canonical schema while preserving all
    original data for future use.
    """

    def __init__(self, enable_validation: bool = True):
        """
        Initialize CSV processor with optional data quality validation.

        Args:
            enable_validation: Enable data quality validation (default: True)
        """
        self.enable_validation = enable_validation
        if self.enable_validation:
            self.data_quality = DataQuality()

    def process_claims_csv(
        self, csv_file_path: str, encoding: str = "utf-8"
    ) -> Dict[str, Any]:
        """
        Process healthcare claims CSV file to canonical JSON.

        Args:
            csv_file_path: Path to CSV file
            encoding: File encoding (default: utf-8)

        Returns:
            Dictionary in canonical JSON format with all data preserved
        """
        logger.info(f"Processing claims CSV: {csv_file_path}")

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

        # Convert DataFrame to list of dictionaries
        raw_records = df.to_dict("records")

        # Generate bundle ID and timestamp
        bundle_id = (
            f"Claims-CSV-{str(uuid.uuid4())[:8]}-{datetime.now().strftime('%Y%m%d')}"
        )
        timestamp = datetime.now(timezone.utc).isoformat()

        # Extract and process claims
        claims = self._process_csv_records(raw_records)
        services = self._create_services_from_claims(claims)

        # Calculate aggregated values
        total_amount = sum(
            claim.get("amount", 0) for claim in claims if claim.get("amount")
        )
        currency = self._detect_currency(raw_records)
        authorization_id = self._extract_primary_id(raw_records)

        # Calculate data quality score
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
            f"Successfully processed claims CSV: {len(claims)} claims, {len(services)} services found"
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
