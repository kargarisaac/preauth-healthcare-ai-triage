import { RequestHistoryItem, ProcessingMetrics, MemberProfile } from '@types/index'

export const mockRequestHistoryItem: RequestHistoryItem = {
  id: 'test-request-1',
  fileName: 'test-claim.xml',
  fileType: 'xml',
  status: 'completed',
  timestamp: new Date('2024-01-15T10:30:00Z'),
  processingTime: 2.5,
  fileSize: 1024 * 50, // 50KB
  recordCount: 25,
  validationErrors: [],
  fhirBundle: {
    resourceType: 'Bundle',
    id: 'bundle-1',
    type: 'collection',
    timestamp: '2024-01-15T10:30:00Z',
    entry: []
  },
  metadata: {
    sender: 'Test Insurance Co',
    receiver: 'Test Hospital',
    totalAmount: 15000,
    currency: 'AED',
    claimCount: 5,
    memberCount: 3
  }
}

export const mockProcessingMetrics: ProcessingMetrics = {
  totalFiles: 150,
  successfulFiles: 142,
  failedFiles: 8,
  averageProcessingTime: 3.2,
  totalRecordsProcessed: 12500,
  errorRate: 0.053,
  lastProcessed: new Date('2024-01-15T14:45:00Z')
}

export const mockMemberProfile: MemberProfile = {
  id: 'member-123',
  name: 'Ahmed Al-Mansouri',
  emiratesId: '784-1990-1234567-1',
  policyNumber: 'POL-2024-001',
  insuranceProvider: 'Emirates Insurance',
  membershipType: 'Family',
  status: 'Active',
  dateOfBirth: '1990-05-15',
  gender: 'Male',
  contactInfo: {
    phone: '+971-50-123-4567',
    email: 'ahmed.almansouri@email.com',
    address: {
      street: 'Sheikh Zayed Road',
      city: 'Dubai',
      emirate: 'Dubai',
      postalCode: '12345'
    }
  },
  coverage: {
    inpatient: true,
    outpatient: true,
    dental: true,
    optical: false,
    maternity: true
  },
  limits: {
    annual: 500000,
    remaining: 425000,
    currency: 'AED'
  },
  dependents: [
    {
      id: 'dep-1',
      name: 'Fatima Al-Mansouri',
      relationship: 'Spouse',
      dateOfBirth: '1992-08-20',
      status: 'Active'
    },
    {
      id: 'dep-2',
      name: 'Omar Al-Mansouri',
      relationship: 'Son',
      dateOfBirth: '2015-03-10',
      status: 'Active'
    }
  ],
  recentClaims: [
    {
      id: 'claim-1',
      date: '2024-01-10',
      provider: 'Dubai Hospital',
      amount: 2500,
      status: 'Approved',
      type: 'Outpatient'
    },
    {
      id: 'claim-2',
      date: '2024-01-05',
      provider: 'American Hospital',
      amount: 15000,
      status: 'Pending',
      type: 'Inpatient'
    }
  ]
}

export const mockFileUpload = {
  file: new File(['test content'], 'test.xml', { type: 'text/xml' }),
  progress: 0,
  status: 'pending' as const,
  error: null
}

export const mockChartData = {
  dailyProcessing: [
    { date: '2024-01-01', files: 15, errors: 1 },
    { date: '2024-01-02', files: 23, errors: 2 },
    { date: '2024-01-03', files: 18, errors: 0 },
    { date: '2024-01-04', files: 31, errors: 3 },
    { date: '2024-01-05', files: 28, errors: 1 }
  ],
  processingTimes: [
    { fileType: 'XML', averageTime: 2.3, count: 45 },
    { fileType: 'CSV', averageTime: 1.8, count: 32 },
    { fileType: 'JSON', averageTime: 1.2, count: 28 }
  ],
  errorDistribution: [
    { type: 'Validation', count: 12, percentage: 45 },
    { type: 'Format', count: 8, percentage: 30 },
    { type: 'Network', count: 4, percentage: 15 },
    { type: 'System', count: 3, percentage: 11 }
  ]
}

export const mockApiResponses = {
  processFile: {
    success: {
      id: 'process-123',
      status: 'completed',
      result: mockRequestHistoryItem,
      processingTime: 2.5
    },
    error: {
      error: 'Invalid file format',
      code: 'INVALID_FORMAT',
      details: 'The uploaded file is not a valid XML or CSV format'
    }
  },
  requestHistory: {
    items: [mockRequestHistoryItem],
    total: 1,
    page: 1,
    limit: 10
  },
  analytics: {
    metrics: mockProcessingMetrics,
    charts: mockChartData
  }
}

// Test utilities for creating mock data with overrides
export const createMockRequestHistoryItem = (overrides: Partial<RequestHistoryItem> = {}): RequestHistoryItem => ({
  ...mockRequestHistoryItem,
  ...overrides,
  id: overrides.id || `test-request-${Date.now()}`,
  timestamp: overrides.timestamp || new Date()
})

export const createMockMemberProfile = (overrides: Partial<MemberProfile> = {}): MemberProfile => ({
  ...mockMemberProfile,
  ...overrides,
  id: overrides.id || `member-${Date.now()}`
})

export const createMockFile = (name = 'test.xml', type = 'text/xml', content = 'test content'): File => {
  return new File([content], name, { type })
}
