---
session_folder: .claude/sessions/2025-08-17_21-33_decision-combiner-audit
lead_agent: lead-agent-1
subagent: backend-engineer-1
created_at: 2025-08-17T21:35:00Z
---

# DecisionCombiner Architecture Analysis and Design

## Current Pipeline Architecture Analysis

### Existing Structure Overview
The current pipeline architecture in `preauth_system/pipeline_module.py` implements a `PreAuthPipeline(dspy.Module)` with the following phases:

1. **Intake & Context Mapping** (`_intake` method)
2. **Clinical Summarization** (using `ClinicalAnalysis` signature)
3. **Evidence Retrieval** (using `EvidenceRetrievalSignature` with ReAct)
4. **Policy Evaluation** (using `PolicyEvaluationSignature`)
5. **Decision Synthesis** (currently placeholder)
6. **Dossier Generation** (placeholder)

### Current Decision Implementation
Lines 308-315 in `pipeline_module.py` show a minimal decision scaffold:
```python
# Minimal deterministic decision scaffold using constants
decision: Dict[str, Any] = {
    "outcome": DecisionOutcome.REVIEW.value,
    "confidence": 0.0,
    "reason_codes": [ReasonCode.POLICY_CRITERIA_UNCERTAIN.value],
    "conditions": [],
    "rationale": "MVP skeleton: downstream modules not yet executed.",
}
```

This is exactly where the DecisionCombiner should be integrated.

### PolicyEvaluator Checklist Schema
From `signatures.py`, the PolicyEvaluationSignature produces a `PolicyChecklistOutput`:
```python
class PolicyChecklistOutput(BaseModel):
    criteria: List[PolicyCriteriaItem]
    missing_documents: List[str]
    overall_compliance_score: float
    policy_source: str

class PolicyCriteriaItem(BaseModel):
    id: str
    description: str
    status: Literal["met", "unmet", "uncertain"]
    rationale: str
    citations: List[str]
    missing_documentation: Optional[str] = None
```

## DecisionCombiner Design

### Interface Definition
```python
class DecisionCombiner:
    """Deterministic decision synthesis engine for prior authorization."""
    
    def __init__(self) -> None:
        """Initialize the decision combiner with deterministic rules."""
        pass
    
    def combine_decision(
        self,
        checklist: Dict[str, Any],
        clinical_summary: Dict[str, Any],
        evidence: List[Dict[str, Any]],
        safety_flags: List[str] = None
    ) -> Dict[str, Any]:
        """
        Combine policy checklist and other inputs into final decision.
        
        Returns deterministic decision based on:
        - APPROVE: All mandatory criteria met AND no safety blocks
        - DENY: Explicit non-coverage criterion present
        - REVIEW: Uncertain/unmet non-mandatory OR missing docs
        """
```

### Decision Logic Rules
Based on system_design.md requirements:

1. **APPROVE Conditions:**
   - All mandatory criteria have status="met" 
   - No safety contraindications present
   - Overall compliance score >= 0.8

2. **DENY Conditions:**
   - Any explicit non-coverage criterion present
   - Safety contraindication flagged
   - Critical mandatory criterion unmet

3. **REVIEW Conditions:**
   - Uncertain status on non-mandatory criteria
   - Missing required documentation
   - Overall compliance score between 0.5-0.8

### Integration Points

#### 1. Pipeline Integration
Replace lines 308-315 in `pipeline_module.py`:
```python
# Replace current placeholder with DecisionCombiner
from preauth_system.decision_combiner import DecisionCombiner

decision_combiner = DecisionCombiner()
decision = decision_combiner.combine_decision(
    checklist=checklist,
    clinical_summary=clinical_summary,
    evidence=evidence,
    safety_flags=[]  # TODO: integrate with safety module
)
```

#### 2. Timing Integration
Add decision timing to existing `PipelineTimings`:
```python
t4 = time.time()
decision = decision_combiner.combine_decision(...)
decision_ms = (time.time() - t4)

timings["decision_ms"] = decision_ms
```

