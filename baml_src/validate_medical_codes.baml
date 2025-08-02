// Medical Code Validation Function with Tests

// Function to validate medical codes against standard coding systems
function ValidateMedicalCodes(data_sample: DataSample) -> LLMValidationResult {
  client ParallelValidator
  prompt #"
    You are a medical coding specialist with expertise in ICD-10-AM, CPT, SNOMED CT, and UAE-specific coding requirements.

    Validate the medical codes in the following healthcare data:

    Resource Type: {{ data_sample.resource_type }}
    Data: {{ data_sample.raw_data }}
    {% if data_sample.context %}
    Context:
    - Source System: {{ data_sample.context.source_system }}
    - Emirate: {{ data_sample.context.emirate }}
    {% endif %}

    Validate codes across these coding systems:

    1. **ICD-10-AM Validation** (Primary in UAE):
       - Valid ICD-10-AM code format and structure
       - Codes exist in current version
       - Appropriate specificity level
       - Correct use of combination codes
       - Valid laterality and encounter type modifiers

    2. **CPT Code Validation**:
       - Valid CPT code format (5-digit numeric)
       - Codes are current and not deleted
       - Appropriate modifiers applied
       - Bundling rules compliance
       - Category I, II, III code usage

    3. **SNOMED CT Validation**:
       - Valid SNOMED CT concept IDs
       - Appropriate hierarchy relationships
       - Current terminology version
       - Correct semantic tags

    4. **LOINC Code Validation**:
       - Valid LOINC codes for laboratory results
       - Appropriate units and reference ranges
       - Correct method and specimen type codes

    5. **UAE Local Codes**:
       - DHA local coding system compliance
       - DOH Abu Dhabi specific codes
       - Emirates-specific procedure codes
       - Local pharmacy and medication codes

    6. **Code Relationships**:
       - Primary-secondary diagnosis code relationships
       - Procedure-diagnosis code compatibility
       - Cross-reference accuracy between coding systems

    7. **Coding Quality**:
       - Appropriate code specificity
       - Complete coding (no unspecified codes when specific codes available)
       - Proper use of combination vs. separate codes
       - Correct sequencing of multiple codes

    8. **Version and Currency**:
       - Codes are from the correct version year
       - Deprecated codes identification
       - New code adoptions

    Focus on identifying:
    - Invalid or non-existent codes
    - Deprecated or outdated codes
    - Inappropriate code usage
    - Missing required modifiers
    - Coding compliance with UAE standards

    {{ ctx.output_format }}
  "#
}

// Test cases for ValidateMedicalCodes function
test medical_codes_valid_standard_codes {
  functions [ValidateMedicalCodes]
  args {
    data_sample {
      resource_type "Claims"
      raw_data #"
        {
          "claims": [
            {
              "claim_id": "CLM-VALID-001",
              "patient_id": "PAT-123",
              "provider_id": "PROV-456",
              "diagnosis_codes": ["E11.9", "I10", "Z51.11"],
              "procedure_codes": ["99213", "83036", "85025"],
              "loinc_codes": ["4548-4", "2345-7"],
              "snomed_codes": ["44054006", "38341003"],
              "rxnorm_codes": ["860975", "617314"],
              "service_date": "2024-12-01",
              "coding_version": "ICD-10-AM-11th-Edition-2024"
            }
          ]
        }
      "#
      context {
        source_system "eClaimLink"
        emirate "Dubai"
      }
    }
  }
}

test medical_codes_invalid_deprecated_codes {
  functions [ValidateMedicalCodes]
  args {
    data_sample {
      resource_type "Claims"
      raw_data #"
        {
          "claims": [
            {
              "claim_id": "CLM-INVALID-001",
              "patient_id": "PAT-789",
              "provider_id": "PROV-123",
              "diagnosis_codes": ["250.00", "401.9", "V58.11"],
              "procedure_codes": ["12345", "00000", "INVALID"],
              "loinc_codes": ["0000-0", "INVALID-LOINC"],
              "snomed_codes": ["12345", "INVALID-SNOMED"],
              "modifier_codes": ["XX", "ZZ"],
              "service_date": "2024-12-01",
              "coding_version": "ICD-9-CM-2015"
            }
          ]
        }
      "#
      context {
        source_system "CSV"
        emirate "Abu Dhabi"
      }
    }
  }
}

test medical_codes_uae_local_codes {
  functions [ValidateMedicalCodes]
  args {
    data_sample {
      resource_type "Claims"
      raw_data #"
        {
          "claims": [
            {
              "claim_id": "CLM-UAE-001",
              "patient_id": "UAE-PAT-456",
              "provider_id": "DHA-PROV-789",
              "diagnosis_codes": ["E11.9"],
              "procedure_codes": ["99213"],
              "dha_local_codes": ["DHA-PROC-2024-001", "DHA-DIAG-2024-002"],
              "doh_local_codes": ["DOH-LAB-2024-001"],
              "emirates_pharmacy_codes": ["UAE-MED-2024-123"],
              "local_facility_codes": ["DXB-FAC-001"],
              "service_date": "2024-12-01",
              "emirate": "Dubai",
              "cross_emirates_codes": {
                "origin": "Dubai",
                "destination": "Abu Dhabi",
                "referral_code": "CROSS-REF-2024-001"
              }
            }
          ]
        }
      "#
      context {
        source_system "eClaimLink"
        emirate "Dubai"
      }
    }
  }
}
