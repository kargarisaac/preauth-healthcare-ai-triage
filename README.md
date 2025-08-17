# Nazmito

AI-powered pre-authorization platform for UAE healthcare insurance that processes XML and CSV healthcare data into FHIR-compliant canonical JSON.

## Testing the System

### 1. Testing Pipeline Module Directly

**Run the standalone pipeline CLI:**
```bash
# Direct CLI execution (processes Patient_007 demo case)
PYTHONPATH=. python preauth_system/pipeline_module.py

# Or using module execution
python -m preauth_system.pipeline_module
```

**Expected Output:**
- Complete 6-phase pipeline processing (intake → clinical → evidence → policy → decision → dossier)
- Timestamped JSON output saved to: `output/YYYYMMDD/HHMMSS/Patient_007_result.json`
- Console summary with processing time (~30-40s), cost ($0.00), and decision outcome

**Using the Pipeline in Python:**
```python
from preauth_system.pipeline_module import PreAuthPipeline

# Initialize pipeline
pipeline = PreAuthPipeline()

# Process XML file
result = pipeline.forward(
    xml_path="data/dataset_2/synthetic_dataset/UAE_XML/Patient_007_eclaim.xml",
    xml_format="eclaim"
)

print(f"Decision: {result['decision']['outcome']}")
print(f"Patient: {result['intake']['patient_id']}")
print(f"Processing Time: {result['timings']['total_ms']}ms")
```

### 2. Testing via FastAPI Backend (curl)

**Start the Backend:**
```bash
# Terminal 1: Start API server
PYTHONPATH=. python api/run_server.py
# ✅ Server running at: http://localhost:8000
```

**Submit XML Request:**
```bash
# Test complete pipeline processing
curl -X POST http://localhost:8000/api/pipeline/process \
  -F "file=@data/dataset_2/synthetic_dataset/UAE_XML/Patient_007_eclaim.xml" \
  -F "source=eclaim" \
  -s | jq '{"success": .success, "patient_id": .patient_id, "decision": .results.decision.outcome}'

# Expected Response:
# {"success": true, "patient_id": "Patient_007", "decision": "REVIEW"}
```

**Test Other Endpoints:**
```bash
# Health check
curl http://localhost:8000/api/health | jq .

# Get insurer notifications
curl http://localhost:8000/api/insurer/notifications | jq .

# View generated dossier (after processing a request)
curl http://localhost:8000/api/dossier/sample123 | jq .

# Get insurer request inbox
curl http://localhost:8000/api/insurer/requests | jq .
```

**Test with Different XML Formats:**
```bash
# eClaimLink format (Dubai)
curl -X POST http://localhost:8000/api/pipeline/process \
  -F "file=@data/dataset_2/synthetic_dataset/UAE_XML/Patient_007_eclaim.xml" \
  -F "source=eclaim"

# Shafafiya format (Abu Dhabi) - if available
curl -X POST http://localhost:8000/api/pipeline/process \
  -F "file=@path/to/shafafiya.xml" \
  -F "source=shafafiya"
```

### 3. Testing via FastAPI Interactive UI

**Access API Documentation:**
1. **Start Backend**: `PYTHONPATH=. python api/run_server.py`
2. **Open Browser**: Navigate to `http://localhost:8000/api/docs`
3. **Interactive Testing**: Use Swagger UI to test endpoints

**Key Endpoints to Test:**
- `POST /api/pipeline/process` - Upload XML file and test complete pipeline
- `GET /api/insurer/requests` - View processed requests
- `GET /api/insurer/notifications` - Check real-time notifications
- `GET /api/dossier/{analysis_id}` - View professional medical dossiers
- `GET /api/health` - System health and component status

**Step-by-Step FastAPI UI Testing:**
1. Click on `POST /api/pipeline/process`
2. Click "Try it out"
3. Upload `Patient_007_eclaim.xml` file
4. Set `source` to "eclaim"
5. Click "Execute"
6. Review complete JSON response with pipeline results

