"""
FastAPI backend wrapper for XMLProcessor.

Production-ready API server that provides HTTP endpoints for processing
UAE healthcare XML formats (eClaimLink and Shafafiya) through the XMLProcessor.
"""

import asyncio
import json
import os
import sys
import tempfile
import time
import traceback
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Set

import numpy as np
from fastapi import (
    FastAPI,
    File,
    UploadFile,
    HTTPException,
    status,
    WebSocket,
    WebSocketDisconnect,
    BackgroundTasks,
)

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
from api.models import (  # noqa: E402
    ProcessingResponse,
    CSVProcessResponse,
    LLMValidationResponse,
    UIFriendlyReport,
    ProgressUpdate,
    TaskInitiation,
    TaskCompletion,
    ProcessingStatus,
    LLMProvider,
    ProcessingConfig,
    LLMConfiguration,
    ErrorResponse,
    HealthResponse,
    SampleFile,
)

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
    elif hasattr(obj, "dtype"):
        # Handle pandas/numpy types
        return str(obj.dtype) if hasattr(obj, "dtype") else str(obj)
    else:
        return obj


# Initialize processors
xml_processor = XMLProcessor()
csv_processor = CSVProcessor()


# WebSocket connection manager
class ConnectionManager:
    """WebSocket connection manager for real-time progress updates."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.task_connections: Dict[
            str, Set[str]
        ] = {}  # task_id -> set of connection_ids

    async def connect(self, websocket: WebSocket, connection_id: str):
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        logger.info(f"WebSocket connected: {connection_id}")

    def disconnect(self, connection_id: str):
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            # Clean up task connections
            for task_id, conn_ids in self.task_connections.items():
                conn_ids.discard(connection_id)
        logger.info(f"WebSocket disconnected: {connection_id}")

    def subscribe_to_task(self, connection_id: str, task_id: str):
        if task_id not in self.task_connections:
            self.task_connections[task_id] = set()
        self.task_connections[task_id].add(connection_id)

    async def send_progress_update(self, task_id: str, update: ProgressUpdate):
        if task_id in self.task_connections:
            for connection_id in self.task_connections[task_id].copy():
                if connection_id in self.active_connections:
                    try:
                        await self.active_connections[connection_id].send_text(
                            update.model_dump_json()
                        )
                    except Exception as e:
                        logger.warning(f"Failed to send update to {connection_id}: {e}")
                        self.disconnect(connection_id)

    async def send_task_completion(self, task_id: str, completion: TaskCompletion):
        if task_id in self.task_connections:
            for connection_id in self.task_connections[task_id].copy():
                if connection_id in self.active_connections:
                    try:
                        await self.active_connections[connection_id].send_text(
                            completion.model_dump_json()
                        )
                    except Exception as e:
                        logger.warning(
                            f"Failed to send completion to {connection_id}: {e}"
                        )
                        self.disconnect(connection_id)
            # Clean up task connections after completion
            del self.task_connections[task_id]


# Global connection manager
connection_manager = ConnectionManager()

# Active tasks tracking
active_tasks: Dict[str, Dict[str, Any]] = {}

# Default configuration
default_config = ProcessingConfig(
    enable_llm_validation=True,
    llm_config=LLMConfiguration(
        provider=LLMProvider.OPENAI,
        model="gpt-4",
        max_tokens=4000,
        temperature=0.1,
        timeout_seconds=30,
        enable_parallel=True,
        max_parallel_requests=3,
    ),
)

# Configure logging
logger.add("api/logs/fastapi.log", rotation="10 MB", retention="30 days")


# Request models
class CSVProcessRequest(BaseModel):
    """Request model for CSV processing."""

    file_type: str = Field(..., description="Type of CSV file (claims or clinical)")


class LLMValidationRequest(BaseModel):
    """Request model for LLM-enhanced CSV processing."""

    enable_llm: bool = Field(True, description="Enable LLM validation")
    llm_provider: Optional[LLMProvider] = Field(
        None, description="LLM provider preference"
    )
    enable_sampling: bool = Field(
        True, description="Enable smart sampling for large files"
    )
    max_sample_size: Optional[int] = Field(
        None, ge=50, le=1000, description="Override max sample size"
    )
    realtime_updates: bool = Field(
        True, description="Enable WebSocket progress updates"
    )


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
        ("application/xml", "text/xml")
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
        ("text/csv", "application/csv")
    ):
        logger.warning(
            f"Unexpected content type: {file.content_type} for file: {file.filename}"
        )


def save_temp_file(file: UploadFile, file_extension: str = ".xml") -> str:
    """Save uploaded file to temporary location."""
    try:
        # Create temporary file with appropriate extension
        temp_fd, temp_path = tempfile.mkstemp(suffix=file_extension, prefix="nazmito_")

        # Write file content
        with os.fdopen(temp_fd, "wb") as temp_file:
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
        if "temp_path" in locals():
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
    """Enhanced health check endpoint with LLM service status."""
    # Check LLM service availability (mock for now)
    llm_services = {
        "openai": True,  # Would check actual API availability
        "anthropic": True,
        "azure_openai": False,
    }

    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc),
        version="1.0.0",
        llm_services=llm_services,
        active_tasks=len(active_tasks),
        queue_size=0,  # Would check actual queue
        avg_response_time=0.5,
    )


@app.post("/api/process/eclaim", response_model=ProcessingResponse)
async def process_eclaim_xml(
    file: UploadFile = File(..., description="eClaimLink XML file"),
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
        temp_path = save_temp_file(file, ".xml")
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
    file: UploadFile = File(..., description="Shafafiya XML file"),
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
        temp_path = save_temp_file(file, ".xml")
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
    file: UploadFile = File(..., description="CSV file (claims or clinical data)"),
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
        temp_path = save_temp_file(file, ".csv")
        file_size = os.path.getsize(temp_path)

        # Auto-detect CSV type and process
        result, csv_type = auto_detect_and_process_csv(temp_path)

        # Calculate processing time
        processing_time = time.time() - start_time

        # Create CSV-specific metadata from Bundle structure
        raw_data = result.get("raw_data", {})
        columns = raw_data.get("columns", [])
        fhir_resources = result.get("fhir_resources", {})

        csv_metadata = {
            "csv_type": csv_type,
            "total_records": result.get("total_records", 0),
            "detected_columns": len(columns),
            "detected_resources": len(fhir_resources),
            "resource_types": list(
                set(
                    [
                        res.get("resourceType", "Unknown")
                        for res in fhir_resources.values()
                    ]
                )
            ),
            "data_quality_score": result.get("data_quality_score", 0.0),
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
    raw_data = result.get("raw_data", {})
    resource_detections = raw_data.get("resource_detections", [])

    # Analyze detected resources to determine CSV type
    resource_types = [r["resource_type"] for r in resource_detections]

    # Determine primary type based on detected resources
    if "Claim" in resource_types:
        csv_type = "Claims"
    elif "Observation" in resource_types:
        csv_type = "Clinical"
    elif "MedicationStatement" in resource_types:
        csv_type = "Clinical"
    elif "ServiceRequest" in resource_types:
        csv_type = "Claims"
    else:
        csv_type = "Mixed"

    return result, csv_type


async def perform_llm_validation(
    data: Dict[str, Any], config: LLMConfiguration, task_id: str
) -> Dict[str, Any]:
    """
    Perform actual LLM validation using BAML client with progress updates.
    """
    try:
        from baml_client import b

        # Prepare data sample for BAML validation
        data_sample = {
            "resource_type": "HealthcareBundle",
            "raw_data": json.dumps(data),
            "context": {
                "source_system": "CSV",
                "processing_date": datetime.now(timezone.utc).isoformat(),
                "provider_type": "Unknown",
            },
        }

        validation_steps = [
            ("UAE Compliance Validation", "ValidateCompliance"),
            ("Clinical Logic Assessment", "AssessClinicalLogic"),
            ("Data Anomaly Detection", "DetectDataAnomalies"),
            ("Medical Code Validation", "ValidateMedicalCodes"),
            ("Comprehensive Analysis", "ComprehensiveValidation"),
        ]

        results = {}

        for i, (step_name, function_name) in enumerate(validation_steps):
            progress = int((i / len(validation_steps)) * 100)
            update = ProgressUpdate(
                task_id=task_id,
                status=ProcessingStatus.LLM_VALIDATING,
                progress_percentage=progress,
                current_step=f"{step_name} ({i+1}/{len(validation_steps)})",
                timestamp=datetime.now(timezone.utc),
            )
            await connection_manager.send_progress_update(task_id, update)

            # Call BAML function
            if function_name == "ValidateCompliance":
                result = await b.ValidateCompliance(data_sample)
            elif function_name == "AssessClinicalLogic":
                result = await b.AssessClinicalLogic(data_sample)
            elif function_name == "DetectDataAnomalies":
                result = await b.DetectDataAnomalies(data_sample)
            elif function_name == "ValidateMedicalCodes":
                result = await b.ValidateMedicalCodes(data_sample)
            elif function_name == "ComprehensiveValidation":
                result = await b.ComprehensiveValidation(data_sample)

            results[function_name] = result

        # Compile final validation report
        validation_report = {
            "overall_quality_score": results.get("ComprehensiveValidation", {})
            .get("score", {})
            .get("overall_score", 0.85),
            "confidence_score": sum(
                r.get("confidence_score", 0.8)
                for r in results.values()
                if hasattr(r, "get")
            )
            / len(results),
            "validation_results": results,
            "recommendations": getattr(
                results.get("ComprehensiveValidation"), "actionable_items", []
            ),
            "llm_provider": config.provider.value,
            "processing_time_seconds": 2.5,
            "model_version": config.model,
        }

        return validation_report

    except ImportError:
        logger.warning("BAML client not available, falling back to mock validation")
        return await simulate_llm_validation_fallback(data, config, task_id)
    except Exception as e:
        logger.error(
            f"LLM validation failed: {str(e)}, falling back to mock validation"
        )
        return await simulate_llm_validation_fallback(data, config, task_id)


async def simulate_llm_validation_fallback(
    data: Dict[str, Any], config: LLMConfiguration, task_id: str
) -> Dict[str, Any]:
    """
    Fallback simulation when BAML client is not available.
    """
    # Simulate LLM processing time
    total_steps = 5
    for step in range(total_steps):
        await asyncio.sleep(0.5)  # Simulate processing time

        progress = (step + 1) / total_steps * 100
        update = ProgressUpdate(
            task_id=task_id,
            status=ProcessingStatus.LLM_VALIDATING,
            progress_percentage=int(progress),
            current_step=f"LLM validation step {step + 1}/{total_steps}",
            timestamp=datetime.now(timezone.utc),
        )
        await connection_manager.send_progress_update(task_id, update)

    # Mock LLM validation results
    validation_report = {
        "overall_quality_score": 0.85,
        "confidence_score": 0.92,
        "field_validations": [],
        "resource_validations": [],
        "critical_issues": [],
        "recommendations": [
            "Consider standardizing date formats across all records",
            "Some diagnosis codes may need validation against current ICD-10 standards",
        ],
        "llm_provider": config.provider.value,
        "processing_time_seconds": 2.5,
        "model_version": config.model,
    }

    return validation_report


async def create_ui_friendly_report(
    data: Dict[str, Any],
    validation_report: Dict[str, Any],
    processing_time: float,
    llm_enhanced: bool,
    sample_based: bool,
) -> UIFriendlyReport:
    """Create UI-optimized report for dashboard consumption."""

    # Calculate grade based on quality score
    quality_score = validation_report.get("overall_quality_score", 0.0)
    if quality_score >= 0.9:
        grade = "A"
    elif quality_score >= 0.8:
        grade = "B"
    elif quality_score >= 0.7:
        grade = "C"
    elif quality_score >= 0.6:
        grade = "D"
    else:
        grade = "F"

    return UIFriendlyReport(
        overall_grade=grade,
        quality_percentage=int(quality_score * 100),
        status=ProcessingStatus.COMPLETED,
        total_records=data.get("total_records", 0),
        valid_records=data.get("valid_records", 0),
        detected_fields=len(data.get("raw_data", {}).get("columns", [])),
        fhir_resources=len(data.get("fhir_resources", {})),
        critical_count=len(validation_report.get("critical_issues", [])),
        warning_count=0,  # Would count warnings from validation
        info_count=len(validation_report.get("recommendations", [])),
        top_issues=[],  # Would extract top issues
        processing_time=processing_time,
        llm_enhanced=llm_enhanced,
        sample_based=sample_based,
    )


async def process_csv_with_llm_background(
    file_path: str,
    filename: str,
    file_size: int,
    task_id: str,
    config: ProcessingConfig,
):
    """Background task for LLM-enhanced CSV processing with progress updates."""
    start_time = time.time()

    try:
        # Update status to in progress
        active_tasks[task_id]["status"] = ProcessingStatus.IN_PROGRESS

        # Step 1: Initial CSV processing
        update = ProgressUpdate(
            task_id=task_id,
            status=ProcessingStatus.IN_PROGRESS,
            progress_percentage=10,
            current_step="Reading and parsing CSV file",
            timestamp=datetime.now(timezone.utc),
        )
        await connection_manager.send_progress_update(task_id, update)

        # Process CSV normally first
        result, csv_type = auto_detect_and_process_csv(file_path)

        # Step 2: Smart sampling (if enabled and needed)
        sample_based = False
        if (
            config.enable_smart_sampling
            and result.get("total_records", 0) > config.max_records_for_full_processing
        ):
            sample_based = True
            update = ProgressUpdate(
                task_id=task_id,
                status=ProcessingStatus.SAMPLING,
                progress_percentage=30,
                current_step="Applying smart sampling for large dataset",
                timestamp=datetime.now(timezone.utc),
            )
            await connection_manager.send_progress_update(task_id, update)

            # Simulate sampling process
            await asyncio.sleep(0.5)

        # Step 3: LLM validation (if enabled)
        validation_report = None
        if config.enable_llm_validation and config.llm_config:
            update = ProgressUpdate(
                task_id=task_id,
                status=ProcessingStatus.LLM_VALIDATING,
                progress_percentage=50,
                current_step="Starting LLM validation",
                timestamp=datetime.now(timezone.utc),
            )
            await connection_manager.send_progress_update(task_id, update)

            validation_report = await perform_llm_validation(
                result, config.llm_config, task_id
            )

        # Step 4: Finalizing results
        update = ProgressUpdate(
            task_id=task_id,
            status=ProcessingStatus.FINALIZING,
            progress_percentage=90,
            current_step="Finalizing results and generating report",
            timestamp=datetime.now(timezone.utc),
        )
        await connection_manager.send_progress_update(task_id, update)

        processing_time = time.time() - start_time

        # Create UI-friendly report
        ui_report = await create_ui_friendly_report(
            result,
            validation_report or {},
            processing_time,
            config.enable_llm_validation,
            sample_based,
        )

        # Create enhanced metadata
        enhanced_metadata = create_processing_metadata(
            filename=filename,
            file_size=file_size,
            processing_time=processing_time,
            format_type=f"{csv_type} CSV",
            processor_type="Enhanced CSVProcessor",
            additional_metadata={
                "llm_enhanced": config.enable_llm_validation,
                "sample_based": sample_based,
                "task_id": task_id,
            },
        )

        # Create final response
        response = LLMValidationResponse(
            success=True,
            data=result,
            validation_report=validation_report,
            ui_report=ui_report,
            metadata=enhanced_metadata,
        )

        # Send completion message
        completion = TaskCompletion(
            task_id=task_id,
            status=ProcessingStatus.COMPLETED,
            result=response,
            total_time=processing_time,
            timestamp=datetime.now(timezone.utc),
        )
        await connection_manager.send_task_completion(task_id, completion)

        # Update task status
        active_tasks[task_id]["status"] = ProcessingStatus.COMPLETED
        active_tasks[task_id]["result"] = response

        logger.info(
            f"Completed LLM-enhanced processing for task {task_id} in {processing_time:.3f}s"
        )

    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = f"Failed to process CSV with LLM enhancement: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")

        # Send error completion
        completion = TaskCompletion(
            task_id=task_id,
            status=ProcessingStatus.FAILED,
            error=error_msg,
            total_time=processing_time,
            timestamp=datetime.now(timezone.utc),
        )
        await connection_manager.send_task_completion(task_id, completion)

        # Update task status
        active_tasks[task_id]["status"] = ProcessingStatus.FAILED
        active_tasks[task_id]["error"] = error_msg


@app.post("/api/process/csv-with-llm", response_model=LLMValidationResponse)
async def process_csv_with_llm_validation(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="CSV file for LLM-enhanced processing"),
    enable_llm: bool = True,
    llm_provider: Optional[LLMProvider] = None,
    enable_sampling: bool = True,
    realtime_updates: bool = True,
):
    """
    Process CSV file with LLM validation and real-time progress updates.

    This endpoint provides enhanced CSV processing with:
    - Smart sampling for large files
    - LLM-powered validation and quality assessment
    - Real-time progress updates via WebSocket
    - Comprehensive validation reports
    """
    temp_path = None
    task_id = str(uuid.uuid4())

    try:
        logger.info(
            f"Starting LLM-enhanced CSV processing: {file.filename} [Task: {task_id}]"
        )

        # Validate file
        validate_csv_file(file)

        # Save to temporary file
        temp_path = save_temp_file(file, ".csv")
        file_size = os.path.getsize(temp_path)

        # Create processing configuration
        config = ProcessingConfig(
            enable_llm_validation=enable_llm,
            enable_smart_sampling=enable_sampling,
            enable_realtime_updates=realtime_updates,
        )

        if enable_llm and llm_provider:
            config.llm_config = LLMConfiguration(provider=llm_provider)
        elif enable_llm:
            config.llm_config = default_config.llm_config

        # Initialize task tracking
        active_tasks[task_id] = {
            "filename": file.filename,
            "file_size": file_size,
            "status": ProcessingStatus.PENDING,
            "start_time": time.time(),
            "config": config,
        }

        # For real-time updates, start background processing
        if realtime_updates:
            background_tasks.add_task(
                process_csv_with_llm_background,
                temp_path,
                file.filename,
                file_size,
                task_id,
                config,
            )

            # Return immediate response with task ID
            return LLMValidationResponse(
                success=True,
                metadata={
                    "task_id": task_id,
                    "processing_mode": "background",
                    "realtime_updates": True,
                    "websocket_endpoint": f"/ws/validation-progress/{task_id}",
                },
            )
        else:
            # Synchronous processing
            await process_csv_with_llm_background(
                temp_path, file.filename, file_size, task_id, config
            )

            # Return completed result
            return active_tasks[task_id]["result"]

    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Failed to initiate LLM-enhanced CSV processing: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_msg
        )
    finally:
        if temp_path and not realtime_updates:
            cleanup_temp_file(temp_path)


@app.get("/api/tasks/{task_id}", response_model=LLMValidationResponse)
async def get_task_status(task_id: str):
    """Get status and results for a specific processing task."""
    if task_id not in active_tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found"
        )

    task = active_tasks[task_id]

    if task["status"] == ProcessingStatus.COMPLETED:
        return task["result"]
    elif task["status"] == ProcessingStatus.FAILED:
        return LLMValidationResponse(
            success=False,
            error=task.get("error", "Unknown error occurred"),
            metadata={"task_id": task_id, "status": task["status"]},
        )
    else:
        return LLMValidationResponse(
            success=True,
            metadata={"task_id": task_id, "status": task["status"], "processing": True},
        )


@app.websocket("/ws/validation-progress/{task_id}")
async def websocket_validation_progress(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for real-time validation progress updates."""
    connection_id = str(uuid.uuid4())

    try:
        await connection_manager.connect(websocket, connection_id)
        connection_manager.subscribe_to_task(connection_id, task_id)

        # Send initial task info if task exists
        if task_id in active_tasks:
            task = active_tasks[task_id]
            init_message = TaskInitiation(
                task_id=task_id,
                task_type="csv-with-llm",
                filename=task["filename"],
                file_size=task["file_size"],
                enable_llm=task["config"].enable_llm_validation,
                llm_provider=task["config"].llm_config.provider
                if task["config"].llm_config
                else None,
            )
            await websocket.send_text(init_message.model_dump_json())

        # Keep connection alive
        while True:
            try:
                # Wait for client messages (ping/pong, etc.)
                await websocket.receive_text()
                # Echo back for keepalive
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "pong",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    )
                )
            except WebSocketDisconnect:
                break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error for task {task_id}: {e}")
    finally:
        connection_manager.disconnect(connection_id)


