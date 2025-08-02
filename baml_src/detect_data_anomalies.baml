// Data Anomaly Detection Function with Tests

// Function to detect data anomalies and quality issues
function DetectDataAnomalies(data_sample: DataSample) -> LLMValidationResult {
  client ParallelValidator
  prompt #"
    You are a healthcare data quality analyst specializing in pattern recognition and anomaly detection.

    Analyze the following healthcare data for anomalies, inconsistencies, and quality issues:

    Resource Type: {{ data_sample.resource_type }}
    Data: {{ data_sample.raw_data }}
    {% if data_sample.context %}
    Context:
    - Source System: {{ data_sample.context.source_system }}
    - Processing Date: {{ data_sample.context.processing_date }}
    {% endif %}

    Detect anomalies across these categories:

    1. **Data Completeness**:
       - Required fields that are missing or empty
       - Optional fields that should be present given the context
       - Incomplete FHIR resource structures

    2. **Format and Structure Issues**:
       - Invalid date formats or impossible dates
       - Malformed identifiers or reference patterns
       - Incorrect data types for fields

    3. **Value Range Anomalies**:
       - Numerical values outside expected ranges
       - Unusual quantities or amounts
       - Suspicious patterns in monetary values

    4. **Reference Integrity**:
       - Broken references between resources
       - Circular reference patterns
       - Missing referenced resources

    5. **Pattern Anomalies**:
       - Unusual frequency patterns in service delivery
       - Anomalous provider behavior patterns
       - Statistical outliers in resource utilization

    6. **Consistency Issues**:
       - Conflicting information within the same record
       - Inconsistent formatting across similar fields
       - Version conflicts between related data elements

    7. **Duplicate Detection**:
       - Potential duplicate records or claims
       - Similar patients with different identifiers
       - Repeated procedures with identical details

    8. **Temporal Anomalies**:
       - Future dates in historical records
       - Impossible time sequences
       - Services provided outside business hours without emergency designation

    Flag unusual patterns, statistical outliers, and data that doesn't conform to expected healthcare data distributions.

    {{ ctx.output_format }}
  "#
}

// Test cases for DetectDataAnomalies function
test anomaly_detection_outlier_amounts {
  functions [DetectDataAnomalies]
  args {
    data_sample {
      resource_type "Claims"
      raw_data #"
        {
          "claims": [
            {
              "claim_id": "CLM-OUTLIER-001",
              "patient_id": "PAT-123",
              "provider_id": "PROV-456",
              "diagnosis_code": "Z00.00",
              "procedure_code": "99213",
              "amount": 50000.00,
              "currency": "AED",
              "service_date": "2024-12-01",
              "quantity": 1,
              "typical_range": "150-300 AED"
            },
            {
              "claim_id": "CLM-NORMAL-002",
              "patient_id": "PAT-789",
              "provider_id": "PROV-456",
              "diagnosis_code": "Z00.00",
              "procedure_code": "99213",
              "amount": 180.00,
              "currency": "AED",
              "service_date": "2024-12-01",
              "quantity": 1
            }
          ]
        }
      "#
      context {
        source_system "CSV"
        processing_date "2024-12-01T10:00:00Z"
      }
    }
  }
}

test anomaly_detection_temporal_issues {
  functions [DetectDataAnomalies]
  args {
    data_sample {
      resource_type "Claims"
      raw_data #"
        {
          "claims": [
            {
              "claim_id": "CLM-TIME-001",
              "patient_id": "PAT-TIME-123",
              "provider_id": "PROV-789",
              "diagnosis_code": "E11.9",
              "procedure_code": "99213",
              "amount": 150.00,
              "currency": "AED",
              "service_date": "2025-06-15",
              "authorization_date": "2024-12-01",
              "birth_date": "1990-05-20",
              "processing_date": "2024-12-01"
            },
            {
              "claim_id": "CLM-SEQ-002",
              "patient_id": "PAT-TIME-123",
              "provider_id": "PROV-789",
              "diagnosis_code": "E11.9",
              "procedure_code": "83036",
              "service_date": "2024-11-30",
              "result_date": "2024-11-25",
              "follow_up_scheduled": "2024-11-20"
            }
          ]
        }
      "#
      context {
        source_system "eClaimLink"
        processing_date "2024-12-01T14:00:00Z"
      }
    }
  }
}

test anomaly_detection_duplicate_patterns {
  functions [DetectDataAnomalies]
  args {
    data_sample {
      resource_type "Claims"
      raw_data #"
        {
          "claims": [
            {
              "claim_id": "CLM-DUP-001",
              "patient_id": "PAT-DUP-123",
              "provider_id": "PROV-456",
              "diagnosis_code": "M79.3",
              "procedure_code": "99213",
              "amount": 150.00,
              "service_date": "2024-12-01",
              "service_time": "10:00"
            },
            {
              "claim_id": "CLM-DUP-002",
              "patient_id": "PAT-DUP-456",
              "provider_id": "PROV-456",
              "diagnosis_code": "M79.3",
              "procedure_code": "99213",
              "amount": 150.00,
              "service_date": "2024-12-01",
              "service_time": "10:00",
              "patient_name": "Ahmed Al-Mansouri",
              "similar_demographics": true
            },
            {
              "claim_id": "CLM-DUP-003",
              "patient_id": "PAT-DUP-123",
              "provider_id": "PROV-456",
              "diagnosis_code": "M79.3",
              "procedure_code": "99213",
              "amount": 150.00,
              "service_date": "2024-12-01",
              "service_time": "10:05",
              "submission_time": "2024-12-01T15:30:00Z"
            }
          ]
        }
      "#
      context {
        source_system "CSV"
        processing_date "2024-12-01T16:00:00Z"
      }
    }
  }
}
