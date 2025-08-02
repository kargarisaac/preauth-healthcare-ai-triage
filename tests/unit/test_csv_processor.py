"""
Unit tests for CSVProcessor functionality.

This module tests the CSVProcessor CSV processing method,
focusing on CSV parsing, field mapping, data quality scoring, and output structure.
"""

import pytest
import os
import tempfile
from pipelines.csv_processor import CSVProcessor


class TestCSVProcessor:
    """Unit tests for CSVProcessor CSV processing."""

    @pytest.fixture
    def processor(self):
        """Create CSVProcessor instance."""
        return CSVProcessor()

    @pytest.fixture
    def temp_csv_file(self):
        """
        Fixture that provides a temporary CSV file that gets cleaned up.

        Returns:
            Generator that yields a function to create temp CSV files
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
        csv_content = """claim_id,patient_id,provider_id,amount,currency,status
TXN-001,P123456,PROV001,125.50,AED,pending
TXN-002,P789012,PROV002,250.00,AED,approved"""

        csv_file = temp_csv_file(csv_content, "test_basic.csv")
        result = processor.process_claims_csv(csv_file)

        # Test canonical JSON structure
        assert result['resourceType'] == 'Bundle'
        assert result['meta']['source'] == 'Claims-CSV'
        assert len(result['claims']) == 2
        assert len(result['services']) == 2
        assert 'raw_data' in result

    def test_bundle_metadata(self, processor, temp_csv_file):
        """Test Bundle metadata generation."""
        csv_content = """claim_id,patient_id,amount
TXN-123,P456789,100.00"""

        csv_file = temp_csv_file(csv_content, "test_metadata.csv")
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
        assert meta['profile'] == [
            'https://nazmito.com/fhir/StructureDefinition/healthcare-bundle'
        ]

    def test_claims_extraction(self, processor, temp_csv_file):
        """Test claim extraction from CSV."""
        csv_content = """claim_id,patient_id,procedure_code,amount,diagnosis_code,status
TXN-001,P123456,83036,125.50,E11.9,pending
TXN-002,P789012,99213,250.00,I10,approved"""

        csv_file = temp_csv_file(csv_content, "test_claims.csv")
        result = processor.process_claims_csv(csv_file)

        # Test claims extraction
        claims = result['claims']
        assert len(claims) == 2

        claim1 = claims[0]
        assert claim1['sequence'] == 1
        assert claim1['claim_id'] == 'TXN-001'
        assert claim1['patient_id'] == 'P123456'
        assert claim1['procedure_code'] == '83036'
        assert claim1['amount'] == 125.50
        assert claim1['diagnosis_code'] == 'E11.9'
        assert claim1['status'] == 'pending'

        claim2 = claims[1]
        assert claim2['sequence'] == 2
        assert claim2['claim_id'] == 'TXN-002'
        assert claim2['patient_id'] == 'P789012'
        assert claim2['procedure_code'] == '99213'
        assert claim2['amount'] == 250.00

    def test_raw_data_preservation(self, processor, temp_csv_file):
        """Test that raw CSV data is preserved in output."""
        csv_content = """claim_id,patient_id,amount,notes
TXN-001,P123456,125.50,Test note"""

        csv_file = temp_csv_file(csv_content, "test_raw.csv")
        result = processor.process_claims_csv(csv_file)

        # Test raw data preservation
        assert 'raw_data' in result
        assert isinstance(result['raw_data'], dict)
        assert 'csv_data' in result['raw_data']
        assert len(result['raw_data']['csv_data']) == 1
        assert result['raw_data']['csv_data'][0]['claim_id'] == 'TXN-001'
        assert result['raw_data']['csv_data'][0]['notes'] == 'Test note'

    def test_column_header_variations(self, processor, temp_csv_file):
        """Test handling of different column header variations."""
        csv_content = """ID,Member_ID,CPT_Code,Billed_Amount
REF001,M123456,83036,125.50
REF002,M789012,99213,250.00"""

        csv_file = temp_csv_file(csv_content, "test_variations.csv")
        result = processor.process_claims_csv(csv_file)

        claims = result['claims']
        assert len(claims) == 2

        claim1 = claims[0]
        assert claim1['claim_id'] == 'REF001'  # Mapped from 'ID'
        assert claim1['patient_id'] == 'M123456'  # Mapped from 'Member_ID'
        assert claim1['procedure_code'] == '83036'  # Mapped from 'CPT_Code'
        assert claim1['amount'] == 125.50  # Mapped from 'Billed_Amount'

    def test_case_insensitive_headers(self, processor, temp_csv_file):
        """Test case-insensitive header matching."""
        csv_content = """CLAIM_ID,patient_id,AMOUNT
