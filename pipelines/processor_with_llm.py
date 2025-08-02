"""
Enhanced processor utilities with streamlined LLM validation support.

This module provides wrapper functions to add LLM validation to existing
processors without modifying their core logic.
"""

from typing import Dict, Any, Optional
from loguru import logger

from pipelines.csv_processor import CSVProcessor
from pipelines.xml_processor import XMLProcessor
from pipelines.llm_validator import LLMValidatorSync


class ProcessorWithLLM:
    """
    Wrapper class to add streamlined LLM validation to existing processors.

    This approach maintains backward compatibility while enabling optional
    LLM validation for enhanced data quality assessment.
    """

    def __init__(self):
        """Initialize enhanced processors with LLM support."""
        self.csv_processor = CSVProcessor()
        self.xml_processor = XMLProcessor()
        self.llm_validator = LLMValidatorSync()

    def process_csv_with_optional_llm(
        self,
        csv_file_path: str,
        enable_llm_validation: bool = False,
        context: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Process CSV file with optional LLM validation.

        Args:
            csv_file_path: Path to CSV file
            enable_llm_validation: Whether to run LLM validation
            context: Optional context for LLM validation
            **kwargs: Additional arguments passed to CSV processor

        Returns:
            Processing results with optional LLM validation metadata
        """
        logger.info(f"Processing CSV with LLM validation: {enable_llm_validation}")

        # First, process with standard CSV processor
        try:
            result = self.csv_processor.process_claims_csv(csv_file_path, **kwargs)
        except Exception:
            # Fallback to clinical CSV processing
            result = self.csv_processor.process_clinical_csv(csv_file_path)

        # Add LLM validation if requested
        if enable_llm_validation:
            logger.info("Running streamlined LLM validation on CSV results")
            try:
                # Prepare context with defaults
                validation_context = context or {}
                validation_context.setdefault('source_system', 'CSV')
                validation_context.setdefault('emirate', 'Unknown')
                validation_context.setdefault('provider_type', 'Unknown')
                validation_context.setdefault('patient_category', 'Unknown')

                # Run LLM validation
                llm_result = self.llm_validator.validate_healthcare_data(
                    result, validation_context
                )

                # Add validation results to metadata
                if 'metadata' not in result:
                    result['metadata'] = {}
                result['metadata']['llm_validation'] = llm_result.to_dict()

                logger.info(
                    f"LLM validation completed with score: {llm_result.overall_quality_score:.3f}"
                )

            except Exception as e:
                logger.error(f"LLM validation failed: {e}")
                if 'metadata' not in result:
                    result['metadata'] = {}
                result['metadata']['llm_validation_error'] = str(e)

        return result

    def process_xml_with_optional_llm(
        self,
        xml_file_path: str,
        format_type: str,
        enable_llm_validation: bool = False,
        context: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Process XML file with optional LLM validation.

        Args:
            xml_file_path: Path to XML file
            format_type: XML format ('eclaim' or 'shafafiya')
            enable_llm_validation: Whether to run LLM validation
            context: Optional context for LLM validation

        Returns:
            Processing results with optional LLM validation metadata
        """
        logger.info(
            f"Processing {format_type} XML with LLM validation: {enable_llm_validation}"
        )

        # Process with standard XML processor
        if format_type == 'eclaim':
            result = self.xml_processor.process_eclaim_link(xml_file_path)
        elif format_type == 'shafafiya':
            result = self.xml_processor.process_shafafiya(xml_file_path)
        else:
            raise ValueError(f"Unsupported XML format: {format_type}")

        # Add LLM validation if requested
        if enable_llm_validation:
            logger.info(
                f"Running streamlined LLM validation on {format_type} XML results"
            )
            try:
                # Prepare context with format-specific defaults
                validation_context = context or {}
                validation_context.setdefault('source_system', format_type)

                if format_type == 'eclaim':
                    validation_context.setdefault('emirate', 'Dubai')
                elif format_type == 'shafafiya':
                    validation_context.setdefault('emirate', 'Abu Dhabi')
                else:
                    validation_context.setdefault('emirate', 'Unknown')

                validation_context.setdefault('provider_type', 'Unknown')
                validation_context.setdefault('patient_category', 'Unknown')

                # Run LLM validation
                llm_result = self.llm_validator.validate_healthcare_data(
                    result, validation_context
                )

                # Add validation results to metadata
                if 'metadata' not in result:
                    result['metadata'] = {}
                result['metadata']['llm_validation'] = llm_result.to_dict()

                logger.info(
                    f"LLM validation completed with score: {llm_result.overall_quality_score:.3f}"
                )

            except Exception as e:
                logger.error(f"LLM validation failed: {e}")
                if 'metadata' not in result:
                    result['metadata'] = {}
                result['metadata']['llm_validation_error'] = str(e)

        return result


# Convenience functions for direct use
def process_csv_file(
    csv_file_path: str,
    enable_llm_validation: bool = False,
    context: Optional[Dict[str, str]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    Convenience function to process CSV with optional LLM validation.

    Args:
        csv_file_path: Path to CSV file
        enable_llm_validation: Whether to run LLM validation
        context: Optional context for LLM validation
        **kwargs: Additional arguments passed to CSV processor

    Returns:
        Processing results with optional LLM validation
    """
    processor = ProcessorWithLLM()
    return processor.process_csv_with_optional_llm(
        csv_file_path, enable_llm_validation, context, **kwargs
    )


def process_xml_file(
    xml_file_path: str,
    format_type: str,
    enable_llm_validation: bool = False,
    context: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Convenience function to process XML with optional LLM validation.

    Args:
        xml_file_path: Path to XML file
        format_type: XML format ('eclaim' or 'shafafiya')
        enable_llm_validation: Whether to run LLM validation
        context: Optional context for LLM validation

    Returns:
        Processing results with optional LLM validation
    """
    processor = ProcessorWithLLM()
    return processor.process_xml_with_optional_llm(
        xml_file_path, format_type, enable_llm_validation, context
    )


if __name__ == "__main__":
    """
    Test the enhanced processors with sample data.
    """
    import tempfile
    import os

    # Setup logging
    logger.add("debug_processor_with_llm.log")

    print("=" * 60)
    print("Enhanced Processor with LLM - Test Mode")
    print("=" * 60)

    # Create sample CSV data for testing
    sample_csv_data = """claim_id,patient_id,diagnosis_code,procedure_code,amount,service_date,provider_id
TEST-CLM-001,P001,E11.9,99213,150.50,2024-01-01,PROV001
TEST-CLM-002,P002,M54.5,99214,200.75,2024-01-02,PROV002"""

    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(sample_csv_data)
        temp_csv_path = f.name

    try:
        print("\n🔧 Step 1: Test CSV Processing (without LLM)")
        print("-" * 50)

        result_without_llm = process_csv_file(
            temp_csv_path, enable_llm_validation=False
        )
        print(f"✅ Processed {result_without_llm.get('total_records', 0)} records")
        print(
            f"   Processing time: {result_without_llm.get('metadata', {}).get('processing_time_seconds', 0):.3f}s"
        )

        print("\n🔧 Step 2: Test CSV Processing (with LLM)")
        print("-" * 50)

        context = {
            "source_system": "CSV",
            "emirate": "Dubai",
            "provider_type": "Clinic",
            "patient_category": "UAE_National",
        }

        result_with_llm = process_csv_file(
            temp_csv_path, enable_llm_validation=True, context=context
        )

        print(f"✅ Processed {result_with_llm.get('total_records', 0)} records")
        print(
            f"   Processing time: {result_with_llm.get('metadata', {}).get('processing_time_seconds', 0):.3f}s"
        )

        # Check LLM validation results
        llm_validation = result_with_llm.get('metadata', {}).get('llm_validation')
        if llm_validation:
            print(
                f"   LLM Quality Score: {llm_validation['overall_quality_score']:.3f}"
            )
            print(f"   LLM Grade: {llm_validation['grade']}")
            print(f"   Total Issues: {llm_validation['total_issues']}")
        else:
            print("   ⚠️ LLM validation not available")

        print("\n🔧 Step 3: Save Test Results")
        print("-" * 50)

        test_results = {
            "test_metadata": {
                "test_timestamp": "2024-01-01T00:00:00",  # Static timestamp for testing
                "temp_file_path": temp_csv_path,
            },
            "result_without_llm": {
                "total_records": result_without_llm.get('total_records', 0),
                "has_llm_validation": 'llm_validation'
                in result_without_llm.get('metadata', {}),
            },
            "result_with_llm": {
                "total_records": result_with_llm.get('total_records', 0),
                "has_llm_validation": 'llm_validation'
                in result_with_llm.get('metadata', {}),
                "llm_validation": llm_validation,
            },
        }

        with open("debug_enhanced_processor_results.json", "w", encoding="utf-8") as f:
            import json

            json.dump(test_results, f, indent=2, ensure_ascii=False, default=str)

        print("✅ Test results saved to: debug_enhanced_processor_results.json")

    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        import traceback

        print("\n📋 Full traceback:")
        traceback.print_exc()

    finally:
        # Cleanup
        if os.path.exists(temp_csv_path):
            os.unlink(temp_csv_path)

    print("\n🎉 Enhanced processor test completed!")
    print("=" * 60)
