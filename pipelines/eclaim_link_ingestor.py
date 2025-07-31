"""
EClaimLink XML ingestor for 2019/11 PriorAuthorizationRequest format.

This module implements the XML ingestor for the Dubai Health Authority (DHA)
eClaimLink 2019/11 PriorAuthorizationRequest format, handling the specific
structure and normalization requirements of this healthcare data format.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from pipelines.base import XMLIngestor
from pipelines.exceptions import DataNormalizationError, UnsupportedFormatError
from pipelines.clinical_extraction_methods import ClinicalExtractionMixin


class EClaimLinkIngestor(ClinicalExtractionMixin, XMLIngestor):
    """
    XML ingestor for eClaimLink 2019/11 PriorAuthorizationRequest format.

    This ingestor handles the Dubai Health Authority's eClaimLink format,
    which is used for prior authorization requests in the UAE healthcare system.
    """

    # Class constants for supported formats
    SUPPORTED_ROOT_ELEMENTS = ["PriorAuthorizationRequest"]
    SCHEMA_VERSION = "2019/11"
    FORMAT_NAME = "eClaimLink"

    def __init__(
        self,
        schema_path: Optional[str] = None,
        enable_validation: bool = True,
        logger: Optional[logging.Logger] = None,
        output_format: str = "legacy",
    ):
        """
        Initialize the EClaimLink ingestor.

        Args:
            schema_path: Path to the XSD schema file for eClaimLink format
            enable_validation: Whether to enable schema validation
            logger: Custom logger instance
            output_format: Output format - "legacy" (default for backward compatibility) or "fhir_bundle" for enhanced clinical extraction
        """
        super().__init__(schema_path, enable_validation, logger)
        self.output_format = output_format
        self.logger.info(
            f"Initialized {self.FORMAT_NAME} ingestor for {self.SCHEMA_VERSION} (output: {output_format})"
        )

    def get_supported_root_elements(self) -> List[str]:
        """
        Return list of supported root XML elements for eClaimLink format.

        Returns:
            List containing "PriorAuthorizationRequest"
        """
        return self.SUPPORTED_ROOT_ELEMENTS.copy()

    def normalize(
        self, parsed_data: Dict[str, Any], xml_file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Normalize eClaimLink 2019/11 PriorAuthorizationRequest data to FHIR Bundle format.

        This enhanced method extracts clinical data to all 5 FHIR resources:
        - Claim: Primary authorization request data
        - Observation: Clinical findings from justification text
        - MedicationStatement: Medication history from clinical context
        - Condition: Enhanced diagnosis with clinical context
        - Procedure: Historical and requested procedures

        Args:
            parsed_data: Raw parsed XML data dictionary
            xml_file_path: Optional path to original XML file for error reporting

        Returns:
            FHIR Bundle structure with comprehensive clinical resources

        Raises:
            UnsupportedFormatError: If root element is not supported
            DataNormalizationError: If required data is missing or invalid
        """
        self.logger.info(
            f"Normalizing eClaimLink data to FHIR Bundle from {xml_file_path or 'memory'}"
        )

        # Validate root element
        root_element = next(iter(parsed_data.keys()))
        if root_element not in self.SUPPORTED_ROOT_ELEMENTS:
            raise UnsupportedFormatError(
                f"Unsupported root element '{root_element}' for eClaimLink ingestor",
                file_path=xml_file_path,
                detected_root_element=root_element,
                supported_formats=self.SUPPORTED_ROOT_ELEMENTS,
            )

        try:
            payload = parsed_data[root_element]

            # Extract basic normalized data (always needed)
            header = self._normalize_header(payload, xml_file_path)
            services = self._normalize_service_requests(payload, xml_file_path)
            justification_text = self._safe_get(
                payload, "JustificationText", default="", xml_file_path=xml_file_path
            )

            # Return legacy format for backward compatibility
            if self.output_format == "legacy":
                normalized = {
                    "schema_version": self.SCHEMA_VERSION,
                    "format_name": self.FORMAT_NAME,
                    "ingestion_metadata": {
                        "ingestor_class": self.__class__.__name__,
                        "source_file": xml_file_path,
                        "root_element": root_element,
                    },
                    **header,
                    "justification_text": justification_text,
                    "services": services,
                }

                self.logger.info(
                    f"Successfully normalized eClaimLink data (legacy format): "
                    f"{len(services)} services, "
                    f"authorization_id={normalized.get('authorization_id')}"
                )

                return normalized

            # Otherwise return enhanced FHIR Bundle format
            timestamp = datetime.now(timezone.utc).isoformat()
            bundle_id = self._generate_bundle_id(payload, xml_file_path)

            # Create FHIR Bundle entries
            bundle_entries = []

            # 1. Create primary Claim resource
            claim_resource = self._create_claim_resource(
                payload, header, services, justification_text, xml_file_path
            )
            bundle_entries.append(self._create_bundle_entry(claim_resource, "Claim"))

            # 2. Extract and create Condition resources
            conditions = self._extract_conditions(
                payload,
                services,
                justification_text,
                claim_resource["id"],
                xml_file_path,
            )
            for condition in conditions:
                bundle_entries.append(self._create_bundle_entry(condition, "Condition"))

            # 3. Extract and create Observation resources
            observations = self._extract_observations(
                justification_text, services, claim_resource["id"], xml_file_path
            )
            for observation in observations:
                bundle_entries.append(
                    self._create_bundle_entry(observation, "Observation")
                )

            # 4. Extract and create MedicationStatement resources
            medications = self._extract_medications(
                justification_text, claim_resource["id"], xml_file_path
            )
            for medication in medications:
                bundle_entries.append(
                    self._create_bundle_entry(medication, "MedicationStatement")
                )

            # 5. Extract and create Procedure resources
            procedures = self._extract_procedures(
                services, justification_text, claim_resource["id"], xml_file_path
            )
            for procedure in procedures:
                bundle_entries.append(self._create_bundle_entry(procedure, "Procedure"))

            # Calculate clinical intelligence scores
            clinical_scores = self._calculate_clinical_scores(
                bundle_entries, justification_text
            )

            # Build FHIR Bundle structure
            fhir_bundle = {
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
                "total": len(bundle_entries),
                "entry": bundle_entries,
                "extension": self._create_bundle_extensions(
                    clinical_scores, xml_file_path, root_element
                ),
            }

            self.logger.info(
                f"Successfully created FHIR Bundle with {len(bundle_entries)} resources: "
                f"authorization_id={header.get('authorization_id')}, "
                f"clinical_context_score={clinical_scores.get('clinical_context_score', 0):.2f}"
            )

            return fhir_bundle

        except Exception as e:
            if isinstance(e, (DataNormalizationError, UnsupportedFormatError)):
                raise
            raise DataNormalizationError(
                f"Failed to normalize eClaimLink data to FHIR Bundle: {str(e)}",
                file_path=xml_file_path,
            ) from e

    def _normalize_header(
        self, payload: Dict[str, Any], xml_file_path: Optional[str]
    ) -> Dict[str, Any]:
        """
        Normalize header information from eClaimLink format.

        Args:
            payload: The PriorAuthorizationRequest payload
            xml_file_path: Optional path to XML file for error reporting

        Returns:
            Normalized header data

        Raises:
            DataNormalizationError: If required header fields are missing
        """
        header = payload.get("Header", {})

        if not header:
            raise DataNormalizationError(
                "Missing required Header section in eClaimLink data",
                file_path=xml_file_path,
                field_name="Header",
            )

        return {
            "sender": self._safe_get(
                header,
                "SenderID",
                field_name="Header.SenderID",
                xml_file_path=xml_file_path,
            ),
            "receiver": self._safe_get(
                header,
                "ReceiverID",
                field_name="Header.ReceiverID",
                xml_file_path=xml_file_path,
            ),
            "transaction_date": self._safe_get(
                header,
                "TransactionDateTime",
                field_name="Header.TransactionDateTime",
                xml_file_path=xml_file_path,
            ),
            "authorization_id": self._safe_get(
                header,
                "TransactionID",
                field_name="Header.TransactionID",
                xml_file_path=xml_file_path,
            ),
        }

    def _normalize_service_requests(
        self, payload: Dict[str, Any], xml_file_path: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        Normalize service requests from eClaimLink format.

        Args:
            payload: The PriorAuthorizationRequest payload
            xml_file_path: Optional path to XML file for error reporting

        Returns:
            List of normalized service request data

        Raises:
            DataNormalizationError: If service request data is invalid
        """
        service_requests_container = payload.get("ServiceRequests", {})
        if service_requests_container is None:
            service_requests_container = {}
        service_request_list = service_requests_container.get("ServiceRequest", [])

        # Normalize to list format (XML parser returns dict for single items)
        service_request_list = self._ensure_list(service_request_list)

        normalized_services = []

        for idx, service_request in enumerate(service_request_list, 1):
            try:
                normalized_service = self._normalize_single_service_request(
                    service_request, idx, xml_file_path
                )
                normalized_services.append(normalized_service)

            except Exception as e:
                raise DataNormalizationError(
                    f"Failed to normalize service request {idx}: {str(e)}",
                    file_path=xml_file_path,
                    field_name=f"ServiceRequest[{idx}]",
                ) from e

        self.logger.debug(f"Normalized {len(normalized_services)} service requests")
        return normalized_services

    def _normalize_single_service_request(
        self,
        service_request: Dict[str, Any],
        sequence_id: int,
        xml_file_path: Optional[str],
    ) -> Dict[str, Any]:
        """
        Normalize a single service request from eClaimLink format.

        Args:
            service_request: Single service request data
            sequence_id: Sequential ID for the service
            xml_file_path: Optional path to XML file for error reporting

        Returns:
            Normalized service request data
        """
        # Extract requested amount information
        requested_amount = service_request.get("RequestedAmount", {})
        amount_currency = None
        amount_value = None

        if requested_amount:
            # Handle both attribute and text content formats
            if isinstance(requested_amount, dict):
                amount_currency = requested_amount.get("@currency")
                amount_value = requested_amount.get("#text")
            else:
                amount_value = str(requested_amount)

        return {
            "id": sequence_id,
            "activity_code": self._safe_get(
                service_request,
                "ct:ActivityCode",
                default=None,
                field_name="ActivityCode",
                xml_file_path=xml_file_path,
            ),
            "diagnosis_code": self._safe_get(
                service_request,
                "ct:DiagnosisCode",
                default=None,
                field_name="DiagnosisCode",
                xml_file_path=xml_file_path,
            ),
            "activity_date_time": self._safe_get(
                service_request,
                "ct:ActivityDateTime",
                default=None,
                field_name="ActivityDateTime",
                xml_file_path=xml_file_path,
            ),
            "instructions": self._safe_get(
                service_request,
                "ct:ActivityInstructions",
                default=None,
                xml_file_path=xml_file_path,
            ),
            "requested_amount_currency": amount_currency,
            "requested_amount_value": amount_value,
            # Additional metadata for traceability
            "source_format": self.FORMAT_NAME,
            "source_schema_version": self.SCHEMA_VERSION,
        }

    def get_format_info(self) -> Dict[str, Any]:
        """
        Get detailed information about this format.

        Returns:
            Dictionary with format information
        """
        return {
            "format_name": self.FORMAT_NAME,
            "schema_version": self.SCHEMA_VERSION,
            "authority": "Dubai Health Authority (DHA)",
            "system": "eClaimLink",
            "description": "Prior authorization request format for UAE healthcare",
            "supported_root_elements": self.SUPPORTED_ROOT_ELEMENTS,
            "typical_use_cases": [
                "Prior authorization requests",
                "Treatment approval requests",
                "Medical procedure authorization",
            ],
        }

    def validate_business_rules(self, normalized_data: Dict[str, Any]) -> List[str]:
        """
        Validate business rules specific to eClaimLink format.

        Args:
            normalized_data: Normalized data to validate

        Returns:
            List of business rule validation warnings/errors
        """
        warnings = []

        # Check if authorization_id follows expected pattern
        auth_id = normalized_data.get("authorization_id")
        if auth_id and not isinstance(auth_id, str):
            warnings.append("Authorization ID should be a string")

        # Check if services are present
        services = normalized_data.get("services", [])
        if not services:
            warnings.append("No services found in authorization request")

        # Validate service-level data
        for idx, service in enumerate(services, 1):
            if not service.get("activity_code"):
                warnings.append(f"Service {idx} missing activity code")

            if not service.get("diagnosis_code"):
                warnings.append(f"Service {idx} missing diagnosis code")

            # Check amount format
            amount_value = service.get("requested_amount_value")
            if amount_value:
                try:
                    float(amount_value)
                except (ValueError, TypeError):
                    warnings.append(
                        f"Service {idx} has invalid amount format: {amount_value}"
                    )

        return warnings

    # ========================================================================
    # ENHANCED CLINICAL DATA EXTRACTION METHODS
    # ========================================================================

    def _generate_bundle_id(
        self, payload: Dict[str, Any], xml_file_path: Optional[str]
    ) -> str:
        """
        Generate a unique bundle ID for the FHIR Bundle.

        Args:
            payload: The XML payload
            xml_file_path: Optional path to XML file

        Returns:
            Unique bundle identifier
        """
        header = payload.get("Header", {})
        transaction_id = header.get("TransactionID", str(uuid.uuid4())[:8])
        timestamp = datetime.now().strftime("%Y%m%d")
        return f"eClaimLink-Bundle-{transaction_id}-{timestamp}"

    def _create_bundle_entry(
        self, resource: Dict[str, Any], resource_type: str
    ) -> Dict[str, Any]:
        """
        Create a FHIR Bundle entry for a resource.

        Args:
            resource: The FHIR resource
            resource_type: Type of FHIR resource

        Returns:
            Bundle entry structure
        """
        return {
            "fullUrl": f"urn:uuid:{resource['id']}",
            "resource": resource,
            "search": {"mode": "match", "score": 1.0},
        }

    def _create_claim_resource(
        self,
        payload: Dict[str, Any],
        header: Dict[str, Any],
        services: List[Dict[str, Any]],
        justification_text: str,
        xml_file_path: Optional[str],
    ) -> Dict[str, Any]:
        """
        Create the primary Claim FHIR resource from eClaimLink data.

        Args:
            payload: The XML payload
            header: Normalized header data
            services: Normalized services data
            justification_text: Clinical justification text
            xml_file_path: Optional path to XML file

        Returns:
            FHIR Claim resource
        """
        claim_id = header.get("authorization_id", str(uuid.uuid4())[:8])
        timestamp = datetime.now(timezone.utc).isoformat()

        # Extract patient information
        patient_info = payload.get("Patient", {})
        patient_id = patient_info.get("PatientID", "unknown-patient")
        national_id = patient_info.get("NationalID")

        # Extract provider information
        provider_info = payload.get("Provider", {})
        provider_id = provider_info.get("ProviderID", "unknown-provider")

        # Build diagnosis array from services
        diagnoses = []
        sequence = 1

        for service in services:
            diagnosis_code = service.get("diagnosis_code")
            if diagnosis_code:
                diagnoses.append(
                    {
                        "sequence": sequence,
                        "diagnosisCodeableConcept": {
                            "coding": [
                                {
                                    "system": "http://hl7.org/fhir/sid/icd-10-am",
                                    "code": diagnosis_code,
                                    "display": f"ICD-10-AM: {diagnosis_code}",
                                }
                            ],
                            "text": f"Diagnosis: {diagnosis_code}",
                        },
                        "type": [
                            {
                                "coding": [
                                    {
                                        "system": "http://terminology.hl7.org/CodeSystem/ex-diagnosistype",
                                        "code": "principal"
                                        if sequence == 1
                                        else "secondary",
                                    }
                                ]
                            }
                        ],
                    }
                )
                sequence += 1

        # Build item array from services
        items = []
        for service in services:
            activity_code = service.get("activity_code")
            if activity_code:
                item = {
                    "sequence": service.get("id", 1),
                    "productOrService": {
                        "coding": [
                            {
                                "system": "http://www.ama-assn.org/go/cpt",
                                "code": activity_code,
                                "display": f"CPT: {activity_code}",
                            }
                        ],
                        "text": f"Service: {activity_code}",
                    },
                }

                # Add service date if available
                if service.get("activity_date_time"):
                    item["servicedDate"] = service["activity_date_time"]

                # Add amount if available
                if service.get("requested_amount_value") and service.get(
                    "requested_amount_currency"
                ):
                    item["unitPrice"] = {
                        "value": float(service["requested_amount_value"]),
                        "currency": service["requested_amount_currency"],
                    }
                    item["net"] = item["unitPrice"]

                items.append(item)

        # Supporting information with clinical justification
        supporting_info = []
        if justification_text:
            supporting_info.append(
                {
                    "sequence": 1,
                    "category": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/claiminformationcategory",
                                "code": "info",
                            }
                        ]
                    },
                    "valueString": justification_text,
                }
            )

        claim_resource = {
            "resourceType": "Claim",
            "id": claim_id,
            "meta": {
                "profile": ["https://nazmito.com/fhir/StructureDefinition/uae-claim"],
                "source": "eClaimLink",
                "lastUpdated": timestamp,
            },
            "identifier": [
                {
                    "use": "official",
                    "system": "https://nazmito.com/identifiers/eclaim-transaction",
                    "value": claim_id,
                }
            ],
            "status": "active",
            "type": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/claim-type",
                        "code": "professional",
                    }
                ]
            },
            "use": "preauthorization",
            "patient": {
                "reference": f"Patient/{patient_id}",
                "identifier": {
                    "system": "https://nazmito.com/identifiers/uae-national-id",
                    "value": national_id,
                }
                if national_id
                else None,
            },
            "created": header.get("transaction_date", timestamp),
            "provider": {"reference": f"Organization/{provider_id}"},
            "billablePeriod": {"start": header.get("transaction_date", timestamp)},
            "diagnosis": diagnoses,
            "item": items,
            "supportingInfo": supporting_info,
            "extension": [
                {
                    "url": "https://nazmito.com/fhir/StructureDefinition/source-mapping",
                    "extension": [
                        {
                            "url": "source-field",
                            "valueString": "PriorAuthorizationRequest",
                        },
                        {
                            "url": "extraction-method",
                            "valueString": "direct-xml-mapping",
                        },
                        {"url": "confidence-score", "valueDecimal": 0.95},
                    ],
                },
                {
                    "url": "https://nazmito.com/fhir/StructureDefinition/emirate-authority",
                    "valueString": "Dubai Health Authority",
                },
            ],
        }

        # Clean up None values
        if claim_resource["patient"]["identifier"] is None:
            del claim_resource["patient"]["identifier"]

        return claim_resource


if __name__ == "__main__":
    """
    Standalone testing and debugging for eClaimLink ingestor.
    
    This section enables step-by-step debugging of the eClaimLink processing pipeline
    with detailed outputs showing FHIR resource extraction and clinical intelligence scoring.
    """
    import json
    import os
    from pathlib import Path
    
    # Setup logging for detailed debug output
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    print("=" * 80)
    print("eClaimLink Ingestor - Debug Mode")
    print("=" * 80)
    
    # Configuration
    schema_path = "schemas/CommonTypes_20191113.xsd"
    sample_file = "samples/eclaim_link_request.xml"
    
    # Check if files exist
    if not os.path.exists(sample_file):
        print(f"❌ Sample file not found: {sample_file}")
        print("Please ensure the sample file exists before running debug mode.")
        exit(1)
    
    if not os.path.exists(schema_path):
        print(f"⚠️  Schema file not found: {schema_path}")
        print("Continuing without schema validation...")
        schema_path = None
    
    try:
        print("\n🔧 Step 1: Initialize eClaimLink Ingestor")
        print("-" * 50)
        
        # Test both output formats
        for output_format in ["legacy", "fhir_bundle"]:
            print(f"\n📋 Testing output format: {output_format}")
            
            ingestor = EClaimLinkIngestor(
                schema_path=schema_path,
                enable_validation=schema_path is not None,
                output_format=output_format
            )
            
            print(f"✅ Ingestor initialized successfully")
            print(f"   Format: {ingestor.FORMAT_NAME}")
            print(f"   Schema Version: {ingestor.SCHEMA_VERSION}")
            print(f"   Output Format: {ingestor.output_format}")
            
            print(f"\n🔧 Step 2: Process XML File ({output_format})")
            print("-" * 50)
            
            result = ingestor.ingest_file(sample_file)
            
            print(f"✅ File processed successfully")
            
            if output_format == "legacy":
                print(f"   Authorization ID: {result.get('authorization_id')}")
                print(f"   Services Count: {len(result.get('services', []))}")
                print(f"   Justification Length: {len(result.get('justification_text', ''))}")
                
                # Show services detail
                services = result.get('services', [])
                for i, service in enumerate(services, 1):
                    print(f"   Service {i}:")
                    print(f"     - Activity Code: {service.get('activity_code')}")
                    print(f"     - Diagnosis Code: {service.get('diagnosis_code')}")
                    print(f"     - Amount: {service.get('requested_amount_value')} {service.get('requested_amount_currency')}")
            
            else:  # fhir_bundle format
                print(f"   Bundle ID: {result.get('id')}")
                print(f"   Resource Type: {result.get('resourceType')}")
                print(f"   Total Resources: {result.get('total')}")
                print(f"   Timestamp: {result.get('timestamp')}")
                
                # Show resource breakdown
                entries = result.get('entry', [])
                resource_counts = {}
                for entry in entries:
                    resource_type = entry.get('resource', {}).get('resourceType')
                    resource_counts[resource_type] = resource_counts.get(resource_type, 0) + 1
                
                print(f"\n   📊 FHIR Resource Breakdown:")
                for resource_type, count in resource_counts.items():
                    print(f"     - {resource_type}: {count}")
                
                # Show clinical intelligence scores
                extensions = result.get('extension', [])
                for ext in extensions:
                    if 'clinical-intelligence' in ext.get('url', ''):
                        for sub_ext in ext.get('extension', []):
                            if sub_ext.get('url') == 'clinical-context-score':
                                score = sub_ext.get('valueDecimal', 0)
                                print(f"   🧠 Clinical Context Score: {score:.2f}")
                            elif sub_ext.get('url') == 'data-quality-score':
                                score = sub_ext.get('valueDecimal', 0)
                                print(f"   📈 Data Quality Score: {score:.2f}")
            
            print(f"\n🔧 Step 3: Business Rule Validation ({output_format})")
            print("-" * 50)
            
            warnings = ingestor.validate_business_rules(result)
            if warnings:
                print(f"⚠️  Business rule warnings found:")
                for warning in warnings:
                    print(f"   - {warning}")
            else:
                print(f"✅ All business rules passed")
            
            print(f"\n💾 Step 4: Save Debug Output ({output_format})")
            print("-" * 50)
            
            debug_output_file = f"debug_output_eclaim_{output_format}.json"
            with open(debug_output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"✅ Debug output saved to: {debug_output_file}")
            print(f"   File size: {os.path.getsize(debug_output_file)} bytes")
            
            print("\n" + "=" * 80)
    
    except Exception as e:
        print(f"\n❌ Error during processing:")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback
        print(f"\n📋 Full traceback:")
        traceback.print_exc()
        exit(1)
    
    print("\n🎉 eClaimLink ingestor debug session completed successfully!")
    print("=" * 80)
