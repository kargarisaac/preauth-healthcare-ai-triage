# FHIR Resource Mapping Guide for UAE Healthcare Data

## Overview

This guide documents how XML data from eClaimLink and Shafafiya systems maps to the extended canonical FHIR resources in the Healthcare AI Pre-authorization Platform's healthcare bundle schema. The mapping supports 5 core FHIR resources: Claim, Observation, MedicationStatement, Condition, and Procedure.

## Schema Version: v0.2

**Bundle Structure**: All resources are contained within a FHIR Bundle resource type with `type: "collection"`

**Core Principle**: Each XML source element can contribute to multiple FHIR resources, and multiple XML elements may be consolidated into single FHIR resources through clinical intelligence and NLP processing.

---

## 1. Claim Resource Mapping

### eClaimLink XML → Claim FHIR

| **FHIR Field** | **eClaimLink XML Path** | **Data Type** | **Transformation Notes** |
|---|---|---|---|
| `id` | `PriorAuthorizationRequest/Header/TransactionID` | string | Direct mapping |
| `identifier[0].value` | `PriorAuthorizationRequest/Header/TransactionID` | string | Primary transaction identifier |
| `identifier[1].value` | `PriorAuthorizationRequest/Header/SenderID` | string | Sender identifier |
| `status` | `PriorAuthorizationRequest/Header/MessageStatus` | code | Map: "NEW" → "active", "CANCEL" → "cancelled" |
| `patient.reference` | `PriorAuthorizationRequest/Patient/PatientID` | Reference | Format: "Patient/{PatientID}" |
| `patient.identifier.value` | `PriorAuthorizationRequest/Patient/NationalID` | string | UAE National ID |
| `created` | `PriorAuthorizationRequest/Header/MessageDateTime` | dateTime | ISO 8601 format |
| `provider.reference` | `PriorAuthorizationRequest/Provider/ProviderID` | Reference | Format: "Organization/{ProviderID}" |
| `billablePeriod.start` | `PriorAuthorizationRequest/Authorization/StartDate` | dateTime | Authorization period start |
| `billablePeriod.end` | `PriorAuthorizationRequest/Authorization/EndDate` | dateTime | Authorization period end |
| `diagnosis[].diagnosisCodeableConcept` | `PriorAuthorizationRequest/Diagnosis/DiagnosisCode` | CodeableConcept | ICD-10-AM codes |
| `item[].productOrService` | `PriorAuthorizationRequest/Activities/ActivityCode` | CodeableConcept | CPT codes |
| `item[].unitPrice` | `PriorAuthorizationRequest/Activities/UnitPrice` | Money | AED currency |
| `supportingInfo[].valueString` | `PriorAuthorizationRequest/ClinicalJustification` | string | Clinical justification text |

### Shafafiya XML → Claim FHIR

| **FHIR Field** | **Shafafiya XML Path** | **Data Type** | **Transformation Notes** |
|---|---|---|---|
| `id` | `Prior.Authorization/MessageHeader/MessageControlID` | string | Direct mapping |
| `identifier[0].value` | `Prior.Authorization/MessageHeader/MessageControlID` | string | Primary identifier |
| `status` | Always "active" | code | Shafafiya doesn't provide status |
| `patient.reference` | `Prior.Authorization/Patient/PatientInformation/MemberID` | Reference | Format: "Patient/{MemberID}" |
| `created` | `Prior.Authorization/MessageHeader/DateTimeStamp` | dateTime | ISO 8601 format |
| `provider.reference` | `Prior.Authorization/Provider/ProviderID` | Reference | Format: "Organization/{ProviderID}" |
| `diagnosis[].diagnosisCodeableConcept` | `Prior.Authorization/DiagnosisInformation/DiagnosisCode` | CodeableConcept | ICD-10-AM codes |
| `item[].productOrService` | `Prior.Authorization/ServiceInformation/ServiceCode` | CodeableConcept | Local procedure codes |

---

## 2. Observation Resource Mapping