### 4. Testing via React Dashboard UI

**Start Both Services:**
```bash
# Terminal 1: Backend
PYTHONPATH=. python api/run_server.py

# Terminal 2: Frontend
cd ui-react && npm run dev
```

**Access Dashboard:**
- **URL**: `http://localhost:3000` (or `http://localhost:3001` if 3000 is occupied)
- **Professional Interface**: Designed for medical directors and insurance professionals

**Complete Workflow Testing:**

#### **Provider Workflow (XML Submission):**
1. **Navigate**: Go to "Pipeline Processing" or "Upload" section
2. **Upload XML**: Select `data/dataset_2/synthetic_dataset/UAE_XML/Patient_007_eclaim.xml`
3. **Watch Processing**: Real-time progress through 6 phases:
   - ✅ Intake & Normalization
   - ✅ Clinical Summarization  
   - ✅ Evidence Retrieval
   - ✅ Policy Evaluation
   - ✅ Decision Synthesis
   - ✅ Dossier Generation
4. **View Results**: Complete pipeline results with decision and reasoning

#### **Insurer Workflow (Dashboard Review):**
1. **Navigate**: Go to "Insurer Dashboard" 
2. **Request Inbox**: View all submitted PA requests with priority indicators
3. **Click Request**: Review complete request details including:
   - Patient history and clinical context
   - AI-generated clinical summary
   - Evidence and policy compliance
   - Professional medical dossier with citations
   - Recommended decision with confidence scores
4. **Make Decision**: Use decision interface to approve/deny/request more info
5. **Track Status**: Monitor request lifecycle and communications

#### **Analytics & Monitoring:**
1. **Dashboard Metrics**: Real-time processing statistics
2. **Decision Analytics**: Approval rates, processing times, cost efficiency
3. **System Health**: Component status and performance monitoring
4. **Recent Activity**: Latest processed requests and outcomes

**Expected Results for Patient_007:**
- **Processing Time**: ~30-40 seconds
- **Cost**: $0.00 (deterministic processing)
- **Decision**: APPROVE or REVIEW (depending on policy compliance)
- **Dossier**: Professional medical narrative with clinical reasoning
- **Patient History**: Integrated timeline with previous requests

### 5. End-to-End Workflow Validation

**Complete Insurer Workflow Test:**
```bash
# 1. Start both services
PYTHONPATH=. python api/run_server.py &
cd ui-react && npm run dev &

# 2. Submit request via API
curl -X POST http://localhost:8000/api/pipeline/process \
  -F "file=@data/dataset_2/synthetic_dataset/UAE_XML/Patient_007_eclaim.xml" \
  -F "xml_format=eclaim" > /tmp/result.json

# 3. Verify request appears in insurer dashboard
curl http://localhost:8000/api/insurer/requests | jq '.requests | length'

# 4. Check notifications
curl http://localhost:8000/api/insurer/notifications | jq '.total_count'
```

**Validation Checklist:**
- ✅ XML processed successfully through all 6 pipeline phases
- ✅ Request stored and appears in insurer dashboard
- ✅ Patient history integrated with new request
- ✅ Professional dossier generated with medical citations
- ✅ Decision made with clear reasoning and policy compliance
- ✅ Real-time notifications working
- ✅ Complete audit trail maintained for regulatory compliance

### Key Endpoints Reference

| Endpoint | Method | Purpose |
|----------|---------|---------|
| `/api/pipeline/process` | POST | Complete pipeline processing |
| `/api/insurer/requests` | GET | Request inbox for insurers |
| `/api/insurer/notifications` | GET | Real-time notifications |
| `/api/dossier/{analysis_id}` | GET | Professional medical dossiers |
| `/api/health` | GET | System health check |
| `/api/dashboard/summary` | GET | Analytics and metrics |

---

Built with FastAPI, DSPy, and AI-powered decision support following CLAUDE.md principles.