# Integration Tests for Pipeline Milestones

## Overview

Comprehensive integration tests validating the Aug 20-22 pipeline milestones implementation, covering all aspects from pipeline processing to UI workflows.

## Test Structure

### 1. Pipeline Integration Tests (`test_pipeline_integration.py`)
- **Complete Pipeline Flow**: XML input → processing → JSON output
- **All 6 Phases**: intake, clinical_summary, evidence, checklist, decision, dossier
- **Demo Patients**: Patient_007, Patient_005, Patient_011
- **Performance**: Cost and timing validation
- **Reproducibility**: Deterministic decision validation

### 2. API Endpoint Tests (`test_api_endpoints.py`)
- **Unified Processing**: `POST /api/process/unified`
- **Dossier Retrieval**: `GET /api/dossier/{analysis_id}`
- **Health Monitoring**: `GET /api/health`
- **Dashboard Analytics**: `GET /api/dashboard/summary`
- **Error Handling**: Validation and user feedback

### 3. CLI Interface Tests (`test_cli_interface.py`)
- **Direct Execution**: `python -m preauth_system.pipeline_module`
- **Output Files**: Timestamped JSON creation in `output/`
- **Console Output**: Summary accuracy and formatting
- **Performance**: Memory and timing validation

### 4. Dossier Quality Tests (`test_dossier_quality.py`)
- **Professional Quality**: Medical language standards
- **Citation Accuracy**: Evidence integration and formatting
- **Cost Efficiency**: <$0.02 per dossier target
- **Multilingual Support**: Bilingual framework validation

### 5. UI Workflow Tests (`test_ui_workflow.py`)
- **End-to-End Flow**: Upload → process → results → dossier
- **Error States**: User feedback and error handling
- **Multi-Format**: eClaimLink and Shafafiya support
- **Performance**: Concurrent user load testing

## Running Tests

### All Integration Tests
```bash
pytest tests/integration/ -v
```

### Specific Test Categories
```bash
# Pipeline core functionality
pytest tests/integration/test_pipeline_integration.py -v

# API endpoints
pytest tests/integration/test_api_endpoints.py -v

# CLI interface
pytest tests/integration/test_cli_interface.py -v

# Dossier quality
pytest tests/integration/test_dossier_quality.py -v

# UI workflows
pytest tests/integration/test_ui_workflow.py -v
```

### Performance Tests Only
```bash
pytest tests/integration/ -m performance -v
```

### Skip Slow Tests
```bash
pytest tests/integration/ -m "not slow" -v
```

## Test Configuration

### Performance Targets (Adjusted for Integration)
- **Pipeline Execution**: <2 minutes (including LLM calls)
- **API Response Time**: <3 minutes for complex operations
- **CLI Execution**: <2 minutes with output generation
- **Dossier Generation**: <30 seconds
- **Cost per Request**: <$1.00 (including all LLM usage)

### Demo Data Requirements
- Patient_007: Diabetes case (high compliance)
- Patient_005: Complex case (medium compliance)
- Patient_011: Edge case (low compliance)

### Environment Setup
```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-timeout

# Set test environment variables
export PREAUTH_TEST_MODE=true
export PREAUTH_LOG_LEVEL=INFO
```

## Test Markers

### Available Markers
- `@pytest.mark.integration`: Integration test
- `@pytest.mark.performance`: Performance validation
- `@pytest.mark.slow`: Long-running tests
- `@pytest.mark.timeout(N)`: Test timeout in seconds

### Example Usage
```python
@pytest.mark.integration
@pytest.mark.performance
def test_pipeline_performance():
    # Performance integration test
    pass
```

## Validation Criteria

### ✅ Pipeline Milestones Validation
- **Aug 20**: DossierWriter LLM implementation
- **Aug 21**: Pipeline CLI integration with JSON output
- **Aug 22a**: Backend API endpoints integration
- **Aug 22b**: Frontend UI workflow integration

### ✅ Quality Standards
- **Medical Professional**: Dossier language and formatting
- **Performance**: Response times and cost efficiency
- **Reliability**: Deterministic and reproducible results
- **User Experience**: Error handling and feedback

### ✅ Integration Coverage
- **End-to-End Workflows**: Complete user journeys
- **Error Scenarios**: Graceful degradation
- **Concurrent Usage**: Multi-user performance
- **Format Support**: eClaimLink and Shafafiya

## Troubleshooting

### Common Issues

1. **Demo Files Not Found**
   ```
   pytest.skip: Demo XML file not available
   ```
   - Ensure demo files exist in `data/dataset_2/synthetic_dataset/UAE_XML/`

2. **LLM Connection Issues**
   ```
   Error: Failed to connect to LLM service
   ```
   - Check environment variables and API keys
   - Verify network connectivity

3. **Performance Test Failures**
   ```
   AssertionError: Pipeline took Xs > target
   ```
   - Performance targets are relaxed for integration testing
   - Check system resources and network latency

4. **Memory Issues**
   ```
   MemoryError during test execution
   ```
   - Run tests individually: `pytest -k "specific_test"`
   - Increase system memory or reduce concurrent tests

### Test Data Management

```bash
# Clean test outputs
rm -rf output/

# Reset test environment
pytest --cache-clear tests/integration/
```

## Continuous Integration

### Test Pipeline Configuration
```yaml
# Example CI configuration
test_integration:
  script:
    - pytest tests/integration/ -v --tb=short
  timeout: 30 minutes
  allow_failure: false
  artifacts:
    reports:
      junit: tests/integration/results.xml
```

### Required Environment
- Python 3.12+
- All project dependencies
- Demo data files
- LLM API access (for full testing)

## Success Metrics

### ✅ All Tests Passing
- Pipeline core functionality validated
- API endpoints working correctly
- CLI interface operational
- Dossier quality meets standards
- UI workflows complete successfully

### ✅ Performance Within Targets
- Cost efficiency maintained
- Response times acceptable
- Memory usage reasonable
- Concurrent load handling

### ✅ Quality Assurance
- Medical language professional
- Citations accurate and formatted
- Error handling graceful
- User experience smooth