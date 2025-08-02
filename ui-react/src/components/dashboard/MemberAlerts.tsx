import React, { useState, useMemo } from 'react';
import {
  AlertTriangle,
  AlertCircle,
  CheckCircle,
  Clock,
  Calendar,
  DollarSign,
  Stethoscope,
  Activity,
  Heart,
  Eye,
  TestTube,
  Pill,
  Phone,
  Mail,
  FileText,
  TrendingUp,
  Target,
  Award,
  Filter,
  MoreHorizontal,
  ChevronDown,
  ChevronRight,
  X,
  Plus,
  Send
} from 'lucide-react';
import { CareGap, InterventionRecommendation, QualityMetric, Member } from '../../types/healthcare';
import { useCareGaps } from '../../hooks/health/useCareGaps';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { LoadingSpinner } from '../ui/LoadingSpinner';

interface MemberAlertsProps {
  memberId: string;
  member?: Member;
  onScheduleAppointment?: (gapId: string) => void;
  onContactMember?: (method: 'phone' | 'email', gapId: string) => void;
  onUpdateGapStatus?: (gapId: string, status: CareGap['status']) => void;
  className?: string;
  showActions?: boolean;
  compact?: boolean;
}

interface AlertFilters {
  priority: 'all' | 'urgent' | 'high' | 'medium' | 'low';
  type: 'all' | 'preventive' | 'chronic_care' | 'medication_adherence' | 'follow_up';
  status: 'all' | 'open' | 'scheduled' | 'completed' | 'closed';
}

