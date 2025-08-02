import type {
  RequestHistoryItem,
  RequestStatusHistory,
  RequestAuditTrail,
  RequestDocument,
  RequestStatus,
  RequestPriority,
  RequestType,
} from '@/types/requests';

// Mock data generators for testing
const MEMBER_NAMES = [
  'Ahmed Al Mansouri', 'Fatima Al Zahra', 'Mohammed bin Rashid', 'Aisha Al Maktoum',
  'Omar Al Nahyan', 'Mariam Al Otaiba', 'Khalid Al Qasimi', 'Layla Al Thani',
  'Saeed Al Marri', 'Noura Al Suwaidi', 'Hamdan Al Ketbi', 'Sheikha Al Mazrouei',
];

const PROVIDER_NAMES = [
  'Dubai Hospital', 'Cleveland Clinic Abu Dhabi', 'American Hospital Dubai',
  'Mediclinic City Hospital', 'NMC Royal Hospital', 'Zulekha Hospital',
  'Al Zahra Hospital', 'Prime Hospital', 'Aster Hospital', 'Burjeel Hospital',
];

const DIAGNOSES = [
  'Type 2 Diabetes Mellitus', 'Essential Hypertension', 'Acute Myocardial Infarction',
  'Chronic Kidney Disease', 'Pneumonia', 'Fracture of femur', 'Appendicitis',
  'Gastroenteritis', 'Migraine', 'Asthma', 'Coronary Artery Disease',
];

const PROCEDURES = [
  'Cardiac Catheterization', 'MRI Scan', 'CT Scan', 'Blood Test Panel',
  'Surgical Consultation', 'Physical Therapy', 'Endoscopy', 'Ultrasound',
  'X-Ray Examination', 'ECG', 'Colonoscopy', 'Biopsy',
];

const PROCEDURE_CODES = [
  'CPT-93458', 'CPT-70553', 'CPT-74177', 'CPT-80053',
  'CPT-99244', 'CPT-97110', 'CPT-43235', 'CPT-76700',
  'CPT-73060', 'CPT-93000', 'CPT-45378', 'CPT-88305',
];

const DIAGNOSIS_CODES = [
  'E11.9', 'I10', 'I21.9', 'N18.6', 'J18.9', 'S72.90XA',
  'K35.9', 'K59.1', 'G43.909', 'J45.9', 'I25.10',
];

const TAGS = [
  'urgent', 'follow-up', 'complex-case', 'high-value', 'review-required',
  'expedite', 'surgical', 'outpatient', 'emergency', 'routine',
];

const REVIEWERS = [
  'Dr. Sarah Ahmed', 'Dr. Mohammed Hassan', 'Fatima Ali', 'Omar Khalil', 'Aisha Ibrahim',
];

const FACILITIES = [
  'Main Campus', 'Outpatient Center', 'Emergency Department', 'Surgical Center',
  'Diagnostic Center', 'Rehabilitation Center', 'Cardiac Center', 'Cancer Center',
];

// Generate random values
const randomChoice = <T>(array: T[]): T => array[Math.floor(Math.random() * array.length)];
const randomChoices = <T>(array: T[], count: number): T[] => {
  const shuffled = [...array].sort(() => 0.5 - Math.random());
  return shuffled.slice(0, count);
};
const randomDate = (start: Date, end: Date): string => {
  return new Date(start.getTime() + Math.random() * (end.getTime() - start.getTime())).toISOString();
};
const randomAmount = (min: number, max: number): number => {
  return Math.floor(Math.random() * (max - min + 1)) + min;
};

export function generateMockRequestHistory(count: number = 100): RequestHistoryItem[] {
  const requests: RequestHistoryItem[] = [];
  const now = new Date();
  const sixMonthsAgo = new Date(now.getFullYear(), now.getMonth() - 6, now.getDate());

  for (let i = 0; i < count; i++) {
    const submissionDate = randomDate(sixMonthsAgo, now);
    const processedDate = Math.random() > 0.3 ? randomDate(new Date(submissionDate), now) : undefined;
    const memberName = randomChoice(MEMBER_NAMES);
    const providerName = randomChoice(PROVIDER_NAMES);
    const diagnosis = randomChoice(DIAGNOSES);
    const procedure = randomChoice(PROCEDURES);
    const status = randomChoice(['approved', 'pending', 'denied', 'under_review', 'cancelled', 'expired'] as RequestStatus[]);
    const priority = randomChoice(['low', 'medium', 'high', 'urgent'] as RequestPriority[]);
    const type = randomChoice(['authorization', 'claim', 'reimbursement', 'eligibility'] as RequestType[]);
    const requestedAmount = randomAmount(500, 50000);
    const approvedAmount = status === 'approved' ? randomAmount(Math.floor(requestedAmount * 0.8), requestedAmount) : undefined;

    const request: RequestHistoryItem = {
      id: `req_${i + 1}`,
      requestNumber: `REQ-${new Date().getFullYear()}-${String(i + 1).padStart(6, '0')}`,
      memberId: `MBR-${String(i + 1).padStart(8, '0')}`,
      memberName,
      dateOfBirth: randomDate(new Date(1950, 0, 1), new Date(2000, 11, 31)),
      emiratesId: `784-${String(Math.floor(Math.random() * 10000000000)).padStart(10, '0')}`,
      
      providerId: `PRV-${String(Math.floor(Math.random() * 1000)).padStart(4, '0')}`,
      providerName,
      providerType: randomChoice(['Hospital', 'Clinic', 'Specialist', 'Laboratory', 'Pharmacy']),
      facility: randomChoice(FACILITIES),
      
      type,
      status,
      priority,
      submissionDate,
      processedDate,
      expiryDate: randomDate(new Date(submissionDate), new Date(new Date(submissionDate).getTime() + 90 * 24 * 60 * 60 * 1000)),
      
      diagnosis,
      diagnosisCodes: [randomChoice(DIAGNOSIS_CODES)],
      procedure,
      procedureCodes: [randomChoice(PROCEDURE_CODES)],
      serviceDescription: `${procedure} for ${diagnosis.toLowerCase()}`,
      
      requestedAmount,
      approvedAmount,
      currency: 'AED',
      
      format: randomChoice(['eClaimLink', 'Shafafiya', 'CSV', 'Manual'] as const),
      processingTime: Math.random() > 0.5 ? randomAmount(5, 300) : undefined,
      assignedTo: Math.random() > 0.4 ? randomChoice(REVIEWERS) : undefined,
      reviewedBy: processedDate ? randomChoice(REVIEWERS) : undefined,
      
      documents: generateMockDocuments(randomAmount(0, 5)),
      
      createdAt: submissionDate,
      updatedAt: processedDate || submissionDate,
      tags: randomChoices(TAGS, randomAmount(0, 3)),
      notes: Math.random() > 0.7 ? generateMockNotes() : '',
    };

    requests.push(request);
  }

  return requests.sort((a, b) => new Date(b.submissionDate).getTime() - new Date(a.submissionDate).getTime());
}

