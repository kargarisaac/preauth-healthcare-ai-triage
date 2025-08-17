#!/usr/bin/env python3
"""
Insurer Workflow Test Runner

Comprehensive test execution script for validating the complete
insurer workflow implementation.
"""

import sys
import os
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Any


class InsurerWorkflowTestRunner:
    """Test runner for comprehensive insurer workflow validation."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_results = {}
        self.start_time = time.time()
    
    def run_test_suite(self, test_file: str, markers: List[str] = None) -> Dict[str, Any]:
        """Run a specific test suite and return results."""
        print(f"\n{'='*60}")
        print(f"Running {test_file}")
        print(f"{'='*60}")
        
        cmd = ["python", "-m", "pytest", f"tests/{test_file}", "-v", "--tb=short"]
        
        if markers:
            cmd.extend(["-m", " and ".join(markers)])
        
        # Add coverage if available
        try:
            import coverage
            cmd.extend(["--cov=api", "--cov=preauth_system"])
        except ImportError:
            pass
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            duration = time.time() - start_time
            
            return {
                "success": result.returncode == 0,
                "duration": duration,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "duration": time.time() - start_time,
                "stdout": "",
                "stderr": "Test suite timed out after 10 minutes",
                "return_code": -1
            }
        except Exception as e:
            return {
                "success": False,
                "duration": time.time() - start_time,
                "stdout": "",
                "stderr": f"Failed to run tests: {e}",
                "return_code": -2
            }
    
    def check_prerequisites(self) -> bool:
        """Check if prerequisites are met for running tests."""
        print("Checking prerequisites...")
        
        # Check if we're in the right directory
        if not (self.project_root / "api" / "main.py").exists():
            print("❌ Error: Not in the correct project directory")
            return False
        
        # Check if virtual environment is activated (optional but recommended)
        if "VIRTUAL_ENV" not in os.environ:
            print("⚠️  Warning: No virtual environment detected")
        
        # Check if required packages are available
        required_packages = ["pytest", "fastapi", "pydantic"]
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            print(f"❌ Error: Missing required packages: {', '.join(missing_packages)}")
            print("Run: uv pip install -e . or pip install -r requirements.txt")
            return False
        
        print("✅ Prerequisites check passed")
        return True
    
    def run_all_tests(self):
        """Run comprehensive insurer workflow test suite."""
        if not self.check_prerequisites():
            sys.exit(1)
        
        print(f"\n🚀 Starting Comprehensive Insurer Workflow Testing")
        print(f"📁 Project Root: {self.project_root}")
        print(f"⏰ Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test suites to run in order
        test_suites = [
            {
                "name": "API Contract Tests",
                "file": "integration/test_insurer_api_contracts.py",
                "markers": ["integration"],
                "description": "Validate API contracts and response formats"
            },
            {
                "name": "Complete Workflow Tests",
                "file": "integration/test_insurer_workflow_complete.py", 
                "markers": ["integration"],
                "description": "End-to-end workflow validation"
            },
            {
                "name": "Performance Tests",
                "file": "performance/test_insurer_workflow_performance.py",
                "markers": ["performance"],
                "description": "Performance and scalability testing"
            },
            {
                "name": "Existing API Tests",
                "file": "integration/test_api_endpoints.py",
                "markers": ["integration"],
                "description": "Core API endpoint validation"
            }
        ]
        
        # Run each test suite
        for suite in test_suites:
            print(f"\n📋 {suite['name']}")
            print(f"📄 {suite['description']}")
            
            result = self.run_test_suite(suite["file"], suite.get("markers"))
            self.test_results[suite["name"]] = result
            
            if result["success"]:
                print(f"✅ {suite['name']} PASSED ({result['duration']:.1f}s)")
            else:
                print(f"❌ {suite['name']} FAILED ({result['duration']:.1f}s)")
                print(f"Return code: {result['return_code']}")
                
                if result["stderr"]:
                    print(f"Error output:\n{result['stderr']}")
                
                # Show last 20 lines of stdout for context
                stdout_lines = result["stdout"].split('\n')
                if len(stdout_lines) > 20:
                    print(f"Last 20 lines of output:")
                    print('\n'.join(stdout_lines[-20:]))
                elif result["stdout"]:
                    print(f"Output:\n{result['stdout']}")
        
        # Generate summary report
        self.generate_summary_report()
    
    def generate_summary_report(self):
        """Generate final test execution summary."""
        total_duration = time.time() - self.start_time
        passed_suites = sum(1 for result in self.test_results.values() if result["success"])
        total_suites = len(self.test_results)
        
        print(f"\n{'='*80}")
        print(f"📊 INSURER WORKFLOW TEST SUMMARY")
        print(f"{'='*80}")
        
        print(f"⏱️  Total Execution Time: {total_duration:.1f} seconds")
        print(f"📈 Test Suites Passed: {passed_suites}/{total_suites}")
        print(f"🎯 Success Rate: {(passed_suites/total_suites)*100:.1f}%")
        
        print(f"\n📋 Detailed Results:")
        print(f"{'Test Suite':<30} {'Status':<10} {'Duration':<10} {'Details'}")
        print(f"{'-'*70}")
        
        for suite_name, result in self.test_results.items():
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            duration = f"{result['duration']:.1f}s"
            details = f"RC: {result['return_code']}"
            
            print(f"{suite_name:<30} {status:<10} {duration:<10} {details}")
        
        # Performance summary if available
        perf_result = self.test_results.get("Performance Tests")
        if perf_result and perf_result["success"]:
            print(f"\n🚀 Performance Highlights:")
            print(f"   • All performance thresholds met")
            print(f"   • System ready for production load")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        
        failed_suites = [name for name, result in self.test_results.items() if not result["success"]]
        if failed_suites:
            print(f"   • Review and fix failing test suites: {', '.join(failed_suites)}")
            print(f"   • Check error logs above for specific issues")
        else:
            print(f"   • ✅ All tests passed! Insurer workflow is ready for deployment")
            print(f"   • Consider running tests with real data for final validation")
        
        print(f"\n📝 Next Steps:")
        if passed_suites == total_suites:
            print(f"   1. ✅ Deploy insurer workflow to staging environment")
            print(f"   2. ✅ Conduct user acceptance testing with medical directors")
            print(f"   3. ✅ Prepare production deployment")
        else:
            print(f"   1. 🔧 Fix failing tests identified above")
            print(f"   2. 🔄 Re-run test suite to confirm fixes")
            print(f"   3. 📊 Review performance metrics if applicable")
        
        print(f"\n{'='*80}")
        
        # Exit with appropriate code
        if passed_suites == total_suites:
            print(f"🎉 ALL TESTS PASSED - INSURER WORKFLOW VALIDATED!")
            sys.exit(0)
        else:
            print(f"⚠️  SOME TESTS FAILED - REVIEW REQUIRED")
            sys.exit(1)
    
    def run_quick_smoke_test(self):
        """Run quick smoke test for basic functionality."""
        print(f"\n🔥 Running Quick Smoke Test")
        
        smoke_tests = [
            {
                "name": "API Health Check",
                "file": "integration/test_api_endpoints.py::TestAPIEndpoints::test_health_endpoint_with_pipeline_validation"
            },
            {
                "name": "Basic Workflow",
                "file": "integration/test_insurer_workflow_complete.py::TestInsurerWorkflowComplete::test_request_inbox_filtering_and_pagination"
            }
        ]
        
        all_passed = True
        
        for test in smoke_tests:
            print(f"Running {test['name']}...")
            
            cmd = ["python", "-m", "pytest", f"tests/{test['file']}", "-v"]
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True)
            
            if result.returncode == 0:
                print(f"✅ {test['name']} passed")
            else:
                print(f"❌ {test['name']} failed")
                all_passed = False
        
        if all_passed:
            print(f"🎉 Smoke test passed! System basic functionality verified.")
        else:
            print(f"⚠️  Smoke test failed! Check system configuration.")
            sys.exit(1)


def main():
    """Main entry point."""
    runner = InsurerWorkflowTestRunner()
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--smoke":
            runner.run_quick_smoke_test()
        elif sys.argv[1] == "--help":
            print("Insurer Workflow Test Runner")
            print("Usage:")
            print("  python tests/run_insurer_workflow_tests.py           # Run all tests")
            print("  python tests/run_insurer_workflow_tests.py --smoke   # Run smoke tests only")
            print("  python tests/run_insurer_workflow_tests.py --help    # Show this help")
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            print("Use --help for usage information")
            sys.exit(1)
    else:
        runner.run_all_tests()


if __name__ == "__main__":
    main()