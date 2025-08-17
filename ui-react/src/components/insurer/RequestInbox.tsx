import React, { useState, useEffect, useMemo } from 'react';
import {
  Search,
  Filter,
  SortAsc,
  SortDesc,
  MoreHorizontal,
  Eye,
  User,
  Clock,
  DollarSign,
  AlertTriangle,
  CheckCircle,
  XCircle,
  TrendingUp,
  Calendar,
  Tag,
  RefreshCw,
  Download,
} from 'lucide-react';
import Button from '@components/ui/Button';
import Card from '@components/ui/Card';
import LoadingSpinner from '@components/ui/LoadingSpinner';
import { StatusBadge } from '@components/dashboard/StatusBadges';
import type {
  InsurerRequest,
  InsurerDashboardFilters,
  ReviewStatus,
  UrgencyLevel,
  DecisionType,
  RiskFlag,
} from '@/types/insurer';

// Priority and urgency configurations
const URGENCY_CONFIGS = {
  routine: { color: 'gray', icon: Clock, label: 'Routine' },
  urgent: { color: 'yellow', icon: AlertTriangle, label: 'Urgent' },
  emergency: { color: 'orange', icon: AlertTriangle, label: 'Emergency' },
  critical: { color: 'red', icon: AlertTriangle, label: 'Critical' },
} as const;

const AI_RECOMMENDATION_CONFIGS = {
  approve: { color: 'green', icon: CheckCircle, label: 'Approve' },
  deny: { color: 'red', icon: XCircle, label: 'Deny' },
  request_more_info: { color: 'blue', icon: AlertTriangle, label: 'More Info' },
  partial_approve: { color: 'yellow', icon: CheckCircle, label: 'Partial' },
} as const;

// Mock data - replace with actual API
const mockRequests: InsurerRequest[] = [
  {
    id: 'REQ-2025-001',
    requestNumber: 'PA-001-2025',
    memberId: 'MEM-789',
    memberName: 'Ahmed Al-Mansouri',
    dateOfBirth: '1985-03-15',
    emiratesId: '784-1985-1234567-8',
    providerId: 'PROV-001',
    providerName: 'Dubai Healthcare City',
    providerType: 'Hospital',
    facility: 'Cardiac Surgery Unit',
    type: 'authorization',
    status: 'pending',
    priority: 'high',
    submissionDate: '2025-08-17T10:30:00Z',
    diagnosis: 'Coronary Artery Disease',
    diagnosisCodes: ['I25.10'],
    procedure: 'Coronary Angioplasty',
    procedureCodes: ['92928'],
    serviceDescription: 'Percutaneous coronary intervention with drug-eluting stent',
    requestedAmount: 45000,
    currency: 'AED',
    format: 'eClaimLink',
    documents: [],
    createdAt: '2025-08-17T10:30:00Z',
    updatedAt: '2025-08-17T10:30:00Z',
    tags: ['cardiac', 'high-value'],
    notes: 'Urgent case - patient scheduled for procedure tomorrow',
    
    // Insurer-specific fields
    aiAnalysis: {
      recommendation: 'approve',
      confidence: 87,
      reasoning: 'Patient meets clinical criteria for PCI. Evidence supports medical necessity.',
      riskScore: 23,
      policyCompliance: 92,
      evidenceStrength: 85,
      clinicalNecessity: 91,
    },
    riskFlags: [
      {
        id: 'RF-001',
        type: 'financial',
        severity: 'medium',
        title: 'High Cost Procedure',
        description: 'Request amount exceeds standard threshold',
        recommendation: 'Verify medical necessity documentation',
        detectedAt: '2025-08-17T10:35:00Z',
        source: 'policy_engine',
      },
    ],
    qualityIndicators: [],
    urgency: 'urgent',
    reviewDeadline: '2025-08-18T16:00:00Z',
    communications: [],
    relatedRequests: [],
    patientHistory: [],
  },
  {
    id: 'REQ-2025-002',
    requestNumber: 'PA-002-2025',
    memberId: 'MEM-456',
    memberName: 'Fatima Hassan',
    dateOfBirth: '1992-07-22',
    emiratesId: '784-1992-9876543-2',
    providerId: 'PROV-002',
    providerName: 'Emirates Hospital',
    providerType: 'Specialty Clinic',
    facility: 'Orthopedic Department',
    type: 'authorization',
    status: 'under_review',
    priority: 'medium',
    submissionDate: '2025-08-16T14:20:00Z',
    diagnosis: 'Osteoarthritis of knee',
    diagnosisCodes: ['M17.1'],
    procedure: 'Total knee replacement',
    procedureCodes: ['27447'],
    serviceDescription: 'Total knee arthroplasty with prosthetic implant',
    requestedAmount: 28000,
    currency: 'AED',
    format: 'Shafafiya',
    documents: [],
    createdAt: '2025-08-16T14:20:00Z',
    updatedAt: '2025-08-17T09:15:00Z',
    tags: ['orthopedic'],
    notes: 'Patient has failed conservative treatment',
    assignedReviewer: 'Dr. Ahmed Al-Mansouri',
    assignedDate: '2025-08-17T09:15:00Z',
    
    aiAnalysis: {
      recommendation: 'request_more_info',
      confidence: 72,
      reasoning: 'Missing recent MRI results and physical therapy documentation',
      riskScore: 35,
      policyCompliance: 68,
      evidenceStrength: 65,
      clinicalNecessity: 78,
    },
    riskFlags: [
      {
        id: 'RF-002',
        type: 'clinical',
        severity: 'low',
        title: 'Incomplete Documentation',
        description: 'Missing recent imaging studies',
        recommendation: 'Request additional documentation',
        detectedAt: '2025-08-16T14:25:00Z',
        source: 'ai_analysis',
      },
    ],
    qualityIndicators: [],
    urgency: 'routine',
    reviewDeadline: '2025-08-19T17:00:00Z',
    communications: [],
    relatedRequests: [],
    patientHistory: [],
  },
];

