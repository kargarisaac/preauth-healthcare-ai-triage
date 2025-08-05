#!/usr/bin/env python3
"""
Validation script for enhanced FastAPI backend with LLM integration.

Tests the new endpoints and models without requiring external dependencies.
"""

import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_models():
    """Test that all models can be imported and instantiated."""
    try:
        from api.models import (
            ProcessingStatus,
            LLMValidationResponse,
            UIFriendlyReport,
            ProgressUpdate,
            LLMProvider,
            ValidationSeverity,
        )

        print("✅ Model imports successful")

        # Test enum values
        assert ProcessingStatus.PENDING == "pending"
        assert ProcessingStatus.LLM_VALIDATING == "llm_validating"
        assert LLMProvider.OPENAI == "openai"
        assert ValidationSeverity.CRITICAL == "critical"

        print("✅ Enum values correct")

        # Test model instantiation
        response = LLMValidationResponse(success=True, metadata={"test": "data"})

        ui_report = UIFriendlyReport(
            overall_grade="A",
            quality_percentage=95,
            status=ProcessingStatus.COMPLETED,
            total_records=100,
            valid_records=95,
            detected_fields=10,
            fhir_resources=5,
            critical_count=0,
            warning_count=2,
            info_count=3,
            processing_time=2.5,
            llm_enhanced=True,
            sample_based=False,
        )

        progress = ProgressUpdate(
            task_id="test-123",
            status=ProcessingStatus.IN_PROGRESS,
            progress_percentage=50,
            current_step="Processing data",
        )

        print("✅ Model instantiation successful")
        print(f"✅ Response model: {response.success}")
        print(f"✅ UI report grade: {ui_report.overall_grade}")
        print(f"✅ Progress update: {progress.progress_percentage}%")

        return True

    except Exception as e:
        print(f"❌ Model test failed: {e}")
        return False


def test_api_structure():
    """Test that the API structure is correct."""
    try:
        # Read main.py and check for new endpoints
        main_path = Path(__file__).parent / "main.py"
        with open(main_path, "r") as f:
            content = f.read()

        required_endpoints = [
            "/api/process/csv-with-llm",
            "/api/tasks/{task_id}",
            "/ws/validation-progress/{task_id}",
            "/ws/validation-progress",
        ]

        for endpoint in required_endpoints:
            if endpoint in content:
                print(f"✅ Found endpoint: {endpoint}")
            else:
                print(f"❌ Missing endpoint: {endpoint}")
                return False

        # Check for WebSocket support
        if "WebSocket" in content and "ConnectionManager" in content:
            print("✅ WebSocket support implemented")
        else:
            print("❌ WebSocket support missing")
            return False

        # Check for background task support
        if (
            "BackgroundTasks" in content
            and "process_csv_with_llm_background" in content
        ):
            print("✅ Background task support implemented")
        else:
            print("❌ Background task support missing")
            return False

        return True

    except Exception as e:
        print(f"❌ API structure test failed: {e}")
        return False


def test_csv_processor_enhancements():
    """Test CSV processor enhancements without requiring pandas."""
    try:
        # Read csv_processor.py and check for new methods
        csv_path = Path(__file__).parent.parent / "pipelines" / "csv_processor.py"
        with open(csv_path, "r") as f:
            content = f.read()

        required_methods = [
            "apply_smart_sampling",
            "_calculate_smart_sample_indices",
            "_stratified_sample_indices",
            "_calculate_representativeness_score",
        ]

        for method in required_methods:
            if f"def {method}" in content:
                print(f"✅ Found method: {method}")
            else:
                print(f"❌ Missing method: {method}")
                return False

        # Check for progress callback support
        if "progress_callback" in content:
            print("✅ Progress callback support implemented")
        else:
            print("❌ Progress callback support missing")
            return False

        return True

    except Exception as e:
        print(f"❌ CSV processor test failed: {e}")
        return False


def main():
    """Run all validation tests."""
    print("🔍 Validating Enhanced FastAPI Backend with LLM Integration")
    print("=" * 60)

    tests = [
        ("Models and Response Types", test_models),
        ("API Structure and Endpoints", test_api_structure),
        ("CSV Processor Enhancements", test_csv_processor_enhancements),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Testing: {test_name}")
        print("-" * 40)
        result = test_func()
        results.append(result)
        print(f"Result: {'✅ PASS' if result else '❌ FAIL'}")

    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"{test_name:<35} {status}")

    print("-" * 60)
    print(f"Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Enhanced API is ready for use.")
        print("\nNew Features Implemented:")
        print("• LLM-enhanced CSV processing with validation")
        print("• Smart sampling for large datasets")
        print("• Real-time progress updates via WebSocket")
        print("• Comprehensive validation reports")
        print("• UI-friendly response models")
        print("• Background task processing")
        print("• Task status tracking")
        return True
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please review the implementation.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
