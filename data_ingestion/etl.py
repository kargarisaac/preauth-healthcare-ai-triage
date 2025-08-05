#!/usr/bin/env python3
"""
Simple ETL for Patient Data Retrieval
=====================================

Simple data retrieval system that gets patient data from CSV and FHIR files.
No agent logic - just pure data extraction.

Usage:
    from etl import get_patient_data, DATASET_PATH
    data = get_patient_data("Patient_001")
"""

import pandas as pd
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Dataset path configuration - set outside functions
DATASET_PATH = Path(__file__).parent.parent / "data" / "dataset_2" / "synthetic_dataset"

def get_patient_data(patient_id: str, dataset_path: str = None) -> Dict[str, Any]:
    """
    Get all data for a specific patient from CSV and FHIR files.
    
    Args:
        patient_id: Patient ID (e.g., "Patient_001")
        dataset_path: Path to dataset directory (auto-detected if None)
        
    Returns:
        Dictionary with all patient data
    """
    
    # Use provided path or default
    if not dataset_path:
        dataset_path = DATASET_PATH
        
    if not Path(dataset_path).exists():
        raise FileNotFoundError(f"Dataset directory not found: {dataset_path}")
    
    dataset_path = Path(dataset_path)
    csv_path = dataset_path / "CSV"
    fhir_path = dataset_path / "FHIR_JSON"
    
    # Load CSV data
    csv_data = {
        'patients': pd.read_csv(csv_path / "patients.csv"),
        'labs': pd.read_csv(csv_path / "labs.csv"),
        'medications': pd.read_csv(csv_path / "medications.csv"),
        'claims': pd.read_csv(csv_path / "claims.csv"),
        'preauth_requests': pd.read_csv(csv_path / "preauth_requests.csv")
    }
    
    # Extract patient-specific data
    patient_data = {}
    
    # Demographics
    patient_row = csv_data['patients'][csv_data['patients']['patient_id'] == patient_id]
    if patient_row.empty:
        raise ValueError(f"Patient {patient_id} not found")
    
    patient_data['demographics'] = patient_row.iloc[0].to_dict()
    
    # Lab records
    patient_data['labs'] = csv_data['labs'][csv_data['labs']['patient_id'] == patient_id].to_dict('records')
    
    # Medications
    patient_data['medications'] = csv_data['medications'][csv_data['medications']['patient_id'] == patient_id].to_dict('records')
    
    # Claims
    patient_data['claims'] = csv_data['claims'][csv_data['claims']['patient_id'] == patient_id].to_dict('records')
    
    # Pre-authorization history
    patient_data['preauth_history'] = csv_data['preauth_requests'][csv_data['preauth_requests']['patient_id'] == patient_id].to_dict('records')
    
    # FHIR bundle
    fhir_file = fhir_path / f"{patient_id.lower()}.json"
    if fhir_file.exists():
        with open(fhir_file, 'r') as f:
            patient_data['fhir_bundle'] = json.load(f)
    else:
        patient_data['fhir_bundle'] = None
    
    return patient_data

def find_patient_by_emirates_id(emirates_id: str, dataset_path: str = None) -> Optional[str]:
    """
    Find patient ID by Emirates ID.
    
    Args:
        emirates_id: Emirates ID to search for
        dataset_path: Path to dataset directory
        
    Returns:
        Patient ID if found, None otherwise
    """
    
    if not dataset_path:
        dataset_path = DATASET_PATH
    
    csv_path = Path(dataset_path) / "CSV"
    patients_df = pd.read_csv(csv_path / "patients.csv")
    
    match = patients_df[patients_df['emirates_id'] == emirates_id]
    if not match.empty:
        return match.iloc[0]['patient_id']
    
    return None

# Example usage
if __name__ == "__main__":
    # Test the ETL
    try:
        data = get_patient_data("Patient_001")
        print(f"✅ Retrieved data for {data['demographics']['first_name']} {data['demographics']['last_name']}")
        print(f"   Lab records: {len(data['labs'])}")
        print(f"   Medications: {len(data['medications'])}")
        print(f"   Claims: {len(data['claims'])}")
        print(f"   FHIR bundle: {'✅' if data['fhir_bundle'] else '❌'}")
        
        # Test Emirates ID lookup
        emirates_id = data['demographics']['emirates_id']
        found_id = find_patient_by_emirates_id(emirates_id)
        print(f"   Emirates ID lookup: {found_id}")
        
    except Exception as e:
        print(f"❌ ETL Error: {e}")