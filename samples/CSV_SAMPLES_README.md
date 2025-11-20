# CSV Sample Files Documentation

This directory contains representative CSV datasets for testing the Healthcare AI Pre-authorization Platform CSV processing pipeline. Each file is designed to test specific aspects of healthcare data ingestion and FHIR conversion.

## Sample Files Overview

### 1. CMS DE-SynPUF Style Sample
**File:** `cms_claims_sample.csv`
**Size:** ~3KB, 20 records
**Purpose:** Mimics the structure of CMS Medicare synthetic claims data

**Key Features:**
- Standard Medicare claims format with realistic synthetic data
- Contains beneficiary IDs, claim IDs, provider numbers, diagnosis codes
- Includes both ICD-9 and ICD-10 diagnosis codes
- Financial data in US dollars (for comparison with UAE AED amounts)
- Multiple procedure codes per claim (HCPCS/CPT)
- Payment amounts and primary payer information

**Column Structure:**
- `DESYNPUF_ID`: Synthetic beneficiary identifier
- `CLM_ID`: Unique claim identifier
- `CLM_FROM_DT`/`CLM_THRU_DT`: Service date range
- `PRVDR_NUM`: Provider identifier
- `CLM_PMT_AMT`: Total claim payment amount
- `ICD_DGNS_CD1/2`: ICD diagnosis codes
- `HCPCS_CD_1/2`: Procedure codes
- `LINE_NCH_PMT_AMT_1/2`: Line-level payment amounts

**Expected Processing:** Should map to FHIR Claim resources with multiple diagnosis and procedure entries.

### 2. UAE Healthcare Sample
**File:** `uae_healthcare_sample.csv`
**Size:** ~6KB, 20 records
**Purpose:** Comprehensive UAE-specific healthcare data with realistic local patterns

**Key Features:**
- UAE Emirates authorities (DHA, ADHA) as data sources
- Arabic and English patient names (realistic UAE demographics)
- ICD-10-AM diagnosis codes (Australian modification used in UAE)
- AED currency amounts
- CPT procedure codes commonly used in UAE
- Approval status and authorization IDs
- Clinical notes in English with medical context

**Column Structure:**
- `patient_id`: UAE-style patient identifier (P2025xxx format)
- `emirate_authority`: DHA (Dubai) or ADHA (Abu Dhabi)
- `service_code`: CPT procedure codes
- `icd10_am_code`: ICD-10-AM diagnosis codes
- `amount_aed`: Service costs in UAE Dirhams
- `patient_name_arabic`/`patient_name_english`: Bilingual patient names
- `approval_status`: APPROVED/PENDING/DENIED
- `clinical_notes`: Medical justification text

**Expected Processing:** Should map to FHIR Claim with UAE-specific extensions for emirate authority and bilingual data.

### 3. Synthea Clinical Data Sample
**File:** `synthea_clinical_data.csv`
**Size:** ~7KB, 35+ records
**Purpose:** Multi-resource FHIR data covering all 6 core resource types

**Key Features:**
- Comprehensive patient records with multiple FHIR resource types
- Patient demographics, claims, service requests, observations, medications, conditions
- Realistic clinical relationships (diabetes → HbA1c tests → Metformin)
- LOINC codes for lab results and vital signs
- RxNorm codes for medications
- Structured to demonstrate FHIR resource relationships

**Resource Types Covered:**
- **Patient**: Demographics and basic information
- **Claim**: Authorization requests with financial data
- **ServiceRequest**: Individual service/procedure requests
- **Observation**: Lab results, vital signs, clinical measurements
- **MedicationStatement**: Current and historical medications
- **Condition**: Diagnoses and clinical conditions

**Expected Processing:** Should intelligently route data to appropriate FHIR resources based on `resource_type` column.

### 4. Edge Case Samples

#### 4A. Minimal Data Sample
**File:** `minimal_data_sample.csv`
**Size:** <1KB, 3 records
**Purpose:** Test processing with minimal required fields only

**Features:**
- Only essential columns: patient_id, claim_id, service_code, amount
- No optional fields, minimal data validation requirements
- Tests baseline processing capabilities

#### 4B. Malformed Sample
**File:** `malformed_sample.csv`
**Size:** <1KB, 10 records
**Purpose:** Test error handling and data cleaning capabilities

