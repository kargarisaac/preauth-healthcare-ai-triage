# Nazmito Healthcare XML API

FastAPI backend wrapper for processing UAE healthcare XML formats (eClaimLink and Shafafiya).

## Quick Start

### 1. Install Dependencies

```bash
# Install all dependencies including FastAPI
uv pip install -r pyproject.toml

# Or with pip
pip install fastapi uvicorn[standard] python-multipart pydantic
```

### 2. Start the Server

```bash
# Development mode (auto-reload)
python api/run_server.py

# Or directly with uvicorn
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
python api/run_server.py --mode production --workers 4
```

### 3. Access the API

- **API Documentation**: http://localhost:8000/api/docs
- **Alternative Docs**: http://localhost:8000/api/redoc
- **Health Check**: http://localhost:8000/api/health

## API Endpoints

### Core Processing Endpoints

#### `POST /api/process/eclaim`
Process eClaimLink XML files
- **Input**: XML file upload (multipart/form-data)
- **Output**: Canonical JSON format with healthcare data
- **Max file size**: 10MB

#### `POST /api/process/shafafiya`
Process Shafafiya XML files
- **Input**: XML file upload (multipart/form-data)
- **Output**: Canonical JSON format with healthcare data
- **Max file size**: 10MB

#### `POST /api/process/csv`
Process healthcare CSV files
- **Input**: CSV file upload (multipart/form-data)
- **Output**: Canonical JSON format with healthcare data
- **Max file size**: 10MB

### LLM-Enhanced Processing

#### `POST /api/process/csv-with-llm`
Process CSV files with LLM-powered validation
- **Input**: CSV file upload with optional parameters
- **Parameters**:
  - `enable_llm`: Boolean (default: true)
  - `llm_provider`: String (openai, anthropic, google)
  - `enable_sampling`: Boolean (default: true for files > 1000 records)
  - `realtime_updates`: Boolean (default: true)
- **Output**: Enhanced validation with confidence scores and recommendations
- **Features**: Smart sampling, real-time progress updates, comprehensive validation reports

### Utility Endpoints

#### `GET /api/health`
Health check endpoint
- **Output**: Service status, timestamp, version, and LLM service availability
- **Enhanced Response**: Includes active tasks, queue size, and LLM service status

#### `GET /api/samples`
List available sample files
- **Output**: Array of sample file information

#### `POST /api/process/sample/eclaim`
Process built-in eClaimLink sample file
- **Output**: Processed sample data

#### `POST /api/process/sample/shafafiya`
Process built-in Shafafiya sample file
- **Output**: Processed sample data

### Task Management

#### `GET /api/tasks/{task_id}`
Retrieve task status and results
- **Input**: Task ID from async processing
- **Output**: Task status, progress, and results when completed
- **Statuses**: pending, in_progress, completed, failed

### Real-Time Updates

#### `WebSocket /ws/validation-progress/{task_id}`
Real-time progress updates for LLM validation
- **Connection**: WebSocket protocol
- **Updates**: Progress percentage, current step, status changes
- **Features**: Automatic reconnection, keep-alive pings

## Response Formats

### Standard Processing Response

XML and basic CSV processing endpoints return:

```json
{
  "success": true,
  "data": {
    "resourceType": "Bundle",
    "id": "eClaimLink-abc12345-20240801",
    "meta": {
      "profile": ["https://nazmito.com/fhir/StructureDefinition/healthcare-bundle"],
      "source": "eClaimLink",
      "lastUpdated": "2024-08-01T10:30:00Z",
      "versionId": "1"
    },
    "authorization_id": "TXN123456789",
    "sender": "SENDER001",
    "receiver": "RECEIVER001",
    "services": [...],
    "raw_data": {...}
  },
  "metadata": {
    "filename": "uploaded_file.xml",
    "file_size_bytes": 15420,
    "processing_time_seconds": 0.125,
    "format": "eClaimLink",
    "api_version": "1.0.0"
  }
}
```

