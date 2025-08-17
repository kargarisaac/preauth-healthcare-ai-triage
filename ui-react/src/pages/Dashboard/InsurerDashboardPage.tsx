import React, { useState, useEffect, useMemo } from 'react';
import {
  Bell,
  Filter,
  Search,
  Users,
  Clock,
  AlertTriangle,
  CheckCircle,
  XCircle,
  TrendingUp,
  FileText,
  Settings,
} from 'lucide-react';
import { useTheme } from '@contexts/ThemeContext';
import { useToast } from '@contexts/ToastContext';
import Card from '@components/ui/Card';
import Button from '@components/ui/Button';
import LoadingSpinner from '@components/ui/LoadingSpinner';
import { RequestInbox } from '@components/insurer/RequestInbox';
import { PatientHistoryTimeline } from '@components/insurer/PatientHistoryTimeline';
import { RequestReviewInterface } from '@components/insurer/RequestReviewInterface';
import { DecisionWorkflow } from '@components/insurer/DecisionWorkflow';
import { InsurerNotifications } from '@components/insurer/InsurerNotifications';
import { InsurerAnalytics } from '@components/insurer/InsurerAnalytics';
import type {
  InsurerRequest,
  InsurerMetrics,
  InsurerDashboardFilters,
  ReviewStatus,
  UrgencyLevel,
  DecisionType,
} from '@/types/insurer';

// Mock data service - replace with actual API calls
const mockInsurerMetrics: InsurerMetrics = {
  workload: {
    totalPending: 24,
    underReview: 8,
    overdueReviews: 3,
    avgReviewTime: 18,
    decisionsToday: 12,
  },
  performance: {
    approvalRate: 76.5,
    aiAgreementRate: 88.2,
    overrideRate: 11.8,
    avgDecisionTime: 14.5,
    qualityScore: 92.3,
  },
  distribution: {
    byUrgency: {
      routine: 15,
      urgent: 6,
      emergency: 2,
      critical: 1,
    },
    byAmount: [
      { range: '0-1K', count: 8 },
      { range: '1K-5K', count: 12 },
      { range: '5K-10K', count: 4 },
      { range: '10K+', count: 0 },
    ],
    byRiskLevel: {
      low: 10,
      medium: 8,
      high: 5,
      critical: 1,
    },
    byProvider: [
      { name: 'Dubai Healthcare City', count: 8, approvalRate: 85.2 },
      { name: 'Emirates Hospital', count: 6, approvalRate: 78.9 },
      { name: 'Mediclinic', count: 5, approvalRate: 92.1 },
    ],
  },
  trends: {
    dailyVolume: [
      { date: '2025-08-10', requests: 32, decisions: 28 },
      { date: '2025-08-11', requests: 28, decisions: 31 },
      { date: '2025-08-12', requests: 35, decisions: 29 },
      { date: '2025-08-13', requests: 41, decisions: 36 },
      { date: '2025-08-14', requests: 38, decisions: 42 },
      { date: '2025-08-15', requests: 29, decisions: 35 },
      { date: '2025-08-16', requests: 31, decisions: 33 },
    ],
    monthlyApprovals: [
      { month: 'Jun 2025', approved: 328, denied: 84 },
      { month: 'Jul 2025', approved: 342, denied: 91 },
      { month: 'Aug 2025', approved: 215, denied: 47 },
    ],
  },
};

interface ViewState {
  currentView: 'overview' | 'inbox' | 'review' | 'analytics';
  selectedRequestId?: string;
  selectedPatientId?: string;
  showPatientHistory: boolean;
}

