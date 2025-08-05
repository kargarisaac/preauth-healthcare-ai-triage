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
from typing import Dict, Any, List
import xmltodict
from loguru import logger

try:
    from pipelines.data_quality import DataQuality
    from pipelines.canonical_models import (
        CanonicalBundle,
        Patient,
        Provider,
        Service,
        Activity,
        Address,
        InsuranceInfo,
        ClinicalInfo,
        FHIRMeta,
        DataQuality as DataQualityModel,
        QualityScore,
    )
except ImportError:
    # Handle direct execution from pipelines directory
    from data_quality import DataQuality
    from canonical_models import (
        CanonicalBundle,
        Patient,
        Provider,
        Service,
        Activity,
        Address,
        InsuranceInfo,
        ClinicalInfo,
        FHIRMeta,
        DataQuality as DataQualityModel,
        QualityScore,
    )


class BaseProcessor:
    """Base class for XML processors to handle common data extraction."""

    def __init__(self, enable_validation: bool = True):
        """
        Initialize XML processor with optional data quality validation.

        Args:
            enable_validation: Enable data quality validation (default: True)
        """
        self.enable_validation = enable_validation
        if self.enable_validation:
            self.data_quality = DataQuality()

    def _extract_patient_dataclass(self, patient_data: Dict[str, Any]) -> Patient:
        """Extract patient information as dataclass."""
        if not patient_data:
            return Patient()

        # Handle address information
        address_data = patient_data.get("Address", {})
        address = Address(
            street=address_data.get("Street"),
            city=address_data.get("City"),
            emirate=address_data.get("Emirate"),
            postal_code=address_data.get("PostalCode"),
        )

        # Handle insurance policy/details
        insurance_data = patient_data.get(
            "InsurancePolicy", patient_data.get("InsuranceDetails", {})
        )
        insurance = InsuranceInfo(
            policy_number=insurance_data.get(
                "PolicyNumber", insurance_data.get("MemberNumber")
            ),
            payer_name=insurance_data.get("PayerName"),
            policy_holder=insurance_data.get("PolicyHolder"),
            valid_from=insurance_data.get(
                "ValidFrom", insurance_data.get("EffectiveDate")
            ),
            valid_to=insurance_data.get("ValidTo", insurance_data.get("ExpiryDate")),
            coverage_type=insurance_data.get(
                "CoverageType", insurance_data.get("CoverageLevel")
            ),
        )

        # Handle medical history/clinical information
        medical_history = patient_data.get(
            "MedicalHistory", patient_data.get("ClinicalInformation", {})
        )
        conditions = medical_history.get(
            "Condition", medical_history.get("PrimaryDiagnosis")
        )
        if conditions and not isinstance(conditions, list):
            conditions = [conditions]

        clinical_info = ClinicalInfo(
            conditions=conditions or [],
            allergies=medical_history.get("Allergy", medical_history.get("Allergies")),
            current_medications=medical_history.get(
                "CurrentMedications", medical_history.get("CurrentTreatment")
            ),
            vital_signs=medical_history.get("VitalSigns"),
        )

        return Patient(
            member_id=patient_data.get("MemberID", patient_data.get("PersonID")),
            emirates_id=patient_data.get(
                "EmiratesIDNumber", patient_data.get("EmiratesID")
            ),
            first_name=patient_data.get("FirstName"),
            last_name=patient_data.get("LastName"),
            date_of_birth=patient_data.get("DateOfBirth"),
            gender=patient_data.get("Gender"),
            nationality=patient_data.get("Nationality"),
            phone_number=patient_data.get(
                "PhoneNumber", patient_data.get("ContactNumber")
            ),
            email=patient_data.get("Email"),
            weight=patient_data.get("Weight"),
            height=patient_data.get("Height"),
            address=address,
            insurance=insurance,
            clinical_info=clinical_info,
        )

    def _extract_provider_dataclass(self, provider_data: Dict[str, Any]) -> Provider:
        """Extract provider information as dataclass."""
        if not provider_data:
            return Provider()

        # Handle provider address
        address_data = provider_data.get(
            "Address", provider_data.get("FacilityAddress", {})
        )
        address = Address(
            street=address_data.get("Street"),
            city=address_data.get("City"),
            emirate=address_data.get("Emirate"),
            postal_code=address_data.get("PostalCode"),
        )

        return Provider(
            provider_id=provider_data.get("ProviderID"),
            provider_name=provider_data.get("ProviderName"),
            license_number=provider_data.get("LicenseNumber"),
            contact_person=provider_data.get(
                "ContactPerson", provider_data.get("AttendingPhysician")
            ),
            specialty=provider_data.get("Specialty"),
            phone_number=provider_data.get(
                "PhoneNumber", provider_data.get("ContactNumber")
            ),
            email=provider_data.get("Email"),
            address=address,
        )


