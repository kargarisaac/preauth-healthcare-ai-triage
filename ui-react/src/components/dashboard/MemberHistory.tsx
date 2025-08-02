import React, { useState, useMemo } from 'react';
import {
  Calendar,
  Clock,
  FileText,
  DollarSign,
  User,
  Phone,
  AlertCircle,
  CheckCircle,
  XCircle,
  Filter,
  Search,
  Download,
  ChevronDown,
  ChevronRight,
  Activity,
  Stethoscope,
  Pill,
  Heart,
  MessageCircle
} from 'lucide-react';
import { MemberActivity, AuthorizationHistory } from '../../types/healthcare';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';

interface MemberHistoryProps {
  activities: MemberActivity[];
  authorizationHistory?: AuthorizationHistory[];
  memberId: string;
  memberName: string;
  className?: string;
  showFilters?: boolean;
  compact?: boolean;
}

interface TimelineFilters {
  dateRange: 'all' | 'last30' | 'last90' | 'last365' | 'custom';
  activityType: 'all' | 'authorization' | 'claim' | 'appointment' | 'communication' | 'care_gap' | 'intervention';
  status: 'all' | 'approved' | 'denied' | 'pending' | 'completed' | 'cancelled';
  customStartDate?: string;
  customEndDate?: string;
}

