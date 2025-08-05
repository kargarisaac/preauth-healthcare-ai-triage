#!/usr/bin/env python3
"""
Unit tests for WorkflowOrchestrator service.

Tests the patient-centric workflow orchestration, including XML processing
and Claude analysis integration.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

import pytest

from api.services.workflow_orchestrator import get_workflow_orchestrator, WorkflowOrchestrator


class TestWorkflowOrchestrator:
    """Test suite for WorkflowOrchestrator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.orchestrator = WorkflowOrchestrator()
        self.sample_patient_id = "patient-test-123"
        self.sample_bundle = {
            "resourceType": "Bundle",
            "id": "test-bundle",
            "authorization_id": self.sample_patient_id,
            "fhir_resources": {},
            "raw_data": {"patient_id": self.sample_patient_id}
        }
    
    @pytest.fixture
    def mock_services(self):
        """Mock all dependent services."""
        with patch('api.services.workflow_orchestrator.get_patient_lookup_service') as mock_patient, \
             patch('api.services.workflow_orchestrator.get_xml_processing_service') as mock_xml, \
             patch('api.services.workflow_orchestrator.get_claude_analysis_service') as mock_claude:
            
            # Mock patient lookup service
            mock_patient_service = Mock()
            mock_patient_service.find_patient_folder.return_value = Path("/test/patient/123")
            mock_patient_service.get_patient_history.return_value = []
            mock_patient_service.extract_patient_id_from_bundle.return_value = self.sample_patient_id
            mock_patient_service.create_patient_folders.return_value = {
                "patient_id": self.sample_patient_id,
                "raw_data_path": "/test/raw",
                "processed_data_path": "/test/processed"
            }
            mock_patient.return_value = mock_patient_service
            
            # Mock XML processing service
            mock_xml_service = Mock()
            mock_xml_service.process_xml_file = AsyncMock(return_value={
                "success": True,
                "bundle": self.sample_bundle,
                "patient_id": self.sample_patient_id
            })
            mock_xml.return_value = mock_xml_service
            
            # Mock Claude analysis service
            mock_claude_service = Mock()
            mock_claude_service.analyze_patient_data = AsyncMock(return_value={
                "success": True,
                "analysis": {"summary": "Test analysis"},
                "cost_usd": 0.50
            })
            mock_claude_service.claude_available = True
            mock_claude.return_value = mock_claude_service
            
            yield {
                "patient": mock_patient_service,
                "xml": mock_xml_service,
                "claude": mock_claude_service
            }
    
    @pytest.mark.asyncio
    async def test_process_new_patient_upload_success(self, mock_services, temp_xml_file):
        """Test successful processing of new patient XML upload."""
        # Create test XML file
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <PriorAuthorizationRequest>
            <Header>
                <SenderID>TEST123</SenderID>
                <TransactionID>TXN-001</TransactionID>
            </Header>
        </PriorAuthorizationRequest>"""
        xml_file = temp_xml_file(xml_content)
        
        # Create mock UploadFile
        mock_file = Mock()
        mock_file.filename = "test.xml"
        mock_file.file.read.return_value = xml_content.encode()
        
        # Test the workflow
        result = await self.orchestrator.process_new_patient_upload(
            file=mock_file,
            source="eclaim",
            patient_id=self.sample_patient_id
        )
        
        # Verify result
        assert result["success"] is True
        assert result["patient_id"] == self.sample_patient_id
        assert "bundle" in result
        assert "file_metadata" in result
        
        # Verify service calls
        mock_services["xml"].process_xml_file.assert_called_once()
        mock_services["patient"].extract_patient_id_from_bundle.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_new_patient_upload_xml_processing_failure(self, mock_services, temp_xml_file):
        """Test handling of XML processing failure."""
        # Mock XML processing failure
        mock_services["xml"].process_xml_file.return_value = {
            "success": False,
            "error": "Invalid XML format"
        }
        
        xml_content = "<invalid>xml</invalid>"
        xml_file = temp_xml_file(xml_content)
        
        mock_file = Mock()
        mock_file.filename = "invalid.xml"
        mock_file.file.read.return_value = xml_content.encode()
        
        result = await self.orchestrator.process_new_patient_upload(
            file=mock_file,
            source="eclaim",
            patient_id=self.sample_patient_id
        )
        
        assert result["success"] is False
        assert "Invalid XML format" in result["error"]
    
    @pytest.mark.asyncio
    async def test_analyze_existing_patient_success(self, mock_services):
        """Test successful Claude analysis of existing patient."""
        # Mock patient data availability
        mock_services["patient"].get_patient_history.return_value = [self.sample_bundle]
        
        result = await self.orchestrator.analyze_existing_patient(
            patient_id=self.sample_patient_id,
            cost_limit_usd=1.0
        )
        
        assert result["success"] is True
        assert result["patient_id"] == self.sample_patient_id
        assert "claude_analysis" in result
        assert result["claude_analysis"]["cost_usd"] == 0.50
        
        # Verify Claude service was called
        mock_services["claude"].analyze_patient_data.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_existing_patient_no_data(self, mock_services):
        """Test analysis failure when patient has no data."""
        # Mock no patient history
        mock_services["patient"].get_patient_history.return_value = []
        
        result = await self.orchestrator.analyze_existing_patient(
            patient_id=self.sample_patient_id,
            cost_limit_usd=1.0
        )
        
        assert result["success"] is False
        assert "No processed data found" in result["error"]
        mock_services["claude"].analyze_patient_data.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_analyze_existing_patient_cost_limit_exceeded(self, mock_services):
        """Test analysis stops when cost limit is exceeded."""
        # Mock high-cost analysis
        mock_services["claude"].analyze_patient_data.return_value = {
            "success": False,
            "error": "Cost limit exceeded",
            "cost_usd": 2.0
        }
        mock_services["patient"].get_patient_history.return_value = [self.sample_bundle]
        
        result = await self.orchestrator.analyze_existing_patient(
            patient_id=self.sample_patient_id,
            cost_limit_usd=1.0
        )
        
        assert result["success"] is False
        assert "Cost limit exceeded" in result["error"]
    
    @pytest.mark.asyncio
    async def test_analyze_existing_patient_claude_unavailable(self, mock_services):
        """Test analysis failure when Claude service is unavailable."""
        # Mock Claude unavailable
        mock_services["claude"].claude_available = False
        mock_services["patient"].get_patient_history.return_value = [self.sample_bundle]
        
        result = await self.orchestrator.analyze_existing_patient(
            patient_id=self.sample_patient_id,
            cost_limit_usd=1.0
        )
        
        assert result["success"] is False
        assert "Claude analysis service is not available" in result["error"]
        mock_services["claude"].analyze_patient_data.assert_not_called()
    
    def test_get_workflow_statistics(self, mock_services):
        """Test retrieval of workflow statistics."""
        stats = self.orchestrator.get_workflow_statistics()
        
        assert "total_patients_processed" in stats
        assert "total_analyses_completed" in stats
        assert "average_processing_time" in stats
        assert "success_rate" in stats
        assert isinstance(stats["total_patients_processed"], int)
    
    def test_validate_upload_parameters_valid(self):
        """Test validation of valid upload parameters."""
        mock_file = Mock()
        mock_file.filename = "test.xml"
        mock_file.size = 1024 * 1024  # 1MB
        
        # Should not raise any exception
        self.orchestrator.validate_upload_parameters(
            file=mock_file,
            source="eclaim",
            patient_id=self.sample_patient_id
        )
    
    def test_validate_upload_parameters_invalid_source(self):
        """Test validation failure for invalid source."""
        mock_file = Mock()
        mock_file.filename = "test.xml"
        mock_file.size = 1024 * 1024
        
        with pytest.raises(ValueError, match="Invalid source"):
            self.orchestrator.validate_upload_parameters(
                file=mock_file,
                source="invalid_source",
                patient_id=self.sample_patient_id
            )
    
    def test_validate_upload_parameters_invalid_file_extension(self):
        """Test validation failure for invalid file extension."""
        mock_file = Mock()
        mock_file.filename = "test.txt"
        mock_file.size = 1024 * 1024
        
        with pytest.raises(ValueError, match="Invalid file type"):
            self.orchestrator.validate_upload_parameters(
                file=mock_file,
                source="eclaim",
                patient_id=self.sample_patient_id
            )
    
    def test_validate_upload_parameters_file_too_large(self):
        """Test validation failure for file size limit."""
        mock_file = Mock()
        mock_file.filename = "test.xml"
        mock_file.size = 20 * 1024 * 1024  # 20MB
        
        with pytest.raises(ValueError, match="File too large"):
            self.orchestrator.validate_upload_parameters(
                file=mock_file,
                source="eclaim",
                patient_id=self.sample_patient_id
            )
    
    @pytest.mark.asyncio
    async def test_complete_patient_workflow_integration(self, mock_services, temp_xml_file):
        """Test complete workflow from upload to analysis."""
        # Create test XML
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <PriorAuthorizationRequest>
            <Header>
                <SenderID>TEST123</SenderID>
                <TransactionID>TXN-001</TransactionID>
            </Header>
            <JustificationText>Patient with diabetes needs HbA1c test.</JustificationText>
        </PriorAuthorizationRequest>"""
        
        mock_file = Mock()
        mock_file.filename = "complete_test.xml"
        mock_file.file.read.return_value = xml_content.encode()
        
        # Step 1: Process upload
        upload_result = await self.orchestrator.process_new_patient_upload(
            file=mock_file,
            source="eclaim",
            patient_id=self.sample_patient_id
        )
        
        assert upload_result["success"] is True
        extracted_patient_id = upload_result["patient_id"]
        
        # Step 2: Analyze patient (mock that we now have history)
        mock_services["patient"].get_patient_history.return_value = [upload_result["bundle"]]
        
        analysis_result = await self.orchestrator.analyze_existing_patient(
            patient_id=extracted_patient_id,
            cost_limit_usd=2.0
        )
        
        assert analysis_result["success"] is True
        assert analysis_result["patient_id"] == extracted_patient_id
        assert "claude_analysis" in analysis_result
        
        # Verify both services were called
        mock_services["xml"].process_xml_file.assert_called_once()
        mock_services["claude"].analyze_patient_data.assert_called_once()


def test_get_workflow_orchestrator_singleton():
    """Test that get_workflow_orchestrator returns singleton instance."""
    orchestrator1 = get_workflow_orchestrator()
    orchestrator2 = get_workflow_orchestrator()
    
    assert orchestrator1 is orchestrator2
    assert isinstance(orchestrator1, WorkflowOrchestrator)
