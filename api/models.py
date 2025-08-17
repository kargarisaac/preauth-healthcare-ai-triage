"""
Simplified models for patient-centric workflow API.

Essential Pydantic models for patient workflow endpoints.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum


# Core patient workflow models
class PatientInfo(BaseModel):
    """Complete information about a patient in the system."""

    # Basic patient metadata
    patient_id: str = Field(..., description="Patient identifier")
    folder_name: str = Field(..., description="Patient folder name")
    folder_path: str = Field(..., description="Path to patient folder")
    has_profile: bool = Field(..., description="Whether patient has profile data")
    xml_files: int = Field(..., ge=0, description="Number of XML files available")
    processed_json_files: int = Field(..., ge=0, description="Number of processed JSON files")
    
    # Complete patient profile information from profile.json
    full_name: Optional[str] = Field(None, description="Patient full name")
    gender: Optional[str] = Field(None, description="Patient gender")
    birth_year: Optional[int] = Field(None, description="Patient birth year")
    nationality: Optional[str] = Field(None, description="Patient nationality")
    marital_status: Optional[str] = Field(None, description="Patient marital status")
    employment_sector: Optional[str] = Field(None, description="Patient employment sector")
    insurance_plan: Optional[str] = Field(None, description="Insurance plan name")
    coverage_tier: Optional[str] = Field(None, description="Insurance coverage tier")
    smoker: Optional[str] = Field(None, description="Patient smoking status (Y/N)")
    baseline_BMI: Optional[float] = Field(None, description="Patient baseline BMI")
    baseline_BP_systolic: Optional[int] = Field(None, description="Patient baseline systolic blood pressure")
    family_history_diabetes: Optional[str] = Field(None, description="Family history of diabetes (Y/N)")
    family_history_CAD: Optional[str] = Field(None, description="Family history of coronary artery disease (Y/N)")


class XMLProcessResponse(BaseModel):
    """Response model for XML processing."""

    success: bool = Field(..., description="Whether processing was successful")
    patient_id: Optional[str] = Field(None, description="Extracted patient ID")
    data: Optional[Dict[str, Any]] = Field(None, description="Processed JSON data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Processing metadata")
    error: Optional[str] = Field(None, description="Error message if processing failed")


class AnalysisResponse(BaseModel):
    """Response model for Claude analysis."""

    success: bool = Field(..., description="Whether analysis was successful")
    patient_id: str = Field(..., description="Patient identifier")
    analysis: Optional[Dict[str, Any]] = Field(None, description="Claude analysis results")
    recommendations: List[str] = Field(default_factory=list, description="Analysis recommendations")
    confidence_score: Optional[float] = Field(None, description="Analysis confidence score")
    error: Optional[str] = Field(None, description="Error message if analysis failed")


class SystemStatus(BaseModel):
    """System health and status information."""

    status: str = Field(..., description="Overall system status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Status timestamp")
    version: str = Field(..., description="API version")
    xml_processing_available: bool = Field(..., description="XML processing service status")
    claude_analysis_available: bool = Field(..., description="Claude analysis service status")
    patient_index_size: int = Field(..., ge=0, description="Number of patients indexed")
    supported_sources: List[str] = Field(default_factory=list, description="Supported XML sources")


class DashboardData(BaseModel):
    """Patient dashboard data."""

    patient_info: PatientInfo = Field(..., description="Patient information")
    recent_files: List[Dict[str, Any]] = Field(default_factory=list, description="Recent processed files")
    analysis_history: List[Dict[str, Any]] = Field(default_factory=list, description="Analysis history")
    summary_stats: Dict[str, Any] = Field(default_factory=dict, description="Summary statistics")


# Error response model
class UnifiedProcessResponse(BaseModel):
    """Response model for unified XML processing workflow."""
    
    success: bool = Field(..., description="Whether the complete workflow was successful")
    patient_id: str = Field(..., description="Patient identifier")
    
    # File storage information
    file_storage: Dict[str, Any] = Field(..., description="Information about stored files")
    
    # XML processing results
    xml_processing: Dict[str, Any] = Field(..., description="XML processing results")
    
    # Claude analysis results (optional)
    claude_analysis: Optional[Dict[str, Any]] = Field(None, description="Claude analysis results if enabled")
    
    # Patient data summary
    patient_data: Dict[str, Any] = Field(..., description="Patient folder and file statistics")
    
    # Workflow metadata
    workflow_metadata: Dict[str, Any] = Field(..., description="Workflow execution metadata")
    
    # Error information
    error: Optional[str] = Field(None, description="Error message if workflow failed")


class ErrorResponse(BaseModel):
    """Standard error response model."""

    success: bool = Field(False, description="Always false for error responses")
    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


# Request Management Models
class RequestStatus(str, Enum):
    """Pre-authorization request status enumeration."""
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    DECIDED = "decided"
    COMMUNICATED = "communicated"
    CANCELLED = "cancelled"


class RequestPriority(str, Enum):
    """Request priority levels for medical review."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class DecisionOutcome(str, Enum):
    """Final decision outcomes for requests."""
    APPROVED = "approved"
    DENIED = "denied"
    PARTIAL = "partial"
    REQUIRES_INFO = "requires_info"