TXN-001,P123456,125.50"""

        csv_file = temp_csv_file(csv_content, "test_case.csv")
        result = processor.process_claims_csv(csv_file)

        claims = result['claims']
        assert len(claims) == 1
        assert claims[0]['claim_id'] == 'TXN-001'
        assert claims[0]['patient_id'] == 'P123456'
        assert claims[0]['amount'] == 125.50

    def test_numeric_field_parsing(self, processor, temp_csv_file):
        """Test parsing of various numeric field formats."""
        csv_content = """claim_id,patient_id,amount
TXN-001,P123456,"1,250.50"
TXN-002,P789012,$750.25
TXN-003,P456789,500.00 AED
TXN-004,P321654,300"""

        csv_file = temp_csv_file(csv_content, "test_numeric.csv")
        result = processor.process_claims_csv(csv_file)

        claims = result['claims']
        assert len(claims) == 4
        assert claims[0]['amount'] == 1250.50  # Comma removed
        assert claims[1]['amount'] == 750.25  # Dollar sign removed
        assert claims[2]['amount'] == 500.00  # AED removed
        assert claims[3]['amount'] == 300.0  # Integer converted to float

    def test_missing_essential_fields(self, processor, temp_csv_file):
        """Test handling of records with missing essential fields."""
        csv_content = """claim_id,patient_id,procedure_code,amount
TXN-001,P123456,83036,125.50
TXN-002,,99213,250.00
,P789012,80061,175.00
TXN-004,P456789,,100.00"""

        csv_file = temp_csv_file(csv_content, "test_missing.csv")
        result = processor.process_claims_csv(csv_file)

        # Should include records with claim_id OR (patient_id AND procedure_code)
        claims = result['claims']
        assert len(claims) == 4  # All records have claim_id or patient+procedure
        assert result['total_records'] == 4
        assert result['valid_records'] == 4

    def test_empty_csv_file(self, processor, temp_csv_file):
        """Test handling of empty CSV file."""
        csv_content = """claim_id,patient_id,amount"""

        csv_file = temp_csv_file(csv_content, "test_empty.csv")
        result = processor.process_claims_csv(csv_file)

        assert result['resourceType'] == 'Bundle'
        assert result['total_records'] == 0
        assert result['valid_records'] == 0
        assert len(result['claims']) == 0
        assert result['data_quality_score'] == 0.0

    def test_malformed_csv_handling(self, processor, temp_csv_file):
        """Test handling of malformed CSV data."""
        csv_content = """claim_id,patient_id,amount,notes
TXN-001,P123456,125.50,Valid record
TXN-002,,INVALID,Missing patient
,P789012,175.00,Missing claim ID
TXN-004,P456789,300.00,Valid record"""

        csv_file = temp_csv_file(csv_content, "test_malformed.csv")
        result = processor.process_claims_csv(csv_file)

        # Should handle malformed data gracefully
        assert result['resourceType'] == 'Bundle'
        assert result['total_records'] == 4
        claims = result['claims']
        assert len(claims) >= 2  # At least the valid records

    def test_file_stats_calculation(self, processor, temp_csv_file):
        """Test file statistics calculation."""
        csv_content = """claim_id,patient_id,amount
TXN-001,P123456,125.50
TXN-002,P789012,250.00"""

        csv_file = temp_csv_file(csv_content, "test_stats.csv")
        result = processor.process_claims_csv(csv_file)

        # Check file statistics from raw_data
        raw_data = result['raw_data']
        assert raw_data['shape'][0] == 2  # rows
        assert raw_data['shape'][1] == 3  # columns
        assert len(raw_data['csv_data']) == 2

    def test_column_headers_extraction(self, processor, temp_csv_file):
        """Test extraction of column headers."""
        csv_content = """claim_id,patient_id,provider_id,amount,status
TXN-001,P123456,PROV001,125.50,pending"""

        csv_file = temp_csv_file(csv_content, "test_headers.csv")
        result = processor.process_claims_csv(csv_file)

        headers = result['raw_data']['columns']
        expected_headers = ['claim_id', 'patient_id', 'provider_id', 'amount', 'status']
        assert headers == expected_headers

    def test_data_quality_scoring(self, processor, temp_csv_file):
        """Test data quality score calculation."""
        # High quality data
        high_quality_csv = """claim_id,patient_id,procedure_code,amount,service_date
