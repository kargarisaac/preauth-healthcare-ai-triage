"""
XML Ingestion Pipeline for Healthcare Data Processing.

This package provides a robust, extensible framework for ingesting and normalizing
healthcare XML data from various UAE healthcare systems including eClaimLink and Shafafiya.

Key Features:
- Automatic format detection and ingestor selection
- Schema validation with detailed error reporting
- Extensible architecture supporting custom formats
- Comprehensive error handling and logging
- Backward compatibility with existing code

Usage:
    # Simple usage with automatic format detection
    from pipelines import process_xml_file

    result = process_xml_file("path/to/healthcare.xml")

    # Advanced usage with factory
    from pipelines import XMLIngestorFactory

    factory = XMLIngestorFactory(schema_base_path="schemas/")
    ingestor = factory.create_ingestor_for_file("path/to/healthcare.xml")
    result = ingestor.process("path/to/healthcare.xml")

    # Backward compatibility
    from pipelines import normalize_prior_authorization

    result = normalize_prior_authorization("path/to/healthcare.xml")
"""

import logging
from typing import Dict, Any, Optional, List

# Import main classes
from .base import XMLIngestor
from .factory import XMLIngestorFactory
from .eclaim_link_ingestor import EClaimLinkIngestor
from .shafafiya_ingestor import ShafafiyaIngestor

# Import exceptions
from .exceptions import (
    XMLIngestionError,
    SchemaValidationError,
    XMLParsingError,
    UnsupportedFormatError,
    DataNormalizationError,
    ConfigurationError,
)

# Package version
__version__ = "1.0.0"
__author__ = "Nazmito Healthcare Platform"

# Default logger for the package
logger = logging.getLogger(__name__)

# Global factory instance for convenience functions
_default_factory: Optional[XMLIngestorFactory] = None


def get_default_factory() -> XMLIngestorFactory:
    """
    Get or create the default factory instance.

    Returns:
        Default XMLIngestorFactory instance
    """
    global _default_factory
    if _default_factory is None:
        _default_factory = XMLIngestorFactory()
    return _default_factory


def configure_default_factory(
    schema_base_path: Optional[str] = None,
    enable_validation: bool = True,
    logger_instance: Optional[logging.Logger] = None,
) -> None:
    """
    Configure the default factory instance.

    Args:
        schema_base_path: Base directory path for schema files
        enable_validation: Whether to enable schema validation by default
        logger_instance: Custom logger instance
    """
    global _default_factory
    _default_factory = XMLIngestorFactory(
        schema_base_path=schema_base_path,
        enable_validation=enable_validation,
        logger=logger_instance,
    )