function generateMockDocuments(count: number): RequestDocument[] {
  const documents: RequestDocument[] = [];
  const documentTypes: RequestDocument['type'][] = ['medical_report', 'prescription', 'lab_result', 'imaging', 'authorization_form', 'other'];
  const now = new Date();
  const oneMonthAgo = new Date(now.getFullYear(), now.getMonth() - 1, now.getDate());

  for (let i = 0; i < count; i++) {
    const type = randomChoice(documentTypes);
    documents.push({
      id: `doc_${Date.now()}_${i}`,
      name: `${type.replace('_', '-')}-${Date.now()}.pdf`,
      type,
      size: randomAmount(50000, 5000000), // 50KB to 5MB
      uploadedAt: randomDate(oneMonthAgo, now),
      url: `/api/documents/${Date.now()}_${i}`,
    });
  }

  return documents;
}

function generateMockNotes(): string {
  const notes = [
    'Patient requires additional documentation for prior authorization.',
    'Medical necessity has been established through clinical review.',
    'Follow-up required with treating physician for clarification.',
    'Duplicate request - referring to original submission.',
    'Urgent case due to patient condition - expedited processing required.',
    'Additional imaging studies needed before approval.',
    'Insurance verification completed - proceeding with authorization.',
    'Complex case requiring multi-disciplinary review.',
    'Patient has history of similar procedures - approved based on previous outcomes.',
    'Coordination of care required with multiple specialists.',
  ];
  
  return randomChoice(notes);
}

export function generateMockStatusHistory(requestId: string): RequestStatusHistory[] {
  const statuses: RequestStatus[] = ['pending', 'under_review', 'approved'];
  const history: RequestStatusHistory[] = [];
  const now = new Date();
  let currentDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000); // 7 days ago

  statuses.forEach((status, index) => {
    history.push({
      id: `status_${requestId}_${index}`,
      requestId,
      status,
      timestamp: currentDate.toISOString(),
      updatedBy: randomChoice(REVIEWERS),
      reason: index === 2 ? 'Medical necessity confirmed through clinical review' : undefined,
      notes: index === 1 ? 'Additional documentation reviewed and found satisfactory' : undefined,
    });
    
    currentDate = new Date(currentDate.getTime() + randomAmount(1, 3) * 24 * 60 * 60 * 1000);
  });

  return history;
}

export function generateMockAuditTrail(requestId: string): RequestAuditTrail[] {
  const actions = [
    'Request submitted',
    'Initial review started',
    'Documents uploaded',
    'Assigned to reviewer',
    'Medical review completed',
    'Status updated to approved',
    'Notification sent to provider',
  ];

  return actions.map((action, index) => ({
    id: `audit_${requestId}_${index}`,
    requestId,
    action,
    performedBy: randomChoice(REVIEWERS),
    timestamp: new Date(Date.now() - (actions.length - index) * 60 * 60 * 1000).toISOString(),
    details: {
      action_type: action.toLowerCase().replace(/\s+/g, '_'),
      metadata: {
        user_agent: 'Nazmito Dashboard v1.0',
        session_id: `sess_${Math.random().toString(36).substring(7)}`,
      },
    },
    ipAddress: `192.168.1.${Math.floor(Math.random() * 254) + 1}`,
  }));
}

// Mock API responses
export const mockRequestHistoryResponse = {
  success: true,
  data: {
    requests: generateMockRequestHistory(50),
    total: 247,
    page: 1,
    pageSize: 25,
    totalPages: 10,
  },
};

export const mockRequestDetailsResponse = (requestId: string) => ({
  success: true,
  data: {
    request: generateMockRequestHistory(1)[0],
    statusHistory: generateMockStatusHistory(requestId),
    auditTrail: generateMockAuditTrail(requestId),
  },
});

// Helper to create mock data for development
export function setupMockData() {
  // Store mock data in localStorage for development
  const mockData = {
    requests: generateMockRequestHistory(100),
    timestamp: Date.now(),
  };
  
  localStorage.setItem('nazmito_mock_requests', JSON.stringify(mockData));
  console.log('Mock request data generated and stored in localStorage');
}