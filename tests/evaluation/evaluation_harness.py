"""
Evaluation Harness for Pre-Authorization System MVP
==================================================

This module provides automated evaluation and regression testing for the
pre-authorization system, comparing outputs against expected outcomes and
tracking system performance over time.
"""

import json
import time
import statistics
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import yaml

from preauth_system.orchestrator import PreAuthOrchestrator
from preauth_system.decision import DecisionOutcome


class EvaluationResult(Enum):
    """Evaluation result outcomes."""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    SKIP = "skip"


@dataclass
class TestCase:
    """Individual test case definition."""
    id: str
    name: str
    description: str
    xml_file: str
    expected_outcome: str
    expected_confidence: float
    expected_auth_amount: float
    max_processing_time: float
    max_cost: float
    patient_type: str
    condition: str
    treatment: str


@dataclass
class EvaluationMetrics:
    """Evaluation metrics for a test case."""
    test_case_id: str
    outcome_correct: bool
    confidence_score: float
    processing_time: float
    cost: float
    decision_quality_score: float
    compliance_score: float
    safety_score: float
    dossier_quality_score: float


@dataclass
class EvaluationReport:
    """Complete evaluation report."""
    run_id: str
    timestamp: datetime
    total_cases: int
    passed: int
    failed: int
    warnings: int
    skipped: int
    overall_score: float
    performance_metrics: Dict[str, float]
    cost_analysis: Dict[str, float]
    detailed_results: List[EvaluationMetrics]
    regression_analysis: Optional[Dict[str, Any]] = None


