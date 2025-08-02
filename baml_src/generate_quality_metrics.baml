// Quality Metrics Generation Function with Tests

// Function to generate quality metrics and scoring
function GenerateQualityMetrics(validation_results: LLMValidationResult[]) -> QualityScore {
  client ParallelValidator
  prompt #"
    You are a healthcare data quality analyst tasked with generating comprehensive quality scores.

    Based on the following validation results from multiple LLM validators:

    {% for result in validation_results %}
    Validation Result {{ loop.index }}:
    - Validation Passed: {{ result.validation_passed }}
    - Confidence Score: {{ result.confidence_score }}
    - Issues Count: {{ result.issues|length }}
    - Quality Metrics: {{ result.quality_metrics }}
    {% endfor %}

    Generate a comprehensive quality score that includes:

    1. **Overall Score** (0.0 to 1.0):
       - Weighted combination of all validation dimensions
       - Consider issue severity and frequency
       - Account for validator confidence levels

    2. **Dimensional Scores**:
       - Compliance Score: UAE regulatory adherence
       - Clinical Logic Score: Medical appropriateness
       - Data Completeness Score: Required field presence
       - Code Validity Score: Medical coding accuracy

    3. **Issue Quantification**:
       - Total issues across all validators
       - Breakdown by severity (critical, error, warning, info)
       - Issue frequency analysis

    4. **Quality Assessment**:
       - Identify the strongest and weakest areas
       - Calculate improvement potential
       - Assess data fitness for processing

    Use these scoring guidelines:
    - 0.9-1.0: Excellent quality, minimal issues
    - 0.8-0.89: Good quality, minor issues
    - 0.7-0.79: Acceptable quality, some issues need attention
    - 0.6-0.69: Poor quality, significant issues present
    - 0.0-0.59: Unacceptable quality, major remediation required

    Weight critical and error issues more heavily than warnings and info items.
    Consider the UAE healthcare context where compliance issues are particularly important.

    {{ ctx.output_format }}
  "#
}

// Simple test for quality metrics
test quality_metrics_simple {
  functions [GenerateQualityMetrics]
  args {
    validation_results #"
      [
        {
          "validation_passed": true,
          "confidence_score": 0.95,
          "issues": [],
          "quality_metrics": {"compliance_score": 0.98},
          "processing_time_ms": 1200,
          "model_used": "gemini-2.5-flash"
        }
      ]
    "#
  }
}
