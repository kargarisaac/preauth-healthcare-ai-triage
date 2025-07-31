# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Nazmito is an intelligent AI-powered pre-authorization platform for UAE healthcare insurance. It transforms manual pre-authorization processes into opportunities for cost savings, quality improvement, and enhanced patient outcomes by applying AI and clinical rules to enrich authorization decisions.

## Parallel Development

Try to prioritize parallel subagents as much as you can. only use sequential subagents when absolutely necessary and the task needs to be done after another one. This will help us to speed up the development process and get the most out of our resources.

## Commands and Development

### Package Management
- **Package Manager**: `uv` (ultra-fast Python package manager)
- **Install dependencies**: `uv pip install -r pyproject.toml`
- **Add new package**: `uv pip install <package_name>`
- **Create virtual environment**: `uv venv .venv && source .venv/bin/activate`

### Code Quality
- **Format code**: `black . --skip-string-normalization`
- **Lint code**: `ruff check . --fix`
- **Run pre-commit hooks**: `pre-commit run --all-files`

### Testing
- **Run all tests**: `pytest`
- **Run specific test file**: `pytest tests/test_xml_ingest.py`
- **Run tests with markers**: `pytest -m fhir` (clinical FHIR tests), `pytest -m unit` (unit tests), `pytest -m integration` (integration tests)
- **Run tests with coverage**: `pytest --cov=pipelines --cov-report=html`
- **Skip slow tests**: `pytest -m "not slow"`

### XML Processing Pipeline
- **Process sample files**: `python pipelines/factory.py` (comprehensive factory testing)
- **Debug eClaimLink**: `python pipelines/eclaim_link_ingestor.py` (standalone debugging)
- **Debug Shafafiya**: `python pipelines/shafafiya_ingestor.py` (standalone debugging)
- **Test format detection**: Use `XMLIngestorFactory.detect_format(file_path)`

### Running the Application
- **Run main script**: `python main.py`
- **Start demo environment**: `make demo` (if Makefile exists)

### Website Development
- **View website locally**:
  - Open directly: `open ui/index.html`
  - Or start server: `python3 -m http.server 8000` in ui directory
- **Legacy website**: Located in `legacy-website/` folder

## Architecture Overview

### High-Level System Design

Nazmito implements a **medallion architecture** with three data layers and AI-powered clinical intelligence:

1. **Bronze Layer**: Raw ingested data with immutable storage and SHA-256 hashing
2. **Silver Layer**: Cleaned, source-shaped data with basic validation  
3. **Gold Layer**: FHIR-compliant canonical schema with UAE extensions
4. **AI Layer**: Vector embeddings, knowledge graphs (KuzuDB), and LLM agents (LangGraph)

### Core Components

1. **XML Ingestion Pipeline** (`pipelines/`)
   - **Factory Pattern**: `XMLIngestorFactory` automatically detects format and creates appropriate ingestor
   - **Format-Specific Ingestors**: `EClaimLinkIngestor` (Dubai DHA) and `ShafafiyaIngestor` (Abu Dhabi DOH)
   - **Dual Output Modes**: Legacy format for backward compatibility, FHIR Bundle for enhanced clinical extraction
   - **Clinical Intelligence**: Extracts 5 FHIR resource types (Claim, Condition, Observation, MedicationStatement, Procedure)

2. **FHIR Clinical Extraction** (`pipelines/clinical_extraction_methods.py`)
   - **ClinicalExtractionMixin**: Medical NLP patterns for extracting clinical entities
   - **Text Analysis**: Processes justification/comments text for conditions, medications, observations, procedures
   - **Clinical Scoring**: Data quality, clinical context, enrichment, and AI confidence scores
   - **UAE Extensions**: Custom FHIR profiles for UAE healthcare compliance

3. **Schema and Validation** (`schemas/`)
   - **XSD Schemas**: `CommonTypes_20191113.xsd` (eClaimLink), `PriorAuthorization.xsd` (Shafafiya)
   - **Canonical Schema**: FHIR Bundle structure supporting all 5 resource types with UAE extensions
   - **Field Mappings**: Complete XML-to-FHIR mapping documentation

4. **Testing Infrastructure** (`tests/`)
   - **Comprehensive Fixtures**: Mock data factories, XML generators, FHIR validation helpers
   - **Test Categories**: Unit, integration, FHIR extraction, clinical NLP, performance tests
   - **Clinical Validation**: Specialized helpers for validating clinical data quality and FHIR compliance

### XML Processing Factory Pattern

The system uses a **factory pattern** for automatic format detection and processing:

```python
from pipelines.factory import XMLIngestorFactory

# Auto-detect format and process with legacy output
factory = XMLIngestorFactory(schema_base_path="schemas/")
result = factory.process_file("path/to/healthcare_data.xml")

# Create FHIR Bundle with clinical intelligence
ingestor = factory.create_ingestor("eClaimLink", output_format="fhir_bundle")
fhir_bundle = ingestor.ingest_file("samples/eclaim_link_request.xml")
```

