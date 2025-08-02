"""
Unit tests for CSVProcessor functionality (Simplified).

This module tests the existing CSVProcessor implementation,
focusing on core functionality and Bundle structure validation.
"""

import pytest
import os
import tempfile
from pipelines.csv_processor import CSVProcessor


class TestCSVProcessorSimplified:
    """Simplified unit tests for existing CSV processor."""

    @pytest.fixture
    def processor(self):
        """Create CSVProcessor instance."""
        return CSVProcessor()

    @pytest.fixture
    def temp_csv_file(self):
        """
        Fixture that provides a temporary CSV file that gets cleaned up.
        """
        temp_files = []

        def create_temp_csv(content: str, filename: str = "test.csv") -> str:
            """Create a temporary CSV file with given content."""
            temp_file = tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.csv',
                prefix=filename.replace('.csv', '_'),
                delete=False,
                encoding='utf-8',
            )
            temp_file.write(content)
            temp_file.close()
            temp_files.append(temp_file.name)
            return temp_file.name

        yield create_temp_csv

        # Cleanup
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except (OSError, FileNotFoundError):
                pass

    def test_basic_csv_processing(self, processor, temp_csv_file):
        """Test basic CSV processing functionality."""
        csv_content = """claim_id,patient_id,amount
TXN-001,P123456,125.50
TXN-002,P789012,250.00"""

        csv_file = temp_csv_file(csv_content, "test_basic.csv")
        result = processor.process_claims_csv(csv_file)

        # Test canonical JSON structure
        assert result['resourceType'] == 'Bundle'
        assert result['meta']['source'] == 'Claims-CSV'
        assert len(result['claims']) == 2
        assert 'raw_data' in result

    def test_bundle_structure(self, processor, temp_csv_file):
        """Test Bundle structure compliance."""
        csv_content = """claim_id,patient_id,amount
TXN-123,P456789,100.00"""

        csv_file = temp_csv_file(csv_content, "test_bundle.csv")
        result = processor.process_claims_csv(csv_file)

        # Test Bundle structure
        assert result['resourceType'] == 'Bundle'
        assert 'id' in result
        assert result['id'].startswith('Claims-CSV-')
        assert result['type'] == 'collection'

        # Test meta information
        meta = result['meta']
        assert meta['source'] == 'Claims-CSV'
        assert 'lastUpdated' in meta
        assert 'versionId' in meta

    def test_claims_and_services_extraction(self, processor, temp_csv_file):
        """Test extraction of claims and services."""
        csv_content = """claim_id,patient_id,procedure_code,amount
TXN-001,P123456,83036,125.50
TXN-002,P789012,99213,250.00"""

        csv_file = temp_csv_file(csv_content, "test_extract.csv")
        result = processor.process_claims_csv(csv_file)

        # Test extraction
        assert len(result['claims']) == 2
        assert len(result['services']) == 2
        assert 'fhir_resources' in result

    def test_raw_data_preservation(self, processor, temp_csv_file):
        """Test that raw CSV data is preserved."""
        csv_content = """claim_id,patient_id,amount
TXN-001,P123456,125.50"""

        csv_file = temp_csv_file(csv_content, "test_raw.csv")
        result = processor.process_claims_csv(csv_file)

        # Test raw data preservation
        assert 'raw_data' in result
        raw_data = result['raw_data']
        assert 'csv_data' in raw_data
        assert 'columns' in raw_data
        assert len(raw_data['csv_data']) == 1

    def test_fhir_resources_mapping(self, processor, temp_csv_file):
        """Test FHIR resources mapping."""
        csv_content = """claim_id,patient_id,amount
TXN-001,P123456,125.50"""

        csv_file = temp_csv_file(csv_content, "test_fhir.csv")
        result = processor.process_claims_csv(csv_file)

        # Test FHIR mapping
        assert 'fhir_resources' in result
        assert 'entry' in result
        assert isinstance(result['fhir_resources'], dict)
        assert isinstance(result['entry'], list)

    def test_empty_csv_file(self, processor, temp_csv_file):
        """Test handling of empty CSV file."""
        csv_content = """claim_id,patient_id,amount"""

        csv_file = temp_csv_file(csv_content, "test_empty.csv")
        result = processor.process_claims_csv(csv_file)

        assert result['resourceType'] == 'Bundle'
        assert len(result['claims']) == 0
        assert len(result['services']) == 0

    def test_missing_file_error(self, processor):
        """Test error handling for missing CSV file."""
        with pytest.raises(FileNotFoundError):
            processor.process_claims_csv("nonexistent_file.csv")

    def test_amount_calculation(self, processor, temp_csv_file):
        """Test total amount calculation."""
        csv_content = """claim_id,patient_id,amount
TXN-001,P123456,125.50
TXN-002,P789012,250.00"""

        csv_file = temp_csv_file(csv_content, "test_amount.csv")
        result = processor.process_claims_csv(csv_file)

        # Test amount calculation
        assert 'total_amount' in result
        assert result['total_amount'] == 375.50

    def test_currency_detection(self, processor, temp_csv_file):
        """Test currency detection."""
        csv_content = """claim_id,patient_id,amount,currency
TXN-001,P123456,125.50,AED"""

        csv_file = temp_csv_file(csv_content, "test_currency.csv")
        result = processor.process_claims_csv(csv_file)

        # Test currency detection
        assert 'currency' in result
        assert result['currency'] == 'AED'

    def test_timestamp_format(self, processor, temp_csv_file):
        """Test timestamp format."""
        csv_content = """claim_id,patient_id,amount
TXN-001,P123456,125.50"""

        csv_file = temp_csv_file(csv_content, "test_timestamp.csv")
        result = processor.process_claims_csv(csv_file)

        # Check timestamp format (ISO 8601)
        timestamp = result['processing_timestamp']
        assert 'T' in timestamp
        assert timestamp.endswith('Z') or '+' in timestamp

    def test_bundle_id_uniqueness(self, processor, temp_csv_file):
        """Test Bundle ID uniqueness."""
        csv_content = """claim_id,patient_id,amount
TXN-001,P123456,125.50"""

        csv_file = temp_csv_file(csv_content, "test_unique.csv")
        result1 = processor.process_claims_csv(csv_file)
        result2 = processor.process_claims_csv(csv_file)

        # Bundle IDs should be unique
        assert result1['id'] != result2['id']

    def test_data_types_consistency(self, processor, temp_csv_file):
        """Test data type consistency."""
        csv_content = """claim_id,patient_id,amount
TXN-001,P123456,125.50"""

        csv_file = temp_csv_file(csv_content, "test_types.csv")
        result = processor.process_claims_csv(csv_file)

        # Check data types
        assert isinstance(result['claims'], list)
        assert isinstance(result['services'], list)
        assert isinstance(result['raw_data'], dict)
        assert isinstance(result['fhir_resources'], dict)

    def test_authorization_id_extraction(self, processor, temp_csv_file):
        """Test authorization ID extraction."""
        csv_content = """claim_id,patient_id,amount
TXN-001,P123456,125.50"""

        csv_file = temp_csv_file(csv_content, "test_auth.csv")
        result = processor.process_claims_csv(csv_file)

        # Test authorization ID
        assert 'authorization_id' in result
        assert result['authorization_id'] == 'TXN-001'

    def test_multiple_records_processing(self, processor, temp_csv_file):
        """Test processing multiple records."""
        csv_content = """claim_id,patient_id,amount,status
TXN-001,P123456,125.50,pending
TXN-002,P789012,250.00,approved
TXN-003,P456789,175.75,rejected"""

        csv_file = temp_csv_file(csv_content, "test_multiple.csv")
        result = processor.process_claims_csv(csv_file)

        # Test multiple records
        assert len(result['claims']) == 3
        assert len(result['services']) == 3
        assert result['total_amount'] == 551.25

    def test_source_file_tracking(self, processor, temp_csv_file):
        """Test source file tracking."""
        csv_content = """claim_id,patient_id,amount
TXN-001,P123456,125.50"""

        csv_file = temp_csv_file(csv_content, "test_source.csv")
        result = processor.process_claims_csv(csv_file)

        # Test source file tracking
        assert 'source_file' in result
        assert result['source_file'] == csv_file

    def test_csv_shape_and_columns(self, processor, temp_csv_file):
        """Test CSV shape and column extraction."""
        csv_content = """claim_id,patient_id,amount,status
TXN-001,P123456,125.50,pending
TXN-002,P789012,250.00,approved"""

        csv_file = temp_csv_file(csv_content, "test_shape.csv")
        result = processor.process_claims_csv(csv_file)

        # Test shape and columns
        raw_data = result['raw_data']
        assert raw_data['shape'] == [2, 4]  # 2 rows, 4 columns
        assert 'claim_id' in raw_data['columns']
        assert len(raw_data['columns']) == 4

    def test_clinical_csv_processing(self, processor, temp_csv_file):
        """Test clinical CSV processing method."""
        csv_content = """patient_id,observation_date,test_name,value,unit
P123456,2025-07-31,HbA1c,8.5,%
P789012,2025-07-30,Glucose,150,mg/dL"""

        csv_file = temp_csv_file(csv_content, "test_clinical.csv")
        result = processor.process_clinical_csv(csv_file)

        # Test clinical processing
        assert result['resourceType'] == 'Bundle'
        assert 'clinical_data_type' in result
        assert 'observations' in result

    def test_large_dataset_basic(self, processor):
        """Test processing of large sample file if it exists."""
        large_file_path = "samples/large_claims.csv"
        if os.path.exists(large_file_path):
            result = processor.process_claims_csv(large_file_path)

            assert result['resourceType'] == 'Bundle'
            assert len(result['claims']) >= 10
            assert result['total_amount'] > 0

    def test_sample_files_processing(self, processor):
        """Test processing of actual sample files."""
        sample_files = [
            "samples/sample_claims.csv",
            "samples/healthcare_claims_variations.csv",
        ]

        for sample_file in sample_files:
            if os.path.exists(sample_file):
                result = processor.process_claims_csv(sample_file)

                # Verify successful processing
                assert result['resourceType'] == 'Bundle'
                assert len(result['claims']) > 0
                assert 'raw_data' in result

    def test_whitespace_handling(self, processor, temp_csv_file):
        """Test handling of whitespace in CSV fields."""
        csv_content = """claim_id,patient_id,amount
  TXN-001  ,  P123456  ,  125.50
TXN-002,P789012,250.00"""

        csv_file = temp_csv_file(csv_content, "test_whitespace.csv")
        result = processor.process_claims_csv(csv_file)

        # Should handle whitespace gracefully
        assert result['resourceType'] == 'Bundle'
        assert len(result['claims']) == 2

    def test_special_characters(self, processor, temp_csv_file):
        """Test handling of special characters."""
        csv_content = """claim_id,patient_id,description
TXN-001,P123456,"Description with, comma"
TXN-002,P789012,Normal description"""

        csv_file = temp_csv_file(csv_content, "test_special.csv")
        result = processor.process_claims_csv(csv_file)

        # Should handle special characters
        assert result['resourceType'] == 'Bundle'
        assert len(result['claims']) == 2

    def test_numerical_field_types(self, processor, temp_csv_file):
        """Test handling of different numerical formats."""
        csv_content = """claim_id,patient_id,amount
TXN-001,P123456,125.50
TXN-002,P789012,250
TXN-003,P456789,175.75"""

        csv_file = temp_csv_file(csv_content, "test_numeric.csv")
        result = processor.process_claims_csv(csv_file)

        # Should handle different numeric formats
        assert result['resourceType'] == 'Bundle'
        assert len(result['claims']) == 3
        assert result['total_amount'] == 551.25

    def test_comprehensive_workflow(self, processor, temp_csv_file):
        """Test comprehensive workflow with all expected fields."""
        csv_content = """claim_id,patient_id,provider_id,service_date,diagnosis_code,procedure_code,amount,currency,status,description
TXN-001,P123456,PROV001,2025-07-31,E11.9,83036,125.50,AED,pending,HbA1c test
TXN-002,P789012,PROV002,2025-07-30,I10,99213,250.00,AED,approved,Office visit"""

        csv_file = temp_csv_file(csv_content, "test_comprehensive.csv")
        result = processor.process_claims_csv(csv_file)

        # Test comprehensive processing
        assert result['resourceType'] == 'Bundle'
        assert len(result['claims']) == 2
        assert len(result['services']) == 2
        assert result['total_amount'] == 375.50
        assert result['currency'] == 'AED'
        assert len(result['fhir_resources']) > 0
