# Field Mappings Reference for Nazmito Healthcare Platform

## Overview

This document provides comprehensive field mapping specifications for transforming various healthcare data formats (XML, CSV) into the canonical FHIR Bundle structure used by Nazmito. It serves as the authoritative reference for data transformation rules and field correspondence.

## Canonical Bundle Structure

All processed healthcare data is transformed into a standardized Bundle structure:

```json
{
  "resourceType": "Bundle",
  "id": "bundle-{unique-id}",
  "type": "collection",
  "timestamp": "ISO-8601-datetime",
  "authorization_id": "string",
  "sender": "string",
  "receiver": "string",
  "patient_info": {
    "patient_id": "string",
    "demographics": {}
  },
  "services": [],
  "activities": [],
  "diagnosis_codes": [],
  "raw_data": {},
  "meta": {
    "source_format": "string",
    "source_file": "string",
    "processing_timestamp": "ISO-8601-datetime",
    "processor_version": "string",
    "quality_score": "number"
  }
}
```

## XML Format Mappings

### eClaimLink (Dubai Health Authority)

#### Core Identification Fields
| Bundle Field | eClaimLink XML Path | Data Type | Required | Notes |
|-------------|-------------------|-----------|----------|-------|
| `authorization_id` | `PriorAuthorizationRequest/Header/AuthorizationId` | string | Yes | Primary identifier |
| `sender` | `PriorAuthorizationRequest/Header/Sender` | string | Yes | Healthcare provider |
| `receiver` | `PriorAuthorizationRequest/Header/Receiver` | string | Yes | Insurance payer |
| `timestamp` | `PriorAuthorizationRequest/Header/Timestamp` | datetime | Yes | ISO 8601 format |

#### Patient Information
| Bundle Field | eClaimLink XML Path | Data Type | Required | Notes |
|-------------|-------------------|-----------|----------|-------|
| `patient_info.patient_id` | `PriorAuthorizationRequest/Patient/PatientId` | string | Yes | Unique patient identifier |
| `patient_info.demographics` | `PriorAuthorizationRequest/Patient/Demographics` | object | No | Complete demographics object |

#### Service/Activity Data
| Bundle Field | eClaimLink XML Path | Data Type | Required | Notes |
|-------------|-------------------|-----------|----------|-------|
| `services` | `PriorAuthorizationRequest/Activities/Activity` | array | Yes | List of all activities |
| `services[].sequence` | `Activity/@sequence` | number | Yes | Activity sequence number |
| `services[].code` | `Activity/ActivityCode` | string | Yes | CPT or local code |
| `services[].description` | `Activity/Description` | string | No | Service description |
| `services[].amount` | `Activity/Amount` | number | No | Service cost |
| `services[].currency` | `Activity/Amount/@currency` | string | No | Currency code (AED) |

#### Clinical Data
| Bundle Field | eClaimLink XML Path | Data Type | Required | Notes |
|-------------|-------------------|-----------|----------|-------|
| `diagnosis_codes` | `PriorAuthorizationRequest/DiagnosisCodes/Diagnosis` | array | No | ICD-10-AM codes |

### Shafafiya (Abu Dhabi Department of Health)

#### Core Identification Fields
| Bundle Field | Shafafiya XML Path | Data Type | Required | Notes |
|-------------|-------------------|-----------|----------|-------|
| `authorization_id` | `Prior.Authorization/Authorization.Details/AuthorizationNumber` | string | Yes | Primary identifier |
| `sender` | `Prior.Authorization/Authorization.Details/Provider` | string | Yes | Healthcare provider |
| `receiver` | `Prior.Authorization/Authorization.Details/Payer` | string | Yes | Insurance payer |
| `timestamp` | `Prior.Authorization/Authorization.Details/DateTime` | datetime | Yes | ISO 8601 format |

#### Patient Information
| Bundle Field | Shafafiya XML Path | Data Type | Required | Notes |
|-------------|-------------------|-----------|----------|-------|
| `patient_info.patient_id` | `Prior.Authorization/Patient.Info/PatientID` | string | Yes | Unique patient identifier |
| `patient_info.demographics` | `Prior.Authorization/Patient.Info/PatientData` | object | No | Complete patient data |

#### Service/Activity Data
| Bundle Field | Shafafiya XML Path | Data Type | Required | Notes |
|-------------|-------------------|-----------|----------|-------|
| `activities` | `Prior.Authorization/Clinical.Services/Service` | array | Yes | List of all services |
| `activities[].sequence` | `Service/@id` | number | Yes | Service ID as sequence |
| `activities[].code` | `Service/ServiceCode` | string | Yes | CPT or local code |
| `activities[].description` | `Service/ServiceName` | string | No | Service name |
| `activities[].amount` | `Service/Cost` | number | No | Service cost |