**Key Architectural Decisions:**
- **Abstract Base Class**: `XMLIngestor` defines common interface and utilities
- **Format Registry**: Dynamic registration of ingestor classes with root element mapping
- **Dual Output**: Legacy format for backward compatibility, FHIR Bundle for AI/ML processing
- **Clinical Extraction**: NLP-powered medical entity recognition with confidence scoring
- **Error Hierarchy**: Structured exceptions with detailed context for debugging

**Detailed Technical Design**: See `/docs/ARCHITECTURE.md` for complete system architecture

## Key UAE Healthcare Standards

- **eClaimLink** (Dubai Health Authority): XML-based claims and authorization system
- **Shafafiya** (Abu Dhabi Department of Health): Healthcare data exchange platform
- **ICD-10-AM**: Australian modification of ICD-10 used in UAE
- **CPT**: Current Procedural Terminology codes

## Development Guidelines

### XML Processing Workflow

1. **Format Detection**: Use `XMLIngestorFactory.detect_format()` to identify XML structure
2. **Ingestor Creation**: Factory creates appropriate ingestor (`EClaimLinkIngestor` or `ShafafiyaIngestor`)
3. **Processing Options**: Choose between legacy output or FHIR Bundle with clinical extraction
4. **Validation**: XSD schema validation with detailed error reporting
5. **Clinical Intelligence**: NLP-powered extraction of medical entities and scoring

**Complete Processing Example:**
```python
from pipelines.factory import XMLIngestorFactory

# Initialize factory with schema validation
factory = XMLIngestorFactory(
    schema_base_path="schemas/",
    enable_validation=True
)

# Auto-detect and process with FHIR clinical extraction
ingestor = factory.create_ingestor_for_file(
    "samples/eclaim_link_request.xml",
    output_format="fhir_bundle"
)
fhir_bundle = ingestor.ingest_file("samples/eclaim_link_request.xml")

# Extract clinical intelligence scores
extensions = fhir_bundle.get("extension", [])
clinical_scores = {
    ext["url"].split("/")[-1]: ext.get("valueDecimal", 0)
    for ext in extensions
    if "nazmito.com/fhir" in ext.get("url", "")
}
```

### When working with FHIR Resources

The system extracts **5 FHIR resource types** from clinical text:
- **Claim**: Primary authorization request (always present)
- **Condition**: Medical diagnoses from ICD codes and clinical text
- **Observation**: Lab values, vital signs, clinical findings
- **MedicationStatement**: Current and historical medications
- **Procedure**: Requested procedures and historical procedures

**Clinical Extraction Patterns:**
- Text contains medical terms → Extract Conditions
- Mentions lab values/vitals → Create Observations  
- Lists medications → Generate MedicationStatements
- References procedures → Build Procedure resources

### Error Handling and Debugging

The system provides **structured error hierarchy**:
- `XMLIngestionError`: Base class for all XML processing errors
- `XMLParsingError`: Malformed XML, encoding issues
- `SchemaValidationError`: XSD validation failures with field details
- `UnsupportedFormatError`: Unknown XML root elements
- `DataNormalizationError`: Missing required data or invalid values

**Debugging Tools:**
- Each ingestor has `if __name__ == '__main__'` section for standalone testing
- VS Code launch configurations in `.vscode/launch.json` for step-by-step debugging
- Performance monitoring and clinical intelligence scoring
- Detailed logging with file paths and error context

### When building new features
- Follow the sprint-based architecture in `docs/todo_list.md` (28-day MVP timeline)
- Reference complete technical design in `docs/ARCHITECTURE.md`
- Use FHIR implementation guide in `docs/FHIR_GUIDE.md` for clinical data handling
- Maintain compatibility with UAE healthcare standards (eClaimLink, Shafafiya)
- Ensure PDPL (Personal Data Protection Law) compliance for UAE

### Extending the System

To add support for **new XML formats**:
1. Create ingestor class inheriting from `XMLIngestor`
2. Implement `get_supported_root_elements()` and `normalize()` methods
3. Register with factory using `XMLIngestorFactory.register_ingestor()`
4. Add XSD schema to `schemas/` directory
5. Create sample files in `samples/` directory
6. Add comprehensive tests in `tests/`

### API and Integration Points
- REST API implemented with FastAPI (`/ingest`, `/claim/{id}`, `/search`, `/chat`)
- Kafka event streaming for real-time data flow
- FHIR-compliant canonical schema with UAE extensions
- WebSocket support for conversational AI interfaces
- Server-sent events for real-time dashboard updates

## Testing Strategy

### Test Organization Structure (Organized by Separation of Concerns)

The test suite is organized into separate directories to eliminate repetitive tests and provide clear separation of concerns:

#### `/tests/unit/` - Unit Tests
- `test_eclaim_link_ingestor.py` - eClaimLink ingestor unit tests (XML parsing, normalization, business rules)
- `test_shafafiya_ingestor.py` - Shafafiya ingestor unit tests (activity mapping, observations, payment extraction)  
- `test_xml_factory.py` - Factory pattern unit tests (ingestor creation, format detection, registry operations)

