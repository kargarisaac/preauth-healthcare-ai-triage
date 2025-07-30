# Nazmito – Intelligent AI-Powered Pre‑Authorization Platform

## Problem Statement

Mandatory pre-authorization processes in UAE healthcare insurance are highly inefficient, manual, and reactive. Current systems primarily use static rule engines managed by third-party administrators (TPAs) or internal insurer portals, which lack proactive intelligence. This manual approach generates unnecessary administrative costs, delays patient care by days, frustrates healthcare providers, and misses significant opportunities for proactive chronic care management.

Chronic conditions, such as diabetes, hypertension, and cardiovascular diseases, represent a substantial portion of healthcare costs. Specifically, chronic diseases account for approximately 35% of healthcare spending due to complications that could often be prevented through early, targeted interventions. Manual reviews add costs and complexity, with roughly 40% of requests still manually processed, taking approximately 3 days on average.

## Nazmito’s Solution

Nazmito introduces an intelligent, proactive AI-driven layer to the existing pre-authorization workflows, transforming them from mere administrative checkpoints into opportunities for cost savings, quality improvement, and enhanced patient outcomes.

### Detailed Workflow

1. **Ingestion & Enrichment:**

   * Data Sources: Claims data (XML/EDI), pharmacy records, lab results; EMR data via HL7/FHIR (planned).
   * Process: Data normalization, quality scoring, identification of clinical guideline gaps.

2. **Decision & Incentivization:**

   * AI Engine: Applies rule-based and machine learning (ML) algorithms to identify optimal care pathways.
   * Output: Returns enriched, pre-approved care pathways, bundles overdue tests or screenings, suggests cost-effective equivalent medications, and includes provider incentives to encourage guideline adherence.

3. **Explanation & Learning:**

   * Transparency: Audit trails showing detailed rationale, rules triggered, model versions, and citations.
   * Continuous Improvement: Feedback loops from outcomes, quarterly updates to models and rules, publication of confusion matrices, and performance benchmarks.

## Market Opportunity

### Total Addressable Market (TAM)

* UAE Insured Population: \~9.3 million insured lives by 2025.
* Pricing Model: USD 2–5 Per Member Per Month (PMPM).
* TAM: USD 224M–560M annually (9.3M lives × USD 2–5 × 12 months).

### Serviceable Available Market (SAM)

* Chronic Condition Cohort: Approximately 30% of insured lives (\~2.8 million).
* SAM: Approximately USD 84M annually (2.8M chronic lives × USD 2.5 PMPM × 12 months).

### Serviceable Obtainable Market (SOM)

* Target Market by Year 3: Approximately 120,000 chronic members across initial payers.
* SOM: Approximately USD 3.6M annual recurring revenue (120,000 × USD 2.5 PMPM × 12 months).

## Competitive Landscape

Nazmito differentiates itself clearly from existing competitors by providing proactive, AI-driven, chronic-care focused authorization processes specifically tailored to UAE regulations and practices.

### Incumbent TPAs

* **NAS, Neuron, NextCare, MedNet:** Provide basic, static rule engines with manual-intensive processes. Limited proactive management of chronic care or automated incentives.

### Clinical Guidelines Providers

* **InterQual, MCG (Milliman Care Guidelines):** Offer static, evidence-based guidelines. Lack personalization and proactive, patient-centric recommendations or gap closures.

### Global Technology Companies

* **Optum, eviCore:** Primarily US-focused, powerful technology but limited regional presence, local compliance, or direct UAE market integration.

### Local and Regional Health Tech Companies

* **AppliedAI:** UAE-based startup focusing on insurance claims automation and billing processes, but lacks a dedicated pre-authorization or proactive chronic care management solution.
* **OlaDoc/Okadoc:** Patient-facing apps primarily for doctor appointment booking and basic insurance integration, but limited direct involvement in proactive authorization.
* **Klaim, Wellx.ai, HealthGena, Bayzat:** Regional players mostly focused on claims management, insurance brokerage, or patient experience apps without deep pre-authorization intelligence or chronic care proactive management.

### Nazmito’s Unique Value Proposition

* Deep integration with existing UAE digital rails (Shafafiya in Abu Dhabi, eClaimLink in Dubai).
* Robust compliance tailored to UAE standards (PDPL, ADHICS, ISO 27001).
* AI-driven proactive intervention specifically targeting chronic-care cost containment.
* Transparent audit trails providing clear rationales and measurable ROI.

## Technology and Governance