#### Clinical Data
| Bundle Field | Shafafiya XML Path | Data Type | Required | Notes |
|-------------|-------------------|-----------|----------|-------|
| `diagnosis_codes` | `Prior.Authorization/Clinical.History/Diagnosis` | array | No | ICD-10-AM codes |

## CSV Format Mappings

### Standard Claims CSV

#### Core Fields
| Bundle Field | CSV Column | Alternative Names | Data Type | Required | Transformation |
|-------------|------------|------------------|-----------|----------|----------------|
| `authorization_id` | `authorization_id` | `auth_id`, `claim_id`, `reference_number` | string | Yes | Direct mapping |
| `sender` | `provider_name` | `provider`, `sender`, `facility_name` | string | Yes | Direct mapping |
| `receiver` | `payer_name` | `payer`, `receiver`, `insurance_company` | string | Yes | Direct mapping |
| `timestamp` | `request_date` | `date`, `created_date`, `submission_date` | datetime | Yes | Parse to ISO 8601 |

#### Patient Information
| Bundle Field | CSV Column | Alternative Names | Data Type | Required | Transformation |
|-------------|------------|------------------|-----------|----------|----------------|
| `patient_info.patient_id` | `patient_id` | `member_id`, `subscriber_id` | string | Yes | Direct mapping |
| `patient_info.demographics.name` | `patient_name` | `name`, `full_name` | string | No | Direct mapping |
| `patient_info.demographics.dob` | `date_of_birth` | `dob`, `birth_date` | date | No | Parse to ISO date |
| `patient_info.demographics.gender` | `gender` | `sex` | string | No | Normalize (M/F) |

#### Service Data
| Bundle Field | CSV Column | Alternative Names | Data Type | Required | Transformation |
|-------------|------------|------------------|-----------|----------|----------------|
| `services[].code` | `service_code` | `procedure_code`, `cpt_code` | string | Yes | Direct mapping |
| `services[].description` | `service_description` | `procedure_name`, `service_name` | string | No | Direct mapping |
| `services[].amount` | `amount` | `cost`, `price`, `charge` | number | No | Parse as decimal |
| `services[].currency` | `currency` | - | string | No | Default to "AED" |
| `services[].quantity` | `quantity` | `units`, `count` | number | No | Default to 1 |

#### Clinical Data
| Bundle Field | CSV Column | Alternative Names | Data Type | Required | Transformation |
|-------------|------------|------------------|-----------|----------|----------------|
| `diagnosis_codes[].code` | `diagnosis_code` | `icd_code`, `primary_diagnosis` | string | No | Split on semicolon |
| `diagnosis_codes[].description` | `diagnosis_description` | `diagnosis_name` | string | No | Direct mapping |

### Clinical Observations CSV

#### Observation Data
| Bundle Field | CSV Column | Alternative Names | Data Type | Required | Transformation |
|-------------|------------|------------------|-----------|----------|----------------|
| `observations[].code` | `observation_code` | `test_code`, `lab_code` | string | Yes | Direct mapping |
| `observations[].value` | `value` | `result`, `measurement` | varies | Yes | Type-aware parsing |
| `observations[].unit` | `unit` | `units`, `uom` | string | No | Standardize units |
| `observations[].reference_range` | `reference_range` | `normal_range` | string | No | Direct mapping |
| `observations[].date` | `observation_date` | `test_date`, `result_date` | datetime | Yes | Parse to ISO 8601 |

### Medication CSV

#### Medication Data
| Bundle Field | CSV Column | Alternative Names | Data Type | Required | Transformation |
|-------------|------------|------------------|-----------|----------|----------------|
| `medications[].code` | `medication_code` | `drug_code`, `ndc_code` | string | Yes | Direct mapping |
| `medications[].name` | `medication_name` | `drug_name`, `generic_name` | string | No | Direct mapping |
| `medications[].dosage` | `dosage` | `dose`, `strength` | string | No | Direct mapping |
| `medications[].frequency` | `frequency` | `directions`, `sig` | string | No | Direct mapping |
| `medications[].start_date` | `start_date` | `prescribed_date` | date | No | Parse to ISO date |

## Data Transformation Rules

### String Normalization
- Trim whitespace from all string fields
- Convert empty strings to null
- Standardize case for coded values (uppercase for codes, title case for names)
- Remove special characters from identifiers

### Date/Time Handling
- Parse various date formats to ISO 8601
- Handle missing time components (default to midnight UTC)
- Validate date ranges (reject future dates for historical data)
- Support multiple input formats (MM/DD/YYYY, DD/MM/YYYY, YYYY-MM-DD)

### Numeric Processing
- Parse currency amounts as decimals with 2 decimal places
- Handle thousand separators (commas)
- Convert percentage strings to decimals
- Validate ranges for clinical values

### Code Standardization
- Validate CPT codes (5-digit numeric)
- Validate ICD-10-AM codes (format: Letter + 2-3 digits + optional decimal)
- Normalize currency codes to ISO 4217 (AED for UAE)
- Standardize gender codes (M/F/U for Unknown)

