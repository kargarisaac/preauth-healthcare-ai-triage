"""
DossierWriter Quality Assurance Tests

Tests the professional quality of generated dossiers,
validating medical language, citations, cost efficiency, and formatting.
"""

import pytest
import time
from pathlib import Path

from preauth_system.dossier_writer import DossierWriter
from preauth_system.pipeline_module import PreAuthPipeline


@pytest.mark.integration
class TestDossierQuality:
    """Quality assurance tests for DossierWriter."""
    
    @pytest.fixture
    def dossier_writer(self):
        """Create DossierWriter instance for testing."""
        return DossierWriter(language="en")
    
    @pytest.fixture
    def sample_pipeline_data(self):
        """Provide sample pipeline data for dossier generation."""
        return {
            "clinical_summary": {
                "executive_summary": "35-year-old patient with Type 2 Diabetes Mellitus presenting for glycemic control assessment and HbA1c monitoring.",
                "patient_profile": {
                    "age": 35,
                    "gender": "M",
                    "primary_conditions": ["Type 2 Diabetes Mellitus"]
                },
                "timeline": [
                    {"date": "2024-12-01", "event": "Last HbA1c: 9.2%"},
                    {"date": "2025-07-31", "event": "Current visit for monitoring"}
                ],
                "recommendations": ["HbA1c monitoring", "Glycemic control assessment"]
            },
            "checklist": {
                "criteria": [
                    {
                        "id": "diabetes_diagnosis",
                        "description": "Confirmed diabetes diagnosis",
                        "status": "met",
                        "rationale": "Type 2 diabetes documented",
                        "citations": ["Clinical summary", "ICD-10: E11.9"]
                    },
                    {
                        "id": "monitoring_frequency",
                        "description": "Appropriate monitoring interval",
                        "status": "met",
                        "rationale": "6-month interval appropriate for poor control",
                        "citations": ["ADA Guidelines 2025"]
                    }
                ],
                "overall_compliance_score": 0.95,
                "policy_source": "diabetes_technology.yaml"
            },
            "decision": {
                "outcome": "APPROVE",
                "confidence": 1.0,
                "rationale": "All diabetes monitoring criteria satisfied with 95% compliance",
                "conditions": ["Subject to diabetes technology policy terms"]
            },
            "evidence": [
                {
                    "source": "diabetes_technology_guidelines.md",
                    "snippet": "HbA1c monitoring every 3-6 months for patients with poor glycemic control"
                },
                {
                    "source": "diabetes_technology.yaml",
                    "snippet": "HbA1c testing coverage approved for established diabetes patients"
                }
            ],
            "patient_context": {
                "age": "35",
                "gender": "M",
                "emirates_id": "784-1234-5678901-2",
                "policy_number": "POL-2025-001"
            }
        }
    
    def test_dossier_professional_quality(self, dossier_writer, sample_pipeline_data):
        """Test that generated dossier meets professional medical standards."""
        start_time = time.time()
        
        dossier = dossier_writer.forward(
            clinical_summary=sample_pipeline_data["clinical_summary"],
            checklist=sample_pipeline_data["checklist"],
            decision=sample_pipeline_data["decision"],
            evidence=sample_pipeline_data["evidence"],
            patient_context=sample_pipeline_data["patient_context"]
        )
        
        generation_time = time.time() - start_time
        
        # Validate basic structure
        assert "executive_summary" in dossier
        assert "sections" in dossier
        assert "citations" in dossier
        assert "language" in dossier
        assert "metadata" in dossier
        
        # Validate professional content quality
        executive_summary = dossier["executive_summary"]
        assert len(executive_summary) >= 50, "Executive summary too brief"
        assert "diabetes" in executive_summary.lower(), "Missing key medical context"
        assert "authorization" in executive_summary.lower() or "approve" in executive_summary.lower(), "Missing authorization context"
        
        # Validate sections structure
        sections = dossier["sections"]
        assert len(sections) >= 3, "Insufficient number of sections"
        
        # Expected section types
        section_types = [section.get("type", "") for section in sections]
        expected_types = ["clinical", "decision", "policy"]
        for expected_type in expected_types:
            assert any(expected_type in stype for stype in section_types), f"Missing {expected_type} section"
        
        # Validate each section quality
        for i, section in enumerate(sections):
            assert "title" in section, f"Section {i} missing title"
            assert "content" in section, f"Section {i} missing content"
            assert len(section["title"]) > 5, f"Section {i} title too short"
            assert len(section["content"]) > 20, f"Section {i} content too brief"
            
            # Check for medical terminology appropriateness
            content = section["content"].lower()
            if "clinical" in section.get("type", ""):
                assert any(term in content for term in ["patient", "diagnosis", "treatment", "monitoring"]), f"Section {i} lacks clinical terminology"
        
        # Validate metadata quality
        metadata = dossier["metadata"]
        assert "sections_count" in metadata
        assert metadata["sections_count"] == len(sections)
        assert "complexity_score" in metadata
        assert metadata["complexity_score"] > 0
        
        # Validate generation performance
        assert generation_time < 5.0, f"Dossier generation took {generation_time:.2f}s > 5s"
    
    def test_citation_accuracy(self, dossier_writer, sample_pipeline_data):
        """Test that citations are properly formatted and accurately reference evidence."""
        dossier = dossier_writer.forward(
            clinical_summary=sample_pipeline_data["clinical_summary"],
            checklist=sample_pipeline_data["checklist"],
            decision=sample_pipeline_data["decision"],
            evidence=sample_pipeline_data["evidence"],
            patient_context=sample_pipeline_data["patient_context"]
        )
        
        citations = dossier["citations"]
        
        # Should have citations from evidence and checklist
        assert len(citations) >= 2, "Insufficient citations"
        
        # Validate citation structure
        for citation in citations:
            assert "source" in citation, "Citation missing source"
            assert "reference" in citation, "Citation missing reference"
            assert len(citation["source"]) > 0, "Empty citation source"
            assert len(citation["reference"]) > 0, "Empty citation reference"
        
        # Validate citations reference actual evidence
        evidence_sources = [ev["source"] for ev in sample_pipeline_data["evidence"]]
        checklist_citations = []
        for criterion in sample_pipeline_data["checklist"]["criteria"]:
            checklist_citations.extend(criterion.get("citations", []))
        
        # At least some citations should reference provided evidence
        citation_sources = [c["source"] for c in citations]
        has_evidence_citations = any(es in str(citation_sources) for es in evidence_sources)
        has_checklist_citations = any(cc in str(citation_sources) for cc in checklist_citations)
        
        assert has_evidence_citations or has_checklist_citations, "Citations do not reference provided evidence"
        
        # Validate citation formatting
        for citation in citations:
            reference = citation["reference"]
            # Should be properly formatted (e.g., "Source Name: Citation text")
            assert ":" in reference or "[" in reference, f"Citation not properly formatted: {reference}"
    
    def test_cost_efficiency(self, dossier_writer, sample_pipeline_data):
        """Test that dossier generation meets cost efficiency targets."""
        # Generate multiple dossiers to test consistency
        costs = []
        generation_times = []
        
        for i in range(3):
            start_time = time.time()
            
            # Mock cost tracking
            initial_cost = 0.01  # Simulated baseline cost
            
            dossier = dossier_writer.forward(
                clinical_summary=sample_pipeline_data["clinical_summary"],
                checklist=sample_pipeline_data["checklist"],
                decision=sample_pipeline_data["decision"],
                evidence=sample_pipeline_data["evidence"],
                patient_context=sample_pipeline_data["patient_context"]
            )
            
            generation_time = time.time() - start_time
            generation_times.append(generation_time)
            
            # Estimate cost based on content length (rough approximation)
            total_content_length = len(dossier["executive_summary"])
            for section in dossier["sections"]:
                total_content_length += len(section["content"])
            
            # Estimate cost: ~$0.01 per 1000 characters (rough GPT-4 approximation)
            estimated_cost = initial_cost + (total_content_length / 1000) * 0.01
            costs.append(estimated_cost)
            
            # Individual dossier should meet cost target
            assert estimated_cost < 0.02, f"Dossier {i+1} cost ${estimated_cost:.4f} > $0.02"
            
            # Validate quality wasn't sacrificed for cost
            assert len(dossier["sections"]) >= 3, f"Dossier {i+1} has too few sections"
            assert len(dossier["executive_summary"]) >= 50, f"Dossier {i+1} summary too brief"
        
        # Validate average cost efficiency
        avg_cost = sum(costs) / len(costs)
        assert avg_cost < 0.015, f"Average dossier cost ${avg_cost:.4f} > $0.015"
        
        # Validate generation speed
        avg_time = sum(generation_times) / len(generation_times)
        assert avg_time < 3.0, f"Average generation time {avg_time:.2f}s > 3s"
    
    def test_multilingual_support(self, sample_pipeline_data):
        """Test bilingual framework support and language handling."""
        # Test English dossier
        en_writer = DossierWriter(language="en")
        en_dossier = en_writer.forward(
            clinical_summary=sample_pipeline_data["clinical_summary"],
            checklist=sample_pipeline_data["checklist"],
            decision=sample_pipeline_data["decision"],
            evidence=sample_pipeline_data["evidence"],
            patient_context=sample_pipeline_data["patient_context"]
        )
        
        # Validate English dossier
        assert en_dossier["language"] == "en"
        assert "diabetes" in en_dossier["executive_summary"].lower()
        
        # Test Arabic dossier capability (framework test)
        ar_writer = DossierWriter(language="ar")
        ar_dossier = ar_writer.forward(
            clinical_summary=sample_pipeline_data["clinical_summary"],
            checklist=sample_pipeline_data["checklist"],
            decision=sample_pipeline_data["decision"],
            evidence=sample_pipeline_data["evidence"],
            patient_context=sample_pipeline_data["patient_context"]
        )
        
        # Validate Arabic framework is in place
        assert ar_dossier["language"] == "ar"
        # Content might still be English if translation not implemented, but framework should work
        assert len(ar_dossier["executive_summary"]) > 0
        assert len(ar_dossier["sections"]) > 0
        
        # Validate both dossiers have same structure
        assert len(en_dossier["sections"]) == len(ar_dossier["sections"])
        assert len(en_dossier["citations"]) == len(ar_dossier["citations"])
    
    def test_template_compliance(self, dossier_writer, sample_pipeline_data):
        """Test that dossier follows professional template standards."""
        dossier = dossier_writer.forward(
            clinical_summary=sample_pipeline_data["clinical_summary"],
            checklist=sample_pipeline_data["checklist"],
            decision=sample_pipeline_data["decision"],
            evidence=sample_pipeline_data["evidence"],
            patient_context=sample_pipeline_data["patient_context"]
        )
        
        # Validate professional structure
        assert "executive_summary" in dossier
        assert "sections" in dossier
        assert "citations" in dossier
        assert "metadata" in dossier
        
        # Validate executive summary format
        exec_summary = dossier["executive_summary"]
        assert exec_summary.endswith("."), "Executive summary should end with period"
        assert not exec_summary.startswith(" "), "Executive summary should not start with space"
        
        # Validate section formatting
        for section in dossier["sections"]:
            title = section["title"]
            content = section["content"]
            
            # Title formatting
            assert title[0].isupper(), "Section title should start with capital letter"
            assert not title.endswith("."), "Section title should not end with period"
            
            # Content formatting
            assert content.strip() == content, "Section content should not have leading/trailing whitespace"
            assert len(content.split(".")) >= 2, "Section content should have multiple sentences"
        
        # Validate metadata completeness
        metadata = dossier["metadata"]
        required_metadata = ["sections_count", "has_citations", "complexity_score"]
        for field in required_metadata:
            assert field in metadata, f"Missing metadata field: {field}"
    
    def test_real_pipeline_integration(self):
        """Test dossier generation with real pipeline output."""
        demo_xml_path = Path("data/dataset_2/synthetic_dataset/UAE_XML/Patient_007_eclaim.xml")
        if not demo_xml_path.exists():
            pytest.skip("Demo XML file not available")
        
        # Run full pipeline to get real data
        pipeline = PreAuthPipeline()
        pipeline_result = pipeline.forward(xml_path=str(demo_xml_path), xml_format="eclaim")
        
        # Validate dossier was generated
        assert "dossier" in pipeline_result
        dossier = pipeline_result["dossier"]
        
        # Test dossier quality with real data
        assert "executive_summary" in dossier
        assert "sections" in dossier
        assert len(dossier["sections"]) >= 1
        
        # Validate real dossier meets quality standards
        exec_summary = dossier["executive_summary"]
        assert len(exec_summary) >= 30, "Real dossier summary too brief"
        
        # Validate sections have substantive content
        for section in dossier["sections"]:
            assert len(section.get("content", "")) >= 15, "Real dossier section content too brief"
        
        # Validate metadata is reasonable
        metadata = dossier.get("metadata", {})
        if "complexity_score" in metadata:
            assert 0 <= metadata["complexity_score"] <= 100, "Invalid complexity score"
    
    def test_error_handling_and_fallbacks(self, dossier_writer):
        """Test dossier generation with incomplete or invalid data."""
        # Test with minimal data
        minimal_data = {
            "clinical_summary": {"executive_summary": "Minimal summary"},
            "checklist": {"criteria": [], "overall_compliance_score": 0.5},
            "decision": {"outcome": "REVIEW", "confidence": 0.5, "rationale": "Insufficient data"},
            "evidence": [],
            "patient_context": {}
        }
        
        dossier = dossier_writer.forward(**minimal_data)
        
        # Should still generate a valid dossier
        assert "executive_summary" in dossier
        assert "sections" in dossier
        assert len(dossier["executive_summary"]) > 0
        assert len(dossier["sections"]) >= 1
        
        # Test with None values
        none_data = {
            "clinical_summary": None,
            "checklist": None,
            "decision": {"outcome": "UNKNOWN", "confidence": 0, "rationale": ""},
            "evidence": None,
            "patient_context": None
        }
        
        dossier = dossier_writer.forward(**none_data)
        
        # Should generate fallback dossier
        assert "executive_summary" in dossier
        assert len(dossier["executive_summary"]) > 0
        
        # Metadata should indicate fallback
        metadata = dossier.get("metadata", {})
        assert metadata.get("is_fallback", False) or "fallback" in dossier["executive_summary"].lower()
    
    @pytest.mark.performance
    def test_dossier_generation_performance(self, dossier_writer, sample_pipeline_data):
        """Test dossier generation performance under load."""
        import threading
        import time
        
        results = []
        errors = []
        
        def generate_dossier():
            try:
                start_time = time.time()
                dossier = dossier_writer.forward(
                    clinical_summary=sample_pipeline_data["clinical_summary"],
                    checklist=sample_pipeline_data["checklist"],
                    decision=sample_pipeline_data["decision"],
                    evidence=sample_pipeline_data["evidence"],
                    patient_context=sample_pipeline_data["patient_context"]
                )
                generation_time = time.time() - start_time
                
                results.append({
                    "generation_time": generation_time,
                    "sections_count": len(dossier["sections"]),
                    "summary_length": len(dossier["executive_summary"]),
                    "citations_count": len(dossier["citations"])
                })
            except Exception as e:
                errors.append(str(e))
        
        # Run 5 concurrent dossier generations
        threads = []
        for i in range(5):
            thread = threading.Thread(target=generate_dossier)
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join(timeout=30)
        
        # Validate results
        assert len(errors) == 0, f"Errors in concurrent generation: {errors}"
        assert len(results) == 5, f"Expected 5 results, got {len(results)}"
        
        # Validate performance
        avg_time = sum(r["generation_time"] for r in results) / len(results)
        max_time = max(r["generation_time"] for r in results)
        
        assert avg_time < 4.0, f"Average generation time {avg_time:.2f}s > 4s"
        assert max_time < 8.0, f"Max generation time {max_time:.2f}s > 8s"
        
        # Validate consistency
        sections_counts = [r["sections_count"] for r in results]
        assert min(sections_counts) == max(sections_counts), "Inconsistent section counts in concurrent generation"
