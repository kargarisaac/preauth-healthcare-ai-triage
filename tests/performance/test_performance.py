"""
Performance tests validating MVP requirements (aligned with current API).
"""

import pytest
import time
import statistics
from unittest.mock import patch, MagicMock
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from preauth_system.orchestrator import PreAuthOrchestrator
from preauth_system.safety import RiskLevel


@pytest.mark.performance
class TestMVPPerformanceRequirements:
    """Test MVP performance requirements: P50 < 6s, P95 < 12s, cost < $0.10."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance for performance testing."""
        with patch("preauth_system.rag.kb_loader.KnowledgeBaseLoader") as mock_kb:
            mock_kb.return_value = MagicMock()
            orchestrator = PreAuthOrchestrator()
            yield orchestrator

    def test_single_request_performance_p50(self, orchestrator):
        xml_data = self._create_test_xml("diabetes_cgm")
        self._mock_realistic_workflow(orchestrator, "APPROVE")

        processing_times = []
        for _ in range(10):
            start_time = time.time()
            result = orchestrator.process_request(xml_content=xml_data)
            processing_times.append(time.time() - start_time)
            assert "decision" in result
            assert result["decision"]["outcome"] in [
                "APPROVED",
                "REQUIRES_REVIEW",
                "DENIED",
                "APPROVE",
                "REVIEW",
                "DENY",
            ]

        p50 = statistics.median(processing_times)
        assert p50 < 6.0

    def test_batch_performance_p95(self, orchestrator):
        cases = [
            self._create_test_xml(x)
            for x in ["diabetes_cgm", "osteoarthritis_knee", "parkinsons_dbs"]
        ] * 10
        processing_times = []
        for i, xml_data in enumerate(cases):
            expected = ["APPROVE", "REVIEW", "DENY"][i % 3]
            self._mock_realistic_workflow(orchestrator, expected)
            start_time = time.time()
            orchestrator.process_request(xml_content=xml_data)
            processing_times.append(time.time() - start_time)
        p50 = statistics.median(processing_times)
        p95 = statistics.quantiles(processing_times, n=20)[18]
        assert p50 < 6.0
        assert p95 < 12.0

    def test_cost_per_case_requirement(self, orchestrator):
        cases = [
            ("diabetes_cgm", 0.025, "APPROVE"),
            ("osteoarthritis_knee", 0.045, "REVIEW"),
            ("parkinsons_dbs", 0.085, "DENY"),
        ]
        total_cost = 0.0
        for case_type, expected_cost, expected_outcome in cases:
            xml_data = self._create_test_xml(case_type)
            self._mock_realistic_workflow(orchestrator, expected_outcome)
            with patch(
                "preauth_system.utils.track_llm_cost", return_value=expected_cost
            ):
                result = orchestrator.process_request(xml_content=xml_data)
                case_cost = result.get("estimated_cost", 0)
                assert 0 < case_cost <= 0.10
                total_cost += case_cost
        avg_cost = total_cost / len(cases)
        assert avg_cost <= 0.06

    def test_concurrent_processing_performance(self, orchestrator):
        xml_data = self._create_test_xml("diabetes_cgm")
        self._mock_realistic_workflow(orchestrator, "APPROVE")

        def process_request():
            start = time.time()
            result = orchestrator.process_request(xml_content=xml_data)
            return time.time() - start, result

        processing_times = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            for fut in as_completed(
                [executor.submit(process_request) for _ in range(5)]
            ):
                t, r = fut.result()
                processing_times.append(t)
                assert "decision" in r
        assert max(processing_times) < 8.0
        assert statistics.mean(processing_times) < 6.0

    def test_cached_performance_requirement(self, orchestrator):
        xml_data = self._create_test_xml("diabetes_cgm")
        self._mock_realistic_workflow(orchestrator, "APPROVE")

        start = time.time()
        first_result = orchestrator.process_request(xml_content=xml_data)
        first_time = time.time() - start
        assert first_time < 20.0

        with patch.object(orchestrator, "check_cache", return_value=first_result):
            cached_times = []
            for _ in range(5):
                start = time.time()
                cached_result = orchestrator.process_request(xml_content=xml_data)
                cached_times.append(time.time() - start)
                assert cached_result == first_result
        assert max(cached_times) < 5.0
        assert statistics.mean(cached_times) < 2.0

    def test_memory_usage_stability(self, orchestrator, performance_monitor):
        """Test memory usage remains stable during processing."""
        xml_data = self._create_test_xml("diabetes_cgm")
        self._mock_realistic_workflow(orchestrator, "APPROVE")

        performance_monitor.start()

        # Process multiple requests to test memory stability
        for i in range(20):
            result = orchestrator.process_request(xml_content=xml_data)
            assert "decision" in result

            # Vary request types to test different memory patterns
            if i % 3 == 1:
                xml_data = self._create_test_xml("osteoarthritis_knee")
                self._mock_realistic_workflow(orchestrator, "REVIEW")
            elif i % 3 == 2:
                xml_data = self._create_test_xml("parkinsons_dbs")
                self._mock_realistic_workflow(orchestrator, "DENY")
            else:
                xml_data = self._create_test_xml("diabetes_cgm")
                self._mock_realistic_workflow(orchestrator, "APPROVE")

        performance_monitor.stop()

        # Memory usage should remain reasonable
        performance_monitor.assert_performance(max_time=60.0, max_memory_mb=500.0)

        print(
            f"Memory stability - Peak usage: {performance_monitor.memory_usage_mb:.1f}MB"
        )

    def test_end_to_end_demo_performance(self, orchestrator):
        """Test end-to-end performance with all 3 demo cases."""
        demo_cases = [
            ("Patient_007_diabetes_cgm", "APPROVE", 6.0),
            ("Patient_005_osteoarthritis", "REVIEW", 8.0),
            ("Patient_011_parkinsons_dbs", "DENY", 10.0),
        ]

        total_time = 0.0
        case_times = []

        for case_name, expected_outcome, max_time in demo_cases:
            xml_data = self._create_test_xml(case_name)
            self._mock_realistic_workflow(orchestrator, expected_outcome)

            start_time = time.time()
            result = orchestrator.process_request(xml_content=xml_data)
            processing_time = time.time() - start_time

            case_times.append(processing_time)
            total_time += processing_time

            # Verify expected outcome
            assert result["decision"]["outcome"].upper() == expected_outcome.upper()

            # Individual case time requirements
            assert (
                processing_time <= max_time
            ), f"{case_name} took {processing_time:.2f}s, max {max_time}s"

        # Overall performance requirements
        avg_time = total_time / len(demo_cases)
        assert avg_time <= 6.0, f"Average demo case time {avg_time:.2f}s exceeds 6s"
        assert total_time <= 20.0, f"Total demo time {total_time:.2f}s exceeds 20s"

        print(f"Demo performance - Total: {total_time:.2f}s, Average: {avg_time:.2f}s")
        for i, (case_name, _, _) in enumerate(demo_cases):
            print(f"  {case_name}: {case_times[i]:.2f}s")

    # Helper methods

    def _create_test_xml(self, case_type: str) -> str:
        templates = {
            "diabetes_cgm": """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<PriorAuthorizationRequest xmlns:ct=\"http://www.eclaimlink.ae/DHD/ValidationSchema\">
  <Header><SenderID>PERF_TEST</SenderID><TransactionID>PERF-CGM-001</TransactionID><TransactionDateTime>08/08/2025 10:00</TransactionDateTime></Header>
  <JustificationText>Performance test - diabetes CGM request</JustificationText>
  <ServiceRequests><ServiceRequest><ct:ActivityCode>95250</ct:ActivityCode><ct:DiagnosisCode>E11.9</ct:DiagnosisCode><RequestedAmount currency=\"AED\">1200.00</RequestedAmount></ServiceRequest></ServiceRequests>
</PriorAuthorizationRequest>""",
            "osteoarthritis_knee": """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<PriorAuthorizationRequest xmlns:ct=\"http://www.eclaimlink.ae/DHD/ValidationSchema\">
  <Header><SenderID>PERF_TEST</SenderID><TransactionID>PERF-KNEE-001</TransactionID><TransactionDateTime>08/08/2025 10:00</TransactionDateTime></Header>
  <JustificationText>Performance test - knee osteoarthritis treatment</JustificationText>
  <ServiceRequests><ServiceRequest><ct:ActivityCode>27447</ct:ActivityCode><ct:DiagnosisCode>M17.9</ct:DiagnosisCode><RequestedAmount currency=\"AED\">25000.00</RequestedAmount></ServiceRequest></ServiceRequests>
</PriorAuthorizationRequest>""",
            "parkinsons_dbs": """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<PriorAuthorizationRequest xmlns:ct=\"http://www.eclaimlink.ae/DHD/ValidationSchema\">
  <Header><SenderID>PERF_TEST</SenderID><TransactionID>PERF-DBS-001</TransactionID><TransactionDateTime>08/08/2025 10:00</TransactionDateTime></Header>
  <JustificationText>Performance test - Parkinson's DBS procedure</JustificationText>
  <ServiceRequests><ServiceRequest><ct:ActivityCode>61885</ct:ActivityCode><ct:DiagnosisCode>G20</ct:DiagnosisCode><RequestedAmount currency=\"AED\">75000.00</RequestedAmount></ServiceRequest></ServiceRequests>
</PriorAuthorizationRequest>""",
        }
        if "Patient_007" in case_type or "diabetes" in case_type:
            return templates["diabetes_cgm"]
        if "Patient_005" in case_type or "osteoarthritis" in case_type:
            return templates["osteoarthritis_knee"]
        if "Patient_011" in case_type or "parkinsons" in case_type:
            return templates["parkinsons_dbs"]
        return templates["diabetes_cgm"]

    def _mock_realistic_workflow(self, orchestrator, expected_outcome: str):
        def mock_intake(*args, **kwargs):
            time.sleep(0.1)
            return MagicMock(
                patient_id="PX",
                services=[{"code": "95250"}],
                diagnoses=[{"code": "E11.9"}],
                total_cost=1200.0,
            )

        def mock_clinical(*args, **kwargs):
            time.sleep(0.3)
            return MagicMock(
                patient_id="PX", age=45, egfr_latest=85.0, data_completeness_score=0.9
            )

        def mock_safety(*args, **kwargs):
            time.sleep(0.2)
            mapping = {
                "APPROVE": RiskLevel.LOW,
                "REVIEW": RiskLevel.MODERATE,
                "DENY": RiskLevel.HIGH,
            }
            return MagicMock(
                overall_risk_level=mapping.get(expected_outcome, RiskLevel.MODERATE),
                total_alerts=0,
                contraindications=0,
            )

        def mock_policy(*args, **kwargs):
            time.sleep(0.4)
            conf = {"APPROVE": 0.95, "REVIEW": 0.6, "DENY": 0.7}
            return MagicMock(
                decision=expected_outcome,
                confidence_score=conf.get(expected_outcome, 0.8),
                met_criteria=3,
                total_criteria=3,
                missing_documentation=[],
            )

        def mock_decision(*args, **kwargs):
            time.sleep(0.1)
            return MagicMock(
                outcome=expected_outcome,
                confidence_score=0.9 if expected_outcome == "APPROVE" else 0.7,
                authorization_amount=1200.0 if expected_outcome == "APPROVE" else 0.0,
            )

        def mock_dossier(*args, **kwargs):
            time.sleep(0.2)
            return f"<html><body>Dossier for {expected_outcome} case</body></html>"

        with patch.object(orchestrator, "intake_processor") as mi, patch.object(
            orchestrator, "clinical_aggregator"
        ) as mc, patch.object(orchestrator, "safety_checker") as ms, patch.object(
            orchestrator, "policy_engine"
        ) as mp, patch.object(orchestrator, "decision_engine") as md, patch.object(
            orchestrator, "dossier_generator"
        ) as mdoc:
            mi.process_pa_request = mock_intake
            mc.build_clinical_summary = mock_clinical
            ms.run_basic_safety_checks = mock_safety
            mp.evaluate_request = mock_policy
            md.synthesize_decision = mock_decision
            mdoc.generate_dossier = mock_dossier