### LLM-Enhanced Processing Response

CSV processing with LLM validation returns:

```json
{
  "success": true,
  "data": {
    "resourceType": "Bundle",
    "id": "Claims-CSV-abc123-20250802",
    "claims": [...],
    "fhir_resources": {...},
    "raw_data": {
      "sampling_applied": true,
      "sampling_metadata": {
        "total_records": 5000,
        "sampled_records": 500,
        "sampling_strategy": "smart_hybrid",
        "representative_score": 0.92
      }
    }
  },
  "validation_report": {
    "overall_quality_score": 0.85,
    "confidence_score": 0.92,
    "field_validations": [...],
    "resource_validations": [...],
    "recommendations": [...]
  },
  "ui_report": {
    "overall_grade": "B",
    "quality_percentage": 85,
    "total_records": 5000,
    "valid_records": 4250,
    "critical_count": 0,
    "warning_count": 5,
    "llm_enhanced": true,
    "sample_based": true
  },
  "metadata": {
    "task_id": "abc123-def456",
    "filename": "healthcare_data.csv",
    "processing_time_seconds": 15.3,
    "llm_processing_time_seconds": 12.1,
    "api_version": "1.0.0"
  }
}
```

### WebSocket Progress Updates

```json
{
  "task_id": "abc123-def456",
  "status": "llm_validating",
  "progress_percentage": 75,
  "current_step": "LLM validation step 4/5",
  "timestamp": "2025-08-02T08:49:00Z"
}
```

### Enhanced Health Check Response

```json
{
  "status": "healthy",
  "timestamp": "2025-08-02T08:49:00Z",
  "version": "1.0.0",
  "llm_services": {
    "openai": true,
    "anthropic": true,
    "google": true
  },
  "active_tasks": 2,
  "queue_size": 0,
  "avg_response_time": 0.5
}
```

## Testing

### Automated Tests

```bash
# Run the test suite (server must be running)
python api/test_api.py
```

### Manual Testing with curl

```bash
# Health check
curl http://localhost:8000/api/health

# List samples
curl http://localhost:8000/api/samples

# Process sample eClaimLink file
curl -X POST http://localhost:8000/api/process/sample/eclaim

# Upload and process XML file
curl -X POST \
  -F "file=@samples/eclaim_link_request.xml" \
  http://localhost:8000/api/process/eclaim
```

### Testing with Python requests

#### Basic Processing

```python
import requests

# Health check
response = requests.get("http://localhost:8000/api/health")
print(response.json())

# XML file upload
with open("samples/eclaim_link_request.xml", "rb") as f:
    files = {"file": ("test.xml", f, "application/xml")}
    response = requests.post("http://localhost:8000/api/process/eclaim", files=files)
    result = response.json()
    print(f"Success: {result['success']}")
    print(f"Authorization ID: {result['data']['authorization_id']}")
```

#### LLM-Enhanced Processing

```python
import requests
import time

# Upload CSV for LLM-enhanced processing
with open('healthcare_data.csv', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/process/csv-with-llm',
        files={'file': f},
        params={
            'enable_llm': True,
            'llm_provider': 'openai',
            'enable_sampling': True,
            'realtime_updates': True
        }
    )

task_data = response.json()
task_id = task_data['metadata']['task_id']
print(f"Task started: {task_id}")

# Poll task status
while True:
    response = requests.get(f'http://localhost:8000/api/tasks/{task_id}')
    task_status = response.json()

    if task_status['metadata']['status'] == 'completed':
        print("Task completed!")
        validation_report = task_status['validation_report']
        ui_report = task_status['ui_report']
        print(f"Quality Score: {ui_report['quality_percentage']}%")
        break
    elif task_status['metadata']['status'] == 'failed':
        print(f"Task failed: {task_status['error']}")
        break

    time.sleep(2)  # Poll every 2 seconds
```

#### WebSocket Integration

