"""
Clean XML processor for UAE healthcare data formats.

This module provides a minimal, clean approach to processing XML files from
UAE healthcare systems (eClaimLink and Shafafiya) and converting them to
canonical JSON format while preserving all original data.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Any
import xmltodict
from loguru import logger

from .data_quality import DataQuality


class XMLProcessor:
    """
    Clean XML processor for UAE healthcare formats.

    Processes eClaimLink and Shafafiya XML files, mapping essential fields
    to canonical schema while preserving all original data for future use.
    """

    def __init__(self, enable_validation: bool = True):
        """
        Initialize XML processor with optional data quality validation.

        Args:
            enable_validation: Enable data quality validation (default: True)
        """
        self.enable_validation = enable_validation
        if self.enable_validation:
            self.data_quality = DataQuality()

    def process_eclaim_link(self, xml_file_path: str) -> Dict[str, Any]:
        """
        Process eClaimLink XML format to canonical JSON.

        Args:
            xml_file_path: Path to eClaimLink XML file

        Returns:
            Dictionary in canonical JSON format with all data preserved
        """
        logger.info(f"Processing eClaimLink XML: {xml_file_path}")

        # Parse XML to dictionary
        with open(xml_file_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()

        parsed_data = xmltodict.parse(xml_content)

        # Extract the main payload
        root_element = next(iter(parsed_data.keys()))
        payload = parsed_data[root_element]

        # Generate bundle ID and timestamp
        bundle_id = (
            f"eClaimLink-{str(uuid.uuid4())[:8]}-{datetime.now().strftime('%Y%m%d')}"
        )
        timestamp = datetime.now(timezone.utc).isoformat()

        # Extract essential fields for canonical schema
        header = payload.get("Header", {})
        services = self._extract_eclaim_services(payload)
        justification = payload.get("JustificationText", "")

        # Build canonical JSON structure
        canonical_data = {
            "resourceType": "Bundle",
            "id": bundle_id,
            "meta": {
                "profile": [
                    "https://nazmito.com/fhir/StructureDefinition/healthcare-bundle"
                ],
                "source": "eClaimLink",
                "lastUpdated": timestamp,
                "versionId": "1",
            },
            "type": "collection",
            "timestamp": timestamp,
            # Essential mapped fields
            "authorization_id": header.get("TransactionID"),
            "sender": header.get("SenderID"),
            "receiver": header.get("ReceiverID"),
            "transaction_date": header.get("TransactionDateTime"),
            "justification_text": justification,
            "services": services,
            # Preserve ALL original data
            "raw_data": parsed_data,
            "source_file": xml_file_path,
            "processing_timestamp": timestamp,
        }

        # Add data quality validation
        if self.enable_validation:
            validation_report = self.data_quality.validate_fhir_bundle(canonical_data)
            canonical_data["data_quality"] = validation_report
            logger.info(
                f"Data quality score: {validation_report['quality_score'].overall_score:.3f}"
            )

        logger.info(
            f"Successfully processed eClaimLink XML: {len(services)} services found"
        )
        return canonical_data

    def process_shafafiya(self, xml_file_path: str) -> Dict[str, Any]:
        """
        Process Shafafiya XML format to canonical JSON.

        Args:
            xml_file_path: Path to Shafafiya XML file

        Returns:
            Dictionary in canonical JSON format with all data preserved
        """
        logger.info(f"Processing Shafafiya XML: {xml_file_path}")

        # Parse XML to dictionary
        with open(xml_file_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()

        parsed_data = xmltodict.parse(xml_content)

        # Extract the main payload
        root_element = next(iter(parsed_data.keys()))
        payload = parsed_data[root_element]

        # Generate bundle ID and timestamp
        bundle_id = (
            f"Shafafiya-{str(uuid.uuid4())[:8]}-{datetime.now().strftime('%Y%m%d')}"
        )
        timestamp = datetime.now(timezone.utc).isoformat()

        # Extract essential fields for canonical schema
        header = payload.get("Header", {})
        authorization = payload.get("Authorization", {})
        activities = self._extract_shafafiya_activities(authorization)

        # Build canonical JSON structure
        canonical_data = {
            "resourceType": "Bundle",
            "id": bundle_id,
            "meta": {
                "profile": [
                    "https://nazmito.com/fhir/StructureDefinition/healthcare-bundle"
                ],
                "source": "Shafafiya",
                "lastUpdated": timestamp,
                "versionId": "1",
            },
            "type": "collection",
            "timestamp": timestamp,
            # Essential mapped fields
            "authorization_id": authorization.get("ID"),
            "sender": header.get("SenderID"),
            "receiver": header.get("ReceiverID"),
            "transaction_date": header.get("TransactionDate"),
            "authorization_result": authorization.get("Result"),
            "authorization_start": authorization.get("Start"),
            "authorization_end": authorization.get("End"),
            "comments": authorization.get("Comments", ""),
            "activities": activities,
            # Preserve ALL original data
            "raw_data": parsed_data,
            "source_file": xml_file_path,
            "processing_timestamp": timestamp,
        }

        # Add data quality validation
        if self.enable_validation:
            validation_report = self.data_quality.validate_fhir_bundle(canonical_data)
            canonical_data["data_quality"] = validation_report
            logger.info(
                f"Data quality score: {validation_report['quality_score'].overall_score:.3f}"
            )

        logger.info(
            f"Successfully processed Shafafiya XML: {len(activities)} activities found"
        )
        return canonical_data

    def _extract_eclaim_services(self, payload: Dict[str, Any]) -> list:
        """Extract services from eClaimLink payload."""
        services = []
        service_requests = payload.get("ServiceRequests", {})
        service_list = service_requests.get("ServiceRequest", [])

        # Ensure list format
        if isinstance(service_list, dict):
            service_list = [service_list]

        for idx, service in enumerate(service_list, 1):
            # Extract requested amount
            requested_amount = service.get("RequestedAmount", {})
            amount_currency = None
            amount_value = None

            if requested_amount:
                if isinstance(requested_amount, dict):
                    amount_currency = requested_amount.get("@currency")
                    amount_value = requested_amount.get("#text")
                else:
                    amount_value = str(requested_amount)

            service_data = {
                "sequence": idx,
                "activity_code": service.get("ct:ActivityCode"),
                "diagnosis_code": service.get("ct:DiagnosisCode"),
                "activity_date_time": service.get("ct:ActivityDateTime"),
                "instructions": service.get("ct:ActivityInstructions"),
                "requested_amount_value": amount_value,
                "requested_amount_currency": amount_currency,
                "raw_service_data": service,  # Preserve original service data
            }
            services.append(service_data)

        return services

    def _extract_shafafiya_activities(self, authorization: Dict[str, Any]) -> list:
        """Extract activities from Shafafiya authorization."""
        activities = []
        activity_list = authorization.get("Activity", [])

        # Ensure list format
        if isinstance(activity_list, dict):
            activity_list = [activity_list]

        for activity in activity_list:
            activity_data = {
                "id": activity.get("ID"),
                "type": activity.get("Type"),
                "code": activity.get("Code"),
                "description": activity.get("Description"),
                "quantity": activity.get("Quantity"),
                "unit_cost": activity.get("UnitCost"),
                "amount": activity.get("Amount"),
                "raw_activity_data": activity,  # Preserve original activity data
            }
            activities.append(activity_data)

        return activities


if __name__ == "__main__":
    """
    Debug and testing section for XML processor.

    Tests both eClaimLink and Shafafiya formats and saves debug output.
    """

    # Setup logging
    logger.add("debug_xml_processor.log")

    print("=" * 80)
    print("XML Processor - Debug Mode")
    print("=" * 80)

    processor = XMLProcessor()

    # Test files
    eclaim_file = "samples/eclaim_link_request.xml"
    shafafiya_file = "samples/shafafiya_prior_auth_request.xml"

    try:
        print("\n🔧 Step 1: Process eClaimLink XML")
        print("-" * 50)

        if os.path.exists(eclaim_file):
            eclaim_result = processor.process_eclaim_link(eclaim_file)

            print("✅ eClaimLink processed successfully")
            print(f"   Authorization ID: {eclaim_result.get('authorization_id')}")
            print(f"   Services Count: {len(eclaim_result.get('services', []))}")
            print(
                f"   Justification Length: {len(eclaim_result.get('justification_text', ''))}"
            )

            # Save debug output
            with open("debug_eclaim_output.json", "w", encoding="utf-8") as f:
                json.dump(eclaim_result, f, indent=2, ensure_ascii=False, default=str)
            print("   Debug saved to: debug_eclaim_output.json")
        else:
            print(f"❌ eClaimLink file not found: {eclaim_file}")

        print("\n🔧 Step 2: Process Shafafiya XML")
        print("-" * 50)

        if os.path.exists(shafafiya_file):
            shafafiya_result = processor.process_shafafiya(shafafiya_file)

            print("✅ Shafafiya processed successfully")
            print(f"   Authorization ID: {shafafiya_result.get('authorization_id')}")
            print(f"   Activities Count: {len(shafafiya_result.get('activities', []))}")
            print(
                f"   Authorization Result: {shafafiya_result.get('authorization_result')}"
            )

            # Save debug output
            with open("debug_shafafiya_output.json", "w", encoding="utf-8") as f:
                json.dump(
                    shafafiya_result, f, indent=2, ensure_ascii=False, default=str
                )
            print("   Debug saved to: debug_shafafiya_output.json")
        else:
            print(f"❌ Shafafiya file not found: {shafafiya_file}")

    except Exception as e:
        print("\n❌ Error during processing:")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback

        print("\n📋 Full traceback:")
        traceback.print_exc()
        exit(1)

    print("\n🎉 XML processor debug session completed successfully!")
    print("=" * 80)
