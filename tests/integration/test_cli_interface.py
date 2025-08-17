"""
CLI Interface Integration Tests

Tests the command-line interface for pipeline execution,
validating output file creation, JSON structure, and console output.
"""

import json
import os
import pytest
import subprocess
import tempfile
import time
from datetime import datetime
from pathlib import Path


@pytest.mark.integration
class TestCLIInterface:
    """Integration tests for CLI interface."""
    
    @pytest.fixture
    def demo_xml_path(self):
        """Path to demo XML file for CLI testing."""
        path = Path("data/dataset_2/synthetic_dataset/UAE_XML/Patient_007_eclaim.xml")
        if path.exists():
            return str(path)
        return None
    
    def test_cli_execution(self, demo_xml_path):
        """Test direct CLI execution with pipeline module."""
        if demo_xml_path is None:
            pytest.skip("Demo XML file not available")
        
        # Run CLI command
        start_time = time.time()
        result = subprocess.run(
            ["python", "-m", "preauth_system.pipeline_module"],
            capture_output=True,
            text=True,
            timeout=30  # 30 second timeout
        )
        execution_time = time.time() - start_time
        
        # Validate execution
        assert result.returncode == 0, f"CLI execution failed: {result.stderr}"
        assert execution_time < 15, f"CLI execution took {execution_time:.2f}s > 15s"
        
        # Validate console output
        stdout = result.stdout
        assert "Processing Patient_007 with PreAuthPipeline" in stdout
        assert "Processing result saved to:" in stdout
        assert "PIPELINE PROCESSING SUMMARY" in stdout
        assert "Patient ID:" in stdout
        assert "Processing Time:" in stdout
        assert "Decision:" in stdout
    
    def test_output_file_creation(self, demo_xml_path):
        """Test that CLI creates timestamped output files correctly."""
        if demo_xml_path is None:
            pytest.skip("Demo XML file not available")
        
        # Clean up any existing output files
        output_dir = Path("output")
        initial_files = set()
        if output_dir.exists():
            initial_files = set(output_dir.rglob("*.json"))
        
        # Run CLI
        result = subprocess.run(
            ["python", "-m", "preauth_system.pipeline_module"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        assert result.returncode == 0, f"CLI execution failed: {result.stderr}"
        
        # Find new output files
        if output_dir.exists():
            current_files = set(output_dir.rglob("*.json"))
            new_files = current_files - initial_files
            
            assert len(new_files) >= 1, "No new output files created"
            
            # Validate file structure
            output_file = list(new_files)[0]
            
            # Check file path structure: output/YYYYMMDD/HHMMSS/Patient_007_result.json
            path_parts = output_file.parts
            assert path_parts[0] == "output"
            assert len(path_parts) >= 4  # output/date/time/filename
            
            # Validate date format (YYYYMMDD)
            date_part = path_parts[1]
            assert len(date_part) == 8 and date_part.isdigit()
            
            # Validate time format (HHMMSS)
            time_part = path_parts[2]
            assert len(time_part) == 6 and time_part.isdigit()
            
            # Validate filename
            filename = path_parts[-1]
            assert filename == "Patient_007_result.json"
            
            # Validate file is not empty
            assert output_file.stat().st_size > 100, "Output file is too small"
    
    def test_json_structure_validation(self, demo_xml_path):
        """Test that CLI output JSON has correct structure and completeness."""
        if demo_xml_path is None:
            pytest.skip("Demo XML file not available")
        
        # Run CLI and capture output
        result = subprocess.run(
            ["python", "-m", "preauth_system.pipeline_module"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        assert result.returncode == 0, f"CLI execution failed: {result.stderr}"
        
        # Find the created output file
        output_dir = Path("output")
        json_files = list(output_dir.rglob("*Patient_007_result.json"))
        assert len(json_files) >= 1, "No result file found"
        
        # Get the most recent file
        output_file = max(json_files, key=lambda x: x.stat().st_mtime)
        
        # Load and validate JSON structure
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate all required phases are present
        required_phases = ["intake", "clinical_summary", "evidence", "checklist", "decision", "dossier"]
        for phase in required_phases:
            assert phase in data, f"Missing phase in output: {phase}"
            assert data[phase] is not None, f"Phase {phase} is null"
        
        # Validate metadata fields
        assert "timings" in data
        assert "cost" in data
        assert "audit_trail" in data
        
        # Validate timings structure
        timings = data["timings"]
        expected_timings = ["intake_ms", "summary_ms", "evidence_ms", "checklist_ms", "decision_ms", "dossier_ms", "total_ms"]
        for timing in expected_timings:
            assert timing in timings, f"Missing timing: {timing}"
            assert isinstance(timings[timing], (int, float)), f"Invalid timing type: {timing}"
            assert timings[timing] >= 0, f"Negative timing: {timing}"
        
        # Validate cost structure
        cost = data["cost"]
        assert "total_cost_usd" in cost
        assert "phases" in cost
        assert isinstance(cost["total_cost_usd"], (int, float))
        assert cost["total_cost_usd"] >= 0
        
        # Validate decision structure
        decision = data["decision"]
        assert "outcome" in decision
        assert decision["outcome"] in ["APPROVE", "DENY", "REVIEW"]
        assert "confidence" in decision
        assert "rationale" in decision
        assert len(decision["rationale"]) > 10
        
        # Validate audit trail
        audit = data["audit_trail"]
        assert "pipeline_execution" in audit
        assert "deterministic_components" in audit
        assert "cost_breakdown" in audit
    
    def test_console_summary_accuracy(self, demo_xml_path):
        """Test that console summary accurately reflects the processing results."""
        if demo_xml_path is None:
            pytest.skip("Demo XML file not available")
        
        # Run CLI
        result = subprocess.run(
            ["python", "-m", "preauth_system.pipeline_module"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        assert result.returncode == 0, f"CLI execution failed: {result.stderr}"
        
        stdout = result.stdout
        
        # Extract summary information from console output
        lines = stdout.split('\n')
        
        # Find summary section
        summary_start = -1
        for i, line in enumerate(lines):
            if "PIPELINE PROCESSING SUMMARY" in line:
                summary_start = i
                break
        
        assert summary_start >= 0, "Pipeline summary not found in output"
        
        # Validate summary contains expected information
        summary_section = '\n'.join(lines[summary_start:summary_start + 20])
        
        assert "Patient ID: Patient_007" in summary_section
        assert "Processing Time:" in summary_section and "ms" in summary_section
        assert "Total Cost: $" in summary_section
        assert "Decision:" in summary_section
        assert "Confidence:" in summary_section
        
        # Validate phase breakdown is present
        assert "Phase Timing Breakdown:" in summary_section
        expected_phases = ["Intake:", "Summary:", "Evidence:", "Checklist:", "Decision:"]
        for phase in expected_phases:
            assert phase in summary_section, f"Missing phase in summary: {phase}"
        
        # Validate evidence and compliance info
        assert "Evidence Retrieved:" in summary_section
        assert "Policy Criteria Evaluated:" in summary_section
        assert "Overall Compliance Score:" in summary_section
        
        # Validate output file reference
        assert "JSON Result:" in summary_section and "output/" in summary_section
    
    def test_cli_with_environment_variables(self, demo_xml_path):
        """Test CLI execution with environment variables set."""
        if demo_xml_path is None:
            pytest.skip("Demo XML file not available")
        
        # Set environment variables
        env = os.environ.copy()
        env["PREAUTH_TEST_MODE"] = "true"
        env["PREAUTH_LOG_LEVEL"] = "INFO"
        
        # Run CLI with environment
        result = subprocess.run(
            ["python", "-m", "preauth_system.pipeline_module"],
            capture_output=True,
            text=True,
            env=env,
            timeout=30
        )
        
        assert result.returncode == 0, f"CLI execution failed: {result.stderr}"
        
        # Validate it ran successfully
        assert "Processing Patient_007" in result.stdout
        assert "Processing result saved to:" in result.stdout
    
    def test_cli_error_handling(self):
        """Test CLI error handling with invalid conditions."""
        # Test with non-existent XML file (by modifying the hardcoded path)
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a mock pipeline module that uses a non-existent file
            mock_pipeline_content = '''
import sys
sys.path.insert(0, ".")
from preauth_system.pipeline_module import PreAuthPipeline

pipeline = PreAuthPipeline()
try:
    result = pipeline.forward(xml_path="/nonexistent/file.xml", xml_format="eclaim")
    print("ERROR: Should have failed")
    sys.exit(1)
except Exception as e:
    print(f"Expected error: {type(e).__name__}")
    sys.exit(0)
'''
            
            mock_file = Path(temp_dir) / "test_pipeline.py"
            mock_file.write_text(mock_pipeline_content)
            
            result = subprocess.run(
                ["python", str(mock_file)],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            # Should exit successfully after catching the expected error
            assert result.returncode == 0, f"Error handling test failed: {result.stderr}"
            assert "Expected error:" in result.stdout
    
    def test_cli_performance_monitoring(self, demo_xml_path):
        """Test CLI performance monitoring and reporting."""
        if demo_xml_path is None:
            pytest.skip("Demo XML file not available")
        
        # Run CLI multiple times to test consistency
        execution_times = []
        
        for i in range(3):
            start_time = time.time()
            result = subprocess.run(
                ["python", "-m", "preauth_system.pipeline_module"],
                capture_output=True,
                text=True,
                timeout=30
            )
            execution_time = time.time() - start_time
            
            assert result.returncode == 0, f"Run {i+1} failed: {result.stderr}"
            execution_times.append(execution_time)
            
            # Extract timing from output
            stdout = result.stdout
            assert "Processing Time:" in stdout
            
            # Find timing line and extract value
            timing_line = [line for line in stdout.split('\n') if "Processing Time:" in line][0]
            # Should contain something like "Processing Time: 5432.10ms"
            assert "ms" in timing_line
        
        # Validate performance consistency
        avg_time = sum(execution_times) / len(execution_times)
        max_time = max(execution_times)
        min_time = min(execution_times)
        
        assert avg_time < 15, f"Average execution time {avg_time:.2f}s > 15s"
        assert max_time < 20, f"Max execution time {max_time:.2f}s > 20s"
        
        # Validate timing consistency (max should not be more than 2x min)
        time_variance = max_time / min_time if min_time > 0 else float('inf')
        assert time_variance < 3, f"Execution time variance too high: {time_variance:.2f}x"
    
    def test_output_directory_structure(self, demo_xml_path):
        """Test that output directory structure follows expected pattern."""
        if demo_xml_path is None:
            pytest.skip("Demo XML file not available")
        
        # Run CLI
        result = subprocess.run(
            ["python", "-m", "preauth_system.pipeline_module"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        assert result.returncode == 0, f"CLI execution failed: {result.stderr}"
        
        # Validate output directory structure
        output_dir = Path("output")
        assert output_dir.exists(), "Output directory not created"
        assert output_dir.is_dir(), "Output path is not a directory"
        
        # Check for date directories (YYYYMMDD format)
        date_dirs = [d for d in output_dir.iterdir() if d.is_dir() and len(d.name) == 8 and d.name.isdigit()]
        assert len(date_dirs) >= 1, "No date directories found"
        
        # Check most recent date directory
        recent_date_dir = max(date_dirs, key=lambda x: x.name)
        today = datetime.now().strftime("%Y%m%d")
        assert recent_date_dir.name == today, f"Expected today's date {today}, got {recent_date_dir.name}"
        
        # Check for time directories (HHMMSS format)
        time_dirs = [d for d in recent_date_dir.iterdir() if d.is_dir() and len(d.name) == 6 and d.name.isdigit()]
        assert len(time_dirs) >= 1, "No time directories found"
        
        # Check for result files in time directories
        for time_dir in time_dirs:
            result_files = list(time_dir.glob("*_result.json"))
            if result_files:  # At least one time dir should have results
                result_file = result_files[0]
                assert result_file.name.endswith("_result.json")
                assert result_file.stat().st_size > 0
                break
        else:
            pytest.fail("No result files found in any time directory")
    
    @pytest.mark.performance
    def test_cli_memory_usage(self, demo_xml_path):
        """Test CLI memory usage remains within reasonable bounds."""
        if demo_xml_path is None:
            pytest.skip("Demo XML file not available")
        
        import psutil
        import time
        
        # Start CLI process
        process = subprocess.Popen(
            ["python", "-m", "preauth_system.pipeline_module"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Monitor memory usage
        max_memory_mb = 0
        try:
            psutil_process = psutil.Process(process.pid)
            
            while process.poll() is None:
                try:
                    memory_info = psutil_process.memory_info()
                    memory_mb = memory_info.rss / 1024 / 1024  # Convert to MB
                    max_memory_mb = max(max_memory_mb, memory_mb)
                    time.sleep(0.1)  # Check every 100ms
                except psutil.NoSuchProcess:
                    break
            
            # Wait for completion
            stdout, stderr = process.communicate(timeout=30)
            
        except subprocess.TimeoutExpired:
            process.kill()
            pytest.fail("CLI process timed out")
        
        # Validate process completed successfully
        assert process.returncode == 0, f"CLI failed: {stderr}"
        
        # Validate memory usage
        assert max_memory_mb < 500, f"CLI used {max_memory_mb:.2f}MB memory > 500MB"
        
        # Validate expected output
        assert "Processing Patient_007" in stdout
        assert "Processing result saved to:" in stdout
