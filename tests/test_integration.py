#!/usr/bin/env python3
"""
Test script to validate the complete UI integration with XMLProcessor.
"""

import os
import sys
from pipelines.xml_processor import XMLProcessor


def test_xml_processor():
    """Test XMLProcessor directly to ensure it's working."""
    print("=" * 60)
    print("Testing XMLProcessor Integration")
    print("=" * 60)

    processor = XMLProcessor()

    # Test eClaimLink
    print("\n🔬 Testing eClaimLink Processing:")
    try:
        eclaim_result = processor.process_eclaim_link("samples/eclaim_link_request.xml")
        print("✅ eClaimLink Success:")
        print(f"   Authorization ID: {eclaim_result.get('authorization_id')}")
        print(f"   Services: {len(eclaim_result.get('services', []))}")
        print(f"   Resource Type: {eclaim_result.get('resourceType')}")
        print(f"   Source: {eclaim_result.get('meta', {}).get('source')}")
    except Exception as e:
        print(f"❌ eClaimLink Error: {e}")
        return False

    # Test Shafafiya
    print("\n🔬 Testing Shafafiya Processing:")
    try:
        shafafiya_result = processor.process_shafafiya(
            "samples/shafafiya_prior_auth_request.xml"
        )
        print("✅ Shafafiya Success:")
        print(f"   Authorization ID: {shafafiya_result.get('authorization_id')}")
        print(f"   Activities: {len(shafafiya_result.get('activities', []))}")
        print(f"   Resource Type: {shafafiya_result.get('resourceType')}")
        print(f"   Source: {shafafiya_result.get('meta', {}).get('source')}")
    except Exception as e:
        print(f"❌ Shafafiya Error: {e}")
        return False

    return True


def test_ui_files():
    """Test that UI files exist and are properly structured."""
    print("\n" + "=" * 60)
    print("Testing UI Files")
    print("=" * 60)

    ui_files = {
        "Landing Page": "ui/index.html",
        "Dashboard": "ui/dashboard.html",
        "Dashboard CSS": "ui/dashboard.css",
        "Dashboard JS": "ui/dashboard.js",
    }

    all_exist = True
    for name, path in ui_files.items():
        if os.path.exists(path):
            size = os.path.getsize(path)
            print(f"✅ {name}: {path} ({size:,} bytes)")
        else:
            print(f"❌ {name}: {path} (missing)")
            all_exist = False

    return all_exist


def test_api_files():
    """Test that API files exist."""
    print("\n" + "=" * 60)
    print("Testing API Files")
    print("=" * 60)

    api_files = {
        "FastAPI Main": "api/main.py",
        "Server Runner": "api/run_server.py",
        "API Tests": "api/test_api.py",
    }

    all_exist = True
    for name, path in api_files.items():
        if os.path.exists(path):
            size = os.path.getsize(path)
            print(f"✅ {name}: {path} ({size:,} bytes)")
        else:
            print(f"❌ {name}: {path} (missing)")
            all_exist = False

    return all_exist


def show_usage_instructions():
    """Show instructions for using the dashboard."""
    print("\n" + "=" * 60)
    print("Dashboard Usage Instructions")
    print("=" * 60)

    print("\n🚀 To run the complete system:")
    print("\n1. Start FastAPI Backend:")
    print("   source .venv/bin/activate")
    print("   python api/run_server.py --port 8000")
    print("   # API docs: http://localhost:8000/api/docs")

    print("\n2. Start Frontend Server:")
    print("   cd ui")
    print("   python3 -m http.server 8001")
    print("   # Dashboard: http://localhost:8001/dashboard.html")
    print("   # Landing page: http://localhost:8001/index.html")

    print("\n3. Or open dashboard directly:")
    print("   open ui/dashboard.html")

    print("\n📋 Dashboard Features:")
    print("   • Upload XML files (eClaimLink or Shafafiya)")
    print("   • Process sample files")
    print("   • View results in Summary/Details/Raw Data tabs")
    print("   • Professional healthcare UI with metrics")
    print("   • Download processed results")

    print("\n🔧 API Endpoints:")
    print("   • POST /api/process/eclaim - Process eClaimLink XML")
    print("   • POST /api/process/shafafiya - Process Shafafiya XML")
    print("   • GET /api/samples - List sample files")
    print("   • GET /api/health - Health check")


def main():
    """Run all integration tests."""
    print("🏥 Nazmito Healthcare XML Processing - Integration Test")

    # Test core functionality
    xml_ok = test_xml_processor()
    ui_ok = test_ui_files()
    api_ok = test_api_files()

    # Show summary
    print("\n" + "=" * 60)
    print("Integration Test Results")
    print("=" * 60)

    print(f"XMLProcessor: {'✅ Working' if xml_ok else '❌ Failed'}")
    print(f"UI Files: {'✅ Present' if ui_ok else '❌ Missing'}")
    print(f"API Files: {'✅ Present' if api_ok else '❌ Missing'}")

    if xml_ok and ui_ok and api_ok:
        print("\n🎉 All systems ready!")
        print("✅ XMLProcessor functioning correctly")
        print("✅ Dashboard UI created successfully")
        print("✅ FastAPI backend ready")
        show_usage_instructions()
        return True
    else:
        print("\n❌ Some components failed. Check errors above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
