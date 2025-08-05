#!/usr/bin/env python3
"""
Unit tests for PatientLookupService
Tests patient ID resolution and history retrieval functionality.
"""

import json
import sys
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.services.patient_lookup_service import PatientLookupService  # noqa: E402


class TestPatientLookupService:
    """Test suite for PatientLookupService."""
    
    @pytest.fixture
    def sample_profile_data(self):
        """Sample profile.json data."""
        return {
            "patient_id": "11f5688b-6c4a-4c41-baad-71e6a4b82d91",
            "full_name": "Test Patient",
            "gender": "Male",
            "birth_year": 1985,
            "nationality": "Indian"
        }
    
    @pytest.fixture
    def sample_fhir_bundle(self):
        """Sample FHIR Bundle."""
        return {
            "resourceType": "Bundle",
            "id": "test-bundle",
            "authorization_id": "11f5688b-6c4a-4c41-baad-71e6a4b82d91",
            "fhir_resources": {
                "Patient/test": {
                    "resourceType": "Patient",
                    "id": "11f5688b-6c4a-4c41-baad-71e6a4b82d91"
                }
            },
            "raw_data": {
                "patient_id": "11f5688b-6c4a-4c41-baad-71e6a4b82d91"
            }
        }
    
    def test_build_patient_index_success(self, sample_profile_data):
        """Test successful patient index building."""
        with TemporaryDirectory() as temp_dir:
            dataset_path = Path(temp_dir)
            
            # Create patient folder with profile.json
            patient_folder = dataset_path / "1"
            patient_folder.mkdir()
            
            profile_path = patient_folder / "profile.json"
            with open(profile_path, 'w') as f:
                json.dump(sample_profile_data, f)
            
            # Initialize service
            service = PatientLookupService(dataset_path=str(dataset_path))
            
            # Verify index was built
            assert len(service.patient_index) == 1
            assert "11f5688b-6c4a-4c41-baad-71e6a4b82d91" in service.patient_index
            assert service.patient_index["11f5688b-6c4a-4c41-baad-71e6a4b82d91"] == patient_folder
    
    def test_build_patient_index_no_profile(self):
        """Test index building with folder missing profile.json."""
        with TemporaryDirectory() as temp_dir:
            dataset_path = Path(temp_dir)
            
            # Create patient folder without profile.json
            patient_folder = dataset_path / "1"
            patient_folder.mkdir()
            
            service = PatientLookupService(dataset_path=str(dataset_path))
            
            # Should have empty index
            assert len(service.patient_index) == 0
    
    def test_build_patient_index_invalid_json(self):
        """Test index building with invalid JSON in profile."""
        with TemporaryDirectory() as temp_dir:
            dataset_path = Path(temp_dir)
            
            # Create patient folder with invalid profile.json
            patient_folder = dataset_path / "1"
            patient_folder.mkdir()
            
            profile_path = patient_folder / "profile.json"
            with open(profile_path, 'w') as f:
                f.write("invalid json content")
            
            service = PatientLookupService(dataset_path=str(dataset_path))
            
            # Should have empty index due to JSON error
            assert len(service.patient_index) == 0
    
    def test_find_patient_folder_success(self, sample_profile_data):
        """Test successful patient folder finding."""
        with TemporaryDirectory() as temp_dir:
            dataset_path = Path(temp_dir)
            patient_folder = dataset_path / "1"
            patient_folder.mkdir()
            
            profile_path = patient_folder / "profile.json"
            with open(profile_path, 'w') as f:
                json.dump(sample_profile_data, f)
            
            service = PatientLookupService(dataset_path=str(dataset_path))
            
            # Find patient folder
            found_folder = service.find_patient_folder("11f5688b-6c4a-4c41-baad-71e6a4b82d91")
            
            assert found_folder == patient_folder
    
    def test_find_patient_folder_not_found(self):
        """Test patient folder finding for non-existent patient."""
        with TemporaryDirectory() as temp_dir:
            dataset_path = Path(temp_dir)
            service = PatientLookupService(dataset_path=str(dataset_path))
            
            # Try to find non-existent patient
            found_folder = service.find_patient_folder("non-existent-id")
            
            assert found_folder is None
    
    def test_get_patient_profile_success(self, sample_profile_data):
        """Test successful patient profile retrieval."""
        with TemporaryDirectory() as temp_dir:
            dataset_path = Path(temp_dir)
            patient_folder = dataset_path / "1"
            patient_folder.mkdir()
            
            profile_path = patient_folder / "profile.json"
            with open(profile_path, 'w') as f:
                json.dump(sample_profile_data, f)
            
            service = PatientLookupService(dataset_path=str(dataset_path))
            
            # Get patient profile
            profile = service.get_patient_profile("11f5688b-6c4a-4c41-baad-71e6a4b82d91")
            
            assert profile == sample_profile_data
            assert profile["full_name"] == "Test Patient"
    
    def test_get_patient_profile_not_found(self):
        """Test patient profile retrieval for non-existent patient."""
        with TemporaryDirectory() as temp_dir:
            dataset_path = Path(temp_dir)
            service = PatientLookupService(dataset_path=str(dataset_path))
            
            profile = service.get_patient_profile("non-existent-id")
            
            assert profile is None
    
    def test_get_patient_history_success(self, sample_profile_data):
        """Test successful patient history retrieval."""
        with TemporaryDirectory() as temp_dir:
            dataset_path = Path(temp_dir)
            processed_path = Path(temp_dir) / "processed_dataset"
            
            # Create patient folder
            patient_folder = dataset_path / "1"
            patient_folder.mkdir()
            
            profile_path = patient_folder / "profile.json"
            with open(profile_path, 'w') as f:
                json.dump(sample_profile_data, f)
            
            # Create processed folder with JSON files
            processed_patient_folder = processed_path / "1"
            processed_patient_folder.mkdir(parents=True)
            
            # Create historical JSON files
            bundle1 = {"resourceType": "Bundle", "id": "bundle-1"}
            bundle2 = {"resourceType": "Bundle", "id": "bundle-2"}
            
            with open(processed_patient_folder / "req01.json", 'w') as f:
                json.dump(bundle1, f)
            with open(processed_patient_folder / "req02.json", 'w') as f:
                json.dump(bundle2, f)
            with open(processed_patient_folder / "profile.json", 'w') as f:
                json.dump(sample_profile_data, f)
            
            # Initialize service with custom processed path
            service = PatientLookupService(dataset_path=str(dataset_path))
            service.processed_path = processed_path
            
            # Get patient history
            history = service.get_patient_history("11f5688b-6c4a-4c41-baad-71e6a4b82d91")
            
            assert len(history) == 2
            assert history[0]["id"] == "bundle-1"
            assert history[1]["id"] == "bundle-2"
    
    def test_get_patient_history_no_processed_data(self, sample_profile_data):
        """Test patient history retrieval with no processed data."""
        with TemporaryDirectory() as temp_dir:
            dataset_path = Path(temp_dir)
            patient_folder = dataset_path / "1"
            patient_folder.mkdir()
            
            profile_path = patient_folder / "profile.json"
            with open(profile_path, 'w') as f:
                json.dump(sample_profile_data, f)
            
            service = PatientLookupService(dataset_path=str(dataset_path))
            
            # Get patient history (should be empty)
            history = service.get_patient_history("11f5688b-6c4a-4c41-baad-71e6a4b82d91")
            
            assert len(history) == 0
    
    def test_extract_patient_id_from_bundle_authorization_id(self, sample_fhir_bundle, sample_profile_data):
        """Test patient ID extraction from bundle authorization_id."""
        with TemporaryDirectory() as temp_dir:
            dataset_path = Path(temp_dir)
            patient_folder = dataset_path / "1"
            patient_folder.mkdir()
            
            profile_path = patient_folder / "profile.json"
            with open(profile_path, 'w') as f:
                json.dump(sample_profile_data, f)
            
            service = PatientLookupService(dataset_path=str(dataset_path))
            
            # Extract patient ID
            patient_id = service.extract_patient_id_from_bundle(sample_fhir_bundle)
            
            assert patient_id == "11f5688b-6c4a-4c41-baad-71e6a4b82d91"
    
    def test_extract_patient_id_from_bundle_patient_resource(self, sample_profile_data):
        """Test patient ID extraction from Patient resource."""
        bundle = {
            "resourceType": "Bundle",
            "fhir_resources": {
                "Patient/test": {
                    "resourceType": "Patient",
                    "id": "11f5688b-6c4a-4c41-baad-71e6a4b82d91"
                }
            }
        }
        
        with TemporaryDirectory() as temp_dir:
            dataset_path = Path(temp_dir)
            patient_folder = dataset_path / "1"
            patient_folder.mkdir()
            
            profile_path = patient_folder / "profile.json"
            with open(profile_path, 'w') as f:
                json.dump(sample_profile_data, f)
            
            service = PatientLookupService(dataset_path=str(dataset_path))
            
            patient_id = service.extract_patient_id_from_bundle(bundle)
            
            assert patient_id == "11f5688b-6c4a-4c41-baad-71e6a4b82d91"
    
    def test_extract_patient_id_from_bundle_raw_data(self, sample_profile_data):
        """Test patient ID extraction from raw_data."""
        bundle = {
            "resourceType": "Bundle",
            "raw_data": {
                "patient_id": "11f5688b-6c4a-4c41-baad-71e6a4b82d91"
            }
        }
        
        with TemporaryDirectory() as temp_dir:
            dataset_path = Path(temp_dir)
            patient_folder = dataset_path / "1"
            patient_folder.mkdir()
            
            profile_path = patient_folder / "profile.json"
            with open(profile_path, 'w') as f:
                json.dump(sample_profile_data, f)
            
            service = PatientLookupService(dataset_path=str(dataset_path))
            
            patient_id = service.extract_patient_id_from_bundle(bundle)
            
            assert patient_id == "11f5688b-6c4a-4c41-baad-71e6a4b82d91"
    
    def test_extract_patient_id_from_bundle_not_found(self):
        """Test patient ID extraction when no valid ID found."""
        bundle = {
            "resourceType": "Bundle",
            "id": "unknown-bundle"
        }
        
        with TemporaryDirectory() as temp_dir:
            dataset_path = Path(temp_dir)
            service = PatientLookupService(dataset_path=str(dataset_path))
            
            patient_id = service.extract_patient_id_from_bundle(bundle)
            
            assert patient_id is None
    
    def test_validate_patient_folder_structure_valid(self, sample_profile_data):
        """Test patient folder structure validation for valid folder."""
        with TemporaryDirectory() as temp_dir:
            dataset_path = Path(temp_dir)
            processed_path = Path(temp_dir) / "processed_dataset"
            
            # Create patient folder with XML files
            patient_folder = dataset_path / "1"
            patient_folder.mkdir()
            
            profile_path = patient_folder / "profile.json"
            with open(profile_path, 'w') as f:
                json.dump(sample_profile_data, f)
            
            # Create XML files
            (patient_folder / "req01.xml").touch()
            (patient_folder / "req02.xml").touch()
            
            # Create processed folder
            processed_patient_folder = processed_path / "1"
            processed_patient_folder.mkdir(parents=True)
            (processed_patient_folder / "req01.json").touch()
            
            service = PatientLookupService(dataset_path=str(dataset_path))
            service.processed_path = processed_path
            
            validation = service.validate_patient_folder_structure("11f5688b-6c4a-4c41-baad-71e6a4b82d91")
            
            assert validation["valid"] is True
            assert validation["has_profile"] is True
            assert validation["xml_files"] == 2
            assert validation["processed_json_files"] == 1
    
    def test_validate_patient_folder_structure_missing_profile(self):
        """Test validation for folder missing profile.json."""
        with TemporaryDirectory() as temp_dir:
            dataset_path = Path(temp_dir)
            
            # Create patient folder without profile.json
            patient_folder = dataset_path / "1"
            patient_folder.mkdir()
            (patient_folder / "req01.xml").touch()
            
            # Manually add to index (simulating folder exists but no profile)
            service = PatientLookupService(dataset_path=str(dataset_path))
            service.patient_index["test-patient-id"] = patient_folder
            
            validation = service.validate_patient_folder_structure("test-patient-id")
            
            assert validation["valid"] is False
            assert validation["error"] == "Missing profile.json"
    
    def test_get_all_patients(self, sample_profile_data):
        """Test getting all patients in index."""
        with TemporaryDirectory() as temp_dir:
            dataset_path = Path(temp_dir)
            
            # Create multiple patient folders
            for i, patient_id in enumerate(["patient-1", "patient-2"], 1):
                patient_folder = dataset_path / str(i)
                patient_folder.mkdir()
                
                profile_data = sample_profile_data.copy()
                profile_data["patient_id"] = patient_id
                
                profile_path = patient_folder / "profile.json"
                with open(profile_path, 'w') as f:
                    json.dump(profile_data, f)
            
            service = PatientLookupService(dataset_path=str(dataset_path))
            
            all_patients = service.get_all_patients()
            
            assert len(all_patients) == 2
            assert "patient-1" in all_patients
            assert "patient-2" in all_patients
            assert all_patients["patient-1"] == "1"
            assert all_patients["patient-2"] == "2"
    
    def test_refresh_index(self, sample_profile_data):
        """Test index refresh functionality."""
        with TemporaryDirectory() as temp_dir:
            dataset_path = Path(temp_dir)
            
            # Initially create one patient
            patient_folder = dataset_path / "1"
            patient_folder.mkdir()
            
            profile_path = patient_folder / "profile.json"
            with open(profile_path, 'w') as f:
                json.dump(sample_profile_data, f)
            
            service = PatientLookupService(dataset_path=str(dataset_path))
            assert len(service.patient_index) == 1
            
            # Add another patient
            patient_folder2 = dataset_path / "2"
            patient_folder2.mkdir()
            
            profile_data2 = sample_profile_data.copy()
            profile_data2["patient_id"] = "second-patient-id"
            
            profile_path2 = patient_folder2 / "profile.json"
            with open(profile_path2, 'w') as f:
                json.dump(profile_data2, f)
            
            # Refresh index
            service.refresh_index()
            
            assert len(service.patient_index) == 2
            assert "second-patient-id" in service.patient_index


if __name__ == "__main__":
    pytest.main([__file__, "-v"])