#!/usr/bin/env python3
"""
Workflow Orchestrator Service
Coordinates end-to-end XML processing and Claude analysis workflows.

This service orchestrates complex workflows that combine XML processing,
patient ID resolution, and Claude analysis with proper progress tracking
and error handling.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Literal, Callable
from fastapi import UploadFile, HTTPException, status
from loguru import logger

from api.services.xml_processing_service import get_xml_processing_service
from api.services.claude_analysis_service import get_claude_analysis_service
from api.services.patient_lookup_service import get_patient_lookup_service

# Removed auto-detection service - source should be explicitly provided
from api.config_loader import get_config


class WorkflowOrchestrator:
    """
    Service for orchestrating end-to-end processing workflows.

    Coordinates XML processing, patient lookup, and Claude analysis
    in integrated workflows with progress tracking and error recovery.
    """

    def __init__(self):
        """Initialize workflow orchestrator."""
        self.xml_service = get_xml_processing_service()
        self.claude_service = get_claude_analysis_service()
        self.patient_lookup = get_patient_lookup_service()
        # Removed auto-detection service - source should be explicitly provided
        self.config = get_config()
        self.dataset_paths = self.config.get_dataset_paths()

        logger.info(
            "Workflow Orchestrator initialized with patient-centric capabilities"
        )

    async def xml_to_analysis_workflow(
        self,
        file: UploadFile,
        source: Literal["eclaim", "shafafiya"],
        enable_analysis: bool = True,
        cost_limit_usd: float = 1.0,
        include_history: bool = True,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> Dict[str, Any]:
        """
        Complete XML-to-analysis workflow.

        Args:
            file: Uploaded XML file
            source: XML format source ("eclaim" or "shafafiya")
            enable_analysis: Whether to run Claude analysis
            cost_limit_usd: Cost limit for Claude analysis
            include_history: Whether to include patient history in analysis
            progress_callback: Optional progress callback function

        Returns:
            Complete workflow results with XML processing and analysis
        """
        workflow_start = datetime.now()

        try:
            if progress_callback:
                progress_callback("Starting XML-to-analysis workflow", 0.05)

            logger.info(
                f"Starting XML-to-analysis workflow: {file.filename} ({source})"
            )

            # Step 1: Process XML file
            if progress_callback:
                progress_callback("Processing XML file", 0.1)

            xml_results = await self.xml_service.process_xml_file(file, source)

            if not xml_results["success"]:
                raise ValueError("XML processing failed")

            bundle = xml_results["bundle"]
            patient_id = xml_results["patient_id"]

            if progress_callback:
                progress_callback("XML processing completed", 0.3)

            # Step 2: Validate patient for analysis
            analysis_results = None
            if enable_analysis:
                if not patient_id:
                    logger.warning("Cannot run analysis without patient ID")
                    if progress_callback:
                        progress_callback("Skipping analysis - no patient ID", 0.9)
                elif not self.claude_service.claude_available:
                    logger.warning("Claude analysis not available")
                    if progress_callback:
                        progress_callback("Skipping analysis - Claude unavailable", 0.9)
                else:
                    # Step 3: Run Claude analysis
                    if progress_callback:
                        progress_callback("Running Claude analysis", 0.4)

                    def analysis_progress(message: str, progress: float):
                        # Map analysis progress to overall workflow progress (0.4 to 0.9)
                        workflow_progress = 0.4 + (progress * 0.5)
                        if progress_callback:
                            progress_callback(f"Analysis: {message}", workflow_progress)

                    analysis_results = await self.claude_service.analyze_preauth(
                        patient_id=patient_id,
                        current_request=bundle,
                        include_history=include_history,
                        cost_limit_usd=cost_limit_usd,
                        progress_callback=analysis_progress,
                    )

            if progress_callback:
                progress_callback("Compiling results", 0.95)

            # Step 4: Compile workflow results
            workflow_end = datetime.now()
            total_time = (workflow_end - workflow_start).total_seconds()

            results = {
                "success": True,
                "workflow_type": "xml_to_analysis",
                "xml_processing": {
                    "success": xml_results["success"],
                    "bundle": bundle,
                    "source": source,
                    "patient_id": patient_id,
                    "patient_folder": xml_results["patient_folder"],
                    "metadata": xml_results["metadata"],
                },
                "claude_analysis": analysis_results if enable_analysis else None,
                "workflow_metadata": {
                    "start_time": workflow_start.isoformat(),
                    "end_time": workflow_end.isoformat(),
                    "total_time_seconds": total_time,
                    "enable_analysis": enable_analysis,
                    "cost_limit_usd": cost_limit_usd,
                    "include_history": include_history,
                },
                "summary": {
                    "patient_id": patient_id,
                    "source": source,
                    "analysis_enabled": enable_analysis
                    and analysis_results is not None,
                    "analysis_cost_usd": analysis_results.get("cost_usd", 0.0)
                    if analysis_results
                    else 0.0,
                    "total_processing_time": total_time,
                },
            }

            if progress_callback:
                progress_callback("Workflow completed", 1.0)

            logger.info(
                f"XML-to-analysis workflow completed: {file.filename}, "
                f"patient: {patient_id}, analysis: {enable_analysis}, "
                f"time: {total_time:.1f}s"
            )

            return results

        except Exception as e:
            workflow_end = datetime.now()
            total_time = (workflow_end - workflow_start).total_seconds()

            logger.error(f"XML-to-analysis workflow failed: {file.filename}: {e}")

            if progress_callback:
                progress_callback(f"Workflow failed: {str(e)}", 1.0)

            return {
                "success": False,
                "workflow_type": "xml_to_analysis",
                "error": str(e),
                "workflow_metadata": {
                    "start_time": workflow_start.isoformat(),
                    "end_time": workflow_end.isoformat(),
                    "total_time_seconds": total_time,
                    "enable_analysis": enable_analysis,
                    "cost_limit_usd": cost_limit_usd,
                },
            }

    async def analyze_existing_patient(
        self,
        patient_id: str,
        cost_limit_usd: float = 1.0,
        include_history: bool = True,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze existing patient using most recent processed data.

        Args:
            patient_id: Patient UUID
            cost_limit_usd: Cost limit for analysis
            include_history: Whether to include patient history
            progress_callback: Optional progress callback function

        Returns:
            Analysis results for existing patient
        """
        workflow_start = datetime.now()

        try:
            if progress_callback:
                progress_callback("Loading patient data", 0.1)

            logger.info(f"Starting analysis for existing patient: {patient_id}")

            # Get patient history
            historical_data = self.patient_lookup.get_patient_history(patient_id)

            if not historical_data:
                raise ValueError(f"No processed data found for patient {patient_id}")

            # Use most recent data as current request
            current_request = historical_data[-1]  # Last item is most recent
            remaining_history = historical_data[:-1] if include_history else []

            if progress_callback:
                progress_callback("Running Claude analysis", 0.2)

            # Run analysis
            analysis_results = await self.claude_service.analyze_preauth(
                patient_id=patient_id,
                current_request=current_request,
                include_history=include_history,
                cost_limit_usd=cost_limit_usd,
                progress_callback=progress_callback,
            )

            workflow_end = datetime.now()
            total_time = (workflow_end - workflow_start).total_seconds()

            results = {
                "success": True,
                "workflow_type": "existing_patient_analysis",
                "patient_id": patient_id,
                "claude_analysis": analysis_results,
                "workflow_metadata": {
                    "start_time": workflow_start.isoformat(),
                    "end_time": workflow_end.isoformat(),
                    "total_time_seconds": total_time,
                    "historical_files_used": len(remaining_history),
                    "current_request_source": "most_recent_processed",
                },
            }

            logger.info(
                f"Existing patient analysis completed: {patient_id}, "
                f"cost: ${analysis_results.get('cost_usd', 0):.3f}"
            )

            return results

        except Exception as e:
            workflow_end = datetime.now()
            total_time = (workflow_end - workflow_start).total_seconds()

            logger.error(f"Existing patient analysis failed: {patient_id}: {e}")

            return {
                "success": False,
                "workflow_type": "existing_patient_analysis",
                "patient_id": patient_id,
                "error": str(e),
                "workflow_metadata": {
                    "start_time": workflow_start.isoformat(),
                    "end_time": workflow_end.isoformat(),
                    "total_time_seconds": total_time,
                },
            }

    async def batch_process_patient(
        self,
        patient_id: str,
        source: Literal["eclaim", "shafafiya"],
        enable_analysis: bool = False,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> Dict[str, Any]:
        """
        Process all XML files for a patient from synthetic dataset.

        Args:
            patient_id: Patient UUID
            source: XML format source
            enable_analysis: Whether to run analysis on latest file
            progress_callback: Optional progress callback function

        Returns:
            Batch processing results for patient
        """
        workflow_start = datetime.now()

        try:
            if progress_callback:
                progress_callback("Finding patient folder", 0.1)

            # Find patient folder
            patient_folder = self.patient_lookup.find_patient_folder(patient_id)
            if not patient_folder:
                raise ValueError(f"Patient {patient_id} not found")

            # Get XML files
            xml_files = list(patient_folder.glob("*.xml"))
            if not xml_files:
                raise ValueError(f"No XML files found for patient {patient_id}")

            xml_files.sort()  # Process in chronological order

            if progress_callback:
                progress_callback(f"Processing {len(xml_files)} XML files", 0.2)

            # Process each XML file
            processed_files = []
            for i, xml_file in enumerate(xml_files):
                file_progress = 0.2 + (i / len(xml_files)) * 0.6
                if progress_callback:
                    progress_callback(f"Processing {xml_file.name}", file_progress)

                # Process XML using data pipeline logic
                if source == "eclaim":
                    bundle = self.xml_service.xml_processor.process_eclaim_link(
                        str(xml_file)
                    )
                else:
                    bundle = self.xml_service.xml_processor.process_shafafiya(
                        str(xml_file)
                    )

                processed_files.append(
                    {
                        "file": xml_file.name,
                        "bundle": bundle,
                        "processed_at": datetime.now().isoformat(),
                    }
                )

            # Optionally run analysis on latest file
            analysis_results = None
            if enable_analysis and processed_files:
                if progress_callback:
                    progress_callback("Running analysis on latest file", 0.85)

                latest_bundle = processed_files[-1]["bundle"]
                analysis_results = await self.claude_service.analyze_preauth(
                    patient_id=patient_id,
                    current_request=latest_bundle,
                    include_history=True,
                    cost_limit_usd=1.0,
                )

            workflow_end = datetime.now()
            total_time = (workflow_end - workflow_start).total_seconds()

            if progress_callback:
                progress_callback("Batch processing completed", 1.0)

            results = {
                "success": True,
                "workflow_type": "batch_process_patient",
                "patient_id": patient_id,
                "source": source,
                "processed_files": processed_files,
                "files_processed": len(processed_files),
                "claude_analysis": analysis_results,
                "workflow_metadata": {
                    "start_time": workflow_start.isoformat(),
                    "end_time": workflow_end.isoformat(),
                    "total_time_seconds": total_time,
                    "patient_folder": str(patient_folder),
                },
            }

            logger.info(
                f"Batch processing completed for patient {patient_id}: "
                f"{len(processed_files)} files, {total_time:.1f}s"
            )

            return results

        except Exception as e:
            logger.error(f"Batch processing failed for patient {patient_id}: {e}")

            return {
                "success": False,
                "workflow_type": "batch_process_patient",
                "patient_id": patient_id,
                "error": str(e),
                "workflow_metadata": {
                    "start_time": workflow_start.isoformat(),
                    "total_time_seconds": (
                        datetime.now() - workflow_start
                    ).total_seconds(),
                },
            }

    async def patient_centric_workflow(
        self,
        patient_id: str,
        xml_file: UploadFile,
        auto_detect_source: bool = True,
        source: Optional[Literal["eclaim", "shafafiya"]] = None,
        enable_analysis: bool = True,
        cost_limit_usd: float = 1.0,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> Dict[str, Any]:
        """
        Patient-centric workflow that stores files in patient folders and processes them.

        Args:
            patient_id: Patient UUID
            xml_file: Uploaded XML file
            auto_detect_source: Whether to auto-detect XML source
            source: Manual source specification (overrides auto-detection)
            enable_analysis: Whether to run Claude analysis
            cost_limit_usd: Cost limit for analysis
            progress_callback: Optional progress callback function

        Returns:
            Complete workflow results with file storage and processing
        """
        workflow_start = datetime.now()

        try:
            if progress_callback:
                progress_callback("Starting patient-centric workflow", 0.05)

            logger.info(
                f"Starting patient-centric workflow for patient {patient_id}: {xml_file.filename}"
            )

            # Step 1: Ensure patient folders exist
            if progress_callback:
                progress_callback("Setting up patient folders", 0.1)

            patient_folders = self.patient_lookup.get_patient_folder_paths(patient_id)
            if not patient_folders:
                # Create new patient folders
                logger.info(f"Creating new patient folders for {patient_id}")
                patient_folders = self.patient_lookup.create_patient_folders(patient_id)

            raw_data_path = Path(patient_folders["raw_data_path"])
            processed_data_path = Path(patient_folders["processed_data_path"])

            # Step 2: Auto-detect or validate source
            if progress_callback:
                progress_callback("Detecting XML source format", 0.15)

            if auto_detect_source and not source:
                # Read file content for detection
                file_content = await xml_file.read()
                xml_content = file_content.decode("utf-8")
                await xml_file.seek(0)  # Reset file pointer

                # Auto-detection removed - must explicitly provide source
                raise ValueError(
                    "Source parameter is required. Auto-detection has been removed."
                )
            elif not source:
                # Use default source
                source = self.config.get("processing.default_source", "eclaim")
                logger.info(f"Using default source: {source}")

            # Step 3: Generate filename and store XML file
            if progress_callback:
                progress_callback("Storing XML file in patient folder", 0.2)

            timestamp = datetime.now().strftime("%Y%m%d")
            # Count existing files to generate request number
            existing_files = list(raw_data_path.glob("*.xml"))
            req_num = len(existing_files) + 1

            # Generate filename following convention
            if source == "eclaim":
                stored_filename = (
                    f"dubai_{patient_id}_{timestamp}_req{req_num:02d}_eclaim.xml"
                )
            else:
                stored_filename = (
                    f"abudhabi_{patient_id}_{timestamp}_req{req_num:02d}_shafafiya.xml"
                )

            stored_file_path = raw_data_path / stored_filename

            # Save file to patient's raw data folder
            with open(stored_file_path, "wb") as f:
                file_content = await xml_file.read()
                f.write(file_content)
                await xml_file.seek(0)  # Reset for further processing

            logger.info(f"Stored XML file: {stored_file_path}")

            # Step 4: Process XML to JSON
            if progress_callback:
                progress_callback("Processing XML to JSON", 0.3)

            xml_results = await self.xml_service.process_xml_file(xml_file, source)

            if not xml_results["success"]:
                raise ValueError("XML processing failed")

            bundle = xml_results["bundle"]

            # Step 5: Store processed JSON
            if progress_callback:
                progress_callback("Storing processed JSON", 0.5)

            json_filename = stored_filename.replace(".xml", ".json")
            json_file_path = processed_data_path / json_filename

            with open(json_file_path, "w", encoding="utf-8") as f:
                json.dump(bundle, f, indent=2, ensure_ascii=False)

            logger.info(f"Stored processed JSON: {json_file_path}")

            # Step 6: Update patient profile if needed
            if progress_callback:
                progress_callback("Updating patient profile", 0.6)

            self._update_patient_profile_if_needed(patient_id, bundle)

            # Step 7: Run Claude analysis if enabled
            analysis_results = None
            if enable_analysis and self.claude_service.claude_available:
                if progress_callback:
                    progress_callback("Running Claude analysis", 0.7)

                def analysis_progress(message: str, progress: float):
                    workflow_progress = 0.7 + (progress * 0.2)
                    if progress_callback:
                        progress_callback(f"Analysis: {message}", workflow_progress)

                analysis_results = await self.claude_service.analyze_preauth(
                    patient_id=patient_id,
                    current_request=bundle,
                    include_history=True,
                    cost_limit_usd=cost_limit_usd,
                    progress_callback=analysis_progress,
                )

            # Step 8: Compile results
            if progress_callback:
                progress_callback("Compiling workflow results", 0.95)

            workflow_end = datetime.now()
            total_time = (workflow_end - workflow_start).total_seconds()

            results = {
                "success": True,
                "workflow_type": "patient_centric",
                "patient_id": patient_id,
                "file_storage": {
                    "original_filename": xml_file.filename,
                    "stored_filename": stored_filename,
                    "raw_data_path": str(stored_file_path),
                    "processed_data_path": str(json_file_path),
                    "source": source,
                    "auto_detected": auto_detect_source and source,
                },
                "xml_processing": {
                    "success": xml_results["success"],
                    "bundle": bundle,
                    "source": source,
                    "metadata": xml_results["metadata"],
                },
                "claude_analysis": analysis_results if enable_analysis else None,
                "patient_data": {
                    "folder_paths": patient_folders,
                    "total_xml_files": len(list(raw_data_path.glob("*.xml"))),
                    "total_json_files": len(
                        [
                            f
                            for f in processed_data_path.glob("*.json")
                            if f.name != "profile.json"
                        ]
                    ),
                },
                "workflow_metadata": {
                    "start_time": workflow_start.isoformat(),
                    "end_time": workflow_end.isoformat(),
                    "total_time_seconds": total_time,
                    "auto_detect_source": auto_detect_source,
                    "enable_analysis": enable_analysis,
                    "cost_limit_usd": cost_limit_usd,
                },
            }

            if progress_callback:
                progress_callback("Patient-centric workflow completed", 1.0)

            logger.info(
                f"Patient-centric workflow completed for {patient_id}: "
                f"stored as {stored_filename}, analysis: {enable_analysis}, "
                f"time: {total_time:.1f}s"
            )

            return results

        except Exception as e:
            workflow_end = datetime.now()
            total_time = (workflow_end - workflow_start).total_seconds()

            logger.error(f"Patient-centric workflow failed for {patient_id}: {e}")

            if progress_callback:
                progress_callback(f"Workflow failed: {str(e)}", 1.0)

            return {
                "success": False,
                "workflow_type": "patient_centric",
                "patient_id": patient_id,
                "error": str(e),
                "workflow_metadata": {
                    "start_time": workflow_start.isoformat(),
                    "end_time": workflow_end.isoformat(),
                    "total_time_seconds": total_time,
                },
            }

    def _update_patient_profile_if_needed(
        self, patient_id: str, bundle: Dict[str, Any]
    ) -> None:
        """
        Update patient profile with information from processed bundle if needed.

        Args:
            patient_id: Patient UUID
            bundle: Processed FHIR bundle
        """
        try:
            patient_folders = self.patient_lookup.get_patient_folder_paths(patient_id)
            if not patient_folders:
                return

            profile_path = Path(patient_folders["processed_data_path"]) / "profile.json"

            # Check if profile exists
            if profile_path.exists():
                logger.debug(f"Profile already exists for patient {patient_id}")
                return

            # Extract patient information from bundle
            patient_info = self._extract_patient_info_from_bundle(bundle)

            if patient_info:
                # Create basic profile
                profile = {
                    "patient_id": patient_id,
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    **patient_info,
                }

                # Save profile
                with open(profile_path, "w", encoding="utf-8") as f:
                    json.dump(profile, f, indent=2, ensure_ascii=False)

                logger.info(f"Created profile for new patient {patient_id}")

                # Update patient lookup index
                self.patient_lookup.refresh_index()

        except Exception as e:
            logger.error(f"Failed to update patient profile for {patient_id}: {e}")

    def _extract_patient_info_from_bundle(
        self, bundle: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Extract patient information from FHIR bundle.

        Args:
            bundle: FHIR bundle dictionary

        Returns:
            Extracted patient information or None
        """
        try:
            # Look for Patient resource in FHIR resources
            fhir_resources = bundle.get("fhir_resources", {})

            for resource_id, resource in fhir_resources.items():
                if resource.get("resourceType") == "Patient":
                    # Extract basic patient info
                    patient_data = {
                        "full_name": "Unknown",
                        "date_of_birth": "Unknown",
                        "gender": "Unknown",
                        "insurance_details": {},
                    }

                    # Extract name
                    names = resource.get("name", [])
                    if names and isinstance(names, list) and len(names) > 0:
                        name = names[0]
                        given = name.get("given", [])
                        family = name.get("family", "")
                        if given and family:
                            patient_data["full_name"] = f"{' '.join(given)} {family}"

                    # Extract birth date
                    birth_date = resource.get("birthDate")
                    if birth_date:
                        patient_data["date_of_birth"] = birth_date

                    # Extract gender
                    gender = resource.get("gender")
                    if gender:
                        patient_data["gender"] = gender

                    return patient_data

            return None

        except Exception as e:
            logger.error(f"Failed to extract patient info from bundle: {e}")
            return None

    def get_workflow_status(self) -> Dict[str, Any]:
        """
        Get workflow orchestrator status.

        Returns:
            Service status and capabilities
        """
        return {
            "service_status": "ready",
            "xml_processing_available": True,
            "claude_analysis_available": self.claude_service.claude_available,
            "auto_detection_available": False,
            "patient_index_size": len(self.patient_lookup.patient_index),
            "dataset_paths": self.dataset_paths,
            "supported_workflows": [
                "xml_to_analysis",
                "existing_patient_analysis",
                "batch_process_patient",
                "patient_centric",  # New workflow
            ],
            "configuration": {
                "auto_detect_source": self.config.get(
                    "processing.auto_detect_source", True
                ),
                "default_source": self.config.get(
                    "processing.default_source", "eclaim"
                ),
                "claude_enabled": self.config.is_claude_enabled(),
            },
        }


# Global service instance
_workflow_orchestrator = None


def get_workflow_orchestrator() -> WorkflowOrchestrator:
    """Get global workflow orchestrator instance."""
    global _workflow_orchestrator
    if _workflow_orchestrator is None:
        _workflow_orchestrator = WorkflowOrchestrator()
    return _workflow_orchestrator