TXN-001,P123456,83036,125.50,2025-07-31
TXN-002,P789012,99213,250.00,2025-07-30"""

        csv_file = temp_csv_file(high_quality_csv, "test_high_quality.csv")
        result = processor.process_claims_csv(csv_file)

        assert result['data_quality_score'] > 0.8  # Should be high quality

        # Low quality data
        low_quality_csv = """claim_id,patient_id,amount
TXN-001,,
,P789012,INVALID"""

        csv_file2 = temp_csv_file(low_quality_csv, "test_low_quality.csv")
        result2 = processor.process_claims_csv(csv_file2)

        assert result2['data_quality_score'] < 0.5  # Should be low quality

    def test_duplicate_detection(self, processor, temp_csv_file):
        """Test duplicate record detection in quality scoring."""
        csv_content = """claim_id,patient_id,amount
TXN-001,P123456,125.50
TXN-001,P123456,125.50
TXN-002,P789012,250.00"""

        csv_file = temp_csv_file(csv_content, "test_duplicates.csv")
        result = processor.process_claims_csv(csv_file)

        # Quality score should be affected by duplicates
        assert result['data_quality_score'] < 1.0
        assert result['total_records'] == 3

    def test_currency_field_handling(self, processor, temp_csv_file):
        """Test currency field extraction and defaults."""
        csv_content = """claim_id,patient_id,amount,currency
TXN-001,P123456,125.50,USD
TXN-002,P789012,250.00,
TXN-003,P456789,175.00,EUR"""

        csv_file = temp_csv_file(csv_content, "test_currency.csv")
        result = processor.process_claims_csv(csv_file)

        claims = result['claims']
        assert claims[0]['currency'] == 'USD'
        assert claims[1]['currency'] == 'AED'  # Default value
        assert claims[2]['currency'] == 'EUR'

    def test_field_extraction_methods(self, processor):
        """Test internal field extraction methods."""
        record = {
            'claim_id': 'TXN-001',
            'Patient_ID': 'P123456',  # Different case
            'amount': '125.50',
            'BILLED_AMOUNT': '250.00',  # Alternative field name
            'invalid_amount': 'NOT_A_NUMBER',
        }

        # Test string field extraction
        claim_id = processor._extract_field(record, ['claim_id'])
        assert claim_id == 'TXN-001'

        # Test case-insensitive extraction
        patient_id = processor._extract_field(record, ['patient_id'])
        assert patient_id == 'P123456'

        # Test numeric field extraction
        amount = processor._extract_numeric_field(record, ['amount'])
        assert amount == 125.50

        # Test alternative field names
        billed_amount = processor._extract_numeric_field(record, ['billed_amount'])
        assert billed_amount == 250.00

        # Test invalid numeric field
        invalid = processor._extract_numeric_field(record, ['invalid_amount'])
        assert invalid is None

    def test_encoding_detection(self, processor, temp_csv_file):
        """Test automatic encoding detection."""
        # Create CSV with UTF-8 content
        csv_content = """claim_id,patient_id,description
TXN-001,P123456,Regular description
TXN-002,P789012,Description with special chars: café"""

        csv_file = temp_csv_file(csv_content, "test_encoding.csv")
        result = processor.process_claims_csv(csv_file)

        assert result['encoding_used'] in ['utf-8', 'utf-8-sig']
        assert result['total_records'] == 2

    def test_missing_file_error(self, processor):
        """Test error handling for missing CSV file."""
        with pytest.raises(FileNotFoundError):
            processor.process_claims_csv("nonexistent_file.csv")

    def test_large_dataset_handling(self, processor):
        """Test processing of larger datasets."""
        # Test with actual large sample file if it exists
        large_file_path = "samples/large_claims.csv"
        if os.path.exists(large_file_path):
            result = processor.process_claims_csv(large_file_path)

            assert result['resourceType'] == 'Bundle'
            assert result['total_records'] >= 10  # Expecting at least 10 records
            assert result['data_quality_score'] > 0.0

    def test_whitespace_handling(self, processor, temp_csv_file):
        """Test handling of whitespace in fields."""
        csv_content = """claim_id,patient_id,amount
  TXN-001  ,  P123456  ,  125.50
TXN-002,P789012,250.00"""

        csv_file = temp_csv_file(csv_content, "test_whitespace.csv")
        result = processor.process_claims_csv(csv_file)

        claims = result['claims']
        assert claims[0]['claim_id'] == 'TXN-001'  # Whitespace stripped
        assert claims[0]['patient_id'] == 'P123456'  # Whitespace stripped
        assert claims[0]['amount'] == 125.50

    def test_special_characters_in_data(self, processor, temp_csv_file):
        """Test handling of special characters in data."""
        csv_content = """claim_id,patient_id,description