class EclaimLinkProcessor(BaseProcessor):
    """
    Clean XML processor for eClaimLink format.

    Processes eClaimLink XML files, mapping essential fields
    to canonical schema while preserving all original data for future use.
    """

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
        with open(xml_file_path, "r", encoding="utf-8") as f:
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
        patient_data = self._extract_patient_dataclass(payload.get("Patient", {}))
        provider_data = self._extract_provider_dataclass(payload.get("Provider", {}))
        services = self._extract_eclaim_services(payload)
        justification = payload.get("JustificationText", "")

        # Create canonical bundle using dataclass
        meta = FHIRMeta(source="eClaimLink", last_updated=timestamp)

        canonical_bundle = CanonicalBundle(
            id=bundle_id,
            meta=meta,
            timestamp=timestamp,
            authorization_id=header.get("TransactionID"),
            sender=header.get("SenderID"),
            receiver=header.get("ReceiverID"),
            transaction_date=header.get("TransactionDateTime"),
            patient=patient_data,
            provider=provider_data,
            justification_text=justification,
            services=services,
            raw_data=parsed_data,
            source_file=xml_file_path,
            processing_timestamp=timestamp,
        )

        # Add data quality validation
        if self.enable_validation:
            # Convert to dict for validation
            bundle_dict = canonical_bundle.to_dict()
            validation_report = self.data_quality.validate_fhir_bundle(bundle_dict)

            # Convert validation report to dataclass format
            quality_score = QualityScore(
                overall_score=validation_report["quality_score"].overall_score,
                code_validity=validation_report["quality_score"].code_validity,
                completeness=validation_report["quality_score"].completeness,
                clinical_consistency=validation_report[
                    "quality_score"
                ].clinical_consistency,
                format_compliance=validation_report["quality_score"].format_compliance,
            )

            canonical_bundle.data_quality = DataQualityModel(
                quality_score=quality_score,
                validation_issues=validation_report.get("validation_issues", []),
                recommendations=validation_report.get("recommendations", []),
            )

            logger.info(f"Data quality score: {quality_score.overall_score:.3f}")

        logger.info(
            f"Successfully processed eClaimLink XML: {len(services)} services found"
        )
        return canonical_bundle.to_dict()

    def _extract_eclaim_services(self, payload: Dict[str, Any]) -> List[Service]:
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

            service_obj = Service(
                sequence=idx,
                activity_code=service.get("ct:ActivityCode"),
                diagnosis_code=service.get("ct:DiagnosisCode"),
                activity_date_time=service.get("ct:ActivityDateTime"),
                instructions=service.get("ct:ActivityInstructions"),
                requested_amount_value=amount_value,
                requested_amount_currency=amount_currency,
                raw_service_data=service,
            )
            services.append(service_obj)

        return services


