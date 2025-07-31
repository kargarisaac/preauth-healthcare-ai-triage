# Nazmito – Intelligent AI-Powered Pre‑Authorization Platform

## Overview

Nazmito transforms manual healthcare pre-authorization processes in the UAE into intelligent clinical decision opportunities. Our AI-powered platform ingests multi-format healthcare data (XML, CSV, PDF, scanned documents), normalizes it to FHIR standards, and provides explainable clinical intelligence that reduces costs while improving patient outcomes.

**Key Differentiators:**
- **Deep UAE Integration**: Native support for eClaimLink (Dubai) and Shafafiya (Abu Dhabi) standards
- **Multi-Format Intelligence**: Handle structured data, PDFs, and scanned documents with OCR and NLP
- **Clinical Context**: AI agents provide explainable recommendations based on patient history and guidelines
- **Regulatory Compliance**: Built for UAE PDPL, ADHICS, and ISO 27001 requirements

## Business Impact

### Market Opportunity
- **TAM**: USD 224M–560M annually (9.3M UAE insured lives)
- **Target**: 30% chronic condition cohort (~2.8M lives)
- **Pricing**: USD 2–5 Per Member Per Month (PMPM)

### Value Proposition
- **40% reduction** in manual review processes
- **50% faster** authorization turnaround times
- **25% improvement** in clinical guideline adherence
- **Proactive chronic care** management preventing costly complications

## Technology Stack

### Architecture
- **Medallion Data Architecture**: Bronze (raw) → Silver (cleaned) → Gold (FHIR canonical)
- **AI-Powered Processing**: Vector embeddings, knowledge graphs, LLM agents
- **Event-Driven**: Kafka streaming for real-time processing
- **FHIR-Compliant**: International standards with UAE extensions

### Core Capabilities
1. **Multi-Format Ingestion**: XML (eClaimLink/Shafafiya), CSV, PDF table extraction, OCR for scanned documents
2. **Clinical NLP**: Fine-tuned models for Arabic/English medical text processing
3. **Knowledge Graphs**: Clinical reasoning with patient history and drug interactions
4. **Explainable AI**: Transparent decision-making with audit trails

## Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- `uv` package manager (ultra-fast Python dependency management)

### Installation
```bash
# Install uv package manager
curl -Ls https://astral.sh/uv/install.sh | sh

# Clone repository
git clone https://github.com/isaackargar/nazmito.git
cd nazmito

# Set up environment
uv venv .venv && source .venv/bin/activate
uv pip install -r pyproject.toml

# Start development environment
make demo
```

### Access Points
- **Streamlit UI**: http://localhost:8501 (Data audit and processing interface)
- **FastAPI Docs**: http://localhost:8000/docs (REST API documentation)
- **Kafka UI**: http://localhost:8080 (Event streaming dashboard)

### Quick Demo
```bash
# Load sample data (XML, CSV, PDF)
make ingest-sample

# View processed results in UI
open http://localhost:8501

# Query via API
curl http://localhost:8000/claim/PA-2025-000123
```

## Architecture & Documentation

### Technical Documentation
- **System Architecture**: [`docs/ARCHITECTURE.md`](/docs/ARCHITECTURE.md) - Complete technical design and data flow
- **FHIR Strategy**: [`docs/FHIR_GUIDE.md`](/docs/FHIR_GUIDE.md) - UAE FHIR implementation and clinical enhancements
- **Development Roadmap**: [`docs/todo_list.md`](/docs/todo_list.md) - Sprint-based development timeline

### Data Standards
- **UAE Compliance**: eClaimLink (Dubai), Shafafiya (Abu Dhabi), ICD-10-AM, CPT codes
- **FHIR Resources**: Claim, ServiceRequest, Observation, MedicationStatement with UAE extensions
- **Security**: AES-256 encryption, TLS 1.2+, RBAC, immutable audit logs

## 28-Day MVP Timeline

Our accelerated development approach delivers a complete platform in four 7-day sprints:

