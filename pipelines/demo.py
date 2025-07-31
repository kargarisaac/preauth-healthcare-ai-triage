"""
Demonstration script for the XML ingestion pipeline.

This script shows how to use the new class-based XML ingestion architecture
and demonstrates backward compatibility with the existing code.
"""

from loguru import logger
import os

from pipelines import (
    process_xml_file,
    detect_xml_format,
    XMLIngestorFactory,
    ShafafiyaIngestor,
    # Backward compatibility
    normalize_prior_authorization,
    validate_xml_against_schema,
)

# Configure logging
logger.add("logs/demo.log", rotation="100 MB", retention="10 days")


def demo_basic_usage():
    """Demonstrate basic usage of the new pipeline."""
    print("\n" + "=" * 60)
    print("DEMO: Basic Usage")
    print("=" * 60)

    # Sample XML file
    xml_file = (
        "/Users/isaackargar/codes/personal/nazmito/samples/prior_auth_request.xml"
    )

    if not os.path.exists(xml_file):
        print(f"Sample file not found: {xml_file}")
        return

    try:
        # 1. Detect format
        print(f"\n1. Detecting format for: {xml_file}")
        format_name = detect_xml_format(xml_file)
        print(f"   Detected format: {format_name}")

        # 2. Process the file
        print("\n2. Processing file...")
        result = process_xml_file(xml_file, enable_validation=False)

        print(f"   Schema version: {result.get('schema_version')}")
        print(f"   Format name: {result.get('format_name')}")
        print(f"   Authorization ID: {result.get('authorization_id')}")
        print(f"   Number of services: {len(result.get('services', []))}")

        # Show first service details
        services = result.get('services', [])
        if services:
            print("\n   First service details:")
            first_service = services[0]
            print(f"     ID: {first_service.get('id')}")
            print(f"     Type: {first_service.get('type')}")
            print(f"     Code: {first_service.get('code')}")
            print(f"     Net: {first_service.get('net')}")

    except Exception as e:
        print(f"   Error: {e}")


def demo_factory_usage():
    """Demonstrate factory pattern usage."""
    print("\n" + "=" * 60)
    print("DEMO: Factory Pattern Usage")
    print("=" * 60)

    xml_file = (
        "/Users/isaackargar/codes/personal/nazmito/samples/prior_auth_request.xml"
    )
    schema_base = "/Users/isaackargar/codes/personal/nazmito/schemas"

    if not os.path.exists(xml_file):
        print(f"Sample file not found: {xml_file}")
        return

    try:
        # 1. Create factory with schema configuration
        print(f"\n1. Creating factory with schema base: {schema_base}")
        factory = XMLIngestorFactory(
            schema_base_path=schema_base, enable_validation=False  # Disable for demo
        )

        # 2. Get supported formats
        print("\n2. Supported formats:")
        formats = factory.get_supported_formats()
        for fmt in formats:
            print(f"   - {fmt.get('format_name')}: {fmt.get('description', 'N/A')}")

        # 3. Create ingestor for specific file
        print("\n3. Creating ingestor for file...")
        ingestor = factory.create_ingestor_for_file(xml_file)
        print(f"   Created: {ingestor.__class__.__name__}")

        # 4. Process with the ingestor
        print("\n4. Processing with ingestor...")
        result = ingestor.process(xml_file)
        print(f"   Successfully processed. Services: {len(result.get('services', []))}")

        # 5. Check file compatibility
        print("\n5. Checking file compatibility...")
        compatibility = factory.validate_file_compatibility(xml_file)
        print(f"   Detected format: {compatibility.get('detected_format')}")
        print(
            f"   Compatible ingestors: {len(compatibility.get('compatible_ingestors', []))}"
        )

    except Exception as e:
        print(f"   Error: {e}")