class ShafafiyaProcessor(BaseProcessor):
    """
    Clean XML processor for Shafafiya format.

    Processes Shafafiya XML files, mapping essential fields
    to canonical schema while preserving all original data for future use.
    """

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
        with open(xml_file_path, "r", encoding="utf-8") as f:
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
        patient_data = self._extract_patient_dataclass(payload.get("Patient", {}))
        provider_data = self._extract_provider_dataclass(payload.get("Provider", {}))
        auth_request = payload.get(
            "AuthorizationRequest", payload.get("Authorization", {})
        )
        activities = self._extract_shafafiya_activities(auth_request)

        # Create canonical bundle using dataclass
        meta = FHIRMeta(source="Shafafiya", last_updated=timestamp)

        canonical_bundle = CanonicalBundle(
            id=bundle_id,
            meta=meta,
            timestamp=timestamp,
            authorization_id=auth_request.get("RequestID", auth_request.get("ID")),
            sender=header.get("SenderID"),
            receiver=header.get("ReceiverID"),
            transaction_date=header.get("TransactionDate"),
            patient=patient_data,
            provider=provider_data,
            request_status=auth_request.get("Status", auth_request.get("Result")),
            coverage_start=auth_request.get("CoverageStart", auth_request.get("Start")),
            coverage_end=auth_request.get("CoverageEnd", auth_request.get("End")),
            clinical_justification=auth_request.get(
                "ClinicalJustification", auth_request.get("Comments", "")
            ),
            activities=activities,
            raw_data=parsed_data,
            source_file=xml_file_path,
            processing_timestamp=timestamp,
        )

        # Add data quality validation
        if self.enable_validation:
            # Convert to dict for validation
            bundle_dict = canonical_bundle.to_dict()
            validation_report = self.data_quality.validate_fhir_bundle(bundle_dict)

            # Convert validation report to dataclass format
            quality_score = QualityScore(
                overall_score=validation_report["quality_score"].overall_score,
                code_validity=validation_report["quality_score"].code_validity,
                completeness=validation_report["quality_score"].completeness,
                clinical_consistency=validation_report[
                    "quality_score"
                ].clinical_consistency,
                format_compliance=validation_report["quality_score"].format_compliance,
            )

            canonical_bundle.data_quality = DataQualityModel(
                quality_score=quality_score,
                validation_issues=validation_report.get("validation_issues", []),
                recommendations=validation_report.get("recommendations", []),
            )

            logger.info(f"Data quality score: {quality_score.overall_score:.3f}")

        logger.info(
            f"Successfully processed Shafafiya XML: {len(activities)} activities found"
        )
        return canonical_bundle.to_dict()

    def _extract_shafafiya_activities(
        self, auth_request: Dict[str, Any]
    ) -> List[Activity]:
        """Extract activities from Shafafiya authorization request."""
        activities = []
        # Handle both old (Activity) and new (RequestedService) formats
        activity_list = auth_request.get(
            "RequestedService", auth_request.get("Activity", [])
        )

        # Ensure list format
        if isinstance(activity_list, dict):
            activity_list = [activity_list]

        for activity in activity_list:
            activity_obj = Activity(
                id=activity.get("ServiceID", activity.get("ID")),
                type=activity.get("ServiceType", activity.get("Type")),
                code=activity.get("Code"),
                description=activity.get("Description"),
                quantity=activity.get("Quantity"),
                estimated_cost=activity.get("EstimatedCost", activity.get("Net")),
                urgency=activity.get("Urgency"),
                scheduled_date=activity.get("ScheduledDate"),
                raw_activity_data=activity,
            )
            activities.append(activity_obj)

        return activities


if __name__ == "__main__":
    """
    Debug and testing section for XML processor.

    Tests both eClaimLink and Shafafiya formats and saves debug output.
    """

    # Setup logging
    logger.add("logs/debug_xml_processor.log")

    print("=" * 80)
    print("XML Processor - Debug Mode")
    print("=" * 80)

    eclaim_processor = EclaimLinkProcessor()
    shafafiya_processor = ShafafiyaProcessor()

    # Test files - handle both execution contexts
    base_path = ".." if os.path.basename(os.getcwd()) == "pipelines" else "."
    eclaim_file = os.path.join(base_path, "samples/eclaim_link_request.xml")
    shafafiya_file = os.path.join(base_path, "samples/shafafiya_prior_auth_request.xml")

    try:
        print("\n🔧 Step 1: Process eClaimLink XML")
        print("-" * 50)

        if os.path.exists(eclaim_file):
            eclaim_result = eclaim_processor.process_eclaim_link(eclaim_file)

            print("✅ eClaimLink processed successfully")
            print(f"   Authorization ID: {eclaim_result.get('authorization_id')}")
            print(f"   Services Count: {len(eclaim_result.get('services', []))}")
            print(
                f"   Justification Length: {len(eclaim_result.get('justification_text', ''))}"
            )

            # Save debug output
            with open("logs/debug_eclaim_output.json", "w", encoding="utf-8") as f:
                json.dump(eclaim_result, f, indent=2, ensure_ascii=False, default=str)
            print("   Debug saved to: debug_eclaim_output.json")
        else:
            print(f"❌ eClaimLink file not found: {eclaim_file}")

        print("\n🔧 Step 2: Process Shafafiya XML")
        print("-" * 50)

        if os.path.exists(shafafiya_file):
            shafafiya_result = shafafiya_processor.process_shafafiya(shafafiya_file)

            print("✅ Shafafiya processed successfully")
            print(f"   Authorization ID: {shafafiya_result.get('authorization_id')}")
            print(f"   Activities Count: {len(shafafiya_result.get('activities', []))}")
            print(
                f"   Authorization Result: {shafafiya_result.get('authorization_result')}"
            )

            # Save debug output
            with open("logs/debug_shafafiya_output.json", "w", encoding="utf-8") as f:
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
