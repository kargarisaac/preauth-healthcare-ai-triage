#!/usr/bin/env python3
"""
Patient Lookup Service
Resolves patient IDs to folder paths and retrieves patient history.

This service builds an index mapping patient IDs from profile.json files
to their folder locations, enabling proper patient context retrieval
for Claude pre-authorization analysis.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from loguru import logger

# Simplified config - removed complex config_loader


class PatientLookupService:
    """
    Service for resolving patient IDs to folder paths and retrieving patient history.
    
    Handles the mismatch between folder names (1, 2, 3...) and actual patient IDs
    (UUIDs from profile.json files) by building and maintaining an index.
    """
    
    def __init__(self, dataset_path: Optional[str] = None):
        """
        Initialize patient lookup service.
        
        Args:
            dataset_path: Path to dataset directory (uses config if not provided)
        """
        # Simplified: use direct paths instead of complex config
        self.raw_data_path = Path(dataset_path or "data/dataset_1/raw_data")
        self.processed_data_path = Path("data/dataset_1/processed_data")
        self.patient_index = {}
        self._build_patient_index()
        
        logger.info(f"PatientLookupService initialized with {len(self.patient_index)} patients")
        logger.info(f"Raw data path: {self.raw_data_path}")
        logger.info(f"Processed data path: {self.processed_data_path}")
    
    def _build_patient_index(self) -> None:
        """Build patient_id → folder_path mapping from profile.json files."""
        self._build_patient_database()
    
    def _build_patient_database(self) -> None:
        """Build patient database from profile.json files in raw_data."""
        if not self.raw_data_path.exists():
            logger.warning(f"Raw data path does not exist: {self.raw_data_path}")
            return
        
        for folder in self.raw_data_path.iterdir():
            if folder.is_dir():
                profile_path = folder / "profile.json"
                if profile_path.exists():
                    try:
                        with open(profile_path, 'r', encoding='utf-8') as f:
                            profile = json.load(f)
                            patient_id = profile.get("patient_id")
                            
                            if patient_id:
                                self.patient_index[patient_id] = folder
                                logger.debug(f"Indexed patient {patient_id} → {folder.name}")
                            else:
                                logger.warning(f"No patient_id found in {profile_path}")
                                
                    except (json.JSONDecodeError, IOError) as e:
                        logger.error(f"Failed to read profile {profile_path}: {e}")
                else:
                    logger.debug(f"No profile.json found in {folder}")
        
        logger.info(f"Built patient database with {len(self.patient_index)} patients")
    
    def find_patient_folder(self, patient_id: str) -> Optional[Path]:
        """
        Find folder path for given patient_id.
        
        Args:
            patient_id: Patient UUID from profile.json
            
        Returns:
            Path to patient folder, or None if not found
        """
        folder = self.patient_index.get(patient_id)
        if folder:
            logger.debug(f"Found patient {patient_id} in folder {folder.name}")
        else:
            logger.warning(f"Patient {patient_id} not found in index")
        return folder
    
    def get_patient_profile(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """
        Get patient profile data.
        
        Args:
            patient_id: Patient UUID
            
        Returns:
            Patient profile data, or None if not found
        """
        folder = self.find_patient_folder(patient_id)
        if not folder:
            return None
        
        profile_path = folder / "profile.json"
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to read profile for {patient_id}: {e}")
            return None
    
    def get_patient_history(self, patient_id: str) -> List[Dict[str, Any]]:
        """
        Get all historical JSON files for patient from processed dataset.
        
        Args:
            patient_id: Patient UUID
            
        Returns:
            List of historical FHIR Bundles for the patient
        """
        folder = self.find_patient_folder(patient_id)
        if not folder:
            logger.warning(f"Cannot get history for unknown patient {patient_id}")
            return []
        
        # Look in processed dataset using folder name
        processed_folder = self.processed_data_path / folder.name
        if not processed_folder.exists():
            logger.info(f"No processed data found for patient {patient_id} in {processed_folder}")
            return []
        
        # Get all JSON files except profile.json
        json_files = [f for f in processed_folder.glob("*.json") if f.name != "profile.json"]
        json_files.sort()  # Sort by filename for chronological order
        
        history = []
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    history.append(data)
                    logger.debug(f"Loaded historical data from {json_file.name}")
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Failed to read historical data {json_file}: {e}")
        
        logger.info(f"Retrieved {len(history)} historical records for patient {patient_id}")
        return history
    
    def get_all_patients(self) -> Dict[str, str]:
        """
        Get all patients in the index.
        
        Returns:
            Dict mapping patient_id → folder_name
        """
        return {pid: folder.name for pid, folder in self.patient_index.items()}
    
    def refresh_index(self) -> None:
        """Refresh the patient index by rescanning the dataset."""
        logger.info("Refreshing patient index...")
        self.patient_index.clear()
        self._build_patient_index()
    
    def extract_patient_id_from_bundle(self, bundle: Dict[str, Any]) -> Optional[str]:
        """
        Extract patient ID from FHIR Bundle.
        
        Args:
            bundle: FHIR Bundle dictionary
            
        Returns:
            Patient ID if found, None otherwise
        """
        # Try to extract from various possible locations in the bundle
        
        # 1. Check bundle ID (might be patient ID)
        bundle_id = bundle.get("id")
        if bundle_id and bundle_id in self.patient_index:
            return bundle_id
        
        # 2. Check authorization_id field (common in our bundles)
        auth_id = bundle.get("authorization_id")
        if auth_id and auth_id in self.patient_index:
            return auth_id
        
        # 3. Check FHIR resources for Patient resource
        fhir_resources = bundle.get("fhir_resources", {})
        for resource_id, resource in fhir_resources.items():
            if resource.get("resourceType") == "Patient":
                patient_id = resource.get("id")
                if patient_id and patient_id in self.patient_index:
                    return patient_id
        
        # 4. Check raw_data for patient identifiers
        raw_data = bundle.get("raw_data", {})
        if isinstance(raw_data, dict):
            # Look for common patient ID fields
            for field_name in ["patient_id", "patientId", "member_id", "memberId"]:
                patient_id = raw_data.get(field_name)
                if patient_id and patient_id in self.patient_index:
                    return patient_id
        
        logger.warning("Could not extract patient ID from bundle")
        return None
    
    def validate_patient_folder_structure(self, patient_id: str) -> Dict[str, Any]:
        """
        Validate patient folder structure and contents.
        
        Args:
            patient_id: Patient UUID
            
        Returns:
            Validation results with details about folder contents
        """
        folder = self.find_patient_folder(patient_id)
        if not folder:
            return {
                "valid": False,
                "error": f"Patient {patient_id} not found"
            }
        
        validation = {
            "valid": True,
            "patient_id": patient_id,
            "folder_name": folder.name,
            "folder_path": str(folder),
            "has_profile": False,
            "xml_files": 0,
            "processed_folder_exists": False,
            "processed_json_files": 0
        }
        
        # Check profile.json
        profile_path = folder / "profile.json"
        validation["has_profile"] = profile_path.exists()
        
        # Count XML files
        xml_files = list(folder.glob("*.xml"))
        validation["xml_files"] = len(xml_files)
        
        # Check processed folder
        processed_folder = self.processed_data_path / folder.name
        validation["processed_folder_exists"] = processed_folder.exists()
        
        if processed_folder.exists():
            json_files = [f for f in processed_folder.glob("*.json") if f.name != "profile.json"]
            validation["processed_json_files"] = len(json_files)
        
        # Determine overall validity
        if not validation["has_profile"]:
            validation["valid"] = False
            validation["error"] = "Missing profile.json"
        elif validation["xml_files"] == 0:
            validation["valid"] = False
            validation["error"] = "No XML files found"
        
        return validation
    
    def build_patient_database(self) -> Dict[str, Any]:
        """
        Build complete patient database from profile.json files.
        
        Returns:
            Dictionary with database statistics and patient information
        """
        logger.info("Building patient database from profile.json files...")
        
        # Clear existing index
        self.patient_index.clear()
        
        # Build new index
        self._build_patient_database()
        
        # Collect statistics
        stats = {
            "total_patients": len(self.patient_index),
            "patients_with_raw_data": 0,
            "patients_with_processed_data": 0,
            "patients_with_both": 0,
            "raw_data_path": str(self.raw_data_path),
            "processed_data_path": str(self.processed_data_path),
            "timestamp": "now"
        }
        
        # Check data availability for each patient
        for patient_id, folder in self.patient_index.items():
            has_raw = len(list(folder.glob("*.xml"))) > 0
            has_processed = (self.processed_data_path / folder.name).exists()
            
            if has_raw:
                stats["patients_with_raw_data"] += 1
            if has_processed:
                stats["patients_with_processed_data"] += 1
            if has_raw and has_processed:
                stats["patients_with_both"] += 1
        
        logger.info(f"Patient database built: {stats['total_patients']} patients, "
                   f"{stats['patients_with_both']} with complete data")
        
        return stats
    
    def get_all_patients_for_dropdown(self) -> List[Dict[str, Any]]:
        """
        Get all patients formatted for dropdown selection.
        
        Returns:
            List of patient information for dropdown display
        """
        patients = []
        
        for patient_id, folder in self.patient_index.items():
            # Get profile information
            profile = self.get_patient_profile(patient_id)
            if not profile:
                continue
            
            # Count available data
            xml_count = len(list(folder.glob("*.xml")))
            processed_folder = self.processed_data_path / folder.name
            json_count = 0
            if processed_folder.exists():
                json_count = len([f for f in processed_folder.glob("*.json") if f.name != "profile.json"])
            
            patient_info = {
                "patient_id": patient_id,
                "name": profile.get("full_name", "Unknown"),
                "dob": profile.get("date_of_birth", "Unknown"),
                "insurance_company": profile.get("insurance_details", {}).get("company", "Unknown"),
                "insurance_id": profile.get("insurance_details", {}).get("policy_number", "Unknown"),
                "member_id": profile.get("insurance_details", {}).get("member_id", "Unknown"),
                "xml_files_count": xml_count,
                "processed_files_count": json_count,
                "has_data": xml_count > 0 or json_count > 0,
                "folder_name": folder.name
            }
            
            patients.append(patient_info)
        
        # Sort by name for better UX
        patients.sort(key=lambda x: x["name"])
        
        logger.debug(f"Retrieved {len(patients)} patients for dropdown")
        return patients
    
    def check_patient_data_availability(self, patient_id: str) -> Dict[str, Any]:
        """
        Check if patient exists in both raw_data and processed_data.
        
        Args:
            patient_id: Patient UUID
            
        Returns:
            Dictionary with data availability status
        """
        folder = self.find_patient_folder(patient_id)
        if not folder:
            return {
                "patient_exists": False,
                "raw_data_available": False,
                "processed_data_available": False,
                "error": f"Patient {patient_id} not found"
            }
        
        # Check raw data
        xml_files = list(folder.glob("*.xml"))
        has_raw_data = len(xml_files) > 0
        
        # Check processed data
        processed_folder = self.processed_data_path / folder.name
        has_processed_data = processed_folder.exists()
        json_files = []
        if has_processed_data:
            json_files = [f for f in processed_folder.glob("*.json") if f.name != "profile.json"]
        
        return {
            "patient_exists": True,
            "patient_id": patient_id,
            "folder_name": folder.name,
            "raw_data_available": has_raw_data,
            "processed_data_available": has_processed_data and len(json_files) > 0,
            "raw_data_path": str(folder),
            "processed_data_path": str(processed_folder) if has_processed_data else None,
            "xml_files_count": len(xml_files),
            "json_files_count": len(json_files),
            "xml_files": [f.name for f in xml_files],
            "json_files": [f.name for f in json_files]
        }
    
    def get_patient_folder_paths(self, patient_id: str) -> Optional[Dict[str, str]]:
        """
        Get patient folder paths for raw and processed data.
        
        Args:
            patient_id: Patient UUID
            
        Returns:
            Dictionary with folder paths or None if patient not found
        """
        folder = self.find_patient_folder(patient_id)
        if not folder:
            return None
        
        processed_folder = self.processed_data_path / folder.name
        
        return {
            "patient_id": patient_id,
            "folder_name": folder.name,
            "raw_data_path": str(folder),
            "processed_data_path": str(processed_folder),
            "raw_data_exists": folder.exists(),
            "processed_data_exists": processed_folder.exists()
        }
    
    def create_patient_folders(self, patient_id: str) -> Dict[str, str]:
        """
        Create patient folders in both raw_data and processed_data if they don't exist.
        
        Args:
            patient_id: Patient UUID
            
        Returns:
            Dictionary with created folder paths
        """
        # Use patient_id as folder name for new patients
        raw_folder = self.raw_data_path / patient_id
        processed_folder = self.processed_data_path / patient_id
        
        # Create directories
        try:
            raw_folder.mkdir(parents=True, exist_ok=True)
            processed_folder.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Created patient folders for {patient_id}")
            
            # Add to index
            self.patient_index[patient_id] = raw_folder
            
            return {
                "patient_id": patient_id,
                "raw_data_path": str(raw_folder),
                "processed_data_path": str(processed_folder),
                "created": True
            }
            
        except OSError as e:
            logger.error(f"Failed to create patient folders for {patient_id}: {e}")
            raise ValueError(f"Failed to create patient folders: {e}")
    
    def get_patient_summary_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics for all patients in the database.
        
        Returns:
            Dictionary with patient summary statistics
        """
        stats = {
            "total_patients": len(self.patient_index),
            "patients_with_raw_data": 0,
            "patients_with_processed_data": 0,
            "patients_with_complete_data": 0,
            "total_xml_files": 0,
            "total_json_files": 0,
            "insurance_companies": set(),
            "data_sources": {"eclaim": 0, "shafafiya": 0, "unknown": 0}
        }
        
        for patient_id, folder in self.patient_index.items():
            # Count files
            xml_files = list(folder.glob("*.xml"))
            processed_folder = self.processed_data_path / folder.name
            json_files = []
            
            if processed_folder.exists():
                json_files = [f for f in processed_folder.glob("*.json") if f.name != "profile.json"]
            
            has_raw = len(xml_files) > 0
            has_processed = len(json_files) > 0
            
            if has_raw:
                stats["patients_with_raw_data"] += 1
                stats["total_xml_files"] += len(xml_files)
            
            if has_processed:
                stats["patients_with_processed_data"] += 1
                stats["total_json_files"] += len(json_files)
            
            if has_raw and has_processed:
                stats["patients_with_complete_data"] += 1
            
            # Get profile for additional stats
            profile = self.get_patient_profile(patient_id)
            if profile:
                insurance_company = profile.get("insurance_details", {}).get("company")
                if insurance_company:
                    stats["insurance_companies"].add(insurance_company)
            
            # Detect data sources from filenames
            for xml_file in xml_files:
                filename = xml_file.name.lower()
                if "dubai" in filename or "eclaim" in filename:
                    stats["data_sources"]["eclaim"] += 1
                elif "abudhabi" in filename or "shafafiya" in filename:
                    stats["data_sources"]["shafafiya"] += 1
                else:
                    stats["data_sources"]["unknown"] += 1
        
        # Convert set to list for JSON serialization
        stats["insurance_companies"] = list(stats["insurance_companies"])
        
        return stats


# Global service instance
_patient_lookup_service = None

def get_patient_lookup_service() -> PatientLookupService:
    """Get global patient lookup service instance."""
    global _patient_lookup_service
    if _patient_lookup_service is None:
        _patient_lookup_service = PatientLookupService()
    return _patient_lookup_service