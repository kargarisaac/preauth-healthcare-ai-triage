"""
Clinical Safety Assessment Module
================================

Performs basic safety checks for pre-authorization requests including:
- eGFR thresholds and renal safety
- Medication interactions and contraindications  
- Age-based risk flags
- Red flag detection for high-risk procedures

Key Functions:
- Basic safety checks with eGFR thresholds
- Medication safety for diabetes therapies
- Age-based risk stratification
- Contrast imaging safety assessment
- Structured warning outputs for decision engine
"""

from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

from preauth_system.summary import ClinicalSummary


class RiskLevel(Enum):
    """Risk level categorization."""
    LOW = "LOW"
    MODERATE = "MODERATE" 
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class SafetyAlert:
    """
    Individual safety alert or warning.
    """
    alert_id: str
    category: str  # 'renal', 'cardiac', 'medication', 'age', 'procedure'
    severity: RiskLevel
    title: str
    description: str
    recommendation: str
    clinical_evidence: List[str]  # Supporting evidence from patient data
    contraindication: bool = False  # True if absolute contraindication
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'alert_id': self.alert_id,
            'category': self.category,
            'severity': self.severity.value,
            'title': self.title,
            'description': self.description,
            'recommendation': self.recommendation,
            'clinical_evidence': self.clinical_evidence,
            'contraindication': self.contraindication
        }


@dataclass
class SafetyAssessment:
    """
    Complete safety assessment for a PA request.
    """
    patient_id: str
    assessment_timestamp: str
    overall_risk_level: RiskLevel
    
    # Safety alerts by category
    renal_alerts: List[SafetyAlert]
    cardiac_alerts: List[SafetyAlert]
    medication_alerts: List[SafetyAlert]
    age_alerts: List[SafetyAlert]
    procedure_alerts: List[SafetyAlert]
    
    # Summary
    total_alerts: int
    critical_alerts: int
    contraindications: int
    
    # Recommendations
    monitoring_requirements: List[str]
    dose_adjustments: List[str]
    alternative_approaches: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        all_alerts = (self.renal_alerts + self.cardiac_alerts + 
                     self.medication_alerts + self.age_alerts + self.procedure_alerts)
        
        return {
            'patient_id': self.patient_id,
            'assessment_timestamp': self.assessment_timestamp,
            'overall_risk_level': self.overall_risk_level.value,
            'alerts': [alert.to_dict() for alert in all_alerts],
            'alerts_by_category': {
                'renal': [alert.to_dict() for alert in self.renal_alerts],
                'cardiac': [alert.to_dict() for alert in self.cardiac_alerts],
                'medication': [alert.to_dict() for alert in self.medication_alerts],
                'age': [alert.to_dict() for alert in self.age_alerts],
                'procedure': [alert.to_dict() for alert in self.procedure_alerts]
            },
            'summary': {
                'total_alerts': self.total_alerts,
                'critical_alerts': self.critical_alerts,
                'contraindications': self.contraindications
            },
            'recommendations': {
                'monitoring_requirements': self.monitoring_requirements,
                'dose_adjustments': self.dose_adjustments,
                'alternative_approaches': self.alternative_approaches
            }
        }


