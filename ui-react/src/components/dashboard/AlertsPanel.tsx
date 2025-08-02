import React, { useState, useMemo } from 'react';
import {
  AlertTriangle,
  AlertCircle,
  Clock,
  Heart,
  Shield,
  TrendingUp,
  TrendingDown,
  Activity,
  DollarSign,
  Calendar,
  Pill,
  Users,
  Eye,
  Zap,
  CheckCircle,
  XCircle,
  Filter,
  ArrowUp,
  ArrowDown,
  ChevronRight,
  Bell,
  MessageCircle
} from 'lucide-react';
import {
  CareGap,
  InterventionRecommendation,
  Member,
  QualityMetric
} from '../../types/healthcare';
import { useCareGaps } from '../../hooks/health/useCareGaps';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';

interface AlertsPanelProps {
  memberId?: string;
  member?: Member;
  careGaps?: CareGap[];
  recommendations?: InterventionRecommendation[];
  qualityMetrics?: QualityMetric[];
  onAlertClick?: (alert: CareGap | InterventionRecommendation) => void;
  onViewAllCareGaps?: () => void;
  onScheduleIntervention?: (recommendationId: string) => void;
  className?: string;
  compact?: boolean;
  showFilters?: boolean;
}

interface AlertFilter {
  priority: 'all' | 'urgent' | 'high' | 'medium' | 'low';
  type: 'all' | 'care_gaps' | 'recommendations' | 'quality_metrics';
  status: 'all' | 'open' | 'scheduled' | 'completed';
}