```python
import asyncio
import websockets
import json

async def monitor_progress(task_id):
    uri = f"ws://localhost:8000/ws/validation-progress/{task_id}"

    async with websockets.connect(uri) as websocket:
        async for message in websocket:
            update = json.loads(message)

            if update['status'] == 'completed':
                print("Processing completed!")
                break
            else:
                print(f"Progress: {update['progress_percentage']}%")
                print(f"Step: {update['current_step']}")

# Run WebSocket monitoring
# asyncio.run(monitor_progress(task_id))
```

## Development

### Project Structure

```
api/
├── main.py          # FastAPI application
├── run_server.py    # Server runner script
├── test_api.py      # API test suite
├── README.md        # This file
└── logs/           # Log files (created automatically)
```

### Key Features

- **Clean Architecture**: Wraps XMLProcessor without modification
- **Production Ready**: Proper error handling, logging, and validation
- **CORS Support**: Configured for frontend integration
- **File Validation**: Size limits, type checking, and security
- **Temporary File Handling**: Automatic cleanup of uploaded files
- **Comprehensive Logging**: Structured logs with rotation
- **Modern FastAPI**: Uses lifespan events and Pydantic v2

### Error Handling

The API provides structured error responses:

```json
{
  "success": false,
  "error": "Failed to process XML file",
  "details": "Invalid XML structure at line 45",
  "timestamp": "2024-08-01T10:30:00Z"
}
```

Common HTTP status codes:
- `200`: Success
- `400`: Bad request (invalid file, validation error)
- `413`: File too large
- `422`: Validation error
- `500`: Internal server error

### Configuration

Key configuration constants in `main.py`:
- `MAX_FILE_SIZE`: 10MB file upload limit
- `ALLOWED_EXTENSIONS`: Only `.xml` files accepted
- `SAMPLES_DIR`: Location of sample files

### Logging

Logs are written to:
- Console: Real-time output
- File: `api/logs/fastapi.log` (10MB rotation, 30 days retention)

## Smart Sampling Configuration

### Automatic Sampling

For CSV files with more than 1000 records, smart sampling is automatically applied:

```python
# Sampling configuration
config = {
    "enable_smart_sampling": True,
    "max_records_for_full_processing": 1000,
    "max_sample_size": 500,
    "min_sample_size": 100,
    "sampling_strategy": {
        "systematic_percentage": 60,
        "stratified_percentage": 30,
        "random_percentage": 10
    }
}
```

### Sample Size Calculation

- **Formula**: `min(500, max(100, sqrt(total_records) * 10))`
- **Example**: 5000 records → ~707 samples, capped at 500
- **Strategy**: 60% systematic + 30% stratified + 10% random
- **Quality**: Representativeness score calculated automatically

## LLM Validation Features

### Parallel Processing

- **Concurrent Validation**: Up to 5 parallel LLM calls
- **Provider Fallback**: OpenAI → Anthropic → Google AI
- **Rate Limiting**: Automatic throttling based on provider limits
- **Cost Optimization**: Uses fast models (GPT-4o-mini, Gemini Flash) by default

### Validation Types

1. **UAE Compliance Validation**
   - DHA/DOH regulation compliance
   - Cross-emirate referral validation
   - Authorization requirement checks

2. **Clinical Logic Assessment**
   - Medical procedure consistency
   - Diagnosis-treatment alignment
   - Age-appropriate care validation

3. **Data Anomaly Detection**
   - Statistical outlier identification
   - Temporal inconsistency detection
   - Duplicate pattern recognition

4. **Medical Code Validation**
   - ICD-10-AM code verification
   - CPT code validation
   - UAE-specific code compliance

## Integration with Data Processors

The API integrates with multiple data processors:

### XMLProcessor Integration

```python
from pipelines.xml_processor import XMLProcessor

processor = XMLProcessor()

# eClaimLink processing
result = processor.process_eclaim_link("path/to/file.xml")

# Shafafiya processing
result = processor.process_shafafiya("path/to/file.xml")
```

### CSVProcessor Integration

