"""
Test cases for BAML agent output functions.

Tests the structured extraction and validation of agent responses
for the Pre-Authorization LangGraph workflow.
"""

import pytest
from baml_client import extract_clinical_analysis, extract_medication_analysis, extract_risk_assessment, extract_decision_making, extract_compliance_audit, integrate_final_decision


class TestClinicalAnalysisExtraction:
    """Test clinical analysis output extraction."""
    
    def test_extract_clinical_analysis_comprehensive(self):
        """Test comprehensive clinical analysis extraction."""
        agent_response = """
        Clinical Analysis Summary:
        The patient presents with Type 2 Diabetes Mellitus with poor glycemic control (HbA1c 8.2%). 
        Current management appears inadequate requiring intensification.

        Key Findings:
        - Active Type 2 Diabetes with HbA1c 8.2% (target <7%)
        - Chronic condition requiring immediate intervention
        - Evidence of diabetic complications risk
        - Patient adherence to current regimen appears suboptimal

        Disease Progression:
        Progressive worsening over past 6 months with increasing glucose levels.
        Risk of microvascular complications if not addressed promptly.

        Current Health Status:
        Stable but requires immediate medication adjustment and closer monitoring.

        Clinical Necessity Score: 0.85 - High medical necessity for intervention

        Supporting Evidence:
        - Elevated HbA1c indicating poor control
        - Patient symptoms of polyuria and fatigue
        - Risk of complications without treatment intensification

        Concerns:
        - Risk of diabetic ketoacidosis
        - Progression to insulin dependence
        - Development of microvascular complications

        Recommendations:
        - Intensify diabetes management
        - Add SGLT-2 inhibitor or GLP-1 agonist
        - Increase monitoring frequency
        - Diabetes education reinforcement
        """
        
        result = extract_clinical_analysis(agent_response)
        
        assert result.summary is not None
        assert len(result.key_findings) > 0
        assert result.clinical_necessity_score > 0.8
        assert len(result.supporting_evidence) > 0
        assert len(result.concerns) > 0
        assert len(result.recommendations) > 0
    
    def test_extract_clinical_analysis_minimal(self):
        """Test clinical analysis extraction with minimal input."""
        agent_response = """
        Patient appears stable with no acute concerns identified.
        Routine follow-up appropriate.
        Clinical necessity score: 0.3
        """
        
        result = extract_clinical_analysis(agent_response)
        
        assert result.summary is not None
        assert result.clinical_necessity_score < 0.5


class TestMedicationAnalysisExtraction:
    """Test medication analysis output extraction."""
    
    def test_extract_medication_analysis_with_interactions(self):
        """Test medication analysis with drug interactions."""
        agent_response = """
        Medication Analysis Summary:
        Current regimen includes potential drug interactions requiring monitoring.
        
        Current Medications:
        - Warfarin 5mg daily
        - Amiodarone 200mg daily
        - Omeprazole 20mg daily
        
        Drug Interactions Identified:
        - Warfarin + Amiodarone: Major interaction, increased bleeding risk
        - Warfarin + Omeprazole: Moderate interaction, monitor INR closely
        
        Safety Concerns:
        - Warfarin: Monitor INR weekly, bleeding risk
        - Amiodarone: Monitor thyroid function, pulmonary toxicity risk
        
        Medication Necessity Score: 0.75 - High necessity with monitoring
        
        Alternatives:
        - Consider DOAC instead of warfarin
        - Alternative antiarrhythmic options available
        
        Cost-effectiveness:
        Current regimen cost-effective but requires intensive monitoring
        
        Monitoring:
        - Weekly INR monitoring required
        - Quarterly thyroid function tests
        - Annual pulmonary function testing
        """
        
        result = extract_medication_analysis(agent_response)
        
        assert result.summary is not None
        assert len(result.current_medications) >= 3
        assert len(result.drug_interactions) >= 2
        assert len(result.safety_concerns) > 0
        assert result.medication_necessity_score > 0.7
        assert len(result.therapeutic_alternatives) > 0
        assert len(result.monitoring_recommendations) > 0