const InsurerDashboardPage: React.FC = () => {
  const [viewState, setViewState] = useState<ViewState>({
    currentView: 'inbox',
    showPatientHistory: false,
  });
  const [metrics, setMetrics] = useState<InsurerMetrics>(mockInsurerMetrics);
  const [filters, setFilters] = useState<InsurerDashboardFilters>({
    status: [],
    urgency: [],
    riskLevel: [],
    aiRecommendation: [],
    hasRiskFlags: false,
    requiresEscalation: false,
  });
  const [isLoading, setIsLoading] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);

  const { isDarkMode } = useTheme();
  const { showToast } = useToast();

  // Filter active requests based on current filters
  const activeFilters = useMemo(() => {
    const hasActiveFilters =
      filters.status.length > 0 ||
      filters.urgency.length > 0 ||
      filters.riskLevel.length > 0 ||
      filters.aiRecommendation.length > 0 ||
      filters.hasRiskFlags ||
      filters.requiresEscalation ||
      filters.amountRange ||
      filters.dateRange;
    
    return hasActiveFilters;
  }, [filters]);

  // Handle request selection for review
  const handleRequestSelect = (requestId: string, patientId?: string) => {
    setViewState({
      currentView: 'review',
      selectedRequestId: requestId,
      selectedPatientId: patientId,
      showPatientHistory: Boolean(patientId),
    });
  };

  // Handle decision submission
  const handleDecisionSubmit = async (decision: any) => {
    try {
      setIsLoading(true);
      // API call to submit decision
      await new Promise(resolve => setTimeout(resolve, 1000)); // Mock delay
      
      showToast({
        type: 'success',
        title: 'Decision Submitted',
        message: 'The authorization decision has been processed successfully.',
      });
      
      // Return to inbox
      setViewState({ currentView: 'inbox', showPatientHistory: false });
      
      // Refresh metrics
      // await refreshMetrics();
    } catch (error) {
      showToast({
        type: 'error',
        title: 'Submission Failed',
        message: 'Failed to submit decision. Please try again.',
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Navigation items
  const navigationItems = [
    {
      id: 'overview',
      label: 'Overview',
      icon: TrendingUp,
      count: undefined,
    },
    {
      id: 'inbox',
      label: 'Request Inbox',
      icon: FileText,
      count: metrics?.workload?.totalPending || 0,
    },
    {
      id: 'analytics',
      label: 'Analytics',
      icon: TrendingUp,
      count: undefined,
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-dark-bg-primary">
      {/* Header */}
      <header className="bg-white dark:bg-dark-bg-secondary shadow-sm border-b border-gray-200 dark:border-dark-border-primary">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Users className="h-8 w-8 text-blue-600" />
                <div>
                  <h1 className="text-xl font-bold text-gray-900 dark:text-dark-text-primary">
                    Medical Director Dashboard
                  </h1>
                  <p className="text-sm text-gray-600 dark:text-dark-text-secondary">
                    Pre-Authorization Review & Decision Management
                  </p>
                </div>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* Quick Stats */}
              <div className="hidden md:flex items-center space-x-6 text-sm">
                <div className="flex items-center space-x-2">
                  <Clock className="h-4 w-4 text-orange-500" />
                  <span className="text-gray-600 dark:text-dark-text-secondary">
                    {metrics?.workload?.overdueReviews} overdue
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <AlertTriangle className="h-4 w-4 text-red-500" />
                  <span className="text-gray-600 dark:text-dark-text-secondary">
                    {metrics.distribution.byRiskLevel.critical + metrics.distribution.byRiskLevel.high} high risk
                  </span>
                </div>
              </div>
              
              {/* Notifications */}
              <div className="relative">
                <Button
                  variant="tertiary"
                  onClick={() => setNotificationsOpen(!notificationsOpen)}
                  className="p-2 relative"
                >
                  <Bell className="h-5 w-5" />
                  {metrics?.workload?.overdueReviews > 0 && (
                    <span className="absolute -top-1 -right-1 h-4 w-4 bg-red-500 rounded-full text-xs text-white flex items-center justify-center">
                      {metrics?.workload?.overdueReviews}
                    </span>
                  )}
                </Button>
                {notificationsOpen && (
                  <InsurerNotifications
                    onClose={() => setNotificationsOpen(false)}
                    onRequestSelect={handleRequestSelect}
                  />
                )}
              </div>
              
              {/* User Profile */}
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center">
                  <span className="text-blue-600 dark:text-blue-400 font-medium text-sm">DA</span>
                </div>
                <div className="hidden sm:block">
                  <p className="text-sm font-medium text-gray-900 dark:text-dark-text-primary">
                    Dr. Ahmed Al-Mansouri
                  </p>
                  <p className="text-xs text-gray-600 dark:text-dark-text-secondary">
                    Medical Director
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {viewState.currentView === 'inbox' && (
          <RequestInbox
            filters={filters}
            onFiltersChange={setFilters}
            onRequestSelect={handleRequestSelect}
            showFilters={true}
          />
        )}
        
        {viewState.currentView === 'review' && viewState.selectedRequestId && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <Button
                variant="tertiary"
                onClick={() => setViewState({ currentView: 'inbox', showPatientHistory: false })}
              >
                ← Back to Inbox
              </Button>
              <Button
                variant="secondary"
                onClick={() => setViewState(prev => ({
                  ...prev,
                  showPatientHistory: !prev.showPatientHistory
                }))}
              >
                {viewState.showPatientHistory ? 'Hide' : 'Show'} Patient History
              </Button>
            </div>
            
            <div className={`grid gap-6 ${
              viewState.showPatientHistory ? 'grid-cols-1 xl:grid-cols-3' : 'grid-cols-1'
            }`}>
              {viewState.showPatientHistory && viewState.selectedPatientId && (
                <div className="xl:col-span-1">
                  <PatientHistoryTimeline
                    patientId={viewState.selectedPatientId}
                    currentRequestId={viewState.selectedRequestId}
                  />
                </div>
              )}
              
              <div className={viewState.showPatientHistory ? 'xl:col-span-2' : 'col-span-1'}>
                <RequestReviewInterface
                  requestId={viewState.selectedRequestId}
                  onDecisionSubmit={handleDecisionSubmit}
                  isSubmitting={isLoading}
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};


export default InsurerDashboardPage;
