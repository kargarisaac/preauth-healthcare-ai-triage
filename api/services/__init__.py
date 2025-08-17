"""
FastAPI Services Package - Simplified
Essential services for XML processing and patient lookup.
"""

from .patient_lookup_service import get_patient_lookup_service
from .xml_processing_service import get_xml_processing_service

__all__ = [
    "get_patient_lookup_service",
    "get_xml_processing_service"
]