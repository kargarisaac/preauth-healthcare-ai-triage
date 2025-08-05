# Nazmito Patient-Centric Workflow Test Suite

Comprehensive test suite for the Nazmito patient-centric healthcare XML processing and analysis workflow.

## Overview

This test suite provides comprehensive coverage for the complete patient workflow:

- **Backend Services**: Patient lookup, XML processing, Claude analysis, workflow orchestration
- **API Endpoints**: All 5 patient-centric endpoints with success/error scenarios
- **Frontend Components**: Patient selection, file upload, processing status, dashboard
- **End-to-End Workflow**: Complete patient journey from selection to analysis
- **Performance & Integration**: Real-world scenarios and load testing

## Test Architecture

```
tests/
├── conftest.py                                    # Shared fixtures and test data factories
├── unit/                                         # Backend service unit tests
│   ├── test_patient_lookup_service.py           # Patient ID resolution and folder management
│   ├── test_workflow_orchestrator.py            # End-to-end workflow coordination
│   ├── test_xml_processing_service.py           # XML to FHIR processing
│   ├── test_claude_analysis_service.py          # Claude AI analysis integration
│   ├── test_csv_processor.py                    # CSV processing (legacy)
│   ├── test_data_quality.py                     # Data validation (legacy)
│   ├── test_eclaim_link_ingestor.py            # eClaimLink format (legacy)
│   └── test_shafafiya_ingestor.py              # Shafafiya format (legacy)
├── api/                                          # API integration tests
│   ├── test_enhanced_endpoints.py               # Legacy endpoints
│   └── test_patient_workflow_endpoints.py       # Patient workflow endpoints
├── integration/                                  # End-to-end integration tests
│   ├── test_data_pipeline.py                   # Legacy pipeline tests
│   └── test_patient_workflow_e2e.py            # Complete patient workflow E2E
ui-react/src/components/dashboard/__tests__/     # Frontend component tests
├── PatientSelector.test.tsx                     # Patient selection dropdown
├── ProcessingStatus.test.tsx                    # Workflow progress tracking
├── PatientDashboard.test.tsx                    # Patient information dashboard
└── FileUploadArea.test.tsx                      # File upload interface
```

## Quick Start

### Running Tests

```bash
# Run all tests using our test runner
python scripts/run_tests.py --all

# Run critical path tests (fastest, for development)
python scripts/run_tests.py --critical

# Run specific test suites
python scripts/run_tests.py --unit           # Backend unit tests
python scripts/run_tests.py --integration    # API integration tests  
python scripts/run_tests.py --frontend       # React component tests
python scripts/run_tests.py --e2e           # End-to-end workflow tests
python scripts/run_tests.py --performance    # Performance tests

# Setup test environment
python scripts/run_tests.py --setup

# Generate comprehensive test report
python scripts/run_tests.py --report
```

### Direct Pytest Commands

```bash
# Backend tests
pytest tests/unit/ -v --cov=api/services
pytest tests/api/ -v 
pytest tests/integration/ -v -m integration

# Frontend tests (in ui-react directory)
cd ui-react && npm test

# Specific test files
pytest tests/unit/test_patient_lookup_service.py -v
pytest tests/api/test_patient_workflow_endpoints.py::TestPatientWorkflowEndpoints::test_complete_patient_workflow_integration -v
```

## Patient Workflow Test Coverage

### 1. Backend Service Unit Tests

**PatientLookupService** (`test_patient_lookup_service.py`):
- Patient ID to folder path resolution
- Patient profile and history retrieval
- Data availability validation
- Patient database building and indexing

**WorkflowOrchestrator** (`test_workflow_orchestrator.py`):
- Complete upload-to-analysis workflow
- Error handling and recovery
- Service coordination and integration
- Cost limit management

**XMLProcessingService** (`test_xml_processing_service.py`):
- eClaimLink and Shafafiya XML processing
- FHIR bundle generation
- Patient ID extraction from XML
- File validation and error handling