class RenalSafetyChecker:
    """
    Checks for renal safety concerns based on eGFR and procedures.
    """
    
    # eGFR thresholds for different interventions
    EGFR_THRESHOLDS = {
        'contrast_imaging': 30,  # Avoid contrast if eGFR < 30
        'metformin_caution': 30,  # Metformin caution if eGFR < 30
        'dose_adjustment': 60,   # Consider dose adjustments if eGFR < 60
        'nephrotoxic_drugs': 60  # Extra caution with nephrotoxic drugs
    }
    
    # Contrast procedures that require eGFR monitoring
    CONTRAST_PROCEDURES = [
        'CT_CONTRAST', 'MRI_GADOLINIUM', 'CARDIAC_CATH', 
        'ANGIOGRAPHY', 'IVP', 'VENOGRAPHY'
    ]
    
    @classmethod
    def check_renal_safety(cls, summary: ClinicalSummary, requested_services: List[Dict]) -> List[SafetyAlert]:
        """
        Check for renal safety concerns.
        
        Args:
            summary: Patient clinical summary
            requested_services: List of requested services
            
        Returns:
            List of renal safety alerts
        """
        alerts = []
        
        if summary.egfr_latest is None:
            # Missing eGFR data
            alerts.append(SafetyAlert(
                alert_id=f"RENAL_001_{datetime.now().strftime('%H%M%S')}",
                category='renal',
                severity=RiskLevel.MODERATE,
                title='Missing eGFR Data',
                description='eGFR not available for renal safety assessment',
                recommendation='Obtain recent creatinine and calculate eGFR before proceeding',
                clinical_evidence=['No recent creatinine values found'],
                contraindication=False
            ))
            return alerts
        
        egfr = summary.egfr_latest
        
        # Check eGFR thresholds
        if egfr < cls.EGFR_THRESHOLDS['contrast_imaging']:
            alerts.append(SafetyAlert(
                alert_id=f"RENAL_002_{datetime.now().strftime('%H%M%S')}",
                category='renal',
                severity=RiskLevel.HIGH,
                title='Severe Renal Impairment - Contrast Risk',
                description=f'eGFR {egfr} mL/min/1.73m² indicates severe renal impairment',
                recommendation='Avoid contrast agents; consider alternative imaging modalities',
                clinical_evidence=[f'eGFR: {egfr} mL/min/1.73m²', summary.kidney_function_stage],
                contraindication=True
            ))
            
        elif egfr < cls.EGFR_THRESHOLDS['dose_adjustment']:
            alerts.append(SafetyAlert(
                alert_id=f"RENAL_003_{datetime.now().strftime('%H%M%S')}",
                category='renal',
                severity=RiskLevel.MODERATE,
                title='Moderate Renal Impairment',
                description=f'eGFR {egfr} mL/min/1.73m² requires dose adjustments',
                recommendation='Consider dose adjustments for renally-cleared medications',
                clinical_evidence=[f'eGFR: {egfr} mL/min/1.73m²', summary.kidney_function_stage],
                contraindication=False
            ))
        
        # Check for metformin with renal impairment
        has_metformin = any('metformin' in med['name'].lower() 
                          for med in summary.current_medications)
        
        if has_metformin and egfr < cls.EGFR_THRESHOLDS['metformin_caution']:
            alerts.append(SafetyAlert(
                alert_id=f"RENAL_004_{datetime.now().strftime('%H%M%S')}",
                category='renal',
                severity=RiskLevel.HIGH,
                title='Metformin with Renal Impairment',
                description='Metformin contraindicated with severe renal impairment',
                recommendation='Discontinue metformin; consider alternative diabetes therapy',
                clinical_evidence=[f'eGFR: {egfr} mL/min/1.73m²', 'Current metformin therapy'],
                contraindication=True
            ))
        
        return alerts


class MedicationSafetyChecker:
    """
    Checks for medication interactions and safety concerns.
    """
    
    # High-risk medications requiring monitoring
    HIGH_RISK_MEDICATIONS = {
        'insulin': {
            'risks': ['hypoglycemia', 'weight_gain'],
            'monitoring': ['glucose_monitoring', 'hba1c_q3months'],
            'contraindications': ['diabetic_ketoacidosis']
        },
        'metformin': {
            'risks': ['lactic_acidosis', 'gi_upset'],
            'monitoring': ['renal_function', 'b12_levels'],
            'contraindications': ['severe_renal_impairment', 'heart_failure']
        },
        'warfarin': {
            'risks': ['bleeding', 'thrombosis'],
            'monitoring': ['inr_monitoring', 'bleeding_assessment'],
            'contraindications': ['active_bleeding', 'severe_hepatic_impairment']
        }
    }
    
    # Diabetes therapy safety considerations
    DIABETES_SAFETY_RULES = [
        {
            'condition': 'pediatric_t1dm',
            'age_range': (0, 18),
            'diagnosis': 'E10',
            'considerations': ['growth_monitoring', 'hypoglycemia_risk', 'school_management']
        }
    ]
    
    @classmethod
    def check_medication_safety(cls, summary: ClinicalSummary, requested_services: List[Dict]) -> List[SafetyAlert]:
        """
        Check for medication safety concerns.
        
        Args:
            summary: Patient clinical summary
            requested_services: List of requested services
            
        Returns:
            List of medication safety alerts
        """
        alerts = []
        
        # Check high-risk medications
        for med in summary.current_medications:
            med_name = med.get('name', '').lower()
            
            for risk_med, safety_info in cls.HIGH_RISK_MEDICATIONS.items():
                if risk_med in med_name:
                    # Check for specific contraindications
                    if risk_med == 'metformin' and summary.egfr_latest and summary.egfr_latest < 30:
                        alerts.append(SafetyAlert(
                            alert_id=f"MED_001_{datetime.now().strftime('%H%M%S')}",
                            category='medication',
                            severity=RiskLevel.HIGH,
                            title=f'{risk_med.title()} Safety Concern',
                            description='Metformin with severe renal impairment increases lactic acidosis risk',
                            recommendation='Consider alternative diabetes therapy',
                            clinical_evidence=[f'Current {risk_med} therapy', f'eGFR: {summary.egfr_latest}'],
                            contraindication=True
                        ))
                    
                    # Check for insulin in pediatric patients
                    elif risk_med == 'insulin' and summary.age < 18:
                        alerts.append(SafetyAlert(
                            alert_id=f"MED_002_{datetime.now().strftime('%H%M%S')}",
                            category='medication',
                            severity=RiskLevel.MODERATE,
                            title='Pediatric Insulin Therapy',
                            description='Pediatric patients require specialized insulin monitoring',
                            recommendation='Ensure appropriate pediatric glucose monitoring and hypoglycemia protocols',
                            clinical_evidence=[f'Age: {summary.age} years', 'Current insulin therapy'],
                            contraindication=False
                        ))
        
        # Check for diabetes technology with appropriate therapy
        diabetes_tech_codes = ['E0784', '95250']  # Pump, CGM
        service_codes = [svc.get('code', '') for svc in requested_services]
        
        if any(code in service_codes for code in diabetes_tech_codes):
            has_insulin = any('insulin' in med['name'].lower() for med in summary.current_medications)
            if not has_insulin:
                alerts.append(SafetyAlert(
                    alert_id=f"MED_003_{datetime.now().strftime('%H%M%S')}",
                    category='medication',
                    severity=RiskLevel.HIGH,
                    title='Diabetes Technology without Insulin',
                    description='Insulin pump/CGM requested without current insulin therapy',
                    recommendation='Confirm insulin therapy before approving diabetes technology',
                    clinical_evidence=['No current insulin medications documented'],
                    contraindication=True
                ))
        
        return alerts


