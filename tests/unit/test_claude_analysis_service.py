#!/usr/bin/env python3
"""
Unit tests for ClaudeAnalysisService.

Tests the Claude analysis service for patient pre-authorization analysis,
including multi-agent workflow and cost management.
"""

import json
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List

import pytest

from api.services.claude_analysis_service import get_claude_analysis_service, ClaudeAnalysisService


class TestClaudeAnalysisService:
    """Test suite for ClaudeAnalysisService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = ClaudeAnalysisService()
        self.sample_patient_id = "patient-test-123"
        self.sample_bundle = {
            "resourceType": "Bundle",
            "id": "test-bundle",
            "authorization_id": "AUTH-123",
            "fhir_resources": {
                "claim-1": {
                    "resourceType": "Claim",
                    "diagnosis": [{"code": "E11.9", "display": "Type 2 diabetes"}],
                    "item": [{"productOrService": {"code": "83036", "display": "HbA1c test"}}]
                }
            },
            "raw_data": {
                "JustificationText": "Patient with diabetes needs HbA1c monitoring"
            }
        }
        
    @pytest.fixture
    def mock_claude_client(self):
        """Mock Claude client for testing."""
        with patch('api.services.claude_analysis_service.anthropic') as mock_anthropic:
            mock_client = Mock()
            mock_message = Mock()
            mock_message.content = [
                Mock(text=json.dumps({
                    "summary": "Patient requires HbA1c test for diabetes monitoring",
                    "recommendations": ["Approve test", "Schedule follow-up"],
                    "confidence_score": 0.85,
                    "approval_recommendation": "APPROVE"
                }))
            ]
            mock_message.usage.input_tokens = 1000
            mock_message.usage.output_tokens = 500
            
            mock_client.messages.create = AsyncMock(return_value=mock_message)
            mock_anthropic.AsyncAnthropic.return_value = mock_client
            
            yield mock_client
    
    def test_claude_available_with_api_key(self):
        """Test Claude availability when API key is configured."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            service = ClaudeAnalysisService()
            assert service.claude_available is True
    
    def test_claude_unavailable_without_api_key(self):
        """Test Claude unavailability when API key is missing."""
        with patch.dict('os.environ', {}, clear=True):
            service = ClaudeAnalysisService()
            assert service.claude_available is False
    
    @pytest.mark.asyncio
    async def test_analyze_patient_data_success(self, mock_claude_client):
        """Test successful patient data analysis."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            service = ClaudeAnalysisService()
            
            result = await service.analyze_patient_data(
                patient_id=self.sample_patient_id,
                patient_bundles=[self.sample_bundle],
                cost_limit_usd=2.0
            )
            
            assert result["success"] is True
            assert result["patient_id"] == self.sample_patient_id
            assert "analysis" in result
            assert "cost_usd" in result
            assert result["cost_usd"] > 0  # Should have some cost
            
            # Verify Claude client was called
            mock_claude_client.messages.create.assert_called()
    
    @pytest.mark.asyncio
    async def test_analyze_patient_data_claude_unavailable(self):
        """Test analysis failure when Claude is unavailable."""
        with patch.dict('os.environ', {}, clear=True):
            service = ClaudeAnalysisService()
            
            result = await service.analyze_patient_data(
                patient_id=self.sample_patient_id,
                patient_bundles=[self.sample_bundle],
                cost_limit_usd=2.0
            )
            
            assert result["success"] is False
            assert "Claude analysis service is not available" in result["error"]
    
    @pytest.mark.asyncio
    async def test_analyze_patient_data_empty_bundles(self, mock_claude_client):
        """Test analysis with empty patient bundles."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            service = ClaudeAnalysisService()
            
            result = await service.analyze_patient_data(
                patient_id=self.sample_patient_id,
                patient_bundles=[],
                cost_limit_usd=2.0
            )
            
            assert result["success"] is False
            assert "No patient data provided" in result["error"]
    
    @pytest.mark.asyncio
    async def test_analyze_patient_data_cost_estimation(self, mock_claude_client):
        """Test cost estimation and tracking."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            service = ClaudeAnalysisService()
            
            # Mock token usage for cost calculation
            mock_claude_client.messages.create.return_value.usage.input_tokens = 2000
            mock_claude_client.messages.create.return_value.usage.output_tokens = 1000
            
            result = await service.analyze_patient_data(
                patient_id=self.sample_patient_id,
                patient_bundles=[self.sample_bundle],
                cost_limit_usd=5.0
            )
            
            assert result["success"] is True
            assert "cost_usd" in result
            assert isinstance(result["cost_usd"], float)
            assert result["cost_usd"] > 0
    
    @pytest.mark.asyncio
    async def test_analyze_patient_data_cost_limit_exceeded(self, mock_claude_client):
        """Test behavior when cost limit is exceeded."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            service = ClaudeAnalysisService()
            
            # Mock very high token usage
            mock_claude_client.messages.create.return_value.usage.input_tokens = 50000
            mock_claude_client.messages.create.return_value.usage.output_tokens = 25000
            
            result = await service.analyze_patient_data(
                patient_id=self.sample_patient_id,
                patient_bundles=[self.sample_bundle],
                cost_limit_usd=0.10  # Very low limit
            )
            
            # Should still succeed but track high cost
            assert "cost_usd" in result
    
    @pytest.mark.asyncio
    async def test_multi_agent_analysis_workflow(self, mock_claude_client):
        """Test multi-agent analysis workflow."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            service = ClaudeAnalysisService()
            
            # Mock different responses for different agents
            responses = [
                # Clinical analyzer response
                Mock(content=[Mock(text=json.dumps({
                    "clinical_summary": "Diabetes management case",
                    "key_findings": ["HbA1c test requested", "Diabetes diagnosis present"]
                }))], usage=Mock(input_tokens=1000, output_tokens=500)),
                
                # Medical reviewer response
                Mock(content=[Mock(text=json.dumps({
                    "medical_necessity": "HIGH",
                    "approval_recommendation": "APPROVE",
                    "confidence_score": 0.90
                }))], usage=Mock(input_tokens=1200, output_tokens=400)),
                
                # Recommendation agent response
                Mock(content=[Mock(text=json.dumps({
                    "recommendations": ["Approve HbA1c test", "Schedule 3-month follow-up"],
                    "priority": "HIGH"
                }))], usage=Mock(input_tokens=800, output_tokens=300))
            ]
            
            mock_claude_client.messages.create.side_effect = responses
            
            result = await service.analyze_patient_data(
                patient_id=self.sample_patient_id,
                patient_bundles=[self.sample_bundle],
                cost_limit_usd=5.0,
                enable_multi_agent=True
            )
            
            assert result["success"] is True
            assert "agent_results" in result["analysis"]
            assert len(result["analysis"]["agent_results"]) > 1
            
            # Verify multiple Claude calls were made
            assert mock_claude_client.messages.create.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_analyze_patient_data_api_error(self, mock_claude_client):
        """Test handling of Claude API errors."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            service = ClaudeAnalysisService()
            
            # Mock API error
            mock_claude_client.messages.create.side_effect = Exception("API rate limit exceeded")
            
            result = await service.analyze_patient_data(
                patient_id=self.sample_patient_id,
                patient_bundles=[self.sample_bundle],
                cost_limit_usd=2.0
            )
            
            assert result["success"] is False
            assert "API rate limit exceeded" in result["error"]
    
    def test_get_analysis_status(self):
        """Test analysis service status retrieval."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            service = ClaudeAnalysisService()
            
            status = service.get_analysis_status()
            
            assert "claude_available" in status
            assert "patient_index_size" in status
            assert "total_analyses_completed" in status
            assert status["claude_available"] is True
    
    def test_estimate_analysis_cost(self):
        """Test cost estimation for analysis."""
        service = ClaudeAnalysisService()
        
        # Test with sample bundle
        estimated_cost = service.estimate_analysis_cost([self.sample_bundle])
        
        assert isinstance(estimated_cost, float)
        assert estimated_cost > 0
        assert estimated_cost < 1.0  # Should be reasonable for one bundle
    
    def test_estimate_analysis_cost_multiple_bundles(self):
        """Test cost estimation with multiple bundles."""
        service = ClaudeAnalysisService()
        
        # Test with multiple bundles
        multiple_bundles = [self.sample_bundle] * 5
        estimated_cost = service.estimate_analysis_cost(multiple_bundles)
        
        single_cost = service.estimate_analysis_cost([self.sample_bundle])
        
        # Multiple bundles should cost more
        assert estimated_cost > single_cost
        assert estimated_cost < single_cost * 10  # But not linearly more due to efficiency
    
    def test_extract_clinical_context(self):
        """Test extraction of clinical context from bundles."""
        service = ClaudeAnalysisService()
        
        context = service.extract_clinical_context([self.sample_bundle])
        
        assert "diagnosis_codes" in context
        assert "procedure_codes" in context
        assert "clinical_text" in context
        assert "patient_summary" in context
        
        # Should extract diagnosis and procedure codes
        assert "E11.9" in context["diagnosis_codes"]
        assert "83036" in context["procedure_codes"]
        assert "diabetes" in context["clinical_text"].lower()
    
    def test_format_analysis_prompt(self):
        """Test formatting of analysis prompt for Claude."""
        service = ClaudeAnalysisService()
        
        clinical_context = {
            "diagnosis_codes": ["E11.9"],
            "procedure_codes": ["83036"],
            "clinical_text": "Patient with diabetes needs HbA1c monitoring",
            "patient_summary": "Type 2 diabetes patient"
        }
        
        prompt = service.format_analysis_prompt(
            patient_id=self.sample_patient_id,
            clinical_context=clinical_context,
            agent_role="clinical_analyzer"
        )
        
        assert self.sample_patient_id in prompt
        assert "E11.9" in prompt
        assert "83036" in prompt
        assert "diabetes" in prompt.lower()
        assert "clinical_analyzer" in prompt.lower()
    
    @pytest.mark.asyncio
    async def test_analyze_with_history_context(self, mock_claude_client):
        """Test analysis with patient history context."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            service = ClaudeAnalysisService()
            
            # Create historical bundle
            historical_bundle = {
                "resourceType": "Bundle",
                "id": "historical-bundle",
                "authorization_id": "AUTH-HIST",
                "fhir_resources": {
                    "claim-hist": {
                        "resourceType": "Claim",
                        "diagnosis": [{"code": "E11.9", "display": "Type 2 diabetes"}]
                    }
                },
                "raw_data": {
                    "JustificationText": "Previous diabetes monitoring"
                }
            }
            
            result = await service.analyze_patient_data(
                patient_id=self.sample_patient_id,
                patient_bundles=[self.sample_bundle, historical_bundle],
                cost_limit_usd=3.0,
                include_history=True
            )
            
            assert result["success"] is True
            
            # Verify the prompt included historical context
            call_args = mock_claude_client.messages.create.call_args
            prompt_content = str(call_args)
            assert "historical" in prompt_content.lower() or "previous" in prompt_content.lower()


def test_get_claude_analysis_service_singleton():
    """Test that get_claude_analysis_service returns singleton instance."""
    service1 = get_claude_analysis_service()
    service2 = get_claude_analysis_service()
    
    assert service1 is service2
    assert isinstance(service1, ClaudeAnalysisService)