**ClaudeAnalysisService** (`test_claude_analysis_service.py`):
- Multi-agent analysis workflow
- Cost estimation and tracking
- Clinical context extraction
- API error handling and fallbacks

### 2. API Integration Tests

**Patient Workflow Endpoints** (`test_patient_workflow_endpoints.py`):

```python
# Core endpoints tested:
GET  /api/patients                     # Patient dropdown data
POST /api/upload-xml                   # File upload with patient selection
POST /api/process/{patient_id}         # XML processing for patient
POST /api/analyze/{patient_id}         # Claude analysis
GET  /api/patient/{patient_id}/dashboard # Patient dashboard data

# Test scenarios:
- Successful responses with real patient data
- Error handling (invalid patient_id, missing files, etc.)
- File upload validation (size, format, encoding)
- Claude analysis cost limits and availability
- Complete workflow integration
- Concurrent request handling
```

### 3. Frontend Component Tests

**PatientSelector** (`PatientSelector.test.tsx`):
- Patient list loading and display
- Search and filtering functionality  
- Patient selection handling
- Error states and retry mechanisms
- Accessibility support

**ProcessingStatus** (`ProcessingStatus.test.tsx`):
- Workflow step visualization
- Progress tracking and updates
- Error state handling
- Real-time status updates
- Interactive step details

**PatientDashboard** (`PatientDashboard.test.tsx`):
- Patient information display
- File history and processing status
- Analysis results visualization
- Dashboard actions (refresh, export, analyze)
- Real-time data updates

### 4. End-to-End Workflow Tests

**Complete Patient Journey** (`test_patient_workflow_e2e.py`):

```python
# Full workflow scenarios:
1. Patient selection from dropdown
2. XML file upload with patient context
3. XML processing and FHIR bundle generation
4. Claude analysis with multi-agent workflow
5. Dashboard view with complete results

# Error scenarios:
- XML processing failures
- Claude service unavailability
- Cost limit exceeded
- Network timeouts and retries

# Performance scenarios:
- Large file processing
- Concurrent patient workflows
- Memory usage and cleanup
```

## Test Data and Fixtures

### Dynamic Test Data Generation

```python
# Patient test data
mock_patients = [
    {
        "patient_id": "patient-123",
        "folder_name": "Ahmed_Al_Mansoori", 
        "has_profile": True,
        "xml_files": 3,
        "processed_json_files": 2
    }
]

# Realistic XML samples
sample_eclaim_xml = """
<?xml version="1.0" encoding="UTF-8"?>
<PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
    <Header>
        <SenderID>PROV12345</SenderID>
        <TransactionID>TXN-ECLAIM-2025-001789</TransactionID>
    </Header>
    <JustificationText>Patient with Type 2 diabetes needs HbA1c monitoring...</JustificationText>
    <ServiceRequests>
        <ServiceRequest>
            <ct:ActivityCode>83036</ct:ActivityCode>
            <ct:DiagnosisCode>E11.9</ct:DiagnosisCode>
            <RequestedAmount currency="AED">125.50</RequestedAmount>
        </ServiceRequest>
    </ServiceRequests>
</PriorAuthorizationRequest>
"""

# Expected FHIR bundles
expected_bundle = {
    "resourceType": "Bundle",
    "authorization_id": "TXN-ECLAIM-2025-001789",
    "fhir_resources": {
        "claim-1": {"resourceType": "Claim", "diagnosis": [{"code": "E11.9"}]}
    }
}

# Claude analysis results
expected_analysis = {
    "summary": "Comprehensive diabetes management analysis",
    "cost_usd": 1.25,
    "agent_results": {
        "clinical_analyzer": {"findings": ["Type 2 diabetes confirmed"]},
        "medical_reviewer": {"approval_recommendation": "APPROVE"},
        "recommendation_agent": {"recommendations": ["Approve HbA1c test"]}
    }
}
```

### Service Mocking Strategy

