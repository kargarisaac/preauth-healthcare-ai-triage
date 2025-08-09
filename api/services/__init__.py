"""
FastAPI Services Package - Simplified
Essential services for XML processing, Claude analysis, and patient lookup.
"""

from .patient_lookup_service import get_patient_lookup_service
from .xml_processing_service import get_xml_processing_service
from .claude_analysis_service import get_claude_analysis_service

__all__ = [
    "get_patient_lookup_service",
    "get_xml_processing_service", 
    "get_claude_analysis_service"
]