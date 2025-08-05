#!/usr/bin/env python3
"""
XML Processing Service
Handles XML file processing with mandatory source specification.

This service provides async wrapper around XMLProcessor with patient ID
extraction and proper error handling for FastAPI integration.
"""

import tempfile
import os
from pathlib import Path
from typing import Dict, Any, Optional, Literal
from fastapi import UploadFile, HTTPException, status
from loguru import logger

from api.config_loader import get_config
from pipelines.xml_processor import EclaimLinkProcessor, ShafafiyaProcessor
from api.services.patient_lookup_service import get_patient_lookup_service


class XMLProcessingService:
    """
    Service for processing XML files with mandatory source specification.

    Handles XML → JSON conversion with patient ID resolution and
    proper integration with the patient lookup system.
    """

    def __init__(self, enable_validation: bool = True):
        """
        Initialize XML processing service.

        Args:
            enable_validation: Enable data quality validation
        """
        self.eclaim_processor = EclaimLinkProcessor(enable_validation=enable_validation)
        self.shafafiya_processor = ShafafiyaProcessor(
            enable_validation=enable_validation
        )
        self.patient_lookup = get_patient_lookup_service()

        logger.info("XML Processing Service initialized")

    async def process_xml_file(
        self,
        file: UploadFile,
        source: Literal["eclaim", "shafafiya"],
        patient_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process uploaded XML file with mandatory source specification.

        Args:
            file: Uploaded XML file
            source: XML format source ("eclaim" or "shafafiya")
            patient_id: Optional patient ID override

        Returns:
            Processing results with bundle, patient info, and metadata
        """
        # Validate source
        if source not in ["eclaim", "shafafiya"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Source must be 'eclaim' or 'shafafiya'",
            )

        # Validate file
        self._validate_xml_file(file)

        # Save to temporary file
        temp_path = self._save_temp_file(file)

        try:
            logger.info(f"Processing {source} XML file: {file.filename}")

            # Process based on source
            if source == "eclaim":
                bundle = self.eclaim_processor.process_eclaim_link(temp_path)
            else:  # shafafiya
                bundle = self.shafafiya_processor.process_shafafiya(temp_path)

            # Extract or use provided patient ID
            extracted_patient_id = patient_id or self._extract_patient_id(bundle)

            # Find patient folder if patient ID is available
            patient_folder = None
            if extracted_patient_id:
                folder_path = self.patient_lookup.find_patient_folder(
                    extracted_patient_id
                )
                patient_folder = str(folder_path) if folder_path else None

            # Create processing metadata
            metadata = {
                "filename": file.filename,
                "file_size": file.size,
                "source": source,
                "processing_timestamp": bundle.get("processing_timestamp"),
                "bundle_id": bundle.get("id"),
                "patient_resolution": {
                    "patient_id": extracted_patient_id,
                    "patient_folder": patient_folder,
                    "id_source": "provided" if patient_id else "extracted",
                },
            }

            logger.info(
                f"Successfully processed {source} XML: {file.filename}, "
                f"patient: {extracted_patient_id}"
            )

            return {
                "success": True,
                "bundle": bundle,
                "source": source,
                "patient_id": extracted_patient_id,
                "patient_folder": patient_folder,
                "metadata": metadata,
            }

        except Exception as e:
            logger.error(f"Failed to process {source} XML {file.filename}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process {source} XML file: {str(e)}",
            )
        finally:
            self._cleanup_temp_file(temp_path)

    def _validate_xml_file(self, file: UploadFile) -> None:
        """Validate uploaded XML file."""
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided"
            )

        # Check file extension
        file_extension = Path(file.filename).suffix.lower()
        if file_extension != ".xml":
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

    def _save_temp_file(self, file: UploadFile) -> str:
        """Save uploaded file to temporary location."""
        try:
            # Create temporary file
            temp_fd, temp_path = tempfile.mkstemp(suffix=".xml", prefix="nazmito_xml_")

            # Write file content
            with os.fdopen(temp_fd, "wb") as temp_file:
                content = file.file.read()

                # Check file size (10MB limit)
                max_size = 10 * 1024 * 1024
                if len(content) > max_size:
                    os.unlink(temp_path)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File too large. Maximum size: 10MB",
                    )

                temp_file.write(content)

            logger.debug(f"Saved uploaded file to: {temp_path}")
            return temp_path

        except HTTPException:
            raise
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

    def _cleanup_temp_file(self, temp_path: str) -> None:
        """Clean up temporary file."""
        try:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                logger.debug(f"Cleaned up temporary file: {temp_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temporary file {temp_path}: {e}")

    def _extract_patient_id(self, bundle: Dict[str, Any]) -> Optional[str]:
        """
        Extract patient ID from FHIR Bundle.

        Args:
            bundle: FHIR Bundle dictionary

        Returns:
            Patient ID if found and valid, None otherwise
        """
        # Use patient lookup service for extraction
        patient_id = self.patient_lookup.extract_patient_id_from_bundle(bundle)

        if patient_id:
            logger.debug(f"Extracted patient ID from bundle: {patient_id}")
        else:
            logger.warning("Could not extract valid patient ID from bundle")

        return patient_id

    def validate_source_compatibility(
        self, filename: str, source: str
    ) -> Dict[str, Any]:
        """
        Validate that the specified source matches filename patterns (optional check).

        Args:
            filename: Name of the uploaded file
            source: Specified source ("eclaim" or "shafafiya")

        Returns:
            Validation result with warnings if mismatch detected
        """
        filename_lower = filename.lower()
        warnings = []

        # Check for potential mismatches
        if source == "eclaim":
            if "shafafiya" in filename_lower or "abudhabi" in filename_lower:
                warnings.append(
                    f"File '{filename}' appears to be Shafafiya format but source specified as eClaimLink"
                )
        elif source == "shafafiya":
            if "eclaim" in filename_lower or "dubai" in filename_lower:
                warnings.append(
                    f"File '{filename}' appears to be eClaimLink format but source specified as Shafafiya"
                )

        return {
            "source": source,
            "filename": filename,
            "warnings": warnings,
            "potential_mismatch": len(warnings) > 0,
        }

    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get XML processing service statistics.

        Returns:
            Service statistics and status
        """
        return {
            "service_status": "ready",
            "validation_enabled": self.eclaim_processor.enable_validation,  # Assuming both have same setting
            "patient_index_size": len(self.patient_lookup.patient_index),
            "supported_sources": ["eclaim", "shafafiya"],
        }


# Global service instance
_xml_processing_service = None


def get_xml_processing_service() -> XMLProcessingService:
    """Get global XML processing service instance."""
    global _xml_processing_service
    if _xml_processing_service is None:
        _xml_processing_service = XMLProcessingService()
    return _xml_processing_service
