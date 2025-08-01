#!/usr/bin/env python3
"""
Simple test script for the FastAPI backend.

Tests basic functionality of the Nazmito Healthcare XML API endpoints.
"""

import requests
import sys
from pathlib import Path

# Test configuration
API_BASE_URL = "http://localhost:8000"
SAMPLES_DIR = Path(__file__).parent.parent / "samples"


def test_health_endpoint():
    """Test the health check endpoint."""
    print("🔍 Testing health endpoint...")

    try:
        response = requests.get(f"{API_BASE_URL}/api/health")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data['status']}")
            print(f"   Timestamp: {data['timestamp']}")
            print(f"   Version: {data['version']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server. Is it running?")
        print("   Start server with: python api/run_server.py")
        return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False


def test_samples_endpoint():
    """Test the samples listing endpoint."""
    print("\n🔍 Testing samples endpoint...")

    try:
        response = requests.get(f"{API_BASE_URL}/api/samples")

        if response.status_code == 200:
            samples = response.json()
            print(f"✅ Found {len(samples)} sample files:")

            for sample in samples:
                print(
                    f"   - {sample['name']} ({sample['format']}, {sample['size']} bytes)"
                )

            return len(samples) > 0
        else:
            print(f"❌ Samples endpoint failed: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Samples endpoint error: {e}")
        return False


def test_sample_processing():
    """Test processing sample files."""
    print("\n🔍 Testing sample file processing...")

    success_count = 0

    # Test eClaimLink sample
    print("   Testing eClaimLink sample...")
    try:
        response = requests.post(f"{API_BASE_URL}/api/process/sample/eclaim")

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                bundle_data = data['data']
                metadata = data['metadata']

                print("   ✅ eClaimLink processed successfully")
                print(f"      Authorization ID: {bundle_data.get('authorization_id')}")
                print(f"      Services: {len(bundle_data.get('services', []))}")
                print(
                    f"      Processing time: {metadata.get('processing_time_seconds')}s"
                )
                success_count += 1
            else:
                print(f"   ❌ eClaimLink processing failed: {data.get('error')}")
        else:
            print(f"   ❌ eClaimLink request failed: {response.status_code}")

    except Exception as e:
        print(f"   ❌ eClaimLink processing error: {e}")

    # Test Shafafiya sample
    print("   Testing Shafafiya sample...")
    try:
        response = requests.post(f"{API_BASE_URL}/api/process/sample/shafafiya")

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                bundle_data = data['data']
                metadata = data['metadata']

                print("   ✅ Shafafiya processed successfully")
                print(f"      Authorization ID: {bundle_data.get('authorization_id')}")
                print(f"      Activities: {len(bundle_data.get('activities', []))}")
                print(
                    f"      Processing time: {metadata.get('processing_time_seconds')}s"
                )
                success_count += 1
            else:
                print(f"   ❌ Shafafiya processing failed: {data.get('error')}")
        else:
            print(f"   ❌ Shafafiya request failed: {response.status_code}")

    except Exception as e:
        print(f"   ❌ Shafafiya processing error: {e}")

    return success_count == 2


def test_file_upload():
    """Test file upload functionality."""
    print("\n🔍 Testing file upload...")

    # Test with eClaimLink sample file
    eclaim_file = SAMPLES_DIR / "eclaim_link_request.xml"

    if not eclaim_file.exists():
        print(f"   ❌ Sample file not found: {eclaim_file}")
        return False

    try:
        with open(eclaim_file, 'rb') as f:
            files = {'file': ('test_eclaim.xml', f, 'application/xml')}
            response = requests.post(f"{API_BASE_URL}/api/process/eclaim", files=files)

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                bundle_data = data['data']
                metadata = data['metadata']

                print("   ✅ File upload processed successfully")
                print(f"      Filename: {metadata.get('filename')}")
                print(f"      File size: {metadata.get('file_size_bytes')} bytes")
                print(f"      Format: {metadata.get('format')}")
                print(f"      Authorization ID: {bundle_data.get('authorization_id')}")
                return True
            else:
                print(f"   ❌ File upload processing failed: {data.get('error')}")
                return False
        else:
            print(f"   ❌ File upload request failed: {response.status_code}")
            print(f"      Response: {response.text}")
            return False

    except Exception as e:
        print(f"   ❌ File upload error: {e}")
        return False


def main():
    """Run all API tests."""
    print("=" * 60)
    print("Nazmito Healthcare XML API - Test Suite")
    print("=" * 60)

    tests = [
        ("Health Check", test_health_endpoint),
        ("Samples Endpoint", test_samples_endpoint),
        ("Sample Processing", test_sample_processing),
        ("File Upload", test_file_upload),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {passed + failed}")

    if failed == 0:
        print("\n🎉 All tests passed! API is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed. Check the logs above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
