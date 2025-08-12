enum PreAuthDecision {
  APPROVED
  DENIED
  REQUIRES_REVIEW
}

class AgentAnalysis {
  agent_name string @description("Name of the agent that performed this analysis")
  success bool @description("Whether the agent completed successfully")
  response string? @description("The agent's analysis response")
  confidence float? @description("Confidence score from 0.0 to 1.0")
  error string? @description("Error message if agent failed")
}

class FinalPreAuthDecision {
  decision PreAuthDecision @description("Final pre-authorization decision")
  confidence float @description("Confidence score from 0.0 to 1.0 for this decision")
  rationale string @description("Detailed reasoning that synthesizes all agent analyses")
  key_factors string[] @description("List of key factors that influenced this decision")
  conditions string[] @description("Any conditions or requirements attached to this decision")
  risk_assessment string @description("Summary of clinical and financial risks identified")
  policy_compliance string @description("Assessment of compliance with insurance policies")
  recommendation string @description("Specific recommendation for the healthcare provider")
}

function FinalizePreAuthDecision(
  clinical_analysis: AgentAnalysis,
  medication_analysis: AgentAnalysis,
  risk_assessment: AgentAnalysis,
  decision_making: AgentAnalysis,
  compliance_audit: AgentAnalysis,
  patient_demographics: string,
  requested_services: string,
  clinical_context: string
) -> FinalPreAuthDecision {
  // client GPT4oMini
  // client GptOss20b
  client OpenaiFallback
  prompt #"
    You are a senior medical director responsible for making final pre-authorization decisions for UAE healthcare insurance. 

    Your role is to synthesize all the agent analyses provided and make a definitive decision about whether to approve, deny, or flag for review the requested medical services.

    ## Decision Criteria
    
    **APPROVED** - Grant authorization when:
    - Clinical need is clearly established and well-documented
    - Requested services are medically necessary and appropriate
    - Risk factors are manageable or outweighed by benefits
    - Policy compliance requirements are met
    - Cost-effectiveness is reasonable for the clinical benefit

    **DENIED** - Reject authorization when:
    - Clinical necessity is not established or insufficient documentation
    - Requested services are experimental, investigational, or not evidence-based
    - Unacceptable risk factors or contraindications present
    - Policy exclusions apply or coverage criteria not met
    - More appropriate/cost-effective alternatives available

    **REQUIRES_REVIEW** - Flag for manual review when:
    - Complex clinical scenario requiring specialist input
    - Conflicting analysis results or uncertain risk assessment
    - Policy interpretation requires clarification
    - High-cost services needing additional scrutiny
    - Incomplete information affecting decision confidence

    ## Analysis Integration Guidelines

    1. **Clinical Analysis**: Primary source for medical necessity and appropriateness
    2. **Medication Analysis**: Critical for drug interactions, dosing, and therapy optimization
    3. **Risk Assessment**: Key factor in benefit-risk analysis and safety considerations  
    4. **Decision Making**: Previous reasoning to validate or challenge
    5. **Compliance Audit**: Ensures regulatory and policy adherence

    ## UAE Healthcare Context

    Consider UAE-specific factors:
    - PDPL (Personal Data Protection Law) compliance
    - Dubai Health Authority and Abu Dhabi DOH guidelines
    - Cultural sensitivity and family dynamics in healthcare decisions
    - Local healthcare infrastructure and provider capabilities
    - Insurance policy terms specific to UAE market

    ## Output Requirements

    Provide a comprehensive decision that:
    - Clearly states the final decision with high confidence
    - Synthesizes insights from all agent analyses 
    - Identifies the most critical factors influencing the decision
    - Includes specific conditions or requirements if approved
    - Assesses both clinical and financial risks
    - Confirms policy compliance status
    - Offers actionable recommendations for the provider

    {{ ctx.output_format }}

    {{ _.role("user") }}

    ## Agent Analysis Results

    ### Clinical Analysis
    **Agent**: {{ clinical_analysis.agent_name }}
    **Status**: {% if clinical_analysis.success %}✅ Completed{% else %}❌ Failed{% endif %}
    **Result**: {% if clinical_analysis.success %}{{ clinical_analysis.response }}{% else %}Error: {{ clinical_analysis.error }}{% endif %}
    {% if clinical_analysis.confidence %}**Confidence**: {{ clinical_analysis.confidence }}{% endif %}

    ### Medication Analysis  
    **Agent**: {{ medication_analysis.agent_name }}
    **Status**: {% if medication_analysis.success %}✅ Completed{% else %}❌ Failed{% endif %}
    **Result**: {% if medication_analysis.success %}{{ medication_analysis.response }}{% else %}Error: {{ medication_analysis.error }}{% endif %}
    {% if medication_analysis.confidence %}**Confidence**: {{ medication_analysis.confidence }}{% endif %}

    ### Risk Assessment
    **Agent**: {{ risk_assessment.agent_name }}
    **Status**: {% if risk_assessment.success %}✅ Completed{% else %}❌ Failed{% endif %}
    **Result**: {% if risk_assessment.success %}{{ risk_assessment.response }}{% else %}Error: {{ risk_assessment.error }}{% endif %}
    {% if risk_assessment.confidence %}**Confidence**: {{ risk_assessment.confidence }}{% endif %}

    ### Decision Making Analysis
    **Agent**: {{ decision_making.agent_name }}
    **Status**: {% if decision_making.success %}✅ Completed{% else %}❌ Failed{% endif %}
    **Result**: {% if decision_making.success %}{{ decision_making.response }}{% else %}Error: {{ decision_making.error }}{% endif %}
    {% if decision_making.confidence %}**Confidence**: {{ decision_making.confidence }}{% endif %}

    ### Compliance Audit
    **Agent**: {{ compliance_audit.agent_name }}
    **Status**: {% if compliance_audit.success %}✅ Completed{% else %}❌ Failed{% endif %}
    **Result**: {% if compliance_audit.success %}{{ compliance_audit.response }}{% else %}Error: {{ compliance_audit.error }}{% endif %}
    {% if compliance_audit.confidence %}**Confidence**: {{ compliance_audit.confidence }}{% endif %}

    ## Patient Context

    ### Demographics & Clinical Profile
    {{ patient_demographics }}

    ### Requested Services
    {{ requested_services }}

    ### Clinical Context
    {{ clinical_context }}

    ## Instructions

    Based on all the above analyses and context, provide your final pre-authorization decision. Ensure your reasoning clearly explains how you integrated the different agent analyses and why this decision best serves the patient's medical needs while maintaining appropriate risk management and policy compliance.

    {{ ctx.output_format }}
  "#
}