```python
@pytest.fixture
def mock_comprehensive_services():
    """Mock all services for E2E testing."""
    with patch('api.main.patient_lookup_service') as mock_patient, \
         patch('api.main.xml_processing_service') as mock_xml, \
         patch('api.main.claude_analysis_service') as mock_claude:
        
        # Configure realistic mock responses
        mock_patient.get_all_patients.return_value = mock_patients
        mock_xml.process_xml_file.return_value = {"success": True, "bundle": expected_bundle}
        mock_claude.analyze_patient_data.return_value = {"success": True, "analysis": expected_analysis}
        
        yield {"patient": mock_patient, "xml": mock_xml, "claude": mock_claude}
```

## Test Categories and Markers

```python
# Test execution categories
@pytest.mark.unit           # Fast, isolated unit tests
@pytest.mark.integration    # API and service integration tests
@pytest.mark.performance    # Performance and load tests
@pytest.mark.e2e           # End-to-end workflow tests
@pytest.mark.slow          # Long-running tests (may be skipped)

# Feature-specific markers
@pytest.mark.patient_workflow  # Patient-centric workflow tests
@pytest.mark.claude_analysis   # Claude AI analysis tests
@pytest.mark.xml_processing    # XML to FHIR processing tests
@pytest.mark.fhir              # FHIR resource validation tests

# Quality markers
@pytest.mark.critical       # Critical path tests (must pass)
@pytest.mark.edge_case      # Edge cases and error scenarios
@pytest.mark.regression     # Regression prevention tests
```

## Performance Benchmarks

### Backend Performance Targets

```python
# API Response Times (95th percentile)
GET  /api/patients                 < 500ms   # Patient list retrieval
POST /api/upload-xml              < 2s      # File upload and basic processing
POST /api/process/{patient_id}    < 10s     # XML to FHIR processing
POST /api/analyze/{patient_id}    < 30s     # Claude analysis (depends on complexity)
GET  /api/patient/{id}/dashboard  < 1s      # Dashboard data retrieval

# File Processing Limits
XML files: Up to 10MB, processed in < 30s
Concurrent requests: Up to 5 simultaneous analyses
Memory usage: < 1GB per analysis
Claude API cost: Configurable limits ($1-$10 per analysis)
```

### Frontend Performance Targets

```typescript
// Component Rendering Times
PatientSelector render:     < 100ms (for 100 patients)
ProcessingStatus updates:   < 50ms (real-time updates)
PatientDashboard load:      < 200ms (with full data)
FileUpload validation:      < 10ms (client-side validation)

// User Experience Metrics
First meaningful paint:     < 1s
Time to interactive:        < 2s
File upload feedback:       Immediate (< 100ms)
Status updates:             Real-time (WebSocket or polling)
```

## Test Execution Strategies

### Development Workflow

```bash
# Quick validation during development
python scripts/run_tests.py --critical

# Test specific component you're working on
python scripts/run_tests.py --test tests/unit/test_patient_lookup_service.py

# Test API changes
python scripts/run_tests.py --integration

# Test frontend changes
python scripts/run_tests.py --frontend
```

### CI/CD Pipeline

```yaml
# GitHub Actions / CI pipeline
steps:
  - name: Setup Test Environment
    run: python scripts/run_tests.py --setup
    
  - name: Run Critical Path Tests
    run: python scripts/run_tests.py --critical
    
  - name: Run Full Test Suite
    run: python scripts/run_tests.py --all
    
  - name: Generate Test Report
    run: python scripts/run_tests.py --report
    
  - name: Upload Coverage
    uses: codecov/codecov-action@v3
```

### Pre-Release Testing

```bash
# Comprehensive test suite before release
python scripts/run_tests.py --all
python scripts/run_tests.py --performance
python scripts/run_tests.py --report

# Stress testing with large datasets
pytest tests/integration/test_patient_workflow_e2e.py::TestPatientWorkflowRealScenarios -v

# Security and error handling validation
pytest -m "edge_case or security" -v
```

