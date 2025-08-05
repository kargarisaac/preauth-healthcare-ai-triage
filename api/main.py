"""
Streamlined FastAPI backend for patient-centric XML processing workflow.

Provides unified XML processing endpoint with integrated upload, processing, and analysis capabilities.
Key endpoints: patient listing, unified XML processing, analysis, and dashboard.
"""

import json
import os
import sys
import time
import traceback
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, status, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import services
from api.services.patient_lookup_service import get_patient_lookup_service
from api.services.xml_processing_service import get_xml_processing_service
from api.services.claude_analysis_service import get_claude_analysis_service
from api.services.workflow_orchestrator import get_workflow_orchestrator

# Import models
from api.models import (
    PatientInfo,
    AnalysisResponse,
    SystemStatus,
    DashboardData,
    UnifiedProcessResponse,
    ErrorResponse
)



@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    # Startup
    logger.info("Starting Nazmito Patient Processing API...")
    
    # Create logs directory
    os.makedirs("api/logs", exist_ok=True)
    
    logger.info("API Version: 2.0.0")
    logger.info("Supported formats: XML (eClaimLink, Shafafiya)")
    logger.info("Single unified XML processing endpoint ready")
    logger.info("Patient-centric workflow ready")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Nazmito Patient Processing API...")


# Initialize FastAPI app
app = FastAPI(
    title="Nazmito Patient Processing API",
    description="Streamlined API for patient-centric XML processing with unified upload and analysis workflow",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Initialize services
patient_lookup_service = get_patient_lookup_service()
xml_processing_service = get_xml_processing_service()
claude_analysis_service = get_claude_analysis_service()  
workflow_orchestrator = get_workflow_orchestrator()

# Configure logging
logger.add("api/logs/fastapi.log", rotation="10 MB", retention="30 days")






# API Endpoints

@app.get("/api/health", response_model=SystemStatus)
async def health_check():
    """System health check endpoint."""
    try:
        # Get service statuses
        xml_status = xml_processing_service.get_processing_stats()
        claude_status = claude_analysis_service.get_analysis_status()
        
        return SystemStatus(
            status="healthy",
            timestamp=datetime.now(timezone.utc),
            version="2.0.0",
            xml_processing_available=xml_status.get("service_status") == "ready",
            claude_analysis_available=claude_status.get("claude_available", False),
            patient_index_size=claude_status.get("patient_index_size", 0),
            supported_sources=["eclaim", "shafafiya"]
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return SystemStatus(
            status="degraded",
            timestamp=datetime.now(timezone.utc),
            version="2.0.0",
            xml_processing_available=False,
            claude_analysis_available=False,
            patient_index_size=0,
            supported_sources=[]
        )


@app.get("/api/patients", response_model=List[PatientInfo])
async def list_patients():
    """List all patients with complete profile information."""
    try:
        patients = []
        all_patients = patient_lookup_service.get_all_patients()
        
        for patient_id, folder_name in all_patients.items():
            # Get folder validation data
            validation = patient_lookup_service.validate_patient_folder_structure(patient_id)
            
            # Get complete patient profile
            profile = patient_lookup_service.get_patient_profile(patient_id)
            
            # Create patient info with all available data
            patient_info_data = {
                "patient_id": patient_id,
                "folder_name": folder_name,
                "folder_path": validation.get("folder_path", ""),
                "has_profile": validation.get("has_profile", False),
                "xml_files": validation.get("xml_files", 0),
                "processed_json_files": validation.get("processed_json_files", 0)
            }
            
            # Add profile data if available
            if profile:
                patient_info_data.update({
                    "full_name": profile.get("full_name"),
                    "gender": profile.get("gender"),
                    "birth_year": profile.get("birth_year"),
                    "nationality": profile.get("nationality"),
                    "marital_status": profile.get("marital_status"),
                    "employment_sector": profile.get("employment_sector"),
                    "insurance_plan": profile.get("insurance_plan"),
                    "coverage_tier": profile.get("coverage_tier"),
                    "smoker": profile.get("smoker"),
                    "baseline_BMI": profile.get("baseline_BMI"),
                    "baseline_BP_systolic": profile.get("baseline_BP_systolic"),
                    "family_history_diabetes": profile.get("family_history_diabetes"),
                    "family_history_CAD": profile.get("family_history_CAD")
                })
            
            patient_info = PatientInfo(**patient_info_data)
            patients.append(patient_info)
        
        logger.info(f"Retrieved complete profile data for {len(patients)} patients")
        return patients
        
    except Exception as e:
        logger.error(f"Failed to list patients: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list patients: {str(e)}"
        )




@app.post("/api/process-xml/{patient_id}", response_model=UnifiedProcessResponse)
async def process_xml_for_patient(
    patient_id: str,
    file: UploadFile = File(..., description="XML file to process"),
    source: str = Form(..., description="XML source type: 'eclaim' or 'shafafiya'"),
    enable_analysis: bool = Form(True, description="Whether to run Claude analysis"),
    cost_limit_usd: float = Form(1.0, description="Cost limit for Claude analysis")
):
    """
    Primary XML processing endpoint - upload and process XML files for patients.
    
    This is the main endpoint for XML processing workflow that:
    - Accepts XML file upload via multipart/form-data
    - Takes patient_id as path parameter 
    - Validates and processes XML immediately
    - Stores files in patient-specific directories (raw + processed)
    - Optionally runs Claude analysis with cost controls
    - Returns comprehensive workflow results
    
    Replaces the previous separate upload/process endpoints for better efficiency.
    """
    start_time = time.time()
    
    try:
        logger.info(f"Starting unified XML processing for patient {patient_id}: {file.filename}")
        
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="No filename provided"
            )

        # Check file extension
        file_extension = Path(file.filename).suffix.lower()
        if file_extension != ".xml":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Only XML files are allowed. Got: {file_extension}",
            )
        
        # Validate source parameter
        if source not in ['eclaim', 'shafafiya']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid source '{source}'. Must be 'eclaim' or 'shafafiya'"
            )
        
        # Validate patient_id format (basic validation)
        if not patient_id or len(patient_id.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Patient ID cannot be empty"
            )
        
        patient_id = patient_id.strip()
        logger.info(f"Processing XML with source: {source}, enable_analysis: {enable_analysis}")
        
        # Use the patient-centric workflow from WorkflowOrchestrator
        # Note: include_history=True is used by the workflow internally during Claude analysis
        workflow_result = await workflow_orchestrator.patient_centric_workflow(
            patient_id=patient_id,
            xml_file=file,
            auto_detect_source=False,  # Use explicit source
            source=source,
            enable_analysis=enable_analysis,
            cost_limit_usd=cost_limit_usd,
            progress_callback=None  # Could add progress tracking later
        )
        
        # Calculate total processing time
        processing_time = time.time() - start_time
        
        if not workflow_result["success"]:
            raise ValueError(workflow_result.get("error", "Workflow processing failed"))
        
        # Extract data from workflow result
        file_storage = workflow_result.get("file_storage", {})
        xml_processing = workflow_result.get("xml_processing", {})
        claude_analysis = workflow_result.get("claude_analysis")
        patient_data = workflow_result.get("patient_data", {})
        workflow_metadata = workflow_result.get("workflow_metadata", {})
        
        # Add API-specific metadata
        workflow_metadata.update({
            "api_processing_time_seconds": round(processing_time, 3),
            "api_version": "2.0.0",
            "endpoint": "/api/process-xml/{patient_id}",
            "unified_workflow": True
        })
        
        logger.info(
            f"Successfully completed unified XML processing for patient {patient_id}: "
            f"{file.filename} in {processing_time:.3f}s, analysis: {enable_analysis}"
        )
        
        return UnifiedProcessResponse(
            success=True,
            patient_id=patient_id,
            file_storage=file_storage,
            xml_processing=xml_processing,
            claude_analysis=claude_analysis,
            patient_data=patient_data,
            workflow_metadata=workflow_metadata,
            error=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = f"Failed to process XML for patient {patient_id}: {str(e)}"
        logger.error(f"{error_msg}\\n{traceback.format_exc()}")
        
        # Return error response following the same model structure
        return UnifiedProcessResponse(
            success=False,
            patient_id=patient_id,
            file_storage={},
            xml_processing={},
            claude_analysis=None,
            patient_data={},
            workflow_metadata={
                "api_processing_time_seconds": round(processing_time, 3),
                "api_version": "2.0.0",
                "endpoint": "/api/process-xml/{patient_id}",
                "unified_workflow": True,
                "error_occurred": True
            },
            error=error_msg
        )


@app.post("/api/analyze/{patient_id}", response_model=AnalysisResponse)
async def analyze_patient(
    patient_id: str,
    cost_limit_usd: float = 1.0,
    include_history: bool = True
):
    """Run Claude analysis for specific patient using multi-agent analysis."""
    try:
        logger.info(f"Starting Claude analysis for patient {patient_id}")
        
        # Validate patient exists and has processed data
        patient_data_availability = patient_lookup_service.check_patient_data_availability(patient_id)
        if not patient_data_availability["patient_exists"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient {patient_id} not found"
            )
        
        if not patient_data_availability["processed_data_available"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No processed data found for patient {patient_id}. Please process XML files first."
            )
        
        # Check if Claude analysis is available
        if not claude_analysis_service.claude_available:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Claude analysis service is not available"
            )
        
        # Run Claude analysis using existing patient workflow
        result = await workflow_orchestrator.analyze_existing_patient(
            patient_id=patient_id,
            cost_limit_usd=cost_limit_usd,
            include_history=include_history
        )
        
        if not result["success"]:
            raise ValueError(result.get("error", "Analysis failed"))
        
        claude_analysis = result["claude_analysis"]
        
        logger.info(f"Claude analysis completed for patient {patient_id}, cost: ${claude_analysis.get('cost_usd', 0):.3f}")
        
        # Extract recommendations from agent results if available
        recommendations = []
        agent_results = claude_analysis.get("agent_results", {})
        if "recommendation_agent" in agent_results:
            rec_data = agent_results["recommendation_agent"]
            if isinstance(rec_data, dict) and "recommendations" in rec_data:
                recommendations = rec_data["recommendations"]
        
        # Extract confidence score
        confidence_score = None
        if "medical_reviewer_agent" in agent_results:
            reviewer_data = agent_results["medical_reviewer_agent"]
            if isinstance(reviewer_data, dict):
                confidence_score = reviewer_data.get("confidence_score")
        
        return AnalysisResponse(
            success=True,
            patient_id=patient_id,
            analysis=claude_analysis,
            recommendations=recommendations,
            confidence_score=confidence_score,
            error=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Failed to analyze patient {patient_id}: {str(e)}"
        logger.error(f"{error_msg}\\n{traceback.format_exc()}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )


@app.get("/api/patient/{patient_id}/dashboard", response_model=DashboardData)
async def get_patient_dashboard(patient_id: str):
    """Get comprehensive patient dashboard data with file history and analysis results."""
    try:
        logger.info(f"Getting dashboard data for patient {patient_id}")
        
        # Validate patient exists
        patient_data_availability = patient_lookup_service.check_patient_data_availability(patient_id)
        if not patient_data_availability["patient_exists"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient {patient_id} not found"
            )
        
        # Get patient profile
        patient_profile = patient_lookup_service.get_patient_profile(patient_id)
        
        # Get patient folder paths
        patient_folders = patient_lookup_service.get_patient_folder_paths(patient_id)
        
        # Create patient info with complete profile data
        patient_info_data = {
            "patient_id": patient_id,
            "folder_name": patient_data_availability["folder_name"],
            "folder_path": patient_data_availability["raw_data_path"],
            "has_profile": patient_profile is not None,
            "xml_files": patient_data_availability["xml_files_count"],
            "processed_json_files": patient_data_availability["json_files_count"]
        }
        
        # Add profile data if available
        if patient_profile:
            patient_info_data.update({
                "full_name": patient_profile.get("full_name"),
                "gender": patient_profile.get("gender"),
                "birth_year": patient_profile.get("birth_year"),
                "nationality": patient_profile.get("nationality"),
                "marital_status": patient_profile.get("marital_status"),
                "employment_sector": patient_profile.get("employment_sector"),
                "insurance_plan": patient_profile.get("insurance_plan"),
                "coverage_tier": patient_profile.get("coverage_tier"),
                "smoker": patient_profile.get("smoker"),
                "baseline_BMI": patient_profile.get("baseline_BMI"),
                "baseline_BP_systolic": patient_profile.get("baseline_BP_systolic"),
                "family_history_diabetes": patient_profile.get("family_history_diabetes"),
                "family_history_CAD": patient_profile.get("family_history_CAD")
            })
        
        patient_info = PatientInfo(**patient_info_data)
        
        # Get recent file processing history
        recent_files = []
        if patient_folders:
            raw_data_path = Path(patient_folders["raw_data_path"])
            processed_data_path = Path(patient_folders["processed_data_path"])
            
            # Get XML files with timestamps
            xml_files = list(raw_data_path.glob("*.xml"))
            xml_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)  # Most recent first
            
            for xml_file in xml_files[:5]:  # Get last 5 files
                # Check if corresponding JSON exists
                json_filename = xml_file.name.replace(".xml", ".json")
                json_file = processed_data_path / json_filename
                
                file_info = {
                    "filename": xml_file.name,
                    "upload_date": datetime.fromtimestamp(xml_file.stat().st_mtime).isoformat(),
                    "file_size": xml_file.stat().st_size,
                    "source": "unknown",  # TODO: Store actual source information with files
                    "processed": json_file.exists(),
                    "processed_date": datetime.fromtimestamp(json_file.stat().st_mtime).isoformat() if json_file.exists() else None
                }
                recent_files.append(file_info)
        
        # Get analysis history (simplified - would need analysis service to track this)
        analysis_history = []
        # This would be populated from analysis service logs/database if available
        
        # Get patient history for more detailed stats
        patient_history = patient_lookup_service.get_patient_history(patient_id)
        
        # Calculate summary stats
        last_activity = None
        if recent_files:
            last_activity = recent_files[0]["upload_date"]
        
        summary_stats = {
            "total_xml_files": patient_data_availability["xml_files_count"],
            "total_processed_files": patient_data_availability["json_files_count"],
            "total_historical_records": len(patient_history),
            "processing_success_rate": (
                patient_data_availability["json_files_count"] / patient_data_availability["xml_files_count"]
                if patient_data_availability["xml_files_count"] > 0 else 0.0
            ),
            "last_activity": last_activity,
            "has_profile": patient_profile is not None,
            "claude_analysis_available": claude_analysis_service.claude_available
        }
        
        # Add patient demographics if available
        if patient_profile:
            summary_stats.update({
                "patient_name": patient_profile.get("full_name", "Unknown"),
                "insurance_company": patient_profile.get("insurance_plan", "Unknown"),
                "member_id": patient_profile.get("patient_id", "Unknown")  # Use patient_id as member identifier
            })
        
        # Create dashboard data
        dashboard_data = DashboardData(
            patient_info=patient_info,
            recent_files=recent_files,
            analysis_history=analysis_history,
            summary_stats=summary_stats
        )
        
        logger.info(f"Dashboard data retrieved for patient {patient_id}: "
                   f"{patient_data_availability['xml_files_count']} XML files, "
                   f"{patient_data_availability['json_files_count']} processed files")
        
        return dashboard_data
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Failed to get dashboard data for patient {patient_id}: {str(e)}"
        logger.error(f"{error_msg}\\n{traceback.format_exc()}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {str(exc)}\\n{traceback.format_exc()}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal server error",
            details=str(exc),
            timestamp=datetime.now(timezone.utc)
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