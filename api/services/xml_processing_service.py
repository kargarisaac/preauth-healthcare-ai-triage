#!/usr/bin/env python3
"""
Modern XML Processing Service for Nazmito API.
Uses the async orchestrator for workflow processing.
"""

from typing import Dict, Any
from datetime import datetime
from fastapi import HTTPException
from loguru import logger
import tempfile
import os

from preauth_system.pipeline_module import PreAuthPipeline


class XMLProcessingService:
    """Modern XML processing service using pipeline."""
    
    def __init__(self):
        self.processed_count = 0
        self.pipeline = PreAuthPipeline()
        logger.info("XMLProcessingService initialized with PreAuthPipeline")
    
    async def process_xml(self, xml_content: bytes, filename: str) -> Dict[str, Any]:
        """Process XML content using the pipeline workflow."""
        try:
            # Save XML to temporary file for processing
            with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False, encoding='utf-8') as temp_file:
                xml_string = xml_content.decode('utf-8')
                temp_file.write(xml_string)
                temp_file_path = temp_file.name
            
            try:
                # Determine XML format (simple detection)
                xml_format = "eclaim" if "eclaimlink" in xml_string.lower() else "shafafiya"
                
                # Run the pipeline
                logger.info(f"Processing XML file: {filename} (format: {xml_format})")
                pipeline_result = self.pipeline.forward(xml_path=temp_file_path, xml_format=xml_format)
                
                self.processed_count += 1
                
                # Extract decision and timing data
                decision_data = pipeline_result.get("decision", {})
                timings = pipeline_result.get("timings", {})
                cost_data = pipeline_result.get("cost", {})
                
                # Map pipeline decision to service format
                decision_mapping = {
                    "APPROVE": "APPROVED",
                    "DENY": "DENIED", 
                    "REVIEW": "REQUIRES_REVIEW"
                }
                
                mapped_decision = decision_mapping.get(decision_data.get("outcome", "REVIEW"), "REQUIRES_REVIEW")
                
                result = {
                    "success": True,
                    "filename": filename,
                    "format": xml_format,
                    "processing_time": timings.get("total_ms", 0) / 1000,  # Convert to seconds
                    "final_decision": {
                        "decision": mapped_decision,
                        "confidence": decision_data.get("confidence", 0.0),
                        "rationale": decision_data.get("rationale", ""),
                        "conditions": decision_data.get("conditions", [])
                    },
                    "workflow_complete": True,
                    "agent_results": {
                        "pipeline": {
                            "status": "completed",
                            "success": True,
                            "processing_time": timings.get("total_ms", 0) / 1000,
                            "response": "Pipeline execution completed successfully"
                        }
                    },
                    "cost_tracking": {
                        "processing_start": datetime.now().isoformat(),
                        "processing_end": datetime.now().isoformat(),
                        "total_processing_time": timings.get("total_ms", 0) / 1000,
                        "token_usage_by_agent": cost_data.get("tokens", {}),
                        "total_cost_usd": cost_data.get("total_cost_usd", 0.0),
                        "cost_optimization_notes": ["Using optimized pipeline execution"],
                    },
                    "processed_count": self.processed_count,
                    "timestamp": datetime.now().isoformat(),
                    "pipeline_details": {
                        "timings": timings,
                        "evidence_count": len(pipeline_result.get("evidence", [])),
                        "criteria_evaluated": len(pipeline_result.get("checklist", {}).get("criteria", [])),
                        "compliance_score": pipeline_result.get("checklist", {}).get("overall_compliance_score", 0.0)
                    }
                }
                
                logger.info(f"Successfully processed {filename}: {mapped_decision}")
                return result
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
            
        except Exception as e:
            logger.error(f"Failed to process XML {filename}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"XML processing failed: {str(e)}"
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return {
            "processed_count": self.processed_count,
            "service_type": "PreAuth Pipeline",
            "status": "active"
        }


# Singleton pattern for service instance
_xml_processing_service_instance = None

def get_xml_processing_service() -> XMLProcessingService:
    """Get or create the XML processing service instance."""
    global _xml_processing_service_instance
    if _xml_processing_service_instance is None:
        _xml_processing_service_instance = XMLProcessingService()
    return _xml_processing_service_instance