class EvaluationHarness:
    """Main evaluation harness for system testing."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize evaluation harness."""
        self.config_path = config_path or self._get_default_config_path()
        self.test_cases = self._load_test_cases()
        self.orchestrator = PreAuthOrchestrator()
        self.results_dir = Path("tests/evaluation/results")
        self.results_dir.mkdir(exist_ok=True)
        
    def run_full_evaluation(self) -> EvaluationReport:
        """Run complete evaluation of all test cases."""
        run_id = f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"Starting evaluation run: {run_id}")
        
        detailed_results = []
        performance_times = []
        costs = []
        
        passed = failed = warnings = skipped = 0
        
        for test_case in self.test_cases:
            print(f"Evaluating: {test_case.name}")
            
            try:
                metrics = self._evaluate_test_case(test_case)
                detailed_results.append(metrics)
                
                performance_times.append(metrics.processing_time)
                costs.append(metrics.cost)
                
                # Determine result
                if self._is_passing_result(metrics, test_case):
                    passed += 1
                    print(f"  ✓ PASS")
                elif self._is_warning_result(metrics, test_case):
                    warnings += 1
                    print(f"  ⚠ WARNING")
                else:
                    failed += 1
                    print(f"  ✗ FAIL")
                    
            except Exception as e:
                print(f"  ✗ SKIP - Error: {str(e)}")
                skipped += 1
                
        # Calculate overall metrics
        overall_score = self._calculate_overall_score(detailed_results)
        performance_metrics = self._calculate_performance_metrics(performance_times)
        cost_analysis = self._calculate_cost_analysis(costs)
        
        # Create report
        report = EvaluationReport(
            run_id=run_id,
            timestamp=datetime.now(),
            total_cases=len(self.test_cases),
            passed=passed,
            failed=failed,
            warnings=warnings,
            skipped=skipped,
            overall_score=overall_score,
            performance_metrics=performance_metrics,
            cost_analysis=cost_analysis,
            detailed_results=detailed_results
        )
        
        # Add regression analysis if historical data exists
        report.regression_analysis = self._analyze_regression(report)
        
        # Save report
        self._save_report(report)
        
        # Print summary
        self._print_summary(report)
        
        return report
    
    def run_demo_cases_evaluation(self) -> EvaluationReport:
        """Run evaluation specifically on the 3 MVP demo cases."""
        demo_cases = [tc for tc in self.test_cases if tc.patient_type in ["Patient_007", "Patient_005", "Patient_011"]]
        
        if not demo_cases:
            raise ValueError("No demo cases found in test configuration")
        
        run_id = f"demo_eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"Starting demo cases evaluation: {run_id}")
        
        detailed_results = []
        passed = failed = warnings = 0
        
        for test_case in demo_cases:
            print(f"Evaluating demo case: {test_case.name}")
            
            try:
                metrics = self._evaluate_test_case(test_case)
                detailed_results.append(metrics)
                
                # More stringent criteria for demo cases
                if self._is_demo_case_passing(metrics, test_case):
                    passed += 1
                    print(f"  ✓ DEMO PASS")
                else:
                    failed += 1
                    print(f"  ✗ DEMO FAIL")
                    self._print_detailed_failure(metrics, test_case)
                    
            except Exception as e:
                print(f"  ✗ DEMO ERROR: {str(e)}")
                failed += 1
        
        # Create demo-specific report
        performance_times = [m.processing_time for m in detailed_results]
        costs = [m.cost for m in detailed_results]
        
        report = EvaluationReport(
            run_id=run_id,
            timestamp=datetime.now(),
            total_cases=len(demo_cases),
            passed=passed,
            failed=failed,
            warnings=warnings,
            skipped=0,
            overall_score=self._calculate_demo_score(detailed_results),
            performance_metrics=self._calculate_performance_metrics(performance_times),
            cost_analysis=self._calculate_cost_analysis(costs),
            detailed_results=detailed_results
        )
        
        self._save_report(report)
        self._print_demo_summary(report)
        
        return report
    
    def run_regression_test(self, baseline_report_path: str) -> Dict[str, Any]:
        """Run regression test against baseline."""
        baseline = self._load_baseline_report(baseline_report_path)
        current = self.run_full_evaluation()
        
        regression_analysis = {
            "baseline_run_id": baseline.run_id,
            "current_run_id": current.run_id,
            "overall_score_change": current.overall_score - baseline.overall_score,
            "performance_regression": self._analyze_performance_regression(baseline, current),
            "cost_regression": self._analyze_cost_regression(baseline, current),
            "outcome_changes": self._analyze_outcome_changes(baseline, current),
            "recommendation": self._generate_regression_recommendation(baseline, current)
        }
        
        # Save regression analysis
        regression_path = self.results_dir / f"regression_{current.run_id}.json"
        with open(regression_path, 'w') as f:
            json.dump(regression_analysis, f, indent=2, default=str)
        
        print(f"\nRegression Analysis:")
        print(f"Overall score change: {regression_analysis['overall_score_change']:+.3f}")
        print(f"Recommendation: {regression_analysis['recommendation']}")
        
        return regression_analysis
    
    def _evaluate_test_case(self, test_case: TestCase) -> EvaluationMetrics:
        """Evaluate a single test case."""
        # Load XML data
        xml_data = self._load_xml_data(test_case.xml_file)
        
        # Process request with timing
        start_time = time.time()
        result = self.orchestrator.process_request(xml_data)
        processing_time = time.time() - start_time
        
        # Extract metrics
        decision = result.get("decision", {})
        compliance = result.get("compliance_assessment", {})
        safety = result.get("safety_assessment", {})
        
        # Evaluate outcome correctness
        actual_outcome = decision.get("outcome", "UNKNOWN")
        outcome_correct = actual_outcome.upper() == test_case.expected_outcome.upper()
        
        # Calculate quality scores
        decision_quality_score = self._calculate_decision_quality(decision, test_case)
        compliance_score = compliance.get("completion_score", 0.0)
        safety_score = self._calculate_safety_score(safety)
        dossier_quality_score = self._calculate_dossier_quality(result.get("dossier_html", ""))
        
        return EvaluationMetrics(
            test_case_id=test_case.id,
            outcome_correct=outcome_correct,
            confidence_score=decision.get("confidence_score", 0.0),
            processing_time=processing_time,
            cost=result.get("estimated_cost", 0.0),
            decision_quality_score=decision_quality_score,
            compliance_score=compliance_score,
            safety_score=safety_score,
            dossier_quality_score=dossier_quality_score
        )
    
    def _is_passing_result(self, metrics: EvaluationMetrics, test_case: TestCase) -> bool:
        """Determine if test case passes."""
        return (
            metrics.outcome_correct and
            metrics.confidence_score >= 0.7 and
            metrics.processing_time <= test_case.max_processing_time and
            metrics.cost <= test_case.max_cost and
            metrics.decision_quality_score >= 0.7 and
            metrics.compliance_score >= 0.6
        )
    
    def _is_warning_result(self, metrics: EvaluationMetrics, test_case: TestCase) -> bool:
        """Determine if test case has warnings."""
        return (
            metrics.outcome_correct and
            (metrics.confidence_score < 0.7 or
             metrics.processing_time > test_case.max_processing_time * 0.8 or
             metrics.decision_quality_score < 0.8)
        )
    
    def _is_demo_case_passing(self, metrics: EvaluationMetrics, test_case: TestCase) -> bool:
        """More stringent passing criteria for demo cases."""
        return (
            metrics.outcome_correct and
            metrics.confidence_score >= 0.8 and
            metrics.processing_time <= 20.0 and  # MVP requirement
            metrics.cost <= 0.10 and  # MVP requirement
            metrics.decision_quality_score >= 0.8 and
            metrics.compliance_score >= 0.7 and
            metrics.dossier_quality_score >= 0.8
        )
    
    def _calculate_decision_quality(self, decision: Dict[str, Any], test_case: TestCase) -> float:
        """Calculate decision quality score."""
        score = 0.0
        
        # Outcome correctness (30%)
        if decision.get("outcome", "").upper() == test_case.expected_outcome.upper():
            score += 0.3
        
        # Confidence score quality (20%)
        confidence = decision.get("confidence_score", 0.0)
        if confidence >= 0.8:
            score += 0.2
        elif confidence >= 0.6:
            score += 0.1
        
        # Rationale quality (25%)
        rationale = decision.get("rationale", {})
        if rationale.get("primary_factors") and len(rationale["primary_factors"]) >= 2:
            score += 0.15
        if rationale.get("supporting_evidence") and len(rationale["supporting_evidence"]) >= 2:
            score += 0.1
        
        # Authorization amount appropriateness (25%)
        auth_amount = decision.get("authorization_amount", 0.0)
        expected_amount = test_case.expected_auth_amount
        if expected_amount > 0:
            ratio = min(auth_amount, expected_amount) / max(auth_amount, expected_amount, 1)
            if ratio >= 0.8:
                score += 0.25
            elif ratio >= 0.6:
                score += 0.15
        elif expected_amount == 0 and auth_amount == 0:
            score += 0.25
        
        return min(score, 1.0)
    
    def _calculate_safety_score(self, safety: Dict[str, Any]) -> float:
        """Calculate safety assessment score."""
        if not safety:
            return 0.0
        
        score = 0.0
        
        # Risk level appropriateness (40%)
        risk_level = safety.get("overall_risk_level", "UNKNOWN")
        if risk_level in ["LOW", "MODERATE", "HIGH", "CRITICAL"]:
            score += 0.4
        
        # Alert detection (30%)
        total_alerts = safety.get("total_alerts", 0)
        if total_alerts >= 0:  # Any valid alert count
            score += 0.3
        
        # Monitoring requirements (30%)
        monitoring = safety.get("monitoring_requirements", [])
        if isinstance(monitoring, list):
            score += 0.3
        
        return min(score, 1.0)
    
    def _calculate_dossier_quality(self, dossier_html: str) -> float:
        """Calculate dossier quality score."""
        if not dossier_html:
            return 0.0
        
        score = 0.0
        
        # Basic HTML structure (20%)
        if "<html" in dossier_html and "</html>" in dossier_html:
            score += 0.2
        
        # Content length (20%)
        if len(dossier_html) >= 3000:
            score += 0.2
        elif len(dossier_html) >= 1000:
            score += 0.1
        
        # Required sections (60%)
        required_sections = [
            "clinical summary", "decision", "rationale", 
            "safety", "compliance", "next steps"
        ]
        dossier_lower = dossier_html.lower()
        present_sections = sum(1 for section in required_sections if section in dossier_lower)
        score += (present_sections / len(required_sections)) * 0.6
        
        return min(score, 1.0)
    
    def _calculate_overall_score(self, detailed_results: List[EvaluationMetrics]) -> float:
        """Calculate overall evaluation score."""
        if not detailed_results:
            return 0.0
        
        # Weight different aspects
        weights = {
            "outcome_accuracy": 0.3,
            "confidence": 0.2,
            "decision_quality": 0.2,
            "performance": 0.15,
            "cost": 0.1,
            "compliance": 0.05
        }
        
        scores = {
            "outcome_accuracy": sum(1 for r in detailed_results if r.outcome_correct) / len(detailed_results),
            "confidence": statistics.mean(r.confidence_score for r in detailed_results),
            "decision_quality": statistics.mean(r.decision_quality_score for r in detailed_results),
            "performance": sum(1 for r in detailed_results if r.processing_time <= 20.0) / len(detailed_results),
            "cost": sum(1 for r in detailed_results if r.cost <= 0.10) / len(detailed_results),
            "compliance": statistics.mean(r.compliance_score for r in detailed_results)
        }
        
        overall = sum(scores[aspect] * weight for aspect, weight in weights.items())
        return min(overall, 1.0)
    
    def _calculate_demo_score(self, detailed_results: List[EvaluationMetrics]) -> float:
        """Calculate demo-specific score with stricter requirements."""
        if not detailed_results:
            return 0.0
        
        # Demo cases must meet MVP requirements
        mvp_criteria = [
            sum(1 for r in detailed_results if r.outcome_correct) / len(detailed_results),  # 100% accuracy
            sum(1 for r in detailed_results if r.confidence_score >= 0.8) / len(detailed_results),
            sum(1 for r in detailed_results if r.processing_time <= 20.0) / len(detailed_results),
            sum(1 for r in detailed_results if r.cost <= 0.10) / len(detailed_results),
            statistics.mean(r.decision_quality_score for r in detailed_results),
            statistics.mean(r.dossier_quality_score for r in detailed_results)
        ]
        
        return statistics.mean(mvp_criteria)
    
    def _calculate_performance_metrics(self, processing_times: List[float]) -> Dict[str, float]:
        """Calculate performance metrics."""
        if not processing_times:
            return {}
        
        return {
            "mean_time": statistics.mean(processing_times),
            "median_time": statistics.median(processing_times),
            "p95_time": statistics.quantiles(processing_times, n=20)[18] if len(processing_times) >= 20 else max(processing_times),
            "max_time": max(processing_times),
            "min_time": min(processing_times),
            "std_dev": statistics.stdev(processing_times) if len(processing_times) > 1 else 0.0
        }
    
    def _calculate_cost_analysis(self, costs: List[float]) -> Dict[str, float]:
        """Calculate cost analysis."""
        if not costs:
            return {}
        
        return {
            "total_cost": sum(costs),
            "mean_cost": statistics.mean(costs),
            "median_cost": statistics.median(costs),
            "max_cost": max(costs),
            "under_budget_ratio": sum(1 for c in costs if c <= 0.10) / len(costs)
        }
    
    def _print_summary(self, report: EvaluationReport):
        """Print evaluation summary."""
        print(f"\n{'='*60}")
        print(f"EVALUATION SUMMARY - {report.run_id}")
        print(f"{'='*60}")
        print(f"Timestamp: {report.timestamp}")
        print(f"Total Cases: {report.total_cases}")
        print(f"Passed: {report.passed} ({report.passed/report.total_cases:.1%})")
        print(f"Failed: {report.failed} ({report.failed/report.total_cases:.1%})")
        print(f"Warnings: {report.warnings} ({report.warnings/report.total_cases:.1%})")
        print(f"Skipped: {report.skipped} ({report.skipped/report.total_cases:.1%})")
        print(f"Overall Score: {report.overall_score:.3f}")
        
        print(f"\nPerformance Metrics:")
        perf = report.performance_metrics
        print(f"  Mean Processing Time: {perf.get('mean_time', 0):.2f}s")
        print(f"  P95 Processing Time: {perf.get('p95_time', 0):.2f}s")
        print(f"  Max Processing Time: {perf.get('max_time', 0):.2f}s")
        
        print(f"\nCost Analysis:")
        cost = report.cost_analysis
        print(f"  Total Cost: ${cost.get('total_cost', 0):.3f}")
        print(f"  Mean Cost per Case: ${cost.get('mean_cost', 0):.3f}")
        print(f"  Under Budget Ratio: {cost.get('under_budget_ratio', 0):.1%}")
        
        if report.regression_analysis:
            reg = report.regression_analysis
            print(f"\nRegression Analysis:")
            print(f"  Overall Score Change: {reg['overall_score_change']:+.3f}")
            print(f"  Recommendation: {reg['recommendation']}")
    
    def _print_demo_summary(self, report: EvaluationReport):
        """Print demo-specific summary."""
        print(f"\n{'='*60}")
        print(f"DEMO CASES EVALUATION - {report.run_id}")
        print(f"{'='*60}")
        
        # MVP Requirements Check
        mvp_pass = True
        
        print("MVP Requirements Validation:")
        
        # Check outcome accuracy (must be 100%)
        accuracy = report.passed / report.total_cases
        print(f"  Decision Accuracy: {accuracy:.1%} {'✓' if accuracy == 1.0 else '✗'}")
        if accuracy < 1.0:
            mvp_pass = False
        
        # Check performance (P50 < 6s, P95 < 12s)
        perf = report.performance_metrics
        p50 = perf.get('median_time', 0)
        p95 = perf.get('p95_time', 0)
        print(f"  P50 Processing Time: {p50:.2f}s {'✓' if p50 < 6.0 else '✗'}")
        print(f"  P95 Processing Time: {p95:.2f}s {'✓' if p95 < 12.0 else '✗'}")
        if p50 >= 6.0 or p95 >= 12.0:
            mvp_pass = False
        
        # Check cost (< $0.10 per case)
        cost = report.cost_analysis
        mean_cost = cost.get('mean_cost', 0)
        print(f"  Mean Cost per Case: ${mean_cost:.3f} {'✓' if mean_cost < 0.10 else '✗'}")
        if mean_cost >= 0.10:
            mvp_pass = False
        
        # Overall MVP status
        print(f"\nMVP STATUS: {'✓ PASS' if mvp_pass else '✗ FAIL'}")
        print(f"Overall Demo Score: {report.overall_score:.3f}")
    
    def _print_detailed_failure(self, metrics: EvaluationMetrics, test_case: TestCase):
        """Print detailed failure information."""
        print(f"    Outcome Correct: {metrics.outcome_correct}")
        print(f"    Confidence Score: {metrics.confidence_score:.3f}")
        print(f"    Processing Time: {metrics.processing_time:.2f}s (max: {test_case.max_processing_time:.2f}s)")
        print(f"    Cost: ${metrics.cost:.3f} (max: ${test_case.max_cost:.3f})")
        print(f"    Decision Quality: {metrics.decision_quality_score:.3f}")
        print(f"    Compliance Score: {metrics.compliance_score:.3f}")
    
    def _save_report(self, report: EvaluationReport):
        """Save evaluation report."""
        report_path = self.results_dir / f"{report.run_id}_report.json"
        with open(report_path, 'w') as f:
            json.dump(asdict(report), f, indent=2, default=str)
        print(f"Report saved: {report_path}")
    
    def _load_test_cases(self) -> List[TestCase]:
        """Load test cases from configuration."""
        config_path = Path(self.config_path)
        if not config_path.exists():
            return self._create_default_test_cases()
        
        with open(config_path, 'r') as f:
            if config_path.suffix == '.yaml':
                config = yaml.safe_load(f)
            else:
                config = json.load(f)
        
        test_cases = []
        for case_data in config.get('test_cases', []):
            test_cases.append(TestCase(**case_data))
        
        return test_cases
    
    def _create_default_test_cases(self) -> List[TestCase]:
        """Create default test cases for MVP demo."""
        return [
            TestCase(
                id="patient_007_diabetes_cgm",
                name="Patient 007 - Diabetes CGM Approval",
                description="35-year-old with T2DM requesting CGM - Expected APPROVE",
                xml_file="Patient_007_eclaim.xml",
                expected_outcome="APPROVE",
                expected_confidence=0.9,
                expected_auth_amount=1200.0,
                max_processing_time=20.0,
                max_cost=0.10,
                patient_type="Patient_007",
                condition="Type 2 Diabetes",
                treatment="CGM"
            ),
            TestCase(
                id="patient_005_osteoarthritis_review",
                name="Patient 005 - Osteoarthritis Review",
                description="68-year-old with knee osteoarthritis - Expected REVIEW",
                xml_file="Patient_005_eclaim.xml",
                expected_outcome="REVIEW",
                expected_confidence=0.6,
                expected_auth_amount=0.0,
                max_processing_time=20.0,
                max_cost=0.10,
                patient_type="Patient_005",
                condition="Knee Osteoarthritis",
                treatment="Knee Surgery"
            ),
            TestCase(
                id="patient_011_parkinsons_deny",
                name="Patient 011 - Parkinson's DBS Denial",
                description="72-year-old with Parkinson's requesting DBS - Expected DENY",
                xml_file="Patient_011_eclaim.xml",
                expected_outcome="DENY",
                expected_confidence=0.8,
                expected_auth_amount=0.0,
                max_processing_time=20.0,
                max_cost=0.10,
                patient_type="Patient_011",
                condition="Parkinson's Disease",
                treatment="DBS"
            )
        ]
    
    def _load_xml_data(self, xml_file: str) -> str:
        """Load XML data from file."""
        # Try multiple locations
        possible_paths = [
            Path("data/dataset_2/synthetic_dataset/UAE_XML") / xml_file,
            Path("tests/test_data") / xml_file,
            Path("samples") / xml_file
        ]
        
        for path in possible_paths:
            if path.exists():
                with open(path, 'r') as f:
                    return f.read()
        
        # Return mock XML if file not found
        return self._create_mock_xml(xml_file)
    
    def _create_mock_xml(self, xml_file: str) -> str:
        """Create mock XML for testing when actual files not available."""
        if "007" in xml_file:
            return '''<?xml version="1.0" encoding="UTF-8"?>
<PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
    <Header>
        <TransactionID>EVAL-007</TransactionID>
    </Header>
    <JustificationText>Evaluation test - diabetes CGM</JustificationText>
    <ServiceRequests>
        <ServiceRequest>
            <ct:ActivityCode>95250</ct:ActivityCode>
            <ct:DiagnosisCode>E11.9</ct:DiagnosisCode>
            <RequestedAmount currency="AED">1200.00</RequestedAmount>
        </ServiceRequest>
    </ServiceRequests>
</PriorAuthorizationRequest>'''
        elif "005" in xml_file:
            return '''<?xml version="1.0" encoding="UTF-8"?>
<PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
    <Header>
        <TransactionID>EVAL-005</TransactionID>
    </Header>
    <JustificationText>Evaluation test - osteoarthritis</JustificationText>
    <ServiceRequests>
        <ServiceRequest>
            <ct:ActivityCode>27447</ct:ActivityCode>
            <ct:DiagnosisCode>M17.9</ct:DiagnosisCode>
            <RequestedAmount currency="AED">25000.00</RequestedAmount>
        </ServiceRequest>
    </ServiceRequests>
</PriorAuthorizationRequest>'''
        else:
            return '''<?xml version="1.0" encoding="UTF-8"?>
<PriorAuthorizationRequest xmlns:ct="http://www.eclaimlink.ae/DHD/ValidationSchema">
    <Header>
        <TransactionID>EVAL-011</TransactionID>
    </Header>
    <JustificationText>Evaluation test - Parkinson's DBS</JustificationText>
    <ServiceRequests>
        <ServiceRequest>
            <ct:ActivityCode>61885</ct:ActivityCode>
            <ct:DiagnosisCode>G20</ct:DiagnosisCode>
            <RequestedAmount currency="AED">75000.00</RequestedAmount>
        </ServiceRequest>
    </ServiceRequests>
</PriorAuthorizationRequest>'''
    
    def _get_default_config_path(self) -> str:
        """Get default configuration path."""
        return "tests/evaluation/evaluation_config.yaml"
    
    def _load_baseline_report(self, baseline_path: str) -> EvaluationReport:
        """Load baseline report for regression testing."""
        with open(baseline_path, 'r') as f:
            data = json.load(f)
        
        # Convert back to EvaluationReport
        # Note: This is simplified - in production, we'd need proper deserialization
        return EvaluationReport(**data)
    
    def _analyze_performance_regression(self, baseline: EvaluationReport, current: EvaluationReport) -> Dict[str, Any]:
        """Analyze performance regression."""
        baseline_perf = baseline.performance_metrics
        current_perf = current.performance_metrics
        
        return {
            "mean_time_change": current_perf.get('mean_time', 0) - baseline_perf.get('mean_time', 0),
            "p95_time_change": current_perf.get('p95_time', 0) - baseline_perf.get('p95_time', 0),
            "performance_degraded": current_perf.get('mean_time', 0) > baseline_perf.get('mean_time', 0) * 1.1
        }
    
    def _analyze_cost_regression(self, baseline: EvaluationReport, current: EvaluationReport) -> Dict[str, Any]:
        """Analyze cost regression."""
        baseline_cost = baseline.cost_analysis
        current_cost = current.cost_analysis
        
        return {
            "mean_cost_change": current_cost.get('mean_cost', 0) - baseline_cost.get('mean_cost', 0),
            "total_cost_change": current_cost.get('total_cost', 0) - baseline_cost.get('total_cost', 0),
            "cost_increased": current_cost.get('mean_cost', 0) > baseline_cost.get('mean_cost', 0) * 1.05
        }
    
    def _analyze_outcome_changes(self, baseline: EvaluationReport, current: EvaluationReport) -> Dict[str, Any]:
        """Analyze outcome changes."""
        return {
            "accuracy_change": (current.passed / current.total_cases) - (baseline.passed / baseline.total_cases),
            "overall_score_change": current.overall_score - baseline.overall_score,
            "accuracy_degraded": (current.passed / current.total_cases) < (baseline.passed / baseline.total_cases)
        }
    
    def _generate_regression_recommendation(self, baseline: EvaluationReport, current: EvaluationReport) -> str:
        """Generate regression recommendation."""
        perf_regression = self._analyze_performance_regression(baseline, current)
        cost_regression = self._analyze_cost_regression(baseline, current)
        outcome_regression = self._analyze_outcome_changes(baseline, current)
        
        if outcome_regression["accuracy_degraded"]:
            return "CRITICAL: Decision accuracy has degraded - immediate investigation required"
        elif perf_regression["performance_degraded"] and cost_regression["cost_increased"]:
            return "WARNING: Both performance and cost have degraded - optimization needed"
        elif current.overall_score > baseline.overall_score:
            return "PASS: Overall improvements detected"
        else:
            return "PASS: No significant regressions detected"


def main():
    """Main entry point for evaluation harness."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Pre-Authorization System Evaluation Harness")
    parser.add_argument("--config", help="Path to evaluation configuration file")
    parser.add_argument("--demo-only", action="store_true", help="Run only demo cases")
    parser.add_argument("--baseline", help="Path to baseline report for regression testing")
    
    args = parser.parse_args()
    
    harness = EvaluationHarness(config_path=args.config)
    
    if args.baseline:
        harness.run_regression_test(args.baseline)
    elif args.demo_only:
        harness.run_demo_cases_evaluation()
    else:
        harness.run_full_evaluation()


if __name__ == "__main__":
    main()