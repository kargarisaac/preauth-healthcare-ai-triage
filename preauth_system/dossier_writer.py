"""
Professional Medical Dossier Writer using DSPy Framework
Generates comprehensive medical narratives from structured pipeline outputs.
"""

import time
from typing import Dict, Any, List, Optional
import dspy
from loguru import logger

from preauth_system.signatures import FinalReportSignature, FinalReportOutput
from preauth_system.utils import get_module_lm, with_dspy_lm


class DossierWriter(dspy.Module):
    """
    Professional medical dossier writer that generates comprehensive reports
    from structured pre-authorization pipeline outputs.
    
    Designed for medical directors and clinical reviewers, providing:
    - Executive summary with key decision points
    - Clinical context and medical history
    - Policy compliance analysis with citations
    - Risk assessment and clinical reasoning
    - Clear next steps and recommendations
    """
    
    def __init__(self, language: str = "en"):
        """
        Initialize DossierWriter with language preference.
        
        Args:
            language: Target language ("en" for English, "ar" for Arabic - future)
        """
        super().__init__()
        self.language = language
        self.lm = get_module_lm("dossier_writer")
        self.report_generator = dspy.ChainOfThought(FinalReportSignature)
        
    def forward(
        self,
        clinical_summary: Dict[str, Any],
        checklist: Dict[str, Any], 
        decision: Dict[str, Any],
        evidence: List[Dict[str, Any]],
        patient_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate professional medical dossier from pipeline components.
        
        Args:
            clinical_summary: Clinical analysis and patient summary
            checklist: Policy evaluation results with criteria
            decision: Final authorization decision with rationale
            evidence: Supporting evidence and citations
            patient_context: Additional patient demographic/clinical context
            
        Returns:
            Structured dossier with executive summary, sections, and metadata
        """
        start_time = time.time()
        
        try:
            # Prepare structured input for LLM
            decision_data = self._prepare_decision_context(
                clinical_summary, checklist, decision, patient_context
            )
            
            agent_results = self._prepare_evidence_context(evidence, checklist)
            
            # Generate comprehensive report using FinalReportSignature
            with with_dspy_lm(self.lm):
                result = self.report_generator(
                    decision_data=decision_data,
                    agent_results=agent_results
                )
            
            # Extract structured output
            final_report: FinalReportOutput = result.final_report
            
            # Convert to pipeline-expected dossier format
            dossier = final_report.to_structured_dossier()
            
            # Add processing metadata
            processing_time = (time.time() - start_time) * 1000
            dossier["metadata"].update({
                "processing_time_ms": processing_time,
                "language": self.language,
                "generated_at": time.time(),
                "word_count": self._calculate_word_count(dossier),
                "cost_estimate_usd": self._estimate_cost(dossier)
            })
            
            logger.info(f"Dossier generated in {processing_time:.2f}ms")
            return dossier
            
        except Exception as e:
            logger.error(f"Dossier generation failed: {e}")
            return self._create_fallback_dossier(clinical_summary, decision, evidence)
    
    def _prepare_decision_context(
        self, 
        clinical_summary: Dict[str, Any],
        checklist: Dict[str, Any],
        decision: Dict[str, Any],
        patient_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Prepare decision context for LLM processing."""
        
        # Extract key clinical information
        clinical_exec = clinical_summary.get("executive_summary", "No clinical summary available")
        primary_diagnosis = clinical_summary.get("primary_diagnosis", {})
        risk_factors = clinical_summary.get("risk_factors", [])
        
        # Extract decision details
        decision_outcome = decision.get("outcome", "unknown")
        decision_reason = decision.get("reason_code", "unspecified")
        confidence_score = decision.get("confidence_score", 0)
        
        # Extract policy compliance
        compliance_score = checklist.get("overall_compliance_score", 0)
        policy_source = checklist.get("policy_source", "unknown")
        criteria_met = len([c for c in checklist.get("criteria", []) if c.get("status") == "met"])
        total_criteria = len(checklist.get("criteria", []))
        
        # Patient demographics (if available)
        patient_info = ""
        if patient_context:
            age = patient_context.get("age", "unknown")
            gender = patient_context.get("gender", "unknown")
            patient_info = f"Patient: {age} years old, {gender}. "
        
        context = f"""
CLINICAL SUMMARY:
{clinical_exec}

PATIENT CONTEXT:
{patient_info}Primary Diagnosis: {primary_diagnosis.get('code', 'N/A')} - {primary_diagnosis.get('description', 'Not specified')}
Risk Factors: {', '.join(risk_factors) if risk_factors else 'None identified'}

AUTHORIZATION DECISION:
Outcome: {decision_outcome.upper()}
Reason Code: {decision_reason}
Confidence: {confidence_score:.1%}

POLICY COMPLIANCE:
Policy: {policy_source}
Compliance Score: {compliance_score:.1%}
Criteria Met: {criteria_met}/{total_criteria}
Missing Documents: {', '.join(checklist.get('missing_documents', [])) if checklist.get('missing_documents') else 'None'}

LANGUAGE PREFERENCE: {self.language}
        """.strip()
        
        return context
    
    def _prepare_evidence_context(
        self, 
        evidence: List[Dict[str, Any]], 
        checklist: Dict[str, Any]
    ) -> str:
        """Prepare evidence and citations context for LLM processing."""
        
        # Process evidence sources and citations
        evidence_summary = []
        citations = []
        
        for idx, evt in enumerate(evidence, 1):
            source = evt.get("source", f"Evidence {idx}")
            content = evt.get("content", "No content available")
            citation = evt.get("citation", f"Ref {idx}")
            
            evidence_summary.append(f"[{citation}] {source}: {content[:200]}...")
            citations.append(f"{citation}: {source}")
        
        # Process policy criteria in detail
        criteria_analysis = []
        for criterion in checklist.get("criteria", []):
            criterion_name = criterion.get("criterion", "Unknown criterion")
            status = criterion.get("status", "unknown")
            rationale = criterion.get("rationale", "No rationale provided")
            required_evidence = criterion.get("required_evidence", [])
            
            criteria_analysis.append(
                f"• {criterion_name}: {status.upper()}\n"
                f"  Rationale: {rationale}\n"
                f"  Required Evidence: {', '.join(required_evidence) if required_evidence else 'Not specified'}"
            )
        
        context = f"""
SUPPORTING EVIDENCE:
{chr(10).join(evidence_summary) if evidence_summary else 'No evidence provided'}

POLICY CRITERIA ANALYSIS:
{chr(10).join(criteria_analysis) if criteria_analysis else 'No criteria evaluated'}

CITATIONS:
{chr(10).join(citations) if citations else 'No citations available'}

ADDITIONAL NOTES:
- Generate professional medical language appropriate for medical directors
- Include specific medical terminology and clinical reasoning
- Cite evidence using provided reference format
- Provide clear, actionable next steps
- Ensure compliance with UAE healthcare standards
        """.strip()
        
        return context
    
    def _calculate_word_count(self, dossier: Dict[str, Any]) -> int:
        """Calculate approximate word count for the generated dossier."""
        word_count = 0
        
        # Count words in executive summary
        exec_summary = dossier.get("executive_summary", "")
        word_count += len(exec_summary.split())
        
        # Count words in all sections
        for section in dossier.get("sections", []):
            content = section.get("content", "")
            word_count += len(content.split())
        
        return word_count
    
    def _estimate_cost(self, dossier: Dict[str, Any]) -> float:
        """Estimate cost based on content complexity and length."""
        word_count = dossier["metadata"]["word_count"]
        sections_count = dossier["metadata"]["sections_count"]
        
        # Base cost for LLM processing (estimated)
        base_cost = 0.01  # $0.01 base
        
        # Additional cost based on complexity
        word_cost = word_count * 0.0001  # $0.0001 per word
        section_cost = sections_count * 0.002  # $0.002 per section
        
        return min(0.02, base_cost + word_cost + section_cost)  # Cap at $0.02
    
    def _create_fallback_dossier(
        self,
        clinical_summary: Dict[str, Any],
        decision: Dict[str, Any],
        evidence: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create a basic fallback dossier when LLM generation fails."""
        
        decision_outcome = decision.get("outcome", "unknown")
        clinical_exec = clinical_summary.get("executive_summary", "Clinical summary unavailable")
        
        fallback_summary = f"""
AUTHORIZATION DECISION: {decision_outcome.upper()}

This case has been processed through the automated pre-authorization system. 
{clinical_exec}

Please review the supporting documentation and contact the medical review team 
for additional information if needed.
        """.strip()
        
        return {
            "executive_summary": fallback_summary,
            "sections": [
                {
                    "title": "System Notice",
                    "content": "This is a fallback report generated due to processing limitations. Please review manually.",
                    "type": "notice"
                }
            ],
            "citations": [f"Ref {idx+1}: {evt.get('source', 'Unknown')}" for idx, evt in enumerate(evidence[:3])],
            "language": self.language,
            "metadata": {
                "sections_count": 1,
                "has_citations": len(evidence) > 0,
                "complexity_score": 10,
                "processing_time_ms": 0,
                "word_count": len(fallback_summary.split()),
                "cost_estimate_usd": 0.0,
                "is_fallback": True
            }
        }


# Convenience function for direct usage
def generate_dossier(
    clinical_summary: Dict[str, Any],
    checklist: Dict[str, Any],
    decision: Dict[str, Any],
    evidence: List[Dict[str, Any]],
    patient_context: Optional[Dict[str, Any]] = None,
    language: str = "en"
) -> Dict[str, Any]:
    """
    Generate a professional medical dossier from pipeline outputs.
    
    Convenience function that creates a DossierWriter instance and generates
    a comprehensive medical report suitable for medical directors.
    
    Args:
        clinical_summary: Clinical analysis results
        checklist: Policy evaluation results  
        decision: Authorization decision
        evidence: Supporting evidence and citations
        patient_context: Optional patient demographics
        language: Target language (en/ar)
        
    Returns:
        Structured dossier with executive summary, sections, and metadata
    """
    writer = DossierWriter(language=language)
    return writer.forward(
        clinical_summary=clinical_summary,
        checklist=checklist,
        decision=decision,
        evidence=evidence,
        patient_context=patient_context
    )