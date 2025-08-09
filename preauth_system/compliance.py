"""
Compliance and Documentation Validation Module
============================================

This module implements compliance checks for UAE regulatory requirements,
documentation completeness validation, and PDPL privacy protection stubs.

Key Features:
- Minimal documentation completeness checks
- UAE regulatory compliance flags (DHA/DOH)
- PDPL redaction stubs and privacy protection
- Next-steps generation for missing information
- Audit trail for compliance verification
"""

import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta

from preauth_system.state import PreAuthState


class ComplianceLevel(Enum):
    """Compliance assessment levels."""
    COMPLIANT = "compliant"
    MINOR_ISSUES = "minor_issues"
    MAJOR_ISSUES = "major_issues"
    NON_COMPLIANT = "non_compliant"


class DocumentationType(Enum):
    """Types of required documentation."""
    CLINICAL_NOTES = "clinical_notes"
    LAB_RESULTS = "lab_results"
    IMAGING_REPORTS = "imaging_reports"
    MEDICATION_HISTORY = "medication_history"
    SPECIALIST_CONSULTATION = "specialist_consultation"
    DIAGNOSTIC_CODES = "diagnostic_codes"
    PROCEDURE_JUSTIFICATION = "procedure_justification"


@dataclass
class DocumentationGap:
    """Individual documentation gap."""
    doc_type: DocumentationType
    description: str
    requirement_level: str  # "required", "recommended", "optional"
    next_steps: str
    deadline_days: Optional[int] = None


@dataclass
class PDPLAssessment:
    """PDPL privacy compliance assessment."""
    phi_elements_identified: List[str]
    redaction_required: List[str]
    consent_status: str
    data_retention_period: Optional[str]
    cross_border_transfer: bool = False


@dataclass
class RegulatoryCompliance:
    """UAE regulatory compliance status."""
    dha_compliant: bool
    doh_compliant: bool
    licensing_valid: bool
    provider_network_status: str
    regulatory_flags: List[str]


@dataclass
class ComplianceAssessment:
    """Complete compliance evaluation result."""
    overall_level: ComplianceLevel
    documentation_gaps: List[DocumentationGap]
    pdpl_assessment: PDPLAssessment
    regulatory_compliance: RegulatoryCompliance
    completion_score: float
    next_steps: List[str]
    estimated_review_time: str
    rationale: str