@pytest.mark.performance
class TestScalabilityAndStress:
    """Test system scalability and stress handling."""

    def test_high_volume_processing(self, performance_monitor):
        """Test processing high volume of requests."""
        with patch(
            "preauth_system.orchestrator.PreAuthOrchestrator"
        ) as MockOrchestrator:
            orchestrator = MockOrchestrator.return_value

            # Mock fast processing
            def mock_process(xml_data):
                time.sleep(0.05)  # Very fast processing
                return {
                    "decision": {"outcome": "APPROVE", "confidence_score": 0.85},
                    "processing_time": 0.05,
                    "estimated_cost": 0.02,
                }

            orchestrator.process_request = mock_process

            performance_monitor.start()

            # Process high volume
            results = []
            for i in range(100):
                xml_data = f"<test>request_{i}</test>"
                result = orchestrator.process_request(xml_content=xml_data)
                results.append(result)

            performance_monitor.stop()

            # Verify all processed successfully
            assert len(results) == 100
            assert all("decision" in result for result in results)

            # Performance should remain reasonable even at scale
            performance_monitor.assert_performance(max_time=15.0, max_memory_mb=200.0)

    def test_memory_leak_detection(self, performance_monitor):
        """Test for memory leaks during extended processing."""
        with patch(
            "preauth_system.orchestrator.PreAuthOrchestrator"
        ) as MockOrchestrator:
            orchestrator = MockOrchestrator.return_value

            # Mock processing that might accumulate data
            request_count = 0

            def mock_process_with_accumulation(xml_data):
                nonlocal request_count
                request_count += 1
                # Simulate some data accumulation
                dummy_data = [i for i in range(100)]  # Small data per request
                return {
                    "decision": {"outcome": "APPROVE"},
                    "processing_time": 0.1,
                    "request_count": request_count,
                    "dummy_data": dummy_data,
                }

            orchestrator.process_request = mock_process_with_accumulation

            performance_monitor.start()

            # Extended processing to detect memory leaks
            for i in range(50):
                xml_data = f"<leak_test>request_{i}</leak_test>"
                result = orchestrator.process_request(xml_content=xml_data)
                assert "decision" in result

            performance_monitor.stop()

            # Memory usage should not be excessive
            peak_memory = performance_monitor.memory_usage_mb
            assert (
                peak_memory < 100.0
            ), f"Potential memory leak - peak usage {peak_memory:.1f}MB"

    def test_error_recovery_performance(self):
        """Test performance of error recovery mechanisms."""
        with patch(
            "preauth_system.orchestrator.PreAuthOrchestrator"
        ) as MockOrchestrator:
            orchestrator = MockOrchestrator.return_value

            error_count = 0
            success_count = 0

            def mock_process_with_errors(xml_data):
                nonlocal error_count, success_count

                # Simulate 20% error rate
                if error_count < 2 and (error_count + success_count) % 5 == 0:
                    error_count += 1
                    time.sleep(0.5)  # Error handling overhead
                    return {
                        "decision": {"outcome": "REVIEW", "confidence_score": 0.1},
                        "processing_time": 0.5,
                        "errors": ["Simulated processing error"],
                    }
                else:
                    success_count += 1
                    time.sleep(0.1)  # Normal processing
                    return {
                        "decision": {"outcome": "APPROVE", "confidence_score": 0.9},
                        "processing_time": 0.1,
                        "estimated_cost": 0.03,
                    }

            orchestrator.process_request = mock_process_with_errors

            # Process requests with mixed success/error
            start_time = time.time()
            results = []

            for i in range(10):
                xml_data = f"<error_test>request_{i}</error_test>"
                result = orchestrator.process_request(xml_content=xml_data)
                results.append(result)

            total_time = time.time() - start_time

            # Verify error handling
            assert len(results) == 10
            error_results = [r for r in results if r.get("errors")]
            success_results = [r for r in results if not r.get("errors")]

            assert len(error_results) > 0, "Should have some error cases"
            assert len(success_results) > 0, "Should have some success cases"

            # Performance should degrade gracefully with errors
            avg_time = total_time / len(results)
            assert (
                avg_time < 1.0
            ), f"Error recovery too slow - avg {avg_time:.2f}s per request"


