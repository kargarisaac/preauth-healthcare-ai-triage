"""
Shafafiya XML ingestor for 2011 Prior.Authorization format.

This module implements the XML ingestor for the Abu Dhabi Department of Health
Shafafiya 2011 Prior.Authorization format, handling the specific structure
and normalization requirements of this healthcare data format.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from pipelines.base import XMLIngestor
from pipelines.exceptions import DataNormalizationError, UnsupportedFormatError
from pipelines.clinical_extraction_methods import ClinicalExtractionMixin


class ShafafiyaIngestor(ClinicalExtractionMixin, XMLIngestor):
    """
    XML ingestor for Shafafiya 2011 Prior.Authorization format.

    This ingestor handles the Abu Dhabi Department of Health's Shafafiya format,
    which is used for prior authorization data in the UAE healthcare system.
    """

    # Class constants for supported formats
    SUPPORTED_ROOT_ELEMENTS = ["Prior.Authorization"]
    SCHEMA_VERSION = "2011"
    FORMAT_NAME = "Shafafiya"

    def __init__(
        self,
        schema_path: Optional[str] = None,
        enable_validation: bool = True,
        logger: Optional[logging.Logger] = None,
        output_format: str = "legacy",
    ):
        """
        Initialize the Shafafiya ingestor.

        Args:
            schema_path: Path to the XSD schema file for Shafafiya format
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
        Return list of supported root XML elements for Shafafiya format.

        Returns:
            List containing "Prior.Authorization"
        """
        return self.SUPPORTED_ROOT_ELEMENTS.copy()

    def normalize(
        self, parsed_data: Dict[str, Any], xml_file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Normalize Shafafiya 2011 Prior.Authorization data to FHIR Bundle format.

        This enhanced method extracts clinical data to all 5 FHIR resources:
        - Claim: Primary authorization request data
        - Observation: Structured observations from Activity elements
        - MedicationStatement: Medication history from clinical context
        - Condition: Enhanced diagnosis with clinical context
        - Procedure: Historical and authorized procedures

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
            f"Normalizing Shafafiya data to FHIR Bundle from {xml_file_path or 'memory'}"
        )

        # Validate root element
        root_element = next(iter(parsed_data.keys()))
        if root_element not in self.SUPPORTED_ROOT_ELEMENTS:
            raise UnsupportedFormatError(
                f"Unsupported root element '{root_element}' for Shafafiya ingestor",
                file_path=xml_file_path,
                detected_root_element=root_element,
                supported_formats=self.SUPPORTED_ROOT_ELEMENTS,
            )

        try:
            payload = parsed_data[root_element]

            # Extract basic normalized data (always needed)
            header = self._normalize_header(payload, xml_file_path)
            authorization = self._normalize_authorization(payload, xml_file_path)
            activities = self._normalize_activities(payload, xml_file_path)

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
                    **authorization,
                    "services": activities,
                }

                self.logger.info(
                    f"Successfully normalized Shafafiya data (legacy format): "
                    f"{len(activities)} activities, "
                    f"authorization_id={normalized.get('authorization_id')}"
                )

                return normalized

            # Otherwise return enhanced FHIR Bundle format
            timestamp = datetime.now(timezone.utc).isoformat()
            bundle_id = self._generate_shafafiya_bundle_id(payload, xml_file_path)

            # Extract clinical context from comments
            clinical_comments = authorization.get("comments", "")

            # Create FHIR Bundle entries
            bundle_entries = []

            # 1. Create primary Claim resource
            claim_resource = self._create_shafafiya_claim_resource(
                payload,
                header,
                authorization,
                activities,
                clinical_comments,
                xml_file_path,
            )
            bundle_entries.append(self._create_bundle_entry(claim_resource, "Claim"))

            # 2. Extract and create Condition resources from diagnosis codes
            conditions = self._extract_shafafiya_conditions(
                payload,
                activities,
                clinical_comments,
                claim_resource["id"],
                xml_file_path,
            )
            for condition in conditions:
                bundle_entries.append(self._create_bundle_entry(condition, "Condition"))

            # 3. Extract and create Observation resources from structured observations
            observations = self._extract_shafafiya_observations(
                activities, clinical_comments, claim_resource["id"], xml_file_path
            )
            for observation in observations:
                bundle_entries.append(
                    self._create_bundle_entry(observation, "Observation")
                )

            # 4. Extract and create MedicationStatement resources
            medications = self._extract_medications(
                clinical_comments, claim_resource["id"], xml_file_path
            )
            for medication in medications:
                bundle_entries.append(
                    self._create_bundle_entry(medication, "MedicationStatement")
                )

            # 5. Extract and create Procedure resources
            procedures = self._extract_shafafiya_procedures(
                activities, clinical_comments, claim_resource["id"], xml_file_path
            )
            for procedure in procedures:
                bundle_entries.append(self._create_bundle_entry(procedure, "Procedure"))

            # Calculate clinical intelligence scores
            clinical_scores = self._calculate_clinical_scores(
                bundle_entries, clinical_comments
            )

            # Build FHIR Bundle structure
            fhir_bundle = {
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
                "total": len(bundle_entries),
                "entry": bundle_entries,
                "extension": self._create_shafafiya_bundle_extensions(
                    clinical_scores, xml_file_path, root_element
                ),
            }

            self.logger.info(
                f"Successfully created FHIR Bundle with {len(bundle_entries)} resources: "
                f"authorization_id={authorization.get('authorization_id')}, "
                f"clinical_context_score={clinical_scores.get('clinical_context_score', 0):.2f}"
            )

            return fhir_bundle

        except Exception as e:
            if isinstance(e, (DataNormalizationError, UnsupportedFormatError)):
                raise
            raise DataNormalizationError(
                f"Failed to normalize Shafafiya data to FHIR Bundle: {str(e)}",
                file_path=xml_file_path,
            ) from e

    def _normalize_header(
        self, payload: Dict[str, Any], xml_file_path: Optional[str]
    ) -> Dict[str, Any]:
        """
        Normalize header information from Shafafiya format.

        Args:
            payload: The Prior.Authorization payload
            xml_file_path: Optional path to XML file for error reporting

        Returns:
            Normalized header data

        Raises:
            DataNormalizationError: If required header fields are missing
        """
        header = payload.get("Header", {})

        if not header:
            raise DataNormalizationError(
                "Missing required Header section in Shafafiya data",
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
                "TransactionDate",
                field_name="Header.TransactionDate",
                xml_file_path=xml_file_path,
            ),
            "record_count": self._safe_get(
                header, "RecordCount", default=None, xml_file_path=xml_file_path
            ),
            "disposition_flag": self._safe_get(
                header, "DispositionFlag", default=None, xml_file_path=xml_file_path
            ),
        }

    def _normalize_authorization(
        self, payload: Dict[str, Any], xml_file_path: Optional[str]
    ) -> Dict[str, Any]:
        """
        Normalize authorization information from Shafafiya format.

        Args:
            payload: The Prior.Authorization payload
            xml_file_path: Optional path to XML file for error reporting

        Returns:
            Normalized authorization data

        Raises:
            DataNormalizationError: If authorization section is missing
        """
        authorization = payload.get("Authorization", {})

        if not authorization:
            raise DataNormalizationError(
                "Missing required Authorization section in Shafafiya data",
                file_path=xml_file_path,
                field_name="Authorization",
            )

        return {
            "result": self._safe_get(
                authorization, "Result", default=None, xml_file_path=xml_file_path
            ),
            "authorization_id": self._safe_get(
                authorization,
                "ID",
                field_name="Authorization.ID",
                xml_file_path=xml_file_path,
            ),
            "id_payer": self._safe_get(
                authorization, "IDPayer", default=None, xml_file_path=xml_file_path
            ),
            "denial_code": self._safe_get(
                authorization, "DenialCode", default=None, xml_file_path=xml_file_path
            ),
            "start": self._safe_get(
                authorization,
                "Start",
                field_name="Authorization.Start",
                xml_file_path=xml_file_path,
            ),
            "end": self._safe_get(
                authorization,
                "End",
                field_name="Authorization.End",
                xml_file_path=xml_file_path,
            ),
            "limit": self._safe_get(
                authorization, "Limit", default=None, xml_file_path=xml_file_path
            ),
            "comments": self._safe_get(
                authorization, "Comments", default=None, xml_file_path=xml_file_path
            ),
        }

    def _normalize_activities(
        self, payload: Dict[str, Any], xml_file_path: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        Normalize activities from Shafafiya format.

        Args:
            payload: The Prior.Authorization payload
            xml_file_path: Optional path to XML file for error reporting

        Returns:
            List of normalized activity data

        Raises:
            DataNormalizationError: If activity data is invalid
        """
        authorization = payload.get("Authorization", {})
        activities = authorization.get("Activity", [])

        # Normalize to list format (XML parser returns dict for single items)
        activities = self._ensure_list(activities)

        normalized_services = []

        for activity in activities:
            try:
                normalized_activity = self._normalize_single_activity(
                    activity, xml_file_path
                )
                normalized_services.append(normalized_activity)

            except Exception as e:
                activity_id = activity.get("ID", "unknown")
                raise DataNormalizationError(
                    f"Failed to normalize activity {activity_id}: {str(e)}",
                    file_path=xml_file_path,
                    field_name=f"Activity[{activity_id}]",
                ) from e

        self.logger.debug(f"Normalized {len(normalized_services)} activities")
        return normalized_services

    def _normalize_single_activity(
        self, activity: Dict[str, Any], xml_file_path: Optional[str]
    ) -> Dict[str, Any]:
        """
        Normalize a single activity from Shafafiya format.

        Args:
            activity: Single activity data
            xml_file_path: Optional path to XML file for error reporting

        Returns:
            Normalized activity data
        """
        # Extract observations if present
        observations = self._normalize_observations(activity.get("Observation", []))

        return {
            "id": self._safe_get(
                activity, "ID", field_name="Activity.ID", xml_file_path=xml_file_path
            ),
            "type": self._safe_get(
                activity,
                "Type",
                field_name="Activity.Type",
                xml_file_path=xml_file_path,
            ),
            "code": self._safe_get(
                activity,
                "Code",
                field_name="Activity.Code",
                xml_file_path=xml_file_path,
            ),
            "quantity": self._safe_get(
                activity, "Quantity", default=None, xml_file_path=xml_file_path
            ),
            "net": self._safe_get(
                activity, "Net", field_name="Activity.Net", xml_file_path=xml_file_path
            ),
            "list": self._safe_get(
                activity, "List", default=None, xml_file_path=xml_file_path
            ),
            "patient_share": self._safe_get(
                activity, "PatientShare", default=None, xml_file_path=xml_file_path
            ),
            "payment_amount": self._safe_get(
                activity,
                "PaymentAmount",
                field_name="Activity.PaymentAmount",
                xml_file_path=xml_file_path,
            ),
            "denial_code": self._safe_get(
                activity, "DenialCode", default=None, xml_file_path=xml_file_path
            ),
            "observations": observations,
            # Additional metadata for traceability
            "source_format": self.FORMAT_NAME,
            "source_schema_version": self.SCHEMA_VERSION,
        }

    def _normalize_observations(self, observations_data: Any) -> List[Dict[str, Any]]:
        """
        Normalize observations from Shafafiya format.

        Args:
            observations_data: Raw observations data (can be dict, list, or None)

        Returns:
            List of normalized observation data
        """
        observations = self._ensure_list(observations_data)
        normalized_observations = []

        for obs in observations:
            if isinstance(obs, dict):
                normalized_obs = {
                    "type": obs.get("Type"),
                    "code": obs.get("Code"),
                    "value": obs.get("Value"),
                    "value_type": obs.get("ValueType"),
                }
                normalized_observations.append(normalized_obs)

        return normalized_observations

    def get_format_info(self) -> Dict[str, Any]:
        """
        Get detailed information about this format.

        Returns:
            Dictionary with format information
        """
        return {
            "format_name": self.FORMAT_NAME,
            "schema_version": self.SCHEMA_VERSION,
            "authority": "Abu Dhabi Department of Health (DoH)",
            "system": "Shafafiya",
            "description": "Prior authorization format for Abu Dhabi healthcare system",
            "supported_root_elements": self.SUPPORTED_ROOT_ELEMENTS,
            "typical_use_cases": [
                "Prior authorization responses",
                "Authorization status updates",
                "Treatment approval confirmations",
            ],
        }

    def validate_business_rules(self, normalized_data: Dict[str, Any]) -> List[str]:
        """
        Validate business rules specific to Shafafiya format.

        Args:
            normalized_data: Normalized data to validate

        Returns:
            List of business rule validation warnings/errors
        """
        warnings = []

        # Check authorization result
        result = normalized_data.get("result")
        if result and result.lower() not in ["yes", "no", "pending"]:
            warnings.append(f"Unexpected authorization result: {result}")

        # Check date format consistency
        start_date = normalized_data.get("start")
        end_date = normalized_data.get("end")
        if start_date and end_date:
            # Basic date format check (could be enhanced with proper date parsing)
            if not (isinstance(start_date, str) and isinstance(end_date, str)):
                warnings.append("Start and end dates should be strings")

        # Check record count consistency
        record_count = normalized_data.get("record_count")
        services_count = len(normalized_data.get("services", []))
        if record_count and str(record_count) != str(services_count):
            warnings.append(
                f"Record count mismatch: header says {record_count}, "
                f"but found {services_count} services"
            )

        # Validate activity-level data
        services = normalized_data.get("services", [])
        for service in services:
            activity_id = service.get("id")
            activity_type = service.get("type")

            if not activity_id:
                warnings.append("Activity missing ID")

            if not activity_type:
                warnings.append(f"Activity {activity_id} missing type")

            # Check payment amounts
            net = service.get("net")
            payment_amount = service.get("payment_amount")

            try:
                if net:
                    float(net)
                if payment_amount:
                    float(payment_amount)
            except (ValueError, TypeError):
                warnings.append(f"Activity {activity_id} has invalid amount format")

        return warnings

    # ========================================================================
    # SHAFAFIYA-SPECIFIC CLINICAL DATA EXTRACTION METHODS
    # ========================================================================

    def _generate_shafafiya_bundle_id(
        self, payload: Dict[str, Any], xml_file_path: Optional[str]
    ) -> str:
        """
        Generate a unique bundle ID for the Shafafiya FHIR Bundle.

        Args:
            payload: The XML payload
            xml_file_path: Optional path to XML file

        Returns:
            Unique bundle identifier
        """
        header = payload.get("Header", {})
        auth_data = payload.get("Authorization", {})
        auth_id = auth_data.get("ID", str(uuid.uuid4())[:8])
        timestamp = datetime.now().strftime("%Y%m%d")
        return f"Shafafiya-Bundle-{auth_id}-{timestamp}"

    def _create_shafafiya_claim_resource(
        self,
        payload: Dict[str, Any],
        header: Dict[str, Any],
        authorization: Dict[str, Any],
        activities: List[Dict[str, Any]],
        clinical_comments: str,
        xml_file_path: Optional[str],
    ) -> Dict[str, Any]:
        """
        Create the primary Claim FHIR resource from Shafafiya data.

        Args:
            payload: The XML payload
            header: Normalized header data
            authorization: Normalized authorization data
            activities: Normalized activities data
            clinical_comments: Clinical comments text
            xml_file_path: Optional path to XML file

        Returns:
            FHIR Claim resource
        """
        claim_id = authorization.get("authorization_id", str(uuid.uuid4())[:8])
        timestamp = datetime.now(timezone.utc).isoformat()

        # Extract patient information - Shafafiya doesn't have explicit patient section
        # Will need to be inferred from other data or use placeholder
        patient_id = "shafafiya-patient"  # Placeholder

        # Extract provider information - also not explicit in Shafafiya format
        provider_id = "shafafiya-provider"  # Placeholder

        # Build diagnosis array from activities that have diagnosis-related codes
        diagnoses = []
        sequence = 1

        for activity in activities:
            activity_code = activity.get("code")
            activity_type = activity.get("type")

            # Check if this activity represents a diagnosis
            if activity_type and str(activity_type) in [
                "1",
                "2",
            ]:  # Assuming type 1,2 are diagnosis-related
                diagnoses.append(
                    {
                        "sequence": sequence,
                        "diagnosisCodeableConcept": {
                            "coding": [
                                {
                                    "system": "http://hl7.org/fhir/sid/icd-10-am",
                                    "code": activity_code,
                                    "display": f"Activity Code: {activity_code}",
                                }
                            ],
                            "text": f"Diagnosis from activity: {activity_code}",
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

        # Build item array from activities
        items = []
        for activity in activities:
            activity_code = activity.get("code")
            if activity_code:
                item = {
                    "sequence": activity.get("id", 1),
                    "productOrService": {
                        "coding": [
                            {
                                "system": "https://nazmito.com/code-systems/shafafiya-activity",
                                "code": activity_code,
                                "display": f"Shafafiya Activity: {activity_code}",
                            }
                        ],
                        "text": f"Activity: {activity_code}",
                    },
                }

                # Add quantity if available
                if activity.get("quantity"):
                    item["quantity"] = {"value": float(activity["quantity"])}

                # Add amount information
                if activity.get("net"):
                    item["net"] = {
                        "value": float(activity["net"]),
                        "currency": "AED",  # Assuming AED for UAE
                    }
                    item["unitPrice"] = item["net"]

                if activity.get("payment_amount"):
                    item["unitPrice"] = {
                        "value": float(activity["payment_amount"]),
                        "currency": "AED",
                    }

                items.append(item)

        # Supporting information with clinical comments
        supporting_info = []
        if clinical_comments:
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
                    "valueString": clinical_comments,
                }
            )

        claim_resource = {
            "resourceType": "Claim",
            "id": claim_id,
            "meta": {
                "profile": ["https://nazmito.com/fhir/StructureDefinition/uae-claim"],
                "source": "Shafafiya",
                "lastUpdated": timestamp,
            },
            "identifier": [
                {
                    "use": "official",
                    "system": "https://nazmito.com/identifiers/shafafiya-authorization",
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
            "patient": {"reference": f"Patient/{patient_id}"},
            "created": header.get("transaction_date", timestamp),
            "provider": {"reference": f"Organization/{provider_id}"},
            "billablePeriod": {
                "start": authorization.get("start", timestamp),
                "end": authorization.get("end", timestamp),
            },
            "diagnosis": diagnoses,
            "item": items,
            "supportingInfo": supporting_info,
            "extension": [
                {
                    "url": "https://nazmito.com/fhir/StructureDefinition/source-mapping",
                    "extension": [
                        {"url": "source-field", "valueString": "Prior.Authorization"},
                        {
                            "url": "extraction-method",
                            "valueString": "direct-xml-mapping",
                        },
                        {"url": "confidence-score", "valueDecimal": 0.95},
                    ],
                },
                {
                    "url": "https://nazmito.com/fhir/StructureDefinition/emirate-authority",
                    "valueString": "Abu Dhabi Department of Health",
                },
                {
                    "url": "https://nazmito.com/fhir/StructureDefinition/authorization-result",
                    "valueString": authorization.get("result", "unknown"),
                },
            ],
        }

        return claim_resource

    def _extract_shafafiya_conditions(
        self,
        payload: Dict[str, Any],
        activities: List[Dict[str, Any]],
        clinical_comments: str,
        claim_id: str,
        xml_file_path: Optional[str],
    ) -> List[Dict[str, Any]]:
        """
        Extract Condition resources from Shafafiya activity codes and clinical text.

        Args:
            payload: The XML payload
            activities: Normalized activities data
            clinical_comments: Clinical comments text
            claim_id: Reference to parent claim
            xml_file_path: Optional path to XML file

        Returns:
            List of FHIR Condition resources
        """
        conditions = []
        sequence = 1
        timestamp = datetime.now(timezone.utc).isoformat()

        # Extract conditions from diagnosis-type activities
        for activity in activities:
            activity_code = activity.get("code")
            activity_type = activity.get("type")

            # Check if this is a diagnosis-related activity
            if activity_code and activity_type and str(activity_type) in ["1", "2"]:
                condition_id = f"shafafiya-condition-{activity_code}-{sequence}"

                # Enhanced clinical context from text analysis
                clinical_context = self._analyze_condition_context(
                    activity_code, clinical_comments
                )

                condition = {
                    "resourceType": "Condition",
                    "id": condition_id,
                    "meta": {
                        "profile": [
                            "https://nazmito.com/fhir/StructureDefinition/uae-condition"
                        ],
                        "source": "Shafafiya",
                    },
                    "identifier": [
                        {
                            "system": "https://nazmito.com/identifiers/condition",
                            "value": condition_id,
                        }
                    ],
                    "clinicalStatus": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                                "code": clinical_context.get(
                                    "clinical_status", "active"
                                ),
                            }
                        ]
                    },
                    "verificationStatus": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                                "code": "confirmed",
                            }
                        ]
                    },
                    "category": [
                        {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                                    "code": "encounter-diagnosis",
                                }
                            ]
                        }
                    ],
                    "code": {
                        "coding": [
                            {
                                "system": "https://nazmito.com/code-systems/shafafiya-activity",
                                "code": activity_code,
                                "display": clinical_context.get(
                                    "display_name",
                                    f"Shafafiya Activity: {activity_code}",
                                ),
                            }
                        ],
                        "text": clinical_context.get(
                            "condition_text",
                            f"Condition from activity: {activity_code}",
                        ),
                    },
                    "subject": {"reference": f"Patient/shafafiya-patient"},
                    "recordedDate": timestamp,
                    "extension": [
                        {
                            "url": "https://nazmito.com/fhir/StructureDefinition/clinical-context-score",
                            "valueDecimal": clinical_context.get(
                                "confidence_score", 0.8
                            ),
                        },
                        {
                            "url": "https://nazmito.com/fhir/StructureDefinition/source-mapping",
                            "extension": [
                                {
                                    "url": "source-field",
                                    "valueString": "Authorization/Activity",
                                },
                                {
                                    "url": "extraction-method",
                                    "valueString": "activity-code-mapping-with-nlp-enhancement",
                                },
                            ],
                        },
                    ],
                }

                # Add clinical severity if detected
                if clinical_context.get("severity"):
                    condition["severity"] = {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": clinical_context["severity"]["code"],
                                "display": clinical_context["severity"]["display"],
                            }
                        ],
                        "text": clinical_context["severity"]["text"],
                    }

                # Add onset information if detected
                if clinical_context.get("onset_date"):
                    condition["onsetDateTime"] = clinical_context["onset_date"]
                elif clinical_context.get("onset_text"):
                    condition["onsetString"] = clinical_context["onset_text"]

                # Add clinical notes
                if clinical_context.get("notes"):
                    condition["note"] = [
                        {"text": clinical_context["notes"], "time": timestamp}
                    ]

                conditions.append(condition)
                sequence += 1

        return conditions

    def _extract_shafafiya_observations(
        self,
        activities: List[Dict[str, Any]],
        clinical_comments: str,
        claim_id: str,
        xml_file_path: Optional[str],
    ) -> List[Dict[str, Any]]:
        """
        Extract Observation resources from Shafafiya structured observations and clinical text.

        Args:
            activities: Normalized activities data
            clinical_comments: Clinical comments text
            claim_id: Reference to parent claim
            xml_file_path: Optional path to XML file

        Returns:
            List of FHIR Observation resources
        """
        observations = []
        timestamp = datetime.now(timezone.utc).isoformat()

        # Extract structured observations from activities
        for activity in activities:
            activity_observations = activity.get("observations", [])

            for idx, obs in enumerate(activity_observations, 1):
                if obs.get("type") and obs.get("code"):
                    observation_id = f"shafafiya-obs-{obs['code']}-{idx}"

                    observation = {
                        "resourceType": "Observation",
                        "id": observation_id,
                        "meta": {
                            "profile": [
                                "https://nazmito.com/fhir/StructureDefinition/uae-observation"
                            ],
                            "source": "Shafafiya",
                        },
                        "identifier": [
                            {
                                "system": "https://nazmito.com/identifiers/observation",
                                "value": observation_id,
                            }
                        ],
                        "status": "final",
                        "category": [
                            {
                                "coding": [
                                    {
                                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                        "code": self._map_shafafiya_obs_category(
                                            obs.get("type", "")
                                        ),
                                    }
                                ]
                            }
                        ],
                        "code": {
                            "coding": [
                                {
                                    "system": "https://nazmito.com/code-systems/shafafiya-observation",
                                    "code": obs["code"],
                                    "display": f"Shafafiya Observation: {obs['code']}",
                                }
                            ],
                            "text": f"Observation: {obs.get('type', '')} - {obs['code']}",
                        },
                        "subject": {"reference": f"Patient/shafafiya-patient"},
                        "basedOn": [{"reference": f"Claim/{claim_id}"}],
                        "effectiveDateTime": timestamp,
                        "extension": [
                            {
                                "url": "https://nazmito.com/fhir/StructureDefinition/clinical-context-score",
                                "valueDecimal": 0.9,  # High confidence for structured data
                            },
                            {
                                "url": "https://nazmito.com/fhir/StructureDefinition/source-mapping",
                                "extension": [
                                    {
                                        "url": "source-field",
                                        "valueString": "Activity/Observation",
                                    },
                                    {
                                        "url": "extraction-method",
                                        "valueString": "structured-observation-mapping",
                                    },
                                ],
                            },
                        ],
                    }

                    # Add value based on observation data
                    if obs.get("value"):
                        value = obs["value"]
                        value_type = obs.get("value_type", "").upper()

                        if value_type in ["NUMERIC", "NUMBER", "DECIMAL"]:
                            try:
                                numeric_value = float(value)
                                observation["valueQuantity"] = {
                                    "value": numeric_value,
                                    "unit": self._infer_unit_from_obs_code(obs["code"]),
                                    "system": "http://unitsofmeasure.org",
                                }
                            except (ValueError, TypeError):
                                observation["valueString"] = str(value)
                        elif value_type in ["BOOLEAN", "BOOL"]:
                            observation["valueBoolean"] = str(value).lower() in [
                                "true",
                                "1",
                                "yes",
                            ]
                        else:
                            observation["valueString"] = str(value)

                    observations.append(observation)

        # Extract observations from clinical comments using NLP
        text_observations = self._extract_clinical_observations(clinical_comments)

        for idx, obs_data in enumerate(text_observations, 1):
            observation_id = f"shafafiya-text-obs-{obs_data['type']}-{idx}"

            observation = {
                "resourceType": "Observation",
                "id": observation_id,
                "meta": {
                    "profile": [
                        "https://nazmito.com/fhir/StructureDefinition/uae-observation"
                    ],
                    "source": "clinical-text",
                },
                "identifier": [
                    {
                        "system": "https://nazmito.com/identifiers/observation",
                        "value": observation_id,
                    }
                ],
                "status": obs_data.get("status", "final"),
                "category": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                "code": obs_data.get("category", "survey"),
                            }
                        ]
                    }
                ],
                "code": {
                    "coding": obs_data.get("coding", []),
                    "text": obs_data.get(
                        "display_text", "Clinical observation from comments"
                    ),
                },
                "subject": {"reference": f"Patient/shafafiya-patient"},
                "basedOn": [{"reference": f"Claim/{claim_id}"}],
                "extension": [
                    {
                        "url": "https://nazmito.com/fhir/StructureDefinition/clinical-context-score",
                        "valueDecimal": obs_data.get("confidence_score", 0.7),
                    },
                    {
                        "url": "https://nazmito.com/fhir/StructureDefinition/source-mapping",
                        "extension": [
                            {
                                "url": "source-field",
                                "valueString": "Authorization/Comments",
                            },
                            {
                                "url": "extraction-method",
                                "valueString": "nlp-medical-entity-recognition",
                            },
                        ],
                    },
                ],
            }

            # Add value based on observation type
            if obs_data.get("value_quantity"):
                observation["valueQuantity"] = obs_data["value_quantity"]
            elif obs_data.get("value_string"):
                observation["valueString"] = obs_data["value_string"]
            elif obs_data.get("value_boolean") is not None:
                observation["valueBoolean"] = obs_data["value_boolean"]

            # Add effective date if available
            if obs_data.get("effective_date"):
                observation["effectiveDateTime"] = obs_data["effective_date"]
            else:
                observation["effectiveDateTime"] = timestamp

            # Add interpretation if available
            if obs_data.get("interpretation"):
                observation["interpretation"] = [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                                "code": obs_data["interpretation"]["code"],
                                "display": obs_data["interpretation"]["display"],
                            }
                        ]
                    }
                ]

            observations.append(observation)

        return observations

    def _extract_shafafiya_procedures(
        self,
        activities: List[Dict[str, Any]],
        clinical_comments: str,
        claim_id: str,
        xml_file_path: Optional[str],
    ) -> List[Dict[str, Any]]:
        """
        Extract Procedure resources from Shafafiya activity codes and clinical timeline.

        Args:
            activities: Normalized activities data
            clinical_comments: Clinical comments text
            claim_id: Reference to parent claim
            xml_file_path: Optional path to XML file

        Returns:
            List of FHIR Procedure resources
        """
        procedures = []
        timestamp = datetime.now(timezone.utc).isoformat()

        # Extract procedures from activities
        for activity in activities:
            activity_code = activity.get("code")
            activity_type = activity.get("type")

            # Check if this is a procedure-type activity (assuming type 3,4,5 are procedures)
            if (
                activity_code
                and activity_type
                and str(activity_type) in ["3", "4", "5"]
            ):
                procedure_id = f"shafafiya-procedure-{activity_code}"

                procedure = {
                    "resourceType": "Procedure",
                    "id": procedure_id,
                    "meta": {
                        "profile": [
                            "https://nazmito.com/fhir/StructureDefinition/uae-procedure"
                        ],
                        "source": "Shafafiya",
                    },
                    "identifier": [
                        {
                            "system": "https://nazmito.com/identifiers/procedure",
                            "value": procedure_id,
                        }
                    ],
                    "basedOn": [{"reference": f"Claim/{claim_id}"}],
                    "status": "completed",  # Shafafiya procedures are typically completed/authorized
                    "code": {
                        "coding": [
                            {
                                "system": "https://nazmito.com/code-systems/shafafiya-activity",
                                "code": activity_code,
                                "display": f"Shafafiya Procedure: {activity_code}",
                            }
                        ],
                        "text": f"Procedure: {activity_code}",
                    },
                    "subject": {"reference": f"Patient/shafafiya-patient"},
                    "performedDateTime": timestamp,
                    "extension": [
                        {
                            "url": "https://nazmito.com/fhir/StructureDefinition/source-mapping",
                            "extension": [
                                {"url": "source-field", "valueString": "Activity/Code"},
                                {
                                    "url": "extraction-method",
                                    "valueString": "activity-code-procedure-mapping",
                                },
                                {"url": "confidence-score", "valueDecimal": 0.9},
                            ],
                        }
                    ],
                }

                # Add quantity if available
                if activity.get("quantity"):
                    procedure["note"] = [
                        {"text": f"Quantity: {activity['quantity']}", "time": timestamp}
                    ]

                procedures.append(procedure)

        # Extract historical procedures from clinical comments
        historical_procedures = self._extract_historical_procedures(
            clinical_comments, claim_id
        )
        procedures.extend(historical_procedures)

        return procedures

    def _map_shafafiya_obs_category(self, obs_type: str) -> str:
        """
        Map Shafafiya observation type to FHIR observation category.

        Args:
            obs_type: Shafafiya observation type

        Returns:
            FHIR observation category code
        """
        type_mapping = {
            "LAB": "laboratory",
            "VITAL": "vital-signs",
            "IMAGING": "imaging",
            "PROCEDURE": "procedure",
            "SURVEY": "survey",
        }

        return type_mapping.get(obs_type.upper(), "survey")

    def _infer_unit_from_obs_code(self, obs_code: str) -> str:
        """
        Infer measurement unit from Shafafiya observation code.

        Args:
            obs_code: Shafafiya observation code

        Returns:
            Measurement unit
        """
        code_unit_mapping = {
            "HBA1C": "%",
            "GLUCOSE": "mg/dL",
            "CHOLESTEROL": "mg/dL",
            "BP_SYS": "mmHg",
            "BP_DIA": "mmHg",
            "WEIGHT": "kg",
            "HEIGHT": "cm",
            "BMI": "kg/m2",
        }

        return code_unit_mapping.get(obs_code.upper(), "")

    def _create_shafafiya_bundle_extensions(
        self,
        clinical_scores: Dict[str, Any],
        xml_file_path: Optional[str],
        root_element: str,
    ) -> List[Dict[str, Any]]:
        """
        Create FHIR Bundle extensions with clinical intelligence scores for Shafafiya.

        Args:
            clinical_scores: Calculated clinical scores
            xml_file_path: Optional path to XML file
            root_element: Root XML element

        Returns:
            List of FHIR extensions
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        return [
            {
                "url": "https://nazmito.com/fhir/StructureDefinition/schema-version",
                "valueString": "v0.2",
            },
            {
                "url": "https://nazmito.com/fhir/StructureDefinition/original-format",
                "valueString": "Shafafiya-2011",
            },
            {
                "url": "https://nazmito.com/fhir/StructureDefinition/data-quality-score",
                "valueDecimal": clinical_scores["data_quality_score"],
            },
            {
                "url": "https://nazmito.com/fhir/StructureDefinition/processing-timestamp",
                "valueDateTime": timestamp,
            },
            {
                "url": "https://nazmito.com/fhir/StructureDefinition/enrichment-score",
                "valueDecimal": clinical_scores["enrichment_score"],
            },
            {
                "url": "https://nazmito.com/fhir/StructureDefinition/ai-confidence",
                "valueDecimal": clinical_scores["ai_confidence"],
            },
            {
                "url": "https://nazmito.com/fhir/StructureDefinition/clinical-context-score",
                "valueDecimal": clinical_scores["clinical_context_score"],
            },
            {
                "url": "https://nazmito.com/fhir/StructureDefinition/record-count",
                "valueInteger": clinical_scores["total_resources"],
            },
            {
                "url": "https://nazmito.com/fhir/StructureDefinition/emirate-authority",
                "valueString": "Abu Dhabi Department of Health",
            },
            {
                "url": "https://nazmito.com/fhir/StructureDefinition/source-mapping",
                "extension": [
                    {"url": "source-file", "valueString": xml_file_path or "memory"},
                    {"url": "root-element", "valueString": root_element},
                    {
                        "url": "processing-method",
                        "valueString": "enhanced-clinical-extraction-shafafiya",
                    },
                ],
            },
        ]


if __name__ == "__main__":
    """
    Standalone testing and debugging for Shafafiya ingestor.
    
    This section enables step-by-step debugging of the Shafafiya processing pipeline
    with detailed outputs showing FHIR resource extraction and clinical intelligence scoring.
    """
    import json
    import os
    
    # Setup logging for detailed debug output
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    print("=" * 80)
    print("Shafafiya Ingestor - Debug Mode")
    print("=" * 80)
    
    # Configuration
    schema_path = "schemas/PriorAuthorization.xsd"
    sample_file = "samples/shafafiya_authorization.xml"
    
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
        print("\n🔧 Step 1: Initialize Shafafiya Ingestor")
        print("-" * 50)
        
        # Test both output formats
        for output_format in ["legacy", "fhir_bundle"]:
            print(f"\n📋 Testing output format: {output_format}")
            
            ingestor = ShafafiyaIngestor(
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
                print(f"   Authorization Result: {result.get('result')}")
                print(f"   Services Count: {len(result.get('services', []))}")
                print(f"   Record Count: {result.get('record_count')}")
                
                # Show activities detail
                services = result.get('services', [])
                for i, service in enumerate(services, 1):
                    print(f"   Activity {i}:")
                    print(f"     - Code: {service.get('code')}")
                    print(f"     - Type: {service.get('type')}")
                    print(f"     - Net Amount: {service.get('net')}")
                    print(f"     - Observations: {len(service.get('observations', []))}")
            
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
                    if 'clinical-context-score' in ext.get('url', ''):
                        score = ext.get('valueDecimal', 0)
                        print(f"   🧠 Clinical Context Score: {score:.2f}")
                    elif 'data-quality-score' in ext.get('url', ''):
                        score = ext.get('valueDecimal', 0)
                        print(f"   📈 Data Quality Score: {score:.2f}")
                    elif 'enrichment-score' in ext.get('url', ''):
                        score = ext.get('valueDecimal', 0)
                        print(f"   ⚡ Enrichment Score: {score:.2f}")
                    elif 'ai-confidence' in ext.get('url', ''):
                        score = ext.get('valueDecimal', 0)
                        print(f"   🤖 AI Confidence: {score:.2f}")
            
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
            
            debug_output_file = f"debug_output_shafafiya_{output_format}.json"
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
    
    print("\n🎉 Shafafiya ingestor debug session completed successfully!")
    print("=" * 80)
