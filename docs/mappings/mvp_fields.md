# Minimal MVP Field List for Canonical Schema

## Overview
This document defines the minimal set of fields required for the MVP canonical schema, organized by category. These fields capture the essential data needed for prior authorization processing in the UAE healthcare system.

## Core Field Categories

### 1. Patient Information
- **patient_reference**: Reference to patient resource (required)
- **patient_identifier**: Patient ID/MRN (required)

### 2. Encounter/Transaction Details
- **transaction_id**: Unique identifier for the authorization request (required)
- **transaction_date**: When the request was created (required)
- **sender_id**: Provider/facility submitting request (required)
- **receiver_id**: Payer/TPA receiving request (required)
- **encounter_id**: Associated encounter/visit ID (optional)

### 3. Service/Procedure Information
- **service_items**: Array of requested services (required)
  - **sequence**: Line item number (required)
  - **service_code**: CPT/procedure code (required)
  - **service_type**: Type of service (required)
  - **service_date**: Date of service (required)
  - **quantity**: Number of units (required)

### 4. Financial Information
- **requested_amount**: Total amount requested (required)
- **currency**: Currency code (AED) (required)
- **net_amount**: Net amount per service (required)
- **payment_amount**: Approved payment amount (optional)

### 5. Clinical Information
- **diagnosis_codes**: Array of ICD-10 diagnosis codes (required)
- **justification_text**: Clinical justification/comments (optional but recommended)
- **instructions**: Special instructions for services (optional)

### 6. Authorization Status
- **authorization_status**: Current status (draft/active/completed) (required)
- **authorization_result**: Approval decision (approved/denied/partial) (optional)
- **authorization_id**: Payer's authorization number (optional)
- **denial_codes**: Reasons for denial (optional)
- **start_date**: Authorization validity start (required)
- **end_date**: Authorization validity end (required)

### 7. Metadata & Quality
- **schema_version**: Version of canonical schema used (required)
- **source_format**: Original data format (XML/CSV/PDF) (required)
- **data_quality_score**: Nazmito quality assessment (optional)
- **processing_timestamp**: When data was processed (required)

## Data Type Definitions

### Required Fields Summary
1. Transaction identifiers (ID, date, sender, receiver)
2. Patient reference
3. Service details (code, type, date, quantity)
4. Financial amounts (requested, net, currency)
5. Diagnosis codes
6. Authorization period (start/end dates)
7. Status information
8. Processing metadata

### Optional but Valuable Fields
1. Justification text (critical for auto-approval logic)
2. Payment amounts (for reconciliation)
3. Denial codes (for analytics)
4. Quality scores (for data governance)

## Rationale
This minimal field set ensures we can:
- Uniquely identify and track authorization requests
- Capture essential clinical context (diagnoses, services)
- Process financial aspects (amounts, currency)
- Support authorization workflows (status, approvals, denials)
- Maintain data quality and lineage
- Enable future ML/rules engine integration
