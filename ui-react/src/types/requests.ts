// Request Management Types

export type RequestStatus = 'approved' | 'pending' | 'denied' | 'under_review' | 'cancelled' | 'expired';
export type RequestPriority = 'low' | 'medium' | 'high' | 'urgent';
export type RequestType = 'authorization' | 'claim' | 'reimbursement' | 'eligibility';

export interface RequestHistoryItem {
  id: string;
  requestNumber: string;
  memberId: string;
  memberName: string;
  dateOfBirth: string;
  emiratesId: string;

  // Provider Information
  providerId: string;
  providerName: string;
  providerType: string;
  facility: string;

  // Request Details
  type: RequestType;
  status: RequestStatus;
  priority: RequestPriority;
  submissionDate: string;
  processedDate?: string;
  expiryDate?: string;

  // Clinical Information
  diagnosis: string;
  diagnosisCodes: string[];
  procedure: string;
  procedureCodes: string[];
  serviceDescription: string;

  // Financial Information
  requestedAmount: number;
  approvedAmount?: number;
  currency: string;

  // Processing Information
  format: 'eClaimLink' | 'Shafafiya' | 'CSV' | 'Manual';
  processingTime?: number; // in seconds
  assignedTo?: string;
  reviewedBy?: string;

  // Documents and Attachments
  documents: RequestDocument[];

  // Metadata
  createdAt: string;
  updatedAt: string;
  tags: string[];
  notes: string;
}

export interface RequestDocument {
  id: string;
  name: string;
  type: 'medical_report' | 'prescription' | 'lab_result' | 'imaging' | 'authorization_form' | 'other';
  size: number;
  uploadedAt: string;
  url: string;
}

export interface RequestStatusHistory {
  id: string;
  requestId: string;
  status: RequestStatus;
  timestamp: string;
  updatedBy: string;
  reason?: string;
  notes?: string;
}

export interface RequestAuditTrail {
  id: string;
  requestId: string;
  action: string;
  performedBy: string;
  timestamp: string;
  details: Record<string, any>;
  ipAddress?: string;
}

// Search and Filter Types
export interface RequestSearchCriteria {
  query?: string;
  status?: RequestStatus[];
  type?: RequestType[];
  priority?: RequestPriority[];
  dateRange?: {
    from: string;
    to: string;
  };
  amountRange?: {
    min: number;
    max: number;
  };
  providerId?: string[];
  assignedTo?: string[];
  tags?: string[];
  hasDocuments?: boolean;
}

export interface RequestSortOptions {
  field: keyof RequestHistoryItem;
  direction: 'asc' | 'desc';
}

export interface RequestFilters {
  search: RequestSearchCriteria;
  sort: RequestSortOptions;
  pagination: {
    page: number;
    pageSize: number;
  };
}

// Table and UI Types
export interface RequestTableColumn {
  key: keyof RequestHistoryItem | 'actions';
  label: string;
  sortable: boolean;
  width?: number;
  visible: boolean;
  format?: 'currency' | 'date' | 'status' | 'priority';
}

export interface RequestTableState {
  columns: RequestTableColumn[];
  selectedRows: string[];
  expandedRows: string[];
  filters: RequestFilters;
  isLoading: boolean;
  error?: string;
}

// Bulk Operations
export type BulkActionType = 'approve' | 'deny' | 'assign' | 'tag' | 'export' | 'delete';

export interface BulkAction {
  type: BulkActionType;
  label: string;
  icon: string;
  requiresConfirmation: boolean;
  isDestructive?: boolean;
}

export interface BulkOperationPayload {
  requestIds: string[];
  action: BulkActionType;
  data?: Record<string, any>;
}

// Saved Searches
export interface SavedSearch {
  id: string;
  name: string;
  description?: string;
  criteria: RequestSearchCriteria;
  isDefault?: boolean;
  createdAt: string;
  updatedAt: string;
}

// Export Types
export type RequestExportFormat = 'csv' | 'excel' | 'pdf';

export interface RequestExportOptions {
  format: RequestExportFormat;
  includeColumns: string[];
  includeFilters: boolean;
  dateRange?: {
    from: string;
    to: string;
  };
}

// API Response Types
export interface RequestHistoryResponse {
  success: boolean;
  data: {
    requests: RequestHistoryItem[];
    total: number;
    page: number;
    pageSize: number;
    totalPages: number;
  };
  error?: string;
}

export interface RequestDetailsResponse {
  success: boolean;
  data: {
    request: RequestHistoryItem;
    statusHistory: RequestStatusHistory[];
    auditTrail: RequestAuditTrail[];
  };
  error?: string;
}

// Performance and Caching
export interface RequestCacheEntry {
  key: string;
  data: RequestHistoryItem[];
  timestamp: number;
  filters: RequestFilters;
}

export interface VirtualScrollConfig {
  itemHeight: number;
  overscan: number;
  threshold: number;
}

// Quick Filters
export interface QuickFilter {
  id: string;
  label: string;
  icon: string;
  criteria: Partial<RequestSearchCriteria>;
  count?: number;
  color?: string;
}

// Dashboard Integration
export interface RequestMetrics {
  totalRequests: number;
  pendingRequests: number;
  approvedToday: number;
  averageProcessingTime: number;
  topProviders: Array<{
    id: string;
    name: string;
    requestCount: number;
  }>;
  statusDistribution: Record<RequestStatus, number>;
  monthlyTrends: Array<{
    month: string;
    approved: number;
    denied: number;
    pending: number;
  }>;
}
