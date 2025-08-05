# XML Processing System

## Overview
Processes UAE healthcare XML data from eClaimLink (Dubai) and Shafafiya (Abu Dhabi) into a canonical JSON format with integrated data quality validation.

## Supported Formats

### eClaimLink (Dubai Health Authority)
- **Root Element**: `PriorAuthorizationRequest`
- **Key Sections**: Header, Patient, Provider, JustificationText, ServiceRequests
- **Purpose**: Prior authorization requests from healthcare providers

### Shafafiya (Abu Dhabi Department of Health)
- **Root Element**: `Prior.Authorization`
- **Key Sections**: Header, Patient, Provider, AuthorizationRequest, RequestedService
- **Purpose**: Prior authorization requests with clinical data

## Processing Flow
1. **XML Parsing**: UTF-8 encoding with xmltodict.
2. **Processor Selection**: Use `EclaimLinkProcessor` for eClaimLink files and `ShafafiyaProcessor` for Shafafiya files.
3. **Field Extraction**: Patient, provider, and service/activity data is mapped to a canonical model.
4. **Bundle Creation**: A canonical bundle is created.
5. **Quality Validation**: Optional data quality assessment is performed.

## Usage
To use the processors, import the `EclaimLinkProcessor` and `ShafafiyaProcessor` classes from the `pipelines.xml_processor` module. Instantiate each processor, optionally enabling validation. Then, call the respective processing method (`process_eclaim_link` or `process_shafafiya`) with the path to the XML file. The processed data is returned as a dictionary containing the extracted information and quality reports.

## Output Structure
Canonical Bundle with:
- **Essential Fields**: authorization_id, patient, provider, services/activities
- **Clinical Data**: justification_text, clinical_info, medical_history
- **Quality Report**: validation scores and recommendations (if enabled)
- **Raw Data**: Complete original XML preserved for audit

## Key Features
- **Dual Format Support**: Dedicated processors for both eClaimLink and Shafafiya formats.
- **Patient Data Extraction**: Demographics, insurance, medical history.
- **Provider Information**: License details, contact info, facility data.
- **Service Mapping**: CPT codes, diagnosis codes, cost estimates.
- **Quality Validation**: Medical code validation and clinical logic checks.
- **Error Handling**: Graceful recovery with detailed logging.

## Testing
To run the system in debug mode, execute the `xml_processor.py` script from the project's root directory. This will process the sample files and generate debug output logs.

```bash
# Run debug mode from the project root
python3 pipelines/xml_processor.py
```

For unit testing, run `pytest` on the specific test file `tests/unit/test_xml_processor.py` to validate the functionality of the XML processors.

```bash
# Run tests
pytest tests/unit/test_xml_processor.py -v
```

## Sample Files
- `samples/eclaim_link_request.xml` - Complete eClaimLink authorization request
- `samples/shafafiya_prior_auth_request.xml` - Complete Shafafiya authorization request

Both samples include comprehensive patient demographics, insurance details, medical history, and service requests for dataset building and testing.