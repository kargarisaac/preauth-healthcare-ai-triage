// Comprehensive Validation Function with Tests

// Function to perform comprehensive parallel validation
function ComprehensiveValidation(data_sample: DataSample) -> UIFriendlyReport {
  client ParallelValidator
  prompt #"
    You are a comprehensive healthcare data validation system for UAE insurance platforms.

    Perform a complete validation analysis of the following healthcare data:

    Resource Type: {{ data_sample.resource_type }}
    Data: {{ data_sample.raw_data }}
    {% if data_sample.context %}
    Context:
    - Source: {{ data_sample.context.source_system }}
    - Emirate: {{ data_sample.context.emirate }}
    - Provider: {{ data_sample.context.provider_type }}
    - Patient: {{ data_sample.context.patient_category }}
    {% endif %}

    Perform validation across ALL these areas simultaneously:

    **1. UAE Compliance Validation**
    - DHA/DOH regulatory requirements
    - Authorization and licensing
    - Patient category compliance
    - PDPL data privacy compliance

    **2. Clinical Logic Assessment**
    - Diagnosis-procedure relationships
    - Medical coding consistency
    - Clinical workflow appropriateness
    - Care coordination logic

    **3. Data Quality Analysis**
    - Completeness and format validation
    - Pattern anomaly detection
    - Reference integrity checks
    - Value range validation

    **4. Medical Code Verification**
    - ICD-10-AM, CPT, SNOMED validation
    - UAE local coding compliance
    - Code relationship verification
    - Version currency checks

    Synthesize findings into a comprehensive, actionable report that:
    - Provides an overall quality assessment
    - Prioritizes issues by severity and impact
    - Groups related problems together
    - Offers specific, actionable recommendations
    - Considers the UAE healthcare context

    Create a user-friendly summary suitable for:
    - Healthcare administrators
    - Clinical staff
    - Compliance officers
    - Insurance processors

    Focus on practical next steps and clear explanations of why issues matter for patient care and regulatory compliance.

    {{ ctx.output_format }}
  "#
}

// Test cases for ComprehensiveValidation function
test comprehensive_validation_excellent_quality {
  functions [ComprehensiveValidation]
  args {
    data_sample {
      resource_type "Claims"
      raw_data #"
        {
          "claims": [
            {
              "claim_id": "DHA-CLM-2024-PERFECT",
              "patient_id": "UAE-NAT-123456",
              "provider_id": "DHA-PROV-PREMIUM-789",
              "authorization_id": "DHA-AUTH-2024-001",
              "diagnosis_codes": ["E11.9", "I10"],
              "procedure_codes": ["99213", "83036"],
              "amount": 275.50,
              "currency": "AED",
              "service_date": "2024-12-01",
              "pre_auth_date": "2024-11-28",
              "emirate": "Dubai",
              "patient_category": "UAE_National",
              "provider_license": "DHA-LIC-2024-VALID",
              "facility_accreditation": "DHA-FAC-ACC-2024",
              "care_team": ["endocrinologist", "nurse"],
              "emergency_designation": false,
              "follow_up_scheduled": true,
              "medication_reconciliation": "completed",
              "consent_documented": true,
              "pdpl_compliant": true
            }
          ]
        }
      "#
      context {
        source_system "eClaimLink"
        emirate "Dubai"
        provider_type "Specialty_Clinic"
        patient_category "UAE_National"
        processing_date "2024-12-01T10:00:00Z"
        claim_type "Chronic_Disease_Management"
      }
    }
  }
}

test comprehensive_validation_multiple_issues {
  functions [ComprehensiveValidation]
  args {
    data_sample {
      resource_type "Claims"
      raw_data #"
        {
          "claims": [
            {
              "claim_id": "CLM-ISSUES-001",
              "patient_id": "PAT-PROB-456",
              "provider_id": "UNLICENSED-PROV-123",
              "diagnosis_codes": ["250.00", "XXX.XX"],
              "procedure_codes": ["33533", "INVALID"],
              "amount": 15000.00,
              "currency": "USD",
              "service_date": "2025-06-15",
              "authorization_date": "2024-12-01",
              "emirate": "Unknown",
              "patient_category": "Visitor",
              "service_location": "outpatient_clinic",
              "anesthesia_type": "general",
              "emergency_designation": false,
              "consent_documented": false,
              "cross_emirates_referral": true,
              "referring_emirate": "Sharjah",
              "coding_version": "ICD-9-CM-2015"
            }
          ]
        }
      "#
      context {
        source_system "CSV"
        emirate "Dubai"
        provider_type "Cardiology_Clinic"
        patient_category "Visitor"
        processing_date "2024-12-01T14:30:00Z"
        claim_type "High_Value_Procedure"
      }
    }
  }
}

test comprehensive_validation_emergency_scenario {
  functions [ComprehensiveValidation]
  args {
    data_sample {
      resource_type "Claims"
      raw_data #"
        {
          "claims": [
            {
              "claim_id": "CLM-EMERG-CRITICAL",
              "patient_id": "PAT-EMERG-789",
              "provider_id": "ER-PROV-456",
              "diagnosis_codes": ["I46.9", "R57.0"],
              "procedure_codes": ["92950", "93005", "36415"],
              "amount": 12500.00,
              "currency": "AED",
              "service_date": "2024-12-01",
              "service_time": "02:30",
              "emirate": "Abu Dhabi",
              "patient_category": "UAE_Resident",
              "emergency_designation": true,
              "authorization_required": false,
              "care_team": ["emergency_physician", "cardiologist", "nurse", "pharmacist"],
              "disposition": "admitted_to_icu",
              "lab_results": ["troponin_elevated", "lactate_high"],
              "imaging": ["chest_xray_abnormal", "ecg_vfib"],
              "medications_administered": ["epinephrine", "amiodarone"],
              "consent_waived": "emergency_life_threatening",
              "next_of_kin_contacted": true,
              "quality_indicators": {
                "door_to_balloon_time": "45_minutes",
                "response_time": "3_minutes",
                "documentation_complete": true
              }
            }
          ]
        }
      "#
      context {
        source_system "Hospital_System"
        emirate "Abu Dhabi"
        provider_type "Emergency_Department"
        patient_category "UAE_Resident"
        processing_date "2024-12-01T08:00:00Z"
        claim_type "Emergency_Life_Threatening"
      }
    }
  }
}
