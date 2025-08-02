"""
Response models for LLM validation and enhanced CSV processing API.

Production-ready Pydantic models for structured API responses, WebSocket
communication, and comprehensive error handling.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ProcessingStatus(str, Enum):
    """Status enumeration for processing tasks."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SAMPLING = "sampling"
    LLM_VALIDATING = "llm_validating"
    FINALIZING = "finalizing"


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LLMProvider(str, Enum):
    """Supported LLM providers for validation."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"


# Core response models for existing endpoints
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


# LLM validation models
class ValidationIssue(BaseModel):
    """Individual validation issue detected by LLM."""

    severity: ValidationSeverity = Field(..., description="Issue severity level")
    category: str = Field(
        ..., description="Issue category (e.g., 'data_quality', 'mapping')"
    )
    field: Optional[str] = Field(None, description="Specific field with issue")
    message: str = Field(..., description="Human-readable issue description")
    suggestion: Optional[str] = Field(None, description="Suggested fix or improvement")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="LLM confidence in this finding"
    )
    affected_records: Optional[List[int]] = Field(
        None, description="Record indices affected"
    )


class FieldValidation(BaseModel):
    """Validation results for a specific field."""

    field_name: str = Field(..., description="Name of the validated field")
    mapped_to: Optional[str] = Field(None, description="FHIR resource field mapping")
    data_type: str = Field(..., description="Detected data type")
    completeness_rate: float = Field(
        ..., ge=0.0, le=1.0, description="Percentage of non-null values"
    )
    quality_score: float = Field(
        ..., ge=0.0, le=1.0, description="Overall field quality score"
    )
    issues: List[ValidationIssue] = Field(
        default_factory=list, description="Field-specific issues"
    )
    sample_values: List[str] = Field(
        default_factory=list, description="Sample values for reference"
    )


class ResourceValidation(BaseModel):
    """Validation results for a FHIR resource type."""

    resource_type: str = Field(
        ..., description="FHIR resource type (e.g., 'Claim', 'Observation')"
    )
    total_instances: int = Field(..., ge=0, description="Number of resources created")
    valid_instances: int = Field(..., ge=0, description="Number of valid resources")
    completeness_score: float = Field(
        ..., ge=0.0, le=1.0, description="Resource completeness"
    )
    compliance_score: float = Field(
        ..., ge=0.0, le=1.0, description="FHIR compliance score"
    )
    issues: List[ValidationIssue] = Field(
        default_factory=list, description="Resource-specific issues"
    )


class LLMValidationReport(BaseModel):
    """Comprehensive LLM validation report."""

    overall_quality_score: float = Field(
        ..., ge=0.0, le=1.0, description="Overall data quality score"
    )
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="LLM confidence in analysis"
    )

    # Field-level validation
    field_validations: List[FieldValidation] = Field(
        default_factory=list, description="Per-field validation results"
    )

    # Resource-level validation
    resource_validations: List[ResourceValidation] = Field(
        default_factory=list, description="Per-resource validation results"
    )

    # Overall issues and recommendations
    critical_issues: List[ValidationIssue] = Field(
        default_factory=list, description="Critical issues requiring attention"
    )
    recommendations: List[str] = Field(
        default_factory=list, description="General improvement recommendations"
    )

    # Processing metadata
    llm_provider: LLMProvider = Field(
        ..., description="LLM provider used for validation"
    )
    processing_time_seconds: float = Field(
        ..., ge=0.0, description="LLM processing time"
    )
    tokens_used: Optional[int] = Field(
        None, description="Tokens consumed during validation"
    )
    model_version: str = Field(..., description="Specific model version used")


class SamplingMetadata(BaseModel):
    """Metadata about smart sampling for large files."""

    total_records: int = Field(..., ge=0, description="Total records in original file")
    sampled_records: int = Field(..., ge=0, description="Number of records sampled")
    sampling_strategy: str = Field(..., description="Sampling strategy used")
    sampling_ratio: float = Field(
        ..., ge=0.0, le=1.0, description="Ratio of sampled to total records"
    )
    representative_score: float = Field(
        ..., ge=0.0, le=1.0, description="How representative the sample is"
    )
    sample_indices: List[int] = Field(
        default_factory=list, description="Indices of sampled records"
    )


class UIFriendlyReport(BaseModel):
    """UI-optimized validation report for dashboard consumption."""

    # High-level summary
    overall_grade: str = Field(..., description="Letter grade (A, B, C, D, F)")
    quality_percentage: int = Field(
        ..., ge=0, le=100, description="Quality as percentage"
    )
    status: ProcessingStatus = Field(..., description="Current processing status")

    # Key metrics for dashboard cards
    total_records: int = Field(..., ge=0, description="Total records processed")
    valid_records: int = Field(..., ge=0, description="Records passing validation")
    detected_fields: int = Field(..., ge=0, description="Fields detected and mapped")
    fhir_resources: int = Field(..., ge=0, description="FHIR resources created")

    # Issues summary
    critical_count: int = Field(..., ge=0, description="Number of critical issues")
    warning_count: int = Field(..., ge=0, description="Number of warnings")
    info_count: int = Field(..., ge=0, description="Number of info messages")

    # Top issues for quick review
    top_issues: List[ValidationIssue] = Field(
        default_factory=list, max_items=5, description="Top 5 most important issues"
    )

    # Processing info
    processing_time: float = Field(
        ..., ge=0.0, description="Total processing time in seconds"
    )
    llm_enhanced: bool = Field(..., description="Whether LLM validation was used")
    sample_based: bool = Field(
        ..., description="Whether analysis was based on sampling"
    )

    # Detailed reports (optional for expansion)
    detailed_validation: Optional[LLMValidationReport] = Field(
        None, description="Full validation report"
    )
    sampling_info: Optional[SamplingMetadata] = Field(
        None, description="Sampling metadata if applicable"
    )


class LLMValidationResponse(BaseModel):
    """Response model for LLM-enhanced CSV processing."""

    success: bool = Field(..., description="Whether processing was successful")

    # Core processing data
    data: Optional[Dict[str, Any]] = Field(
        None, description="Processed canonical JSON data"
    )

    # LLM validation results
    validation_report: Optional[LLMValidationReport] = Field(
        None, description="Detailed LLM validation report"
    )

    # UI-friendly summary
    ui_report: Optional[UIFriendlyReport] = Field(
        None, description="UI-optimized validation summary"
    )

    # Standard metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Processing metadata"
    )

    # Error handling
    error: Optional[str] = Field(None, description="Error message if processing failed")
    warnings: List[str] = Field(default_factory=list, description="Non-fatal warnings")


# WebSocket progress models
class ProgressUpdate(BaseModel):
    """Real-time progress update for WebSocket communication."""

    task_id: str = Field(..., description="Unique task identifier")
    status: ProcessingStatus = Field(..., description="Current task status")
    progress_percentage: int = Field(
        ..., ge=0, le=100, description="Completion percentage"
    )
    current_step: str = Field(..., description="Description of current step")

    # Optional detailed information
    records_processed: Optional[int] = Field(
        None, description="Records processed so far"
    )
    total_records: Optional[int] = Field(None, description="Total records to process")
    estimated_completion: Optional[datetime] = Field(
        None, description="ETA for completion"
    )

    # Status-specific data
    sampling_progress: Optional[SamplingMetadata] = Field(
        None, description="Sampling progress"
    )
    llm_progress: Optional[Dict[str, Any]] = Field(
        None, description="LLM validation progress"
    )

    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Update timestamp"
    )


class TaskInitiation(BaseModel):
    """WebSocket message for task initiation."""

    task_id: str = Field(..., description="Unique task identifier")
    task_type: str = Field(..., description="Type of task (csv-with-llm, etc.)")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., ge=0, description="File size in bytes")
    enable_llm: bool = Field(..., description="Whether LLM validation is enabled")
    llm_provider: Optional[LLMProvider] = Field(None, description="LLM provider to use")


class TaskCompletion(BaseModel):
    """WebSocket message for task completion."""

    task_id: str = Field(..., description="Unique task identifier")
    status: ProcessingStatus = Field(..., description="Final task status")
    result: Optional[LLMValidationResponse] = Field(
        None, description="Processing results"
    )
    error: Optional[str] = Field(None, description="Error message if failed")
    total_time: float = Field(..., ge=0.0, description="Total processing time")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Completion timestamp"
    )


# Error response models
class ValidationError(BaseModel):
    """Structured validation error for API responses."""

    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Validation error message")
    invalid_value: Any = Field(None, description="The invalid value provided")


class ErrorResponse(BaseModel):
    """Enhanced error response model."""

    success: bool = Field(False, description="Always false for error responses")
    error: str = Field(..., description="High-level error message")
    error_code: Optional[str] = Field(None, description="Machine-readable error code")
    details: Optional[str] = Field(None, description="Detailed error information")
    validation_errors: List[ValidationError] = Field(
        default_factory=list, description="Field-level validation errors"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Error timestamp"
    )
    request_id: Optional[str] = Field(None, description="Request ID for tracing")


# Health and configuration models
class HealthResponse(BaseModel):
    """Enhanced health check response model."""

    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Current timestamp"
    )
    version: str = Field(..., description="API version")

    # LLM service health
    llm_services: Dict[str, bool] = Field(
        default_factory=dict, description="LLM provider availability"
    )

    # Performance metrics
    active_tasks: int = Field(
        ..., ge=0, description="Currently active processing tasks"
    )
    queue_size: int = Field(
        ..., ge=0, description="Queued tasks waiting for processing"
    )
    avg_response_time: float = Field(
        ..., ge=0.0, description="Average response time in seconds"
    )


class LLMConfiguration(BaseModel):
    """Configuration model for LLM validation settings."""

    provider: LLMProvider = Field(..., description="LLM provider to use")
    model: str = Field(..., description="Specific model name")
    max_tokens: int = Field(
        4000, ge=100, le=32000, description="Maximum tokens per request"
    )
    temperature: float = Field(0.1, ge=0.0, le=2.0, description="Model temperature")
    timeout_seconds: int = Field(30, ge=5, le=300, description="Request timeout")
    enable_parallel: bool = Field(True, description="Enable parallel processing")
    max_parallel_requests: int = Field(
        3, ge=1, le=10, description="Max concurrent LLM requests"
    )


# Configuration and settings
class ProcessingConfig(BaseModel):
    """Configuration for enhanced CSV processing."""

    enable_llm_validation: bool = Field(True, description="Enable LLM validation")
    llm_config: Optional[LLMConfiguration] = Field(
        None, description="LLM configuration"
    )

    # Sampling configuration
    enable_smart_sampling: bool = Field(
        True, description="Enable smart sampling for large files"
    )
    max_records_for_full_processing: int = Field(
        1000, ge=100, description="Threshold for smart sampling"
    )
    min_sample_size: int = Field(100, ge=50, description="Minimum sample size")
    max_sample_size: int = Field(500, ge=100, description="Maximum sample size")

    # Performance settings
    enable_parallel_processing: bool = Field(
        True, description="Enable parallel processing"
    )
    max_concurrent_tasks: int = Field(
        5, ge=1, le=20, description="Max concurrent processing tasks"
    )

    # WebSocket settings
    enable_realtime_updates: bool = Field(
        True, description="Enable WebSocket progress updates"
    )
    update_interval_seconds: float = Field(
        1.0, ge=0.1, le=10.0, description="Progress update frequency"
    )


# Sample file models
class SampleFile(BaseModel):
    """Model for sample file information."""

    name: str = Field(..., description="Sample file name")
    format: str = Field(..., description="File format description")
    size: int = Field(..., ge=0, description="File size in bytes")
    path: str = Field(..., description="Relative path to sample file")
    file_type: str = Field(..., description="File extension/type")
