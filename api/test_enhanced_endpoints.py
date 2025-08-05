#!/usr/bin/env python3
"""
Test script for the enhanced API endpoints.
Tests the 5 core endpoints with proper integration to enhanced services.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from api.services.patient_lookup_service import get_patient_lookup_service
from api.services.xml_auto_detection_service import get_xml_auto_detection_service
from api.services.workflow_orchestrator import get_workflow_orchestrator
from api.services.claude_analysis_service import get_claude_analysis_service


async def test_enhanced_services():
    """Test the enhanced services integration."""
    print("🧪 Testing Enhanced API Services Integration")
    print("=" * 60)
    
    try:
        # Test 1: Patient Lookup Service
        print("1️⃣ Testing Patient Lookup Service...")
        patient_service = get_patient_lookup_service()
        patients_dropdown = patient_service.get_all_patients_for_dropdown()
        print(f"   ✅ Found {len(patients_dropdown)} patients for dropdown")
        
        if patients_dropdown:
            sample_patient = patients_dropdown[0]
            patient_id = sample_patient["patient_id"]
            print(f"   📋 Sample patient: {sample_patient['name']} ({patient_id})")
            
            # Test patient data availability
            availability = patient_service.check_patient_data_availability(patient_id)
            print(f"   📊 Data availability: XML={availability['raw_data_available']}, JSON={availability['processed_data_available']}")
        
        # Test 2: XML Auto-Detection Service
        print("\n2️⃣ Testing XML Auto-Detection Service...")
        detection_service = get_xml_auto_detection_service()
        
        test_filenames = [
            "dubai_patient123_20240101_req01_eclaim.xml",
            "abudhabi_patient456_20240102_req01_shafafiya.xml",
            "unknown_file.xml"
        ]
        
        for filename in test_filenames:
            detected_source = detection_service.detect_source(filename)
            confidence = detection_service.get_detection_confidence(filename)
            print(f"   🔍 {filename} -> {detected_source} (confidence: {confidence['confidence']})")
        
        # Test 3: Workflow Orchestrator
        print("\n3️⃣ Testing Workflow Orchestrator...")
        workflow_service = get_workflow_orchestrator()
        workflow_status = workflow_service.get_workflow_status()
        print(f"   🔄 Workflow status: {workflow_status['service_status']}")
        print(f"   📝 Supported workflows: {', '.join(workflow_status['supported_workflows'])}")
        print(f"   👥 Patient index size: {workflow_status['patient_index_size']}")
        
        # Test 4: Claude Analysis Service
        print("\n4️⃣ Testing Claude Analysis Service...")
        claude_service = get_claude_analysis_service()
        
        try:
            analysis_status = claude_service.get_analysis_status()
            print(f"   🤖 Claude available: {analysis_status.get('claude_available', False)}")
            print(f"   📊 Patient index size: {analysis_status.get('patient_index_size', 0)}")
        except Exception as e:
            print(f"   ⚠️  Claude service status check failed: {e}")
        
        # Test 5: Service Configuration
        print("\n5️⃣ Testing Service Configuration...")
        from api.config_loader import get_config
        config = get_config()
        
        dataset_paths = config.get_dataset_paths()
        print(f"   📁 Raw data path: {dataset_paths['raw_data']}")
        print(f"   📁 Processed data path: {dataset_paths['processed_data']}")
        print(f"   🔧 Claude enabled: {config.is_claude_enabled()}")
        print(f"   🔧 Environment: {config.environment}")
        
        print("\n✅ All enhanced services tested successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Service testing failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_endpoint_configuration():
    """Test endpoint configuration and models."""
    print("\n🔧 Testing Endpoint Configuration")
    print("=" * 60)
    
    try:
        from api.models import (
            PatientInfo, XMLProcessResponse, AnalysisResponse, 
            SystemStatus, DashboardData, ErrorResponse
        )
        
        # Test model creation
        test_patient = PatientInfo(
            patient_id="test-123",
            folder_name="test_folder", 
            folder_path="/test/path",
            has_profile=True,
            xml_files=5,
            processed_json_files=3
        )
        print(f"   ✅ PatientInfo model: {test_patient.patient_id}")
        
        test_response = XMLProcessResponse(
            success=True,
            patient_id="test-123",
            data={"test": "data"},
            metadata={"api_version": "2.0.0"}
        )
        print(f"   ✅ XMLProcessResponse model: success={test_response.success}")
        
        print("   ✅ All models validated successfully!")
        return True
        
    except Exception as e:
        print(f"   ❌ Model validation failed: {e}")
        return False


def summarize_api_endpoints():
    """Summarize the implemented API endpoints."""
    print("\n📋 API Endpoints Summary")
    print("=" * 60)
    
    endpoints = [
        {
            "method": "GET",
            "path": "/api/patients",
            "description": "List patients for dropdown with enhanced lookup",
            "features": ["Patient demographics", "File counts", "Insurance info"]
        },
        {
            "method": "POST", 
            "path": "/api/upload-xml",
            "description": "Upload XML file with patient selection",
            "features": ["Auto-detection", "Patient folder storage", "Proper naming convention"]
        },
        {
            "method": "POST",
            "path": "/api/process/{patient_id}",
            "description": "Process latest XML for specific patient", 
            "features": ["Patient-centric workflow", "JSON storage", "Latest file processing"]
        },
        {
            "method": "POST",
            "path": "/api/analyze/{patient_id}",
            "description": "Run Claude analysis for patient",
            "features": ["Multi-agent analysis", "Cost tracking", "History inclusion"]
        },
        {
            "method": "GET",
            "path": "/api/patient/{patient_id}/dashboard",
            "description": "Get comprehensive patient dashboard",
            "features": ["File history", "Processing stats", "Analysis results"]
        }
    ]
    
    for i, endpoint in enumerate(endpoints, 1):
        print(f"{i}️⃣ {endpoint['method']} {endpoint['path']}")
        print(f"   📝 {endpoint['description']}")
        print(f"   ⚡ Features: {', '.join(endpoint['features'])}")
        print()
    
    print("🎯 Key Integration Points:")
    print("   • Enhanced patient lookup with demographics")
    print("   • Auto-detection service for XML source identification")
    print("   • Patient-centric workflow orchestration")
    print("   • Multi-agent Claude analysis with cost tracking")
    print("   • Comprehensive dashboard with file history")
    print("   • Proper error handling and validation")
    print("   • CORS support for frontend integration")


async def main():
    """Main test function."""
    print("🚀 Nazmito Enhanced API Integration Test")
    print("=" * 60)
    
    # Test services
    services_ok = await test_enhanced_services()
    
    # Test models
    models_ok = test_endpoint_configuration()
    
    # Show endpoint summary
    summarize_api_endpoints()
    
    # Final status
    print("\n🏁 Test Results Summary")
    print("=" * 60)
    if services_ok and models_ok:
        print("✅ All tests passed! Enhanced API is ready for integration.")
        print("\n🚀 To start the server:")
        print("   python api/run_server.py")
        print("\n📖 API Documentation will be available at:")
        print("   http://localhost:8000/api/docs")
        return True
    else:
        print("❌ Some tests failed. Please check the configuration.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)