def process_xml_file(
    xml_file_path: str,
    schema_path: Optional[str] = None,
    enable_validation: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Process an XML file with automatic format detection.

    This is the main convenience function for processing healthcare XML files.
    It automatically detects the format and uses the appropriate ingestor.

    Args:
        xml_file_path: Path to the XML file to process
        schema_path: Optional custom schema path
        enable_validation: Optional validation setting

    Returns:
        Normalized XML data as dictionary

    Raises:
        Various XMLIngestionError subclasses depending on failure type

    Example:
        >>> result = process_xml_file("samples/prior_auth_request.xml")
        >>> print(result["schema_version"])
        2011
        >>> print(len(result["services"]))
        2
    """
    factory = get_default_factory()
    return factory.process_file(xml_file_path, schema_path, enable_validation)


def detect_xml_format(xml_file_path: str) -> str:
    """
    Detect the format of an XML file.

    Args:
        xml_file_path: Path to the XML file to analyze

    Returns:
        Format identifier string (e.g., "eClaimLink", "Shafafiya")

    Raises:
        UnsupportedFormatError: If format cannot be detected
        XMLParsingError: If XML file cannot be parsed

    Example:
        >>> format_name = detect_xml_format("samples/prior_auth_request.xml")
        >>> print(format_name)
        Shafafiya
    """
    factory = get_default_factory()
    return factory.detect_format(xml_file_path)


def get_supported_formats() -> List[Dict[str, Any]]:
    """
    Get information about all supported XML formats.

    Returns:
        List of dictionaries containing format information

    Example:
        >>> formats = get_supported_formats()
        >>> for fmt in formats:
        ...     print(f"{fmt['format_name']}: {fmt['description']}")
        eClaimLink: Prior authorization request format for UAE healthcare
        Shafafiya: Prior authorization format for Abu Dhabi healthcare system
    """
    factory = get_default_factory()
    return factory.get_supported_formats()


def validate_xml_file(xml_file_path: str, schema_path: Optional[str] = None) -> bool:
    """
    Validate an XML file against its appropriate schema.

    Args:
        xml_file_path: Path to the XML file to validate
        schema_path: Optional custom schema path

    Returns:
        True if validation passes

    Raises:
        SchemaValidationError: If validation fails
        UnsupportedFormatError: If format cannot be detected

    Example:
        >>> is_valid = validate_xml_file("samples/prior_auth_request.xml")
        >>> print(is_valid)
        True
    """
    factory = get_default_factory()
    ingestor = factory.create_ingestor_for_file(
        xml_file_path, schema_path, enable_validation=True
    )
    return ingestor.validate(xml_file_path)


def check_file_compatibility(xml_file_path: str) -> Dict[str, Any]:
    """
    Check which ingestors can handle the given XML file.

    Args:
        xml_file_path: Path to the XML file to check

    Returns:
        Dictionary with compatibility information

    Example:
        >>> info = check_file_compatibility("samples/prior_auth_request.xml")
        >>> print(info["detected_format"])
        Shafafiya
        >>> print(len(info["compatible_ingestors"]))
        1
    """
    factory = get_default_factory()
    return factory.validate_file_compatibility(xml_file_path)


# Backward compatibility functions
def normalize_prior_authorization(xml_file_path: str) -> Dict[str, Any]:
    """
    Legacy function for backward compatibility with existing code.

    This function provides the same interface as the original normalize_prior_authorization
    function from data_pipelines/eclaim_link.py, but uses the new architecture internally.

    Args:
        xml_file_path: Path to the XML file to normalize

    Returns:
        Normalized representation ready for downstream use

    Raises:
        Various XMLIngestionError subclasses depending on failure type

    Example:
        >>> # This maintains compatibility with existing code
        >>> result = normalize_prior_authorization("samples/prior_auth_request.xml")
        >>> print(result["schema_version"])
        2011
    """
    logger.info(f"Processing {xml_file_path} using legacy compatibility function")

    try:
        return process_xml_file(xml_file_path, enable_validation=False)
    except Exception as e:
        # Convert new exceptions to legacy format for compatibility
        if isinstance(e, XMLIngestionError):
            raise ValueError(
                f"Unsupported root element or processing error: {str(e)}"
            ) from e
        raise


def validate_xml_against_schema(xml_file_path: str, schema_file_path: str) -> bool:
    """
    Legacy function for backward compatibility with existing validation code.

    Args:
        xml_file_path: The path to the XML file to validate
        schema_file_path: The path to the XSD schema file

    Returns:
        True if the XML is valid against the schema, False otherwise

    Example:
        >>> # This maintains compatibility with existing code
        >>> is_valid = validate_xml_against_schema(
        ...     "samples/prior_auth_request.xml",
        ...     "schemas/PriorAuthorization.xsd"
        ... )
        >>> print(is_valid)
        True
    """
    logger.info(
        f"Validating {xml_file_path} against {schema_file_path} using legacy function"
    )

    try:
        # Create a temporary ingestor with the specific schema
        factory = get_default_factory()
        format_name = factory.detect_format(xml_file_path)
        ingestor = factory.create_ingestor(
            format_name, schema_path=schema_file_path, enable_validation=True
        )
        return ingestor.validate(xml_file_path)

    except SchemaValidationError as e:
        # Print errors in legacy format
        print(f"Validation errors for {xml_file_path}:")
        for error in e.validation_errors or []:
            print(f"- {error}")
        return False

    except Exception as e:
        print(f"An error occurred during validation of {xml_file_path}: {e}")
        return False


# Export public API
__all__ = [
    # Main processing functions
    "process_xml_file",
    "detect_xml_format",
    "validate_xml_file",
    "get_supported_formats",
    "check_file_compatibility",
    # Configuration
    "configure_default_factory",
    # Core classes
    "XMLIngestor",
    "XMLIngestorFactory",
    "EClaimLinkIngestor",
    "ShafafiyaIngestor",
    # Exceptions
    "XMLIngestionError",
    "SchemaValidationError",
    "XMLParsingError",
    "UnsupportedFormatError",
    "DataNormalizationError",
    "ConfigurationError",
    # Backward compatibility
    "normalize_prior_authorization",
    "validate_xml_against_schema",
    # Package info
    "__version__",
    "__author__",
]