@pytest.mark.performance
class TestCacheEffectiveness:
    """Test caching effectiveness and performance."""

    def test_cache_hit_rate_optimization(self):
        """Test cache hit rate and performance improvement."""
        with patch(
            "preauth_system.orchestrator.PreAuthOrchestrator"
        ) as MockOrchestrator:
            orchestrator = MockOrchestrator.return_value

            # Simulate cache with hit tracking
            cache = {}
            cache_hits = 0
            cache_misses = 0

            def mock_process_with_cache(xml_data):
                nonlocal cache_hits, cache_misses

                # Simple hash for caching
                cache_key = hash(xml_data)

                if cache_key in cache:
                    cache_hits += 1
                    time.sleep(0.01)  # Very fast cache hit
                    return cache[cache_key]
                else:
                    cache_misses += 1
                    time.sleep(0.5)  # Slow cache miss processing
                    result = {
                        "decision": {"outcome": "APPROVE", "confidence_score": 0.85},
                        "processing_time": 0.5 if cache_key not in cache else 0.01,
                        "cached": cache_key in cache,
                    }
                    cache[cache_key] = result
                    return result

            orchestrator.process_request = mock_process_with_cache

            # Test with repeated requests (should hit cache)
            test_requests = [
                "<test>request_A</test>",
                "<test>request_B</test>",
                "<test>request_A</test>",  # Repeat
                "<test>request_C</test>",
                "<test>request_A</test>",  # Repeat
                "<test>request_B</test>",  # Repeat
            ]

            results = []
            for xml_data in test_requests:
                result = orchestrator.process_request(xml_content=xml_data)
                results.append(result)

            # Verify cache effectiveness
            assert cache_hits > 0, "Cache should have hits"
            assert cache_misses > 0, "Cache should have misses"

            cache_hit_rate = cache_hits / (cache_hits + cache_misses)
            assert cache_hit_rate >= 0.4, f"Cache hit rate {cache_hit_rate:.1%} too low"

            # Performance should improve with cache hits
            cached_results = [r for r in results if r.get("cached")]
            uncached_results = [r for r in results if not r.get("cached")]

            if cached_results:
                avg_cached_time = sum(
                    r["processing_time"] for r in cached_results
                ) / len(cached_results)
                assert (
                    avg_cached_time < 0.1
                ), f"Cached requests too slow: {avg_cached_time:.3f}s"

            print(
                f"Cache performance - Hit rate: {cache_hit_rate:.1%}, Hits: {cache_hits}, Misses: {cache_misses}"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "performance"])
