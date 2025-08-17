# Complete Insurer Workflow Implementation Plan

## Objective
Implement complete end-to-end insurer workflow: API receives XML → processes with pipeline → stores results → displays in insurer dashboard with patient history and decision interface.

## Target User Experience

### For Insurer (Medical Director):
1. **Request Inbox**: See incoming PA requests with priority/status
2. **Patient Context**: View request + complete patient history + AI analysis
3. **Decision Interface**: Review dossier, approve/deny/request more info
4. **Communication**: Send decision back to provider

### Request Sources:
- **Primary**: API submissions from providers (automated)
- **Secondary**: Manual upload in dashboard (testing/edge cases)

## Implementation Plan

### Phase 1: Backend Request Management
**Agent:** `backend-engineer-1`
- Create request storage system (database tables/models)
- Add patient history integration with new requests
- Implement request status tracking (pending/under_review/decided)
- Add request queue management

### Phase 2: API Endpoints for Insurer Dashboard  
**Agent:** `backend-engineer-2`
- `GET /api/insurer/requests` - Request inbox with filters
- `GET /api/insurer/requests/{request_id}` - Full request details + patient history
- `POST /api/insurer/requests/{request_id}/decision` - Submit decision
- `GET /api/insurer/patients/{patient_id}/history` - Patient timeline
- Request assignment and workflow management

### Phase 3: Insurer Dashboard UI
**Agent:** `frontend-engineer-1`  
- Request Inbox component with priority sorting
- Patient History Timeline component
- Decision Review Interface with dossier display
- Request Details view with all pipeline results
- Decision submission form with reasoning

### Phase 4: Integration & Workflow
**Agent:** `frontend-engineer-2`
- Connect XML upload → automatic request creation
- Integrate pipeline processing with request storage
- Real-time updates for new requests
- Communication interface for provider notifications

### Phase 5: Testing & Validation
**Agent:** `test-engineer-1`
- End-to-end workflow testing
- Request lifecycle validation
- Patient history accuracy
- Decision workflow functionality

## Success Criteria

✅ **XML Request → Dashboard**: Provider submits XML → appears in insurer inbox  
✅ **Patient History**: Full patient context displayed with new request  
✅ **AI Analysis**: Pipeline results integrated and displayed professionally  
✅ **Decision Workflow**: Medical director can review and decide efficiently  
✅ **Communication**: Decision communicated back to provider  

## Workflow Validation
Test complete flow: Submit Patient_007 XML → View in insurer dashboard → See patient history → Review AI dossier → Make decision → Confirm storage