* **Inputs:** Claims, labs, pharmacy data (initially), HL7/FHIR EMR integration (later).
* **Pipeline:** Data ingestion → quality scoring → rules & ML algorithms → optimization & incentives → decision & rationale generation.
* **Governance Structure:** Clinical Advisory Board consisting of two medical doctors and one coder, quarterly audits, and continuous outcome monitoring.
* **Compliance Roadmap:**

  * Month 3: Complete PDPL/DHA compliance gap analysis, appoint Data Protection Officer.
  * Month 6: Initiate ISO 27001 certification process.
  * Month 9: Achieve ADHICS attestation.
  * Month 12: Obtain SOC 2 Type I compliance.
* **Security Measures:** AES-256 encryption at rest, TLS 1.2+ encryption in transit, role-based access controls (RBAC), and immutable audit logs.

## Canonical Schema Overview

Nazmito uses a unified canonical schema based on FHIR (Fast Healthcare Interoperability Resources) standards to normalize healthcare data from various sources. This ensures consistent data processing regardless of the input format (eClaimLink XML, Shafafiya XML, CSV, or PDF).

### Key Components:

1. **FHIR-Based Structure**: Built on FHIR Claim and ServiceRequest resources, ensuring international healthcare interoperability
2. **UAE-Specific Extensions**: Custom extensions for regional requirements (disposition flags, activity types, etc.)
3. **Multi-Format Support**: Unified mapping from both 2019/11 PriorAuthorizationRequest and 2011 Prior.Authorization formats
4. **Data Quality Tracking**: Built-in extensions for quality scores, processing metadata, and audit trails

### Schema Documentation:

- **Canonical Schema**: `schemas/canonical_schema.json` - JSON Schema definition for validated data structure
- **Field Mappings**: `docs/mappings/field_map_v0.csv` - Complete mapping from source formats to FHIR fields
- **MVP Fields**: `docs/mappings/mvp_fields.md` - Minimal required fields for authorization processing
- **Example Data**: `canonical/examples/claim_example.json` - Sample canonical format claim

### Data Flow:

```
Source Data (XML/CSV/PDF) → Normalization → Canonical FHIR Format → Enrichment → Decision Engine
```

This canonical approach enables:
- Consistent downstream processing
- Easy integration with FHIR-compliant systems
- Clear audit trails and data lineage
- Flexible addition of new data sources

## Business Model

* **Primary Model:** SaaS-based PMPM fee.
* **Alternate Pilot Model:** Per-request fees for initial pilots.
* **Value-Share Option:** 15–30% of validated medical cost savings, capped to ensure affordability.
* **Liability & Insurance:** Decision support only (insurers retain final authorization responsibility). Nazmito maintains professional indemnity and tech E\&O coverage.

## Go-To-Market & Traction Strategy

* **Initial Steps:**

  * Develop and showcase synthetic live demonstration (Month 2).
  * Secure Letters of Intent (LOIs) and Memoranda of Understanding (MOUs) from initial pilot partners (Month 3–4).
* **Pilot Plan:**

  * Execute 3-month technical integration followed by a 3-month operational pilot.
  * Measure key performance indicators (KPIs): reduced manual review percentage, turnaround times, and proxy medical loss ratio (MLR) impacts.
* **Growth & Expansion:**

  * Use pilot outcomes to produce case studies.
  * Expand to additional payers and self-funded employers.
  * Enhance product offerings with advanced forecasting and fraud, waste, and abuse (FWA) modules.

## 18-Month Roadmap (With Seed Funding)

* **Months 0–3:** Synthetic demo, initial compliance roadmap, hire advisory team.
* **Months 3–6:** First pilot execution, ISO preparation, initial EMR integration.
* **Months 6–12:** Second pilot launch, publish performance results, SOC 2 Type I compliance.
* **Months 12–18:** Launch additional product features (forecasting, FWA analytics), prepare for next funding round (Seed+ or Series A).

## Team

* **Founder & CEO:** Isaac, AI scientist with extensive experience in healthcare-focused ML product development and GCC regional healthcare ecosystem.
* **Planned Hires:**

  * Founding Head of Engineering (FHIR/claims expertise).
  * Regulatory & Compliance Lead.
* **Advisors:** Experienced professionals including former DHA/ADHICS officials, ex-Daman medical directors, and senior executives from major UAE TPAs (e.g., NAS).

## Funding Request

* **Amount:** USD 500K Seed.
* **Use of Funds:** Product Development (50%), Go-To-Market Activities (30%), Compliance and Operational Costs (20%).
* **Runway:** 18 months.

## Next Steps for Investors

* Schedule a detailed live product demonstration with synthetic UAE claims.
* Review compliance roadmap and data protection policies.
* Finalize and initiate pilot LOI/MOU and integration activities.

Nazmito transforms pre-authorization from administrative paperwork to proactive clinical intervention, significantly reducing healthcare costs and improving patient care in the UAE.
