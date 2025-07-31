"""
Custom exceptions for XML ingestion pipelines.

This module defines specialized exceptions for healthcare XML data processing,
providing clear error categorization and detailed error information.
"""

from typing import Optional, List, Dict, Any


class XMLIngestionError(Exception):
    """Base exception for all XML ingestion related errors."""

    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize XMLIngestionError.

        Args:
            message: Human-readable error message
            file_path: Path to the XML file that caused the error
            details: Additional error details and context
        """
        super().__init__(message)
        self.file_path = file_path
        self.details = details or {}

    def __str__(self) -> str:
        """Return detailed error message with context."""
        base_msg = super().__str__()
        if self.file_path:
            base_msg = f"{base_msg} (File: {self.file_path})"
        if self.details:
            detail_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            base_msg = f"{base_msg} [Details: {detail_str}]"
        return base_msg


class SchemaValidationError(XMLIngestionError):
    """Raised when XML fails schema validation."""

    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        schema_path: Optional[str] = None,
        validation_errors: Optional[List[str]] = None,
    ):
        """
        Initialize SchemaValidationError.

        Args:
            message: Human-readable error message
            file_path: Path to the XML file that failed validation
            schema_path: Path to the XSD schema file
            validation_errors: List of detailed validation error messages
        """
        details = {}
        if schema_path:
            details['schema_path'] = schema_path
        if validation_errors:
            details['validation_errors'] = validation_errors

        super().__init__(message, file_path, details)
        self.schema_path = schema_path
        self.validation_errors = validation_errors or []


class XMLParsingError(XMLIngestionError):
    """Raised when XML parsing fails."""

    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        column_number: Optional[int] = None,
    ):
        """
        Initialize XMLParsingError.

        Args:
            message: Human-readable error message
            file_path: Path to the XML file that failed parsing
            line_number: Line number where parsing failed
            column_number: Column number where parsing failed
        """
        details = {}
        if line_number is not None:
            details['line_number'] = line_number
        if column_number is not None:
            details['column_number'] = column_number

        super().__init__(message, file_path, details)
        self.line_number = line_number
        self.column_number = column_number


class UnsupportedFormatError(XMLIngestionError):
    """Raised when XML format is not supported or recognized."""

    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        detected_root_element: Optional[str] = None,
        supported_formats: Optional[List[str]] = None,
    ):
        """
        Initialize UnsupportedFormatError.

        Args:
            message: Human-readable error message
            file_path: Path to the XML file with unsupported format
            detected_root_element: The root element that was detected
            supported_formats: List of supported format identifiers
        """
        details = {}
        if detected_root_element:
            details['detected_root_element'] = detected_root_element
        if supported_formats:
            details['supported_formats'] = supported_formats

        super().__init__(message, file_path, details)
        self.detected_root_element = detected_root_element
        self.supported_formats = supported_formats or []


class DataNormalizationError(XMLIngestionError):
    """Raised when data normalization fails."""

    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        field_name: Optional[str] = None,
        field_value: Optional[Any] = None,
    ):
        """
        Initialize DataNormalizationError.

        Args:
            message: Human-readable error message
            file_path: Path to the XML file being normalized
            field_name: Name of the field that caused normalization to fail
            field_value: Value of the field that caused the error
        """
        details = {}
        if field_name:
            details['field_name'] = field_name
        if field_value is not None:
            details['field_value'] = str(field_value)

        super().__init__(message, file_path, details)
        self.field_name = field_name
        self.field_value = field_value


class ConfigurationError(XMLIngestionError):
    """Raised when there are configuration issues with the ingestor."""

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_value: Optional[Any] = None,
    ):
        """
        Initialize ConfigurationError.

        Args:
            message: Human-readable error message
            config_key: Configuration key that caused the error
            config_value: Configuration value that caused the error
        """
        details = {}
        if config_key:
            details['config_key'] = config_key
        if config_value is not None:
            details['config_value'] = str(config_value)

        super().__init__(message, None, details)
        self.config_key = config_key
        self.config_value = config_value