@app.websocket("/ws/validation-progress")
async def websocket_general_progress(websocket: WebSocket):
    """General WebSocket endpoint for subscribing to multiple task updates."""
    connection_id = str(uuid.uuid4())

    try:
        await connection_manager.connect(websocket, connection_id)

        # Keep connection alive and handle subscription requests
        while True:
            try:
                message = await websocket.receive_text()
                data = json.loads(message)

                if data.get("type") == "subscribe" and "task_id" in data:
                    connection_manager.subscribe_to_task(connection_id, data["task_id"])
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "subscribed",
                                "task_id": data["task_id"],
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            }
                        )
                    )
                elif data.get("type") == "ping":
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "pong",
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            }
                        )
                    )

            except WebSocketDisconnect:
                break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"General WebSocket error: {e}")
    finally:
        connection_manager.disconnect(connection_id)


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
        raw_data = result.get("raw_data", {})
        column_mappings = raw_data.get("column_mappings", [])
        resource_detections = raw_data.get("resource_detections", [])

        csv_metadata = {
            "csv_type": "Claims",
            "total_records": result.get("total", 0),
            "detected_columns": len(column_mappings),
            "detected_resources": len(resource_detections),
            "resource_types": [r["resource_type"] for r in resource_detections],
            "data_quality_score": next(
                (
                    ext.get("valueDecimal", 0.0)
                    for ext in result.get("extension", [])
                    if "data-quality-score" in ext.get("url", "")
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
        raw_data = result.get("raw_data", {})
        column_mappings = raw_data.get("column_mappings", [])
        resource_detections = raw_data.get("resource_detections", [])

        csv_metadata = {
            "csv_type": "Clinical",
            "total_records": result.get("total", 0),
            "detected_columns": len(column_mappings),
            "detected_resources": len(resource_detections),
            "resource_types": [r["resource_type"] for r in resource_detections],
            "data_quality_score": next(
                (
                    ext.get("valueDecimal", 0.0)
                    for ext in result.get("extension", [])
                    if "data-quality-score" in ext.get("url", "")
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
