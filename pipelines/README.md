# XML Ingestion Pipeline for Healthcare Data

A robust, extensible framework for ingesting and normalizing healthcare XML data from various UAE healthcare systems including eClaimLink and Shafafiya.

## Features

- **Automatic Format Detection**: Detects XML format based on root elements
- **Schema Validation**: Validates XML against XSD schemas with detailed error reporting
- **Extensible Architecture**: Easy to add support for new XML formats
- **Comprehensive Error Handling**: Custom exception hierarchy with detailed context
- **Production-Ready Logging**: Structured logging with configurable levels
- **Backward Compatibility**: Drop-in replacement for existing code
- **Type Safety**: Full type hints throughout the codebase

## Quick Start

### Simple Usage

```python
from pipelines import process_xml_file

# Process any supported XML file with automatic format detection
result = process_xml_file("path/to/healthcare.xml")
print(f"Schema version: {result['schema_version']}")
print(f"Services: {len(result['services'])}")
```

### Advanced Usage

```python
from pipelines import XMLIngestorFactory

# Create factory with schema validation
factory = XMLIngestorFactory(
    schema_base_path="schemas/",
    enable_validation=True
)

# Auto-detect format and create appropriate ingestor
ingestor = factory.create_ingestor_for_file("path/to/healthcare.xml")

# Process the file
result = ingestor.process("path/to/healthcare.xml")
```

### Backward Compatibility

```python
# Existing code continues to work unchanged
from pipelines import normalize_prior_authorization

result = normalize_prior_authorization("samples/prior_auth_request.xml")
```

## Supported Formats

### Shafafiya (Abu Dhabi Department of Health)
- **Root Element**: `Prior.Authorization`
- **Schema Version**: 2011
- **Use Cases**: Prior authorization responses, status updates, treatment approvals

### eClaimLink (Dubai Health Authority)
- **Root Element**: `PriorAuthorizationRequest`
- **Schema Version**: 2019/11
- **Use Cases**: Prior authorization requests, treatment approval requests

## Architecture Overview

```
pipelines/
├── __init__.py              # Public API and convenience functions
├── base.py                  # Abstract XMLIngestor base class
├── factory.py               # Format detection and ingestor factory
├── exceptions.py            # Custom exception hierarchy
├── eclaim_link_ingestor.py  # eClaimLink 2019/11 format support
├── shafafiya_ingestor.py    # Shafafiya 2011 format support
└── demo.py                  # Comprehensive usage examples
```

### Key Components

1. **XMLIngestor (Base Class)**: Abstract base defining the common interface
2. **XMLIngestorFactory**: Handles format detection and ingestor creation
3. **Format-Specific Ingestors**: Implement normalization for each format
4. **Exception Hierarchy**: Detailed error handling with context information

## API Reference

### Main Functions

#### `process_xml_file(xml_file_path, schema_path=None, enable_validation=None)`
Process an XML file with automatic format detection.

**Parameters:**
- `xml_file_path` (str): Path to the XML file
- `schema_path` (str, optional): Custom schema path
- `enable_validation` (bool, optional): Enable/disable validation

**Returns:** Normalized XML data as dictionary

#### `detect_xml_format(xml_file_path)`
Detect the format of an XML file.

**Returns:** Format identifier string (e.g., "eClaimLink", "Shafafiya")

#### `get_supported_formats()`
Get information about all supported XML formats.

**Returns:** List of dictionaries with format information

### Classes

#### `XMLIngestorFactory`
Factory class for creating appropriate XML ingestors.

```python
factory = XMLIngestorFactory(
    schema_base_path="schemas/",
    enable_validation=True
)

# Detect format
format_name = factory.detect_format("file.xml")

# Create ingestor
ingestor = factory.create_ingestor(format_name)

# Process file
result = factory.process_file("file.xml")
```

#### `XMLIngestor` (Abstract Base)
Base class for all XML ingestors with common functionality:

- `validate(xml_file_path)`: Schema validation
- `parse(xml_file_path)`: XML parsing
- `normalize(parsed_data)`: Data normalization (abstract)
- `process(xml_file_path)`: Complete processing pipeline

## Error Handling

The pipeline provides detailed error information through a custom exception hierarchy:

```python
from pipelines import (
    XMLIngestionError,        # Base exception
    SchemaValidationError,    # Schema validation failures
    XMLParsingError,          # XML parsing errors
    UnsupportedFormatError,   # Unsupported XML formats
    DataNormalizationError,   # Data normalization failures
    ConfigurationError        # Configuration issues
)

try:
    result = process_xml_file("file.xml")
except SchemaValidationError as e:
    print(f"Validation failed: {e}")
    print(f"Errors: {e.validation_errors}")
except UnsupportedFormatError as e:
    print(f"Unsupported format: {e.detected_root_element}")
    print(f"Supported: {e.supported_formats}")
```

## Extending the Pipeline

### Adding a New Format

1. **Create a new ingestor class:**

```python
from pipelines.base import XMLIngestor

class MyFormatIngestor(XMLIngestor):
    SUPPORTED_ROOT_ELEMENTS = ["MyRootElement"]
    SCHEMA_VERSION = "1.0"
    FORMAT_NAME = "MyFormat"
    
    def get_supported_root_elements(self):
        return self.SUPPORTED_ROOT_ELEMENTS
    
    def normalize(self, parsed_data, xml_file_path=None):
        # Implement normalization logic
        return normalized_data
```

2. **Register with the factory:**

```python
from pipelines import XMLIngestorFactory

factory = XMLIngestorFactory()
factory.register_ingestor(
    format_name="MyFormat",
    ingestor_class=MyFormatIngestor,
    root_elements=["MyRootElement"],
    schema_filename="MyFormat.xsd"
)
```

## Configuration

### Schema Validation
Enable/disable schema validation globally or per operation:

```python
# Global configuration
from pipelines import configure_default_factory

configure_default_factory(
    schema_base_path="schemas/",
    enable_validation=True
)

# Per-operation configuration
result = process_xml_file("file.xml", enable_validation=False)
```

### Logging
Configure logging for detailed processing information:

```python
import logging

# Enable debug logging
logging.getLogger("pipelines").setLevel(logging.DEBUG)

# Custom logger
factory = XMLIngestorFactory(logger=my_logger)
```

## Examples

### Processing Different Formats

```python
from pipelines import process_xml_file, detect_xml_format

# Detect format first
format_name = detect_xml_format("samples/prior_auth_request.xml")
print(f"Format: {format_name}")  # Output: Shafafiya

# Process the file
result = process_xml_file("samples/prior_auth_request.xml")

# Access normalized data
print(f"Authorization ID: {result['authorization_id']}")
print(f"Services: {len(result['services'])}")

for service in result['services']:
    print(f"  Service {service['id']}: {service['code']} - ${service['net']}")
```

### Batch Processing

```python
import os
from pipelines import XMLIngestorFactory

factory = XMLIngestorFactory(schema_base_path="schemas/")

for filename in os.listdir("xml_files/"):
    if filename.endswith(".xml"):
        file_path = os.path.join("xml_files", filename)
        try:
            result = factory.process_file(file_path)
            print(f"✓ Processed {filename}: {result['format_name']}")
        except Exception as e:
            print(f"✗ Failed {filename}: {e}")
```

### Custom Validation

```python
from pipelines import XMLIngestorFactory

factory = XMLIngestorFactory()
ingestor = factory.create_ingestor_for_file("file.xml")

# Validate against schema
is_valid = ingestor.validate("file.xml")

# Custom business rules validation
if hasattr(ingestor, 'validate_business_rules'):
    result = ingestor.process("file.xml")
    warnings = ingestor.validate_business_rules(result)
    if warnings:
        for warning in warnings:
            print(f"Warning: {warning}")
```

## Migration from Legacy Code

The new pipeline maintains full backward compatibility:

```python
# Old code (still works)
from data_pipelines.eclaim_link import normalize_prior_authorization
result = normalize_prior_authorization("file.xml")

# New equivalent code
from pipelines import normalize_prior_authorization  # Same function name
result = normalize_prior_authorization("file.xml")   # Same interface

# Or use the new API
from pipelines import process_xml_file
result = process_xml_file("file.xml")
```

## Performance Considerations

- **Lazy Schema Loading**: Schemas are loaded only when needed
- **Memory Efficient**: Processes files without loading entire documents into memory unnecessarily
- **Caching**: Factory instances cache format detection results
- **Minimal Dependencies**: Uses lightweight XML parsing libraries

## Testing

Run the demonstration script to see all features in action:

```bash
cd /path/to/nazmito
python pipelines/demo.py
```

## Requirements

- Python 3.7+
- xmlschema
- xmltodict

## License

Part of the Nazmito Healthcare Platform.