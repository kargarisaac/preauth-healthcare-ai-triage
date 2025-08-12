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

from preauth_system.orchestrator import process_preauth_request


class XMLProcessingService:
    """Modern XML processing service using async orchestrator."""
    
    def __init__(self):
        self.processed_count = 0
        logger.info("XMLProcessingService initialized with async orchestrator")
    
    async def process_xml(self, xml_content: bytes, filename: str) -> Dict[str, Any]:
        """Process XML content using the async orchestrator workflow."""
        try:
            # Save XML to temporary file for processing
            with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False, encoding='utf-8') as temp_file:
                xml_string = xml_content.decode('utf-8')
                temp_file.write(xml_string)
                temp_file_path = temp_file.name
            
            try:
                # Determine XML format (simple detection)
                xml_format = "eclaim" if "eclaimlink" in xml_string.lower() else "shafafiya"
                
                # Create initial state for async workflow
                initial_state = {
                    "xml_file_path": temp_file_path,
                    "xml_format": xml_format,
                    "processing_mode": "hybrid",
                    "cost_tracking": {
                        "processing_start": datetime.now().isoformat(),
                        "processing_end": None,
                        "total_processing_time": None,
                        "token_usage_by_agent": {},
                        "total_cost_usd": 0.0,
                        "cost_optimization_notes": [],
                    },
                }
                
                # Run the async workflow
                logger.info(f"Processing XML file: {filename} (format: {xml_format})")
                final_state = await process_preauth_request(initial_state)
                
                self.processed_count += 1
                
                # Extract results
                workflow_complete = final_state.get("workflow_control", {}).get("workflow_complete", False)
                result = {
                    "success": workflow_complete,
                    "filename": filename,
                    "format": xml_format,
                    "processing_time": final_state.get("cost_tracking", {}).get("total_processing_time"),
                    "final_decision": final_state.get("final_decision"),
                    "workflow_complete": workflow_complete,
                    "agent_results": final_state.get("agent_results", {}),
                    "cost_tracking": final_state.get("cost_tracking", {}),
                    "processed_count": self.processed_count,
                    "timestamp": datetime.now().isoformat(),
                }
                
                if workflow_complete:
                    decision_text = result.get('final_decision', {}).get('decision', 'No decision') if result.get('final_decision') else 'No decision'
                    logger.info(f"Successfully processed {filename}: {decision_text}")
                else:
                    errors = final_state.get("workflow_control", {}).get("errors", [])
                    logger.error(f"Workflow failed for {filename}: {'; '.join(errors)}")
                    result["error"] = "; ".join(errors) if errors else "Unknown workflow error"
                
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
            "service_type": "Async Orchestrator",
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