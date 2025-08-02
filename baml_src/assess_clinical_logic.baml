// Clinical Logic Assessment Function with Tests

// Function to assess clinical logic and medical relationships
function AssessClinicalLogic(data_sample: DataSample) -> LLMValidationResult {
  client ParallelValidator
  prompt #"
    You are a clinical validation expert with deep knowledge of medical coding, procedures, and clinical workflows.

    Analyze the following healthcare data for clinical logic and medical relationship validity:

    Resource Type: {{ data_sample.resource_type }}
    Data: {{ data_sample.raw_data }}
    {% if data_sample.context %}
    Context:
    - Source System: {{ data_sample.context.source_system }}
    - Provider Type: {{ data_sample.context.provider_type }}
    - Claim Type: {{ data_sample.context.claim_type }}
    {% endif %}

    Evaluate clinical logic across these dimensions:

    1. **Diagnosis-Procedure Relationships**:
       - ICD-10-AM diagnoses support the procedures performed
       - Procedures are clinically appropriate for the conditions
       - Sequence and timing of procedures make medical sense

    2. **Medical Coding Consistency**:
       - Primary and secondary diagnoses are compatible
       - Procedure codes align with diagnostic codes
       - Modifier codes are used appropriately

    3. **Clinical Workflows**:
       - Referral patterns are medically justified
       - Care team composition is appropriate
       - Service locations match procedure requirements

    4. **Temporal Logic**:
       - Service dates are chronologically consistent
       - Pre-authorization dates precede service dates
       - Follow-up timing is medically appropriate

    5. **Resource Utilization**:
       - Quantity and frequency of services are reasonable
       - Medication dosages and frequencies are appropriate
       - Lab values and ranges are clinically sensible

    6. **Care Coordination**:
       - Multi-provider coordination is evident
       - Specialty referrals are justified
       - Emergency vs. planned care designations are correct

    7. **Medical Necessity**:
       - Services provided are medically necessary
       - Appropriate level of care (inpatient vs. outpatient)
       - Resource intensity matches condition severity

    Identify clinical inconsistencies, impossible medical scenarios, and areas where clinical judgment appears compromised.

    {{ ctx.output_format }}
  "#
}

// Test cases for AssessClinicalLogic function
test clinical_logic_diabetes_management {
  functions [AssessClinicalLogic]
  args {
    data_sample {
      resource_type "Claims"
      raw_data #"
        {
          "claims": [
            {
              "claim_id": "CLM-DM-001",
              "patient_id": "PAT-DM-123",
              "provider_id": "ENDO-PROV-456",
              "diagnosis_code": "E11.9",
              "procedure_code": "99213",
              "service_date": "2024-12-01",
              "follow_up_codes": ["83036", "82947"],
              "medication_codes": ["860975"],
              "previous_visit": "2024-09-01",
              "hba1c_result": "7.2%",
              "care_team": ["endocrinologist", "diabetes_educator", "nutritionist"]
            }
          ]
        }
      "#
      context {
        source_system "eClaimLink"
        provider_type "Specialty_Clinic"
        claim_type "Chronic_Disease_Management"
      }
    }
  }
}

test clinical_logic_inconsistent_procedure {
  functions [AssessClinicalLogic]
  args {
    data_sample {
      resource_type "Claims"
      raw_data #"
        {
          "claims": [
            {
              "claim_id": "CLM-INCONSISTENT-001",
              "patient_id": "PAT-ERR-789",
              "provider_id": "CARDIO-PROV-123",
              "diagnosis_code": "M79.3",
              "procedure_code": "33533",
              "service_date": "2024-12-01",
              "service_location": "outpatient_clinic",
              "anesthesia_type": "general",
              "procedure_duration": "240_minutes",
              "pre_auth_date": "2024-11-30"
            }
          ]
        }
      "#
      context {
        source_system "CSV"
        provider_type "Cardiology_Clinic"
        claim_type "Surgical_Procedure"
      }
    }
  }
}

test clinical_logic_emergency_care_pathway {
  functions [AssessClinicalLogic]
  args {
    data_sample {
      resource_type "Claims"
      raw_data #"
        {
          "claims": [
            {
              "claim_id": "CLM-EMERG-001",
              "patient_id": "PAT-EMERG-456",
              "provider_id": "ER-PROV-789",
              "diagnosis_code": "I46.9",
              "procedure_codes": ["92950", "93005", "36415"],
              "service_date": "2024-12-01",
              "service_time": "02:30",
              "emergency_designation": true,
              "care_team": ["emergency_physician", "cardiologist", "nurse"],
              "disposition": "admitted_to_icu",
              "lab_results": ["troponin_elevated", "bnp_normal"],
              "imaging": ["chest_xray", "ecg_abnormal"]
            }
          ]
        }
      "#
      context {
        source_system "Hospital_System"
        provider_type "Emergency_Department"
        claim_type "Emergency_Care"
      }
    }
  }
}