export const MemberAlerts: React.FC<MemberAlertsProps> = ({
  memberId,
  member,
  onScheduleAppointment,
  onContactMember,
  onUpdateGapStatus,
  className = '',
  showActions = true,
  compact = false
}) => {
  const [filters, setFilters] = useState<AlertFilters>({
    priority: 'all',
    type: 'all',
    status: 'all'
  });
  const [showFilters, setShowFilters] = useState(false);
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());
  const [selectedTab, setSelectedTab] = useState<'gaps' | 'recommendations' | 'metrics'>('gaps');

  const {
    careGaps,
    recommendations,
    qualityMetrics,
    analysis,
    isLoading,
    error,
    updateCareGapStatus,
    getPriorityCareGaps,
    getOverdueCareGaps
  } = useCareGaps(memberId);

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
    const diffTime = date.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays < 0) {
      return `${Math.abs(diffDays)} days overdue`;
    } else if (diffDays === 0) {
      return 'Due today';
    } else if (diffDays === 1) {
      return 'Due tomorrow';
    } else if (diffDays <= 7) {
      return `Due in ${diffDays} days`;
    } else {
      return date.toLocaleDateString('en-AE', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      });
    }
  };

  // Get priority display properties
  const getPriorityDisplay = (priority: CareGap['priority']) => {
    const displays = {
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
        icon: AlertCircle,
        label: 'Medium'
      },
      low: {
        color: 'text-blue-600',
        bgColor: 'bg-blue-100',
        icon: AlertCircle,
        label: 'Low'
      }
    };
    return displays[priority];
  };

  // Get care gap type icon
  const getCareGapIcon = (type: CareGap['type'], category: string) => {
    if (category.toLowerCase().includes('eye') || category.toLowerCase().includes('vision')) {
      return Eye;
    } else if (category.toLowerCase().includes('lab') || category.toLowerCase().includes('test')) {
      return TestTube;
    } else if (category.toLowerCase().includes('medication') || category.toLowerCase().includes('prescription')) {
      return Pill;
    } else if (category.toLowerCase().includes('heart') || category.toLowerCase().includes('cardio')) {
      return Heart;
    } else {
      switch (type) {
        case 'preventive': return Activity;
        case 'chronic_care': return Stethoscope;
        case 'medication_adherence': return Pill;
        case 'follow_up': return Calendar;
        default: return AlertCircle;
      }
    }
  };

  // Filter care gaps
  const filteredCareGaps = useMemo(() => {
    let filtered = [...careGaps];

    if (filters.priority !== 'all') {
      filtered = filtered.filter(gap => gap.priority === filters.priority);
    }

    if (filters.type !== 'all') {
      filtered = filtered.filter(gap => gap.type === filters.type);
    }

    if (filters.status !== 'all') {
      filtered = filtered.filter(gap => gap.status === filters.status);
    }

    // Sort by priority and due date
    return filtered.sort((a, b) => {
      const priorityOrder = { urgent: 4, high: 3, medium: 2, low: 1 };
      const priorityDiff = priorityOrder[b.priority] - priorityOrder[a.priority];
      
      if (priorityDiff !== 0) return priorityDiff;
      
      return new Date(a.dueDate).getTime() - new Date(b.dueDate).getTime();
    });
  }, [careGaps, filters]);

  // Toggle expansion
  const toggleExpansion = (itemId: string) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(itemId)) {
      newExpanded.delete(itemId);
    } else {
      newExpanded.add(itemId);
    }
    setExpandedItems(newExpanded);
  };

  // Handle status update
  const handleStatusUpdate = async (gapId: string, status: CareGap['status']) => {
    try {
      await updateCareGapStatus(gapId, status);
      if (onUpdateGapStatus) {
        onUpdateGapStatus(gapId, status);
      }
    } catch (error) {
      console.error('Failed to update care gap status:', error);
    }
  };

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return (
      <Card className="p-6 text-center">
        <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Error Loading Care Gaps</h3>
        <p className="text-gray-600">{error}</p>
      </Card>
    );
  }

  const overdueCareGaps = getOverdueCareGaps();
  const urgentCareGaps = getPriorityCareGaps('urgent');

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header with Analysis */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Care Management</h2>
          <p className="text-sm text-gray-600">
            {analysis.totalGaps} care gaps • {analysis.urgentGaps} urgent • 
            Potential savings: {formatCurrency(analysis.potentialSavings)}
          </p>
        </div>
        
        {/* Quick Stats */}
        <div className="grid grid-cols-2 gap-4 text-center">
          <div className="bg-red-50 p-3 rounded-lg">
            <div className="text-lg font-bold text-red-600">{overdueCareGaps.length}</div>
            <div className="text-xs text-red-600">Overdue</div>
          </div>
          <div className="bg-orange-50 p-3 rounded-lg">
            <div className="text-lg font-bold text-orange-600">{urgentCareGaps.length}</div>
            <div className="text-xs text-orange-600">Urgent</div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8" aria-label="Tabs">
          {[
            { id: 'gaps', label: 'Care Gaps', count: careGaps.length },
            { id: 'recommendations', label: 'Recommendations', count: recommendations.length },
            { id: 'metrics', label: 'Quality Metrics', count: qualityMetrics.length }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setSelectedTab(tab.id as any)}
              className={`py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap ${
                selectedTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
              {tab.count > 0 && (
                <span className={`ml-2 py-0.5 px-2 rounded-full text-xs ${
                  selectedTab === tab.id
                    ? 'bg-blue-100 text-blue-600'
                    : 'bg-gray-100 text-gray-600'
                }`}>
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* Filters */}
      {selectedTab === 'gaps' && (
        <Card className="p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-gray-900">Filters</h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowFilters(!showFilters)}
            >
              <Filter className="h-4 w-4 mr-2" />
              {showFilters ? 'Hide' : 'Show'} Filters
              <ChevronDown className={`h-3 w-3 ml-1 transition-transform ${
                showFilters ? 'rotate-180' : ''
              }`} />
            </Button>
          </div>
          
          {showFilters && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Priority</label>
                <select
                  value={filters.priority}
                  onChange={(e) => setFilters(prev => ({ ...prev, priority: e.target.value as any }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">All Priorities</option>
                  <option value="urgent">Urgent</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>
              
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Type</label>
                <select
                  value={filters.type}
                  onChange={(e) => setFilters(prev => ({ ...prev, type: e.target.value as any }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">All Types</option>
                  <option value="preventive">Preventive</option>
                  <option value="chronic_care">Chronic Care</option>
                  <option value="medication_adherence">Medication Adherence</option>
                  <option value="follow_up">Follow-up</option>
                </select>
              </div>
              
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Status</label>
                <select
                  value={filters.status}
                  onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value as any }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">All Statuses</option>
                  <option value="open">Open</option>
                  <option value="scheduled">Scheduled</option>
                  <option value="completed">Completed</option>
                  <option value="closed">Closed</option>
                </select>
              </div>
            </div>
          )}
        </Card>
      )}

      {/* Content based on selected tab */}
      {selectedTab === 'gaps' && (
        <div className="space-y-4">
          {filteredCareGaps.length === 0 ? (
            <Card className="p-8 text-center">
              <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">All Caught Up!</h3>
              <p className="text-gray-600">
                No care gaps found matching your current filters.
              </p>
            </Card>
          ) : (
            filteredCareGaps.map((gap) => {
              const priorityDisplay = getPriorityDisplay(gap.priority);
              const Icon = getCareGapIcon(gap.type, gap.category);
              const PriorityIcon = priorityDisplay.icon;
              const isExpanded = expandedItems.has(gap.id);
              const isOverdue = new Date(gap.dueDate) < new Date();
              
              return (
                <Card key={gap.id} className={`p-4 ${isOverdue ? 'border-red-200 bg-red-50' : ''}`}>
                  <div className="flex items-start space-x-4">
                    {/* Icon */}
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${priorityDisplay.bgColor}`}>
                      <Icon className={`h-5 w-5 ${priorityDisplay.color}`} />
                    </div>
                    
                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <h3 className="text-base font-semibold text-gray-900">
                            {gap.category}
                          </h3>
                          <p className="text-sm text-gray-600">
                            {gap.description}
                          </p>
                        </div>
                        
                        <div className="flex items-center space-x-2 ml-4">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium flex items-center space-x-1 ${priorityDisplay.bgColor} ${priorityDisplay.color}`}>
                            <PriorityIcon className="h-3 w-3" />
                            <span>{priorityDisplay.label}</span>
                          </span>
                          
                          <button
                            onClick={() => toggleExpansion(gap.id)}
                            className="text-gray-400 hover:text-gray-600"
                          >
                            {isExpanded ? (
                              <ChevronDown className="h-4 w-4" />
                            ) : (
                              <ChevronRight className="h-4 w-4" />
                            )}
                          </button>
                        </div>
                      </div>
                      
                      {/* Summary Info */}
                      <div className="flex items-center text-sm text-gray-500 space-x-4 mb-3">
                        <span className="flex items-center">
                          <Clock className="h-4 w-4 mr-1" />
                          {formatDate(gap.dueDate)}
                        </span>
                        
                        <span className="flex items-center">
                          <DollarSign className="h-4 w-4 mr-1" />
                          {formatCurrency(gap.potentialCostSaving)} potential savings
                        </span>
                        
                        <span className="capitalize">
                          {gap.type.replace('_', ' ')}
                        </span>
                      </div>
                      
                      {/* Actions */}
                      {showActions && gap.status === 'open' && (
                        <div className="flex items-center space-x-2 mb-3">
                          <Button
                            size="sm"
                            onClick={() => onScheduleAppointment?.(gap.id)}
                            className="flex items-center"
                          >
                            <Calendar className="h-4 w-4 mr-1" />
                            Schedule
                          </Button>
                          
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => onContactMember?.('phone', gap.id)}
                          >
                            <Phone className="h-4 w-4 mr-1" />
                            Call
                          </Button>
                          
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => onContactMember?.('email', gap.id)}
                          >
                            <Mail className="h-4 w-4 mr-1" />
                            Email
                          </Button>
                          
                          <div className="relative">
                            <select
                              value={gap.status}
                              onChange={(e) => handleStatusUpdate(gap.id, e.target.value as CareGap['status'])}
                              className="appearance-none bg-white border border-gray-300 rounded px-3 py-1 text-sm focus:ring-2 focus:ring-blue-500"
                            >
                              <option value="open">Open</option>
                              <option value="scheduled">Scheduled</option>
                              <option value="completed">Completed</option>
                              <option value="closed">Closed</option>
                            </select>
                          </div>
                        </div>
                      )}
                      
                      {/* Expanded Details */}
                      {isExpanded && (
                        <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                              <h4 className="text-sm font-medium text-gray-900 mb-2">Recommendation</h4>
                              <p className="text-sm text-gray-600 mb-4">
                                {gap.recommendation}
                              </p>
                              
                              <h4 className="text-sm font-medium text-gray-900 mb-2">Evidence Base</h4>
                              <p className="text-sm text-gray-600">
                                {gap.evidenceBase}
                              </p>
                            </div>
                            
                            <div>
                              <h4 className="text-sm font-medium text-gray-900 mb-2">Details</h4>
                              <div className="space-y-2 text-sm">
                                <div className="flex justify-between">
                                  <span className="text-gray-600">Due Date:</span>
                                  <span className={`font-medium ${isOverdue ? 'text-red-600' : 'text-gray-900'}`}>
                                    {formatDate(gap.dueDate)}
                                  </span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-gray-600">Potential Savings:</span>
                                  <span className="font-medium text-gray-900">
                                    {formatCurrency(gap.potentialCostSaving)}
                                  </span>
                                </div>
                                {gap.assignedProvider && (
                                  <div className="flex justify-between">
                                    <span className="text-gray-600">Assigned Provider:</span>
                                    <span className="font-medium text-gray-900">
                                      {gap.assignedProvider}
                                    </span>
                                  </div>
                                )}
                                <div className="flex justify-between">
                                  <span className="text-gray-600">Created:</span>
                                  <span className="text-gray-900">
                                    {new Date(gap.createdAt).toLocaleDateString('en-AE')}
                                  </span>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </Card>
              );
            })
          )}
        </div>
      )}

      {selectedTab === 'recommendations' && (
        <div className="space-y-4">
          {recommendations.length === 0 ? (
            <Card className="p-8 text-center">
              <Target className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No Recommendations</h3>
              <p className="text-gray-600">
                No intervention recommendations available at this time.
              </p>
            </Card>
          ) : (
            recommendations.map((recommendation) => (
              <Card key={recommendation.id} className="p-4">
                <div className="flex items-start space-x-4">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                    recommendation.priority === 'high' ? 'bg-red-100' :
                    recommendation.priority === 'medium' ? 'bg-yellow-100' :
                    'bg-blue-100'
                  }`}>
                    <Target className={`h-5 w-5 ${
                      recommendation.priority === 'high' ? 'text-red-600' :
                      recommendation.priority === 'medium' ? 'text-yellow-600' :
                      'text-blue-600'
                    }`} />
                  </div>
                  
                  <div className="flex-1">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <h3 className="text-base font-semibold text-gray-900">
                          {recommendation.title}
                        </h3>
                        <p className="text-sm text-gray-600">
                          {recommendation.description}
                        </p>
                      </div>
                      
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        recommendation.status === 'completed' ? 'bg-green-100 text-green-700' :
                        recommendation.status === 'approved' ? 'bg-blue-100 text-blue-700' :
                        recommendation.status === 'scheduled' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-gray-100 text-gray-700'
                      }`}>
                        {recommendation.status}
                      </span>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                      <div>
                        <h4 className="text-sm font-medium text-gray-900 mb-1">Expected Outcome</h4>
                        <p className="text-sm text-gray-600 mb-3">{recommendation.expectedOutcome}</p>
                        
                        <h4 className="text-sm font-medium text-gray-900 mb-1">Timeframe</h4>
                        <p className="text-sm text-gray-600">{recommendation.timeframe}</p>
                      </div>
                      
                      <div>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-600">Type:</span>
                            <span className="text-gray-900 capitalize">
                              {recommendation.type.replace('_', ' ')}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Priority:</span>
                            <span className="text-gray-900 capitalize">
                              {recommendation.priority}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Cost Estimate:</span>
                            <span className="text-gray-900">
                              {formatCurrency(recommendation.costEstimate)}
                            </span>
                          </div>
                          {recommendation.qualityMeasure && (
                            <div className="flex justify-between">
                              <span className="text-gray-600">Quality Measure:</span>
                              <span className="text-gray-900">
                                {recommendation.qualityMeasure}
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </Card>
            ))
          )}
        </div>
      )}

      {selectedTab === 'metrics' && (
        <div className="space-y-4">
          {qualityMetrics.length === 0 ? (
            <Card className="p-8 text-center">
              <Award className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No Quality Metrics</h3>
              <p className="text-gray-600">
                Quality metrics data is not available at this time.
              </p>
            </Card>
          ) : (
            qualityMetrics.map((metric, index) => (
              <Card key={index} className="p-4">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-base font-semibold text-gray-900">{metric.measure}</h3>
                    <p className="text-sm text-gray-600">{metric.description}</p>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    {metric.trend === 'improving' ? (
                      <TrendingUp className="h-5 w-5 text-green-500" />
                    ) : metric.trend === 'declining' ? (
                      <TrendingDown className="h-5 w-5 text-red-500" />
                    ) : (
                      <Activity className="h-5 w-5 text-gray-500" />
                    )}
                    <span className={`text-sm font-medium ${
                      metric.trend === 'improving' ? 'text-green-600' :
                      metric.trend === 'declining' ? 'text-red-600' :
                      'text-gray-600'
                    }`}>
                      {metric.trend}
                    </span>
                  </div>
                </div>
                
                <div className="space-y-3">
                  {/* Progress Bar */}
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Current Performance</span>
                      <span className="font-medium">{metric.current}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${
                          metric.current >= metric.target ? 'bg-green-500' :
                          metric.current >= metric.target * 0.8 ? 'bg-yellow-500' :
                          'bg-red-500'
                        }`}
                        style={{ width: `${Math.min(metric.current, 100)}%` }}
                      />
                    </div>
                  </div>
                  
                  {/* Metrics Grid */}
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <div className="text-lg font-semibold text-gray-900">{metric.current}%</div>
                      <div className="text-xs text-gray-600">Current</div>
                    </div>
                    <div>
                      <div className="text-lg font-semibold text-blue-600">{metric.target}%</div>
                      <div className="text-xs text-gray-600">Target</div>
                    </div>
                    <div>
                      <div className="text-lg font-semibold text-purple-600">{metric.benchmark}%</div>
                      <div className="text-xs text-gray-600">Benchmark</div>
                    </div>
                  </div>
                  
                  <div className="text-xs text-gray-500 text-center">
                    Last updated: {new Date(metric.lastUpdated).toLocaleDateString('en-AE')}
                  </div>
                </div>
              </Card>
            ))
          )}
        </div>
      )}
    </div>
  );
};

export default MemberAlerts;