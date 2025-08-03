// Streamlined Healthcare Data Validation Functions
//
// This file contains streamlined BAML functions that consolidate the complex
// multi-function validation approach into 2 focused functions for better
// performance and cost-effectiveness.

// LLM input structure
// DataContext

// Single comprehensive validation function replacing 5 specialized functions
function ValidateHealthcareData(data_sample: DataSample) -> ValidationResult {
  client GPT4oMini
  prompt #"
    You are a healthcare data validation expert specializing in UAE healthcare systems and insurance processing.

    Analyze the following healthcare data comprehensively across ALL validation dimensions:

    Resource Type: {{ data_sample.resource_type }}
    Data: {{ data_sample.raw_data }}
    {% if data_sample.context %}
    Context:
    - Source System: {{ data_sample.context.source_system | default("Unknown") }}
    - Emirate: {{ data_sample.context.emirate | default("Unknown") }}
    - Provider Type: {{ data_sample.context.provider_type | default("Unknown") }}
    - Patient Category: {{ data_sample.context.patient_category | default("Unknown") }}
    {% endif %}

    Perform validation across these key areas:

    **1. UAE Healthcare Compliance:**
    - DHA (Dubai Health Authority) and DOH (Abu Dhabi Department of Health) regulatory compliance
    - Required authorization IDs and pre-approval workflows
    - Patient category compliance (UAE National, Resident, Visitor)
    - Cross-emirate referral protocols
    - PDPL (Personal Data Protection Law) compliance

    **2. Clinical Logic & Medical Relationships:**
    - ICD-10-AM diagnosis codes validity and appropriateness
    - CPT procedure codes alignment with diagnoses
    - Clinical workflow appropriateness and care coordination
    - Medical necessity and treatment appropriateness
    - Age/gender appropriateness of treatments

    **3. Data Quality & Completeness:**
    - Required fields presence and completeness
    - Data format consistency and validity
    - Value range appropriateness (dates, amounts, quantities)
    - Reference integrity between related data elements
    - Statistical outliers and anomaly detection

    **4. Medical Code Validation:**
    - ICD-10-AM code format and validity
    - CPT code format and validity
    - UAE-specific local coding compliance
    - Code version currency (not deprecated)
    - Proper code specificity and modifier usage

    **Analysis Guidelines:**
    - Focus on practical, actionable findings
    - Prioritize issues by severity and impact
    - Consider UAE healthcare context and regulations
    - Provide specific field-level feedback when possible
    - Suggest concrete improvements

    **Scoring Approach:**
    - Overall quality score: Weight critical issues heavily (50%), warnings moderately (30%), info lightly (20%)
    - Confidence: Base on data completeness and clarity of findings
    - Validation passed: True if no critical issues and quality score >= 0.7

    {{ ctx.output_format }}
  "#
}


// Test cases for the streamlined validation functions
test validation_excellent_quality {
  functions [ValidateHealthcareData]
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
              "patient_category": "UAE_National"
            }
          ]
        }
      "#
      context {
        source_system "eClaimLink"
        emirate "Dubai"
        provider_type "Clinic"
        patient_category "UAE_National"
      }
    }
  }
}

test validation_multiple_issues {
  functions [ValidateHealthcareData]
  args {
    data_sample {
      resource_type "Claims"
      raw_data #"
        {
          "claims": [
            {
              "claim_id": "CLM-ISSUES-001",
              "patient_id": "PAT-456",
              "provider_id": "UNLICENSED-PROV-123",
              "diagnosis_code": "250.00",
              "procedure_code": "INVALID",
              "amount": 15000.00,
              "currency": "USD",
              "service_date": "2025-06-15",
              "emirate": "Unknown",
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
      }
    }
  }
}