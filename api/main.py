"""
Simplified FastAPI backend for pre-authorization processing.
Following CLAUDE.md principles: minimal, direct, maintainable.
"""

from typing import List, Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from api.services.patient_lookup_service import get_patient_lookup_service
from api.services.xml_processing_service import get_xml_processing_service
from api.services.claude_analysis_service import get_claude_analysis_service
from api.models import PatientInfo, UnifiedProcessResponse
from preauth_system.orchestrator import PreAuthOrchestrator

# Initialize services
patient_lookup_service = get_patient_lookup_service()
xml_processing_service = get_xml_processing_service()
claude_analysis_service = get_claude_analysis_service()

# Initialize FastAPI app
app = FastAPI(
    title="Nazmito Pre-Authorization API",
    description="AI-Powered Pre-Authorization Platform for UAE Healthcare",
    version="2.0.0",
    docs_url="/api/docs",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from datetime import datetime


@app.get("/api/health")
async def health_check():
    """Simple health check endpoint."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/api/patients", response_model=List[PatientInfo])
async def list_patients():
    """List all available patients."""
    try:
        patients = []
        all_patients = patient_lookup_service.get_all_patients()

        for patient_id, folder_name in all_patients.items():
            validation = patient_lookup_service.validate_patient_folder_structure(
                patient_id
            )
            profile = patient_lookup_service.get_patient_profile(patient_id)

            patient_data = {
                "patient_id": patient_id,
                "folder_name": folder_name,
                "folder_path": validation.get("folder_path", ""),
                "has_profile": validation.get("has_profile", False),
                "xml_files": validation.get("xml_files", 0),
                "processed_json_files": validation.get("processed_json_files", 0),
            }

            if profile:
                patient_data.update(
                    {
                        "full_name": profile.get("full_name"),
                        "gender": profile.get("gender"),
                        "birth_year": profile.get("birth_year"),
                        "nationality": profile.get("nationality"),
                    }
                )

            patients.append(PatientInfo(**patient_data))

        return patients

    except Exception as e:
        logger.error(f"Failed to list patients: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/process-xml/{patient_id}", response_model=UnifiedProcessResponse)
async def process_xml(
    patient_id: str,
    file: UploadFile = File(...),
    source: str = Form(...),
    enable_analysis: bool = Form(True),
):
    """Process XML file for a patient."""
    try:
        # Validate inputs
        if not file.filename or not file.filename.endswith(".xml"):
            raise HTTPException(status_code=400, detail="Only XML files allowed")

        if source not in ["eclaim", "shafafiya"]:
            raise HTTPException(
                status_code=400, detail="Source must be 'eclaim' or 'shafafiya'"
            )

        logger.info(f"Processing XML for patient {patient_id}: {file.filename}")

        # Read file content
        content = await file.read()

        # Process XML
        xml_result = xml_processing_service.process_xml_content(
            content=content.decode("utf-8"), filename=file.filename, source=source
        )

        if not xml_result["success"]:
            raise HTTPException(status_code=400, detail=xml_result.get("error"))

        # Run analysis if enabled
        analysis_result = None
        if enable_analysis:
            try:
                orchestrator = PreAuthOrchestrator()
                analysis_result = orchestrator.process_request(
                    xml_content=content.decode("utf-8"), patient_id=patient_id
                )
            except Exception as e:
                logger.warning(f"Analysis failed: {e}")
                analysis_result = {"error": str(e)}

        return UnifiedProcessResponse(
            success=True,
            patient_id=patient_id,
            filename=file.filename,
            xml_processing=xml_result,
            claude_analysis=analysis_result,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"XML processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/preauth/process")
async def preauth_process(
    file: UploadFile = File(...), patient_id: Optional[str] = Form(None)
):
    """Process pre-authorization request."""
    try:
        content = await file.read()
        orchestrator = PreAuthOrchestrator()

        result = orchestrator.process_request(
            xml_content=content.decode("utf-8"), patient_id=patient_id
        )

        return {"success": True, "result": result}

    except Exception as e:
        logger.error(f"Preauth processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/patient/{patient_id}/dashboard")
async def patient_dashboard(patient_id: str):
    """Get dashboard data for a patient."""
    try:
        # Get patient profile
        profile = patient_lookup_service.get_patient_profile(patient_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Patient not found")

        # Get folder validation
        validation = patient_lookup_service.validate_patient_folder_structure(
            patient_id
        )

        return {
            "patient_id": patient_id,
            "profile": profile,
            "folder_validation": validation,
            "xml_files": validation.get("xml_files", 0),
            "processed_files": validation.get("processed_json_files", 0),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dashboard data failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
