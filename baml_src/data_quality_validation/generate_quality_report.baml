



// UI-friendly report generation function
function GenerateQualityReport(validation_result: ValidationResult) -> UIFriendlyReport {
  client GPT4oMini
  prompt #"
    You are a healthcare data analyst creating user-friendly reports for insurance processors.

    Based on the following validation results, create a comprehensive but accessible report:

    Validation Results: {{ validation_result }}

    Generate a report that includes:

    **1. Executive Summary:**
    - Overall data fitness for processing (Excellent/Good/Fair/Poor)
    - Key compliance status with UAE regulations
    - Major findings that require immediate attention

    **2. Quality Assessment:**
    - Letter grade (A-F) based on quality score
    - Breakdown of issue types and counts
    - Confidence level in the analysis

    **3. Actionable Recommendations:**
    - Prioritized list of improvements
    - Specific steps to address critical issues
    - Process improvements for future submissions

    **4. Compliance Status:**
    - DHA/DOH regulatory compliance summary
    - Required documentation status
    - Authorization and approval requirements

    The report should be:
    - Clear and actionable for non-technical users
    - Focused on business impact and next steps
    - Compliant with UAE healthcare standards
    - Professional but accessible language

    {{ ctx.output_format }}
  "#
}


test quality_report_generation {
  functions [GenerateQualityReport]
  args {
    validation_result {
      overall_quality_score 0.85
      confidence_score 0.92
      validation_passed true
      critical_issues 0
      warning_issues 2
      info_issues 3
      top_issues ["Date format should be standardized", "Provider license verification recommended"]
      recommendations ["Standardize all dates to ISO 8601 format", "Verify provider licensing status"]
      processing_time_ms 1200
      model_used "gpt-4o-mini"
      reasoning "High-quality data with minor formatting inconsistencies"
    }
  }
}
