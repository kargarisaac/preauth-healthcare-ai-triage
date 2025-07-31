"""
Base abstract class for XML ingestion in healthcare data processing.

This module provides the foundation for all XML ingestors, defining the
common interface and shared utilities for schema validation, parsing,
and data normalization.
"""

import logging
import os
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
import xmlschema
import xmltodict

from .exceptions import (
    XMLIngestionError,
    SchemaValidationError,
    XMLParsingError,
    DataNormalizationError,
    ConfigurationError,
)


class XMLIngestor(ABC):
    """
    Abstract base class for XML ingestion processors.

    This class defines the common interface for all XML ingestors and provides
    shared utilities for schema validation, XML parsing, and error handling.
    All concrete ingestor implementations must inherit from this class.
    """

    def __init__(
        self,
        schema_path: Optional[str] = None,
        enable_validation: bool = True,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the XML ingestor.

        Args:
            schema_path: Path to the XSD schema file for validation
            enable_validation: Whether to enable schema validation
            logger: Custom logger instance (creates default if None)
        """
        self.schema_path = schema_path
        self.enable_validation = enable_validation
        self.logger = logger or self._create_default_logger()
        self._schema: Optional[xmlschema.XMLSchema11] = None

        # Validate configuration
        self._validate_configuration()

    def _create_default_logger(self) -> logging.Logger:
        """Create a default structured logger for the ingestor."""
        logger = logging.getLogger(
            f"{self.__class__.__module__}.{self.__class__.__name__}"
        )

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

        return logger

    def _validate_configuration(self) -> None:
        """Validate the ingestor configuration."""
        if self.enable_validation and not self.schema_path:
            raise ConfigurationError(
                "Schema validation is enabled but no schema_path provided",
                config_key="schema_path",
                config_value=None,
            )

        if self.schema_path and not os.path.exists(self.schema_path):
            raise ConfigurationError(
                f"Schema file does not exist: {self.schema_path}",
                config_key="schema_path",
                config_value=self.schema_path,
            )

    @property
    def schema(self) -> Optional[xmlschema.XMLSchema11]:
        """Lazy-load and return the XSD schema."""
        if self._schema is None and self.schema_path:
            try:
                self._schema = xmlschema.XMLSchema11(self.schema_path)
                self.logger.debug(f"Loaded schema from {self.schema_path}")
            except Exception as e:
                raise ConfigurationError(
                    f"Failed to load schema from {self.schema_path}: {str(e)}",
                    config_key="schema_path",
                    config_value=self.schema_path,
                ) from e
        return self._schema

    def validate(self, xml_file_path: str) -> bool:
        """
        Validate XML file against the associated schema.

        Args:
            xml_file_path: Path to the XML file to validate

        Returns:
            True if validation passes, False otherwise

        Raises:
            SchemaValidationError: If validation fails
            ConfigurationError: If schema is not configured
        """
        if not self.enable_validation:
            self.logger.debug(f"Validation disabled for {xml_file_path}")
            return True

        if not self.schema:
            raise ConfigurationError(
                "Schema validation requested but no schema configured"
            )

        try:
            self.logger.info(f"Validating {xml_file_path} against schema")

            if not self.schema.is_valid(xml_file_path):
                # Collect validation errors
                validation_errors = []
                for error in self.schema.iter_errors(xml_file_path):
                    error_msg = f"{error.path}: {error.reason}"
                    validation_errors.append(error_msg)
                    self.logger.error(f"Validation error - {error_msg}")

                raise SchemaValidationError(
                    f"XML validation failed with {len(validation_errors)} errors",
                    file_path=xml_file_path,
                    schema_path=self.schema_path,
                    validation_errors=validation_errors,
                )

            self.logger.info(f"Validation successful for {xml_file_path}")
            return True

        except xmlschema.XMLSchemaException as e:
            raise SchemaValidationError(
                f"Schema validation error: {str(e)}",
                file_path=xml_file_path,
                schema_path=self.schema_path,
            ) from e
        except Exception as e:
            raise XMLIngestionError(
                f"Unexpected error during validation: {str(e)}", file_path=xml_file_path
            ) from e

    def parse(self, xml_file_path: str) -> Dict[str, Any]:
        """
        Parse XML file into a Python dictionary.

        Args:
            xml_file_path: Path to the XML file to parse

        Returns:
            Parsed XML data as dictionary

        Raises:
            XMLParsingError: If parsing fails
        """
        if not os.path.exists(xml_file_path):
            raise XMLParsingError(
                f"XML file does not exist: {xml_file_path}", file_path=xml_file_path
            )

        try:
            self.logger.info(f"Parsing XML file: {xml_file_path}")

            with open(xml_file_path, "r", encoding="utf-8") as f:
                xml_content = f.read()

            # Parse with xmltodict for easier data manipulation
            parsed_data = xmltodict.parse(xml_content)

            self.logger.debug(
                f"Successfully parsed XML with root element: {list(parsed_data.keys())[0]}"
            )
            return parsed_data

        except ET.ParseError as e:
            raise XMLParsingError(
                f"XML parsing error: {str(e)}",
                file_path=xml_file_path,
                line_number=getattr(e, 'lineno', None),
                column_number=getattr(e, 'offset', None),
            ) from e
        except UnicodeDecodeError as e:
            raise XMLParsingError(
                f"File encoding error: {str(e)}", file_path=xml_file_path
            ) from e
        except Exception as e:
            raise XMLParsingError(
                f"Unexpected parsing error: {str(e)}", file_path=xml_file_path
            ) from e

    @abstractmethod
    def normalize(
        self, parsed_data: Dict[str, Any], xml_file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Abstract method to normalize parsed XML data into a standard format.

        Args:
            parsed_data: Raw parsed XML data
            xml_file_path: Optional path to the original XML file (for error reporting)

        Returns:
            Normalized data structure

        Raises:
            DataNormalizationError: If normalization fails
        """
        pass

    @abstractmethod
    def get_supported_root_elements(self) -> List[str]:
        """
        Abstract method to return list of supported root XML elements.

        Returns:
            List of supported root element names
        """
        pass

    def process(self, xml_file_path: str) -> Dict[str, Any]:
        """
        Complete processing pipeline: validate, parse, and normalize XML.

        Args:
            xml_file_path: Path to the XML file to process

        Returns:
            Normalized XML data

        Raises:
            Various XMLIngestionError subclasses depending on failure type
        """
        self.logger.info(f"Starting complete processing of {xml_file_path}")

        try:
            # Step 1: Validate
            self.validate(xml_file_path)

            # Step 2: Parse
            parsed_data = self.parse(xml_file_path)

            # Step 3: Normalize
            normalized_data = self.normalize(parsed_data, xml_file_path)

            self.logger.info(f"Successfully processed {xml_file_path}")
            return normalized_data

        except XMLIngestionError:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            # Wrap unexpected exceptions
            raise XMLIngestionError(
                f"Unexpected error during processing: {str(e)}", file_path=xml_file_path
            ) from e

    def can_handle(self, xml_file_path: str) -> bool:
        """
        Check if this ingestor can handle the given XML file.

        Args:
            xml_file_path: Path to the XML file to check

        Returns:
            True if this ingestor can handle the file, False otherwise
        """
        try:
            parsed_data = self.parse(xml_file_path)
            root_element = next(iter(parsed_data.keys()))
            return root_element in self.get_supported_root_elements()
        except Exception as e:
            self.logger.debug(f"Cannot handle {xml_file_path}: {str(e)}")
            return False

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about this ingestor.

        Returns:
            Dictionary containing ingestor metadata
        """
        return {
            "class_name": self.__class__.__name__,
            "module": self.__class__.__module__,
            "supported_root_elements": self.get_supported_root_elements(),
            "schema_path": self.schema_path,
            "validation_enabled": self.enable_validation,
        }

    def _safe_get(
        self,
        data: Dict[str, Any],
        key_path: str,
        default: Any = None,
        field_name: Optional[str] = None,
        xml_file_path: Optional[str] = None,
    ) -> Any:
        """
        Safely extract nested values from parsed XML data.

        Args:
            data: Dictionary to extract from
            key_path: Dot-separated path to the value (e.g., "Header.SenderID")
            default: Default value if path doesn't exist
            field_name: Name of the field for error reporting
            xml_file_path: Path to XML file for error reporting

        Returns:
            Value at the specified path or default

        Raises:
            DataNormalizationError: If required field is missing and no default provided
        """
        try:
            current = data
            keys = key_path.split('.')

            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    if default is None and field_name:
                        raise DataNormalizationError(
                            f"Required field '{field_name}' not found at path '{key_path}'",
                            file_path=xml_file_path,
                            field_name=field_name,
                        )
                    return default

            return current

        except Exception as e:
            if isinstance(e, DataNormalizationError):
                raise
            raise DataNormalizationError(
                f"Error accessing field at path '{key_path}': {str(e)}",
                file_path=xml_file_path,
                field_name=field_name,
            ) from e

    def _ensure_list(self, value: Union[Dict, List, None]) -> List[Dict[str, Any]]:
        """
        Ensure that a value is returned as a list of dictionaries.

        XML parsing sometimes returns single elements as dictionaries
        instead of single-item lists. This utility normalizes the format.

        Args:
            value: Value that might be a dict, list, or None

        Returns:
            List of dictionaries
        """
        if value is None:
            return []
        elif isinstance(value, dict):
            return [value]
        elif isinstance(value, list):
            return value
        else:
            return [{"value": value}]