class AgeSafetyChecker:
    """
    Checks for age-based safety concerns and requirements.
    """
    
    @classmethod
    def check_age_safety(cls, summary: ClinicalSummary, requested_services: List[Dict]) -> List[SafetyAlert]:
        """
        Check for age-based safety concerns.
        
        Args:
            summary: Patient clinical summary  
            requested_services: List of requested services
            
        Returns:
            List of age-based safety alerts
        """
        alerts = []
        age = summary.age
        
        # Pediatric safety considerations (< 18 years)
        if age < 18:
            alerts.append(SafetyAlert(
                alert_id=f"AGE_001_{datetime.now().strftime('%H%M%S')}",
                category='age',
                severity=RiskLevel.MODERATE,
                title='Pediatric Patient Considerations',
                description=f'Patient age {age} years requires pediatric-specific protocols',
                recommendation='Ensure pediatric dosing, monitoring, and safety protocols',
                clinical_evidence=[f'Age: {age} years'],
                contraindication=False
            ))
            
            # Specific pediatric diabetes considerations
            diabetes_conditions = [cond for cond in summary.active_conditions 
                                 if cond['code'].startswith('E1')]
            if diabetes_conditions:
                alerts.append(SafetyAlert(
                    alert_id=f"AGE_002_{datetime.now().strftime('%H%M%S')}",
                    category='age',
                    severity=RiskLevel.MODERATE,
                    title='Pediatric Diabetes Management',
                    description='Pediatric diabetes requires specialized monitoring and family education',
                    recommendation='Ensure age-appropriate diabetes education and monitoring protocols',
                    clinical_evidence=[f'Age: {age} years', 'Type 1 diabetes diagnosis'],
                    contraindication=False
                ))
        
        # Geriatric considerations (≥ 65 years)
        elif age >= 65:
            alerts.append(SafetyAlert(
                alert_id=f"AGE_003_{datetime.now().strftime('%H%M%S')}",
                category='age',
                severity=RiskLevel.MODERATE,
                title='Geriatric Patient Considerations',
                description=f'Patient age {age} years may require dose adjustments and enhanced monitoring',
                recommendation='Consider age-related pharmacokinetic changes and comorbidities',
                clinical_evidence=[f'Age: {age} years'],
                contraindication=False
            ))
        
        return alerts


class ProcedureSafetyChecker:
    """
    Checks for procedure-specific safety concerns.
    """
    
    # High-risk procedures requiring special consideration
    HIGH_RISK_PROCEDURES = {
        '61885': {  # DBS insertion
            'title': 'Deep Brain Stimulation',
            'risks': ['intracranial_bleeding', 'infection', 'device_malfunction'],
            'requirements': ['neurosurgical_evaluation', 'multidisciplinary_team']
        },
        '29881': {  # Knee arthroscopy
            'title': 'Knee Arthroscopy',
            'risks': ['bleeding', 'infection', 'dvt'],
            'requirements': ['conservative_therapy_trial']
        }
    }
    
    @classmethod
    def check_procedure_safety(cls, summary: ClinicalSummary, requested_services: List[Dict]) -> List[SafetyAlert]:
        """
        Check for procedure-specific safety concerns.
        
        Args:
            summary: Patient clinical summary
            requested_services: List of requested services
            
        Returns:
            List of procedure safety alerts
        """
        alerts = []
        
        for service in requested_services:
            service_code = service.get('code', '')
            
            if service_code in cls.HIGH_RISK_PROCEDURES:
                proc_info = cls.HIGH_RISK_PROCEDURES[service_code]
                
                alerts.append(SafetyAlert(
                    alert_id=f"PROC_001_{service_code}_{datetime.now().strftime('%H%M%S')}",
                    category='procedure',
                    severity=RiskLevel.HIGH,
                    title=f'High-Risk Procedure: {proc_info["title"]}',
                    description=f'Procedure {service_code} carries significant risks requiring careful evaluation',
                    recommendation=f'Ensure {", ".join(proc_info["requirements"])} before approval',
                    clinical_evidence=[f'Requested procedure: {service_code}'],
                    contraindication=False
                ))
        
        return alerts


