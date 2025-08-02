"""
FastAPI backend wrapper for XMLProcessor.

Production-ready API server that provides HTTP endpoints for processing
UAE healthcare XML formats (eClaimLink and Shafafiya) through the XMLProcessor.
"""

import os
import sys
import tempfile
import time
import traceback
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, Any, List, Optional

import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import BaseModel, Field

# Import processors from pipelines
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)  # noqa: E402

from pipelines.csv_processor import CSVProcessor  # noqa: E402
from pipelines.xml_processor import XMLProcessor  # noqa: E402

# Constants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_XML_EXTENSIONS = {".xml"}
ALLOWED_CSV_EXTENSIONS = {".csv"}
SAMPLES_DIR = Path(__file__).parent.parent / "samples"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    # Startup
    logger.info("Starting Nazmito Healthcare Data Processing API...")

    # Create logs directory
    os.makedirs("api/logs", exist_ok=True)

    # Log startup info
    logger.info("API Version: 1.0.0")
    logger.info(f"Samples directory: {SAMPLES_DIR}")
    logger.info(f"Max file size: {MAX_FILE_SIZE // (1024*1024)}MB")
    logger.info(
        "Supported formats: XML (eClaimLink, Shafafiya), CSV (Claims, Clinical)"
    )

    logger.info("Nazmito Healthcare Data Processing API started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Nazmito Healthcare Data Processing API...")


# Initialize FastAPI app
app = FastAPI(
    title="Nazmito Healthcare Data Processing API",
    description="API for processing UAE healthcare data formats including XML (eClaimLink and Shafafiya) and CSV (Claims and Clinical)",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# Configure CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


def serialize_numpy_types(obj):
    """Convert numpy types to Python native types for JSON serialization."""
    if isinstance(obj, dict):
        return {k: serialize_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_numpy_types(item) for item in obj]
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    elif isinstance(obj, np.dtype):
        return str(obj)
    elif hasattr(obj, 'dtype'):
        # Handle pandas/numpy types
        return str(obj.dtype) if hasattr(obj, 'dtype') else str(obj)
    else:
        return obj


# Initialize processors
xml_processor = XMLProcessor()
csv_processor = CSVProcessor()

# Configure logging
logger.add("api/logs/fastapi.log", rotation="10 MB", retention="30 days")


# Response models
class ProcessingResponse(BaseModel):
    """Response model for processing endpoints (XML and CSV)."""

    success: bool = Field(..., description="Whether processing was successful")
    data: Optional[Dict[str, Any]] = Field(
        None, description="Processed canonical JSON data"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Processing metadata"
    )
    error: Optional[str] = Field(None, description="Error message if processing failed")


class CSVProcessRequest(BaseModel):
    """Request model for CSV processing."""

    file_type: str = Field(..., description="Type of CSV file (claims or clinical)")


class CSVProcessResponse(BaseModel):
    """Response model for CSV processing endpoints."""

    success: bool = Field(..., description="Whether processing was successful")
    data: Optional[Dict[str, Any]] = Field(
        None, description="Processed canonical JSON data"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="CSV processing metadata"
    )
    error: Optional[str] = Field(None, description="Error message if processing failed")


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Service status")
    timestamp: str = Field(..., description="Current timestamp")
    version: str = Field(..., description="API version")


class SampleFile(BaseModel):
    """Sample file information model."""

    name: str = Field(..., description="Sample file name")
    format: str = Field(
        ..., description="File format (eClaimLink, Shafafiya, Claims CSV, Clinical CSV)"
    )
    size: int = Field(..., description="File size in bytes")
    path: str = Field(..., description="Relative file path")
    file_type: str = Field(..., description="File type (xml or csv)")


class ErrorResponse(BaseModel):
    """Error response model."""

    success: bool = Field(False, description="Always false for error responses")
    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Detailed error information")
    timestamp: str = Field(..., description="Error timestamp")


# Helper functions
def validate_xml_file(file: UploadFile) -> None:
    """Validate uploaded XML file."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided"
        )

    # Check file extension
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in ALLOWED_XML_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Only XML files are allowed. Got: {file_extension}",
        )

    # Check content type
    if file.content_type and not file.content_type.startswith(
        ('application/xml', 'text/xml')
    ):
        logger.warning(
            f"Unexpected content type: {file.content_type} for file: {file.filename}"
        )


def validate_csv_file(file: UploadFile) -> None:
    """Validate uploaded CSV file."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided"
        )

    # Check file extension
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in ALLOWED_CSV_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Only CSV files are allowed. Got: {file_extension}",
        )

    # Check content type
    if file.content_type and not file.content_type.startswith(
        ('text/csv', 'application/csv')
    ):
        logger.warning(
            f"Unexpected content type: {file.content_type} for file: {file.filename}"
        )


