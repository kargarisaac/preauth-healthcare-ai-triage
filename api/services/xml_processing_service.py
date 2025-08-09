#!/usr/bin/env python3
"""
Simplified XML Processing Service for Nazmito API.
Uses preauth_system intake for processing.
"""

import tempfile
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import UploadFile, HTTPException, status
from loguru import logger

from preauth_system.intake import process_pa_request


class XMLProcessingService:
    """Simplified XML processing service using preauth intake."""
    
    def __init__(self):
        self.processed_count = 0
        logger.info("XMLProcessingService initialized (simplified)")
    
    async def process_xml(self, xml_content: bytes, filename: str) -> Dict[str, Any]:
        """Process XML content into canonical format."""
        try:
            # Convert bytes to string
            xml_string = xml_content.decode('utf-8')
            
            # Use preauth intake system
            result = process_pa_request(xml_string, source_format="auto")
            
            self.processed_count += 1
            
            # Return standardized response
            return {
                "bundle": result,
                "metadata": {
                    "filename": filename,
                    "processed_at": str(datetime.now()),
                    "source_format": result.format_source if hasattr(result, 'format_source') else 'unknown'
                },
                "success": True
            }
            
        except Exception as e:
            logger.error(f"XML processing failed for {filename}: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"XML processing failed: {str(e)}"
            )


# Service factory function
_xml_processing_service = None

def get_xml_processing_service() -> XMLProcessingService:
    """Get singleton XML processing service."""
    global _xml_processing_service
    if _xml_processing_service is None:
        _xml_processing_service = XMLProcessingService()
    return _xml_processing_service