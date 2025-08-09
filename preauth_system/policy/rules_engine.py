"""
Policy Rules Engine for Deterministic Prior Authorization Decisions
================================================================

This module implements a YAML-based policy engine that evaluates medical prior
authorization requests against deterministic criteria. It supports temporal
reasoning, policy versioning, and provenance tracking.

Key Features:
- YAML policy file loader and executor
- Deterministic criteria evaluation (met/unmet/uncertain)
- Temporal reasoning helpers (e.g., "failed therapy for ≥6 weeks")
- Policy versioning and provenance tracking
- Integration with LangGraph workflow state
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from dateutil import parser as date_parser
from dataclasses import dataclass
from enum import Enum

from preauth_system.state import PreAuthState, PatientData, PatientInfo


class CriterionStatus(Enum):
    """Status of individual policy criterion evaluation."""
    MET = "met"
    UNMET = "unmet"  
    UNCERTAIN = "uncertain"


@dataclass
class CriterionResult:
    """Result of evaluating a single policy criterion."""
    criterion_id: str
    description: str
    status: CriterionStatus
    rationale: str
    evidence: List[str]
    required: bool = True


@dataclass
class PolicyEvaluation:
    """Complete policy evaluation result."""
    policy_id: str
    policy_version: str
    effective_date: str
    evaluation_timestamp: str
    criteria_results: List[CriterionResult]
    overall_score: float
    missing_documentation: List[str]
    rationale: str
    
    @property
    def met_criteria_count(self) -> int:
        return sum(1 for r in self.criteria_results if r.status == CriterionStatus.MET)
    
    @property
    def unmet_criteria_count(self) -> int:
        return sum(1 for r in self.criteria_results if r.status == CriterionStatus.UNMET)
    
    @property
    def uncertain_criteria_count(self) -> int:
        return sum(1 for r in self.criteria_results if r.status == CriterionStatus.UNCERTAIN)
    
    @property
    def required_criteria_met(self) -> bool:
        """Check if all required criteria are met."""
        for result in self.criteria_results:
            if result.required and result.status != CriterionStatus.MET:
                return False
        return True


class TemporalReasoning:
    """Helper class for time-based criteria evaluation."""
    
    @staticmethod
    def parse_duration(duration_str: str) -> timedelta:
        """Parse duration string like '6 weeks', '3 months', '1 year'."""
        parts = duration_str.lower().split()
        if len(parts) != 2:
            raise ValueError(f"Invalid duration format: {duration_str}")
        
        number = int(parts[0])
        unit = parts[1].rstrip('s')  # Remove plural 's'
        
        if unit == 'day':
            return timedelta(days=number)
        elif unit == 'week':
            return timedelta(weeks=number)
        elif unit == 'month':
            return timedelta(days=number * 30)  # Approximation
        elif unit == 'year':
            return timedelta(days=number * 365)  # Approximation
        else:
            raise ValueError(f"Unknown duration unit: {unit}")
    
    @staticmethod
    def evaluate_duration_criterion(
        start_date: Union[str, datetime],
        end_date: Optional[Union[str, datetime]],
        required_duration: str,
        description: str
    ) -> CriterionResult:
        """Evaluate if a therapy/treatment lasted for required duration."""
        try:
            if isinstance(start_date, str):
                start_dt = date_parser.parse(start_date)
            else:
                start_dt = start_date
            
            if end_date is None:
                end_dt = datetime.now()
            elif isinstance(end_date, str):
                end_dt = date_parser.parse(end_date)
            else:
                end_dt = end_date
            
            actual_duration = end_dt - start_dt
            required_duration_td = TemporalReasoning.parse_duration(required_duration)
            
            if actual_duration >= required_duration_td:
                return CriterionResult(
                    criterion_id="duration_check",
                    description=description,
                    status=CriterionStatus.MET,
                    rationale=f"Treatment duration {actual_duration.days} days meets requirement of {required_duration}",
                    evidence=[f"Start: {start_dt.date()}", f"End: {end_dt.date()}"]
                )
            else:
                return CriterionResult(
                    criterion_id="duration_check",
                    description=description,
                    status=CriterionStatus.UNMET,
                    rationale=f"Treatment duration {actual_duration.days} days less than required {required_duration}",
                    evidence=[f"Start: {start_dt.date()}", f"End: {end_dt.date()}"]
                )
                
        except Exception as e:
            return CriterionResult(
                criterion_id="duration_check",
                description=description,
                status=CriterionStatus.UNCERTAIN,
                rationale=f"Could not evaluate duration: {str(e)}",
                evidence=[]
            )
    
    @staticmethod
    def evaluate_recency_criterion(
        test_date: Union[str, datetime],
        max_age: str,
        description: str
    ) -> CriterionResult:
        """Evaluate if a test/imaging is recent enough."""
        try:
            if isinstance(test_date, str):
                test_dt = date_parser.parse(test_date)
            else:
                test_dt = test_date
            
            max_age_td = TemporalReasoning.parse_duration(max_age)
            age = datetime.now() - test_dt
            
            if age <= max_age_td:
                return CriterionResult(
                    criterion_id="recency_check",
                    description=description,
                    status=CriterionStatus.MET,
                    rationale=f"Test from {test_dt.date()} is within {max_age} requirement",
                    evidence=[f"Test date: {test_dt.date()}", f"Age: {age.days} days"]
                )
            else:
                return CriterionResult(
                    criterion_id="recency_check", 
                    description=description,
                    status=CriterionStatus.UNMET,
                    rationale=f"Test from {test_dt.date()} is older than {max_age} requirement",
                    evidence=[f"Test date: {test_dt.date()}", f"Age: {age.days} days"]
                )
                
        except Exception as e:
            return CriterionResult(
                criterion_id="recency_check",
                description=description,
                status=CriterionStatus.UNCERTAIN,
                rationale=f"Could not evaluate recency: {str(e)}",
                evidence=[]
            )


class PolicyRulesEngine:
    """Main policy rules engine for evaluating prior authorization requests."""
    
    def __init__(self, policies_dir: Optional[str] = None):
        """Initialize the rules engine with policy directory."""
        if policies_dir is None:
            policies_dir = Path(__file__).parent / "policies"
        self.policies_dir = Path(policies_dir)
        self.loaded_policies: Dict[str, Dict[str, Any]] = {}
        self.temporal = TemporalReasoning()
    
    def load_policy(self, policy_file: str) -> Dict[str, Any]:
        """Load a YAML policy file."""
        policy_path = self.policies_dir / policy_file
        
        if not policy_path.exists():
            raise FileNotFoundError(f"Policy file not found: {policy_path}")
        
        try:
            with open(policy_path, 'r') as f:
                policy = yaml.safe_load(f)
            
            # Validate required fields
            required_fields = ['metadata', 'criteria', 'codes']
            for field in required_fields:
                if field not in policy:
                    raise ValueError(f"Policy missing required field: {field}")
            
            policy_id = policy['metadata']['id']
            self.loaded_policies[policy_id] = policy
            return policy
            
        except Exception as e:
            raise ValueError(f"Error loading policy {policy_file}: {str(e)}")
    
    def get_applicable_policy(
        self,
        service_codes: List[str],
        diagnosis_codes: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Find applicable policy for given service and diagnosis codes."""
        for policy in self.loaded_policies.values():
            # Check if service codes match
            policy_service_codes = policy.get('codes', {}).get('service_codes', [])
            if any(code in policy_service_codes for code in service_codes):
                # Check diagnosis codes if specified
                policy_diagnosis_codes = policy.get('codes', {}).get('diagnosis_codes', [])
                if not policy_diagnosis_codes or any(code in policy_diagnosis_codes for code in diagnosis_codes):
                    return policy
        return None
    
    def evaluate_policy(
        self,
        policy: Dict[str, Any],
        state: PreAuthState
    ) -> PolicyEvaluation:
        """Evaluate a policy against patient state."""
        try:
            policy_id = policy['metadata']['id']
            policy_version = policy['metadata']['version']
            effective_date = policy['metadata']['effective_date']
            
            criteria_results = []
            missing_documentation = []
            
            # Evaluate each criterion
            for criterion in policy['criteria']:
                result = self._evaluate_criterion(criterion, state)
                criteria_results.append(result)
                
                # Track missing documentation
                if result.status == CriterionStatus.UNCERTAIN:
                    missing_doc = criterion.get('missing_documentation_message')
                    if missing_doc and missing_doc not in missing_documentation:
                        missing_documentation.append(missing_doc)
            
            # Calculate overall score
            total_criteria = len(criteria_results)
            met_count = sum(1 for r in criteria_results if r.status == CriterionStatus.MET)
            overall_score = met_count / total_criteria if total_criteria > 0 else 0.0
            
            # Generate rationale
            rationale = self._generate_rationale(criteria_results, policy_id)
            
            return PolicyEvaluation(
                policy_id=policy_id,
                policy_version=policy_version,
                effective_date=effective_date,
                evaluation_timestamp=datetime.now().isoformat(),
                criteria_results=criteria_results,
                overall_score=overall_score,
                missing_documentation=missing_documentation,
                rationale=rationale
            )
            
        except Exception as e:
            # Return a failure evaluation
            return PolicyEvaluation(
                policy_id=policy.get('metadata', {}).get('id', 'unknown'),
                policy_version=policy.get('metadata', {}).get('version', '1.0'),
                effective_date=policy.get('metadata', {}).get('effective_date', datetime.now().isoformat()),
                evaluation_timestamp=datetime.now().isoformat(),
                criteria_results=[],
                overall_score=0.0,
                missing_documentation=[f"Policy evaluation error: {str(e)}"],
                rationale=f"Failed to evaluate policy: {str(e)}"
            )
    
    def _evaluate_criterion(
        self,
        criterion: Dict[str, Any],
        state: PreAuthState
    ) -> CriterionResult:
        """Evaluate a single policy criterion."""
        criterion_id = criterion.get('id', 'unknown')
        description = criterion.get('description', 'No description')
        criterion_type = criterion.get('type', 'simple')
        required = criterion.get('required', True)
        
        try:
            if criterion_type == 'age_range':
                return self._evaluate_age_criterion(criterion, state)
            elif criterion_type == 'lab_value':
                return self._evaluate_lab_criterion(criterion, state)
            elif criterion_type == 'medication_history':
                return self._evaluate_medication_criterion(criterion, state)
            elif criterion_type == 'condition_present':
                return self._evaluate_condition_criterion(criterion, state)
            elif criterion_type == 'therapy_duration':
                return self._evaluate_therapy_duration_criterion(criterion, state)
            elif criterion_type == 'imaging_recency':
                return self._evaluate_imaging_recency_criterion(criterion, state)
            elif criterion_type == 'documentation':
                return self._evaluate_documentation_criterion(criterion, state)
            else:
                return CriterionResult(
                    criterion_id=criterion_id,
                    description=description,
                    status=CriterionStatus.UNCERTAIN,
                    rationale=f"Unknown criterion type: {criterion_type}",
                    evidence=[],
                    required=required
                )
                
        except Exception as e:
            return CriterionResult(
                criterion_id=criterion_id,
                description=description,
                status=CriterionStatus.UNCERTAIN,
                rationale=f"Error evaluating criterion: {str(e)}",
                evidence=[],
                required=required
            )
    
    def _evaluate_age_criterion(
        self,
        criterion: Dict[str, Any],
        state: PreAuthState
    ) -> CriterionResult:
        """Evaluate age-based criterion."""
        if not state.get('patient_data') or 'demographics' not in state.get('patient_data', {}):
            return CriterionResult(
                criterion_id=criterion['id'],
                description=criterion['description'],
                status=CriterionStatus.UNCERTAIN,
                rationale="Patient demographics not available",
                evidence=[],
                required=criterion.get('required', True)
            )
        
        try:
            # Extract birthdate from demographics or patient info
            birth_date_str = None
            patient_data = state.get('patient_data', {})
            demographics = patient_data.get('demographics', {})
            patient_info = state.get('patient_info', {})
            
            if 'birth_date' in demographics:
                birth_date_str = demographics['birth_date']
            elif 'birthDate' in patient_info:
                birth_date_str = patient_info['birthDate']
            elif 'DateOfBirth' in patient_info:
                birth_date_str = patient_info['DateOfBirth']
            
            if not birth_date_str:
                return CriterionResult(
                    criterion_id=criterion['id'],
                    description=criterion['description'],
                    status=CriterionStatus.UNCERTAIN,
                    rationale="Birth date not available",
                    evidence=[],
                    required=criterion.get('required', True)
                )
            
            birth_date = date_parser.parse(birth_date_str)
            age_years = (datetime.now() - birth_date).days / 365.25
            
            min_age = criterion.get('min_age')
            max_age = criterion.get('max_age')
            
            age_meets_criteria = True
            rationale_parts = []
            
            if min_age is not None and age_years < min_age:
                age_meets_criteria = False
                rationale_parts.append(f"Age {age_years:.1f} is below minimum {min_age}")
            
            if max_age is not None and age_years > max_age:
                age_meets_criteria = False
                rationale_parts.append(f"Age {age_years:.1f} is above maximum {max_age}")
            
            if age_meets_criteria:
                rationale = f"Age {age_years:.1f} years meets criteria"
            else:
                rationale = "; ".join(rationale_parts)
            
            return CriterionResult(
                criterion_id=criterion['id'],
                description=criterion['description'],
                status=CriterionStatus.MET if age_meets_criteria else CriterionStatus.UNMET,
                rationale=rationale,
                evidence=[f"Birth date: {birth_date.date()}", f"Age: {age_years:.1f} years"],
                required=criterion.get('required', True)
            )
            
        except Exception as e:
            return CriterionResult(
                criterion_id=criterion['id'],
                description=criterion['description'],
                status=CriterionStatus.UNCERTAIN,
                rationale=f"Could not evaluate age: {str(e)}",
                evidence=[],
                required=criterion.get('required', True)
            )
    
    def _evaluate_lab_criterion(
        self,
        criterion: Dict[str, Any],
        state: PreAuthState
    ) -> CriterionResult:
        """Evaluate lab value criterion."""
        if not state.get('patient_data') or 'labs' not in state.get('patient_data', {}):
            return CriterionResult(
                criterion_id=criterion['id'],
                description=criterion['description'],
                status=CriterionStatus.UNCERTAIN,
                rationale="Lab data not available",
                evidence=[],
                required=criterion.get('required', True)
            )
        
        lab_code = criterion.get('lab_code')
        lab_name = criterion.get('lab_name', lab_code)
        
        # Find matching lab results
        matching_labs = []
        patient_data = state.get('patient_data', {})
        labs = patient_data.get('labs', [])
        for lab in labs:
            if (lab_code and lab.get('code') == lab_code) or \
               (lab_name and lab_name.lower() in lab.get('name', '').lower()):
                matching_labs.append(lab)
        
        if not matching_labs:
            return CriterionResult(
                criterion_id=criterion['id'],
                description=criterion['description'],
                status=CriterionStatus.UNCERTAIN,
                rationale=f"No lab results found for {lab_name or lab_code}",
                evidence=[],
                required=criterion.get('required', True)
            )
        
        # Use most recent lab result
        most_recent_lab = max(matching_labs, key=lambda x: x.get('date', '1900-01-01'))
        lab_value = most_recent_lab.get('value')
        
        if lab_value is None:
            return CriterionResult(
                criterion_id=criterion['id'],
                description=criterion['description'],
                status=CriterionStatus.UNCERTAIN,
                rationale=f"Lab value not available for {lab_name or lab_code}",
                evidence=[],
                required=criterion.get('required', True)
            )
        
        # Evaluate against thresholds
        min_value = criterion.get('min_value')
        max_value = criterion.get('max_value')
        target_range = criterion.get('target_range')
        
        try:
            lab_value_float = float(lab_value)
            meets_criteria = True
            rationale_parts = []
            
            if min_value is not None and lab_value_float < min_value:
                meets_criteria = False
                rationale_parts.append(f"Value {lab_value_float} below minimum {min_value}")
            
            if max_value is not None and lab_value_float > max_value:
                meets_criteria = False
                rationale_parts.append(f"Value {lab_value_float} above maximum {max_value}")
            
            if target_range:
                target_min, target_max = target_range
                if not (target_min <= lab_value_float <= target_max):
                    meets_criteria = False
                    rationale_parts.append(f"Value {lab_value_float} outside target range {target_min}-{target_max}")
            
            if meets_criteria:
                rationale = f"Lab value {lab_value_float} meets criteria"
            else:
                rationale = "; ".join(rationale_parts)
            
            return CriterionResult(
                criterion_id=criterion['id'],
                description=criterion['description'],
                status=CriterionStatus.MET if meets_criteria else CriterionStatus.UNMET,
                rationale=rationale,
                evidence=[f"Lab: {lab_name or lab_code}", f"Value: {lab_value_float}", f"Date: {most_recent_lab.get('date')}"],
                required=criterion.get('required', True)
            )
            
        except ValueError:
            return CriterionResult(
                criterion_id=criterion['id'],
                description=criterion['description'],
                status=CriterionStatus.UNCERTAIN,
                rationale=f"Could not parse lab value: {lab_value}",
                evidence=[],
                required=criterion.get('required', True)
            )
    
    def _evaluate_medication_criterion(
        self,
        criterion: Dict[str, Any],
        state: PreAuthState
    ) -> CriterionResult:
        """Evaluate medication history criterion."""
        if not state.get('patient_data') or 'medications' not in state.get('patient_data', {}):
            return CriterionResult(
                criterion_id=criterion['id'],
                description=criterion['description'],
                status=CriterionStatus.UNCERTAIN,
                rationale="Medication data not available",
                evidence=[],
                required=criterion.get('required', True)
            )
        
        required_medications = criterion.get('required_medications', [])
        excluded_medications = criterion.get('excluded_medications', [])
        
        evidence = []
        found_required = []
        found_excluded = []
        
        patient_data = state.get('patient_data', {})
        medications = patient_data.get('medications', [])
        for med in medications:
            med_name = med.get('name', '').lower()
            med_code = med.get('code', '').lower()
            
            # Check required medications
            for req_med in required_medications:
                req_med_lower = req_med.lower()
                if req_med_lower in med_name or req_med_lower in med_code:
                    if req_med not in found_required:  # Avoid duplicates
                        found_required.append(req_med)
                    evidence.append(f"Found required medication: {med.get('name', 'Unknown')}")
            
            # Check excluded medications  
            for excl_med in excluded_medications:
                if excl_med.lower() in med_name or excl_med.lower() in med_code:
                    found_excluded.append(excl_med)
                    evidence.append(f"Found excluded medication: {med.get('name', 'Unknown')}")
        
        # Evaluate results
        all_required_found = len(found_required) == len(required_medications) if required_medications else True
        no_excluded_found = len(found_excluded) == 0
        
        meets_criteria = all_required_found and no_excluded_found
        
        rationale_parts = []
        if not all_required_found:
            missing = set(required_medications) - set(found_required)
            rationale_parts.append(f"Missing required medications: {list(missing)}")
        
        if not no_excluded_found:
            rationale_parts.append(f"Found excluded medications: {found_excluded}")
        
        if meets_criteria:
            rationale = "Medication criteria met"
        else:
            rationale = "; ".join(rationale_parts)
        
        return CriterionResult(
            criterion_id=criterion['id'],
            description=criterion['description'],
            status=CriterionStatus.MET if meets_criteria else CriterionStatus.UNMET,
            rationale=rationale,
            evidence=evidence,
            required=criterion.get('required', True)
        )
    
    def _evaluate_condition_criterion(
        self,
        criterion: Dict[str, Any],
        state: PreAuthState
    ) -> CriterionResult:
        """Evaluate condition presence criterion."""
        required_conditions = criterion.get('required_conditions', [])
        any_of_conditions = criterion.get('any_of_conditions', [])
        
        # Use any_of_conditions if provided, otherwise use required_conditions
        conditions_to_check = any_of_conditions or required_conditions
        
        # Check for diagnosis in service requests (from XML)
        patient_info = state.get('patient_info', {})
        services = patient_info.get('services', [])
        
        # Extract actual diagnosis codes from services
        service_diagnosis_codes = []
        for service in services:
            if service.get('diagnosis_code'):
                service_diagnosis_codes.append(service['diagnosis_code'])
        
        # Find matching conditions
        found_conditions = []
        for condition_code in conditions_to_check:
            # Check exact match first
            if condition_code in service_diagnosis_codes:
                found_conditions.append(condition_code)
                continue
            
            # Check for pattern match (e.g., E10 matches E10.9)
            for diag_code in service_diagnosis_codes:
                if (diag_code.startswith(condition_code) or 
                    condition_code.startswith(diag_code.split('.')[0])):
                    found_conditions.append(condition_code)
                    break
        
        # For any_of_conditions, only need to find at least one
        # For required_conditions, need to find all
        if any_of_conditions:
            criteria_met = len(found_conditions) > 0
        else:
            criteria_met = len(found_conditions) == len(required_conditions) if required_conditions else True
        
        if criteria_met:
            return CriterionResult(
                criterion_id=criterion['id'],
                description=criterion['description'],
                status=CriterionStatus.MET,
                rationale=f"Condition criteria met: {', '.join(found_conditions)}",
                evidence=[f"Found condition: {cond}" for cond in found_conditions],
                required=criterion.get('required', True)
            )
        else:
            if any_of_conditions:
                return CriterionResult(
                    criterion_id=criterion['id'],
                    description=criterion['description'],
                    status=CriterionStatus.UNMET,
                    rationale=f"No qualifying conditions found from: {', '.join(any_of_conditions)}",
                    evidence=[f"Searched for: {cond}" for cond in any_of_conditions],
                    required=criterion.get('required', True)
                )
            else:
                missing = set(required_conditions) - set(found_conditions)
                return CriterionResult(
                    criterion_id=criterion['id'],
                    description=criterion['description'],
                    status=CriterionStatus.UNMET,
                    rationale=f"Missing required conditions: {', '.join(missing)}",
                    evidence=[f"Found condition: {cond}" for cond in found_conditions],
                    required=criterion.get('required', True)
                )
    
    def _evaluate_therapy_duration_criterion(
        self,
        criterion: Dict[str, Any],
        state: PreAuthState
    ) -> CriterionResult:
        """Evaluate therapy duration criterion."""
        # This would use temporal reasoning to check therapy duration
        required_duration = criterion.get('required_duration', '6 weeks')
        return CriterionResult(
            criterion_id=criterion['id'],
            description=criterion['description'],
            status=CriterionStatus.UNCERTAIN,
            rationale=f"Therapy duration evaluation not yet implemented (requires {required_duration})",
            evidence=[],
            required=criterion.get('required', True)
        )
    
    def _evaluate_imaging_recency_criterion(
        self,
        criterion: Dict[str, Any],
        state: PreAuthState
    ) -> CriterionResult:
        """Evaluate imaging recency criterion."""
        # This would check if imaging is recent enough
        max_age = criterion.get('max_age', '6 months')
        return CriterionResult(
            criterion_id=criterion['id'],
            description=criterion['description'],
            status=CriterionStatus.UNCERTAIN,
            rationale=f"Imaging recency evaluation not yet implemented (max age {max_age})",
            evidence=[],
            required=criterion.get('required', True)
        )
    
    def _evaluate_documentation_criterion(
        self,
        criterion: Dict[str, Any],
        state: PreAuthState
    ) -> CriterionResult:
        """Evaluate documentation completeness criterion."""
        required_docs = criterion.get('required_documents', [])
        return CriterionResult(
            criterion_id=criterion['id'],
            description=criterion['description'],
            status=CriterionStatus.UNCERTAIN,
            rationale=f"Documentation check not yet implemented (requires: {required_docs})",
            evidence=[],
            required=criterion.get('required', True)
        )
    
    def _generate_rationale(
        self,
        criteria_results: List[CriterionResult],
        policy_id: str
    ) -> str:
        """Generate overall policy evaluation rationale."""
        met_count = sum(1 for r in criteria_results if r.status == CriterionStatus.MET)
        unmet_count = sum(1 for r in criteria_results if r.status == CriterionStatus.UNMET)
        uncertain_count = sum(1 for r in criteria_results if r.status == CriterionStatus.UNCERTAIN)
        total_count = len(criteria_results)
        
        rationale = f"Policy {policy_id} evaluation: {met_count}/{total_count} criteria met"
        
        if unmet_count > 0:
            rationale += f", {unmet_count} unmet"
        
        if uncertain_count > 0:
            rationale += f", {uncertain_count} uncertain"
        
        return rationale


