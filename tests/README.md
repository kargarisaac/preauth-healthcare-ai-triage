# Test Suite Organization

This document outlines the cleaned and organized test structure for the Nazmito project.

## Test Structure

### Integration Tests (`tests/integration/`)
- **`test_data_pipeline.py`**: Comprehensive tests for the XML-to-JSON data pipeline

### Unit Tests (`tests/unit/`)  
- **`test_csv_processor.py`**: Unit tests for CSV processing functionality
- **`test_data_quality.py`**: Tests for data quality validation
- **`test_eclaim_link_ingestor.py`**: Tests for eClaimLink XML processing
- **`test_shafafiya_ingestor.py`**: Tests for Shafafiya XML processing
- **`test_xml_factory.py`**: Tests for XML processor factory functionality

### Configuration
- **`conftest.py`**: Shared fixtures and test utilities
- **`README.md`**: This documentation file

## Removed Obsolete Tests

The following redundant and obsolete test files have been removed:

- ❌ `tests/test_integration.py` - Obsolete integration test script
- ❌ `tests/integration/test_end_to_end_processing.py` - Redundant with new integration tests
- ❌ `tests/integration/test_csv_end_to_end.py` - Redundant with processor tests
- ❌ `tests/test_canonical_schema.py` - Obsolete schema validation tests
- ❌ `tests/test_csv_api.py` - Obsolete API test script
- ❌ `tests/unit/test_csv_processor_simplified.py` - Redundant simplified version

## Test Coverage

### Data Pipeline Integration (Day 8 Deliverable)
✅ **XML to JSON conversion pipeline**
- Batch processing of synthetic dataset
- Directory structure setup and validation
- Error handling and recovery
- Progress tracking and statistics


### Core Processing Functionality
✅ **XML Processing**
- eClaimLink format support
- Shafafiya format support
- FHIR Bundle generation
- Data quality validation

✅ **CSV Processing**
- Healthcare CSV ingestion
- Column detection and mapping
- Bundle structure generation
- Encoding handling

## Running Tests

### Run All Tests
```bash
python -m pytest tests/ -v
```

### Run Integration Tests Only
```bash
python -m pytest tests/integration/ -v
```

### Run Unit Tests Only
```bash
python -m pytest tests/unit/ -v
```

### Run Specific Test Categories
```bash
# Data pipeline tests
python -m pytest tests/integration/test_data_pipeline.py -v

# XML processing tests
python -m pytest tests/unit/test_*ingestor.py -v
```

### Performance and Slow Tests
```bash
# Skip slow tests for quick validation
python -m pytest tests/ -m "not slow" -v

# Run performance tests only
python -m pytest tests/ -m "performance" -v
```

## Test Markers

The test suite uses pytest markers for organization:

- `@pytest.mark.unit` - Unit tests (automatic)
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.performance` - Performance tests
- `@pytest.mark.slow` - Slow tests (may be skipped)
- `@pytest.mark.edge_case` - Edge case testing
- `@pytest.mark.fhir` - FHIR-related tests
- `@pytest.mark.clinical` - Clinical data processing

## Fixtures and Utilities

The `conftest.py` provides comprehensive fixtures:

### File Creation Fixtures
- `temp_xml_file()` - Create temporary XML files
- `temp_csv_file()` - Create temporary CSV files  
- `create_test_xml_files()` - Create various test XML scenarios
- `create_test_csv_files()` - Create various test CSV scenarios

### Data Factory Fixtures
- `test_data_factory()` - Generate XML test data
- `csv_test_data_factory()` - Generate CSV test data
- `fhir_test_data_factory()` - Generate FHIR Bundle test data

### Validation Helpers
- `clinical_validation_helper()` - FHIR Bundle validation
- `performance_monitor()` - Performance testing utilities
- `mock_file_system()` - File system mocking

## Quality Assurance

The cleaned test suite provides:

✅ **Comprehensive Coverage**: All major components tested
✅ **Integration Validation**: End-to-end pipeline testing  
✅ **Performance Testing**: Memory and timing validation
✅ **Error Handling**: Edge cases and failure scenarios
✅ **Clinical Validation**: FHIR compliance and medical data integrity
✅ **Clean Organization**: Logical grouping and clear naming

This test structure supports the Day 8 integration architecture deliverable and provides a solid foundation for continued development and validation.