interface RequestInboxProps {
  filters: InsurerDashboardFilters;
  onFiltersChange: (filters: InsurerDashboardFilters) => void;
  onRequestSelect: (requestId: string, patientId?: string) => void;
  showFilters?: boolean;
}

export const RequestInbox: React.FC<RequestInboxProps> = ({
  filters,
  onFiltersChange,
  onRequestSelect,
  showFilters = true,
}) => {
  const [requests, setRequests] = useState<InsurerRequest[]>(mockRequests);
  const [isLoading, setIsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortField, setSortField] = useState<keyof InsurerRequest>('submissionDate');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [selectedRequests, setSelectedRequests] = useState<string[]>([]);
  const [showFiltersPanel, setShowFiltersPanel] = useState(false);

  // Filter and sort requests
  const filteredRequests = useMemo(() => {
    let filtered = requests;

    // Apply search
    if (searchQuery) {
      filtered = filtered.filter(request =>
        request.memberName.toLowerCase().includes(searchQuery.toLowerCase()) ||
        request.requestNumber.toLowerCase().includes(searchQuery.toLowerCase()) ||
        request.diagnosis.toLowerCase().includes(searchQuery.toLowerCase()) ||
        request.providerName.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Apply filters
    if (filters.urgency.length > 0) {
      filtered = filtered.filter(request => filters.urgency.includes(request.urgency));
    }

    if (filters.aiRecommendation.length > 0) {
      filtered = filtered.filter(request => 
        filters.aiRecommendation.includes(request.aiAnalysis.recommendation)
      );
    }

    if (filters.hasRiskFlags) {
      filtered = filtered.filter(request => request.riskFlags.length > 0);
    }

    if (filters.amountRange) {
      filtered = filtered.filter(request => 
        request.requestedAmount >= filters.amountRange!.min &&
        request.requestedAmount <= filters.amountRange!.max
      );
    }

    // Sort
    filtered.sort((a, b) => {
      const aValue = a[sortField];
      const bValue = b[sortField];
      
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        const comparison = aValue.localeCompare(bValue);
        return sortDirection === 'asc' ? comparison : -comparison;
      }
      
      if (typeof aValue === 'number' && typeof bValue === 'number') {
        const comparison = aValue - bValue;
        return sortDirection === 'asc' ? comparison : -comparison;
      }
      
      return 0;
    });

    return filtered;
  }, [requests, searchQuery, filters, sortField, sortDirection]);

  const handleSort = (field: keyof InsurerRequest) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const handleSelectRequest = (requestId: string, checked: boolean) => {
    if (checked) {
      setSelectedRequests([...selectedRequests, requestId]);
    } else {
      setSelectedRequests(selectedRequests.filter(id => id !== requestId));
    }
  };

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedRequests(filteredRequests.map(req => req.id));
    } else {
      setSelectedRequests([]);
    }
  };

  const getRiskLevel = (request: InsurerRequest): 'low' | 'medium' | 'high' | 'critical' => {
    const riskScore = request.aiAnalysis.riskScore;
    if (riskScore >= 80) return 'critical';
    if (riskScore >= 60) return 'high';
    if (riskScore >= 30) return 'medium';
    return 'low';
  };

  const formatTimeRemaining = (deadline: string): string => {
    const now = new Date();
    const deadlineDate = new Date(deadline);
    const diff = deadlineDate.getTime() - now.getTime();
    
    if (diff < 0) return 'Overdue';
    
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const days = Math.floor(hours / 24);
    
    if (days > 0) return `${days}d ${hours % 24}h`;
    return `${hours}h`;
  };

  return (
    <div className="space-y-6">
      {/* Header with Search and Filters */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
        <div>
          <h2 className="text-xl font-bold text-gray-900 dark:text-dark-text-primary">
            Request Inbox
          </h2>
          <p className="text-sm text-gray-600 dark:text-dark-text-secondary">
            {filteredRequests.length} of {requests.length} requests
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <Button
            variant="tertiary"
            onClick={() => setIsLoading(true)}
            disabled={isLoading}
          >
            {isLoading ? <LoadingSpinner size="sm" /> : <RefreshCw className="w-4 h-4" />}
            {!isLoading && 'Refresh'}
          </Button>
          
          {selectedRequests.length > 0 && (
            <Button variant="secondary">
              Bulk Actions ({selectedRequests.length})
            </Button>
          )}
        </div>
      </div>

      {/* Search and Filter Bar */}
      <Card className="p-4">
        <div className="flex flex-col sm:flex-row space-y-3 sm:space-y-0 sm:space-x-3">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search requests, patients, providers..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-dark-border-primary rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-dark-bg-secondary dark:text-dark-text-primary"
            />
          </div>
          
          {/* Filter Toggle */}
          {showFilters && (
            <Button
              variant="tertiary"
              onClick={() => setShowFiltersPanel(!showFiltersPanel)}
              className={showFiltersPanel ? 'bg-blue-50 text-blue-700' : ''}
            >
              <Filter className="w-4 h-4 mr-2" />
              Filters
              {Object.values(filters).some(v => Array.isArray(v) ? v.length > 0 : v) && (
                <span className="ml-2 px-1.5 py-0.5 bg-blue-100 text-blue-800 rounded-full text-xs">
                  •
                </span>
              )}
            </Button>
          )}
        </div>
        
        {/* Filters Panel */}
        {showFiltersPanel && (
          <div className="mt-4 pt-4 border-t border-gray-200 dark:border-dark-border-primary">
            <FilterPanel
              filters={filters}
              onFiltersChange={onFiltersChange}
            />
          </div>
        )}
      </Card>

      {/* Request Table */}
      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-dark-border-primary">
            <thead className="bg-gray-50 dark:bg-dark-bg-tertiary">
              <tr>
                <th className="px-6 py-3 text-left">
                  <input
                    type="checkbox"
                    checked={selectedRequests.length === filteredRequests.length && filteredRequests.length > 0}
                    onChange={(e) => handleSelectAll(e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-dark-text-secondary uppercase tracking-wider cursor-pointer"
                    onClick={() => handleSort('submissionDate')}>
                  <div className="flex items-center space-x-1">
                    <span>Submitted</span>
                    {sortField === 'submissionDate' && (
                      sortDirection === 'asc' ? <SortAsc className="w-4 h-4" /> : <SortDesc className="w-4 h-4" />
                    )}
                  </div>
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-dark-text-secondary uppercase tracking-wider">
                  Request Details
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-dark-text-secondary uppercase tracking-wider">
                  Patient
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-dark-text-secondary uppercase tracking-wider">
                  AI Analysis
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-dark-text-secondary uppercase tracking-wider cursor-pointer"
                    onClick={() => handleSort('requestedAmount')}>
                  <div className="flex items-center space-x-1">
                    <span>Amount</span>
                    {sortField === 'requestedAmount' && (
                      sortDirection === 'asc' ? <SortAsc className="w-4 h-4" /> : <SortDesc className="w-4 h-4" />
                    )}
                  </div>
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-dark-text-secondary uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-dark-text-secondary uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-dark-bg-secondary divide-y divide-gray-200 dark:divide-dark-border-primary">
              {filteredRequests.map((request) => {
                const urgencyConfig = URGENCY_CONFIGS[request.urgency];
                const aiRecommendationConfig = AI_RECOMMENDATION_CONFIGS[request.aiAnalysis.recommendation];
                const riskLevel = getRiskLevel(request);
                const timeRemaining = formatTimeRemaining(request.reviewDeadline);
                const isOverdue = timeRemaining === 'Overdue';
                
                return (
                  <tr key={request.id} className="hover:bg-gray-50 dark:hover:bg-dark-bg-tertiary">
                    <td className="px-6 py-4">
                      <input
                        type="checkbox"
                        checked={selectedRequests.includes(request.id)}
                        onChange={(e) => handleSelectRequest(request.id, e.target.checked)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                    </td>
                    
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900 dark:text-dark-text-primary">
                        {new Date(request.submissionDate).toLocaleDateString()}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-dark-text-secondary">
                        {new Date(request.submissionDate).toLocaleTimeString()}
                      </div>
                      <div className={`text-xs font-medium mt-1 ${
                        isOverdue ? 'text-red-600' : 'text-gray-600 dark:text-dark-text-secondary'
                      }`}>
                        {timeRemaining}
                      </div>
                    </td>
                    
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-gray-900 dark:text-dark-text-primary">
                        {request.requestNumber}
                      </div>
                      <div className="text-sm text-gray-600 dark:text-dark-text-secondary">
                        {request.procedure}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-dark-text-secondary">
                        {request.diagnosis}
                      </div>
                      <div className="flex items-center space-x-2 mt-1">
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium
                          ${urgencyConfig.color === 'red' ? 'bg-red-100 text-red-800' :
                            urgencyConfig.color === 'orange' ? 'bg-orange-100 text-orange-800' :
                            urgencyConfig.color === 'yellow' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-gray-100 text-gray-800'}`}>
                          {urgencyConfig.label}
                        </span>
                        {request.riskFlags.length > 0 && (
                          <span className="px-2 py-0.5 bg-red-100 text-red-800 rounded-full text-xs font-medium">
                            {request.riskFlags.length} flag{request.riskFlags.length > 1 ? 's' : ''}
                          </span>
                        )}
                      </div>
                    </td>
                    
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-gray-900 dark:text-dark-text-primary">
                        {request.memberName}
                      </div>
                      <div className="text-sm text-gray-600 dark:text-dark-text-secondary">
                        ID: {request.memberId}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-dark-text-secondary">
                        {request.providerName}
                      </div>
                    </td>
                    
                    <td className="px-6 py-4">
                      <div className="flex items-center space-x-2">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium
                          ${aiRecommendationConfig.color === 'green' ? 'bg-green-100 text-green-800' :
                            aiRecommendationConfig.color === 'red' ? 'bg-red-100 text-red-800' :
                            aiRecommendationConfig.color === 'blue' ? 'bg-blue-100 text-blue-800' :
                            'bg-yellow-100 text-yellow-800'}`}>
                          {aiRecommendationConfig.label}
                        </span>
                      </div>
                      <div className="text-xs text-gray-600 dark:text-dark-text-secondary mt-1">
                        Confidence: {request.aiAnalysis.confidence}%
                      </div>
                      <div className="text-xs text-gray-500 dark:text-dark-text-secondary">
                        Risk: {riskLevel}
                      </div>
                    </td>
                    
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900 dark:text-dark-text-primary">
                        {new Intl.NumberFormat('en-AE', {
                          style: 'currency',
                          currency: request.currency,
                        }).format(request.requestedAmount)}
                      </div>
                    </td>
                    
                    <td className="px-6 py-4 whitespace-nowrap">
                      <StatusBadge status={request.status} />
                      {request.assignedReviewer && (
                        <div className="text-xs text-gray-500 dark:text-dark-text-secondary mt-1">
                          Assigned to: {request.assignedReviewer}
                        </div>
                      )}
                    </td>
                    
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center space-x-2">
                        <Button
                          variant="tertiary"
                          size="sm"
                          onClick={() => onRequestSelect(request.id, request.memberId)}
                          className="p-2"
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="tertiary"
                          size="sm"
                          className="p-2"
                        >
                          <MoreHorizontal className="w-4 h-4" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        
        {filteredRequests.length === 0 && (
          <div className="text-center py-12">
            <Search className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-dark-text-primary mb-2">
              No requests found
            </h3>
            <p className="text-gray-600 dark:text-dark-text-secondary">
              Try adjusting your search criteria or filters.
            </p>
          </div>
        )}
      </Card>
    </div>
  );
};

// Filter Panel Component
interface FilterPanelProps {
  filters: InsurerDashboardFilters;
  onFiltersChange: (filters: InsurerDashboardFilters) => void;
}

const FilterPanel: React.FC<FilterPanelProps> = ({ filters, onFiltersChange }) => {
  const updateFilter = (key: keyof InsurerDashboardFilters, value: any) => {
    onFiltersChange({
      ...filters,
      [key]: value,
    });
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Urgency Filter */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-dark-text-primary mb-2">
          Urgency
        </label>
        <div className="space-y-2">
          {Object.entries(URGENCY_CONFIGS).map(([urgency, config]) => (
            <label key={urgency} className="flex items-center">
              <input
                type="checkbox"
                checked={filters.urgency.includes(urgency as UrgencyLevel)}
                onChange={(e) => {
                  if (e.target.checked) {
                    updateFilter('urgency', [...filters.urgency, urgency as UrgencyLevel]);
                  } else {
                    updateFilter('urgency', filters.urgency.filter(u => u !== urgency));
                  }
                }}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 mr-2"
              />
              <span className="text-sm text-gray-900 dark:text-dark-text-primary">
                {config.label}
              </span>
            </label>
          ))}
        </div>
      </div>
      
      {/* AI Recommendation Filter */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-dark-text-primary mb-2">
          AI Recommendation
        </label>
        <div className="space-y-2">
          {Object.entries(AI_RECOMMENDATION_CONFIGS).map(([recommendation, config]) => (
            <label key={recommendation} className="flex items-center">
              <input
                type="checkbox"
                checked={filters.aiRecommendation.includes(recommendation as DecisionType)}
                onChange={(e) => {
                  if (e.target.checked) {
                    updateFilter('aiRecommendation', [...filters.aiRecommendation, recommendation as DecisionType]);
                  } else {
                    updateFilter('aiRecommendation', filters.aiRecommendation.filter(r => r !== recommendation));
                  }
                }}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 mr-2"
              />
              <span className="text-sm text-gray-900 dark:text-dark-text-primary">
                {config.label}
              </span>
            </label>
          ))}
        </div>
      </div>
      
      {/* Risk Level Filter */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-dark-text-primary mb-2">
          Risk Level
        </label>
        <div className="space-y-2">
          {['low', 'medium', 'high', 'critical'].map((level) => (
            <label key={level} className="flex items-center">
              <input
                type="checkbox"
                checked={filters.riskLevel.includes(level as any)}
                onChange={(e) => {
                  if (e.target.checked) {
                    updateFilter('riskLevel', [...filters.riskLevel, level as any]);
                  } else {
                    updateFilter('riskLevel', filters.riskLevel.filter(r => r !== level));
                  }
                }}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 mr-2"
              />
              <span className="text-sm text-gray-900 dark:text-dark-text-primary capitalize">
                {level}
              </span>
            </label>
          ))}
        </div>
      </div>
      
      {/* Additional Filters */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-dark-text-primary mb-2">
          Additional
        </label>
        <div className="space-y-2">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={filters.hasRiskFlags}
              onChange={(e) => updateFilter('hasRiskFlags', e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 mr-2"
            />
            <span className="text-sm text-gray-900 dark:text-dark-text-primary">
              Has Risk Flags
            </span>
          </label>
          
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={filters.requiresEscalation}
              onChange={(e) => updateFilter('requiresEscalation', e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 mr-2"
            />
            <span className="text-sm text-gray-900 dark:text-dark-text-primary">
              Requires Escalation
            </span>
          </label>
        </div>
      </div>
    </div>
  );
};
