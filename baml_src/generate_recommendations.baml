// Recommendations Generation Function with Tests

// Function to create actionable recommendations
function GenerateRecommendations(quality_report: DataQualityReport) -> ActionableItem[] {
  client ParallelValidator
  prompt #"
    You are a healthcare data improvement consultant specializing in UAE healthcare systems.

    Based on the following quality assessment report:

    Quality Score: {{ quality_report.quality_score.overall_score }}
    Total Issues: {{ quality_report.quality_score.total_issues }}
    Critical Issues: {{ quality_report.quality_score.critical_issues }}

    Issues Summary:
    {% for issue in quality_report.validation_issues %}
    - {{ issue.severity }}: {{ issue.message }} ({{ issue.type }})
    {% endfor %}

    Generate specific, actionable recommendations for improving data quality:

    **Prioritization Criteria**:
    1. Patient safety impact
    2. Regulatory compliance risk
    3. Financial impact
    4. Implementation effort required

    **Recommendation Categories**:
    1. **Immediate Actions** (High Priority):
       - Critical compliance violations
       - Patient safety concerns
       - Data corruption issues

    2. **Short-term Improvements** (Medium Priority):
       - Process standardization
       - Training requirements
       - System configuration updates

    3. **Long-term Enhancements** (Lower Priority):
       - Workflow optimization
       - Technology upgrades
       - Advanced quality monitoring

    **For Each Recommendation**:
    - Provide specific fix instructions
    - Estimate implementation effort
    - Identify responsible parties
    - Include UAE regulatory context
    - Suggest validation methods

    Focus on practical, achievable improvements that align with UAE healthcare standards and can be implemented by typical healthcare organizations.

    {{ ctx.output_format }}
  "#
}

// Simple test for recommendations
test recommendations_simple {
  functions [GenerateRecommendations]
  args {
    quality_report #"
      {
        "bundle_id": "test-bundle-001",
        "assessed_at": "2024-12-01T10:00:00Z",
        "quality_score": {
          "overall_score": 0.88,
          "compliance_score": 0.92,
          "clinical_logic_score": 0.85,
          "data_completeness_score": 0.90,
          "code_validity_score": 0.85,
          "total_issues": 3,
          "critical_issues": 0,
          "error_issues": 0,
          "warning_issues": 2,
          "info_issues": 1
        },
        "validation_issues": [
          {
            "id": "WARN-001",
            "type": "CLINICAL",
            "severity": "WARNING",
            "code": "FOLLOW_UP_MISSING",
            "message": "Follow-up appointment not scheduled"
          }
        ],
        "summary": {
          "total_records": 1,
          "valid_records": 1,
          "invalid_records": 0
        },
        "total_resources": 5,
        "resources_assessed": 5
      }
    "#
  }
}
