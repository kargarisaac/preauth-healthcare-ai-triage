#!/usr/bin/env python3
"""
Integration Test Setup Validation

Quick validation script to ensure all integration test components
are properly configured and working.
"""

import sys
import traceback
from pathlib import Path


def validate_demo_files():
    """Validate demo XML files are available."""
    print("🔍 Validating demo files...")
    
    demo_dir = Path("data/dataset_2/synthetic_dataset/UAE_XML")
    if not demo_dir.exists():
        print(f"❌ Demo directory not found: {demo_dir}")
        return False
    
    required_files = ["Patient_007_eclaim.xml", "Patient_005_eclaim.xml", "Patient_011_eclaim.xml"]
    found_files = []
    
    for filename in required_files:
        file_path = demo_dir / filename
        if file_path.exists():
            found_files.append(filename)
            print(f"✅ Found: {filename}")
        else:
            print(f"⚠️  Missing: {filename}")
    
    if len(found_files) >= 1:
        print(f"✅ Demo files validation: {len(found_files)}/{len(required_files)} files available")
        return True
    else:
        print("❌ Demo files validation failed: No demo files found")
        return False


def validate_pipeline_import():
    """Validate pipeline can be imported and initialized."""
    print("\n🔍 Validating pipeline import...")
    
    try:
        from preauth_system.pipeline_module import PreAuthPipeline
        print("✅ PreAuthPipeline import successful")
        
        pipeline = PreAuthPipeline()
        print("✅ PreAuthPipeline initialization successful")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        return False


def validate_api_import():
    """Validate API components can be imported."""
    print("\n🔍 Validating API imports...")
    
    try:
        from api.main import app
        print("✅ FastAPI app import successful")
        
        from fastapi.testclient import TestClient
        client = TestClient(app)
        print("✅ TestClient initialization successful")
        return True
        
    except ImportError as e:
        print(f"❌ API import error: {e}")
        return False
    except Exception as e:
        print(f"❌ API initialization error: {e}")
        return False


def validate_test_dependencies():
    """Validate test dependencies are installed."""
    print("\n🔍 Validating test dependencies...")
    
    required_packages = ["pytest", "httpx", "fastapi"]
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} available")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} missing")
    
    if not missing_packages:
        print("✅ All test dependencies available")
        return True
    else:
        print(f"❌ Missing packages: {missing_packages}")
        return False


def validate_integration_tests_exist():
    """Validate integration test files exist."""
    print("\n🔍 Validating integration test files...")
    
    test_dir = Path("tests/integration")
    if not test_dir.exists():
        print(f"❌ Integration test directory not found: {test_dir}")
        return False
    
    required_test_files = [
        "test_pipeline_integration.py",
        "test_api_endpoints.py", 
        "test_cli_interface.py",
        "test_dossier_quality.py",
        "test_ui_workflow.py"
    ]
    
    found_files = []
    for filename in required_test_files:
        file_path = test_dir / filename
        if file_path.exists():
            found_files.append(filename)
            print(f"✅ Found: {filename}")
        else:
            print(f"❌ Missing: {filename}")
    
    if len(found_files) == len(required_test_files):
        print("✅ All integration test files present")
        return True
    else:
        print(f"❌ Integration test files incomplete: {len(found_files)}/{len(required_test_files)}")
        return False


def run_quick_pipeline_test():
    """Run a quick pipeline test to validate basic functionality."""
    print("\n🔍 Running quick pipeline validation...")
    
    try:
        from preauth_system.pipeline_module import PreAuthPipeline
        import tempfile
        import time
        
        # Create minimal test XML
        test_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
    <Header>
        <SenderID>TEST</SenderID>
        <ReceiverID>TEST</ReceiverID>
        <TransactionDateTime>31/07/2025 14:15</TransactionDateTime>
        <TransactionID>TEST-001</TransactionID>
    </Header>
    <JustificationText>Quick validation test</JustificationText>
    <ServiceRequests>
        <ServiceRequest>
            <ct:ActivityCode>83036</ct:ActivityCode>
            <ct:DiagnosisCode>E11.9</ct:DiagnosisCode>
            <ct:ActivityDateTime>01/08/2025 09:00</ct:ActivityDateTime>
            <ct:ActivityInstructions>Test</ct:ActivityInstructions>
            <RequestedAmount currency="AED">100.00</RequestedAmount>
        </ServiceRequest>
    </ServiceRequests>
</PriorAuthorizationRequest>'''
        
        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(test_xml)
            temp_path = f.name
        
        try:
            # Test pipeline
            pipeline = PreAuthPipeline()
            start_time = time.time()
            result = pipeline.forward(xml_path=temp_path, xml_format="eclaim")
            execution_time = time.time() - start_time
            
            # Validate basic structure
            required_phases = ["intake", "clinical_summary", "evidence", "checklist", "decision", "dossier"]
            for phase in required_phases:
                if phase not in result:
                    print(f"❌ Missing phase: {phase}")
                    return False
            
            print(f"✅ Quick pipeline test passed in {execution_time:.2f}s")
            print(f"   - Decision: {result['decision'].get('outcome', 'Unknown')}")
            print(f"   - Phases: {len(required_phases)}/6 complete")
            return True
            
        finally:
            # Clean up
            import os
            try:
                os.unlink(temp_path)
            except:
                pass
                
    except Exception as e:
        print(f"❌ Quick pipeline test failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all validation checks."""
    print("🚀 Integration Test Setup Validation")
    print("=" * 50)
    
    validations = [
        ("Demo Files", validate_demo_files),
        ("Pipeline Import", validate_pipeline_import),
        ("API Import", validate_api_import),
        ("Test Dependencies", validate_test_dependencies),
        ("Test Files", validate_integration_tests_exist),
        ("Quick Pipeline Test", run_quick_pipeline_test)
    ]
    
    results = []
    for name, validator in validations:
        try:
            success = validator()
            results.append((name, success))
        except Exception as e:
            print(f"❌ {name} validation error: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Validation Summary")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} validations passed")
    
    if passed == total:
        print("\n🎉 All validations passed! Integration tests are ready to run.")
        print("\nNext steps:")
        print("  1. Run individual tests: pytest tests/integration/test_pipeline_integration.py -v")
        print("  2. Run all integration tests: pytest tests/integration/ -v")
        print("  3. Run performance tests: pytest tests/integration/ -m performance -v")
        return 0
    else:
        print(f"\n⚠️  {total - passed} validation(s) failed. Please fix issues before running integration tests.")
        return 1


if __name__ == "__main__":
    sys.exit(main())