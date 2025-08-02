"""
Integration tests for CSV processing end-to-end workflow.

This module tests the complete CSV processing pipeline from file input
to Bundle output, including performance characteristics and cross-format
consistency with XMLProcessor.
"""

import pytest
import os
import json
from pipelines.csv_processor import CSVProcessor
from pipelines.xml_processor import XMLProcessor


@pytest.mark.integration
class TestCSVEndToEnd:
    """Integration tests for complete CSV processing workflow."""

    @pytest.fixture
    def csv_processor(self):
        """Create CSVProcessor instance."""
        return CSVProcessor()

    @pytest.fixture
    def xml_processor(self):
        """Create XMLProcessor instance for comparison tests."""
        return XMLProcessor()

    def test_complete_csv_processing_workflow(
        self, csv_processor, create_test_csv_files
    ):
        """Test complete CSV processing workflow from file to Bundle."""
        csv_files = create_test_csv_files

        # Process basic claims CSV
        result = csv_processor.process_claims_csv(csv_files["basic"])

        # Verify complete workflow
        assert result['resourceType'] == 'Bundle'
        assert result['type'] == 'collection'
        assert 'id' in result
        assert 'timestamp' in result
        assert 'meta' in result

        # Verify data flow
        assert result['total_records'] > 0
        assert result['valid_records'] > 0
        assert len(result['claims']) == result['valid_records']
        assert len(result['raw_data']['csv_data']) == result['total_records']

        # Verify metadata completeness
        assert 'source_file' in result
        assert 'processing_timestamp' in result
        assert 'encoding_used' in result
        # File stats and headers available in raw_data
        assert 'raw_data' in result
        assert 'columns' in result['raw_data']
        assert 'shape' in result['raw_data']

    def test_sample_files_processing(self, csv_processor):
        """Test processing of actual sample CSV files."""
        sample_files = [
            "samples/sample_claims.csv",
            "samples/healthcare_claims_variations.csv",
            "samples/large_claims.csv",
        ]

        for sample_file in sample_files:
            if os.path.exists(sample_file):
                result = csv_processor.process_claims_csv(sample_file)

                # Verify successful processing
                assert result['resourceType'] == 'Bundle'
                assert result['total_records'] > 0
                assert result['data_quality_score'] >= 0.0
                assert result['data_quality_score'] <= 1.0

                # Verify Bundle structure consistency
                assert 'claims' in result
                assert 'raw_data' in result
                assert isinstance(result['claims'], list)
                assert isinstance(result['raw_data'], dict)

    def test_cross_format_bundle_consistency(
        self, csv_processor, xml_processor, create_test_csv_files
    ):
        """Test that CSV and XML processors produce consistent Bundle structures."""
        csv_files = create_test_csv_files

        # Process CSV
        csv_result = csv_processor.process_claims_csv(csv_files["basic"])

        # Check if XML sample exists for comparison
        xml_sample_path = "samples/eclaim_link_request.xml"
        if os.path.exists(xml_sample_path):
            xml_result = xml_processor.process_eclaim_link(xml_sample_path)

            # Compare Bundle structure consistency
            assert csv_result['resourceType'] == xml_result['resourceType']
            assert csv_result['type'] == xml_result['type']
            assert 'id' in csv_result and 'id' in xml_result
            assert 'meta' in csv_result and 'meta' in xml_result
            assert 'timestamp' in csv_result and 'timestamp' in xml_result

            # Verify meta structure similarity
            assert csv_result['meta']['profile'] == xml_result['meta']['profile']
            assert csv_result['meta']['versionId'] == xml_result['meta']['versionId']

            # Verify both preserve raw data
            assert 'raw_data' in csv_result and 'raw_data' in xml_result

    @pytest.mark.performance
    def test_large_dataset_performance(
        self, csv_processor, create_test_csv_files, performance_monitor
    ):
        """Test performance with large CSV datasets."""
        csv_files = create_test_csv_files

        # Monitor performance
        performance_monitor.start()

        # Process large dataset
        result = csv_processor.process_claims_csv(csv_files["large"])

        performance_monitor.stop()

        # Verify processing completed successfully
        assert result['resourceType'] == 'Bundle'
        assert result['total_records'] >= 20  # Expecting substantial dataset
        assert result['valid_records'] > 0

        # Performance assertions (adjust based on system capabilities)
        performance_monitor.assert_performance(max_time=10.0, max_memory_mb=200.0)

        # Verify data quality maintained with large dataset
        assert result['data_quality_score'] > 0.0

    def test_error_handling_integration(self, csv_processor):
        """Test error handling in complete workflow."""
        # Test missing file
        with pytest.raises(FileNotFoundError):
            csv_processor.process_claims_csv("nonexistent_file.csv")

        # Test malformed file if it exists
        malformed_path = "samples/malformed_claims.csv"
        if os.path.exists(malformed_path):
            result = csv_processor.process_claims_csv(malformed_path)

            # Should handle malformed data gracefully
            assert result['resourceType'] == 'Bundle'
            assert result['total_records'] > 0
            # May have fewer valid records due to malformed data
            assert result['valid_records'] >= 0

    def test_data_quality_scoring_integration(
        self, csv_processor, create_test_csv_files
    ):
        """Test data quality scoring across different file types."""
        csv_files = create_test_csv_files

        quality_tests = [
            ("quality_high_quality", 0.8, 1.0),  # High quality data
            ("quality_medium_quality", 0.4, 0.8),  # Medium quality data
            ("quality_low_quality", 0.0, 0.7),  # Low quality data (more lenient range)
        ]

        for file_key, min_score, max_score in quality_tests:
            if file_key in csv_files:
                result = csv_processor.process_claims_csv(csv_files[file_key])

                score = result['data_quality_score']
                assert (
                    min_score <= score <= max_score
                ), f"Quality score {score} not in expected range [{min_score}, {max_score}] for {file_key}"

    def test_encoding_handling_integration(self, csv_processor, create_test_csv_files):
        """Test encoding detection and handling integration."""
        csv_files = create_test_csv_files

        if "encoding" in csv_files:
            result = csv_processor.process_claims_csv(csv_files["encoding"])

            # Verify encoding was detected and handled
            assert result['encoding_used'] in ['utf-8', 'utf-8-sig', 'latin1', 'cp1256']
            assert result['total_records'] > 0

            # Verify special characters were preserved in raw data
            raw_data = result['raw_data']['csv_data']
            descriptions = [record.get('description', '') for record in raw_data]
            assert any('café' in desc for desc in descriptions)

    def test_memory_usage_with_large_files(
        self, csv_processor, csv_test_data_factory, tmp_path
    ):
        """Test memory usage patterns with progressively larger files."""
        import tracemalloc

        # Create files of different sizes
        file_sizes = [10, 50, 100]
        memory_usage = []

        for size in file_sizes:
            # Create temporary large file
            large_csv_content = csv_test_data_factory.create_large_dataset_csv(size)
            temp_file = tmp_path / f"memory_test_{size}.csv"
            temp_file.write_text(large_csv_content, encoding="utf-8")

            # Monitor memory usage
            tracemalloc.start()

            result = csv_processor.process_claims_csv(str(temp_file))

            current, peak = tracemalloc.get_traced_memory()
            memory_usage.append(peak)
            tracemalloc.stop()

            # Verify processing succeeded
            assert result['total_records'] == size
            assert result['resourceType'] == 'Bundle'

        # Memory usage should scale reasonably (not exponentially)
        # Allow for some variance but ensure it's not growing unreasonably
        if len(memory_usage) >= 2:
            growth_ratio = memory_usage[-1] / memory_usage[0]
            size_ratio = file_sizes[-1] / file_sizes[0]
            # Memory growth should not be more than 3x the size growth
            assert growth_ratio <= size_ratio * 3

    def test_concurrent_processing_safety(self, csv_processor, create_test_csv_files):
        """Test that concurrent processing doesn't cause issues."""
        import threading

        csv_files = create_test_csv_files
        results = []
        errors = []

        def process_file(file_path, result_list, error_list):
            try:
                result = csv_processor.process_claims_csv(file_path)
                result_list.append(result)
            except Exception as e:
                error_list.append(e)

        # Start multiple processing threads
        threads = []
        test_files = [csv_files["basic"], csv_files["variations"], csv_files["numeric"]]

        for file_path in test_files:
            thread = threading.Thread(
                target=process_file, args=(file_path, results, errors)
            )
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=30)  # 30 second timeout

        # Verify all processing completed successfully
        assert len(errors) == 0, f"Concurrent processing errors: {errors}"
        assert len(results) == len(test_files)

        # Verify all results are valid Bundles
        for result in results:
            assert result['resourceType'] == 'Bundle'
            assert result['total_records'] > 0

    @pytest.mark.slow
    def test_comprehensive_workflow_validation(
        self, csv_processor, create_test_csv_files
    ):
        """Test comprehensive workflow with all file types."""
        csv_files = create_test_csv_files

        processed_results = {}

        # Process all test files
        for file_type, file_path in csv_files.items():
            try:
                result = csv_processor.process_claims_csv(file_path)
                processed_results[file_type] = result
            except Exception as e:
                # Skip empty files as they may legitimately fail
                if file_type == "empty":
                    continue
                pytest.fail(f"Failed to process {file_type}: {str(e)}")

        # Verify all files were processed
        assert len(processed_results) > 0

        # Verify Bundle consistency across all files
        for file_type, result in processed_results.items():
            assert result['resourceType'] == 'Bundle', f"Invalid Bundle for {file_type}"
            assert 'id' in result, f"Missing ID for {file_type}"
            assert 'meta' in result, f"Missing meta for {file_type}"
            assert 'timestamp' in result, f"Missing timestamp for {file_type}"
            assert 'raw_data' in result, f"Missing raw_data for {file_type}"

        # Verify data quality scores are within valid range
        for file_type, result in processed_results.items():
            score = result.get('data_quality_score', -1)
            assert 0.0 <= score <= 1.0, f"Invalid quality score {score} for {file_type}"

        # Verify file statistics are reasonable
        for file_type, result in processed_results.items():
            raw_data = result.get('raw_data', {})
            shape = raw_data.get('shape', [-1, -1])
            assert shape[0] >= 0, f"Invalid row count for {file_type}"
            assert shape[1] >= 0, f"Invalid column count for {file_type}"
            assert (
                len(raw_data.get('columns', [])) >= 0
            ), f"Invalid columns for {file_type}"

    def test_output_serialization(self, csv_processor, create_test_csv_files):
        """Test that output can be properly serialized to JSON."""
        csv_files = create_test_csv_files

        result = csv_processor.process_claims_csv(csv_files["basic"])

        # Test JSON serialization
        try:
            json_output = json.dumps(result, indent=2, default=str)
            assert len(json_output) > 0

            # Test deserialization
            deserialized = json.loads(json_output)
            assert deserialized['resourceType'] == 'Bundle'
            assert deserialized['total_records'] == result['total_records']

        except (TypeError, ValueError) as e:
            pytest.fail(f"JSON serialization failed: {str(e)}")

    def test_api_integration_readiness(self, csv_processor, create_test_csv_files):
        """Test that output is ready for API integration."""
        csv_files = create_test_csv_files

        result = csv_processor.process_claims_csv(csv_files["basic"])

        # Verify API-ready structure
        required_api_fields = [
            'resourceType',
            'id',
            'type',
            'meta',
            'timestamp',
            'total_records',
            'valid_records',
            'data_quality_score',
            'claims',
            'raw_data',
            'source_file',
            'processing_timestamp',
        ]

        for field in required_api_fields:
            assert field in result, f"Missing required API field: {field}"

        # Verify meta structure for API compliance
        meta = result['meta']
        required_meta_fields = ['profile', 'source', 'lastUpdated', 'versionId']
        for field in required_meta_fields:
            assert field in meta, f"Missing required meta field: {field}"

        # Verify data types for API serialization
        assert isinstance(result['total_records'], int)
        assert isinstance(result['valid_records'], int)
        assert isinstance(result['data_quality_score'], float)
        assert isinstance(result['claims'], list)
        assert isinstance(result['raw_data'], dict)
