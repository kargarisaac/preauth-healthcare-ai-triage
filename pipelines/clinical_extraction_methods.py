"""
Clinical extraction methods for FHIR resource generation.

This module contains the clinical intelligence and NLP methods used by
both EClaimLink and Shafafiya ingestors for extracting clinical data
from healthcare authorization texts.
"""

import re
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


class ClinicalExtractionMixin:
    """
    Mixin class providing clinical extraction methods for XML ingestors.
    """
    
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
            "search": {
                "mode": "match",
                "score": 1.0
            }
        }
    
    def _extract_conditions(
        self,
        payload: Dict[str, Any],
        services: List[Dict[str, Any]],
        justification_text: str,
        claim_id: str,
        xml_file_path: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        Extract and enhance Condition resources from diagnosis codes and clinical text.
        
        Args:
            payload: The XML payload
            services: Normalized services data
            justification_text: Clinical justification text
            claim_id: Reference to parent claim
            xml_file_path: Optional path to XML file
            
        Returns:
            List of FHIR Condition resources
        """
        conditions = []
        sequence = 1
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Extract conditions from diagnosis codes
        for service in services:
            diagnosis_code = service.get("diagnosis_code")
            if diagnosis_code:
                condition_id = f"condition-{diagnosis_code}-{sequence}"
                
                # Enhanced clinical context from text analysis
                clinical_context = self._analyze_condition_context(
                    diagnosis_code, justification_text
                )
                
                condition = {
                    "resourceType": "Condition",
                    "id": condition_id,
                    "meta": {
                        "profile": ["https://nazmito.com/fhir/StructureDefinition/uae-condition"],
                        "source": "eClaimLink"
                    },
                    "identifier": [{
                        "system": "https://nazmito.com/identifiers/condition",
                        "value": condition_id
                    }],
                    "clinicalStatus": {
                        "coding": [{
                            "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                            "code": clinical_context.get("clinical_status", "active")
                        }]
                    },
                    "verificationStatus": {
                        "coding": [{
                            "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                            "code": "confirmed"
                        }]
                    },
                    "category": [{
                        "coding": [{
                            "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                            "code": "encounter-diagnosis"
                        }]
                    }],
                    "code": {
                        "coding": [{
                            "system": "http://hl7.org/fhir/sid/icd-10-am",
                            "code": diagnosis_code,
                            "display": clinical_context.get("display_name", f"ICD-10-AM: {diagnosis_code}")
                        }],
                        "text": clinical_context.get("condition_text", f"Condition: {diagnosis_code}")
                    },
                    "subject": {
                        "reference": f"Patient/{payload.get('Patient', {}).get('PatientID', 'unknown')}"
                    },
                    "recordedDate": timestamp,
                    "extension": [
                        {
                            "url": "https://nazmito.com/fhir/StructureDefinition/clinical-context-score",
                            "valueDecimal": clinical_context.get("confidence_score", 0.8)
                        },
                        {
                            "url": "https://nazmito.com/fhir/StructureDefinition/source-mapping",
                            "extension": [
                                {
                                    "url": "source-field",
                                    "valueString": "ServiceRequest/DiagnosisCode"
                                },
                                {
                                    "url": "extraction-method",
                                    "valueString": "code-mapping-with-nlp-enhancement"
                                }
                            ]
                        }
                    ]
                }
                
                # Add clinical severity if detected
                if clinical_context.get("severity"):
                    condition["severity"] = {
                        "coding": [{
                            "system": "http://snomed.info/sct",
                            "code": clinical_context["severity"]["code"],
                            "display": clinical_context["severity"]["display"]
                        }],
                        "text": clinical_context["severity"]["text"]
                    }
                
                # Add onset information if detected
                if clinical_context.get("onset_date"):
                    condition["onsetDateTime"] = clinical_context["onset_date"]
                elif clinical_context.get("onset_text"):
                    condition["onsetString"] = clinical_context["onset_text"]
                
                # Add clinical notes
                if clinical_context.get("notes"):
                    condition["note"] = [{
                        "text": clinical_context["notes"],
                        "time": timestamp
                    }]
                
                conditions.append(condition)
                sequence += 1
        
        return conditions
    
    def _extract_observations(
        self,
        justification_text: str,
        services: List[Dict[str, Any]],
        claim_id: str,
        xml_file_path: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        Extract Observation resources from clinical justification text using NLP.
        
        Args:
            justification_text: Clinical justification text
            services: Normalized services data
            claim_id: Reference to parent claim
            xml_file_path: Optional path to XML file
            
        Returns:
            List of FHIR Observation resources
        """
        observations = []
        timestamp = datetime.now(timezone.utc).isoformat()
        
        if not justification_text:
            return observations
        
        # Extract common clinical observations using NLP patterns
        observation_patterns = self._extract_clinical_observations(justification_text)
        
        for idx, obs_data in enumerate(observation_patterns, 1):
            observation_id = f"observation-{obs_data['type']}-{idx}"
            
            observation = {
                "resourceType": "Observation",
                "id": observation_id,
                "meta": {
                    "profile": ["https://nazmito.com/fhir/StructureDefinition/uae-observation"],
                    "source": "clinical-text"
                },
                "identifier": [{
                    "system": "https://nazmito.com/identifiers/observation",
                    "value": observation_id
                }],
                "status": obs_data.get("status", "final"),
                "category": [{
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": obs_data.get("category", "survey")
                    }]
                }],
                "code": {
                    "coding": obs_data.get("coding", []),
                    "text": obs_data.get("display_text", "Clinical observation")
                },
                "subject": {
                    "reference": f"Patient/unknown"  # Will be linked to actual patient in bundle
                },
                "basedOn": [{
                    "reference": f"Claim/{claim_id}"
                }],
                "extension": [
                    {
                        "url": "https://nazmito.com/fhir/StructureDefinition/clinical-context-score",
                        "valueDecimal": obs_data.get("confidence_score", 0.7)
                    },
                    {
                        "url": "https://nazmito.com/fhir/StructureDefinition/source-mapping",
                        "extension": [
                            {
                                "url": "source-field",
                                "valueString": "JustificationText"
                            },
                            {
                                "url": "extraction-method",
                                "valueString": "nlp-medical-entity-recognition"
                            }
                        ]
                    }
                ]
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
                observation["interpretation"] = [{
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                        "code": obs_data["interpretation"]["code"],
                        "display": obs_data["interpretation"]["display"]
                    }]
                }]
            
            # Add reference ranges if available
            if obs_data.get("reference_range"):
                observation["referenceRange"] = [obs_data["reference_range"]]
            
            observations.append(observation)
        
        return observations
    
    def _extract_medications(
        self,
        justification_text: str,
        claim_id: str,
        xml_file_path: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        Extract MedicationStatement resources from clinical justification text.
        
        Args:
            justification_text: Clinical justification text
            claim_id: Reference to parent claim
            xml_file_path: Optional path to XML file
            
        Returns:
            List of FHIR MedicationStatement resources
        """
        medications = []
        timestamp = datetime.now(timezone.utc).isoformat()
        
        if not justification_text:
            return medications
        
        # Extract medication information using NLP patterns
        medication_patterns = self._extract_medication_statements(justification_text)
        
        for idx, med_data in enumerate(medication_patterns, 1):
            medication_id = f"medication-{med_data['name'].lower().replace(' ', '-')}-{idx}"
            
            medication = {
                "resourceType": "MedicationStatement",
                "id": medication_id,
                "meta": {
                    "profile": ["https://nazmito.com/fhir/StructureDefinition/uae-medication-statement"],
                    "source": "clinical-text"
                },
                "identifier": [{
                    "system": "https://nazmito.com/identifiers/medication-statement",
                    "value": medication_id
                }],
                "basedOn": [{
                    "reference": f"Claim/{claim_id}"
                }],
                "status": med_data.get("status", "active"),
                "medicationCodeableConcept": {
                    "coding": med_data.get("coding", []),
                    "text": med_data["name"]
                },
                "subject": {
                    "reference": f"Patient/unknown"  # Will be linked to actual patient in bundle
                },
                "effectiveDateTime": med_data.get("start_date", timestamp),
                "dateAsserted": timestamp,
                "extension": [
                    {
                        "url": "https://nazmito.com/fhir/StructureDefinition/clinical-context-score",
                        "valueDecimal": med_data.get("confidence_score", 0.75)
                    },
                    {
                        "url": "https://nazmito.com/fhir/StructureDefinition/source-mapping",
                        "extension": [
                            {
                                "url": "source-field",
                                "valueString": "JustificationText"
                            },
                            {
                                "url": "extraction-method",
                                "valueString": "nlp-medication-extraction"
                            }
                        ]
                    }
                ]
            }
            
            # Add dosage information if available
            if med_data.get("dosage"):
                medication["dosage"] = [{
                    "text": med_data["dosage"]["text"]
                }]
                
                # Add structured dosage if available
                if med_data["dosage"].get("structured"):
                    medication["dosage"][0].update(med_data["dosage"]["structured"])
            
            # Add reason codes if available
            if med_data.get("reason_codes"):
                medication["reasonCode"] = med_data["reason_codes"]
            
            # Add clinical notes
            if med_data.get("notes"):
                medication["note"] = [{
                    "text": med_data["notes"],
                    "time": timestamp
                }]
            
            medications.append(medication)
        
        return medications
    
    def _extract_procedures(
        self,
        services: List[Dict[str, Any]],
        justification_text: str,
        claim_id: str,
        xml_file_path: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        Extract Procedure resources from service codes and clinical timeline.
        
        Args:
            services: Normalized services data
            justification_text: Clinical justification text
            claim_id: Reference to parent claim
            xml_file_path: Optional path to XML file
            
        Returns:
            List of FHIR Procedure resources
        """
        procedures = []
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Extract requested procedures from services
        for service in services:
            activity_code = service.get("activity_code")
            if activity_code:
                procedure_id = f"procedure-{activity_code}-requested"
                
                procedure = {
                    "resourceType": "Procedure",
                    "id": procedure_id,
                    "meta": {
                        "profile": ["https://nazmito.com/fhir/StructureDefinition/uae-procedure"],
                        "source": "eClaimLink"
                    },
                    "identifier": [{
                        "system": "https://nazmito.com/identifiers/procedure",
                        "value": procedure_id
                    }],
                    "basedOn": [{
                        "reference": f"Claim/{claim_id}"
                    }],
                    "status": "preparation",  # This is a requested procedure
                    "code": {
                        "coding": [{
                            "system": "http://www.ama-assn.org/go/cpt",
                            "code": activity_code,
                            "display": f"CPT: {activity_code}"
                        }],
                        "text": f"Requested procedure: {activity_code}"
                    },
                    "subject": {
                        "reference": f"Patient/unknown"  # Will be linked to actual patient in bundle
                    },
                    "extension": [
                        {
                            "url": "https://nazmito.com/fhir/StructureDefinition/source-mapping",
                            "extension": [
                                {
                                    "url": "source-field",
                                    "valueString": "ServiceRequest/ActivityCode"
                                },
                                {
                                    "url": "extraction-method",
                                    "valueString": "direct-code-mapping"
                                },
                                {
                                    "url": "confidence-score",
                                    "valueDecimal": 0.95
                                }
                            ]
                        }
                    ]
                }
                
                # Add scheduled date if available
                if service.get("activity_date_time"):
                    procedure["performedDateTime"] = service["activity_date_time"]
                
                # Add clinical instructions as notes
                if service.get("instructions"):
                    procedure["note"] = [{
                        "text": service["instructions"],
                        "time": timestamp
                    }]
                
                procedures.append(procedure)
        
        # Extract historical procedures from clinical text
        historical_procedures = self._extract_historical_procedures(justification_text, claim_id)
        procedures.extend(historical_procedures)
        
        return procedures
    
    # ========================================================================
    # CLINICAL NLP AND INTELLIGENCE METHODS
    # ========================================================================
    
    def _analyze_condition_context(self, diagnosis_code: str, clinical_text: str) -> Dict[str, Any]:
        """
        Analyze clinical context for a condition using NLP and medical knowledge.
        
        Args:
            diagnosis_code: ICD-10-AM diagnosis code
            clinical_text: Clinical justification text
            
        Returns:
            Enhanced clinical context for the condition
        """
        context = {
            "clinical_status": "active",
            "confidence_score": 0.8,
            "display_name": f"ICD-10-AM: {diagnosis_code}"
        }
        
        if not clinical_text:
            return context
        
        text_lower = clinical_text.lower()
        
        # Analyze severity from clinical descriptors
        severity_patterns = {
            "mild": ["mild", "slight", "minor", "well-controlled", "stable"],
            "moderate": ["moderate", "moderately", "suboptimal", "partially controlled"],
            "severe": ["severe", "poorly controlled", "uncontrolled", "significant", "marked"]
        }
        
        for severity, patterns in severity_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                context["severity"] = {
                    "code": "24484000" if severity == "severe" else "6736007" if severity == "moderate" else "255604002",
                    "display": severity.title(),
                    "text": f"{severity.title()} condition based on clinical description"
                }
                break
        
        # Extract temporal information
        temporal_patterns = {
            "recently diagnosed": r"(recently|newly|just)\s+(diagnosed|found)",
            "long-standing": r"(long[\s-]?standing|chronic|longstanding|years?\s+of)",
            "acute": r"(acute|sudden|recent|new)"
        }
        
        for pattern_name, pattern in temporal_patterns.items():
            if re.search(pattern, text_lower, re.IGNORECASE):
                context["onset_text"] = pattern_name
                break
        
        # Look for specific dates
        date_pattern = r"(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}|\d{1,2}\s+(months?|years?)\s+ago)"
        date_match = re.search(date_pattern, text_lower)
        if date_match:
            context["onset_text"] = date_match.group(0)
        
        # Extract condition-specific notes
        condition_context_patterns = [
            r"(patient\s+(?:has|presents?\s+with|reports?)\s+.{0,100})",
            r"(history\s+of\s+.{0,50})",
            r"(currently\s+.{0,50})"
        ]
        
        notes = []
        for pattern in condition_context_patterns:
            matches = re.findall(pattern, clinical_text, re.IGNORECASE)
            notes.extend(matches)
        
        if notes:
            context["notes"] = "; ".join(notes[:3])  # Limit to first 3 relevant notes
            context["confidence_score"] = 0.85
        
        return context
    
    def _extract_clinical_observations(self, clinical_text: str) -> List[Dict[str, Any]]:
        """
        Extract clinical observations from text using NLP patterns.
        
        Args:
            clinical_text: Clinical justification text
            
        Returns:
            List of extracted observation data
        """
        observations = []
        
        if not clinical_text:
            return observations
        
        # Common lab value patterns
        lab_patterns = {
            "hba1c": {
                "pattern": r"(hba1c|hemoglobin\s+a1c|glycated\s+hemoglobin)\s*:?\s*(\d+\.\d+)\s*%?",
                "coding": [{
                    "system": "http://loinc.org",
                    "code": "4548-4",
                    "display": "Hemoglobin A1c"
                }],
                "category": "laboratory",
                "unit": "%",
                "reference_ranges": {"high": 7.0}
            },
            "glucose": {
                "pattern": r"(glucose|blood\s+sugar)\s*:?\s*(\d+)\s*(mg/dl|mmol/l)?",
                "coding": [{
                    "system": "http://loinc.org",
                    "code": "2345-7",
                    "display": "Glucose"
                }],
                "category": "laboratory",
                "unit": "mg/dL",
                "reference_ranges": {"high": 126}
            },
            "blood_pressure": {
                "pattern": r"(blood\s+pressure|bp)\s*:?\s*(\d+)/(\d+)\s*(mmhg)?",
                "coding": [{
                    "system": "http://loinc.org",
                    "code": "85354-9",
                    "display": "Blood pressure"
                }],
                "category": "vital-signs",
                "is_complex": True
            }
        }
        
        for obs_type, config in lab_patterns.items():
            matches = re.finditer(config["pattern"], clinical_text, re.IGNORECASE)
            
            for match in matches:
                if config.get("is_complex"):  # Handle blood pressure specially
                    systolic = float(match.group(2))
                    diastolic = float(match.group(3))
                    
                    obs_data = {
                        "type": obs_type,
                        "coding": config["coding"],
                        "category": config["category"],
                        "display_text": f"Blood Pressure: {systolic}/{diastolic} mmHg",
                        "value_string": f"{systolic}/{diastolic} mmHg",
                        "confidence_score": 0.9
                    }
                else:
                    value = float(match.group(2))
                    unit = config["unit"]
                    
                    obs_data = {
                        "type": obs_type,
                        "coding": config["coding"],
                        "category": config["category"],
                        "display_text": f"{config['coding'][0]['display']}: {value} {unit}",
                        "value_quantity": {
                            "value": value,
                            "unit": unit,
                            "system": "http://unitsofmeasure.org",
                            "code": unit
                        },
                        "confidence_score": 0.85
                    }
                    
                    # Add interpretation based on reference ranges
                    if config.get("reference_ranges"):
                        if "high" in config["reference_ranges"] and value > config["reference_ranges"]["high"]:
                            obs_data["interpretation"] = {"code": "H", "display": "High"}
                        elif "low" in config["reference_ranges"] and value < config["reference_ranges"]["low"]:
                            obs_data["interpretation"] = {"code": "L", "display": "Low"}
                        else:
                            obs_data["interpretation"] = {"code": "N", "display": "Normal"}
                
                observations.append(obs_data)
        
        # Extract general clinical findings
        finding_patterns = [
            r"(patient\s+reports?\s+(.{5,50}))",
            r"(complains?\s+of\s+(.{5,50}))",
            r"(symptoms?\s+include\s+(.{5,50}))",
            r"(presents?\s+with\s+(.{5,50}))"
        ]
        
        for pattern in finding_patterns:
            matches = re.finditer(pattern, clinical_text, re.IGNORECASE)
            for match in matches:
                finding_text = match.group(1).strip()
                if len(finding_text) > 10:  # Filter out very short findings
                    obs_data = {
                        "type": "clinical-finding",
                        "coding": [{
                            "system": "http://snomed.info/sct",
                            "code": "404684003",
                            "display": "Clinical finding"
                        }],
                        "category": "survey",
                        "display_text": f"Clinical finding: {finding_text}",
                        "value_string": finding_text,
                        "confidence_score": 0.7
                    }
                    observations.append(obs_data)
        
        return observations
    
    def _extract_medication_statements(self, clinical_text: str) -> List[Dict[str, Any]]:
        """
        Extract medication statements from clinical text using NLP.
        
        Args:
            clinical_text: Clinical justification text
            
        Returns:
            List of medication statement data
        """
        medications = []
        
        if not clinical_text:
            return medications
        
        # Common medication patterns
        medication_patterns = {
            "metformin": {
                "pattern": r"(metformin)\s*(\d+\s*mg)?\s*((?:once|twice|three times)\s*(?:daily|a day|per day)?|bid|tid|qd)?",
                "coding": [{
                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                    "code": "6809",
                    "display": "Metformin"
                }],
                "therapeutic_class": "Antidiabetic"
            },
            "insulin": {
                "pattern": r"(insulin)\s*([\w\s]*)?\s*(\d+\s*units?)?",
                "coding": [{
                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                    "code": "5856",
                    "display": "Insulin"
                }],
                "therapeutic_class": "Antidiabetic"
            },
            "ace_inhibitor": {
                "pattern": r"(ace\s*inhibitor|lisinopril|enalapril|ramipril)",
                "coding": [{
                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                    "code": "18867",
                    "display": "ACE inhibitor"
                }],
                "therapeutic_class": "Antihypertensive"
            },
            "statin": {
                "pattern": r"(statin|atorvastatin|simvastatin|rosuvastatin)",
                "coding": [{
                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                    "code": "36567",
                    "display": "Statin"
                }],
                "therapeutic_class": "Lipid-lowering"
            }
        }
        
        # Medication status patterns
        status_patterns = {
            "active": ["currently on", "taking", "prescribed", "on"],
            "stopped": ["stopped", "discontinued", "ceased"],
            "completed": ["completed", "finished course"]
        }
        
        for med_name, config in medication_patterns.items():
            matches = re.finditer(config["pattern"], clinical_text, re.IGNORECASE)
            
            for match in matches:
                # Determine medication status from context
                med_status = "active"  # default
                surrounding_text = clinical_text[max(0, match.start()-50):match.end()+50].lower()
                
                for status, keywords in status_patterns.items():
                    if any(keyword in surrounding_text for keyword in keywords):
                        med_status = status
                        break
                
                # Extract dosage information
                dosage_text = None
                if match.group(2) and match.group(3):  # Both dose and frequency captured
                    dose = match.group(2).strip()
                    frequency = match.group(3).strip()
                    dosage_text = f"{dose} {frequency}"
                elif match.group(2):  # Only dose captured
                    dosage_text = match.group(2).strip()
                elif match.group(3):  # Only frequency captured
                    dosage_text = match.group(3).strip()
                
                med_data = {
                    "name": config["coding"][0]["display"],
                    "coding": config["coding"],
                    "status": med_status,
                    "therapeutic_class": config["therapeutic_class"],
                    "confidence_score": 0.8
                }
                
                if dosage_text:
                    med_data["dosage"] = {
                        "text": dosage_text
                    }
                
                medications.append(med_data)
        
        return medications
    
    def _extract_historical_procedures(self, clinical_text: str, claim_id: str) -> List[Dict[str, Any]]:
        """
        Extract historical procedures mentioned in clinical text.
        
        Args:
            clinical_text: Clinical justification text
            claim_id: Reference to parent claim
            
        Returns:
            List of historical procedure resources
        """
        procedures = []
        timestamp = datetime.now(timezone.utc).isoformat()
        
        if not clinical_text:
            return procedures
        
        # Common historical procedure patterns
        procedure_patterns = {
            "hba1c_test": {
                "pattern": r"(last\s+hba1c|previous\s+hba1c|hba1c\s+(?:was|done|taken)\s+(?:on|in|at)?)\s*([\w\s,]+?)(?:was|showed?|indicated?)\s*(\d+\.\d+)\s*%?",
                "coding": [{
                    "system": "http://www.ama-assn.org/go/cpt",
                    "code": "83036",
                    "display": "Hemoglobin A1c test"
                }],
                "category": "laboratory"
            },
            "eye_exam": {
                "pattern": r"(eye\s+exam|ophthalmology|retinal\s+exam|fundoscopy)\s+(?:done|performed|completed)?\s*([\w\s,]+?)(?:ago|back)?",
                "coding": [{
                    "system": "http://www.ama-assn.org/go/cpt",
                    "code": "92014",
                    "display": "Comprehensive eye examination"
                }],
                "category": "procedure"
            },
            "blood_test": {
                "pattern": r"(blood\s+test|lab\s+work|laboratory\s+tests?)\s+(?:done|performed|taken)?\s*([\w\s,]+?)(?:ago|back)?",
                "coding": [{
                    "system": "http://www.ama-assn.org/go/cpt",
                    "code": "80053",
                    "display": "Comprehensive metabolic panel"
                }],
                "category": "laboratory"
            }
        }
        
        for proc_type, config in procedure_patterns.items():
            matches = re.finditer(config["pattern"], clinical_text, re.IGNORECASE)
            
            for idx, match in enumerate(matches, 1):
                procedure_id = f"historical-{proc_type}-{idx}"
                
                # Extract timing information
                timing_text = match.group(2) if len(match.groups()) > 1 else ""
                
                procedure = {
                    "resourceType": "Procedure",
                    "id": procedure_id,
                    "meta": {
                        "profile": ["https://nazmito.com/fhir/StructureDefinition/uae-procedure"],
                        "source": "clinical-text"
                    },
                    "identifier": [{
                        "system": "https://nazmito.com/identifiers/procedure",
                        "value": procedure_id
                    }],
                    "status": "completed",  # Historical procedures are completed
                    "code": {
                        "coding": config["coding"],
                        "text": f"Historical {config['coding'][0]['display']}"
                    },
                    "subject": {
                        "reference": f"Patient/unknown"  # Will be linked to actual patient in bundle
                    },
                    "extension": [
                        {
                            "url": "https://nazmito.com/fhir/StructureDefinition/clinical-context-score",
                            "valueDecimal": 0.75
                        },
                        {
                            "url": "https://nazmito.com/fhir/StructureDefinition/source-mapping",
                            "extension": [
                                {
                                    "url": "source-field",
                                    "valueString": "JustificationText"
                                },
                                {
                                    "url": "extraction-method",
                                    "valueString": "nlp-historical-procedure-extraction"
                                }
                            ]
                        }
                    ]
                }
                
                # Add timing information if available
                if timing_text.strip():
                    procedure["note"] = [{
                        "text": f"Timing: {timing_text.strip()}",
                        "time": timestamp
                    }]
                    
                    # Try to parse relative dates
                    if "months ago" in timing_text.lower():
                        months_match = re.search(r"(\d+)\s*months?\s+ago", timing_text, re.IGNORECASE)
                        if months_match:
                            months_ago = int(months_match.group(1))
                            estimated_date = datetime.now(timezone.utc).replace(
                                month=max(1, datetime.now().month - months_ago)
                            )
                            procedure["performedDateTime"] = estimated_date.isoformat()
                
                procedures.append(procedure)
        
        return procedures
    
    def _calculate_clinical_scores(self, bundle_entries: List[Dict[str, Any]], clinical_text: str) -> Dict[str, float]:
        """
        Calculate clinical intelligence and data quality scores.
        
        Args:
            bundle_entries: List of FHIR resources in bundle
            clinical_text: Clinical justification text
            
        Returns:
            Dictionary of calculated scores
        """
        # Count resources by type
        resource_counts = {}
        total_resources = len(bundle_entries)
        
        for entry in bundle_entries:
            resource_type = entry["resource"]["resourceType"]
            resource_counts[resource_type] = resource_counts.get(resource_type, 0) + 1
        
        # Clinical completeness score (0-1)
        expected_resources = ["Claim", "Condition", "Observation", "MedicationStatement", "Procedure"]
        present_resources = len([rt for rt in expected_resources if resource_counts.get(rt, 0) > 0])
        clinical_completeness = present_resources / len(expected_resources)
        
        # Clinical context score based on text richness
        text_length = len(clinical_text) if clinical_text else 0
        clinical_context_score = min(1.0, text_length / 500) * 0.7  # Scale based on text length
        
        # Add bonus for clinical detail
        if clinical_text:
            clinical_keywords = [
                "patient", "diagnosis", "symptoms", "treatment", "history", 
                "medication", "test", "exam", "results", "condition"
            ]
            keyword_count = sum(1 for keyword in clinical_keywords if keyword in clinical_text.lower())
            clinical_context_score += min(0.3, keyword_count * 0.03)
        
        # Data quality score
        data_quality_base = 0.8  # Base score for successful processing
        
        # Bonus for multiple resource types
        if len(resource_counts) >= 4:
            data_quality_base += 0.15
        elif len(resource_counts) >= 3:
            data_quality_base += 0.1
        
        # Bonus for clinical observations and medications
        if resource_counts.get("Observation", 0) > 0:
            data_quality_base += 0.05
        if resource_counts.get("MedicationStatement", 0) > 0:
            data_quality_base += 0.05
        
        data_quality_score = min(1.0, data_quality_base)
        
        # Enrichment score (how much value we added beyond basic claim)
        base_claim_resources = 1  # Just the claim
        enriched_resources = total_resources - base_claim_resources
        enrichment_score = min(1.0, enriched_resources / 10)  # Scale based on additional resources
        
        # AI confidence (average confidence from extractions)
        total_confidence = 0
        confidence_count = 0
        
        for entry in bundle_entries:
            extensions = entry["resource"].get("extension", [])
            for ext in extensions:
                if ext.get("url") == "https://nazmito.com/fhir/StructureDefinition/clinical-context-score":
                    total_confidence += ext.get("valueDecimal", 0)
                    confidence_count += 1
        
        ai_confidence = total_confidence / confidence_count if confidence_count > 0 else 0.8
        
        return {
            "clinical_completeness": round(clinical_completeness, 3),
            "clinical_context_score": round(clinical_context_score, 3),
            "data_quality_score": round(data_quality_score, 3),
            "enrichment_score": round(enrichment_score, 3),
            "ai_confidence": round(ai_confidence, 3),
            "total_resources": total_resources,
            "resource_distribution": resource_counts
        }
    
    def _create_bundle_extensions(
        self, clinical_scores: Dict[str, Any], xml_file_path: Optional[str], root_element: str
    ) -> List[Dict[str, Any]]:
        """
        Create FHIR Bundle extensions with clinical intelligence scores.
        
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
                "valueString": "v0.2"
            },
            {
                "url": "https://nazmito.com/fhir/StructureDefinition/original-format",
                "valueString": "eClaimLink-2019/11"
            },
            {
                "url": "https://nazmito.com/fhir/StructureDefinition/data-quality-score",
                "valueDecimal": clinical_scores["data_quality_score"]
            },
            {
                "url": "https://nazmito.com/fhir/StructureDefinition/processing-timestamp",
                "valueDateTime": timestamp
            },
            {
                "url": "https://nazmito.com/fhir/StructureDefinition/enrichment-score",
                "valueDecimal": clinical_scores["enrichment_score"]
            },
            {
                "url": "https://nazmito.com/fhir/StructureDefinition/ai-confidence",
                "valueDecimal": clinical_scores["ai_confidence"]
            },
            {
                "url": "https://nazmito.com/fhir/StructureDefinition/clinical-context-score",
                "valueDecimal": clinical_scores["clinical_context_score"]
            },
            {
                "url": "https://nazmito.com/fhir/StructureDefinition/record-count",
                "valueInteger": clinical_scores["total_resources"]
            },
            {
                "url": "https://nazmito.com/fhir/StructureDefinition/emirate-authority",
                "valueString": "Dubai Health Authority"
            },
            {
                "url": "https://nazmito.com/fhir/StructureDefinition/source-mapping",
                "extension": [
                    {
                        "url": "source-file",
                        "valueString": xml_file_path or "memory"
                    },
                    {
                        "url": "root-element",
                        "valueString": root_element
                    },
                    {
                        "url": "processing-method",
                        "valueString": "enhanced-clinical-extraction"
                    }
                ]
            }
        ]