def demo_backward_compatibility():
    """Demonstrate backward compatibility with existing code."""
    print("\n" + "=" * 60)
    print("DEMO: Backward Compatibility")
    print("=" * 60)

    xml_file = (
        "/Users/isaackargar/codes/personal/nazmito/samples/prior_auth_request.xml"
    )
    schema_file = (
        "/Users/isaackargar/codes/personal/nazmito/schemas/PriorAuthorization.xsd"
    )

    if not os.path.exists(xml_file):
        print(f"Sample file not found: {xml_file}")
        return

    try:
        # 1. Use legacy normalize function
        print("\n1. Using legacy normalize_prior_authorization function...")
        result = normalize_prior_authorization(xml_file)

        print(f"   Schema version: {result.get('schema_version')}")
        print(f"   Sender: {result.get('sender')}")
        print(f"   Receiver: {result.get('receiver')}")
        print(f"   Services count: {len(result.get('services', []))}")

        # 2. Use legacy validation function (if schema exists)
        if os.path.exists(schema_file):
            print("\n2. Using legacy validate_xml_against_schema function...")
            is_valid = validate_xml_against_schema(xml_file, schema_file)
            print(f"   Validation result: {is_valid}")
        else:
            print(f"\n2. Schema file not found: {schema_file}")

    except Exception as e:
        print(f"   Error: {e}")


def demo_error_handling():
    """Demonstrate error handling capabilities."""
    print("\n" + "=" * 60)
    print("DEMO: Error Handling")
    print("=" * 60)

    # Test with non-existent file
    print("\n1. Testing with non-existent file...")
    try:
        result = process_xml_file("non_existent_file.xml")
    except Exception as e:
        print(f"   Expected error: {type(e).__name__}: {e}")

    # Test with invalid XML (create a temporary invalid file)
    print("\n2. Testing with invalid XML...")
    invalid_xml_path = "/tmp/invalid.xml"
    try:
        with open(invalid_xml_path, "w") as f:
            f.write("<?xml version='1.0'?><invalid><unclosed>content</invalid>")

        result = process_xml_file(invalid_xml_path)
    except Exception as e:
        print(f"   Expected error: {type(e).__name__}: {e}")
    finally:
        if os.path.exists(invalid_xml_path):
            os.remove(invalid_xml_path)

    # Test with unsupported format
    print("\n3. Testing with unsupported format...")
    unsupported_xml_path = "/tmp/unsupported.xml"
    try:
        with open(unsupported_xml_path, "w") as f:
            f.write(
                "<?xml version='1.0'?><UnsupportedRoot><data>test</data></UnsupportedRoot>"
            )

        _ = process_xml_file(unsupported_xml_path)
    except Exception as e:
        print(f"   Expected error: {type(e).__name__}: {e}")
    finally:
        if os.path.exists(unsupported_xml_path):
            os.remove(unsupported_xml_path)


def demo_direct_ingestor_usage():
    """Demonstrate direct usage of specific ingestors."""
    print("\n" + "=" * 60)
    print("DEMO: Direct Ingestor Usage")
    print("=" * 60)

    xml_file = (
        "/Users/isaackargar/codes/personal/nazmito/samples/prior_auth_request.xml"
    )

    if not os.path.exists(xml_file):
        print(f"Sample file not found: {xml_file}")
        return

    try:
        # 1. Use Shafafiya ingestor directly
        print("\n1. Using ShafafiyaIngestor directly...")
        shafafiya_ingestor = ShafafiyaIngestor(enable_validation=False)

        # Check if it can handle the file
        can_handle = shafafiya_ingestor.can_handle(xml_file)
        print(f"   Can handle file: {can_handle}")

        if can_handle:
            result = shafafiya_ingestor.process(xml_file)
            print(
                f"   Processed successfully. Authorization ID: {result.get('authorization_id')}"
            )

            # Get format info
            format_info = shafafiya_ingestor.get_format_info()
            print(
                f"   Format: {format_info.get('format_name')} ({format_info.get('authority')})"
            )

        # 2. Test business rules validation
        print("\n2. Testing business rules validation...")
        if can_handle:
            warnings = shafafiya_ingestor.validate_business_rules(result)
            if warnings:
                print("   Business rule warnings:")
                for warning in warnings:
                    print(f"     - {warning}")
            else:
                print("   No business rule violations found")

    except Exception as e:
        print(f"   Error: {e}")


def main():
    """Run all demonstrations."""
    print("XML Ingestion Pipeline - Demonstration")
    print("=====================================")

    demo_basic_usage()
    demo_factory_usage()
    demo_backward_compatibility()
    demo_error_handling()
    demo_direct_ingestor_usage()

    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print("\nThe new XML ingestion pipeline provides:")
    print("✓ Automatic format detection")
    print("✓ Robust error handling")
    print("✓ Schema validation")
    print("✓ Extensible architecture")
    print("✓ Backward compatibility")
    print("✓ Comprehensive logging")


if __name__ == "__main__":
    main()