```python
from pipelines.csv_processor import CSVProcessor
from pipelines.llm_validator import LLMValidator

csv_processor = CSVProcessor()
llm_validator = LLMValidator()

# Basic CSV processing
result = csv_processor.process_csv("path/to/file.csv")

# Enhanced processing with LLM validation
result = csv_processor.process_csv_with_llm(
    "path/to/file.csv",
    llm_validator=llm_validator,
    enable_sampling=True
)
```

### BAML Integration

```python
from baml_client import b

# Direct BAML function calls
validation_result = await b.ValidateCompliance(data_sample)
quality_metrics = await b.GenerateQualityMetrics(validation_results)
recommendations = await b.GenerateRecommendations(quality_report)
```

All processing logic remains modular:
- Clean separation between API, processors, and LLM validation
- Easy testing and maintenance
- Consistent data models via BAML
- Backward compatibility with existing functionality

## Error Handling

### Standard API Errors

```json
{
  "success": false,
  "error": "Failed to process CSV file",
  "error_code": "PROCESSING_ERROR",
  "details": "Unable to parse CSV encoding",
  "validation_errors": [],
  "timestamp": "2025-08-02T08:49:00Z"
}
```

### LLM-Specific Errors

```json
{
  "success": false,
  "error": "LLM validation failed",
  "error_code": "LLM_ERROR",
  "details": "Rate limit exceeded for OpenAI",
  "fallback_used": "anthropic",
  "partial_results": true,
  "timestamp": "2025-08-02T08:49:00Z"
}
```

### WebSocket Error Handling

```javascript
ws.onerror = function(error) {
    console.error('WebSocket error:', error);
    // Implement reconnection logic
};

ws.onclose = function(event) {
    if (event.code !== 1000) {
        console.log('Connection lost, attempting to reconnect...');
        // Implement exponential backoff reconnection
    }
};
```

## Performance Considerations

### Large File Processing

1. **Smart Sampling**: Automatically applied to files > 1000 records
2. **Background Processing**: CPU-intensive tasks run asynchronously
3. **Progress Updates**: Real-time feedback prevents timeouts
4. **Memory Management**: Streaming processing for large files
5. **Concurrent Processing**: Up to 5 simultaneous tasks

### LLM Optimization

- **Model Selection**: Fast models (GPT-4o-mini, Gemini Flash) for cost efficiency
- **Parallel Execution**: Multiple validation functions run concurrently
- **Provider Fallback**: Automatic failover reduces processing delays
- **Caching**: Results cached for repeated validations (when applicable)

## Security Considerations

### File Validation
- Strict file type checking (XML, CSV only)
- File size limits (10MB default)
- Content validation before processing
- Automatic cleanup of temporary files

### LLM Integration Security
- API key management and rotation
- Rate limiting and quota management
- Data privacy and anonymization
- No sensitive data logged in LLM requests

### WebSocket Security
- Connection limits per IP
- Authentication for sensitive data
- Automatic timeout and cleanup
- CORS protection for production

## Production Deployment

### With uvicorn

```bash
# Single worker
uvicorn api.main:app --host 0.0.0.0 --port 8000

# Multiple workers
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### With gunicorn + uvicorn workers

```bash
pip install gunicorn
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Environment Variables

- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)
- `WORKERS`: Number of workers (default: 1)

### Docker

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt

EXPOSE 8000

CMD ["python", "api/run_server.py", "--mode", "docker"]
```

## Security Considerations

- File size limits prevent DoS attacks
- Only XML files accepted
- Temporary files automatically cleaned up
- Input validation with Pydantic models
- Structured error responses (no stack traces in production)
- CORS configured for specific origins in production

## Performance

- Async/await throughout for concurrency
- Efficient temporary file handling
- Minimal memory footprint
- Processing time tracking
- Optimized for healthcare XML workloads

## Support

For issues and questions:
1. Check the logs in `api/logs/fastapi.log`
2. Run the test suite: `python api/test_api.py`
3. Verify XMLProcessor works directly: `python pipelines/xml_processor.py`