def evaluate_service_against_policies(
    service_codes: List[str],
    diagnosis_codes: List[str],
    state: PreAuthState,
    policies_dir: Optional[str] = None
) -> Optional[PolicyEvaluation]:
    """
    Main entry point for policy evaluation.
    
    Args:
        service_codes: List of procedure/service codes (e.g., CPT codes)
        diagnosis_codes: List of diagnosis codes (e.g., ICD-10 codes)
        state: Current workflow state with patient data
        policies_dir: Optional path to policies directory
        
    Returns:
        PolicyEvaluation if applicable policy found, None otherwise
    """
    engine = PolicyRulesEngine(policies_dir)
    
    # Load all available policies
    policies_dir_path = Path(policies_dir) if policies_dir else Path(__file__).parent / "policies"
    for policy_file in policies_dir_path.glob("*.yaml"):
        try:
            engine.load_policy(policy_file.name)
        except Exception as e:
            print(f"Warning: Could not load policy {policy_file.name}: {e}")
    
    # Find applicable policy
    applicable_policy = engine.get_applicable_policy(service_codes, diagnosis_codes)
    
    if not applicable_policy:
        return None
    
    # Evaluate the policy
    return engine.evaluate_policy(applicable_policy, state)


if __name__ == "__main__":
    # Example usage and testing
    from preauth_system.state import create_initial_state
    
    # Create a test state
    test_state = create_initial_state(
        xml_file_path="/test/path.xml",
        xml_format="eclaim"
    )
    
    # Example evaluation
    evaluation = evaluate_service_against_policies(
        service_codes=["95250"],  # CGM
        diagnosis_codes=["E10.9"],  # Type 1 diabetes
        state=test_state
    )
    
    if evaluation:
        print(f"Policy: {evaluation.policy_id}")
        print(f"Score: {evaluation.overall_score}")
        print(f"Rationale: {evaluation.rationale}")
    else:
        print("No applicable policy found")