## Debugging and Troubleshooting

### Common Issues

1. **Mock Service Configuration**:
   ```python
   # Ensure mocks return expected data structures
   mock_service.method.return_value = {"success": True, "data": expected_data}
   ```

2. **Async Test Issues**:
   ```python
   @pytest.mark.asyncio
   async def test_async_workflow():
       result = await service.async_method()
   ```

3. **File Path Resolution**:
   ```python
   # Use absolute paths in tests
   temp_file = temp_xml_file(xml_content)
   assert Path(temp_file).exists()
   ```

4. **Frontend Test Environment**:
   ```bash
   # Ensure React testing environment is set up
   cd ui-react
   npm install
   npm test -- --watchAll=false
   ```

### Debug Commands

```bash
# Verbose test output with no capture
pytest tests/unit/test_patient_lookup_service.py -vvv -s

# Run single test method
pytest tests/api/test_patient_workflow_endpoints.py::TestPatientWorkflowEndpoints::test_upload_xml_endpoint_success -vvv

# Debug frontend tests
cd ui-react && npm test -- --verbose --no-coverage PatientSelector.test.tsx

# Profile test performance
pytest --durations=10
```

## Coverage Requirements

### Backend Coverage Targets

- **Overall Backend**: ≥ 90% line coverage
- **Core Services**: ≥ 95% line coverage
  - `api/services/patient_lookup_service.py`
  - `api/services/workflow_orchestrator.py`
  - `api/services/xml_processing_service.py`
  - `api/services/claude_analysis_service.py`
- **API Endpoints**: ≥ 90% line coverage
  - All 5 patient workflow endpoints
  - Error handling paths
  - Input validation logic

### Frontend Coverage Targets

- **Component Coverage**: ≥ 85% line coverage
- **Critical Components**: ≥ 90% line coverage
  - `PatientSelector.tsx`
  - `ProcessingStatus.tsx`
  - `PatientDashboard.tsx`
- **Hook Coverage**: ≥ 80% line coverage
- **Utility Functions**: ≥ 95% line coverage

### Coverage Reports

```bash
# Generate coverage reports
python scripts/run_tests.py --report

# View HTML coverage report
open htmlcov/index.html

# Frontend coverage
cd ui-react && npm run test:coverage
open ui-react/coverage/lcov-report/index.html
```

## Contributing to Tests

### Adding New Tests

1. **Follow Naming Conventions**:
   ```python
   def test_[component]_[scenario]_[expected_outcome]():
       """Test [component] [scenario] results in [expected outcome]."""
   ```

2. **Use Appropriate Markers**:
   ```python
   @pytest.mark.unit
   @pytest.mark.patient_workflow
   def test_patient_lookup_service_find_patient_success():
   ```

3. **Follow AAA Pattern**:
   ```python
   def test_example():
       # Arrange
       patient_id = "test-patient-123"
       mock_service.setup_patient_data(patient_id)
       
       # Act
       result = service.find_patient(patient_id)
       
       # Assert
       assert result["success"] is True
       assert result["patient_id"] == patient_id
   ```

### Test Quality Checklist

- [ ] Test name clearly describes scenario and expected outcome
- [ ] Test is isolated and doesn't depend on other tests
- [ ] Both success and failure paths are tested
- [ ] Edge cases and error conditions are covered
- [ ] Performance implications are considered
- [ ] Mock data is realistic and representative
- [ ] Test runs consistently (no flaky behavior)
- [ ] Documentation explains complex test scenarios

### Review Guidelines

- Tests should be reviewed as carefully as production code
- New features require corresponding test coverage
- Breaking changes need updated test expectations
- Performance tests should be updated for new features
- Integration tests should reflect real-world usage patterns

This comprehensive test suite ensures the reliability, performance, and maintainability of the Nazmito patient-centric workflow, providing confidence for healthcare data processing in production environments.