def save_temp_file(file: UploadFile, file_extension: str = '.xml') -> str:
    """Save uploaded file to temporary location."""
    try:
        # Create temporary file with appropriate extension
        temp_fd, temp_path = tempfile.mkstemp(suffix=file_extension, prefix='nazmito_')

        # Write file content
        with os.fdopen(temp_fd, 'wb') as temp_file:
            content = file.file.read()

            # Check file size
            if len(content) > MAX_FILE_SIZE:
                os.unlink(temp_path)
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB",
                )

            temp_file.write(content)

        logger.info(f"Saved uploaded file to temporary location: {temp_path}")
        return temp_path

    except Exception as e:
        if 'temp_path' in locals():
            try:
                os.unlink(temp_path)
            except OSError:
                pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded file: {str(e)}",
        )


def cleanup_temp_file(temp_path: str) -> None:
    """Clean up temporary file."""
    try:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
            logger.info(f"Cleaned up temporary file: {temp_path}")
    except Exception as e:
        logger.warning(f"Failed to cleanup temporary file {temp_path}: {str(e)}")


def create_processing_metadata(
    filename: str,
    file_size: int,
    processing_time: float,
    format_type: str,
    processor_type: str = "XMLProcessor",
    additional_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create processing metadata."""
    metadata = {
        "filename": filename,
        "file_size_bytes": file_size,
        "processing_time_seconds": round(processing_time, 3),
        "format": format_type,
        "api_version": "1.0.0",
        "processor_version": processor_type,
    }

    if additional_metadata:
        metadata.update(additional_metadata)

    return metadata


# API Endpoints


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    from datetime import datetime, timezone

    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc).isoformat(),
        version="1.0.0",
    )


@app.post("/api/process/eclaim", response_model=ProcessingResponse)
async def process_eclaim_xml(
    file: UploadFile = File(..., description="eClaimLink XML file")
):
    """
    Process eClaimLink XML file and return canonical JSON format.

    Accepts XML file upload and processes it through XMLProcessor to extract
    essential healthcare data in standardized format.
    """
    temp_path = None
    start_time = time.time()

    try:
        logger.info(f"Processing eClaimLink XML file: {file.filename}")

        # Validate file
        validate_xml_file(file)

        # Save to temporary file
        temp_path = save_temp_file(file, '.xml')
        file_size = os.path.getsize(temp_path)

        # Process XML
        result = xml_processor.process_eclaim_link(temp_path)

        # Calculate processing time
        processing_time = time.time() - start_time

        # Create metadata
        metadata = create_processing_metadata(
            filename=file.filename,
            file_size=file_size,
            processing_time=processing_time,
            format_type="eClaimLink",
        )

        logger.info(
            f"Successfully processed eClaimLink XML: {file.filename} in {processing_time:.3f}s"
        )

        return ProcessingResponse(success=True, data=result, metadata=metadata)

    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = f"Failed to process eClaimLink XML: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_msg
        )

    finally:
        if temp_path:
            cleanup_temp_file(temp_path)


@app.post("/api/process/shafafiya", response_model=ProcessingResponse)
async def process_shafafiya_xml(
    file: UploadFile = File(..., description="Shafafiya XML file")
):
    """
    Process Shafafiya XML file and return canonical JSON format.

    Accepts XML file upload and processes it through XMLProcessor to extract
    essential healthcare data in standardized format.
    """
    temp_path = None
    start_time = time.time()

    try:
        logger.info(f"Processing Shafafiya XML file: {file.filename}")

        # Validate file
        validate_xml_file(file)

        # Save to temporary file
        temp_path = save_temp_file(file, '.xml')
        file_size = os.path.getsize(temp_path)

        # Process XML
        result = xml_processor.process_shafafiya(temp_path)

        # Calculate processing time
        processing_time = time.time() - start_time

        # Create metadata
        metadata = create_processing_metadata(
            filename=file.filename,
            file_size=file_size,
            processing_time=processing_time,
            format_type="Shafafiya",
        )

        logger.info(
            f"Successfully processed Shafafiya XML: {file.filename} in {processing_time:.3f}s"
        )

        return ProcessingResponse(success=True, data=result, metadata=metadata)

    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = f"Failed to process Shafafiya XML: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_msg
        )

    finally:
        if temp_path:
            cleanup_temp_file(temp_path)


@app.post("/api/process/csv", response_model=CSVProcessResponse)
async def process_csv_file(
    file: UploadFile = File(..., description="CSV file (claims or clinical data)")
):
    """
    Process CSV file and return canonical JSON format.

    Accepts CSV file upload and processes it through CSVProcessor to extract
    healthcare data in standardized format. Automatically detects whether
    the CSV contains claims or clinical data.
    """
    temp_path = None
    start_time = time.time()

    try:
        logger.info(f"Processing CSV file: {file.filename}")

        # Validate file
        validate_csv_file(file)

        # Save to temporary file
        temp_path = save_temp_file(file, '.csv')
        file_size = os.path.getsize(temp_path)

        # Auto-detect CSV type and process
        result, csv_type = auto_detect_and_process_csv(temp_path)

        # Calculate processing time
        processing_time = time.time() - start_time

        # Create CSV-specific metadata from Bundle structure
        raw_data = result.get('raw_data', {})
        columns = raw_data.get('columns', [])
        fhir_resources = result.get('fhir_resources', {})

        csv_metadata = {
            "csv_type": csv_type,
            "total_records": result.get('total_records', 0),
            "detected_columns": len(columns),
            "detected_resources": len(fhir_resources),
            "resource_types": list(
                set(
                    [
                        res.get('resourceType', 'Unknown')
                        for res in fhir_resources.values()
                    ]
                )
            ),
            "data_quality_score": result.get('data_quality_score', 0.0),
        }

        # Create metadata
        metadata = create_processing_metadata(
            filename=file.filename,
            file_size=file_size,
            processing_time=processing_time,
            format_type=f"{csv_type} CSV",
            processor_type="CSVProcessor",
            additional_metadata=csv_metadata,
        )

        logger.info(
            f"Successfully processed {csv_type} CSV: {file.filename} in {processing_time:.3f}s"
        )

        return CSVProcessResponse(success=True, data=result, metadata=metadata)

    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = f"Failed to process CSV file: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_msg
        )

    finally:
        if temp_path:
            cleanup_temp_file(temp_path)


def auto_detect_and_process_csv(csv_path: str) -> tuple[Dict[str, Any], str]:
    """Auto-detect CSV type and process using unified CSVProcessor."""
    # Process CSV using unified processor (automatically detects resource types)
    result = serialize_numpy_types(csv_processor.process_claims_csv(csv_path))

    # Determine dominant CSV type based on detected resources
    raw_data = result.get('raw_data', {})
    resource_detections = raw_data.get('resource_detections', [])

    # Analyze detected resources to determine CSV type
    resource_types = [r['resource_type'] for r in resource_detections]

    # Determine primary type based on detected resources
    if 'Claim' in resource_types:
        csv_type = "Claims"
    elif 'Observation' in resource_types:
        csv_type = "Clinical"
    elif 'MedicationStatement' in resource_types:
        csv_type = "Clinical"
    elif 'ServiceRequest' in resource_types:
        csv_type = "Claims"
    else:
        csv_type = "Mixed"

    return result, csv_type


@app.get("/api/samples", response_model=List[SampleFile])
async def list_sample_files():
    """
    List available sample files (XML and CSV).

    Returns information about sample files that can be used for testing
    the processing endpoints.
    """
    try:
        samples = []

        if not SAMPLES_DIR.exists():
            logger.warning(f"Samples directory not found: {SAMPLES_DIR}")
            return samples

        # Map sample files to their formats
        format_mapping = {
            # XML files
            "eclaim_link_request.xml": ("eClaimLink", "xml"),
            "shafafiya_prior_auth_request.xml": ("Shafafiya", "xml"),
            # CSV files
            "healthcare_claims_sample.csv": ("Claims CSV", "csv"),
            "clinical_observations_sample.csv": ("Clinical CSV", "csv"),
        }

        # Process XML files
        for file_path in SAMPLES_DIR.glob("*.xml"):
            if file_path.is_file():
                file_size = file_path.stat().st_size
                format_info = format_mapping.get(file_path.name, ("Unknown", "xml"))

                sample = SampleFile(
                    name=file_path.name,
                    format=format_info[0],
                    size=file_size,
                    path=f"samples/{file_path.name}",
                    file_type=format_info[1],
                )
                samples.append(sample)

        # Process CSV files
        for file_path in SAMPLES_DIR.glob("*.csv"):
            if file_path.is_file():
                file_size = file_path.stat().st_size
                format_info = format_mapping.get(file_path.name, ("Unknown CSV", "csv"))

                sample = SampleFile(
                    name=file_path.name,
                    format=format_info[0],
                    size=file_size,
                    path=f"samples/{file_path.name}",
                    file_type=format_info[1],
                )
                samples.append(sample)

        logger.info(f"Found {len(samples)} sample files")
        return samples

    except Exception as e:
        logger.error(f"Failed to list sample files: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list sample files: {str(e)}",
        )


@app.get("/api/samples/csv", response_model=List[SampleFile])
async def list_csv_sample_files():
    """
    List available CSV sample files only.

    Returns information about CSV sample files that can be used for testing
    the CSV processing endpoints.
    """
    try:
        samples = []

        if not SAMPLES_DIR.exists():
            logger.warning(f"Samples directory not found: {SAMPLES_DIR}")
            return samples

        # Map CSV sample files to their formats
        csv_format_mapping = {
            "healthcare_claims_sample.csv": "Claims CSV",
            "clinical_observations_sample.csv": "Clinical CSV",
        }

        for file_path in SAMPLES_DIR.glob("*.csv"):
            if file_path.is_file():
                file_size = file_path.stat().st_size
                format_type = csv_format_mapping.get(file_path.name, "Unknown CSV")

                sample = SampleFile(
                    name=file_path.name,
                    format=format_type,
                    size=file_size,
                    path=f"samples/{file_path.name}",
                    file_type="csv",
                )
                samples.append(sample)

        logger.info(f"Found {len(samples)} CSV sample files")
        return samples

    except Exception as e:
        logger.error(f"Failed to list CSV sample files: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list CSV sample files: {str(e)}",
        )


# Optional endpoints for processing sample files
@app.post("/api/process/sample/eclaim")
async def process_sample_eclaim():
    """Process the built-in eClaimLink sample file."""
    sample_path = SAMPLES_DIR / "eclaim_link_request.xml"

    if not sample_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="eClaimLink sample file not found",
        )

    try:
        start_time = time.time()
        result = xml_processor.process_eclaim_link(str(sample_path))
        processing_time = time.time() - start_time

        metadata = create_processing_metadata(
            filename=sample_path.name,
            file_size=sample_path.stat().st_size,
            processing_time=processing_time,
            format_type="eClaimLink",
        )

        return ProcessingResponse(success=True, data=result, metadata=metadata)

    except Exception as e:
        logger.error(f"Failed to process sample eClaimLink file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process sample file: {str(e)}",
        )


@app.post("/api/process/sample/shafafiya")
async def process_sample_shafafiya():
    """Process the built-in Shafafiya sample file."""
    sample_path = SAMPLES_DIR / "shafafiya_prior_auth_request.xml"

    if not sample_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shafafiya sample file not found",
        )

    try:
        start_time = time.time()
        result = xml_processor.process_shafafiya(str(sample_path))
        processing_time = time.time() - start_time

        metadata = create_processing_metadata(
            filename=sample_path.name,
            file_size=sample_path.stat().st_size,
            processing_time=processing_time,
            format_type="Shafafiya",
        )

        return ProcessingResponse(success=True, data=result, metadata=metadata)

    except Exception as e:
        logger.error(f"Failed to process sample Shafafiya file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process sample file: {str(e)}",
        )


@app.post("/api/process/sample/claims-csv", response_model=CSVProcessResponse)
async def process_sample_claims_csv():
    """Process the built-in claims CSV sample file."""
    sample_path = SAMPLES_DIR / "healthcare_claims_sample.csv"

    if not sample_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claims CSV sample file not found",
        )

    try:
        start_time = time.time()
        result = serialize_numpy_types(
            csv_processor.process_claims_csv(str(sample_path))
        )
        processing_time = time.time() - start_time

        # Create CSV-specific metadata from Bundle structure
        raw_data = result.get('raw_data', {})
        column_mappings = raw_data.get('column_mappings', [])
        resource_detections = raw_data.get('resource_detections', [])

        csv_metadata = {
            "csv_type": "Claims",
            "total_records": result.get('total', 0),
            "detected_columns": len(column_mappings),
            "detected_resources": len(resource_detections),
            "resource_types": [r['resource_type'] for r in resource_detections],
            "data_quality_score": next(
                (
                    ext.get('valueDecimal', 0.0)
                    for ext in result.get('extension', [])
                    if 'data-quality-score' in ext.get('url', '')
                ),
                0.0,
            ),
        }

        metadata = create_processing_metadata(
            filename=sample_path.name,
            file_size=sample_path.stat().st_size,
            processing_time=processing_time,
            format_type="Claims CSV",
            processor_type="CSVProcessor",
            additional_metadata=csv_metadata,
        )

        return CSVProcessResponse(success=True, data=result, metadata=metadata)

    except Exception as e:
        logger.error(f"Failed to process sample claims CSV file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process sample file: {str(e)}",
        )


@app.post("/api/process/sample/clinical-csv", response_model=CSVProcessResponse)
async def process_sample_clinical_csv():
    """Process the built-in clinical CSV sample file."""
    sample_path = SAMPLES_DIR / "clinical_observations_sample.csv"

    if not sample_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinical CSV sample file not found",
        )

    try:
        start_time = time.time()
        result = serialize_numpy_types(
            csv_processor.process_claims_csv(str(sample_path))
        )
        processing_time = time.time() - start_time

        # Create CSV-specific metadata from Bundle structure
        raw_data = result.get('raw_data', {})
        column_mappings = raw_data.get('column_mappings', [])
        resource_detections = raw_data.get('resource_detections', [])

        csv_metadata = {
            "csv_type": "Clinical",
            "total_records": result.get('total', 0),
            "detected_columns": len(column_mappings),
            "detected_resources": len(resource_detections),
            "resource_types": [r['resource_type'] for r in resource_detections],
            "data_quality_score": next(
                (
                    ext.get('valueDecimal', 0.0)
                    for ext in result.get('extension', [])
                    if 'data-quality-score' in ext.get('url', '')
                ),
                0.0,
            ),
        }

        metadata = create_processing_metadata(
            filename=sample_path.name,
            file_size=sample_path.stat().st_size,
            processing_time=processing_time,
            format_type="Clinical CSV",
            processor_type="CSVProcessor",
            additional_metadata=csv_metadata,
        )

        return CSVProcessResponse(success=True, data=result, metadata=metadata)

    except Exception as e:
        logger.error(f"Failed to process sample clinical CSV file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process sample file: {str(e)}",
        )


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    _ = request  # Suppress unused parameter warning
    from datetime import datetime, timezone

    logger.error(f"Unhandled exception: {str(exc)}\n{traceback.format_exc()}")

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal server error",
            details=str(exc) if app.debug else "An unexpected error occurred",
            timestamp=datetime.now(timezone.utc).isoformat(),
        ).model_dump(),
    )


if __name__ == "__main__":
    """
    Development server entry point.

    For production, use: uvicorn api.main:app --host 0.0.0.0 --port 8000
    """
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True,
    )
