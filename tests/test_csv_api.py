#!/usr/bin/env python3
"""
Test script for CSV API endpoints.
"""

import requests
from pathlib import Path


def test_csv_endpoints():
    """Test the CSV processing endpoints."""
    base_url = "http://localhost:8000/api"

    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Health check: {response.status_code}")
        if response.status_code == 200:
            print(f"Health response: {response.json()}")
    except Exception as e:
        print(f"Health check failed: {e}")
        return

    # Test listing samples including CSV
    try:
        response = requests.get(f"{base_url}/samples")
        if response.status_code == 200:
            samples = response.json()
            print(f"\nFound {len(samples)} sample files:")
            for sample in samples:
                print(
                    f"  - {sample['name']} ({sample['format']}, {sample['file_type']}, {sample['size']} bytes)"
                )
        else:
            print(f"Failed to list samples: {response.status_code}")
    except Exception as e:
        print(f"Failed to list samples: {e}")

    # Test CSV-only samples endpoint
    try:
        response = requests.get(f"{base_url}/samples/csv")
        if response.status_code == 200:
            csv_samples = response.json()
            print(f"\nFound {len(csv_samples)} CSV sample files:")
            for sample in csv_samples:
                print(
                    f"  - {sample['name']} ({sample['format']}, {sample['size']} bytes)"
                )
        else:
            print(f"Failed to list CSV samples: {response.status_code}")
    except Exception as e:
        print(f"Failed to list CSV samples: {e}")

    # Test processing sample claims CSV
    try:
        response = requests.post(f"{base_url}/process/sample/claims-csv")
        if response.status_code == 200:
            result = response.json()
            print("\nClaims CSV processing successful!")
            print(f"  - Total claims: {result['data']['total_claims']}")
            print(f"  - Bundle ID: {result['data']['id']}")
            print(
                f"  - Processing time: {result['metadata']['processing_time_seconds']}s"
            )
        else:
            print(f"Failed to process claims CSV: {response.status_code}")
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Failed to process claims CSV: {e}")

    # Test processing sample clinical CSV
    try:
        response = requests.post(f"{base_url}/process/sample/clinical-csv")
        if response.status_code == 200:
            result = response.json()
            print("\nClinical CSV processing successful!")
            print(f"  - Total records: {result['data']['total_records']}")
            print(f"  - Bundle ID: {result['data']['id']}")
            print(
                f"  - Processing time: {result['metadata']['processing_time_seconds']}s"
            )
        else:
            print(f"Failed to process clinical CSV: {response.status_code}")
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Failed to process clinical CSV: {e}")

    # Test CSV file upload
    samples_dir = Path("samples")
    claims_file = samples_dir / "healthcare_claims_sample.csv"

    if claims_file.exists():
        try:
            with open(claims_file, 'rb') as f:
                files = {'file': ('healthcare_claims_sample.csv', f, 'text/csv')}
                response = requests.post(f"{base_url}/process/csv", files=files)

            if response.status_code == 200:
                result = response.json()
                print("\nCSV file upload processing successful!")
                print(f"  - Auto-detected type: {result['metadata']['csv_type']}")
                print(f"  - Total records: {result['metadata']['total_records']}")
                print(
                    f"  - Processing time: {result['metadata']['processing_time_seconds']}s"
                )
            else:
                print(f"Failed to process uploaded CSV: {response.status_code}")
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"Failed to test CSV upload: {e}")
    else:
        print(f"\nCSV sample file not found: {claims_file}")


if __name__ == "__main__":
    print("Testing CSV API endpoints...")
    print("Make sure the FastAPI server is running on http://localhost:8000")
    test_csv_endpoints()
