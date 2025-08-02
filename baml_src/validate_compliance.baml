// UAE Healthcare Compliance Validation Function with Tests

// Function to validate compliance with UAE healthcare regulations
function ValidateCompliance(data_sample: DataSample) -> LLMValidationResult {
  client ParallelValidator
  prompt #"
    You are a UAE healthcare compliance expert specializing in Dubai Health Authority (DHA) and Abu Dhabi Department of Health (DOH) regulations.

    Analyze the following healthcare data for compliance with UAE regulations:

    Resource Type: {{ data_sample.resource_type }}
    Data: {{ data_sample.raw_data }}
    {% if data_sample.context %}
    Context:
    - Source System: {{ data_sample.context.source_system }}
    - Emirate: {{ data_sample.context.emirate }}
    - Provider Type: {{ data_sample.context.provider_type }}
    - Patient Category: {{ data_sample.context.patient_category }}
    {% endif %}

    Check for compliance with UAE healthcare regulations including:

    1. **Authorization Requirements**:
       - Valid authorization IDs for pre-authorization claims
       - Proper DHA/DOH approval workflows
       - Required documentation for high-value procedures

    2. **Provider Licensing**:
       - Valid provider licenses for the specified emirate
       - Scope of practice compliance
       - Facility accreditation requirements

    3. **Patient Categories**:
       - Proper patient classification (UAE National, Resident, Visitor)
       - Insurance eligibility verification
       - Emergency vs. planned care protocols

    4. **Emirate-Specific Rules**:
       - Dubai (DHA) specific requirements
       - Abu Dhabi (DOH) specific requirements
       - Cross-emirate referral protocols

    5. **Data Privacy (PDPL)**:
       - Patient data handling compliance
       - Consent requirements
       - Data minimization principles

    6. **Billing and Claims**:
       - Proper coding requirements (ICD-10-AM, CPT)
       - Price transparency regulations
       - Fraud prevention measures

    Return your analysis in the specified format, identifying:
    - Compliance violations with specific regulation references
    - Missing required fields or documentation
    - Severity levels for each issue
    - Actionable recommendations for compliance

    Focus on practical, actionable findings that can be addressed by healthcare providers.

    {{ ctx.output_format }}
  "#
}

// Test cases for ValidateCompliance function
test compliance_dubai_complete_claim {
  functions [ValidateCompliance]
  args {
    data_sample {
      resource_type "Claims"
      raw_data #"
        {
          "claims": [
            {
              "claim_id": "DHA-CLM-2024-001",
              "patient_id": "UAE-PAT-123456",
              "provider_id": "DHA-PROV-789",
              "authorization_id": "DHA-AUTH-2024-001",
              "diagnosis_code": "E11.9",
              "procedure_code": "99213",
              "amount": 150.50,
              "currency": "AED",
              "service_date": "2024-12-01",
              "emirate": "Dubai",
              "patient_category": "UAE_National",
              "provider_license": "DHA-LIC-2024-VALID",
              "facility_accreditation": "DHA-FAC-ACC-2024"
            }
          ]
        }
      "#
      context {
        source_system "eClaimLink"
        emirate "Dubai"
        provider_type "Private_Clinic"
        patient_category "UAE_National"
        processing_date "2024-12-01T10:00:00Z"
        claim_type "Medical"
      }
    }
  }
}

test compliance_missing_authorization {
  functions [ValidateCompliance]
  args {
    data_sample {
      resource_type "Claims"
      raw_data #"
        {
          "claims": [
            {
              "claim_id": "CLM-NO-AUTH-001",
              "patient_id": "PAT-456789",
              "provider_id": "PROV-UNLICENSED",
              "diagnosis_code": "Z51.11",
              "procedure_code": "96413",
              "amount": 5000.00,
              "currency": "AED",
              "service_date": "2024-12-01",
              "emirate": "Dubai",
              "patient_category": "Visitor"
            }
          ]
        }
      "#
      context {
        source_system "CSV"
        emirate "Dubai"
        provider_type "Hospital"
        patient_category "Visitor"
        processing_date "2024-12-01T14:30:00Z"
        claim_type "High_Value_Procedure"
      }
    }
  }
}

test compliance_cross_emirate_referral {
  functions [ValidateCompliance]
  args {
    data_sample {
      resource_type "Claims"
      raw_data #"
        {
          "claims": [
            {
              "claim_id": "CROSS-EMI-001",
              "patient_id": "UAE-RES-789012",
              "provider_id": "DOH-PROV-456",
              "referring_provider_id": "DHA-PROV-123",
              "authorization_id": "DOH-REF-2024-001",
              "diagnosis_code": "C78.00",
              "procedure_code": "77301",
              "amount": 8500.00,
              "currency": "AED",
              "service_date": "2024-12-02",
              "emirate": "Abu Dhabi",
              "referring_emirate": "Dubai",
              "patient_category": "UAE_Resident",
              "emergency_designation": false
            }
          ]
        }
      "#
      context {
        source_system "Shafafiya"
        emirate "Abu Dhabi"
        provider_type "Specialized_Hospital"
        patient_category "UAE_Resident"
        processing_date "2024-12-02T09:15:00Z"
        claim_type "Specialty_Referral"
      }
    }
  }
}