class TestRiskAssessmentExtraction:
    """Test risk assessment output extraction."""
    
    def test_extract_risk_assessment_high_risk(self):
        """Test high-risk patient assessment extraction."""
        agent_response = """
        Risk Assessment Summary:
        Patient presents with multiple cardiovascular risk factors requiring intensive management.
        
        Overall Risk Level: HIGH
        
        Risk Factors:
        - Age >60: High impact, very likely progression
        - Diabetes: High impact, ongoing management needed
        - Smoking history: Moderate impact, possible complications
        
        Outcome Predictions:
        - Cardiovascular event: 0.25 probability within 5 years
        - Diabetic complications: 0.40 probability within 2 years
        
        Cost-Benefit Analysis:
        Early intervention cost-effective compared to treating complications
        
        Monitoring Required:
        - Monthly blood glucose monitoring
        - Quarterly HbA1c testing
        - Annual cardiovascular screening
        
        Risk Mitigation:
        - Aggressive diabetes control
        - Smoking cessation program
        - Regular exercise program
        
        Follow-up:
        - 3-month follow-up required
        - Specialist referral recommended
        """
        
        result = extract_risk_assessment(agent_response)
        
        assert result.summary is not None
        assert result.overall_risk_level.value == "HIGH"
        assert len(result.risk_factors) >= 3
        assert len(result.outcome_predictions) >= 2
        assert len(result.recommended_monitoring) > 0
        assert len(result.risk_mitigation_strategies) > 0


class TestDecisionMakingExtraction:
    """Test decision making output extraction."""
    
    def test_extract_decision_making_approved(self):
        """Test approved decision extraction."""
        agent_response = """
        Decision Analysis Summary:
        Based on comprehensive review, recommendation is APPROVAL with conditions.
        
        Decision: APPROVED
        Confidence Score: 0.87
        
        Medical Necessity:
        Clear evidence of medical necessity based on clinical deterioration
        
        Clinical Evidence:
        - Progressive disease requiring intervention
        - Conservative management has failed
        - Evidence-based treatment approach
        
        Cost Justification:
        Treatment cost-effective compared to alternative approaches
        
        Alternative Analysis:
        Less effective alternatives considered and ruled out
        
        Risk-Benefit Summary:
        Benefits significantly outweigh risks with appropriate monitoring
        
        Conditions for Approval:
        - Patient must complete diabetes education program
        - Monthly monitoring for first 3 months
        - Specialist supervision required
        
        Monitoring Requirements:
        - Weekly glucose monitoring
        - Monthly clinical assessments
        - Quarterly lab work
        
        Authorization Duration: 90 days
        
        Cost Analysis:
        Estimated total cost within reasonable limits for condition severity
        
        Appeals Considerations:
        Strong evidence supporting decision, low likelihood of successful appeal
        """
        
        result = extract_decision_making(agent_response)
        
        assert result.summary is not None
        assert result.decision_recommendation.value == "APPROVED"
        assert result.confidence_score > 0.8
        assert len(result.conditions_for_approval) > 0
        assert len(result.monitoring_requirements) > 0
        assert result.duration_of_authorization == 90


class TestComplianceAuditExtraction:
    """Test compliance audit output extraction."""
    
    def test_extract_compliance_audit_compliant(self):
        """Test compliant case extraction."""
        agent_response = """
        Compliance Audit Summary:
        All UAE regulatory requirements have been met for this pre-authorization request.
        
        Overall Compliance Status: COMPLIANT
        
        UAE Regulatory Checks:
        - DHA Medical Necessity Guidelines: COMPLIANT
        - Documentation requirements met
        - Prior authorization protocols followed
        - Insurance coverage guidelines satisfied
        
        Documentation Review:
        - Medical history: Required and provided, good quality
        - Diagnostic reports: Required and provided, comprehensive
        - Treatment plan: Required and provided, detailed
        - Specialist consultation: Not required for this case
        
        Policy Adherence Score: 0.92
        
        Compliance Gaps:
        None identified
        
        Remediation Actions:
        None required
        
        Audit Recommendations:
        - Continue current documentation standards
        - Maintain regular policy updates
        """
        
        result = extract_compliance_audit(agent_response)
        
        assert result.summary is not None
        assert result.overall_compliance_status.value == "COMPLIANT"
        assert result.policy_adherence_score > 0.9
        assert len(result.uae_regulatory_checks) > 0
        assert len(result.documentation_review) > 0


class TestFinalDecisionIntegration:
    """Test final decision integration."""
    
    def test_integrate_final_decision_approved(self):
        """Test final decision integration for approved case."""
        # This would require mock objects for all the input structures
        # For brevity, showing the test structure
        pass
        
    def test_integrate_final_decision_denied(self):
        """Test final decision integration for denied case."""
        # This would require mock objects for all the input structures
        # For brevity, showing the test structure
        pass


if __name__ == "__main__":
    pytest.main([__file__])