TXN-001,P123456,"Description with, comma"
TXN-002,P789012,Description with "quotes"
TXN-003,P456789,Description with newline"""

        csv_file = temp_csv_file(csv_content, "test_special_chars.csv")
        result = processor.process_claims_csv(csv_file)

        assert result['total_records'] == 3
        claims = result['claims']
        assert len(claims) >= 2  # Should handle most records successfully

    def test_processing_timestamp_format(self, processor, temp_csv_file):
        """Test processing timestamp format."""
        csv_content = """claim_id,patient_id,amount
TXN-001,P123456,125.50"""

        csv_file = temp_csv_file(csv_content, "test_timestamp.csv")
        result = processor.process_claims_csv(csv_file)

        # Check timestamp format (ISO 8601)
        timestamp = result['processing_timestamp']
        assert 'T' in timestamp
        assert timestamp.endswith('Z') or '+' in timestamp

    def test_bundle_id_format(self, processor, temp_csv_file):
        """Test Bundle ID format and uniqueness."""
        csv_content = """claim_id,patient_id,amount
TXN-001,P123456,125.50"""

        csv_file = temp_csv_file(csv_content, "test_bundle_id.csv")
        result1 = processor.process_claims_csv(csv_file)
        result2 = processor.process_claims_csv(csv_file)

        # Bundle IDs should follow format and be unique
        assert result1['id'].startswith('Claims-CSV-')
        assert result2['id'].startswith('Claims-CSV-')
        assert result1['id'] != result2['id']  # Should be unique

    def test_alternative_field_mappings(self, processor, temp_csv_file):
        """Test mapping of alternative field names."""
        csv_content = """ref_no,insurance_id,service_code,total_cost,claim_status
REF-001,INS123456,83036,125.50,pending
REF-002,INS789012,99213,250.00,approved"""

        csv_file = temp_csv_file(csv_content, "test_alternatives.csv")
        result = processor.process_claims_csv(csv_file)

        claims = result['claims']
        assert len(claims) == 2

        claim1 = claims[0]
        assert claim1['claim_id'] == 'REF-001'  # Mapped from ref_no
        assert claim1['patient_id'] == 'INS123456'  # Mapped from insurance_id
        assert claim1['procedure_code'] == '83036'  # Mapped from service_code
        assert claim1['amount'] == 125.50  # Mapped from total_cost
        assert claim1['status'] == 'pending'  # Mapped from claim_status

    def test_data_type_consistency(self, processor, temp_csv_file):
        """Test data type consistency in output."""
        csv_content = """claim_id,patient_id,amount,sequence_num
TXN-001,P123456,125.50,1
TXN-002,P789012,250.00,2"""

        csv_file = temp_csv_file(csv_content, "test_types.csv")
        result = processor.process_claims_csv(csv_file)

        # Check data types
        assert isinstance(result['total_records'], int)
        assert isinstance(result['valid_records'], int)
        assert isinstance(result['data_quality_score'], float)
        assert isinstance(result['claims'], list)
        assert isinstance(result['raw_data'], dict)

        # Check claim data types
        claim = result['claims'][0]
        assert isinstance(claim['sequence'], int)
        assert isinstance(claim['amount'], float)

    def test_comprehensive_field_mapping(self, processor, temp_csv_file):
        """Test comprehensive field mapping coverage."""
        csv_content = """claim_id,patient_id,provider_id,service_date,diagnosis_code,procedure_code,amount,currency,status,description
TXN-001,P123456,PROV001,2025-07-31,E11.9,83036,125.50,AED,pending,HbA1c test"""

        csv_file = temp_csv_file(csv_content, "test_comprehensive.csv")
        result = processor.process_claims_csv(csv_file)

        claim = result['claims'][0]

        # Verify all standard fields are mapped
        expected_fields = [
            'sequence',
            'claim_id',
            'patient_id',
            'provider_id',
            'service_date',
            'diagnosis_code',
            'procedure_code',
            'amount',
            'currency',
            'status',
            'description',
            'raw_record',
        ]

        for field in expected_fields:
            assert field in claim

        # Verify specific values
        assert claim['claim_id'] == 'TXN-001'
        assert claim['patient_id'] == 'P123456'
        assert claim['provider_id'] == 'PROV001'
        assert claim['service_date'] == '2025-07-31'
        assert claim['diagnosis_code'] == 'E11.9'
        assert claim['procedure_code'] == '83036'
        assert claim['amount'] == 125.50
        assert claim['currency'] == 'AED'
        assert claim['status'] == 'pending'
        assert claim['description'] == 'HbA1c test'