#### `/tests/fhir/` - FHIR-Specific Tests
- `test_bundle_structure.py` - FHIR Bundle structure validation (meta info, entry structure, timestamps)
- `test_clinical_extraction.py` - Clinical intelligence and NLP extraction (medical entities, confidence scoring)
- `test_resource_validation.py` - Individual FHIR resource validation (Claim, Condition, Observation, etc.)

#### `/tests/integration/` - Integration Tests
- `test_end_to_end_processing.py` - Complete pipeline integration tests (format detection → processing → FHIR Bundle)

#### `/tests/` - Essential Schema Tests
- `test_canonical_schema.py` - Schema validation and FHIR Bundle structure tests (updated with modern imports)

### Test Execution Commands
- **Run all tests**: `pytest`
- **Run unit tests only**: `pytest tests/unit/`
- **Run FHIR tests only**: `pytest tests/fhir/`  
- **Run integration tests**: `pytest tests/integration/`
- **Run specific test file**: `pytest tests/unit/test_eclaim_link_ingestor.py`
- **Run with coverage**: `pytest --cov=pipelines --cov-report=html`

### Test Infrastructure
- **Comprehensive Fixtures**: `test_data_factory`, `fhir_test_data_factory`, `clinical_validation_helper`
- **Mock Generators**: Dynamic XML creation, schema validation mocking, file system simulation
- **FHIR Validation**: Specialized helpers for validating FHIR Bundle structure and clinical data quality
- **Performance Monitoring**: Memory usage and execution time tracking with `performance_monitor` fixture

### Clinical Intelligence Testing
- **NLP Extraction**: Validate medical entity recognition from clinical text
- **FHIR Bundle Validation**: Ensure proper resource relationships and structure
- **Clinical Scoring**: Test data quality, clinical context, and AI confidence metrics
- **Cross-Format Testing**: Verify consistent extraction patterns across eClaimLink and Shafafiya

### Test Data Factories

The system provides rich test data generation:
```python
def test_clinical_extraction(test_data_factory, clinical_validation_helper):
    # Create rich clinical XML with comprehensive medical context
    xml_content = test_data_factory.create_eclaim_xml(
        justification="35-year-old with poorly controlled diabetes, HbA1c 9.2%, on metformin therapy"
    )
    
    # Process with FHIR extraction
    factory = XMLIngestorFactory()
    ingestor = factory.create_ingestor("eClaimLink", output_format="fhir_bundle")
    bundle = ingestor.process_xml_string(xml_content)
    
    # Validate clinical intelligence
    clinical_validation_helper.validate_fhir_bundle_structure(bundle)
    clinical_validation_helper.validate_clinical_data_quality(bundle, min_score=0.7)
    
    # Check resource extraction
    conditions = clinical_validation_helper.extract_conditions(bundle)
    observations = clinical_validation_helper.extract_clinical_observations(bundle)
    medications = clinical_validation_helper.extract_medications(bundle)
    
    assert len(conditions) >= 1  # Diabetes condition
    assert len(observations) >= 1  # HbA1c value
    assert len(medications) >= 1  # Metformin
```

### Debug and Development Testing
- **Each file should have a `if __name__ == '__main__'` section** for standalone testing and debugging
- **VS Code launch configurations** should be created in `.vscode/launch.json` for each ingestor pipeline
- **Sample files** should be referenced directly in the debug sections for step-by-step execution
- **Debug outputs** should show detailed processing steps, FHIR resource extraction, and clinical intelligence scoring
- This enables developers to run individual ingestors, set breakpoints, and inspect the transformation pipeline in detail

## Security and Compliance Considerations
- UAE PDPL compliance required
- ADHICS (Abu Dhabi Healthcare Information and Cyber Security) standards
- ISO 27001 certification planned
- All data must be encrypted at rest (AES-256) and in transit (TLS 1.2+)

## IMPORTANT: Documentation Maintenance

**ALWAYS UPDATE THIS CLAUDE.md FILE** when you complete work that involves:
- Adding new features, components, or architectural changes
- Modifying existing workflows, commands, or development processes  
- Changing test structures, adding new test categories, or updating test execution methods
- Implementing new XML formats, FHIR resources, or clinical intelligence capabilities
- Adding new dependencies, tools, or development commands
- Updating project structure, file organization, or API endpoints
- Making changes based on user preferences or requirements that future Claude instances should know

**Update Approach:**
1. After completing any substantial work, review what has changed
2. Update the relevant sections in CLAUDE.md to reflect the new state
3. Add new sections if entirely new capabilities or workflows were introduced
4. Ensure commands, file paths, and architectural descriptions remain accurate
5. Include any user preferences or specific requirements discovered during the work

This ensures future Claude Code instances have accurate, up-to-date guidance for working with this repository efficiently.