export const AlertsPanel: React.FC<AlertsPanelProps> = ({
  memberId,
  member,
  careGaps: propCareGaps,
  recommendations: propRecommendations,
  qualityMetrics: propQualityMetrics,
  onAlertClick,
  onViewAllCareGaps,
  onScheduleIntervention,
  className = '',
  compact = false,
  showFilters = true
}) => {
  const [filters, setFilters] = useState<AlertFilter>({
    priority: 'all',
    type: 'all',
    status: 'all'
  });
  const [showFiltersPanel, setShowFiltersPanel] = useState(false);

  // Use care gaps hook if member ID provided
  const {
    careGaps: hookCareGaps,
    recommendations: hookRecommendations,
    qualityMetrics: hookQualityMetrics,
    analysis,
    isLoading,
    error,
    updateCareGapStatus
  } = useCareGaps(memberId);

  // Use prop data or hook data
  const careGaps = propCareGaps || hookCareGaps;
  const recommendations = propRecommendations || hookRecommendations;
  const qualityMetrics = propQualityMetrics || hookQualityMetrics;

  // Format currency
  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-AE', {
      style: 'currency',
      currency: 'AED',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  // Format date
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays <= 1) return 'Today';
    if (diffDays <= 7) return `${diffDays} days`;
    if (diffDays <= 30) return `${Math.ceil(diffDays / 7)} weeks`;
    return date.toLocaleDateString('en-AE', { month: 'short', day: 'numeric' });
  };

  // Get priority configuration
  const getPriorityConfig = (priority: string) => {
    const configs = {
      urgent: {
        color: 'text-red-600',
        bgColor: 'bg-red-100',
        icon: AlertTriangle,
        label: 'Urgent'
      },
      high: {
        color: 'text-orange-600',
        bgColor: 'bg-orange-100',
        icon: AlertCircle,
        label: 'High'
      },
      medium: {
        color: 'text-yellow-600',
        bgColor: 'bg-yellow-100',
        icon: Clock,
        label: 'Medium'
      },
      low: {
        color: 'text-blue-600',
        bgColor: 'bg-blue-100',
        icon: Activity,
        label: 'Low'
      }
    };

    return configs[priority as keyof typeof configs] || configs.medium;
  };

  // Get type icon
  const getTypeIcon = (type: string) => {
    const icons = {
      preventive: Eye,
      chronic_care: Heart,
      medication_adherence: Pill,
      follow_up: Calendar,
      lifestyle: Activity,
      medication: Pill,
      screening: Shield,
      referral: Users
    };

    return icons[type as keyof typeof icons] || Activity;
  };

  // Calculate days until due/overdue
  const getDaysUntilDue = (dueDate: string): { days: number; isOverdue: boolean } => {
    const today = new Date();
    const due = new Date(dueDate);
    const diffTime = due.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    return {
      days: Math.abs(diffDays),
      isOverdue: diffDays < 0
    };
  };

  // Filter and sort alerts
  const filteredCareGaps = useMemo(() => {
    let filtered = careGaps;

    // Apply filters
    if (filters.priority !== 'all') {
      filtered = filtered.filter(gap => gap.priority === filters.priority);
    }

    if (filters.status !== 'all') {
      filtered = filtered.filter(gap => gap.status === filters.status);
    }

    // Sort by priority and due date
    return filtered.sort((a, b) => {
      const priorityOrder = { urgent: 4, high: 3, medium: 2, low: 1 };
      const aPriority = priorityOrder[a.priority as keyof typeof priorityOrder] || 1;
      const bPriority = priorityOrder[b.priority as keyof typeof priorityOrder] || 1;

      if (aPriority !== bPriority) {
        return bPriority - aPriority; // Higher priority first
      }

      return new Date(a.dueDate).getTime() - new Date(b.dueDate).getTime(); // Earlier due date first
    });
  }, [careGaps, filters]);

  const filteredRecommendations = useMemo(() => {
    let filtered = recommendations;

    if (filters.priority !== 'all') {
      filtered = filtered.filter(rec => rec.priority === filters.priority);
    }

    if (filters.status !== 'all') {
      filtered = filtered.filter(rec => rec.status === filters.status);
    }

    return filtered.sort((a, b) => {
      const priorityOrder = { urgent: 4, high: 3, medium: 2, low: 1 };
      const aPriority = priorityOrder[a.priority as keyof typeof priorityOrder] || 1;
      const bPriority = priorityOrder[b.priority as keyof typeof priorityOrder] || 1;

      return bPriority - aPriority;
    });
  }, [recommendations, filters]);

  // Quality metrics with issues
  const qualityIssues = useMemo(() => {
    return qualityMetrics.filter(metric =>
      metric.current < metric.target || metric.trend === 'declining'
    );
  }, [qualityMetrics]);

  // Handle filter change
  const handleFilterChange = (key: keyof AlertFilter, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  // Handle care gap status update
  const handleStatusUpdate = async (gapId: string, newStatus: CareGap['status']) => {
    await updateCareGapStatus(gapId, newStatus);
  };

  // Get alert statistics
  const alertStats = useMemo(() => {
    const urgentGaps = careGaps.filter(gap => gap.priority === 'urgent' && gap.status === 'open').length;
    const overdueGaps = careGaps.filter(gap => {
      const { isOverdue } = getDaysUntilDue(gap.dueDate);
      return isOverdue && gap.status === 'open';
    }).length;
    const totalSavings = careGaps.reduce((sum, gap) => sum + gap.potentialCostSaving, 0);
    const highPriorityRecommendations = recommendations.filter(rec =>
      rec.priority === 'high' && rec.status === 'recommended'
    ).length;

    return {
      urgentGaps,
      overdueGaps,
      totalSavings,
      highPriorityRecommendations,
      qualityIssues: qualityIssues.length
    };
  }, [careGaps, recommendations, qualityIssues]);

  if (isLoading) {
    return (
      <Card className={`p-6 ${className}`}>
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/3"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          </div>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={`p-6 ${className}`}>
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Error Loading Alerts</h3>
          <p className="text-gray-600">{error}</p>
        </div>
      </Card>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header with Statistics */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900 flex items-center">
            <Bell className="h-5 w-5 mr-2" />
            Care Alerts & Recommendations
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            {alertStats.urgentGaps + alertStats.overdueGaps} urgent items requiring attention
          </p>
        </div>

        {showFilters && (
          <Button
            variant={showFiltersPanel ? "default" : "outline"}
            size="sm"
            onClick={() => setShowFiltersPanel(!showFiltersPanel)}
          >
            <Filter className="h-4 w-4 mr-2" />
            Filters
          </Button>
        )}
      </div>

      {/* Quick Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Urgent</p>
              <p className="text-2xl font-bold text-red-600">{alertStats.urgentGaps}</p>
            </div>
            <AlertTriangle className="h-8 w-8 text-red-500" />
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Overdue</p>
              <p className="text-2xl font-bold text-orange-600">{alertStats.overdueGaps}</p>
            </div>
            <Clock className="h-8 w-8 text-orange-500" />
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Potential Savings</p>
              <p className="text-lg font-bold text-green-600">
                {formatCurrency(alertStats.totalSavings)}
              </p>
            </div>
            <DollarSign className="h-8 w-8 text-green-500" />
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Recommendations</p>
              <p className="text-2xl font-bold text-blue-600">{alertStats.highPriorityRecommendations}</p>
            </div>
            <Zap className="h-8 w-8 text-blue-500" />
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Quality Issues</p>
              <p className="text-2xl font-bold text-purple-600">{alertStats.qualityIssues}</p>
            </div>
            <TrendingDown className="h-8 w-8 text-purple-500" />
          </div>
        </Card>
      </div>

      {/* Filters Panel */}
      {showFiltersPanel && (
        <Card className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Priority
              </label>
              <select
                value={filters.priority}
                onChange={(e) => handleFilterChange('priority', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="all">All Priorities</option>
                <option value="urgent">Urgent</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Status
              </label>
              <select
                value={filters.status}
                onChange={(e) => handleFilterChange('status', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="all">All Statuses</option>
                <option value="open">Open</option>
                <option value="scheduled">Scheduled</option>
                <option value="completed">Completed</option>
              </select>
            </div>

            <div className="flex items-end">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setFilters({ priority: 'all', type: 'all', status: 'all' })}
                className="w-full"
              >
                Clear Filters
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Care Gaps Section */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <AlertTriangle className="h-5 w-5 mr-2 text-orange-500" />
            Care Gaps ({filteredCareGaps.length})
          </h3>
          {onViewAllCareGaps && (
            <Button variant="ghost" size="sm" onClick={onViewAllCareGaps}>
              View All
              <ChevronRight className="h-4 w-4 ml-1" />
            </Button>
          )}
        </div>

        <div className="space-y-4">
          {filteredCareGaps.length === 0 ? (
            <div className="text-center py-8">
              <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
              <h4 className="text-lg font-semibold text-gray-900 mb-2">No Care Gaps Found</h4>
              <p className="text-gray-600">All care measures are up to date!</p>
            </div>
          ) : (
            filteredCareGaps.slice(0, compact ? 3 : 10).map((gap) => {
              const priorityConfig = getPriorityConfig(gap.priority);
              const PriorityIcon = priorityConfig.icon;
              const TypeIcon = getTypeIcon(gap.type);
              const { days, isOverdue } = getDaysUntilDue(gap.dueDate);

              return (
                <div
                  key={gap.id}
                  className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                  onClick={() => onAlertClick?.(gap)}
                >
                  <div className="flex items-start space-x-4">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${priorityConfig.bgColor}`}>
                      <PriorityIcon className={`h-5 w-5 ${priorityConfig.color}`} />
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <h4 className="text-base font-semibold text-gray-900">
                            {gap.category}
                          </h4>
                          <p className="text-sm text-gray-600 mt-1">
                            {gap.description}
                          </p>
                        </div>

                        <div className="flex flex-col items-end space-y-2">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${priorityConfig.bgColor} ${priorityConfig.color}`}>
                            {priorityConfig.label}
                          </span>

                          <div className={`text-xs font-medium ${
                            isOverdue ? 'text-red-600' :
                            days <= 7 ? 'text-orange-600' : 'text-gray-600'
                          }`}>
                            {isOverdue ? `${days} days overdue` : `Due in ${days} days`}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4 text-sm text-gray-500">
                          <span className="flex items-center">
                            <TypeIcon className="h-4 w-4 mr-1" />
                            {gap.type.replace('_', ' ')}
                          </span>

                          <span className="flex items-center">
                            <DollarSign className="h-4 w-4 mr-1" />
                            {formatCurrency(gap.potentialCostSaving)} potential savings
                          </span>

                          {gap.assignedProvider && (
                            <span className="flex items-center">
                              <Users className="h-4 w-4 mr-1" />
                              {gap.assignedProvider}
                            </span>
                          )}
                        </div>

                        <div className="flex items-center space-x-2">
                          {gap.status === 'open' && (
                            <>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleStatusUpdate(gap.id, 'scheduled');
                                }}
                              >
                                Schedule
                              </Button>
                              <Button
                                size="sm"
                                variant="default"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleStatusUpdate(gap.id, 'completed');
                                }}
                              >
                                Mark Complete
                              </Button>
                            </>
                          )}

                          {gap.status === 'scheduled' && (
                            <span className={`px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700`}>
                              Scheduled
                            </span>
                          )}

                          {gap.status === 'completed' && (
                            <span className={`px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700`}>
                              <CheckCircle className="h-3 w-3 mr-1 inline" />
                              Completed
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Recommendation */}
                      <div className="mt-3 p-3 bg-blue-50 rounded-lg">
                        <h5 className="text-sm font-medium text-blue-900 mb-1">Recommendation:</h5>
                        <p className="text-sm text-blue-800">{gap.recommendation}</p>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </Card>

      {/* Intervention Recommendations Section */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <Zap className="h-5 w-5 mr-2 text-blue-500" />
            Intervention Recommendations ({filteredRecommendations.length})
          </h3>
        </div>

        <div className="space-y-4">
          {filteredRecommendations.length === 0 ? (
            <div className="text-center py-8">
              <MessageCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h4 className="text-lg font-semibold text-gray-900 mb-2">No Recommendations</h4>
              <p className="text-gray-600">No intervention recommendations at this time.</p>
            </div>
          ) : (
            filteredRecommendations.slice(0, compact ? 2 : 5).map((recommendation) => {
              const priorityConfig = getPriorityConfig(recommendation.priority);
              const PriorityIcon = priorityConfig.icon;
              const TypeIcon = getTypeIcon(recommendation.type);

              return (
                <div
                  key={recommendation.id}
                  className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                  onClick={() => onAlertClick?.(recommendation)}
                >
                  <div className="flex items-start space-x-4">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${priorityConfig.bgColor}`}>
                      <TypeIcon className={`h-5 w-5 ${priorityConfig.color}`} />
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <h4 className="text-base font-semibold text-gray-900">
                            {recommendation.title}
                          </h4>
                          <p className="text-sm text-gray-600 mt-1">
                            {recommendation.description}
                          </p>
                        </div>

                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${priorityConfig.bgColor} ${priorityConfig.color}`}>
                          {priorityConfig.label}
                        </span>
                      </div>

                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4 text-sm text-gray-500">
                          <span className="flex items-center">
                            <Calendar className="h-4 w-4 mr-1" />
                            {recommendation.timeframe}
                          </span>

                          <span className="flex items-center">
                            <DollarSign className="h-4 w-4 mr-1" />
                            {formatCurrency(recommendation.costEstimate)}
                          </span>

                          {recommendation.qualityMeasure && (
                            <span className="flex items-center">
                              <Activity className="h-4 w-4 mr-1" />
                              {recommendation.qualityMeasure}
                            </span>
                          )}
                        </div>

                        <div className="flex items-center space-x-2">
                          {recommendation.status === 'recommended' && (
                            <Button
                              size="sm"
                              variant="default"
                              onClick={(e) => {
                                e.stopPropagation();
                                onScheduleIntervention?.(recommendation.id);
                              }}
                            >
                              Schedule
                            </Button>
                          )}

                          {recommendation.status === 'approved' && (
                            <span className={`px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700`}>
                              Approved
                            </span>
                          )}

                          {recommendation.status === 'scheduled' && (
                            <span className={`px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700`}>
                              Scheduled
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Expected Outcome */}
                      <div className="mt-3 p-3 bg-green-50 rounded-lg">
                        <h5 className="text-sm font-medium text-green-900 mb-1">Expected Outcome:</h5>
                        <p className="text-sm text-green-800">{recommendation.expectedOutcome}</p>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </Card>

      {/* Quality Metrics Issues */}
      {qualityIssues.length > 0 && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center mb-6">
            <TrendingDown className="h-5 w-5 mr-2 text-purple-500" />
            Quality Metric Issues ({qualityIssues.length})
          </h3>

          <div className="space-y-4">
            {qualityIssues.map((metric, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-base font-semibold text-gray-900">
                    {metric.measure}
                  </h4>
                  <div className="flex items-center space-x-2">
                    {metric.trend === 'declining' ? (
                      <ArrowDown className="h-4 w-4 text-red-500" />
                    ) : (
                      <ArrowUp className="h-4 w-4 text-green-500" />
                    )}
                    <span className={`text-sm font-medium ${
                      metric.trend === 'declining' ? 'text-red-600' : 'text-green-600'
                    }`}>
                      {metric.trend}
                    </span>
                  </div>
                </div>

                <p className="text-sm text-gray-600 mb-3">{metric.description}</p>

                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Current:</span>
                    <span className={`ml-2 font-medium ${
                      metric.current < metric.target ? 'text-red-600' : 'text-green-600'
                    }`}>
                      {metric.current}%
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600">Target:</span>
                    <span className="ml-2 font-medium text-gray-900">{metric.target}%</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Benchmark:</span>
                    <span className="ml-2 font-medium text-blue-600">{metric.benchmark}%</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
};

export default AlertsPanel;
