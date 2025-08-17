# Multi-Agent Pipeline Implementation Plan

## Objective
Implement three critical milestones for the pre-authorization pipeline: Aug 20 (DossierWriter LLM), Aug 21 (Orchestrator adapter + CLI/JSON outputs), and Aug 22 (Backend endpoints & UI integration).

## Current Status Analysis

**Completed Components:**
- ✅ `PreAuthPipeline` DSPy module with all phases through decision synthesis
- ✅ Deterministic decision synthesis with 6-tier logic
- ✅ Clinical summarization, evidence retrieval, policy evaluation
- ✅ Comprehensive audit trails and cost tracking
- ✅ FinalReportSignature already exists in signatures.py

**Missing Components:**
- ❌ DossierWriter LLM implementation (skeleton placeholder exists)
- ❌ Pipeline integration with orchestrator (orchestrator.py still separate)
- ❌ CLI output to timestamped JSON files in output/ folder
- ❌ Backend API endpoints for full pipeline exposure
- ❌ UI integration for pipeline results display

## Subtasks & Agent Assignments

### 1. DossierWriter LLM Implementation (Aug 20)
**Agent:** `ai-engineer-1`
- Implement `DossierWriter` class using existing `FinalReportSignature`
- Add professional narrative templates with bilingual support 
- Integrate structured inputs from decision synthesis
- Add citation formatting and medical terminology
- Test with sample pipeline outputs

### 2. Pipeline CLI Integration (Aug 21)
**Agent:** `backend-engineer-1` 
- Remove/deprecate `preauth_system/orchestrator.py` 
- Ensure `PreAuthPipeline` handles complete workflow
- Add CLI interface for direct pipeline execution
- Implement JSON output to `output/YYYYMMDD/HHMMSS/<patient>_result.json`
- Validate end-to-end processing

### 3. Backend API Integration (Aug 22a)
**Agent:** `backend-engineer-2`
- Update FastAPI endpoints to use `PreAuthPipeline` instead of orchestrator
- Expose full pipeline results (intake, summary, checklist, decision, dossier)
- Add new endpoint: `POST /api/process/unified` for pipeline processing
- Ensure proper error handling and response formatting
- Update existing `/api/preauth/process` endpoint

### 4. Frontend UI Integration (Aug 22b)  
**Agent:** `frontend-engineer-1`
- Update React dashboard to consume new pipeline API endpoints
- Add components for displaying dossier and decision results
- Implement file upload → pipeline processing → results display flow
- Add proper error handling and loading states
- Test end-to-end UI workflow

### 5. Testing & Validation
**Agent:** `test-engineer-1`
- Create integration tests for complete pipeline flow
- Validate JSON output format and file creation
- Test API endpoint responses and error handling
- Verify UI functionality with sample data
- Create demo fixtures for each policy type

## Parallel Execution Strategy

**Phase 1 (Parallel):** DossierWriter + CLI Integration
- ai-engineer-1 and backend-engineer-1 can work simultaneously
- DossierWriter is isolated module, CLI integration touches different files

**Phase 2 (Sequential):** API Integration depends on Phase 1 completion
- backend-engineer-2 needs completed pipeline from Phase 1

**Phase 3 (Parallel):** UI Integration + Testing  
- frontend-engineer-1 and test-engineer-1 can work simultaneously
- UI work can proceed with API contracts, testing validates everything

## Validation Criteria

✅ **DossierWriter:** Professional narrative output with citations
✅ **CLI Integration:** Direct pipeline execution with JSON file output  
✅ **API Integration:** Full pipeline exposure via REST endpoints
✅ **UI Integration:** End-to-end file upload → results display
✅ **Testing:** All components validated with integration tests

## Success Metrics
- Pipeline processes Patient_007 end-to-end in <8 seconds
- Cost remains <$0.10 per request
- JSON outputs saved to timestamped output folders
- UI displays complete dossier with decision rationale
- All tests pass with deterministic reproducibility