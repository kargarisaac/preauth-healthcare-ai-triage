"""
Comprehensive Integration Tests for PreAuth Pipeline Milestones

Tests the complete pipeline flow from XML input to JSON output,
validating all 6 phases with performance and quality targets.
"""

import json
import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

from preauth_system.pipeline_module import PreAuthPipeline


@pytest.mark.integration
class TestPipelineIntegration:
    """Integration tests for complete pipeline workflow."""
    
    @pytest.fixture
    def demo_xml_paths(self):
        """Provide paths to demo patient XML files."""
        base_path = Path("data/dataset_2/synthetic_dataset/UAE_XML")
        return {
            "patient_007": base_path / "Patient_007_eclaim.xml",
            "patient_005": base_path / "Patient_005_eclaim.xml", 
            "patient_011": base_path / "Patient_011_eclaim.xml"
        }
    
    @pytest.fixture
    def pipeline(self):
        """Create pipeline instance for testing."""
        return PreAuthPipeline()
    
    def test_complete_pipeline_patient_007(self, pipeline, demo_xml_paths):
        """Test complete pipeline flow with Patient_007 (diabetes case)."""
        xml_path = demo_xml_paths["patient_007"]
        if not xml_path.exists():
            pytest.skip(f"Demo file not found: {xml_path}")
        
        start_time = time.time()
        result = pipeline.forward(xml_path=str(xml_path), xml_format="eclaim")
        total_time = time.time() - start_time
        
        # Validate all 6 phases are present
        required_phases = ["intake", "clinical_summary", "evidence", "checklist", "decision", "dossier"]
        for phase in required_phases:
            assert phase in result, f"Missing phase: {phase}"
            assert result[phase] is not None, f"Phase {phase} is None"
        
        # Validate intake phase
        intake = result["intake"]
        assert intake["xml_format"] == "eclaim"
        assert "patient_info" in intake
        assert "emirates_id" in intake
        
        # Validate clinical summary
        clinical_summary = result["clinical_summary"]
        assert "executive_summary" in clinical_summary
        assert "confidence" in clinical_summary
        assert 0 <= clinical_summary["confidence"] <= 1
        
        # Validate evidence retrieval
        evidence = result["evidence"]
        assert isinstance(evidence, list)
        
        # Validate policy checklist
        checklist = result["checklist"]
        assert "criteria" in checklist
        assert "overall_compliance_score" in checklist
        assert isinstance(checklist["criteria"], list)
        
        # Validate decision synthesis
        decision = result["decision"]
        assert "outcome" in decision
        assert decision["outcome"] in ["APPROVE", "DENY", "REVIEW"]
        assert "confidence" in decision
        assert "rationale" in decision
        
        # Validate dossier generation
        dossier = result["dossier"]
        assert "executive_summary" in dossier
        assert "sections" in dossier
        assert isinstance(dossier["sections"], list)
        
        # Validate performance targets (adjusted for integration testing)
        timings = result.get("timings", {})
        total_ms = timings.get("total_ms", 0)
        assert total_ms < 60000, f"Pipeline took {total_ms}ms, target: <60000ms (1 minute)"
        
        cost = result.get("cost", {})
        total_cost = cost.get("total_cost_usd", 0)
        assert total_cost < 0.50, f"Pipeline cost ${total_cost}, target: <$0.50"
        
        # Validate audit trail
        assert "audit_trail" in result
        audit = result["audit_trail"]
        assert "pipeline_execution" in audit
        assert "deterministic_components" in audit
    
    def test_pipeline_deterministic_decisions(self, pipeline, demo_xml_paths):
        """Test that pipeline produces deterministic, reproducible results."""
        xml_path = demo_xml_paths["patient_007"]
        if not xml_path.exists():
            pytest.skip(f"Demo file not found: {xml_path}")
        
        # Run pipeline multiple times
        results = []
        for i in range(3):
            result = pipeline.forward(xml_path=str(xml_path), xml_format="eclaim")
            results.append(result)
        
        # Validate deterministic outcomes
        first_decision = results[0]["decision"]["outcome"]
        first_confidence = results[0]["decision"]["confidence"]
        first_compliance = results[0]["checklist"]["overall_compliance_score"]
        
        for i, result in enumerate(results[1:], 1):
            decision = result["decision"]
            checklist = result["checklist"]
            
            assert decision["outcome"] == first_decision, f"Run {i+1} decision differs"
            assert decision["confidence"] == first_confidence, f"Run {i+1} confidence differs"
            assert checklist["overall_compliance_score"] == first_compliance, f"Run {i+1} compliance differs"
    
    def test_pipeline_performance_targets(self, pipeline, demo_xml_paths):
        """Test that pipeline meets performance targets across all demo cases."""
        performance_results = []
        
        for patient_id, xml_path in demo_xml_paths.items():
            if not xml_path.exists():
                continue
                
            start_time = time.time()
            result = pipeline.forward(xml_path=str(xml_path), xml_format="eclaim")
            execution_time = time.time() - start_time
            
            timings = result.get("timings", {})
            cost = result.get("cost", {})
            
            performance_results.append({
                "patient_id": patient_id,
                "execution_time_s": execution_time,
                "total_ms": timings.get("total_ms", 0),
                "total_cost_usd": cost.get("total_cost_usd", 0),
                "decision": result["decision"]["outcome"]
            })
        
        # Validate performance across all cases
        assert len(performance_results) >= 2, "Need at least 2 demo cases for validation"
        
        for perf in performance_results:
            # Timing targets (adjusted for integration testing)
            assert perf["execution_time_s"] < 120, f"{perf['patient_id']}: {perf['execution_time_s']:.2f}s > 120s"
            assert perf["total_ms"] < 90000, f"{perf['patient_id']}: {perf['total_ms']:.2f}ms > 90000ms"
            
            # Cost targets (adjusted for LLM calls)
            assert perf["total_cost_usd"] < 1.0, f"{perf['patient_id']}: ${perf['total_cost_usd']:.4f} > $1.00"
            
            # Decision validity
            assert perf["decision"] in ["APPROVE", "DENY", "REVIEW"], f"Invalid decision: {perf['decision']}"
    
    def test_pipeline_all_phases_complete(self, pipeline, demo_xml_paths):
        """Test that all phases complete successfully and have expected content."""
        xml_path = demo_xml_paths["patient_007"]
        if not xml_path.exists():
            pytest.skip(f"Demo file not found: {xml_path}")
        
        result = pipeline.forward(xml_path=str(xml_path), xml_format="eclaim")
        
        # Phase 1: Intake
        intake = result["intake"]
        assert "xml_path" in intake
        assert "patient_info" in intake
        assert isinstance(intake["patient_info"], dict)
        
        # Phase 2: Clinical Summary
        clinical_summary = result["clinical_summary"]
        assert len(clinical_summary.get("executive_summary", "")) > 10
        assert "patient_profile" in clinical_summary
        
        # Phase 3: Evidence Retrieval
        evidence = result["evidence"]
        assert isinstance(evidence, list)
        # Evidence may be empty in deterministic mode, that's OK
        
        # Phase 4: Policy Checklist
        checklist = result["checklist"]
        assert "criteria" in checklist
        assert "overall_compliance_score" in checklist
        assert 0 <= checklist["overall_compliance_score"] <= 1
        
        # Phase 5: Decision Synthesis
        decision = result["decision"]
        assert "outcome" in decision
        assert "rationale" in decision
        assert len(decision["rationale"]) > 20
        assert "audit_trail" in decision
        
        # Phase 6: Dossier Generation
        dossier = result["dossier"]
        assert "executive_summary" in dossier
        assert "sections" in dossier
        assert len(dossier["sections"]) >= 1
        for section in dossier["sections"]:
            assert "title" in section
            assert "content" in section
    
    def test_pipeline_error_handling(self, pipeline):
        """Test pipeline graceful error handling with invalid inputs."""
        # Test with non-existent file
        with pytest.raises(Exception):  # Should raise some kind of error
            pipeline.forward(xml_path="/nonexistent/file.xml", xml_format="eclaim")
        
        # Test with invalid XML format
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write("<invalid>XML content</invalid>")
            f.flush()
            
            # Should not crash, but handle gracefully
            result = pipeline.forward(xml_path=f.name, xml_format="eclaim")
            
            # Basic structure should still be present even with errors
            assert "intake" in result
            assert "timings" in result
            assert "cost" in result
    
    def test_pipeline_timing_breakdown(self, pipeline, demo_xml_paths):
        """Test detailed timing breakdown for performance optimization."""
        xml_path = demo_xml_paths["patient_007"]
        if not xml_path.exists():
            pytest.skip(f"Demo file not found: {xml_path}")
        
        result = pipeline.forward(xml_path=str(xml_path), xml_format="eclaim")
        timings = result["timings"]
        
        # Validate all timing components are present
        expected_timings = [
            "intake_ms", "summary_ms", "evidence_ms", 
            "checklist_ms", "decision_ms", "dossier_ms", "total_ms"
        ]
        
        for timing_key in expected_timings:
            assert timing_key in timings, f"Missing timing: {timing_key}"
            assert timings[timing_key] >= 0, f"Negative timing: {timing_key}"
        
        # Validate decision timing breakdown
        assert "decision_criteria_analysis_ms" in timings
        assert "decision_rule_evaluation_ms" in timings
        assert "decision_audit_generation_ms" in timings
        
        # Sum of individual phases should approximately equal total
        phase_sum = sum(timings[key] for key in expected_timings[:-1])  # Exclude total_ms
        total_ms = timings["total_ms"]
        
        # Allow some variance for overhead
        assert abs(phase_sum - total_ms) < total_ms * 0.2, f"Timing mismatch: {phase_sum} vs {total_ms}"
    
    def test_pipeline_cost_tracking(self, pipeline, demo_xml_paths):
        """Test detailed cost tracking across all phases."""
        xml_path = demo_xml_paths["patient_007"]
        if not xml_path.exists():
            pytest.skip(f"Demo file not found: {xml_path}")
        
        result = pipeline.forward(xml_path=str(xml_path), xml_format="eclaim")
        cost = result["cost"]
        
        # Validate cost structure
        assert "total_cost_usd" in cost
        assert "phases" in cost
        assert "tokens" in cost
        assert "phase_details" in cost
        
        # Validate phase costs
        phase_costs = cost["phases"]
        total_phase_cost = sum(phase_costs.values())
        assert abs(total_phase_cost - cost["total_cost_usd"]) < 0.001, "Cost calculation mismatch"
        
        # Deterministic phases should have zero cost
        assert phase_costs.get("decision", 0) == 0, "Decision phase should be deterministic (free)"
        
        # Validate token tracking
        tokens = cost["tokens"]
        for phase_name, token_data in tokens.items():
            assert "input_tokens" in token_data
            assert "output_tokens" in token_data
            assert "total_tokens" in token_data
            assert token_data["total_tokens"] >= 0
    
    @pytest.mark.performance
    def test_pipeline_concurrent_execution(self, demo_xml_paths):
        """Test pipeline behavior under concurrent execution (thread safety)."""
        import threading
        import queue
        
        xml_path = demo_xml_paths["patient_007"]
        if not xml_path.exists():
            pytest.skip(f"Demo file not found: {xml_path}")
        
        results_queue = queue.Queue()
        errors_queue = queue.Queue()
        
        def run_pipeline():
            try:
                pipeline = PreAuthPipeline()
                result = pipeline.forward(xml_path=str(xml_path), xml_format="eclaim")
                results_queue.put(result)
            except Exception as e:
                errors_queue.put(e)
        
        # Run 3 concurrent pipeline executions
        threads = []
        for i in range(3):
            thread = threading.Thread(target=run_pipeline)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=30)  # 30 second timeout
        
        # Validate results
        assert errors_queue.empty(), f"Pipeline errors in concurrent execution: {list(errors_queue.queue)}"
        assert results_queue.qsize() == 3, f"Expected 3 results, got {results_queue.qsize()}"
        
        # Validate consistency across concurrent runs
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        first_decision = results[0]["decision"]["outcome"]
        for i, result in enumerate(results[1:], 1):
            assert result["decision"]["outcome"] == first_decision, f"Concurrent run {i+1} decision differs"
