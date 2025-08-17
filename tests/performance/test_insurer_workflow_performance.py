"""
Performance Testing for Insurer Workflow

Validates system performance under realistic load conditions
and measures key performance indicators.
"""

import pytest
import time
import io
import concurrent.futures
from typing import List, Dict, Any
from fastapi.testclient import TestClient

from api.main import app


@pytest.mark.performance
class TestInsurerWorkflowPerformance:
    """Performance testing suite for insurer workflow."""
    
    @pytest.fixture
    def client(self):
        """Create FastAPI test client."""
        return TestClient(app)
    
    @pytest.fixture
    def sample_xml_content(self):
        """Sample XML for performance testing."""
        return '''<?xml version="1.0" encoding="UTF-8"?>
<PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
    <Header>
        <SenderID>PROV12345</SenderID>
        <ReceiverID>INSURER001</ReceiverID>
        <TransactionDateTime>17/08/2025 14:30</TransactionDateTime>
        <TransactionID>TXN-PERF-TEST</TransactionID>
    </Header>
    <PatientDetails>
        <ct:PatientID>Patient_PERF</ct:PatientID>
        <ct:EmiratesID>784-1990-1234567-0</ct:EmiratesID>
        <ct:FullName>Performance Test Patient</ct:FullName>
        <ct:DateOfBirth>01/01/1990</ct:DateOfBirth>
        <ct:Gender>M</ct:Gender>
    </PatientDetails>
    <JustificationText>Performance testing request.</JustificationText>
    <ServiceRequests>
        <ServiceRequest>
            <ct:ActivityCode>99213</ct:ActivityCode>
            <ct:DiagnosisCode>Z00.00</ct:DiagnosisCode>
            <ct:ActivityDateTime>20/08/2025 09:00</ct:ActivityDateTime>
            <ct:ActivityInstructions>Performance test procedure</ct:ActivityInstructions>
            <RequestedAmount currency="AED">500.00</RequestedAmount>
        </ServiceRequest>
    </ServiceRequests>
</PriorAuthorizationRequest>'''
    
    def test_request_processing_throughput(self, client, sample_xml_content):
        """Test system throughput for request processing."""
        
        def process_single_request(index: int) -> Dict[str, Any]:
            """Process a single request and measure metrics."""
            start_time = time.time()
            
            xml_file = io.BytesIO(sample_xml_content.encode('utf-8'))
            response = client.post(
                "/api/process/unified",
                files={"file": (f"throughput_test_{index}.xml", xml_file, "application/xml")},
                data={
                    "patient_id": f"Patient_THROUGHPUT_{index}",
                    "xml_format": "eclaim",
                    "include_dossier": False
                }
            )
            
            processing_time = time.time() - start_time
            
            return {
                "success": response.status_code == 200,
                "processing_time": processing_time,
                "cost": response.json().get("performance", {}).get("cost", {}).get("total_cost_usd", 0) if response.status_code == 200 else 0,
                "request_id": response.json().get("request_id") if response.status_code == 200 else None
            }
        
        # Test concurrent processing capability
        num_requests = 10
        max_workers = 5
        
        print(f"\nTesting throughput with {num_requests} requests, {max_workers} workers...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            start_time = time.time()
            futures = [executor.submit(process_single_request, i) for i in range(num_requests)]
            results = [future.result(timeout=120) for future in concurrent.futures.as_completed(futures)]
            total_time = time.time() - start_time
        
        # Analyze results
        successful_requests = [r for r in results if r["success"]]
        success_rate = len(successful_requests) / num_requests
        
        avg_processing_time = sum(r["processing_time"] for r in successful_requests) / len(successful_requests) if successful_requests else 0
        total_cost = sum(r["cost"] for r in successful_requests)
        throughput = len(successful_requests) / total_time  # requests per second
        
        # Performance assertions
        assert success_rate >= 0.8, f"Success rate {success_rate:.2%} below 80%"
        assert avg_processing_time < 20.0, f"Average processing time {avg_processing_time:.2f}s exceeds 20s"
        assert total_cost < 2.0, f"Total cost ${total_cost:.2f} exceeds $2.00 for {num_requests} requests"
        assert throughput >= 0.2, f"Throughput {throughput:.2f} req/s below 0.2 req/s"
        
        print(f"Performance Results:")
        print(f"  Success Rate: {success_rate:.2%}")
        print(f"  Average Processing Time: {avg_processing_time:.2f}s")
        print(f"  Total Cost: ${total_cost:.4f}")
        print(f"  Throughput: {throughput:.2f} requests/second")
        print(f"  Total Test Time: {total_time:.2f}s")
    
    def test_dashboard_response_times(self, client):
        """Test dashboard component response times."""
        
        endpoints_to_test = [
            ("/api/insurer/requests", "Request Inbox"),
            ("/api/insurer/dashboard/metrics", "Dashboard Metrics"),
            ("/api/dashboard/summary", "Dashboard Summary"),
            ("/api/patients", "Patient List"),
            ("/api/health", "Health Check")
        ]
        
        response_times = {}
        
        print(f"\nTesting dashboard response times...")
        
        for endpoint, name in endpoints_to_test:
            times = []
            
            # Test each endpoint 5 times
            for iteration in range(5):
                start_time = time.time()
                try:
                    response = client.get(endpoint)
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        times.append(response_time)
                    else:
                        print(f"  {name}: HTTP {response.status_code} on iteration {iteration + 1}")
                except Exception as e:
                    print(f"  {name}: Error on iteration {iteration + 1}: {e}")
            
            if times:
                avg_time = sum(times) / len(times)
                max_time = max(times)
                min_time = min(times)
                response_times[name] = {"avg": avg_time, "max": max_time, "min": min_time}
        
        # Performance thresholds
        thresholds = {
            "Request Inbox": 3.0,
            "Dashboard Metrics": 5.0, 
            "Dashboard Summary": 3.0,
            "Patient List": 2.0,
            "Health Check": 1.0
        }
        
        for name, threshold in thresholds.items():
            if name in response_times:
                avg_time = response_times[name]["avg"]
                assert avg_time < threshold, f"{name} average response time {avg_time:.2f}s exceeds {threshold}s"
        
        print(f"Dashboard Response Times:")
        for name, times in response_times.items():
            print(f"  {name}: {times['avg']:.2f}s avg, {times['max']:.2f}s max, {times['min']:.2f}s min")
    
    def test_concurrent_dashboard_access(self, client):
        """Test dashboard performance under concurrent access."""
        
        def access_dashboard():
            """Access multiple dashboard endpoints concurrently."""
            start_time = time.time()
            
            endpoints = [
                "/api/insurer/requests?limit=10",
                "/api/dashboard/summary",
                "/api/health"
            ]
            
            results = []
            for endpoint in endpoints:
                try:
                    response = client.get(endpoint)
                    results.append({
                        "endpoint": endpoint,
                        "status_code": response.status_code,
                        "success": response.status_code == 200
                    })
                except Exception as e:
                    results.append({
                        "endpoint": endpoint,
                        "status_code": 500,
                        "success": False,
                        "error": str(e)
                    })
            
            total_time = time.time() - start_time
            return {
                "total_time": total_time,
                "results": results,
                "success_count": sum(1 for r in results if r["success"])
            }
        
        # Test with 5 concurrent users
        num_users = 5
        print(f"\nTesting concurrent dashboard access with {num_users} users...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_users) as executor:
            start_time = time.time()
            futures = [executor.submit(access_dashboard) for _ in range(num_users)]
            results = [future.result(timeout=30) for future in concurrent.futures.as_completed(futures)]
            total_test_time = time.time() - start_time
        
        # Analyze concurrent access results
        avg_user_time = sum(r["total_time"] for r in results) / len(results)
        total_success_count = sum(r["success_count"] for r in results)
        total_possible_successes = num_users * 3  # 3 endpoints per user
        success_rate = total_success_count / total_possible_successes
        
        # Performance assertions
        assert success_rate >= 0.8, f"Concurrent access success rate {success_rate:.2%} below 80%"
        assert avg_user_time < 10.0, f"Average user session time {avg_user_time:.2f}s exceeds 10s"
        assert total_test_time < 15.0, f"Total test time {total_test_time:.2f}s exceeds 15s"
        
        print(f"Concurrent Access Results:")
        print(f"  Success Rate: {success_rate:.2%} ({total_success_count}/{total_possible_successes})")
        print(f"  Average User Session Time: {avg_user_time:.2f}s")
        print(f"  Total Test Time: {total_test_time:.2f}s")
    
    def test_request_inbox_pagination_performance(self, client):
        """Test performance of request inbox with different page sizes."""
        
        page_sizes = [10, 25, 50, 100]
        performance_results = {}
        
        print(f"\nTesting inbox pagination performance...")
        
        for page_size in page_sizes:
            times = []
            
            # Test each page size 3 times
            for _ in range(3):
                start_time = time.time()
                response = client.get(f"/api/insurer/requests?limit={page_size}&offset=0")
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    times.append(response_time)
                    
                    # Also test pagination offset
                    start_time = time.time()
                    response = client.get(f"/api/insurer/requests?limit={page_size}&offset={page_size}")
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        times.append(response_time)
            
            if times:
                avg_time = sum(times) / len(times)
                performance_results[page_size] = avg_time
        
        # Validate performance doesn't degrade significantly with larger page sizes
        for page_size, avg_time in performance_results.items():
            max_time_for_size = 2.0 + (page_size / 100) * 2.0  # Allow more time for larger pages
            assert avg_time < max_time_for_size, f"Page size {page_size} avg time {avg_time:.2f}s exceeds {max_time_for_size:.2f}s"
        
        print(f"Pagination Performance:")
        for page_size, avg_time in performance_results.items():
            print(f"  Page Size {page_size}: {avg_time:.2f}s avg")
    
    def test_patient_history_performance(self, client):
        """Test patient history endpoint performance."""
        
        # Test with known patient IDs (if any exist)
        test_patients = ["Patient_007", "Patient_001", "Patient_002"]
        
        print(f"\nTesting patient history performance...")
        
        response_times = []
        successful_requests = 0
        
        for patient_id in test_patients:
            start_time = time.time()
            response = client.get(f"/api/insurer/patients/{patient_id}/history")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                response_times.append(response_time)
                successful_requests += 1
                
                # Validate response contains expected data
                data = response.json()
                assert "timeline" in data
                assert "history" in data
                assert "trends" in data
                
            elif response.status_code == 404:
                # Patient not found is acceptable for testing
                print(f"  Patient {patient_id} not found (404) - acceptable for testing")
        
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            
            # Performance assertions
            assert avg_time < 3.0, f"Average patient history time {avg_time:.2f}s exceeds 3s"
            assert max_time < 5.0, f"Max patient history time {max_time:.2f}s exceeds 5s"
            
            print(f"Patient History Performance:")
            print(f"  Successful Requests: {successful_requests}/{len(test_patients)}")
            print(f"  Average Response Time: {avg_time:.2f}s")
            print(f"  Max Response Time: {max_time:.2f}s")
        else:
            print("  No patient history data available for performance testing")
    
    def test_memory_usage_during_processing(self, client, sample_xml_content):
        """Test memory usage during request processing (basic monitoring)."""
        import psutil
        import os
        
        # Get current process
        process = psutil.Process(os.getpid())
        
        # Measure baseline memory
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        print(f"\nTesting memory usage during processing...")
        print(f"Baseline Memory: {baseline_memory:.1f} MB")
        
        # Process multiple requests and monitor memory
        memory_readings = [baseline_memory]
        
        for i in range(5):
            xml_file = io.BytesIO(sample_xml_content.encode('utf-8'))
            
            response = client.post(
                "/api/process/unified",
                files={"file": (f"memory_test_{i}.xml", xml_file, "application/xml")},
                data={
                    "patient_id": f"Patient_MEMORY_{i}",
                    "xml_format": "eclaim",
                    "include_dossier": False
                }
            )
            
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_readings.append(current_memory)
            
            if response.status_code == 200:
                print(f"  Request {i+1}: {current_memory:.1f} MB")
        
        peak_memory = max(memory_readings)
        memory_increase = peak_memory - baseline_memory
        
        # Memory usage assertions (generous limits for testing environment)
        assert memory_increase < 200, f"Memory increase {memory_increase:.1f} MB exceeds 200 MB"
        assert peak_memory < 1000, f"Peak memory {peak_memory:.1f} MB exceeds 1000 MB"
        
        print(f"Memory Usage Results:")
        print(f"  Peak Memory: {peak_memory:.1f} MB")
        print(f"  Memory Increase: {memory_increase:.1f} MB")
    
    def test_error_handling_performance(self, client):
        """Test that error responses are returned quickly."""
        
        error_endpoints = [
            ("/api/insurer/requests/INVALID_ID", "Invalid Request ID"),
            ("/api/insurer/patients/INVALID_PATIENT/history", "Invalid Patient"),
            ("/api/insurer/requests?status=invalid_status", "Invalid Filter"),
        ]
        
        print(f"\nTesting error response performance...")
        
        for endpoint, description in error_endpoints:
            times = []
            
            for _ in range(3):
                start_time = time.time()
                response = client.get(endpoint)
                response_time = time.time() - start_time
                
                # Should return error quickly
                assert response.status_code >= 400, f"{description} should return error status"
                times.append(response_time)
            
            avg_time = sum(times) / len(times)
            assert avg_time < 1.0, f"{description} error response time {avg_time:.2f}s exceeds 1s"
            
            print(f"  {description}: {avg_time:.3f}s avg")