## Quality Assessment Rules

### Completeness Scoring
```python
def calculate_completeness_score(bundle_data):
    required_fields = [
        'authorization_id', 'sender', 'receiver', 'timestamp',
        'patient_info.patient_id'
    ]

    optional_fields = [
        'services', 'diagnosis_codes', 'patient_info.demographics'
    ]

    required_score = sum(1 for field in required_fields if get_nested_field(bundle_data, field)) / len(required_fields)
    optional_score = sum(1 for field in optional_fields if get_nested_field(bundle_data, field)) / len(optional_fields)

    return (required_score * 0.8) + (optional_score * 0.2)
```

### Validity Scoring
```python
def calculate_validity_score(bundle_data):
    validations = [
        validate_authorization_id_format(bundle_data.get('authorization_id')),
        validate_timestamp_format(bundle_data.get('timestamp')),
        validate_service_codes(bundle_data.get('services', [])),
        validate_diagnosis_codes(bundle_data.get('diagnosis_codes', [])),
        validate_amounts(bundle_data.get('services', []))
    ]

    return sum(validations) / len(validations)
```

## Error Handling Strategies

### Field Mapping Errors
- **Missing Required Fields**: Log warning, use default value if available
- **Invalid Data Types**: Attempt conversion, log warning if failed
- **Malformed Codes**: Keep original value, flag for manual review
- **Out-of-Range Values**: Cap to valid range, log transformation

### Recovery Strategies
- **Partial Data**: Process available fields, mark incomplete
- **Format Variations**: Use fuzzy matching for column names
- **Encoding Issues**: Attempt multiple encodings (UTF-8, Latin-1, Windows-1252)
- **Structure Changes**: Graceful degradation with logging

## Extension Mappings

### UAE-Specific Extensions
| Extension | Source Field | Purpose | Example Value |
|-----------|-------------|---------|---------------|
| `disposition-flag` | `disposition` or default | Environment indicator | "TEST", "PRODUCTION" |
| `emirate-authority` | Derived from sender/format | Regulatory authority | "DHA", "DOH", "MOH" |
| `quality-score` | Calculated | Data quality assessment | 0.95 |
| `clinical-reasoning` | Derived from clinical data | AI decision support | Complex object |

### Custom Field Handling
```python
def map_custom_fields(source_data, format_type):
    extensions = []

    # Add disposition flag
    disposition = source_data.get('disposition', 'PRODUCTION')
    extensions.append(create_disposition_extension(disposition))

    # Add authority based on format
    authority = get_authority_from_format(format_type)
    extensions.append(create_authority_extension(authority))

    # Add quality score
    quality_score = calculate_quality_score(source_data)
    extensions.append(create_quality_extension(quality_score))

    return extensions
```

## Validation Reference

### Required Field Validation
```python
REQUIRED_FIELDS = {
    'authorization_id': {
        'type': str,
        'pattern': r'^[A-Z]{2}-\d{4}-\d{6}$',
        'example': 'PA-2025-000123'
    },
    'sender': {
        'type': str,
        'min_length': 2,
        'max_length': 100
    },
    'receiver': {
        'type': str,
        'min_length': 2,
        'max_length': 100
    },
    'timestamp': {
        'type': 'datetime',
        'format': 'ISO 8601'
    }
}
```

### Code Validation
```python
CODE_VALIDATORS = {
    'cpt_codes': {
        'pattern': r'^\d{5}$',
        'description': '5-digit numeric CPT codes'
    },
    'icd10_am_codes': {
        'pattern': r'^[A-Z]\d{2}(\.\d{1,2})?$',
        'description': 'ICD-10-AM format: Letter + 2-3 digits + optional decimal'
    },
    'currency_codes': {
        'enum': ['AED', 'USD', 'EUR'],
        'default': 'AED'
    }
}
```

## Performance Considerations

### Mapping Optimization
- **Field Caching**: Cache expensive field transformations
- **Batch Processing**: Process multiple records efficiently
- **Memory Management**: Stream large datasets to avoid memory issues
- **Parallel Processing**: Use multiprocessing for large CSV files

### Indexing Strategy
- **Primary Keys**: Index on authorization_id for fast lookups
- **Temporal Queries**: Index on timestamp for date-range queries
- **Clinical Codes**: Index on service codes and diagnosis codes
- **Patient Queries**: Index on patient_id for patient-centric views

## Related Documentation

- **XML Processing Guide**: `/docs/xml_processing.md`
- **CSV Processing Guide**: `/docs/csv_processing.md`
- **Format Comparison**: `/docs/format_comparison.md`
- **FHIR Implementation**: `/docs/FHIR_GUIDE.md`
- **Architecture Overview**: `/docs/ARCHITECTURE.md`

For implementation examples and development commands, see `/CLAUDE.md`.
