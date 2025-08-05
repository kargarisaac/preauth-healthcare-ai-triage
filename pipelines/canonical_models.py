"""
Canonical data models for UAE healthcare pre-authorization processing.

This module defines standardized dataclasses for representing healthcare
authorization data from eClaimLink and Shafafiya formats in a unified structure.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid


@dataclass
class Address:
    """Patient or provider address information."""
    street: Optional[str] = None
    city: Optional[str] = None
    emirate: Optional[str] = None
    postal_code: Optional[str] = None


@dataclass
class InsuranceInfo:
    """Patient insurance policy information."""
    policy_number: Optional[str] = None
    payer_name: Optional[str] = None
    policy_holder: Optional[str] = None
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None
    coverage_type: Optional[str] = None


@dataclass
class ClinicalInfo:
    """Patient clinical and medical history information."""
    conditions: Optional[List[Any]] = field(default_factory=list)
    allergies: Optional[str] = None
    current_medications: Optional[Any] = None
    vital_signs: Optional[Dict[str, Any]] = None


@dataclass
class Patient:
    """Standardized patient information."""
    member_id: Optional[str] = None
    emirates_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    nationality: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    weight: Optional[str] = None
    height: Optional[str] = None
    address: Optional[Address] = field(default_factory=Address)
    insurance: Optional[InsuranceInfo] = field(default_factory=InsuranceInfo)
    clinical_info: Optional[ClinicalInfo] = field(default_factory=ClinicalInfo)


@dataclass
class Provider:
    """Healthcare provider information."""
    provider_id: Optional[str] = None
    provider_name: Optional[str] = None
    license_number: Optional[str] = None
    contact_person: Optional[str] = None
    specialty: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    address: Optional[Address] = field(default_factory=Address)


@dataclass
class Service:
    """Healthcare service request (eClaimLink format)."""
    sequence: Optional[int] = None
    activity_code: Optional[str] = None
    diagnosis_code: Optional[str] = None
    activity_date_time: Optional[str] = None
    instructions: Optional[str] = None
    requested_amount_value: Optional[str] = None
    requested_amount_currency: Optional[str] = None
    raw_service_data: Optional[Dict[str, Any]] = None


@dataclass
class Activity:
    """Healthcare activity/service (Shafafiya format)."""
    id: Optional[str] = None
    type: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    quantity: Optional[str] = None
    estimated_cost: Optional[str] = None
    urgency: Optional[str] = None
    scheduled_date: Optional[str] = None
    raw_activity_data: Optional[Dict[str, Any]] = None


@dataclass
class QualityScore:
    """Data quality assessment scores."""
    overall_score: float = 0.0
    code_validity: float = 0.0
    completeness: float = 0.0
    clinical_consistency: float = 0.0
    format_compliance: float = 0.0


@dataclass
class DataQuality:
    """Data quality validation report."""
    quality_score: Optional[QualityScore] = field(default_factory=QualityScore)
    validation_issues: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class FHIRMeta:
    """FHIR Bundle metadata."""
    profile: List[str] = field(default_factory=lambda: ["https://nazmito.com/fhir/StructureDefinition/healthcare-bundle"])
    source: Optional[str] = None
    last_updated: Optional[str] = None
    version_id: str = "1"


@dataclass
class CanonicalBundle:
    """
    Unified canonical data structure for UAE healthcare pre-authorization data.
    
    This dataclass provides a standardized representation that works for both
    eClaimLink and Shafafiya formats, enabling consistent processing and analysis.
    """
    # FHIR Bundle structure
    resource_type: str = "Bundle"
    id: Optional[str] = None
    meta: Optional[FHIRMeta] = field(default_factory=FHIRMeta)
    type: str = "collection"
    timestamp: Optional[str] = None
    
    # Essential mapped fields (common to both formats)
    authorization_id: Optional[str] = None
    sender: Optional[str] = None
    receiver: Optional[str] = None
    transaction_date: Optional[str] = None
    
    # Patient and provider information
    patient: Optional[Patient] = field(default_factory=Patient)
    provider: Optional[Provider] = field(default_factory=Provider)
    
    # Clinical justification
    justification_text: Optional[str] = None
    clinical_justification: Optional[str] = None
    
    # Services/Activities (format-specific)
    services: List[Service] = field(default_factory=list)  # eClaimLink
    activities: List[Activity] = field(default_factory=list)  # Shafafiya
    
    # Shafafiya-specific fields
    request_status: Optional[str] = None
    coverage_start: Optional[str] = None
    coverage_end: Optional[str] = None
    
    # Data quality validation
    data_quality: Optional[DataQuality] = None
    
    # Original data preservation
    raw_data: Optional[Dict[str, Any]] = None
    source_file: Optional[str] = None
    processing_timestamp: Optional[str] = None
    
    def __post_init__(self):
        """Initialize computed fields after dataclass creation."""
        if not self.id:
            source_prefix = self.meta.source or "Bundle"
            date_str = datetime.now().strftime('%Y%m%d')
            self.id = f"{source_prefix}-{str(uuid.uuid4())[:8]}-{date_str}"
        
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        
        if not self.processing_timestamp:
            self.processing_timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert dataclass to dictionary format for JSON serialization."""
        result = {}
        
        # Basic FHIR fields
        result["resourceType"] = self.resource_type
        result["id"] = self.id
        result["type"] = self.type
        result["timestamp"] = self.timestamp
        
        # Meta information - convert to dict
        if self.meta:
            result["meta"] = {
                "profile": self.meta.profile,
                "source": self.meta.source,
                "lastUpdated": self.meta.last_updated,
                "versionId": self.meta.version_id
            }
        
        # Essential fields
        result["authorization_id"] = self.authorization_id
        result["sender"] = self.sender
        result["receiver"] = self.receiver
        result["transaction_date"] = self.transaction_date
        
        # Patient information - convert to dict if exists
        if self.patient and any(getattr(self.patient, field.name) for field in self.patient.__dataclass_fields__.values()):
            result["patient"] = self._patient_to_dict()
        
        # Provider information - convert to dict if exists
        if self.provider and any(getattr(self.provider, field.name) for field in self.provider.__dataclass_fields__.values()):
            result["provider"] = self._provider_to_dict()
        
        # Clinical justification (use appropriate field based on format)
        if self.justification_text:
            result["justification_text"] = self.justification_text
        if self.clinical_justification:
            result["clinical_justification"] = self.clinical_justification
        
        # Services (eClaimLink)
        if self.services:
            result["services"] = [self._service_to_dict(service) for service in self.services]
        
        # Activities (Shafafiya)
        if self.activities:
            result["activities"] = [self._activity_to_dict(activity) for activity in self.activities]
        
        # Shafafiya-specific fields
        if self.request_status:
            result["request_status"] = self.request_status
        if self.coverage_start:
            result["coverage_start"] = self.coverage_start
        if self.coverage_end:
            result["coverage_end"] = self.coverage_end
        
        # Data quality
        if self.data_quality:
            result["data_quality"] = self._data_quality_to_dict()
        
        # Preservation fields
        result["raw_data"] = self.raw_data
        result["source_file"] = self.source_file
        result["processing_timestamp"] = self.processing_timestamp
        
        return result
    
    def _patient_to_dict(self) -> Dict[str, Any]:
        """Convert patient dataclass to dictionary."""
        patient_dict = {}
        for field_name in self.patient.__dataclass_fields__:
            value = getattr(self.patient, field_name)
            if value is not None:
                if field_name in ['address', 'insurance', 'clinical_info']:
                    # Handle nested dataclasses
                    if hasattr(value, '__dataclass_fields__'):
                        nested_dict = {}
                        for nested_field in value.__dataclass_fields__:
                            nested_value = getattr(value, nested_field)
                            if nested_value is not None:
                                nested_dict[nested_field] = nested_value
                        if nested_dict:
                            patient_dict[field_name] = nested_dict
                else:
                    patient_dict[field_name] = value
        return patient_dict
    
    def _provider_to_dict(self) -> Dict[str, Any]:
        """Convert provider dataclass to dictionary."""
        provider_dict = {}
        for field_name in self.provider.__dataclass_fields__:
            value = getattr(self.provider, field_name)
            if value is not None:
                if field_name == 'address' and hasattr(value, '__dataclass_fields__'):
                    # Handle address nested dataclass
                    address_dict = {}
                    for addr_field in value.__dataclass_fields__:
                        addr_value = getattr(value, addr_field)
                        if addr_value is not None:
                            address_dict[addr_field] = addr_value
                    if address_dict:
                        provider_dict[field_name] = address_dict
                else:
                    provider_dict[field_name] = value
        return provider_dict
    
    def _service_to_dict(self, service: Service) -> Dict[str, Any]:
        """Convert service dataclass to dictionary."""
        return {k: v for k, v in service.__dict__.items() if v is not None}
    
    def _activity_to_dict(self, activity: Activity) -> Dict[str, Any]:
        """Convert activity dataclass to dictionary."""
        return {k: v for k, v in activity.__dict__.items() if v is not None}
    
    def _data_quality_to_dict(self) -> Dict[str, Any]:
        """Convert data quality to dictionary."""
        if not self.data_quality:
            return {}
        
        result = {}
        if self.data_quality.quality_score:
            result["quality_score"] = self.data_quality.quality_score.__dict__
        if self.data_quality.validation_issues:
            result["validation_issues"] = self.data_quality.validation_issues
        if self.data_quality.recommendations:
            result["recommendations"] = self.data_quality.recommendations
        
        return result