export const MemberHistory: React.FC<MemberHistoryProps> = ({
  activities,
  authorizationHistory = [],
  memberId,
  memberName,
  className = '',
  showFilters = true,
  compact = false
}) => {
  const [filters, setFilters] = useState<TimelineFilters>({
    dateRange: 'all',
    activityType: 'all',
    status: 'all'
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [showFilters, setShowFiltersPanel] = useState(false);
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());

  // Format currency
  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-AE', {
      style: 'currency',
      currency: 'AED',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  // Format date and time
  const formatDateTime = (dateString: string): { date: string; time: string; relative: string } => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    let relative = '';
    if (diffDays === 1) {
      relative = 'Yesterday';
    } else if (diffDays === 0) {
      relative = 'Today';
    } else if (diffDays <= 7) {
      relative = `${diffDays} days ago`;
    } else if (diffDays <= 30) {
      relative = `${Math.ceil(diffDays / 7)} weeks ago`;
    } else if (diffDays <= 365) {
      relative = `${Math.ceil(diffDays / 30)} months ago`;
    } else {
      relative = `${Math.ceil(diffDays / 365)} years ago`;
    }
    
    return {
      date: date.toLocaleDateString('en-AE', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      }),
      time: date.toLocaleTimeString('en-AE', {
        hour: '2-digit',
        minute: '2-digit'
      }),
      relative
    };
  };

  // Get activity icon and color
  const getActivityDisplay = (type: string, status: string) => {
    const displays = {
      authorization: {
        icon: FileText,
        color: 'text-blue-600',
        bgColor: 'bg-blue-100',
        label: 'Authorization'
      },
      claim: {
        icon: DollarSign,
        color: 'text-green-600',
        bgColor: 'bg-green-100',
        label: 'Claim'
      },
      appointment: {
        icon: Calendar,
        color: 'text-purple-600',
        bgColor: 'bg-purple-100',
        label: 'Appointment'
      },
      communication: {
        icon: MessageCircle,
        color: 'text-indigo-600',
        bgColor: 'bg-indigo-100',
        label: 'Communication'
      },
      care_gap: {
        icon: AlertCircle,
        color: 'text-yellow-600',
        bgColor: 'bg-yellow-100',
        label: 'Care Gap'
      },
      intervention: {
        icon: Activity,
        color: 'text-red-600',
        bgColor: 'bg-red-100',
        label: 'Intervention'
      }
    };

    const display = displays[type as keyof typeof displays] || {
      icon: FileText,
      color: 'text-gray-600',
      bgColor: 'bg-gray-100',
      label: 'Activity'
    };

    // Get status color
    let statusColor = 'text-gray-600';
    let statusBgColor = 'bg-gray-100';
    
    switch (status.toLowerCase()) {
      case 'approved':
      case 'completed':
      case 'paid':
        statusColor = 'text-green-600';
        statusBgColor = 'bg-green-100';
        break;
      case 'denied':
      case 'rejected':
      case 'cancelled':
        statusColor = 'text-red-600';
        statusBgColor = 'bg-red-100';
        break;
      case 'pending':
      case 'scheduled':
      case 'open':
        statusColor = 'text-yellow-600';
        statusBgColor = 'bg-yellow-100';
        break;
      case 'in_progress':
      case 'processing':
        statusColor = 'text-blue-600';
        statusBgColor = 'bg-blue-100';
        break;
    }

    return { ...display, statusColor, statusBgColor };
  };

  // Filter activities based on current filters
  const filteredActivities = useMemo(() => {
    let filtered = [...activities];

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(activity => 
        activity.title.toLowerCase().includes(query) ||
        activity.description.toLowerCase().includes(query) ||
        activity.provider?.toLowerCase().includes(query) ||
        activity.status.toLowerCase().includes(query)
      );
    }

    // Apply date range filter
    if (filters.dateRange !== 'all') {
      const now = new Date();
      let startDate: Date;
      
      switch (filters.dateRange) {
        case 'last30':
          startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
          break;
        case 'last90':
          startDate = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000);
          break;
        case 'last365':
          startDate = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000);
          break;
        case 'custom':
          if (filters.customStartDate) {
            startDate = new Date(filters.customStartDate);
            const endDate = filters.customEndDate ? new Date(filters.customEndDate) : now;
            filtered = filtered.filter(activity => {
              const activityDate = new Date(activity.timestamp);
              return activityDate >= startDate && activityDate <= endDate;
            });
          }
          return filtered;
        default:
          return filtered;
      }
      
      filtered = filtered.filter(activity => 
        new Date(activity.timestamp) >= startDate
      );
    }

    // Apply activity type filter
    if (filters.activityType !== 'all') {
      filtered = filtered.filter(activity => activity.type === filters.activityType);
    }

    // Apply status filter
    if (filters.status !== 'all') {
      filtered = filtered.filter(activity => 
        activity.status.toLowerCase() === filters.status.toLowerCase()
      );
    }

    // Sort by timestamp (most recent first)
    return filtered.sort((a, b) => 
      new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );
  }, [activities, filters, searchQuery]);

  // Group activities by date
  const groupedActivities = useMemo(() => {
    const groups: { [key: string]: MemberActivity[] } = {};
    
    filteredActivities.forEach(activity => {
      const dateKey = new Date(activity.timestamp).toDateString();
      if (!groups[dateKey]) {
        groups[dateKey] = [];
      }
      groups[dateKey].push(activity);
    });
    
    return Object.entries(groups).sort(([a], [b]) => 
      new Date(b).getTime() - new Date(a).getTime()
    );
  }, [filteredActivities]);

  // Toggle item expansion
  const toggleExpansion = (itemId: string) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(itemId)) {
      newExpanded.delete(itemId);
    } else {
      newExpanded.add(itemId);
    }
    setExpandedItems(newExpanded);
  };

  // Handle filter changes
  const handleFilterChange = (key: keyof TimelineFilters, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  // Clear all filters
  const clearFilters = () => {
    setFilters({
      dateRange: 'all',
      activityType: 'all',
      status: 'all'
    });
    setSearchQuery('');
  };

  // Export timeline data
  const exportTimeline = () => {
    const data = filteredActivities.map(activity => ({
      Date: formatDateTime(activity.timestamp).date,
      Time: formatDateTime(activity.timestamp).time,
      Type: activity.type,
      Title: activity.title,
      Description: activity.description,
      Status: activity.status,
      Provider: activity.provider || '',
      Amount: activity.amount ? formatCurrency(activity.amount) : '',
      Outcome: activity.outcome || ''
    }));
    
    // Create CSV content
    const headers = Object.keys(data[0] || {});
    const csvContent = [
      headers.join(','),
      ...data.map(row => headers.map(header => `"${row[header as keyof typeof row]}"`).join(','))
    ].join('\n');
    
    // Download file
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${memberName}_timeline_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Member Timeline</h2>
          <p className="text-sm text-gray-600">
            {filteredActivities.length} activities • {memberName}
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <Button
            variant="outline"
            size="sm"
            onClick={exportTimeline}
            disabled={filteredActivities.length === 0}
          >
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
          
          {showFilters && (
            <Button
              variant={showFiltersPanel ? "default" : "outline"}
              size="sm"
              onClick={() => setShowFiltersPanel(!showFiltersPanel)}
            >
              <Filter className="h-4 w-4 mr-2" />
              Filters
              <ChevronDown className={`h-3 w-3 ml-1 transition-transform ${
                showFiltersPanel ? 'rotate-180' : ''
              }`} />
            </Button>
          )}
        </div>
      </div>

      {/* Search and Filters */}
      <Card className="p-4">
        {/* Search Bar */}
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search activities..."
            className="w-full pl-9 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
          />
        </div>

        {/* Filter Panel */}
        {showFiltersPanel && (
          <div className="border-t pt-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {/* Date Range Filter */}
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Date Range
                </label>
                <select
                  value={filters.dateRange}
                  onChange={(e) => handleFilterChange('dateRange', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="all">All Time</option>
                  <option value="last30">Last 30 Days</option>
                  <option value="last90">Last 90 Days</option>
                  <option value="last365">Last Year</option>
                  <option value="custom">Custom Range</option>
                </select>
              </div>

              {/* Activity Type Filter */}
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Activity Type
                </label>
                <select
                  value={filters.activityType}
                  onChange={(e) => handleFilterChange('activityType', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="all">All Types</option>
                  <option value="authorization">Authorization</option>
                  <option value="claim">Claim</option>
                  <option value="appointment">Appointment</option>
                  <option value="communication">Communication</option>
                  <option value="care_gap">Care Gap</option>
                  <option value="intervention">Intervention</option>
                </select>
              </div>

              {/* Status Filter */}
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
                  <option value="approved">Approved</option>
                  <option value="denied">Denied</option>
                  <option value="pending">Pending</option>
                  <option value="completed">Completed</option>
                  <option value="cancelled">Cancelled</option>
                </select>
              </div>

              {/* Clear Filters */}
              <div className="flex items-end">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearFilters}
                  className="w-full"
                >
                  Clear Filters
                </Button>
              </div>
            </div>

            {/* Custom Date Range */}
            {filters.dateRange === 'custom' && (
              <div className="grid grid-cols-2 gap-4 mt-4">
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">
                    Start Date
                  </label>
                  <input
                    type="date"
                    value={filters.customStartDate || ''}
                    onChange={(e) => handleFilterChange('customStartDate', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">
                    End Date
                  </label>
                  <input
                    type="date"
                    value={filters.customEndDate || ''}
                    onChange={(e) => handleFilterChange('customEndDate', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
            )}
          </div>
        )}
      </Card>

      {/* Timeline */}
      <div className="space-y-6">
        {groupedActivities.length === 0 ? (
          <Card className="p-8 text-center">
            <Activity className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No Activities Found</h3>
            <p className="text-gray-600">
              {filteredActivities.length === 0 && activities.length > 0
                ? 'Try adjusting your search or filter criteria.'
                : 'No timeline activities recorded for this member.'}
            </p>
          </Card>
        ) : (
          groupedActivities.map(([dateKey, dayActivities]) => (
            <div key={dateKey} className="relative">
              {/* Date Header */}
              <div className="sticky top-0 z-10 bg-white py-2">
                <div className="flex items-center">
                  <div className="bg-gray-100 rounded-full px-3 py-1">
                    <p className="text-sm font-medium text-gray-700">
                      {formatDateTime(dayActivities[0].timestamp).date}
                    </p>
                  </div>
                  <div className="flex-1 ml-4 border-t border-gray-200" />
                </div>
              </div>

              {/* Activities for this date */}
              <div className="space-y-4 ml-4">
                {dayActivities.map((activity, index) => {
                  const display = getActivityDisplay(activity.type, activity.status);
                  const Icon = display.icon;
                  const datetime = formatDateTime(activity.timestamp);
                  const isExpanded = expandedItems.has(activity.id);
                  
                  return (
                    <div key={activity.id} className="relative">
                      {/* Timeline line */}
                      {index < dayActivities.length - 1 && (
                        <div className="absolute left-6 top-12 w-0.5 h-full bg-gray-200" />
                      )}
                      
                      <Card className="p-4">
                        <div className="flex items-start space-x-4">
                          {/* Icon */}
                          <div className={`w-12 h-12 rounded-full flex items-center justify-center ${display.bgColor}`}>
                            <Icon className={`h-6 w-6 ${display.color}`} />
                          </div>
                          
                          {/* Content */}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-start justify-between mb-2">
                              <div>
                                <h3 className="text-base font-semibold text-gray-900">
                                  {activity.title}
                                </h3>
                                <p className="text-sm text-gray-600">
                                  {activity.description}
                                </p>
                              </div>
                              
                              <div className="flex items-center space-x-2 ml-4">
                                <span className={`px-2 py-1 rounded-full text-xs font-medium ${display.statusBgColor} ${display.statusColor}`}>
                                  {activity.status}
                                </span>
                                <button
                                  onClick={() => toggleExpansion(activity.id)}
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
                            <div className="flex items-center text-sm text-gray-500 space-x-4">
                              <span className="flex items-center">
                                <Clock className="h-4 w-4 mr-1" />
                                {datetime.time}
                              </span>
                              
                              {activity.provider && (
                                <span className="flex items-center">
                                  <Stethoscope className="h-4 w-4 mr-1" />
                                  {activity.provider}
                                </span>
                              )}
                              
                              {activity.amount && (
                                <span className="flex items-center">
                                  <DollarSign className="h-4 w-4 mr-1" />
                                  {formatCurrency(activity.amount)}
                                </span>
                              )}
                              
                              <span className="text-xs">
                                {datetime.relative}
                              </span>
                            </div>
                            
                            {/* Expanded Details */}
                            {isExpanded && (
                              <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                  <div>
                                    <h4 className="text-sm font-medium text-gray-900 mb-2">Details</h4>
                                    <div className="space-y-2 text-sm">
                                      <div className="flex justify-between">
                                        <span className="text-gray-600">Type:</span>
                                        <span className="text-gray-900 capitalize">
                                          {activity.type.replace('_', ' ')}
                                        </span>
                                      </div>
                                      <div className="flex justify-between">
                                        <span className="text-gray-600">Status:</span>
                                        <span className="text-gray-900 capitalize">
                                          {activity.status}
                                        </span>
                                      </div>
                                      {activity.provider && (
                                        <div className="flex justify-between">
                                          <span className="text-gray-600">Provider:</span>
                                          <span className="text-gray-900">
                                            {activity.provider}
                                          </span>
                                        </div>
                                      )}
                                      {activity.amount && (
                                        <div className="flex justify-between">
                                          <span className="text-gray-600">Amount:</span>
                                          <span className="text-gray-900">
                                            {formatCurrency(activity.amount)}
                                          </span>
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                  
                                  {activity.outcome && (
                                    <div>
                                      <h4 className="text-sm font-medium text-gray-900 mb-2">Outcome</h4>
                                      <p className="text-sm text-gray-600">
                                        {activity.outcome}
                                      </p>
                                    </div>
                                  )}
                                </div>
                                
                                {/* Metadata */}
                                {activity.metadata && Object.keys(activity.metadata).length > 0 && (
                                  <div className="mt-4 pt-4 border-t border-gray-200">
                                    <h4 className="text-sm font-medium text-gray-900 mb-2">Additional Information</h4>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                      {Object.entries(activity.metadata).map(([key, value]) => (
                                        <div key={key} className="flex justify-between text-sm">
                                          <span className="text-gray-600 capitalize">
                                            {key.replace(/([A-Z])/g, ' $1').toLowerCase()}:
                                          </span>
                                          <span className="text-gray-900">
                                            {typeof value === 'string' ? value : JSON.stringify(value)}
                                          </span>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                      </Card>
                    </div>
                  );
                })}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default MemberHistory;