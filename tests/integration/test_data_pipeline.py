"""
Integration tests for the Data Pipeline system.

This module tests the complete XML to JSON conversion pipeline
that processes synthetic healthcare data using existing processors.
"""

import pytest
import tempfile
import json
from pathlib import Path
from pipelines.data_pipeline import DataPipeline


class TestDataPipeline:
    """Test data pipeline XML to JSON conversion."""

    @pytest.fixture
    def temp_source_dir(self):
        """Create temporary source directory with test data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            source_dir.mkdir()
            
            # Create patient directory
            patient_dir = source_dir / "1"
            patient_dir.mkdir()
            
            # Create minimal profile.json
            profile_data = {
                "patient_id": "test-patient-123",
                "full_name": "Test Patient",
                "gender": "Male",
                "birth_year": 1980
            }
            with open(patient_dir / "profile.json", "w") as f:
                json.dump(profile_data, f)
            
            # Create minimal XML file (Shafafiya format)
            xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<Prior.Authorization>
  <Header>
    <SenderID>TEST001</SenderID>
    <ReceiverID>TEST002</ReceiverID>
    <TransactionDate>01/01/2025 10:00</TransactionDate>
  </Header>
  <Authorization>
    <ID>TEST-AUTH-001</ID>  
    <Result>Yes</Result>
    <Comments>Test authorization</Comments>
    <Activity>
      <ID>1</ID>
      <Type>3</Type>
      <Code>99999</Code>
      <Quantity>1</Quantity>
      <Net>100.00</Net>
    </Activity>
  </Authorization>
</Prior.Authorization>'''
            
            with open(patient_dir / "test_shafafiya.xml", "w") as f:
                f.write(xml_content)
            
            yield str(source_dir)

    @pytest.fixture  
    def temp_output_dir(self):
        """Create temporary output directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield str(temp_dir)

    @pytest.fixture
    def pipeline(self, temp_source_dir, temp_output_dir):
        """DataPipeline instance for testing."""
        return DataPipeline(
            source_dir=temp_source_dir,
            output_dir=temp_output_dir,
            enable_validation=False  # Disable for testing
        )

    def test_pipeline_initialization(self, pipeline):
        """Test pipeline initialization."""
        assert pipeline.source_dir.exists()
        assert pipeline.xml_processor is not None
        assert pipeline.csv_processor is not None
        assert pipeline.stats['total_patients'] == 0

    def test_setup_output_directory(self, pipeline):
        """Test output directory setup."""
        pipeline.setup_output_directory()
        
        assert pipeline.output_dir.exists()
        assert (pipeline.output_dir / "json_bundles").exists()
        assert (pipeline.output_dir / "metadata").exists()
        assert (pipeline.output_dir / "logs").exists()

    def test_detect_xml_format(self, pipeline, temp_source_dir):
        """Test XML format detection."""
        patient_dir = Path(temp_source_dir) / "1"
        xml_file = patient_dir / "test_shafafiya.xml"
        
        format_type = pipeline.detect_xml_format(xml_file)
        assert format_type in ['eclaim', 'shafafiya']

    def test_process_xml_file(self, pipeline, temp_source_dir):
        """Test processing single XML file."""
        patient_dir = Path(temp_source_dir) / "1"
        xml_file = patient_dir / "test_shafafiya.xml"
        
        result = pipeline.process_xml_file(xml_file, 'shafafiya')
        
        assert result is not None
        assert result['resourceType'] == 'Bundle'
        assert result['meta']['source'] == 'Shafafiya'
        assert 'pipeline_metadata' in result
        assert result['pipeline_metadata']['format_detected'] == 'shafafiya'

    def test_process_patient_dry_run(self, pipeline):
        """Test processing patient in dry run mode."""
        result = pipeline.process_patient("1", dry_run=True)
        
        assert result['status'] in ['completed', 'partial']
        assert result['patient_id'] == "1"
        assert result['processed_files'] >= 0
        assert 'details' in result
        assert 'processed' in result['details']

    def test_process_patient_live(self, pipeline):
        """Test processing patient with actual file creation."""
        result = pipeline.process_patient("1", dry_run=False)
        
        assert result['status'] in ['completed', 'partial']
        assert result['patient_id'] == "1"
        
        # Check that output files were created
        output_patient_dir = pipeline.output_dir / "1"
        assert output_patient_dir.exists()
        assert (output_patient_dir / "profile.json").exists()
        
        # Check for JSON output files
        json_files = list(output_patient_dir.glob("*.json"))
        # Should have at least profile.json
        assert len(json_files) >= 1

    def test_process_all_patients_dry_run(self, pipeline):
        """Test processing all patients in dry run mode."""
        result = pipeline.process_all_patients(dry_run=True)
        
        assert result['status'] == 'completed'
        assert result['dry_run'] is True
        assert 'summary' in result
        assert result['summary']['total_patients'] >= 1

    def test_process_all_patients_live(self, pipeline):
        """Test processing all patients with actual file creation."""
        result = pipeline.process_all_patients(dry_run=False)
        
        assert result['status'] == 'completed'
        assert result['dry_run'] is False
        assert 'summary' in result
        
        # Check that summary file was created
        summary_file = pipeline.output_dir / 'metadata' / 'processing_summary.json'
        assert summary_file.exists()
        
        # Load and validate summary
        with open(summary_file, 'r') as f:
            summary_data = json.load(f)
        assert summary_data['status'] == 'completed'
        assert 'statistics' in summary_data

    def test_process_specific_patient(self, pipeline):
        """Test processing specific patient filter."""
        result = pipeline.process_all_patients(dry_run=False, patient_filter="1")
        
        assert result['status'] == 'completed'
        assert 'patient_results' in result
        assert '1' in result['patient_results']

    def test_process_nonexistent_patient(self, pipeline):
        """Test processing nonexistent patient."""
        result = pipeline.process_all_patients(dry_run=False, patient_filter="999")
        
        assert result['status'] == 'error'
        assert 'Patient 999 not found' in result['message']

    def test_error_handling_invalid_xml(self, pipeline, temp_source_dir):
        """Test error handling with invalid XML."""
        patient_dir = Path(temp_source_dir) / "1"
        
        # Create invalid XML file
        invalid_xml = patient_dir / "invalid.xml"
        with open(invalid_xml, "w") as f:
            f.write("This is not valid XML content")
        
        result = pipeline.process_xml_file(invalid_xml, 'shafafiya')
        assert result is None  # Should return None for failed processing

    def test_copy_metadata_files(self, pipeline, temp_source_dir):
        """Test copying metadata files."""
        source_patient_dir = Path(temp_source_dir) / "1"
        output_patient_dir = pipeline.output_dir / "1"
        output_patient_dir.mkdir(parents=True, exist_ok=True)
        
        pipeline.copy_metadata_files(source_patient_dir, output_patient_dir)
        
        assert (output_patient_dir / "profile.json").exists()

    def test_statistics_tracking(self, pipeline):
        """Test that statistics are properly tracked."""
        # Process a patient
        pipeline.process_all_patients(dry_run=False, patient_filter="1")
        
        # Check statistics
        assert pipeline.stats['total_patients'] >= 0
        assert pipeline.stats['start_time'] is not None
        assert pipeline.stats['end_time'] is not None


class TestDataPipelineIntegration:
    """Integration tests with real synthetic data."""

    def test_with_real_synthetic_data(self):
        """Test pipeline with actual synthetic dataset (if available)."""
        project_root = Path(__file__).parent.parent.parent
        synthetic_dir = project_root / "data" / "synthetic_dataset"
        
        if not synthetic_dir.exists():
            pytest.skip("Synthetic dataset not available")
        
        # Use a temporary output directory
        with tempfile.TemporaryDirectory() as temp_output:
            pipeline = DataPipeline(
                source_dir=str(synthetic_dir),
                output_dir=temp_output,
                enable_validation=False
            )
            
            # Test dry run with first patient
            result = pipeline.process_all_patients(dry_run=True, patient_filter="1")
            
            if result['status'] == 'completed':
                assert result['summary']['total_patients'] == 1
                assert '1' in result['patient_results']