Observations are primarily **derived** from clinical text analysis and historical data inference, not directly mapped from XML structure fields.

### Data Sources for Observations:

#### From eClaimLink:
- **Source Field**: `PriorAuthorizationRequest/ClinicalJustification` (text analysis)
- **Extraction Method**: NLP medical entity recognition
- **Common Observations Extracted**:
  - Lab values (HbA1c, glucose, lipids)
  - Vital signs (BP, weight, BMI)
  - Clinical findings mentioned in text

#### From Shafafiya:
- **Source Field**: `Prior.Authorization/ClinicalInformation/Notes` (text analysis)
- **Extraction Method**: Medical NLP with Arabic language support

### Observation FHIR Mapping:

| **FHIR Field** | **Source** | **Transformation** |
|---|---|---|
| `id` | Generated | Format: "{ObservationType}-{SequenceNumber}" |
| `status` | Default "final" | For extracted historical data |
| `category` | Inferred from observation type | laboratory, vital-signs, survey, etc. |
| `code` | NLP extraction + code mapping | LOINC preferred, CPT secondary |
| `subject.reference` | From parent Claim | Same patient reference |
| `effectiveDateTime` | NLP date extraction | Parse dates from clinical text |
| `valueQuantity` | NLP value extraction | Extract numeric values with units |
| `interpretation` | Clinical rules | Apply reference ranges |
| `basedOn` | Reference to parent Claim | Link to authorization request |

### Example NLP Extractions:

**Input Text**: "Patient's last HbA1c was 8.5% on January 15th, indicating suboptimal diabetes control"

**Generated Observation**:
```json
{
  "resourceType": "Observation",
  "code": {
    "coding": [{"system": "http://loinc.org", "code": "4548-4", "display": "Hemoglobin A1c"}]
  },
  "effectiveDateTime": "2025-01-15T00:00:00Z",
  "valueQuantity": {"value": 8.5, "unit": "%"},
  "interpretation": [{"coding": [{"code": "H", "display": "High"}]}]
}
```

---

## 3. MedicationStatement Resource Mapping

Like Observations, MedicationStatements are primarily derived from clinical text analysis.

### Data Sources:

#### From eClaimLink:
- **Source Field**: `PriorAuthorizationRequest/ClinicalJustification`
- **Additional Source**: `PriorAuthorizationRequest/Activities/ActivityCode` (medication-related CPT codes)

#### From Shafafiya:
- **Source Field**: `Prior.Authorization/ClinicalInformation/Notes`
- **Additional Source**: Pharmacy benefit codes in service information

### MedicationStatement FHIR Mapping:

| **FHIR Field** | **Source** | **Transformation** |
|---|---|---|
| `id` | Generated | Format: "{MedicationName}-{Status}-{Sequence}" |
| `status` | Inferred from text | "active", "completed", "stopped" |
| `medicationCodeableConcept` | NLP + RxNorm mapping | Extract drug names, map to RxNorm |
| `subject.reference` | From parent Claim | Same patient reference |
| `effectiveDateTime` | NLP date extraction | Start date from clinical text |
| `dosage[].text` | Direct extraction | "500mg twice daily with meals" |
| `reasonCode` | Link to diagnosis codes | From Claim.diagnosis |
| `basedOn` | Reference to parent Claim | Link to authorization request |

### Example Medication Extractions:

**Input Text**: "Patient currently on Metformin 500mg BID with meals, well tolerated"

**Generated MedicationStatement**:
```json
{
  "resourceType": "MedicationStatement",
  "status": "active",
  "medicationCodeableConcept": {
    "coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": "6809", "display": "Metformin"}]
  },
  "dosage": [{"text": "500mg twice daily with meals"}]
}
```

---

## 4. Condition Resource Mapping

Conditions have both **direct mapping** from diagnosis codes and **enriched derivation** from clinical context.

### Direct Mapping from XML:

#### From eClaimLink:
| **FHIR Field** | **eClaimLink XML Path** | **Transformation** |
|---|---|---|
| `code` | `PriorAuthorizationRequest/Diagnosis/DiagnosisCode` | ICD-10-AM to FHIR CodeableConcept |
| `category` | Always "encounter-diagnosis" | Fixed value for claim diagnoses |
| `clinicalStatus` | Default "active" | Assume active for current claims |
| `verificationStatus` | Default "confirmed" | Assume confirmed for coded diagnoses |
| `subject.reference` | From Claim patient | Same patient reference |

#### From Shafafiya:
| **FHIR Field** | **Shafafiya XML Path** | **Transformation** |
|---|---|---|
| `code` | `Prior.Authorization/DiagnosisInformation/DiagnosisCode` | ICD-10-AM to FHIR CodeableConcept |

### Enriched Derivation:

**Source**: Clinical justification text analysis
**Method**: Medical NLP + clinical reasoning
**Enhanced Fields**:
- `severity`: Inferred from clinical descriptors
- `onsetDateTime`: Extracted from temporal expressions
- `evidence`: Links to supporting Observations
- `note`: Clinical context and management notes

### Example Condition Enhancement:

**XML Diagnosis Code**: E11.9 (Type 2 diabetes mellitus without complications)

**Enhanced FHIR Condition**:
```json
{
  "resourceType": "Condition",
  "code": {
    "coding": [{"system": "http://hl7.org/fhir/sid/icd-10-am", "code": "E11.9"}]
  },
  "severity": {"text": "Mild - well controlled with medication"},
  "evidence": [{"detail": [{"reference": "Observation/HbA1c-Previous-001"}]}],
  "note": [{"text": "Well-controlled Type 2 diabetes, regular monitoring required"}]
}
```

---

## 5. Procedure Resource Mapping

Procedures are derived from **historical service codes** and **clinical timeline reconstruction**.

### Data Sources:

#### From eClaimLink:
- **Primary**: `PriorAuthorizationRequest/Activities/ActivityCode` (CPT codes)
- **Secondary**: Clinical justification text (previous procedures mentioned)

#### From Shafafiya:
- **Primary**: `Prior.Authorization/ServiceInformation/ServiceCode`

### Procedure FHIR Mapping:

| **FHIR Field** | **Source** | **Transformation** |
|---|---|---|
| `id` | Generated | Format: "{ProcedureCode}-{Status}-{Sequence}" |
| `status` | Context-dependent | "completed" for historical, "preparation" for requested |
| `code` | CPT code mapping | CPT to FHIR CodeableConcept |
| `subject.reference` | From parent Claim | Same patient reference |
| `performedDateTime` | Timeline inference | Infer from clinical context |
| `reasonCode` | Link to diagnosis | From Claim.diagnosis |
| `basedOn` | Reference to parent Claim | For requested procedures |

### Historical vs. Requested Procedures:

**Requested Procedure** (from current authorization):
```json
{
  "status": "preparation",
  "basedOn": [{"reference": "Claim/PA-2025-000123"}],
  "performedDateTime": "2025-08-15T00:00:00Z"  // Future date
}
```

**Historical Procedure** (from clinical timeline):
```json
{
  "status": "completed",
  "performedDateTime": "2025-01-15T09:00:00Z",  // Past date
  "outcome": {"text": "Test completed successfully"}
}
```

---

## UAE-Specific Extensions

All resources include UAE-specific extensions for enhanced clinical decision support:

### Common Extensions:

| **Extension URL** | **Purpose** | **Applied To** |
|---|---|---|
| `https://healthcare-preauth.org/fhir/StructureDefinition/emirate-authority` | Emirates health authority | All resources |
| `https://healthcare-preauth.org/fhir/StructureDefinition/source-mapping` | XML source traceability | All resources |
| `https://healthcare-preauth.org/fhir/StructureDefinition/clinical-context-score` | AI confidence in clinical extraction | Observation, MedicationStatement |
| `https://healthcare-preauth.org/fhir/StructureDefinition/clinical-reasoning` | Clinical decision support scores | Condition, Bundle |
| `https://healthcare-preauth.org/fhir/StructureDefinition/data-quality-score` | Overall data quality assessment | Bundle, Claim |

