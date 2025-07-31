"""
Factory pattern for automatic XML format detection and ingestor selection.

This module provides a factory class that automatically detects the XML format
and returns the appropriate ingestor instance for processing healthcare XML data.
"""

import logging
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional, Type
from pathlib import Path

from pipelines.base import XMLIngestor
from pipelines.eclaim_link_ingestor import EClaimLinkIngestor
from pipelines.shafafiya_ingestor import ShafafiyaIngestor
from pipelines.exceptions import (
    XMLIngestionError,
    UnsupportedFormatError,
    XMLParsingError,
    ConfigurationError,
)


class XMLIngestorFactory:
    """
    Factory class for creating appropriate XML ingestors based on format detection.

    This factory automatically detects the XML format by examining the root element
    and other format-specific characteristics, then returns the appropriate ingestor
    instance configured for that format.
    """

    # Registry of available ingestors
    _INGESTOR_REGISTRY: Dict[str, Type[XMLIngestor]] = {
        "eClaimLink": EClaimLinkIngestor,
        "Shafafiya": ShafafiyaIngestor,
    }

    # Mapping of root elements to ingestor types
    _ROOT_ELEMENT_MAPPING: Dict[str, str] = {
        "PriorAuthorizationRequest": "eClaimLink",
        "Prior.Authorization": "Shafafiya",
    }

    def __init__(
        self,
        schema_base_path: Optional[str] = None,
        enable_validation: bool = True,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the XML ingestor factory.

        Args:
            schema_base_path: Base directory path for schema files
            enable_validation: Whether to enable schema validation by default
            logger: Custom logger instance
        """
        self.schema_base_path = Path(schema_base_path) if schema_base_path else None
        self.enable_validation = enable_validation
        self.logger = logger or self._create_default_logger()

        # Schema mappings for different formats
        self._schema_mappings = {
            "eClaimLink": "CommonTypes_20191113.xsd",  # Or appropriate schema
            "Shafafiya": "PriorAuthorization.xsd",
        }

        self.logger.info("Initialized XMLIngestorFactory")

    def _create_default_logger(self) -> logging.Logger:
        """Create a default logger for the factory."""
        logger = logging.getLogger(
            f"{self.__class__.__module__}.{self.__class__.__name__}"
        )

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

        return logger

    def detect_format(self, xml_file_path: str) -> str:
        """
        Detect the XML format by examining the root element.

        Args:
            xml_file_path: Path to the XML file to analyze

        Returns:
            Format identifier string (e.g., "eClaimLink", "Shafafiya")

        Raises:
            UnsupportedFormatError: If format cannot be detected or is unsupported
            XMLParsingError: If XML file cannot be parsed
        """
        try:
            self.logger.debug(f"Detecting format for {xml_file_path}")

            # Parse the XML directly using xmltodict (same approach as base class)
            import xmltodict
            import os

            if not os.path.exists(xml_file_path):
                raise XMLParsingError(
                    f"XML file does not exist: {xml_file_path}", file_path=xml_file_path
                )

            with open(xml_file_path, "r", encoding="utf-8") as f:
                xml_content = f.read()

            parsed_data = xmltodict.parse(xml_content)
            root_element = next(iter(parsed_data.keys()))

            # Look up format based on root element
            format_name = self._ROOT_ELEMENT_MAPPING.get(root_element)

            if not format_name:
                supported_elements = list(self._ROOT_ELEMENT_MAPPING.keys())
                raise UnsupportedFormatError(
                    f"Unsupported XML format with root element '{root_element}'",
                    file_path=xml_file_path,
                    detected_root_element=root_element,
                    supported_formats=supported_elements,
                )

            self.logger.info(f"Detected format '{format_name}' for {xml_file_path}")
            return format_name

        except UnsupportedFormatError:
            raise
        except XMLParsingError:
            raise
        except ET.ParseError as e:
            raise XMLParsingError(
                f"XML parsing error during format detection: {str(e)}",
                file_path=xml_file_path,
                line_number=getattr(e, "lineno", None),
                column_number=getattr(e, "offset", None),
            ) from e
        except Exception as e:
            # Check if it's an XML parsing error from xmltodict
            if "mismatched tag" in str(e) or "not well-formed" in str(e):
                raise XMLParsingError(
                    f"XML parsing error during format detection: {str(e)}",
                    file_path=xml_file_path,
                ) from e
            raise XMLIngestionError(
                f"Failed to detect format for {xml_file_path}: {str(e)}",
                file_path=xml_file_path,
            ) from e

    def create_ingestor(
        self,
        format_name: str,
        schema_path: Optional[str] = None,
        enable_validation: Optional[bool] = None,
        output_format: str = "legacy",
    ) -> XMLIngestor:
        """
        Create an ingestor instance for the specified format.

        Args:
            format_name: Name of the format (e.g., "eClaimLink", "Shafafiya")
            schema_path: Optional custom schema path (overrides default)
            enable_validation: Optional validation setting (overrides default)
            output_format: Output format ("legacy" or "fhir_bundle")

        Returns:
            Configured ingestor instance

        Raises:
            UnsupportedFormatError: If format is not supported
            ConfigurationError: If schema configuration is invalid
        """
        if format_name not in self._INGESTOR_REGISTRY:
            supported_formats = list(self._INGESTOR_REGISTRY.keys())
            raise UnsupportedFormatError(
                f"Unsupported format '{format_name}'",
                supported_formats=supported_formats,
            )

        # Determine schema path
        final_schema_path = schema_path
        if not final_schema_path and self.schema_base_path:
            schema_filename = self._schema_mappings.get(format_name)
            if schema_filename:
                final_schema_path = str(self.schema_base_path / schema_filename)

        # Determine validation setting
        final_enable_validation = (
            enable_validation
            if enable_validation is not None
            else self.enable_validation
        )

        # Create ingestor instance
        ingestor_class = self._INGESTOR_REGISTRY[format_name]
        ingestor = ingestor_class(
            schema_path=final_schema_path,
            enable_validation=final_enable_validation,
            output_format=output_format,
            logger=self.logger,
        )

        self.logger.info(
            f"Created {format_name} ingestor with validation={final_enable_validation}"
        )
        return ingestor

    def create_ingestor_for_file(
        self,
        xml_file_path: str,
        schema_path: Optional[str] = None,
        enable_validation: Optional[bool] = None,
    ) -> XMLIngestor:
        """
        Auto-detect format and create appropriate ingestor for the given XML file.

        Args:
            xml_file_path: Path to the XML file
            schema_path: Optional custom schema path
            enable_validation: Optional validation setting

        Returns:
            Configured ingestor instance for the detected format

        Raises:
            Various XMLIngestionError subclasses depending on failure type
        """
        format_name = self.detect_format(xml_file_path)
        return self.create_ingestor(format_name, schema_path, enable_validation)

    def process_file(
        self,
        xml_file_path: str,
        schema_path: Optional[str] = None,
        enable_validation: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Complete processing: detect format, create ingestor, and process file.

        Args:
            xml_file_path: Path to the XML file to process
            schema_path: Optional custom schema path
            enable_validation: Optional validation setting

        Returns:
            Normalized XML data

        Raises:
            Various XMLIngestionError subclasses depending on failure type
        """
        self.logger.info(f"Starting complete processing of {xml_file_path}")

        ingestor = self.create_ingestor_for_file(
            xml_file_path, schema_path, enable_validation
        )
        result = ingestor.process(xml_file_path)

        self.logger.info(
            f"Successfully processed {xml_file_path} using {ingestor.__class__.__name__}"
        )
        return result

    def get_supported_formats(self) -> List[Dict[str, Any]]:
        """
        Get information about all supported formats.

        Returns:
            List of dictionaries containing format information
        """
        formats = []

        for format_name, ingestor_class in self._INGESTOR_REGISTRY.items():
            # Create temporary instance to get format info
            temp_ingestor = ingestor_class(enable_validation=False)

            if hasattr(temp_ingestor, "get_format_info"):
                format_info = temp_ingestor.get_format_info()
            else:
                format_info = {
                    "format_name": format_name,
                    "ingestor_class": ingestor_class.__name__,
                    "supported_root_elements": temp_ingestor.get_supported_root_elements(),
                }

            formats.append(format_info)

        return formats

    def register_ingestor(
        self,
        format_name: str,
        ingestor_class: Type[XMLIngestor],
        root_elements: List[str],
        schema_filename: Optional[str] = None,
    ) -> None:
        """
        Register a new ingestor class with the factory.

        Args:
            format_name: Unique name for the format
            ingestor_class: Ingestor class that inherits from XMLIngestor
            root_elements: List of root elements this ingestor handles
            schema_filename: Optional schema filename for this format
        """
        if not issubclass(ingestor_class, XMLIngestor):
            raise ConfigurationError(
                "Ingestor class must inherit from XMLIngestor",
                config_key="ingestor_class",
                config_value=ingestor_class.__name__,
            )

        # Register the ingestor
        self._INGESTOR_REGISTRY[format_name] = ingestor_class

        # Register root element mappings
        for root_element in root_elements:
            if root_element in self._ROOT_ELEMENT_MAPPING:
                self.logger.warning(
                    f"Root element '{root_element}' already mapped to "
                    f"'{self._ROOT_ELEMENT_MAPPING[root_element]}', overriding with '{format_name}'"
                )
            self._ROOT_ELEMENT_MAPPING[root_element] = format_name

        # Register schema mapping if provided
        if schema_filename:
            self._schema_mappings[format_name] = schema_filename

        self.logger.info(
            f"Registered new ingestor: {format_name} -> {ingestor_class.__name__}"
        )

    def unregister_ingestor(self, format_name: str) -> None:
        """
        Unregister an ingestor from the factory.

        Args:
            format_name: Name of the format to unregister
        """
        if format_name not in self._INGESTOR_REGISTRY:
            self.logger.warning(f"Format '{format_name}' is not registered")
            return

        # Remove from ingestor registry
        del self._INGESTOR_REGISTRY[format_name]

        # Remove root element mappings
        root_elements_to_remove = [
            element
            for element, fmt in self._ROOT_ELEMENT_MAPPING.items()
            if fmt == format_name
        ]
        for element in root_elements_to_remove:
            del self._ROOT_ELEMENT_MAPPING[element]

        # Remove schema mapping
        if format_name in self._schema_mappings:
            del self._schema_mappings[format_name]

        self.logger.info(f"Unregistered ingestor: {format_name}")

    def validate_file_compatibility(self, xml_file_path: str) -> Dict[str, Any]:
        """
        Check which ingestors can handle the given file.

        Args:
            xml_file_path: Path to the XML file to check

        Returns:
            Dictionary with compatibility information
        """
        compatibility_info = {
            "file_path": xml_file_path,
            "compatible_ingestors": [],
            "detected_format": None,
            "errors": [],
        }

        try:
            # Try to detect format
            detected_format = self.detect_format(xml_file_path)
            compatibility_info["detected_format"] = detected_format

            # Check each registered ingestor
            for format_name, ingestor_class in self._INGESTOR_REGISTRY.items():
                try:
                    temp_ingestor = ingestor_class(enable_validation=False)
                    if temp_ingestor.can_handle(xml_file_path):
                        compatibility_info["compatible_ingestors"].append(
                            {
                                "format_name": format_name,
                                "ingestor_class": ingestor_class.__name__,
                                "is_detected_format": format_name == detected_format,
                            }
                        )
                except Exception as e:
                    compatibility_info["errors"].append(
                        {"format_name": format_name, "error": str(e)}
                    )

        except Exception as e:
            compatibility_info["errors"].append(
                {"stage": "format_detection", "error": str(e)}
            )

        return compatibility_info


if __name__ == "__main__":
    """
    Standalone testing and debugging for XMLIngestorFactory.
    
    This section enables comprehensive testing of the XML format detection and 
    processing pipeline across both eClaimLink and Shafafiya formats.
    """
    import json
    import os
    from pathlib import Path

    # Setup logging for detailed debug output
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    print("=" * 80)
    print("XMLIngestorFactory - Comprehensive Debug Mode")
    print("=" * 80)

    # Configuration
    schema_base_path = "schemas/"
    sample_files = {
        "eClaimLink": "samples/eclaim_link_request.xml",
        "Shafafiya": "samples/shafafiya_authorization.xml",
    }

    try:
        print("\n🔧 Step 1: Initialize XMLIngestorFactory")
        print("-" * 50)

        factory = XMLIngestorFactory(
            schema_base_path=schema_base_path, enable_validation=True
        )

        print("✅ Factory initialized successfully")
        print(f"   Schema Base Path: {schema_base_path}")
        print(f"   Validation Enabled: True")

        print("\n📋 Step 2: List Supported Formats")
        print("-" * 50)

        supported_formats = factory.get_supported_formats()
        for fmt in supported_formats:
            print(f"✅ Format: {fmt['format_name']}")
            print(f"   Authority: {fmt.get('authority', 'N/A')}")
            print(f"   Schema Version: {fmt.get('schema_version', 'N/A')}")
            print(f"   Root Elements: {fmt.get('supported_root_elements', [])}")
            print(f"   System: {fmt.get('system', 'N/A')}")

        print("\n🔧 Step 3: Test Format Detection")
        print("-" * 50)

        for format_name, sample_file in sample_files.items():
            print(f"\nTesting {format_name} format detection:")

            if not os.path.exists(sample_file):
                print(f"⚠️  Sample file not found: {sample_file}")
                continue

            try:
                detected_format = factory.detect_format(sample_file)
                print(f"✅ Detected format: {detected_format}")

                if detected_format == format_name:
                    print(f"✅ Format detection correct")
                else:
                    print(
                        f"❌ Format detection mismatch: expected {format_name}, got {detected_format}"
                    )

            except Exception as e:
                print(f"❌ Format detection failed: {e}")

        print("\n🔧 Step 4: Test File Compatibility Analysis")
        print("-" * 50)

        for format_name, sample_file in sample_files.items():
            if not os.path.exists(sample_file):
                continue

            print(f"\nCompatibility analysis for {format_name}:")

            compatibility = factory.validate_file_compatibility(sample_file)
            print(f"   File: {compatibility['file_path']}")
            print(f"   Detected Format: {compatibility['detected_format']}")
            print(
                f"   Compatible Ingestors: {len(compatibility['compatible_ingestors'])}"
            )

            for ingestor in compatibility["compatible_ingestors"]:
                status = (
                    "✅ PRIMARY" if ingestor["is_detected_format"] else "⚠️  SECONDARY"
                )
                print(
                    f"     {status}: {ingestor['format_name']} ({ingestor['ingestor_class']})"
                )

            if compatibility["errors"]:
                print(f"   Errors: {len(compatibility['errors'])}")
                for error in compatibility["errors"]:
                    print(f"     ❌ {error}")

        print("\n🔧 Step 5: Test End-to-End Processing")
        print("-" * 50)

        for format_name, sample_file in sample_files.items():
            if not os.path.exists(sample_file):
                continue

            print(f"\nProcessing {format_name} file: {sample_file}")

            try:
                # Test legacy format
                result_legacy = factory.process_file(sample_file)
                print(f"✅ Legacy processing successful")
                print(f"   Format: {result_legacy.get('format_name')}")
                print(f"   Schema Version: {result_legacy.get('schema_version')}")
                print(
                    f"   Services/Activities: {len(result_legacy.get('services', []))}"
                )

                # Test FHIR Bundle format by creating a new factory instance with FHIR mode
                factory_fhir = XMLIngestorFactory(
                    schema_base_path=schema_base_path, enable_validation=True
                )

                # Create FHIR-enabled ingestor
                detected_format = factory_fhir.detect_format(sample_file)
                ingestor_fhir = factory_fhir.create_ingestor(
                    detected_format, output_format="fhir_bundle"
                )
                result_fhir = ingestor_fhir.ingest_file(sample_file)

                print(f"✅ FHIR Bundle processing successful")
                print(f"   Bundle ID: {result_fhir.get('id')}")
                print(f"   Resource Type: {result_fhir.get('resourceType')}")
                print(f"   Total Resources: {result_fhir.get('total')}")

                # Show resource breakdown
                entries = result_fhir.get("entry", [])
                resource_counts = {}
                for entry in entries:
                    resource_type = entry.get("resource", {}).get("resourceType")
                    resource_counts[resource_type] = (
                        resource_counts.get(resource_type, 0) + 1
                    )

                print(f"   📊 FHIR Resource Breakdown:")
                for resource_type, count in resource_counts.items():
                    print(f"     - {resource_type}: {count}")

                # Show clinical intelligence scores
                extensions = result_fhir.get("extension", [])
                for ext in extensions:
                    if "clinical-context-score" in ext.get("url", ""):
                        score = ext.get("valueDecimal", 0)
                        print(f"   🧠 Clinical Context Score: {score:.2f}")
                    elif "data-quality-score" in ext.get("url", ""):
                        score = ext.get("valueDecimal", 0)
                        print(f"   📈 Data Quality Score: {score:.2f}")

                # Save debug outputs
                legacy_output_file = (
                    f"debug_output_factory_{format_name.lower()}_legacy.json"
                )
                fhir_output_file = (
                    f"debug_output_factory_{format_name.lower()}_fhir.json"
                )

                with open(legacy_output_file, "w", encoding="utf-8") as f:
                    json.dump(
                        result_legacy, f, indent=2, ensure_ascii=False, default=str
                    )

                with open(fhir_output_file, "w", encoding="utf-8") as f:
                    json.dump(result_fhir, f, indent=2, ensure_ascii=False, default=str)

                print(f"   💾 Debug outputs saved:")
                print(
                    f"     - Legacy: {legacy_output_file} ({os.path.getsize(legacy_output_file)} bytes)"
                )
                print(
                    f"     - FHIR: {fhir_output_file} ({os.path.getsize(fhir_output_file)} bytes)"
                )

            except Exception as e:
                print(f"❌ Processing failed: {e}")
                import traceback

                traceback.print_exc()

        print("\n🔧 Step 6: Performance and Statistics Summary")
        print("-" * 50)

        total_formats = len(supported_formats)
        total_samples = len([f for f in sample_files.values() if os.path.exists(f)])

        print(f"✅ Factory Debug Session Summary:")
        print(f"   Registered Formats: {total_formats}")
        print(f"   Available Sample Files: {total_samples}")
        print(f"   Schema Base Path: {schema_base_path}")
        print(f"   Validation Enabled: ✅")
        print(f"   FHIR Bundle Support: ✅")
        print(f"   Clinical Intelligence Extraction: ✅")

        print("\n" + "=" * 80)

    except Exception as e:
        print(f"\n❌ Factory debug session failed:")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback

        print(f"\n📋 Full traceback:")
        traceback.print_exc()
        exit(1)

    print("\n🎉 XMLIngestorFactory debug session completed successfully!")
    print("=" * 80)
