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
from api.services import claude_analysis_service as claude_analysis_service

from api.models import PatientInfo
from preauth_system.orchestrator import PreAuthOrchestrator

# Initialize services
patient_lookup_service = get_patient_lookup_service()
xml_processing_service = get_xml_processing_service()
claude_analysis_service = claude_analysis_service  # expose module symbol for tests

# Expose a module-level orchestrator for tests to patch
workflow_orchestrator = PreAuthOrchestrator()

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
from pathlib import Path
import inspect


@app.get("/api/health")
async def health_check():
    """Simple health check endpoint."""
    xml_available = hasattr(xml_processing_service, "process_xml_file") or hasattr(
        xml_processing_service, "process_xml_content"
    )
    patient_index_ready = hasattr(patient_lookup_service, "get_all_patients")
    claude_available = hasattr(claude_analysis_service, "get_claude_analysis_service")
    status = "healthy" if (xml_available and patient_index_ready) else "degraded"
    return {
        "status": status,
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "xml_processing_available": xml_available,
        "patient_index_ready": patient_index_ready,
        "claude_available": claude_available,
        "claude_analysis_available": claude_available,
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


@app.post("/api/upload-xml")
async def upload_xml(
    file: UploadFile = File(...),
    source: str = Form(...),
    patient_id: Optional[str] = Form(None),
):
    """Validate and accept an uploaded XML file for a patient."""
    try:
        if source not in ["eclaim", "shafafiya"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid source. Must be 'eclaim' or 'shafafiya'",
            )
        if not file.filename or not file.filename.endswith(".xml"):
            raise HTTPException(status_code=400, detail="Invalid file type. Only .xml")

        # Limit 10MB
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large")

        # Process via XML service when available
        result = None
        if hasattr(xml_processing_service, "process_xml_file"):
            fn = getattr(xml_processing_service, "process_xml_file")
            if inspect.iscoroutinefunction(fn):
                result = await fn(file=file, source=source, patient_id=patient_id)
            else:
                result = fn(file=file, source=source, patient_id=patient_id)
        else:
            # Fallback to content-based
            result = xml_processing_service.process_xml_content(
                content=content.decode("utf-8"), filename=file.filename, source=source
            )

        return {
            "success": True,
            "patient_id": patient_id,
            "data": result,
            "metadata": {
                "filename": file.filename,
                "xml_source": source,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/process/{patient_id}")
async def process_patient(patient_id: str):
    """Process the most recent XML file for a patient from their raw folder."""
    try:
        availability = patient_lookup_service.check_patient_data_availability(
            patient_id
        )
        if not availability.get("patient_exists"):
            raise HTTPException(
                status_code=404, detail=f"Patient {patient_id} not found"
            )
        if not availability.get("raw_data_available", True):
            raise HTTPException(
                status_code=404, detail="No XML files found for patient"
            )

        # Find latest XML under raw_data_path or default dataset path
        folder_paths = patient_lookup_service.get_patient_folder_paths(patient_id)
        raw_path = Path(folder_paths.get("raw_data_path") or ".")
        candidates = list(raw_path.glob("*.xml"))
        if not candidates:
            raise HTTPException(status_code=404, detail="No XML files found")
        latest = max(candidates, key=lambda p: p.stat().st_mtime)
        xml_content = latest.read_text(encoding="utf-8")

        # Call orchestrator
        result = workflow_orchestrator.process_request(
            xml_content=xml_content, patient_id=patient_id, xml_format="eclaim"
        )

        return {
            "success": True,
            "patient_id": patient_id,
            "data": result,
            "metadata": {"filename": latest.name, "xml_source": "eclaim"},
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze/{patient_id}")
async def analyze_patient(
    patient_id: str, cost_limit_usd: float = 1.0, include_history: bool = True
):
    """Run agentic analysis over an existing patient context via workflow orchestrator."""
    try:
        if not hasattr(workflow_orchestrator, "analyze_existing_patient"):
            raise HTTPException(status_code=501, detail="Analysis not implemented")
        # Delegate to orchestrator (tests patch this method)
        analysis = await workflow_orchestrator.analyze_existing_patient(
            patient_id=patient_id,
            cost_limit_usd=cost_limit_usd,
            include_history=include_history,
        )
        return analysis
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
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