class PreAuthRequest(BaseModel):
    """Complete pre-authorization request model."""
    
    # Primary identifiers
    request_id: str = Field(..., description="Unique request identifier")
    patient_id: str = Field(..., description="Patient identifier")
    
    # Request metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Request creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    submitted_by: Optional[str] = Field(None, description="Provider/user who submitted request")
    
    # Request details
    xml_filename: str = Field(..., description="Original XML filename")
    xml_format: str = Field(..., description="XML format (eclaim/shafafiya)")
    xml_content: Optional[str] = Field(None, description="Original XML content")
    
    # Status and workflow
    status: RequestStatus = Field(default=RequestStatus.PENDING, description="Current request status")
    priority: RequestPriority = Field(default=RequestPriority.MEDIUM, description="Request priority")
    assigned_to: Optional[str] = Field(None, description="Medical director/reviewer assigned")
    
    # Pipeline results (stored as JSON)
    intake_data: Optional[Dict[str, Any]] = Field(None, description="Pipeline intake results")
    clinical_summary: Optional[Dict[str, Any]] = Field(None, description="Clinical summary results")
    evidence_data: Optional[List[Dict[str, Any]]] = Field(None, description="Evidence retrieval results")
    checklist_data: Optional[Dict[str, Any]] = Field(None, description="Policy checklist results")
    decision_data: Optional[Dict[str, Any]] = Field(None, description="Initial pipeline decision")
    dossier_data: Optional[Dict[str, Any]] = Field(None, description="Generated dossier content")
    
    # Performance metrics
    processing_time_seconds: Optional[float] = Field(None, description="Total processing time")
    cost_usd: Optional[float] = Field(None, description="Processing cost")
    
    # Final decision (medical director review)
    final_decision: Optional[DecisionOutcome] = Field(None, description="Final medical director decision")
    decision_rationale: Optional[str] = Field(None, description="Decision reasoning")
    decision_conditions: Optional[List[str]] = Field(None, description="Approval conditions")
    decided_by: Optional[str] = Field(None, description="Medical director who made decision")
    decided_at: Optional[datetime] = Field(None, description="Decision timestamp")
    
    # Communication tracking
    communicated_at: Optional[datetime] = Field(None, description="When decision was communicated")
    communication_method: Optional[str] = Field(None, description="How decision was communicated")
    
    # Audit trail
    audit_trail: Optional[Dict[str, Any]] = Field(None, description="Complete audit trail")


class PatientHistory(BaseModel):
    """Patient medical history aggregated across requests."""
    
    patient_id: str = Field(..., description="Patient identifier")
    total_requests: int = Field(..., description="Total number of requests")
    
    # Request timeline
    first_request_date: datetime = Field(..., description="Date of first request")
    last_request_date: datetime = Field(..., description="Date of most recent request")
    
    # Decision patterns
    approved_count: int = Field(default=0, description="Number of approved requests")
    denied_count: int = Field(default=0, description="Number of denied requests")
    pending_count: int = Field(default=0, description="Number of pending requests")
    
    # Clinical progression
    conditions: List[str] = Field(default_factory=list, description="Unique conditions across requests")
    procedures: List[str] = Field(default_factory=list, description="Unique procedures requested")
    medications: List[str] = Field(default_factory=list, description="Unique medications involved")
    
    # Recent activity
    recent_requests: List[Dict[str, Any]] = Field(default_factory=list, description="Recent request summaries")
    
    # Risk factors
    high_cost_requests: int = Field(default=0, description="Number of high-cost requests")
    emergency_requests: int = Field(default=0, description="Number of emergency requests")
    
    # Patient profile integration
    patient_profile: Optional[Dict[str, Any]] = Field(None, description="Patient profile data")


class RequestInboxFilter(BaseModel):
    """Filters for request inbox queries."""
    
    status: Optional[List[RequestStatus]] = Field(None, description="Filter by status")
    priority: Optional[List[RequestPriority]] = Field(None, description="Filter by priority")
    assigned_to: Optional[str] = Field(None, description="Filter by assigned reviewer")
    date_from: Optional[datetime] = Field(None, description="Filter from date")
    date_to: Optional[datetime] = Field(None, description="Filter to date")
    patient_id: Optional[str] = Field(None, description="Filter by patient")
    limit: int = Field(default=50, description="Maximum results to return")
    offset: int = Field(default=0, description="Results offset for pagination")


class DecisionSubmission(BaseModel):
    """Medical director decision submission."""
    
    decision: DecisionOutcome = Field(..., description="Final decision")
    rationale: str = Field(..., description="Decision reasoning")
    conditions: Optional[List[str]] = Field(None, description="Approval conditions if applicable")
    requires_followup: bool = Field(default=False, description="Whether follow-up is needed")
    followup_date: Optional[datetime] = Field(None, description="Scheduled follow-up date")
    notes: Optional[str] = Field(None, description="Additional notes")


class RequestAssignment(BaseModel):
    """Request assignment to medical director."""
    
    assigned_to: str = Field(..., description="Medical director identifier")
    priority: Optional[RequestPriority] = Field(None, description="Update priority if needed")
    notes: Optional[str] = Field(None, description="Assignment notes")


class RequestInboxResponse(BaseModel):
    """Response model for request inbox."""
    
    success: bool = Field(..., description="Whether request was successful")
    total_count: int = Field(..., description="Total number of matching requests")
    requests: List[PreAuthRequest] = Field(..., description="List of requests")
    filters_applied: RequestInboxFilter = Field(..., description="Filters that were applied")
    
    # Summary statistics
    summary: Dict[str, Any] = Field(default_factory=dict, description="Inbox summary statistics")


class PatientTimelineResponse(BaseModel):
    """Response model for patient history timeline."""
    
    success: bool = Field(..., description="Whether request was successful")
    patient_id: str = Field(..., description="Patient identifier")
    history: PatientHistory = Field(..., description="Patient history data")
    timeline: List[Dict[str, Any]] = Field(..., description="Chronological timeline of events")
    
    # Analytics
    trends: Dict[str, Any] = Field(default_factory=dict, description="Patient trend analysis")
    risk_assessment: Dict[str, Any] = Field(default_factory=dict, description="Current risk assessment")