### Source Mapping Extension Structure:

```json
{
  "url": "https://healthcare-preauth.org/fhir/StructureDefinition/source-mapping",
  "extension": [
    {
      "url": "source-field",
      "valueString": "PriorAuthorizationRequest/ClinicalJustification"
    },
    {
      "url": "extraction-method",
      "valueString": "NLP-medical-entity-recognition"
    },
    {
      "url": "confidence-score",
      "valueDecimal": 0.92
    }
  ]
}
```

---

## Clinical Intelligence Enhancement

### Multi-Resource Relationships:

The extended schema creates rich clinical context through resource relationships:

1. **Claim** → **Condition**: Primary diagnosis codes
2. **Condition** → **Observation**: Supporting evidence (lab results)
3. **Condition** → **MedicationStatement**: Treatment history
4. **Condition** → **Procedure**: Monitoring procedures
5. **Observation** → **Procedure**: Lab tests that generated results

### Example Clinical Timeline:

```
Patient Timeline for Type 2 Diabetes:
┌─────────────────────────────────────────────────────────────┐
│ 2020-03-15: Condition/Diabetes-E11.9-001 (onset)          │
│ 2025-01-01: MedicationStatement/Metformin-Current-001      │
│ 2025-01-15: Procedure/HbA1c-Previous-Procedure-001        │
│ 2025-01-15: Observation/HbA1c-Previous-001 (result: 8.5%) │
│ 2025-07-31: Claim/PA-2025-000123 (current authorization)  │
└─────────────────────────────────────────────────────────────┘
```

### Enhancement Scores:

- **Data Quality Score**: 0.95 (high-quality structured data)
- **Clinical Context Score**: 0.88 (good clinical correlation)
- **Enrichment Score**: 0.88 (significant enhancement over source)
- **AI Confidence**: 0.92 (high confidence in extractions)

---

## Implementation Guidelines

### 1. Processing Pipeline:

```python
def process_xml_to_fhir_bundle(xml_file_path):
    """
    Convert XML healthcare data to FHIR Bundle with enhanced resources
    """
    # Step 1: Parse and validate XML
    parsed_data = xml_ingestor.process(xml_file_path)
    
    # Step 2: Create primary Claim resource
    claim = create_claim_from_xml(parsed_data)
    
    # Step 3: Extract clinical context via NLP
    clinical_text = extract_clinical_justification(parsed_data)
    
    # Step 4: Generate derived resources
    observations = extract_observations_from_text(clinical_text, claim.patient)
    medications = extract_medications_from_text(clinical_text, claim.patient)
    
    # Step 5: Enhance conditions from diagnosis codes
    conditions = enhance_conditions_from_diagnosis(claim.diagnosis, clinical_text)
    
    # Step 6: Infer historical procedures
    procedures = infer_procedures_from_timeline(claim, observations)
    
    # Step 7: Create Bundle with relationships
    bundle = create_fhir_bundle([claim, *observations, *medications, *conditions, *procedures])
    
    return bundle
```

### 2. Validation Requirements:

- **FHIR R4 Compliance**: All resources must validate against FHIR R4 specification
- **UAE Extensions**: Required extensions must be present with valid values
- **Cross-References**: All resource references must resolve within the bundle
- **Clinical Consistency**: Derived resources must be clinically consistent with source data

### 3. Error Handling:

- **Missing Required Fields**: Generate warning logs, use default values where appropriate
- **Invalid Codes**: Flag for manual review, include original codes in notes
- **NLP Extraction Failures**: Mark resources with low confidence scores
- **Inconsistent Dates**: Apply clinical timeline rules for conflict resolution

This mapping guide ensures that the extended FHIR schema maximizes clinical intelligence while maintaining full traceability to source XML systems.