#### 3. Cost Tracking Integration
Update `PipelineCost` to track decision phase:
```python
cost["phases"]["decision"] = 0.0  # Deterministic, no LLM cost
```

## Audit Fields Implementation

### Current Audit Infrastructure
The pipeline already has timing and cost tracking infrastructure:

- `PipelineTimings` TypedDict with per-phase timing
- `PipelineCost` TypedDict with cost breakdown
- Real-time logging with loguru

### Required Audit Enhancements

#### 1. Enhanced Timing Tracking
```python
class PipelineTimings(TypedDict, total=False):
    intake_ms: float
    summary_ms: float
    evidence_ms: float
    checklist_ms: float
    decision_ms: float      # ✅ Already present
    dossier_ms: float
    total_ms: float
    # Add decision breakdown:
    decision_rule_evaluation_ms: float
    decision_criteria_analysis_ms: float
```

#### 2. Decision Audit Trail
```python
class DecisionAuditTrail(TypedDict):
    criteria_evaluations: List[Dict[str, Any]]
    rule_path_taken: str
    confidence_factors: Dict[str, float]
    safety_checks_performed: List[str]
    policy_version: str
    timestamp: str
```

#### 3. Token/Cost Usage
- DecisionCombiner is deterministic (no LLM calls)
- Cost tracking should reflect $0.00 for decision phase
- Preserve existing token tracking for other phases

### Integration Architecture

#### File Structure
```
preauth_system/
├── decision_combiner.py     # New: Core DecisionCombiner class
├── decision_constants.py    # ✅ Existing: Enhance with reason mappings
├── pipeline_module.py       # ✅ Modify: Integrate DecisionCombiner
└── audit/                   # New: Audit trail utilities
    ├── __init__.py
    └── decision_audit.py    # Decision-specific audit logging
```

#### Dependencies
- No new external dependencies required
- Leverages existing `decision_constants.py`
- Integrates with existing timing/cost infrastructure
- Uses loguru for audit logging

### Reason Code Mapping Strategy

Enhance `decision_constants.py` with criterion-to-reason mappings:
```python
CRITERION_TO_REASON_MAP = {
    "diabetes_diagnosis": {
        "unmet": ReasonCode.POLICY_NON_COVERAGE,
        "uncertain": ReasonCode.INCOMPLETE_INFORMATION
    },
    "hba1c_elevated": {
        "unmet": ReasonCode.POLICY_CRITERIA_UNCERTAIN,
        "uncertain": ReasonCode.INCOMPLETE_INFORMATION
    }
}
```

### Data Flow Architecture

```
PolicyChecklistOutput (from pipeline)
         ↓
DecisionCombiner.combine_decision()
         ↓
1. Extract mandatory vs non-mandatory criteria
2. Apply deterministic rules (APPROVE/DENY/REVIEW)
3. Map criteria status → reason codes
4. Generate conditions and rationale
5. Create audit trail
         ↓
Enhanced Decision Object + Audit Trail
```

### Performance Considerations

1. **Deterministic Performance**: DecisionCombiner adds <1ms processing time
2. **Memory Usage**: Minimal, only processes structured data
3. **Caching**: Not needed since rules are deterministic
4. **Concurrency**: Thread-safe by design (no shared state)

## Validation Requirements

To ensure deterministic behavior:

1. **Input Validation**: Strict schema validation on checklist input
2. **Rule Testing**: Unit tests covering all decision paths
3. **Reproducibility Tests**: Same input → same output verification
4. **Audit Completeness**: Every decision includes full audit trail

## Summary

I analyzed the current pipeline architecture and designed the DecisionCombiner interface to integrate seamlessly with the existing `PreAuthPipeline`. The design implements the deterministic rules specified in the system design document while leveraging existing audit infrastructure and maintaining clean separation of concerns.