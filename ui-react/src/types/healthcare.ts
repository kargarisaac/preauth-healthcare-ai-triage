// Healthcare Data Types
export interface FHIRBundle {
  resourceType: 'Bundle';
  id: string;
  meta: {
    versionId: string;
    lastUpdated: string;
  };
  type: string;
  timestamp: string;
  total: number;
  authorization_id?: string;
  sender?: string;
  receiver?: string;
  fhir_resources: Record<string, FHIRResource>;
  raw_data: any;
}

export interface FHIRResource {
  resourceType: string;
  id: string;
  [key: string]: any;
}

export interface ProcessingRequest {
  id: string;
  memberName: string;
  memberId: string;
  provider: string;
  service: string;
  amount: string;
  status: 'Approved' | 'Pending' | 'Denied';
  date: string;
  format: 'eClaimLink' | 'Shafafiya' | 'CSV';
}

// Enhanced Member Management Types
export interface Demographics {
  firstName: string;
  lastName: string;
  fullName: string;
  dateOfBirth: string;
  gender: 'male' | 'female' | 'other';
  nationality: string;
  preferredLanguage: string;
  maritalStatus: 'single' | 'married' | 'divorced' | 'widowed';
}

export interface ContactInformation {
  phone: string;
  alternativePhone?: string;
  email: string;
  address: {
    street: string;
    city: string;
    emirate: string;
    country: string;
    postalCode: string;
  };
  emergencyContact: {
    name: string;
    relationship: string;
    phone: string;
  };
}

export interface InsuranceDetails {
  provider: string;
  policyNumber: string;
  groupNumber?: string;
  planType: string;
  effectiveDate: string;
  expirationDate: string;
  deductible: number;
  coPayment: number;
  outOfPocketMax: number;
  benefitYear: string;
  status: 'active' | 'inactive' | 'suspended';
}

export interface ChronicCondition {
  id: string;
  condition: string;
  icdCode: string;
  diagnosisDate: string;
  severity: 'mild' | 'moderate' | 'severe';
  status: 'active' | 'resolved' | 'chronic';
  managingProvider: string;
  medications: string[];
  lastReview: string;
}

export interface MedicalHistory {
  allergies: Array<{
    allergen: string;
    severity: 'mild' | 'moderate' | 'severe';
    reaction: string;
  }>;
  chronicConditions: ChronicCondition[];
  surgicalHistory: Array<{
    procedure: string;
    date: string;
    hospital: string;
    complications?: string;
  }>;
  familyHistory: Array<{
    relationship: string;
    condition: string;
    ageOfOnset?: number;
  }>;
}

export interface CostUtilization {
  yearToDate: {
    totalCosts: number;
    memberPaid: number;
    planPaid: number;
    deductibleMet: number;
    outOfPocketMet: number;
  };
  monthlyTrends: Array<{
    month: string;
    totalCosts: number;
    visits: number;
    prescriptions: number;
  }>;
  topCategories: Array<{
    category: string;
    amount: number;
    percentage: number;
  }>;
}

export interface Member {
  id: string;
  emiratesId: string;
  demographics: Demographics;
  contact: ContactInformation;
  insurance: InsuranceDetails;
  medicalHistory: MedicalHistory;
  costUtilization: CostUtilization;
  recentRequests: ProcessingRequest[];
  riskScore: number;
  lastActivity: string;
  createdAt: string;
  updatedAt: string;
}

// Search and Filter Types
export interface SearchCriteria {
  query?: string;
  emiratesId?: string;
  policyNumber?: string;
  phone?: string;
  email?: string;
  provider?: string;
  planType?: string;
  status?: string;
  riskLevel?: 'low' | 'medium' | 'high';
  hasChronicConditions?: boolean;
  ageRange?: {
    min: number;
    max: number;
  };
  dateRange?: {
    start: string;
    end: string;
  };
}

export interface SearchResult {
  members: Member[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
  filters: {
    providers: string[];
    planTypes: string[];
    emirates: string[];
    riskLevels: string[];
  };
}

export interface SearchSuggestion {
  id: string;
  type: 'member' | 'provider' | 'policy' | 'condition';
  value: string;
  label: string;
  memberCount?: number;
}

// Care Management Types
export interface CareGap {
  id: string;
  memberId: string;
  type: 'preventive' | 'chronic_care' | 'medication_adherence' | 'follow_up';
  category: string;
  description: string;
  recommendation: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  dueDate: string;
  status: 'open' | 'scheduled' | 'completed' | 'closed';
  evidenceBase: string;
  potentialCostSaving: number;
  assignedProvider?: string;
  createdAt: string;
  updatedAt: string;
}

export interface InterventionRecommendation {
  id: string;
  memberId: string;
  type: 'lifestyle' | 'medication' | 'screening' | 'referral';
  title: string;
  description: string;
  expectedOutcome: string;
  timeframe: string;
  priority: 'low' | 'medium' | 'high';
  costEstimate: number;
  qualityMeasure?: string;
  status: 'recommended' | 'approved' | 'scheduled' | 'completed';
}

export interface QualityMetric {
  measure: string;
  description: string;
  target: number;
  current: number;
  trend: 'improving' | 'stable' | 'declining';
  lastUpdated: string;
  benchmark: number;
}

// Timeline and History Types
export interface MemberActivity {
  id: string;
  memberId: string;
  type: 'authorization' | 'claim' | 'appointment' | 'communication' | 'care_gap' | 'intervention';
  title: string;
  description: string;
  status: string;
  amount?: number;
  provider?: string;
  outcome?: string;
  timestamp: string;
  metadata: Record<string, any>;
}

export interface AuthorizationHistory {
  id: string;
  requestDate: string;
  serviceType: string;
  provider: string;
  requestedAmount: number;
  approvedAmount?: number;
  status: 'approved' | 'denied' | 'pending' | 'expired';
  decisionReason?: string;
  reviewNotes?: string;
  reviewedBy?: string;
  reviewDate?: string;
  appealStatus?: 'none' | 'filed' | 'approved' | 'denied';
}

// Voice Search and Accessibility Types
export interface VoiceSearchCapability {
  isSupported: boolean;
  isListening: boolean;
  confidence: number;
  transcript: string;
  error?: string;
}

export interface BarcodeSearchResult {
  type: 'emirates_id' | 'insurance_card' | 'member_id';
  value: string;
  confidence: number;
}

// Mobile and Offline Types
export interface OfflineSearchCache {
  members: Member[];
  lastSync: string;
  searchHistory: string[];
  recentMembers: string[];
}

export interface DashboardMetrics {
  activeRequests: number;
  autoApproved: number;
  avgResponseTime: string;
  costSavings: string;
  approvedCount: number;
  pendingCount: number;
  deniedCount: number;
}