- **Sprint 1 (Days 1-7)**: Core data pipeline with multi-format ingestion
- **Sprint 2 (Days 8-14)**: Production API, audit UI, and demo packaging
- **Sprint 3 (Days 15-21)**: Advanced AI with knowledge graphs and semantic search
- **Sprint 4 (Days 22-28)**: LLM agents and explainable clinical decision support

See [`docs/todo_list.md`](/docs/todo_list.md) for detailed daily breakdown and implementation plan.

## Competitive Advantage

### vs. Traditional TPAs (NAS, Neuron, NextCare)
- **AI-Driven**: Proactive clinical intelligence vs. static rule engines
- **Comprehensive**: Multi-format data handling vs. limited XML processing
- **Clinical Context**: Historical data analysis vs. transaction-level decisions

### vs. Global Tech (Optum, eviCore)
- **UAE-Native**: Deep integration with local standards and regulations
- **Regional Expertise**: Arabic language support, Islamic calendar, local clinical practices
- **Regulatory Alignment**: PDPL/ADHICS compliance from the ground up

### vs. Regional Players (AppliedAI, Klaim, Wellx.ai)
- **Clinical Intelligence**: Advanced AI reasoning vs. basic automation
- **Pre-Authorization Focus**: Specialized authorization workflows vs. general claims processing
- **Explainable AI**: Transparent clinical decision-making vs. black-box algorithms

## Business Model & Go-to-Market

### Revenue Streams
- **Primary**: SaaS PMPM fees (USD 2-5 per member per month)
- **Pilot**: Per-request pricing for initial integrations
- **Value-Share**: 15-30% of validated medical cost savings

### Go-to-Market Strategy
1. **MVP Demo** (Month 2): Synthetic UAE data showcase
2. **Pilot Partners** (Months 3-4): LOIs with major UAE payers
3. **Technical Integration** (Months 3-6): 3-month integration + 3-month pilot
4. **Market Expansion** (Months 6-12): Additional payers and employers

## Compliance & Security

### UAE Regulatory Compliance
- **PDPL**: Personal Data Protection Law compliance framework
- **ADHICS**: Abu Dhabi Healthcare Cyber Security standards
- **DHA Standards**: Dubai Health Authority integration requirements
- **ISO 27001**: Information security management (certification planned Month 6)

### Data Protection
- **Encryption**: AES-256 at rest, TLS 1.2+ in transit
- **Access Control**: Role-based permissions with audit logging
- **Data Residency**: UAE data localization compliance
- **Immutable Audits**: Complete decision trail for regulatory review

## Investment & Funding

### Current Round
- **Amount**: USD 500K Seed funding
- **Use of Funds**: 50% Product Development, 30% Go-to-Market, 20% Compliance
- **Runway**: 18 months to first revenue and Series A preparation

### Team
- **Founder**: Isaac Kargar - AI scientist with GCC healthcare experience
- **Planned Hires**: Head of Engineering (FHIR expertise), Regulatory Lead
- **Advisors**: Former DHA/ADHICS officials, ex-Daman medical directors, UAE TPA executives

## Next Steps

### For Developers
1. Follow the Quick Start guide above
2. Review [`docs/todo_list.md`](/docs/todo_list.md) for development roadmap
3. Check [`docs/ARCHITECTURE.md`](/docs/ARCHITECTURE.md) for technical deep-dive

### For Investors
1. Schedule live demo with synthetic UAE healthcare data
2. Review detailed compliance roadmap and data protection policies
3. Discuss pilot partnership opportunities with UAE payers

### For Payers/Partners
1. Explore integration with existing authorization workflows
2. Review FHIR compliance and data mapping capabilities
3. Initiate pilot LOI/MOU discussions

**Contact**: [info@nazmito.com](mailto:info@nazmito.com) | [Schedule Demo](https://calendly.com/nazmito-demo)

---

*Nazmito transforms pre-authorization from administrative paperwork to proactive clinical intervention, significantly reducing healthcare costs while improving patient care in the UAE.*
