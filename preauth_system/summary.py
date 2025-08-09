"""
Clinical Data Summarization Module
=================================

Aggregates clinical data from FHIR/CSV sources and produces structured clinical summaries.
Integrates with the existing ETL system and provides support for agentic LLM synthesis.

Key Functions:
- Clinical data aggregation from FHIR/CSV using data_ingestion/etl.py
- Structured clinical summary generation
- Integration point for agentic LLM synthesis (configurable)
- eGFR calculation and kidney function assessment
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

from data_ingestion.etl import get_patient_data
from preauth_system.utils import calculate_egfr, get_latest_creatinine


@dataclass
class ClinicalSummary:
    """
    Structured clinical summary for pre-authorization requests.
    """
    # Patient Demographics
    patient_id: str
    emirates_id: str
    age: int
    gender: str
    
    # Clinical Problems
    active_conditions: List[Dict[str, Any]]
    primary_diagnoses: List[str]
    
    # Treatment History  
    current_medications: List[Dict[str, Any]]
    prior_treatments: List[Dict[str, Any]]
    treatment_responses: List[Dict[str, Any]]
    
    # Recent Clinical Data (Last 12 months)
    recent_labs: List[Dict[str, Any]]
    recent_imaging: List[Dict[str, Any]]
    recent_procedures: List[Dict[str, Any]]
    
    # Risk Factors
    risk_factors: List[str]
    allergies: List[str]
    
    # Healthcare Utilization
    recent_claims: List[Dict[str, Any]]
    preauth_history: List[Dict[str, Any]]
    
    # Calculated Values
    egfr_latest: Optional[float]
    kidney_function_stage: Optional[str]
    
    # Quality Indicators
    data_completeness_score: float  # 0-1 scale
    last_updated: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'patient_id': self.patient_id,
            'emirates_id': self.emirates_id,
            'age': self.age,
            'gender': self.gender,
            'active_conditions': self.active_conditions,
            'primary_diagnoses': self.primary_diagnoses,
            'current_medications': self.current_medications,
            'prior_treatments': self.prior_treatments,
            'treatment_responses': self.treatment_responses,
            'recent_labs': self.recent_labs,
            'recent_imaging': self.recent_imaging,
            'recent_procedures': self.recent_procedures,
            'risk_factors': self.risk_factors,
            'allergies': self.allergies,
            'recent_claims': self.recent_claims,
            'preauth_history': self.preauth_history,
            'egfr_latest': self.egfr_latest,
            'kidney_function_stage': self.kidney_function_stage,
            'data_completeness_score': self.data_completeness_score,
            'last_updated': self.last_updated
        }


class ClinicalDataAggregator:
    """
    Aggregates clinical data from multiple sources into structured summaries.
    """
    
    # Clinical significance thresholds
    RECENT_PERIOD_MONTHS = 12
    MAX_RECENT_LABS = 10
    MAX_RECENT_CLAIMS = 5
    
    # eGFR staging (CKD stages)
    EGFR_STAGES = {
        (90, float('inf')): 'Normal (≥90)',
        (60, 90): 'Mild decrease (60-89)', 
        (45, 60): 'Moderate decrease (45-59)',
        (30, 45): 'Moderate to severe decrease (30-44)',
        (15, 30): 'Severe decrease (15-29)',
        (0, 15): 'Kidney failure (<15)'
    }
    
    @classmethod
    def calculate_age(cls, date_of_birth: str) -> int:
        """
        Calculate age from date of birth string.
        
        Args:
            date_of_birth: DOB in DD/MM/YYYY format
            
        Returns:
            Age in years
        """
        try:
            dob = datetime.strptime(date_of_birth, '%d/%m/%Y')
            today = datetime.now()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            return max(0, age)
        except (ValueError, AttributeError):
            return 0
    
    @classmethod
    def get_egfr_stage(cls, egfr: float) -> str:
        """
        Determine CKD stage based on eGFR value.
        
        Args:
            egfr: eGFR value in mL/min/1.73m²
            
        Returns:
            CKD stage description
        """
        for (min_egfr, max_egfr), stage in cls.EGFR_STAGES.items():
            if min_egfr <= egfr < max_egfr:
                return stage
        return 'Unknown'
    
    @classmethod
    def filter_recent_data(cls, data_list: List[Dict], date_field: str, months: int = None) -> List[Dict]:
        """
        Filter data to recent entries within specified months.
        
        Args:
            data_list: List of data records with date field
            date_field: Name of the date field to filter on
            months: Number of months back to include (default: RECENT_PERIOD_MONTHS)
            
        Returns:
            Filtered list of recent data
        """
        if not months:
            months = cls.RECENT_PERIOD_MONTHS
            
        cutoff_date = datetime.now() - timedelta(days=months * 30)
        recent_data = []
        
        for item in data_list:
            try:
                item_date = datetime.strptime(item.get(date_field, ''), '%Y-%m-%d')
                if item_date >= cutoff_date:
                    recent_data.append(item)
            except (ValueError, TypeError):
                # Include items with invalid dates for manual review
                recent_data.append(item)
                
        # Sort by date, most recent first
        recent_data.sort(key=lambda x: x.get(date_field, ''), reverse=True)
        return recent_data
    
    @classmethod
    def extract_risk_factors(cls, patient_data: Dict[str, Any]) -> List[str]:
        """
        Extract risk factors from patient data.
        
        Args:
            patient_data: Complete patient data from ETL
            
        Returns:
            List of identified risk factors
        """
        risk_factors = []
        demographics = patient_data.get('demographics', {})
        
        # Age-based risk factors
        age = cls.calculate_age(demographics.get('date_of_birth', ''))
        if age < 18:
            risk_factors.append('Pediatric patient')
        elif age >= 65:
            risk_factors.append('Advanced age (≥65)')
            
        # Gender-specific considerations
        gender = demographics.get('gender', '').upper()
        if gender == 'F':
            # Check for reproductive age considerations
            if 18 <= age <= 50:
                risk_factors.append('Reproductive age female')
                
        # Weight-based risk factors
        try:
            weight = float(demographics.get('weight', 0))
            height = float(demographics.get('height', 0))
            if height > 0:
                bmi = weight / ((height/100) ** 2)
                if bmi >= 30:
                    risk_factors.append('Obesity (BMI ≥30)')
                elif bmi < 18.5:
                    risk_factors.append('Underweight (BMI <18.5)')
        except (ValueError, TypeError):
            pass
            
        # Medical history risk factors
        conditions = []
        for claim in patient_data.get('claims', []):
            diagnosis = claim.get('diagnosis_code', '').upper()
            if diagnosis.startswith('E1'):  # Diabetes
                conditions.append('Diabetes mellitus')
            elif diagnosis.startswith('I'):  # Cardiovascular
                conditions.append('Cardiovascular disease')
            elif diagnosis.startswith('N18'):  # CKD
                conditions.append('Chronic kidney disease')
            elif diagnosis.startswith('J44'):  # COPD
                conditions.append('COPD')
                
        risk_factors.extend(list(set(conditions)))
        
        # Medication-based risk factors
        medications = patient_data.get('medications', [])
        high_risk_meds = ['warfarin', 'insulin', 'metformin', 'digoxin']
        for med in medications:
            med_name = med.get('medication_name', '').lower()
            for risk_med in high_risk_meds:
                if risk_med in med_name:
                    risk_factors.append(f'High-risk medication: {risk_med}')
                    
        return list(set(risk_factors))  # Remove duplicates
    
    @classmethod
    def calculate_data_completeness(cls, patient_data: Dict[str, Any]) -> float:
        """
        Calculate data completeness score (0-1).
        
        Args:
            patient_data: Complete patient data
            
        Returns:
            Completeness score between 0 and 1
        """
        required_fields = [
            ('demographics', 'emirates_id'),
            ('demographics', 'date_of_birth'),
            ('demographics', 'gender'),
            ('labs', None),  # Has any labs
            ('medications', None),  # Has any medications
            ('claims', None)  # Has any claims
        ]
        
        score = 0
        total_checks = len(required_fields)
        
        for section, field in required_fields:
            section_data = patient_data.get(section, {})
            if field is None:
                # Check for any data in section
                if section_data:
                    score += 1
            else:
                # Check specific field
                if isinstance(section_data, dict) and section_data.get(field):
                    score += 1
                elif isinstance(section_data, list) and section_data:
                    score += 1
                    
        return round(score / total_checks, 2)


def build_clinical_summary(patient_id: str, mode: str = 'deterministic') -> ClinicalSummary:
    """
    Build structured clinical summary for a patient.
    
    Args:
        patient_id: Patient identifier
        mode: Processing mode ('deterministic', 'hybrid', or 'agentic')
        
    Returns:
        ClinicalSummary object
        
    Raises:
        Exception: If patient data cannot be retrieved
    """
    # Get patient data from ETL
    patient_data = get_patient_data(patient_id)
    demographics = patient_data['demographics']
    
    # Calculate age
    age = ClinicalDataAggregator.calculate_age(demographics.get('date_of_birth', ''))
    
    # Process medications
    current_medications = []
    for med in patient_data.get('medications', []):
        current_medications.append({
            'name': med.get('medication_name', ''),
            'dosage': med.get('dosage', ''),
            'frequency': med.get('frequency', ''),
            'start_date': med.get('start_date', ''),
            'prescriber': med.get('prescribing_provider', ''),
            'indication': med.get('indication', '')
        })
    
    # Process recent labs (last 12 months, top 10)
    recent_labs = ClinicalDataAggregator.filter_recent_data(
        patient_data.get('labs', []), 'test_date'
    )[:ClinicalDataAggregator.MAX_RECENT_LABS]
    
    # Calculate eGFR if creatinine available
    egfr_latest = None
    kidney_function_stage = None
    
    creatinine_data = get_latest_creatinine(patient_data)
    if creatinine_data:
        egfr_latest = calculate_egfr(
            creatinine_data['value'],
            age,
            demographics.get('gender', 'M')
        )
        kidney_function_stage = ClinicalDataAggregator.get_egfr_stage(egfr_latest)
    
    # Process recent claims
    recent_claims = ClinicalDataAggregator.filter_recent_data(
        patient_data.get('claims', []), 'service_date'
    )[:ClinicalDataAggregator.MAX_RECENT_CLAIMS]
    
    # Extract active conditions from claims
    active_conditions = []
    diagnoses_seen = set()
    for claim in recent_claims:
        diagnosis_code = claim.get('diagnosis_code', '')
        diagnosis_desc = claim.get('diagnosis_description', '')
        if diagnosis_code and diagnosis_code not in diagnoses_seen:
            active_conditions.append({
                'code': diagnosis_code,
                'description': diagnosis_desc,
                'first_seen': claim.get('service_date', ''),
                'last_seen': claim.get('service_date', ''),
                'frequency': 1
            })
            diagnoses_seen.add(diagnosis_code)
    
    # Extract primary diagnoses (most common)
    primary_diagnoses = list(diagnoses_seen)[:5]  # Top 5 most recent
    
    # Process prior treatments from claims
    prior_treatments = []
    for claim in recent_claims:
        if claim.get('procedure_code'):
            prior_treatments.append({
                'procedure_code': claim.get('procedure_code', ''),
                'procedure_description': claim.get('procedure_description', ''),
                'date': claim.get('service_date', ''),
                'provider': claim.get('provider_name', ''),
                'outcome': 'Unknown'  # Would need additional data
            })
    
    # Get risk factors
    risk_factors = ClinicalDataAggregator.extract_risk_factors(patient_data)
    
    # Calculate data completeness
    completeness = ClinicalDataAggregator.calculate_data_completeness(patient_data)
    
    # Create clinical summary
    summary = ClinicalSummary(
        patient_id=patient_id,
        emirates_id=demographics.get('emirates_id', ''),
        age=age,
        gender=demographics.get('gender', ''),
        active_conditions=active_conditions,
        primary_diagnoses=primary_diagnoses,
        current_medications=current_medications,
        prior_treatments=prior_treatments,
        treatment_responses=[],  # Would need outcome data
        recent_labs=recent_labs,
        recent_imaging=[],  # Not available in current dataset
        recent_procedures=prior_treatments[:5],  # Reuse procedure data
        risk_factors=risk_factors,
        allergies=[],  # Would extract from medical history if available
        recent_claims=recent_claims,
        preauth_history=patient_data.get('preauth_history', []),
        egfr_latest=egfr_latest,
        kidney_function_stage=kidney_function_stage,
        data_completeness_score=completeness,
        last_updated=datetime.now().isoformat()
    )
    
    return summary


def get_clinical_context_for_services(summary: ClinicalSummary, requested_services: List[Dict]) -> Dict[str, Any]:
    """
    Get relevant clinical context for requested services.
    
    Args:
        summary: Clinical summary for patient
        requested_services: List of requested services with codes
        
    Returns:
        Dict with relevant clinical context for the services
    """
    context = {
        'patient_age_category': 'pediatric' if summary.age < 18 else 'adult' if summary.age < 65 else 'geriatric',
        'diabetes_related': False,
        'cardiac_related': False,
        'renal_concerns': summary.egfr_latest is not None and summary.egfr_latest < 60,
        'relevant_conditions': [],
        'relevant_medications': [],
        'relevant_labs': [],
        'safety_considerations': []
    }
    
    # Analyze service codes for clinical context
    service_codes = [service.get('code', '') for service in requested_services]
    
    # Check for diabetes-related services
    diabetes_codes = ['E0784', '95250', '90772', '82962']  # Pump, CGM, injection, glucose tests
    if any(code in service_codes for code in diabetes_codes):
        context['diabetes_related'] = True
        
        # Find diabetes-related conditions and meds
        for condition in summary.active_conditions:
            if condition['code'].startswith('E1'):  # Diabetes codes
                context['relevant_conditions'].append(condition)
                
        for med in summary.current_medications:
            if 'insulin' in med['name'].lower() or 'metformin' in med['name'].lower():
                context['relevant_medications'].append(med)
                
        # Find relevant labs
        diabetes_labs = ['HbA1c', 'Glucose', 'C-peptide']
        for lab in summary.recent_labs:
            if any(lab_name in lab.get('test_name', '') for lab_name in diabetes_labs):
                context['relevant_labs'].append(lab)
    
    # Check for cardiac procedures
    cardiac_codes = ['93000', '93307', '93458']  # ECG, Echo, Cath
    if any(code in service_codes for code in cardiac_codes):
        context['cardiac_related'] = True
    
    # Add safety considerations based on context
    if context['renal_concerns']:
        context['safety_considerations'].append('Renal function impairment - consider dose adjustments')
        
    if summary.age < 18:
        context['safety_considerations'].append('Pediatric patient - age-appropriate dosing and monitoring')
        
    if 'High-risk medication: warfarin' in summary.risk_factors:
        context['safety_considerations'].append('Warfarin therapy - bleeding risk considerations')
    
    return context


# Example usage and testing
if __name__ == "__main__":
    # Test with Patient_007 (pediatric diabetes case)
    try:
        summary = build_clinical_summary("Patient_007", mode='deterministic')
        
        print(f"✅ Clinical Summary for {summary.patient_id}")
        print(f"   Age: {summary.age}, Gender: {summary.gender}")
        print(f"   Active Conditions: {len(summary.active_conditions)}")
        print(f"   Current Medications: {len(summary.current_medications)}")
        print(f"   Recent Labs: {len(summary.recent_labs)}")
        print(f"   Risk Factors: {', '.join(summary.risk_factors)}")
        
        if summary.egfr_latest:
            print(f"   eGFR: {summary.egfr_latest} mL/min/1.73m² ({summary.kidney_function_stage})")
            
        print(f"   Data Completeness: {summary.data_completeness_score * 100:.0f}%")
        
        # Test service context
        test_services = [{'code': 'E0784'}, {'code': '95250'}]  # Pump and CGM
        context = get_clinical_context_for_services(summary, test_services)
        print(f"   Service Context - Diabetes Related: {context['diabetes_related']}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()