// Insurer Dashboard Types

import type { RequestHistoryItem, RequestStatus, RequestPriority } from './requests';
import type { Member, AuthorizationHistory } from './healthcare';

// Decision Management Types
export type DecisionType = 'approve' | 'deny' | 'request_more_info' | 'partial_approve';
export type ReviewStatus = 'pending' | 'under_review' | 'reviewed' | 'escalated';
export type UrgencyLevel = 'routine' | 'urgent' | 'emergency' | 'critical';

// Extended Request for Insurer View
export interface InsurerRequest extends RequestHistoryItem {
  // AI Analysis Results
  aiAnalysis: {
    recommendation: DecisionType;
    confidence: number; // 0-100
    reasoning: string;
    riskScore: number; // 0-100
    policyCompliance: number; // 0-100
    evidenceStrength: number; // 0-100
    clinicalNecessity: number; // 0-100
  };
  
  // Risk and Flag Indicators
  riskFlags: RiskFlag[];
  qualityIndicators: QualityIndicator[];
  
  // Processing Information
  urgency: UrgencyLevel;
  reviewDeadline: string;
  escalationPath?: string[];
  
  // Reviewer Assignment
  assignedReviewer?: string;
  assignedDate?: string;
  
  // Communication History
  communications: CommunicationRecord[];
  
  // Related Cases
  relatedRequests: string[];
  patientHistory: PatientHistoryEntry[];
}

// Risk and Quality Indicators
export interface RiskFlag {
  id: string;
  type: 'clinical' | 'financial' | 'policy' | 'fraud' | 'safety';
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  recommendation: string;
  detectedAt: string;
  source: 'ai_analysis' | 'policy_engine' | 'manual_review';
}

export interface QualityIndicator {
  id: string;
  metric: string;
  value: number;
  benchmark: number;
  status: 'below' | 'meets' | 'exceeds';
  trend: 'improving' | 'stable' | 'declining';
  description: string;
}

// Communication and Notes
export interface CommunicationRecord {
  id: string;
  type: 'internal_note' | 'provider_communication' | 'member_communication' | 'system_message';
  direction: 'inbound' | 'outbound';
  subject: string;
  content: string;
  sender: string;
  recipient: string;
  timestamp: string;
  status: 'sent' | 'delivered' | 'read' | 'responded';
  attachments?: string[];
}

// Patient History Integration
export interface PatientHistoryEntry {
  id: string;
  type: 'authorization' | 'claim' | 'treatment' | 'prescription' | 'hospitalization';
  date: string;
  provider: string;
  service: string;
  diagnosis: string;
  outcome: string;
  cost: number;
  status: string;
  relevanceScore: number; // How relevant to current request
}

// Decision Management
export interface MedicalDirectorDecision {
  id: string;
  requestId: string;
  decision: DecisionType;
  reasoning: string;
  conditions?: string[];
  limitations?: string[];
  followUpRequired: boolean;
  followUpInstructions?: string;
  overrideAI: boolean;
  overrideReason?: string;
  reviewedBy: string;
  reviewDate: string;
  effectiveDate?: string;
  expirationDate?: string;
  appealable: boolean;
}

// Workflow Management
export interface WorkflowState {
  stage: 'intake' | 'ai_analysis' | 'medical_review' | 'decision' | 'communication' | 'closed';
  assignedTo?: string;
  dueDate?: string;
  escalationTriggers: EscalationTrigger[];
  approvalLimits: ApprovalLimit[];
}

export interface EscalationTrigger {
  condition: string;
  threshold: number;
  escalateTo: string;
  timeLimit: number; // minutes
}

export interface ApprovalLimit {
  role: string;
  maxAmount: number;
  conditions: string[];
}

// Dashboard Filters and Search
export interface InsurerDashboardFilters {
  status: ReviewStatus[];
  urgency: UrgencyLevel[];
  assignedReviewer?: string[];
  riskLevel: ('low' | 'medium' | 'high' | 'critical')[];
  aiRecommendation: DecisionType[];
  amountRange?: {
    min: number;
    max: number;
  };
  dateRange?: {
    from: string;
    to: string;
  };
  hasRiskFlags: boolean;
  requiresEscalation: boolean;
}

// Analytics and Metrics
export interface InsurerMetrics {
  workload: {
    totalPending: number;
    underReview: number;
    overdueReviews: number;
    avgReviewTime: number; // minutes
    decisionsToday: number;
  };
  
  performance: {
    approvalRate: number;
    aiAgreementRate: number; // How often MD agrees with AI
    overrideRate: number;
    avgDecisionTime: number;
    qualityScore: number;
  };
  
  distribution: {
    byUrgency: Record<UrgencyLevel, number>;
    byAmount: Array<{ range: string; count: number }>;
    byRiskLevel: Record<string, number>;
    byProvider: Array<{ name: string; count: number; approvalRate: number }>;
  };
  
  trends: {
    dailyVolume: Array<{ date: string; requests: number; decisions: number }>;
    monthlyApprovals: Array<{ month: string; approved: number; denied: number }>;
  };
}

// Batch Operations
export interface BatchOperation {
  id: string;
  type: 'bulk_approve' | 'bulk_deny' | 'bulk_assign' | 'bulk_escalate';
  requestIds: string[];
  criteria: Record<string, any>;
  createdBy: string;
  createdAt: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  progress: number; // 0-100
  results?: {
    successful: number;
    failed: number;
    errors: string[];
  };
}

// Templates and Automation
export interface DecisionTemplate {
  id: string;
  name: string;
  description: string;
  decision: DecisionType;
  conditions: Array<{
    field: string;
    operator: 'equals' | 'greater_than' | 'less_than' | 'contains';
    value: any;
  }>;
  reasoning: string;
  limitations?: string[];
  followUpActions?: string[];
  active: boolean;
  usage: number;
  lastUsed?: string;
}

// Mobile and Accessibility
export interface MobileNotification {
  id: string;
  type: 'urgent_review' | 'escalation' | 'deadline_approaching' | 'new_assignment';
  title: string;
  message: string;
  requestId?: string;
  priority: 'low' | 'medium' | 'high';
  timestamp: string;
  read: boolean;
  actionRequired: boolean;
}

// Real-time Updates
export interface RealtimeUpdate {
  type: 'new_request' | 'status_change' | 'assignment' | 'escalation' | 'decision';
  requestId: string;
  data: Record<string, any>;
  timestamp: string;
  affectedUsers: string[];
}

// Export consolidated types
export type {
  RequestHistoryItem,
  RequestStatus,
  RequestPriority,
  Member,
  AuthorizationHistory,
};