**Intentional Issues:**
- Mixed delimiters (comma and semicolon)
- Missing required fields (empty patient IDs, amounts)
- Malformed quotes and escaped characters
- Special characters and Unicode text
- Inconsistent data formatting

**Expected Processing:** Should handle gracefully with comprehensive error reporting and data quality scoring.

#### 4C. Mixed Data Types Sample
**File:** `mixed_data_types_sample.csv`
**Size:** ~2KB, 15 records
**Purpose:** Test intelligent data routing to multiple FHIR resource types

**Features:**
- Single CSV containing multiple resource types in rows
- `record_type` column to specify target FHIR resource
- Comprehensive clinical relationships across resource types
- Tests CSV processor's ability to handle heterogeneous data

#### 4D. Large File Sample
**File:** `large_file_sample.csv`
**Size:** ~3MB, 9,500+ records
**Purpose:** Test memory-efficient processing and performance

**Features:**
- Generated from UAE healthcare sample with realistic variations
- Tests batch processing capabilities
- Validates memory usage for large datasets
- Simulates real-world CSV file sizes from payer systems

## Data Quality & Validation Patterns

### Realistic Healthcare Relationships
- **Diabetes Management**: Patients with diabetes (E11.9) → HbA1c tests (83036) → Metformin medication
- **Hypertension Care**: Essential hypertension (I10) → Blood pressure monitoring → Lisinopril
- **Preventive Care**: Routine screenings → Age-appropriate procedures → Follow-up care

### UAE-Specific Patterns
- **Emirate Authorities**: Realistic distribution between DHA and ADHA
- **Cultural Names**: Arabic and English name pairs following UAE conventions
- **Medical Codes**: ICD-10-AM codes used in UAE healthcare system
- **Currency**: All amounts in AED (UAE Dirhams)

### Data Quality Testing
- **Completeness**: Mix of complete and incomplete records
- **Consistency**: Some inconsistent data patterns for validation testing
- **Accuracy**: Medically logical relationships between diagnoses and procedures
- **Timeliness**: Recent dates (2025) with realistic temporal relationships

## Expected Processing Outcomes

### FHIR Mapping Results
Each CSV should produce Bundle resources containing:
1. **Primary Claim resources** with financial and administrative data
2. **ServiceRequest resources** for individual procedures/services
3. **Patient references** (when demographic data available)
4. **Clinical context** through Observation, Condition, and MedicationStatement resources

### Data Quality Scores
- **High Quality (>0.9)**: Complete records with consistent medical relationships
- **Medium Quality (0.7-0.9)**: Minor missing fields or formatting issues
- **Low Quality (<0.7)**: Significant data issues requiring manual review

### UAE Extensions
UAE-specific samples should include:
- `emirate-authority` extension with DHA/ADHA values
- `quality-score` extension with calculated data quality metrics
- `clinical-reasoning` extension with AI-generated insights

## Usage in Testing

### Unit Tests
- Individual file processing validation
- FHIR resource generation verification
- Data quality scoring accuracy

### Integration Tests
- End-to-end CSV → FHIR conversion
- Batch processing performance
- Error handling and recovery

### Performance Tests
- Large file processing (large_file_sample.csv)
- Memory usage monitoring
- Processing time benchmarks

## File Maintenance

### Regenerating Large File
```bash
cd samples/
head -1 uae_healthcare_sample.csv > large_file_sample.csv
for i in {1..500}; do
    tail -n +2 uae_healthcare_sample.csv | \
    sed "s/P2025/P$(printf "%06d" $i)/g" | \
    sed "s/CLM-DHA-2025-/CLM-DHA-2025-$(printf "%04d" $i)-/g" | \
    sed "s/PA-2025-/PA-2025-$(printf "%06d" $i)-/g" >> large_file_sample.csv
done
```

### Validation Commands
```bash
# Check file formats
file *.csv

# Validate CSV structure
python -c "import pandas as pd; [print(f'{f}: {pd.read_csv(f).shape}') for f in ['cms_claims_sample.csv', 'uae_healthcare_sample.csv', 'synthea_clinical_data.csv']]"

# Test CSV processing
python pipelines/csv_processor.py samples/uae_healthcare_sample.csv
```

This comprehensive set of CSV samples provides thorough testing coverage for the Healthcare AI Pre-authorization Platform CSV processing pipeline, ensuring robust handling of real-world healthcare data scenarios.