class ComplianceValidator:
    """Main compliance validation engine."""
    
    def __init__(self):
        """Initialize compliance validator with UAE standards."""
        self.required_fields = self._load_required_fields()
        self.phi_patterns = self._load_phi_patterns()
        self.regulatory_requirements = self._load_regulatory_requirements()
    
    def validate_compliance(
        self,
        state: PreAuthState,
        service_codes: List[str],
        diagnosis_codes: List[str]  # noqa: ARG002
    ) -> ComplianceAssessment:
        """
        Perform complete compliance validation.
        
        Args:
            state: Current workflow state
            service_codes: Requested service codes
            diagnosis_codes: Diagnosis codes
            
        Returns:
            ComplianceAssessment with gaps and recommendations
        """
        try:
            # Check documentation completeness
            doc_gaps = self._check_documentation_completeness(state, service_codes)
            
            # Assess PDPL compliance
            pdpl_assessment = self._assess_pdpl_compliance(state)
            
            # Check regulatory compliance
            regulatory_compliance = self._check_regulatory_compliance(state)
            
            # Calculate completion score
            completion_score = self._calculate_completion_score(doc_gaps, state)
            
            # Determine overall compliance level
            overall_level = self._determine_compliance_level(
                doc_gaps, pdpl_assessment, regulatory_compliance, completion_score
            )
            
            # Generate next steps
            next_steps = self._generate_next_steps(doc_gaps, pdpl_assessment, regulatory_compliance)
            
            # Estimate review time
            review_time = self._estimate_review_time(overall_level, doc_gaps)
            
            # Generate rationale
            rationale = self._generate_compliance_rationale(
                overall_level, doc_gaps, completion_score
            )
            
            return ComplianceAssessment(
                overall_level=overall_level,
                documentation_gaps=doc_gaps,
                pdpl_assessment=pdpl_assessment,
                regulatory_compliance=regulatory_compliance,
                completion_score=completion_score,
                next_steps=next_steps,
                estimated_review_time=review_time,
                rationale=rationale
            )
            
        except Exception as e:
            # Return minimal compliance assessment on error
            return ComplianceAssessment(
                overall_level=ComplianceLevel.MAJOR_ISSUES,
                documentation_gaps=[],
                pdpl_assessment=PDPLAssessment(
                    phi_elements_identified=[],
                    redaction_required=[],
                    consent_status="unknown",
                    data_retention_period="7 years per UAE healthcare standards"
                ),
                regulatory_compliance=RegulatoryCompliance(
                    dha_compliant=False,
                    doh_compliant=False,
                    licensing_valid=False,
                    provider_network_status="unknown",
                    regulatory_flags=[f"Compliance validation error: {str(e)}"]
                ),
                completion_score=0.0,
                next_steps=[f"Compliance system error: {str(e)}"],
                estimated_review_time="Unknown",
                rationale=f"Unable to complete compliance validation: {str(e)}"
            )
    
    def _check_documentation_completeness(
        self,
        state: PreAuthState,
        service_codes: List[str]
    ) -> List[DocumentationGap]:
        """Check for missing required documentation."""
        gaps = []
        
        # Check patient demographics
        patient_info = state.get('patient_info', {})
        if not patient_info or not patient_info.get('EmiratesIDNumber'):
            gaps.append(DocumentationGap(
                doc_type=DocumentationType.DIAGNOSTIC_CODES,
                description="Emirates ID number missing or invalid",
                requirement_level="required",
                next_steps="Provide valid UAE Emirates ID number",
                deadline_days=1
            ))
        
        # Check diagnosis codes
        if not patient_info or not patient_info.get('services'):
            gaps.append(DocumentationGap(
                doc_type=DocumentationType.DIAGNOSTIC_CODES,
                description="Service/procedure codes not specified",
                requirement_level="required",
                next_steps="Provide specific CPT/HCPCS service codes",
                deadline_days=1
            ))
        
        # Check justification
        if not patient_info or not patient_info.get('justification'):
            gaps.append(DocumentationGap(
                doc_type=DocumentationType.PROCEDURE_JUSTIFICATION,
                description="Medical necessity justification missing",
                requirement_level="required",
                next_steps="Provide detailed medical necessity justification",
                deadline_days=3
            ))
        elif len(patient_info.get('justification', '')) < 50:
            gaps.append(DocumentationGap(
                doc_type=DocumentationType.PROCEDURE_JUSTIFICATION,
                description="Medical necessity justification insufficient detail",
                requirement_level="required",
                next_steps="Expand justification with clinical details and treatment history",
                deadline_days=3
            ))
        
        # Check patient history availability
        patient_data = state.get('patient_data', {})
        if not patient_data:
            gaps.append(DocumentationGap(
                doc_type=DocumentationType.CLINICAL_NOTES,
                description="Patient medical history not available",
                requirement_level="required",
                next_steps="Provide access to patient medical history and records",
                deadline_days=7
            ))
        else:
            # Lab results check
            if not patient_data.get('labs') or len(patient_data['labs']) == 0:
                gaps.append(DocumentationGap(
                    doc_type=DocumentationType.LAB_RESULTS,
                    description="Recent laboratory results not available",
                    requirement_level="recommended",
                    next_steps="Upload recent lab results (within 6 months)",
                    deadline_days=14
                ))
            
            # Medication history check
            if not patient_data.get('medications') or len(patient_data['medications']) == 0:
                gaps.append(DocumentationGap(
                    doc_type=DocumentationType.MEDICATION_HISTORY,
                    description="Current medication list not available",
                    requirement_level="required",
                    next_steps="Provide current medication list with dosages and start dates",
                    deadline_days=7
                ))
        
        # Service-specific documentation requirements
        for service_code in service_codes:
            service_gaps = self._check_service_specific_documentation(service_code, state)
            gaps.extend(service_gaps)
        
        return gaps
    
    def _check_service_specific_documentation(
        self,
        service_code: str,
        state: PreAuthState
    ) -> List[DocumentationGap]:
        """Check documentation requirements specific to service codes."""
        gaps = []
        
        # Diabetes technology (CGM/Insulin Pump)
        if service_code in ["95250", "E0784"]:
            # HbA1c requirement
            if not self._has_recent_lab(state, "HbA1c", days=90):
                gaps.append(DocumentationGap(
                    doc_type=DocumentationType.LAB_RESULTS,
                    description="Recent HbA1c results required for diabetes technology",
                    requirement_level="required",
                    next_steps="Upload HbA1c results from last 3 months showing ≥7.0%",
                    deadline_days=14
                ))
            
            # Endocrinology consultation
            if not self._has_specialist_consultation(state, "endocrin"):
                gaps.append(DocumentationGap(
                    doc_type=DocumentationType.SPECIALIST_CONSULTATION,
                    description="Endocrinology consultation recommended for diabetes technology",
                    requirement_level="recommended",
                    next_steps="Obtain endocrinology consultation report",
                    deadline_days=30
                ))
        
        # Orthopedic procedures
        elif service_code in ["29881", "20610"]:
            # Recent imaging
            if not self._has_recent_imaging(state, "knee", days=180):
                gaps.append(DocumentationGap(
                    doc_type=DocumentationType.IMAGING_REPORTS,
                    description="Recent knee imaging required for orthopedic intervention",
                    requirement_level="required",
                    next_steps="Upload knee X-ray or MRI within last 6 months",
                    deadline_days=14
                ))
            
            # Physical therapy documentation
            gaps.append(DocumentationGap(
                doc_type=DocumentationType.CLINICAL_NOTES,
                description="Physical therapy trial documentation required",
                requirement_level="required",
                next_steps="Document 6+ weeks of physical therapy or contraindication",
                deadline_days=21
            ))
        
        # Neurological procedures (DBS)
        elif service_code in ["61885"]:
            # Movement disorders specialist
            if not self._has_specialist_consultation(state, "neurol"):
                gaps.append(DocumentationGap(
                    doc_type=DocumentationType.SPECIALIST_CONSULTATION,
                    description="Movement disorders specialist evaluation required for DBS",
                    requirement_level="required",
                    next_steps="Obtain movement disorders neurologist evaluation",
                    deadline_days=30
                ))
            
            # Cognitive assessment
            gaps.append(DocumentationGap(
                doc_type=DocumentationType.CLINICAL_NOTES,
                description="Cognitive assessment (MMSE/MoCA) required for DBS candidacy",
                requirement_level="required",
                next_steps="Complete cognitive assessment with MMSE ≥24 or MoCA ≥21",
                deadline_days=21
            ))
            
            # Brain MRI
            if not self._has_recent_imaging(state, "brain", days=180):
                gaps.append(DocumentationGap(
                    doc_type=DocumentationType.IMAGING_REPORTS,
                    description="Recent brain MRI required for DBS evaluation",
                    requirement_level="required",
                    next_steps="Upload brain MRI within last 6 months",
                    deadline_days=14
                ))
        
        return gaps
    
    def _assess_pdpl_compliance(self, state: PreAuthState) -> PDPLAssessment:
        """Assess UAE PDPL privacy compliance."""
        phi_elements = []
        redaction_required = []
        
        # Identify PHI elements in the request
        patient_info = state.get('patient_info', {})
        if patient_info:
            if patient_info.get('EmiratesIDNumber'):
                phi_elements.append("Emirates ID Number")
            
            # Check justification text for potential PHI
            justification = patient_info.get('justification', '')
            if self._contains_phi(justification):
                phi_elements.append("Justification text contains potential PHI")
                redaction_required.append("Redact specific personal identifiers in justification")
        
        # Check patient data for sensitive information
        patient_data = state.get('patient_data', {})
        if patient_data:
            if patient_data.get('demographics'):
                phi_elements.extend(["Patient demographics", "Address information"])
            
            if patient_data.get('labs'):
                phi_elements.append("Laboratory results with dates")
            
            if patient_data.get('medications'):
                phi_elements.append("Medication history")
        
        # Determine consent status from patient data or XML
        consent_status = self._check_consent_status(state)
        
        return PDPLAssessment(
            phi_elements_identified=phi_elements,
            redaction_required=redaction_required,
            consent_status=consent_status,
            data_retention_period="7 years per UAE healthcare standards",
            cross_border_transfer=False  # Assuming local processing
        )
    
    def _check_regulatory_compliance(self, state: PreAuthState) -> RegulatoryCompliance:
        """Check UAE regulatory compliance (DHA/DOH)."""
        regulatory_flags = []
        
        # Provider licensing check - extract from XML or lookup
        licensing_valid = self._check_provider_licensing(state)
        
        # Network status check - extract from XML or payer database
        provider_network_status = self._check_network_status(state)
        
        # DHA compliance (stub)
        xml_format = state.get('xml_format', 'unknown')
        dha_compliant = True
        if xml_format != "eclaim":
            regulatory_flags.append("Non-eClaimLink format may require DHA validation")
        
        # DOH compliance (stub)
        doh_compliant = True
        if xml_format != "shafafiya":
            regulatory_flags.append("Non-Shafafiya format may require DOH validation")
        
        # Format-specific checks
        if xml_format not in ["eclaim", "shafafiya"]:
            regulatory_flags.append("Unknown XML format - regulatory compliance uncertain")
            dha_compliant = False
            doh_compliant = False
        
        return RegulatoryCompliance(
            dha_compliant=dha_compliant,
            doh_compliant=doh_compliant,
            licensing_valid=licensing_valid,
            provider_network_status=provider_network_status,
            regulatory_flags=regulatory_flags
        )
    
    def _calculate_completion_score(
        self,
        gaps: List[DocumentationGap],
        state: PreAuthState
    ) -> float:
        """Calculate documentation completion score (0.0 to 1.0)."""
        
        # Base score from available data
        score = 0.0
        # total_possible = 1.0  # Future scoring implementation
        
        # Patient info completeness (30% weight)
        patient_info = state.get('patient_info', {})
        if patient_info:
            patient_score = 0.0
            if patient_info.get('EmiratesIDNumber'):
                patient_score += 0.4
            if patient_info.get('services'):
                patient_score += 0.3
            if patient_info.get('justification'):
                if len(patient_info['justification']) >= 50:
                    patient_score += 0.3
                else:
                    patient_score += 0.15
            score += patient_score * 0.3
        
        # Patient data completeness (40% weight)
        patient_data = state.get('patient_data', {})
        if patient_data:
            data_score = 0.0
            if patient_data.get('demographics'):
                data_score += 0.2
            if patient_data.get('labs') and len(patient_data['labs']) > 0:
                data_score += 0.3
            if patient_data.get('medications') and len(patient_data['medications']) > 0:
                data_score += 0.3
            if patient_data.get('claims') and len(patient_data['claims']) > 0:
                data_score += 0.2
            score += data_score * 0.4
        
        # Documentation gaps penalty (30% weight)
        required_gaps = [g for g in gaps if g.requirement_level == "required"]
        if len(required_gaps) == 0:
            score += 0.3
        else:
            penalty = min(len(required_gaps) * 0.1, 0.3)
            score += max(0, 0.3 - penalty)
        
        return min(score, 1.0)
    
    def _determine_compliance_level(
        self,
        gaps: List[DocumentationGap],
        pdpl_assessment: PDPLAssessment,  # noqa: ARG002
        regulatory_compliance: RegulatoryCompliance,
        completion_score: float
    ) -> ComplianceLevel:
        """Determine overall compliance level."""
        
        # Critical issues that warrant non-compliant status
        if not regulatory_compliance.dha_compliant and not regulatory_compliance.doh_compliant:
            return ComplianceLevel.NON_COMPLIANT
        
        # Count required vs recommended gaps
        required_gaps = [g for g in gaps if g.requirement_level == "required"]
        
        if len(required_gaps) >= 3:
            return ComplianceLevel.MAJOR_ISSUES
        elif len(required_gaps) >= 1 or completion_score < 0.6:
            return ComplianceLevel.MINOR_ISSUES
        else:
            return ComplianceLevel.COMPLIANT
    
    def _generate_next_steps(
        self,
        gaps: List[DocumentationGap],
        pdpl_assessment: PDPLAssessment,
        regulatory_compliance: RegulatoryCompliance
    ) -> List[str]:
        """Generate actionable next steps."""
        next_steps = []
        
        # Documentation gaps (prioritize required)
        required_gaps = [g for g in gaps if g.requirement_level == "required"]
        for gap in required_gaps[:3]:  # Top 3 required gaps
            next_steps.append(gap.next_steps)
        
        # PDPL requirements
        if pdpl_assessment.redaction_required:
            next_steps.extend(pdpl_assessment.redaction_required[:2])
        
        # Regulatory issues
        if regulatory_compliance.regulatory_flags:
            for flag in regulatory_compliance.regulatory_flags[:2]:
                next_steps.append(f"Address regulatory concern: {flag}")
        
        # Default if no specific steps
        if not next_steps:
            next_steps.append("Documentation review complete - proceed with medical evaluation")
        
        return next_steps
    
    def _estimate_review_time(
        self,
        compliance_level: ComplianceLevel,
        gaps: List[DocumentationGap]
    ) -> str:
        """Estimate time required to address compliance issues."""
        
        if compliance_level == ComplianceLevel.COMPLIANT:
            return "0-1 business days"
        elif compliance_level == ComplianceLevel.MINOR_ISSUES:
            return "1-3 business days"
        elif compliance_level == ComplianceLevel.MAJOR_ISSUES:
            # Look at deadlines
            max_deadline = max([g.deadline_days or 7 for g in gaps if g.deadline_days])
            return f"{max_deadline}-{max_deadline+3} business days"
        else:  # NON_COMPLIANT
            return "7-14 business days"
    
    def _generate_compliance_rationale(
        self,
        compliance_level: ComplianceLevel,
        gaps: List[DocumentationGap],
        completion_score: float
    ) -> str:
        """Generate compliance assessment rationale."""
        
        rationale_parts = []
        
        rationale_parts.append(f"Documentation completion score: {completion_score:.1%}")
        
        required_gaps = [g for g in gaps if g.requirement_level == "required"]
        if required_gaps:
            rationale_parts.append(f"{len(required_gaps)} required documentation gaps identified")
        
        recommended_gaps = [g for g in gaps if g.requirement_level == "recommended"]
        if recommended_gaps:
            rationale_parts.append(f"{len(recommended_gaps)} recommended improvements identified")
        
        if compliance_level == ComplianceLevel.COMPLIANT:
            rationale_parts.append("All required documentation criteria met")
        elif compliance_level == ComplianceLevel.MINOR_ISSUES:
            rationale_parts.append("Minor documentation gaps can be addressed quickly")
        elif compliance_level == ComplianceLevel.MAJOR_ISSUES:
            rationale_parts.append("Significant documentation required before approval")
        else:
            rationale_parts.append("Critical compliance issues must be resolved")
        
        return "Compliance assessment: " + "; ".join(rationale_parts)
    
    # Helper methods
    
    def _has_recent_lab(self, state: PreAuthState, lab_name: str, days: int = 90) -> bool:
        """Check if recent lab result is available."""
        patient_data = state.get('patient_data', {})
        if not patient_data or not patient_data.get('labs'):
            return False
        
        cutoff_date = datetime.now() - timedelta(days=days)
        for lab in patient_data['labs']:
            if lab_name.lower() in lab.get('name', '').lower():
                lab_date_str = lab.get('date')
                if lab_date_str:
                    try:
                        from dateutil import parser as date_parser
                        lab_date = date_parser.parse(lab_date_str)
                        if lab_date >= cutoff_date:
                            return True
                    except Exception:
                        continue
        return False
    
    def _has_recent_imaging(self, state: PreAuthState, body_part: str, days: int = 180) -> bool:
        """Check if recent imaging is available in clinical summary."""
        if 'clinical_summary' not in state:
            return False
        
        clinical_summary = state['clinical_summary']
        if not clinical_summary or not hasattr(clinical_summary, 'recent_imaging'):
            return False
        
        # Check recent imaging for matching body part
        for imaging in clinical_summary.recent_imaging:
            if body_part.lower() in imaging.get('description', '').lower():
                return True
        return False
    
    def _has_specialist_consultation(self, state: PreAuthState, specialty: str) -> bool:
        """Check if specialist consultation is documented in clinical data."""
        if 'clinical_summary' not in state:
            return False
        
        clinical_summary = state['clinical_summary']
        if not clinical_summary or not hasattr(clinical_summary, 'recent_procedures'):
            return False
        
        # Check for specialist consultation in procedures
        for procedure in clinical_summary.recent_procedures:
            if specialty.lower() in procedure.get('description', '').lower():
                return True
        return False
    
    def _check_consent_status(self, state: PreAuthState) -> str:
        """Check patient consent status from available data."""
        # Check if consent is documented in XML
        if 'xml_data' in state and state['xml_data']:
            xml_data = state['xml_data']
            # Look for consent fields in XML
            if hasattr(xml_data, 'get') and xml_data.get('consent_status'):
                return xml_data['consent_status']
        
        # Check canonical request for consent info
        if 'canonical_request' in state:
            canonical_request = state['canonical_request']
            if hasattr(canonical_request, 'patient') and canonical_request.patient.get('consent_given'):
                return "valid"
        
        # Default to assumed valid for existing patients with medical history
        if 'clinical_summary' in state and state['clinical_summary']:
            return "assumed_valid"
        
        return "unknown"
    
    def _check_provider_licensing(self, state: PreAuthState) -> bool:
        """Check if provider has valid licensing."""
        # Extract provider info from XML/canonical request
        if 'canonical_request' in state:
            canonical_request = state['canonical_request']
            if hasattr(canonical_request, 'provider'):
                provider_id = canonical_request.provider.get('license_number')
                if provider_id and len(provider_id) >= 6:  # Basic validation
                    return True
        
        # If no provider info found, default to valid for demo
        return True
    
    def _check_network_status(self, state: PreAuthState) -> str:
        """Check provider network status."""
        # Extract provider info from XML/canonical request
        if 'canonical_request' in state:
            canonical_request = state['canonical_request']
            if hasattr(canonical_request, 'provider'):
                provider_type = canonical_request.provider.get('type', '').lower()
                if 'government' in provider_type or 'dha' in provider_type:
                    return "in_network"
                elif 'private' in provider_type:
                    return "preferred_network"
        
        # Default assumption for demo
        return "in_network"
    
    def _contains_phi(self, text: str) -> bool:
        """Check if text contains potential PHI."""
        if not text:
            return False
        
        # Look for common PHI patterns
        for pattern in self.phi_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def _load_required_fields(self) -> Dict[str, List[str]]:
        """Load required field definitions."""
        return {
            "patient_info": [
                "EmiratesIDNumber", "services", "justification"
            ],
            "demographics": [
                "birth_date", "gender"
            ],
            "clinical_data": [
                "diagnosis_codes", "procedure_codes"
            ]
        }
    
    def _load_phi_patterns(self) -> List[str]:
        """Load PHI detection patterns."""
        return [
            r'\b784-\d{4}-\d{7}-\d\b',  # Emirates ID pattern
            r'\b\d{10,}\b',             # Long numbers
            r'\b[A-Za-z]+\s+[A-Za-z]+\b'  # Names (basic pattern)
        ]
    
    def _load_regulatory_requirements(self) -> Dict[str, Any]:
        """Load UAE regulatory requirements."""
        return {
            "dha_requirements": {
                "format": "eclaim",
                "provider_license": "required",
                "coding_standards": ["ICD-10", "CPT"]
            },
            "doh_requirements": {
                "format": "shafafiya", 
                "provider_license": "required",
                "coding_standards": ["ICD-10", "CPT"]
            }
        }


def validate_request_compliance(
    state: PreAuthState,
    service_codes: List[str],
    diagnosis_codes: List[str]
) -> ComplianceAssessment:
    """
    Main entry point for compliance validation.
    
    Args:
        state: Current workflow state
        service_codes: Requested service codes
        diagnosis_codes: Diagnosis codes
        
    Returns:
        ComplianceAssessment with gaps and next steps
    """
    validator = ComplianceValidator()
    return validator.validate_compliance(state, service_codes, diagnosis_codes)


if __name__ == "__main__":
    # Example usage and testing
    from preauth_system.state import create_initial_state
    
    # Create test state
    test_state = create_initial_state(
        xml_file_path="/test/path.xml",
        xml_format="eclaim"
    )
    
    # Validate compliance
    assessment = validate_request_compliance(
        state=test_state,
        service_codes=["95250"],
        diagnosis_codes=["E10.9"]
    )
    
    print(f"Compliance Level: {assessment.overall_level.value}")
    print(f"Completion Score: {assessment.completion_score:.1%}")
    print(f"Documentation Gaps: {len(assessment.documentation_gaps)}")
    print(f"Next Steps: {assessment.next_steps}")
    print(f"Rationale: {assessment.rationale}")