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

### Utility Endpoints

#### `GET /api/health`
Health check endpoint
- **Output**: Service status, timestamp, and version

#### `GET /api/samples`
List available sample files
- **Output**: Array of sample file information

#### `POST /api/process/sample/eclaim`
Process built-in eClaimLink sample file
- **Output**: Processed sample data

#### `POST /api/process/sample/shafafiya`
Process built-in Shafafiya sample file
- **Output**: Processed sample data

## Response Format

All processing endpoints return data in this format:

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

```python
import requests

# Health check
response = requests.get("http://localhost:8000/api/health")
print(response.json())

# File upload
with open("samples/eclaim_link_request.xml", "rb") as f:
    files = {"file": ("test.xml", f, "application/xml")}
    response = requests.post("http://localhost:8000/api/process/eclaim", files=files)
    result = response.json()
    print(f"Success: {result['success']}")
    print(f"Authorization ID: {result['data']['authorization_id']}")
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

## Integration with XMLProcessor

The API is a thin wrapper around the existing `XMLProcessor` class:

```python
from pipelines.xml_processor import XMLProcessor

processor = XMLProcessor()

# eClaimLink processing
result = processor.process_eclaim_link("path/to/file.xml")

# Shafafiya processing
result = processor.process_shafafiya("path/to/file.xml")
```

All data processing logic remains in `XMLProcessor`, ensuring:
- Clean separation of concerns
- Easy testing and maintenance
- Consistency between API and direct usage
- Preservation of all original functionality

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
