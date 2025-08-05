"""
Simplified models for patient-centric workflow API.

Essential Pydantic models for patient workflow endpoints.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


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