def run_basic_safety_checks(summary: ClinicalSummary, requested_services: List[Dict]) -> SafetyAssessment:
    """
    Run comprehensive basic safety checks for a PA request.
    
    Args:
        summary: Patient clinical summary
        requested_services: List of requested services with codes
        
    Returns:
        SafetyAssessment with all identified safety concerns
    """
    # Run all safety checks
    renal_alerts = RenalSafetyChecker.check_renal_safety(summary, requested_services)
    medication_alerts = MedicationSafetyChecker.check_medication_safety(summary, requested_services)
    age_alerts = AgeSafetyChecker.check_age_safety(summary, requested_services)
    procedure_alerts = ProcedureSafetyChecker.check_procedure_safety(summary, requested_services)
    
    # Combine all alerts
    all_alerts = renal_alerts + medication_alerts + age_alerts + procedure_alerts
    
    # Calculate summary statistics
    total_alerts = len(all_alerts)
    critical_alerts = len([alert for alert in all_alerts if alert.severity == RiskLevel.CRITICAL])
    contraindications = len([alert for alert in all_alerts if alert.contraindication])
    
    # Determine overall risk level
    if contraindications > 0:
        overall_risk = RiskLevel.CRITICAL
    elif any(alert.severity == RiskLevel.HIGH for alert in all_alerts):
        overall_risk = RiskLevel.HIGH
    elif any(alert.severity == RiskLevel.MODERATE for alert in all_alerts):
        overall_risk = RiskLevel.MODERATE
    else:
        overall_risk = RiskLevel.LOW
    
    # Generate monitoring requirements
    monitoring_requirements = []
    dose_adjustments = []
    alternative_approaches = []
    
    for alert in all_alerts:
        if 'monitoring' in alert.recommendation.lower():
            monitoring_requirements.append(alert.recommendation)
        elif 'dose' in alert.recommendation.lower():
            dose_adjustments.append(alert.recommendation)
        elif 'alternative' in alert.recommendation.lower():
            alternative_approaches.append(alert.recommendation)
    
    # Create safety assessment
    assessment = SafetyAssessment(
        patient_id=summary.patient_id,
        assessment_timestamp=datetime.now().isoformat(),
        overall_risk_level=overall_risk,
        renal_alerts=renal_alerts,
        cardiac_alerts=[],  # Not implemented in basic version
        medication_alerts=medication_alerts,
        age_alerts=age_alerts,
        procedure_alerts=procedure_alerts,
        total_alerts=total_alerts,
        critical_alerts=critical_alerts,
        contraindications=contraindications,
        monitoring_requirements=list(set(monitoring_requirements)),
        dose_adjustments=list(set(dose_adjustments)),
        alternative_approaches=list(set(alternative_approaches))
    )
    
    return assessment


# Example usage and testing
if __name__ == "__main__":
    # Test with Patient_007 data
    try:
        from preauth_system.summary import build_clinical_summary
        
        summary = build_clinical_summary("Patient_007")
        test_services = [
            {'code': 'E0784', 'description': 'Insulin pump'},
            {'code': '95250', 'description': 'CGM'}
        ]
        
        safety_assessment = run_basic_safety_checks(summary, test_services)
        
        print(f"✅ Safety Assessment for {summary.patient_id}")
        print(f"   Overall Risk Level: {safety_assessment.overall_risk_level.value}")
        print(f"   Total Alerts: {safety_assessment.total_alerts}")
        print(f"   Critical Alerts: {safety_assessment.critical_alerts}")
        print(f"   Contraindications: {safety_assessment.contraindications}")
        
        # Print alerts by category
        for category in ['renal', 'medication', 'age', 'procedure']:
            alerts = getattr(safety_assessment, f'{category}_alerts')
            if alerts:
                print(f"   {category.title()} Alerts: {len(alerts)}")
                for alert in alerts:
                    print(f"     - {alert.title} ({alert.severity.value})")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()